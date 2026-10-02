import os
import sys
import json
import time
import socket
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from utils import (
    load_config,
    save_config,
    load_friends,
    save_friends,
    init_browser,
    login_with_cookies,
    save_cookies,
    scan_friends,
    send_messages_to_selected
)

# ----------------- BIẾN TOÀN CỤC & NHẬT KÝ -----------------
LOG_BUFFER = []
LOG_LOCK = threading.Lock()
CURRENT_TASK = {"name": "", "is_running": False}
STOP_EVENT = threading.Event()
TASK_THREAD = None


def add_log(message):
    timestamp = time.strftime("[%H:%M:%S]")
    line = f"{timestamp} {message}"
    print(line)
    with LOG_LOCK:
        LOG_BUFFER.append(line)
        if len(LOG_BUFFER) > 600:
            LOG_BUFFER.pop(0)


def get_logs(since_index=0):
    with LOG_LOCK:
        if since_index < len(LOG_BUFFER):
            return LOG_BUFFER[since_index:], len(LOG_BUFFER)
        return [], len(LOG_BUFFER)


def clear_logs():
    with LOG_LOCK:
        LOG_BUFFER.clear()


# ----------------- TÁC VỤ NỀN (BACKGROUND THREADS) -----------------

def run_background_task(task_name, target_func):
    global TASK_THREAD
    if CURRENT_TASK["is_running"]:
        return False, "Đang có tác vụ khác đang chạy!"

    STOP_EVENT.clear()
    CURRENT_TASK["name"] = task_name
    CURRENT_TASK["is_running"] = True

    def wrapper():
        try:
            target_func()
        except Exception as e:
            add_log(f"[Lỗi]: {e}")
        finally:
            CURRENT_TASK["name"] = ""
            CURRENT_TASK["is_running"] = False
            add_log(f"[Hoàn thành] Tác vụ '{task_name}' đã kết thúc.")

    TASK_THREAD = threading.Thread(target=wrapper, daemon=True)
    TASK_THREAD.start()
    return True, "Đã khởi chạy tác vụ."


def task_scan_friends():
    add_log("Bắt đầu quét danh sách bạn bè từ TikTok...")
    cfg = load_config()
    is_headless = cfg.get("headless", True)
    browser = None
    try:
        browser, wait = init_browser(headless=is_headless)
        login_with_cookies(browser, wait, log_cb=add_log)
        scan_friends(browser, wait, log_cb=add_log, should_stop=lambda: STOP_EVENT.is_set())
    finally:
        if browser:
            browser.quit()


def task_send_messages():
    add_log("Bắt đầu gửi tin nhắn duy trì streak cho bạn bè được chọn...")
    cfg = load_config()
    is_headless = cfg.get("headless", True)
    msg = cfg.get("message", "Streak")
    delay = cfg.get("delay_seconds", 3)
    browser = None
    try:
        browser, wait = init_browser(headless=is_headless)
        login_with_cookies(browser, wait, log_cb=add_log)
        send_messages_to_selected(
            browser, wait,
            message=msg,
            delay_sec=delay,
            log_cb=add_log,
            should_stop=lambda: STOP_EVENT.is_set()
        )
    finally:
        if browser:
            browser.quit()


def task_login_and_save_cookies():
    add_log("Đang mở trình duyệt Chrome để đăng nhập TikTok...")
    browser = None
    try:
        browser, wait = init_browser(headless=False)
        browser.get("https://www.tiktok.com/login/qrcode")
        add_log("Chrome đã mở. Hãy quét mã QR trên điện thoại hoặc đăng nhập.")
        add_log("Hệ thống sẽ tự động lưu cookies sau khi bạn đăng nhập thành công...")

        logged_in = False
        start_time = time.time()
        while time.time() - start_time < 180:
            if STOP_EVENT.is_set():
                add_log("Đã hủy quá trình đăng nhập.")
                return
            try:
                _ = browser.current_url
                cookies = browser.get_cookies() or []
                has_session = any(c and c.get("name") in ["sessionid", "sessionid_ss", "sid_tt"] for c in cookies)
                if has_session:
                    logged_in = True
                    break
            except Exception:
                add_log("Cửa sổ trình duyệt đã bị đóng.")
                break
            time.sleep(2)

        if logged_in:
            time.sleep(2)
            save_cookies(browser, "cookies.json")
            add_log("[Thành công] Đã lưu cookies vào file 'cookies.json'!")
        else:
            add_log("[Thông báo] Quá trình đăng nhập đã dừng hoặc chưa hoàn tất.")
    except Exception as e:
        add_log(f"[Lỗi]: {e}")
    finally:
        if browser:
            try:
                browser.quit()
            except Exception:
                pass


def reset_all_data():
    """Xóa toàn bộ dữ liệu bạn bè, cookies, cấu hình để đưa tool về trạng thái trắng."""
    # 1. Xóa danh sách bạn bè
    save_friends([])

    # 2. Xóa cookies
    if os.path.exists("cookies.json"):
        try:
            os.remove("cookies.json")
        except Exception:
            with open("cookies.json", "w", encoding="utf-8") as f:
                f.write("[]")

    # 3. Đưa cấu hình về mặc định
    default_cfg = {
        "message": "Streak",
        "delay_seconds": 3,
        "headless": True
    }
    save_config(default_cfg)

    # 4. Xóa nhật ký
    clear_logs()
    add_log("[Hệ thống] Đã xóa toàn bộ dữ liệu. Công cụ đã trở về trạng thái ban đầu.")


# ----------------- HTTP REQUEST HANDLER -----------------

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Tắt log mặc định của HTTP server để console sạch sẽ
        pass

    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw)
        return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            html_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Không tìm thấy file web/index.html")
            return

        # API: Status
        if path == "/api/status":
            has_cookies = os.path.exists("cookies.json") and os.path.getsize("cookies.json") > 50
            cookies_count = 0
            if has_cookies:
                try:
                    with open("cookies.json", "r", encoding="utf-8") as f:
                        cookies_count = len(json.load(f))
                except Exception:
                    pass

            self.send_json({
                "has_cookies": has_cookies,
                "cookies_count": cookies_count,
                "is_running": CURRENT_TASK["is_running"],
                "task_name": CURRENT_TASK["name"]
            })
            return

        # API: Config
        if path == "/api/config":
            self.send_json(load_config())
            return

        # API: Friends list
        if path == "/api/friends":
            self.send_json(load_friends())
            return

        # API: Logs
        if path == "/api/logs":
            query = parse_qs(parsed.query)
            since = int(query.get("since", [0])[0])
            logs, next_idx = get_logs(since)
            self.send_json({"logs": logs, "next_index": next_idx})
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API: Save Config
        if path == "/api/config":
            data = self.read_json_body()
            cfg = load_config()
            cfg.update(data)
            save_config(cfg)
            add_log("[Cấu hình] Đã cập nhật cài đặt.")
            self.send_json({"success": True})
            return

        # API: Toggle Friend Enabled
        if path == "/api/friends/toggle":
            data = self.read_json_body()
            username = data.get("username", "").lower()
            friends = load_friends()
            for f in friends:
                if f.get("username", "").lower() == username:
                    f["enabled"] = not f.get("enabled", True)
                    break
            save_friends(friends)
            self.send_json({"success": True})
            return

        # API: Select All / Deselect All
        if path == "/api/friends/select-all":
            data = self.read_json_body()
            state = bool(data.get("state", True))
            friends = load_friends()
            for f in friends:
                f["enabled"] = state
            save_friends(friends)
            add_log(f"Đã {'chọn tất cả' if state else 'bỏ chọn tất cả'} bạn bè.")
            self.send_json({"success": True})
            return

        # API: Add Friend
        if path == "/api/friends/add":
            data = self.read_json_body()
            u = data.get("username", "").strip().replace("@", "")
            nick = data.get("nickname", "").strip() or u
            if not u:
                self.send_json({"success": False, "error": "Username không hợp lệ"}, 400)
                return
            friends = load_friends()
            if any(f.get("username", "").lower() == u.lower() for f in friends):
                self.send_json({"success": False, "error": "Bạn bè này đã có trong danh sách"}, 400)
                return
            friends.append({
                "username": u,
                "nickname": nick,
                "enabled": True,
                "status": "Chưa gửi"
            })
            save_friends(friends)
            add_log(f"Đã thêm bạn bè thủ công: {nick} (@{u})")
            self.send_json({"success": True})
            return

        # API: Delete Friend
        if path == "/api/friends/delete":
            data = self.read_json_body()
            username = data.get("username", "").lower()
            friends = load_friends()
            friends = [f for f in friends if f.get("username", "").lower() != username]
            save_friends(friends)
            add_log(f"Đã xóa bạn bè: @{username}")
            self.send_json({"success": True})
            return

        # API: Start Scan
        if path == "/api/scan":
            ok, msg = run_background_task("Quét bạn bè từ TikTok", task_scan_friends)
            self.send_json({"success": ok, "message": msg})
            return

        # API: Start Send
        if path == "/api/send":
            friends = load_friends()
            selected = [f for f in friends if f.get("enabled", True)]
            if not selected:
                self.send_json({"success": False, "error": "Không có bạn bè nào được chọn để gửi tin nhắn!"})
                return
            ok, msg = run_background_task("Gửi tin nhắn Streak", task_send_messages)
            self.send_json({"success": ok, "message": msg})
            return

        # API: Stop Task
        if path == "/api/stop":
            STOP_EVENT.set()
            add_log("[Yêu cầu] Đang gửi tín hiệu dừng tác vụ...")
            self.send_json({"success": True})
            return

        # API: Login & Save Cookies
        if path == "/api/login-cookies":
            ok, msg = run_background_task("Đăng nhập TikTok", task_login_and_save_cookies)
            self.send_json({"success": ok, "message": msg})
            return

        # API: Reset All Data
        if path == "/api/reset-data":
            if CURRENT_TASK["is_running"]:
                self.send_json({"success": False, "error": "Không thể xóa dữ liệu khi đang có tác vụ chạy!"}, 400)
                return
            reset_all_data()
            self.send_json({"success": True})
            return

        self.send_error(404, "Not Found")


# ----------------- HÀM KHỞI TẠO VÀ CHẠY SERVER -----------------

def find_free_port(start_port=5000):
    for port in range(start_port, start_port + 30):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def main():
    port = find_free_port(5000)
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, DashboardHandler)

    url = f"http://localhost:{port}"
    print("=" * 65)
    print(" TIKTOK STREAK MANAGER - LOCAL WEB DASHBOARD (SHADCN LIGHT)")
    print("=" * 65)
    print(f"-> Máy chủ local đang chạy tại: {url}")
    print("-> Đang tự động mở Google Chrome...")
    print("-> Nhấn Ctrl + C để dừng máy chủ bất cứ lúc nào.")
    print("-" * 65)

    add_log(f"Máy chủ cục bộ đã khởi động tại {url}")

    # Tự động mở Chrome hoặc trình duyệt mặc định
    threading.Thread(target=lambda: (time.sleep(0.8), webbrowser.open(url)), daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang tắt máy chủ...")
    finally:
        httpd.server_close()
        print("Máy chủ đã dừng.")


if __name__ == "__main__":
    main()
