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
    load_accounts,
    save_accounts,
    get_account,
    create_account,
    update_account,
    delete_account,
    get_account_cookie_path,
    parse_cookie_data,
    import_cookies_to_account,
    load_config,
    save_config,
    load_friends,
    save_friends,
    init_browser,
    login_with_cookies,
    save_cookies,
    extract_logged_in_username,
    scan_friends,
    send_messages_to_selected
)

# ----------------- BIẾN TOÀN CỤC & NHẬT KÝ -----------------
LOG_BUFFER = []
LOG_LOCK = threading.Lock()
CURRENT_TASK = {"name": "", "is_running": False}
STOP_EVENT = threading.Event()
TASK_THREAD = None
ACTIVE_ACCOUNT_ID = "acc_1"


def add_log(message):
    timestamp = time.strftime("[%H:%M:%S]")
    line = f"{timestamp} {message}"
    print(line)
    with LOG_LOCK:
        LOG_BUFFER.append(line)
        if len(LOG_BUFFER) > 800:
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

def run_background_task(task_name, target_func, *args, **kwargs):
    global TASK_THREAD
    if CURRENT_TASK["is_running"]:
        return False, "Đang có tác vụ khác đang chạy! Vui lòng đợi hoặc bấm 'Dừng lại'."

    STOP_EVENT.clear()
    CURRENT_TASK["name"] = task_name
    CURRENT_TASK["is_running"] = True

    def wrapper():
        try:
            target_func(*args, **kwargs)
        except Exception as e:
            add_log(f"[Lỗi hệ thống]: {e}")
        finally:
            CURRENT_TASK["name"] = ""
            CURRENT_TASK["is_running"] = False
            add_log(f"[Hoàn thành] Tác vụ '{task_name}' đã kết thúc.")

    TASK_THREAD = threading.Thread(target=wrapper, daemon=True)
    TASK_THREAD.start()
    return True, "Đã khởi chạy tác vụ."


def task_scan_friends(account_id):
    acc = get_account(account_id)
    acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
    add_log(f"[{acc_name}] Bắt đầu quét danh sách bạn bè từ hộp thư TikTok...")
    cookie_file = get_account_cookie_path(account_id)

    if not (os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 50):
        add_log(f"[{acc_name}] [Lỗi] Chưa có cookies! Vui lòng đăng nhập tài khoản này trước.")
        return

    cfg = load_config(account_id)
    is_headless = cfg.get("headless", True)
    browser = None
    try:
        browser, wait = init_browser(headless=is_headless)
        login_with_cookies(browser, wait, cookie_file=cookie_file, log_cb=add_log)

        # Cập nhật thời gian đăng nhập lần cuối
        now_str = time.strftime("%H:%M:%S %d/%m/%Y")
        update_account(account_id, last_login=now_str)

        # Nhận diện username nếu chưa có
        if not acc.get("username"):
            u = extract_logged_in_username(browser)
            if u:
                update_account(account_id, username=u)
                add_log(f"[{acc_name}] Nhận diện username TikTok: @{u}")

        scan_friends(browser, wait, log_cb=add_log, should_stop=lambda: STOP_EVENT.is_set(), account_id=account_id)
    finally:
        if browser:
            try:
                browser.quit()
            except Exception:
                pass
            add_log(f"[{acc_name}] Đã đóng cửa sổ trình duyệt.")


def task_login_and_save_cookies(account_id):
    acc = get_account(account_id)
    acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
    add_log(f"[{acc_name}] Đang mở trình duyệt Chrome để đăng nhập TikTok...")
    browser = None
    try:
        browser, wait = init_browser(headless=False)
        browser.get("https://www.tiktok.com/login/qrcode")
        add_log(f"[{acc_name}] Cửa sổ Chrome đã mở. Hãy dùng ứng dụng TikTok quét mã QR trên điện thoại.")
        add_log(f"[{acc_name}] Hệ thống sẽ tự động lưu cookies sau khi quét thành công...")

        logged_in = False
        start_time = time.time()
        while time.time() - start_time < 180:
            if STOP_EVENT.is_set():
                add_log(f"[{acc_name}] Đã hủy quá trình đăng nhập.")
                return
            try:
                _ = browser.current_url
                cookies = browser.get_cookies() or []
                has_session = any(c and c.get("name") in ["sessionid", "sessionid_ss", "sid_tt"] for c in cookies)
                if has_session:
                    logged_in = True
                    break
            except Exception:
                add_log(f"[{acc_name}] Cửa sổ trình duyệt đã bị đóng.")
                break
            time.sleep(2)

        if logged_in:
            time.sleep(2)
            cookie_path = get_account_cookie_path(account_id)
            save_cookies(browser, cookie_path)

            now_str = time.strftime("%H:%M:%S %d/%m/%Y")
            update_data = {
                "last_login": now_str,
                "status": "Đã có cookies"
            }

            u = extract_logged_in_username(browser)
            if u:
                update_data["username"] = u
                add_log(f"[{acc_name}] Nhận diện username TikTok: @{u}")

            update_account(account_id, **update_data)
            add_log(f"[{acc_name}] [Thành công] Đã lưu cookies và cập nhật thời gian đăng nhập: {now_str}")
        else:
            add_log(f"[{acc_name}] [Thông báo] Quá trình đăng nhập đã dừng hoặc chưa hoàn tất.")
    except Exception as e:
        add_log(f"[{acc_name}] [Lỗi]: {e}")
    finally:
        if browser:
            try:
                browser.quit()
            except Exception:
                pass
            add_log(f"[{acc_name}] Đã đóng trình duyệt.")


def task_send_messages_sequential(account_ids=None):
    """
    Thực hiện chạy tuần tự từng tài khoản được chọn:
    Chạy xong tài khoản này -> tắt cửa sổ trình duyệt -> chuyển sang tài khoản khác.
    """
    if not account_ids:
        accounts = load_accounts()
        account_ids = [a["id"] for a in accounts if a.get("enabled", True)]

    if not account_ids:
        add_log("[Cảnh báo] Không có tài khoản nào được chọn để chạy!")
        return

    total = len(account_ids)
    add_log("=" * 62)
    add_log(f"[*] BẮT ĐẦU CHẠY TUẦN TỰ CHO {total} TÀI KHOẢN ĐÃ CHỌN")
    add_log("[*] Thao tác: Mở browser -> Gửi streak -> Tắt browser -> Chuyển tài khoản tiếp theo")
    add_log("=" * 62)

    success_accounts = 0
    for idx, acc_id in enumerate(account_ids, start=1):
        if STOP_EVENT.is_set():
            add_log("[Dừng] Người dùng đã yêu cầu dừng chuỗi tác vụ.")
            break

        acc = get_account(acc_id)
        if not acc:
            continue
        acc_name = acc.get("name", f"Tài khoản {idx}")

        add_log(f"\n------------------------------------------------------------")
        add_log(f">>> [{idx}/{total}] ĐANG XỬ LÝ: {acc_name} <<<")
        add_log(f"------------------------------------------------------------")

        cookie_file = get_account_cookie_path(acc_id)
        if not (os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 50):
            add_log(f"[{acc_name}] [Bỏ qua] Chưa có cookies! Vui lòng đăng nhập tài khoản này trước.")
            update_account(acc_id, status="Lỗi: Chưa có cookies")
            continue

        cfg = load_config(acc_id)
        msg = cfg.get("message", "Chào {nickname}, rep chuỗi streak nè {time}!")
        delay = cfg.get("delay_seconds", 3)
        headless = cfg.get("headless", True)

        friends = load_friends(acc_id)
        selected_friends = [f for f in friends if f.get("enabled", True)]
        if not selected_friends:
            add_log(f"[{acc_name}] [Bỏ qua] Không có bạn bè nào được chọn để gửi streak!")
            update_account(acc_id, status="Bỏ qua (0 bạn chọn)")
            continue

        update_account(acc_id, status="Đang chạy...")
        browser = None
        try:
            add_log(f"[{acc_name}] Mở trình duyệt Chrome (Chạy ẩn: {headless})...")
            browser, wait = init_browser(headless=headless)

            add_log(f"[{acc_name}] Nạp cookies và xác thực phiên...")
            login_with_cookies(browser, wait, cookie_file=cookie_file, log_cb=add_log)

            # Cập nhật thời gian đăng nhập lần cuối
            now_str = time.strftime("%H:%M:%S %d/%m/%Y")
            update_account(acc_id, last_login=now_str)

            # Nhận diện username nếu chưa có
            if not acc.get("username"):
                u = extract_logged_in_username(browser)
                if u:
                    update_account(acc_id, username=u)
                    add_log(f"[{acc_name}] Nhận diện TikTok: @{u}")

            # Gửi tin nhắn streak
            sent_count, target_count = send_messages_to_selected(
                browser, wait,
                message=msg,
                delay_sec=delay,
                log_cb=add_log,
                should_stop=lambda: STOP_EVENT.is_set(),
                account_id=acc_id
            )

            if STOP_EVENT.is_set():
                update_account(acc_id, status=f"Đã dừng ({sent_count}/{target_count} bạn)")
                add_log(f"[{acc_name}] Đã dừng tiến trình theo yêu cầu.")
            else:
                finish_time = time.strftime("%H:%M:%S %d/%m/%Y")
                update_account(acc_id, status=f"Hoàn thành ({sent_count}/{target_count} bạn)", last_run=finish_time)
                add_log(f"[{acc_name}] [Hoàn thành] Đã gửi tin nhắn cho {sent_count}/{target_count} bạn bè!")
                success_accounts += 1

        except Exception as e:
            add_log(f"[{acc_name}] [Lỗi]: {e}")
            update_account(acc_id, status=f"Lỗi: {e}")
        finally:
            if browser:
                add_log(f"[{acc_name}] Đang tắt cửa sổ trình duyệt...")
                try:
                    browser.quit()
                except Exception:
                    pass
                add_log(f"[{acc_name}] Đã tắt cửa sổ trình duyệt thành công.")

        if STOP_EVENT.is_set():
            break

        if idx < total:
            add_log(f"[*] Nghỉ 3 giây trước khi chuyển sang tài khoản kế tiếp...")
            for _ in range(3):
                if STOP_EVENT.is_set():
                    break
                time.sleep(1)

    add_log("\n" + "=" * 62)
    add_log(f"[KẾT THÚC] Đã hoàn thành quy trình chạy tuần tự: {success_accounts}/{total} tài khoản thành công.")
    add_log("=" * 62)


def reset_account_data(account_id=None):
    """Xóa dữ liệu của một tài khoản hoặc toàn bộ."""
    if account_id:
        acc = get_account(account_id)
        name = acc.get("name", account_id) if acc else account_id
        save_friends([], account_id)
        c_path = get_account_cookie_path(account_id)
        if os.path.exists(c_path):
            try:
                os.remove(c_path)
            except Exception:
                pass
        default_cfg = {
            "message": "Chào {nickname}, rep chuỗi streak nè {time}!",
            "delay_seconds": 3,
            "headless": True
        }
        save_config(default_cfg, account_id)
        update_account(account_id, last_login="Chưa đăng nhập", last_run="Chưa chạy", status="Chưa có cookies")
        add_log(f"[Hệ thống] Đã reset dữ liệu của tài khoản '{name}'.")
    else:
        accounts = load_accounts()
        for a in accounts:
            reset_account_data(a["id"])
        clear_logs()
        add_log("[Hệ thống] Đã reset dữ liệu của toàn bộ các tài khoản.")


# ----------------- HTTP REQUEST HANDLER -----------------

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw)
        return {}

    def do_GET(self):
        global ACTIVE_ACCOUNT_ID
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in ["/", "/index.html"]:
            html_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Không tìm thấy file web/index.html")
            return

        # API: Status
        if path == "/api/status":
            accounts = load_accounts()
            # Đảm bảo ACTIVE_ACCOUNT_ID hợp lệ
            if not any(a["id"] == ACTIVE_ACCOUNT_ID for a in accounts):
                if accounts:
                    ACTIVE_ACCOUNT_ID = accounts[0]["id"]

            self.send_json({
                "is_running": CURRENT_TASK["is_running"],
                "task_name": CURRENT_TASK["name"],
                "active_account_id": ACTIVE_ACCOUNT_ID,
                "accounts": accounts
            })
            return

        # API: Accounts list
        if path == "/api/accounts":
            self.send_json(load_accounts())
            return

        # API: Config của tài khoản
        if path == "/api/config":
            acc_id = query.get("account_id", [ACTIVE_ACCOUNT_ID])[0]
            self.send_json(load_config(acc_id))
            return

        # API: Friends list của tài khoản
        if path == "/api/friends":
            acc_id = query.get("account_id", [ACTIVE_ACCOUNT_ID])[0]
            self.send_json(load_friends(acc_id))
            return

        # API: Logs
        if path == "/api/logs":
            since = int(query.get("since", [0])[0])
            logs, next_idx = get_logs(since)
            self.send_json({"logs": logs, "next_index": next_idx})
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        global ACTIVE_ACCOUNT_ID
        parsed = urlparse(self.path)
        path = parsed.path

        # API: Create Account
        if path == "/api/accounts/create":
            data = self.read_json_body()
            name = data.get("name", "").strip() or "Tài khoản mới"
            cookies_raw = data.get("cookies_raw")
            try:
                new_acc = create_account(name, raw_cookies=cookies_raw)
                ACTIVE_ACCOUNT_ID = new_acc["id"]
                if cookies_raw:
                    add_log(f"Đã tạo tài khoản mới: '{name}' (đã nạp sẵn cookies).")
                else:
                    add_log(f"Đã tạo tài khoản mới: '{name}'")
                self.send_json({"success": True, "account": new_acc})
            except Exception as e:
                self.send_json({"success": False, "error": f"Lỗi tạo tài khoản: {e}"}, 400)
            return

        # API: Import Cookies to Account (Paste text hoặc JSON file content)
        if path == "/api/accounts/import-cookies":
            data = self.read_json_body()
            acc_id = data.get("account_id") or ACTIVE_ACCOUNT_ID
            cookies_raw = data.get("cookies_raw", "")
            if not cookies_raw:
                self.send_json({"success": False, "error": "Dữ liệu cookie trống"}, 400)
                return
            try:
                parsed = import_cookies_to_account(acc_id, cookies_raw)
                acc = get_account(acc_id)
                acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
                add_log(f"[{acc_name}] Đã nạp thành công {len(parsed)} cookies từ file/dán.")
                self.send_json({"success": True, "count": len(parsed)})
            except Exception as e:
                self.send_json({"success": False, "error": f"Lỗi nạp cookie: {e}"}, 400)
            return

        # API: Update Account (rename or toggle enabled)
        if path == "/api/accounts/update":
            data = self.read_json_body()
            acc_id = data.get("id")
            if not acc_id:
                self.send_json({"success": False, "error": "Thiếu account id"}, 400)
                return
            kwargs = {}
            if "name" in data:
                kwargs["name"] = data["name"].strip() or "Tài khoản"
            if "enabled" in data:
                kwargs["enabled"] = bool(data["enabled"])
            if kwargs:
                update_account(acc_id, **kwargs)
            self.send_json({"success": True})
            return

        # API: Delete Account
        if path == "/api/accounts/delete":
            data = self.read_json_body()
            acc_id = data.get("id")
            if CURRENT_TASK["is_running"]:
                self.send_json({"success": False, "error": "Không thể xóa tài khoản khi đang có tác vụ chạy!"}, 400)
                return
            acc = get_account(acc_id)
            acc_name = acc.get("name", acc_id) if acc else acc_id
            delete_account(acc_id)
            accounts = load_accounts()
            if ACTIVE_ACCOUNT_ID == acc_id and accounts:
                ACTIVE_ACCOUNT_ID = accounts[0]["id"]
            add_log(f"Đã xóa tài khoản: '{acc_name}'")
            self.send_json({"success": True})
            return

        # API: Toggle All Accounts (chọn tất cả / bỏ chọn tất cả để chạy)
        if path == "/api/accounts/toggle-all":
            data = self.read_json_body()
            state = bool(data.get("state", True))
            accounts = load_accounts()
            for a in accounts:
                a["enabled"] = state
            save_accounts(accounts)
            add_log(f"Đã {'chọn tất cả' if state else 'bỏ chọn tất cả'} tài khoản để chạy.")
            self.send_json({"success": True})
            return

        # API: Select Active Account
        if path == "/api/accounts/select-active":
            data = self.read_json_body()
            acc_id = data.get("id")
            if acc_id:
                ACTIVE_ACCOUNT_ID = acc_id
            self.send_json({"success": True, "active_account_id": ACTIVE_ACCOUNT_ID})
            return

        # API: Save Config cho tài khoản
        if path == "/api/config":
            data = self.read_json_body()
            apply_to_all = bool(data.get("apply_to_all", False))

            if apply_to_all:
                accounts = load_accounts()
                for a in accounts:
                    a_id = a.get("id")
                    if not a_id:
                        continue
                    cfg = load_config(a_id)
                    if "message" in data:
                        cfg["message"] = data["message"]
                    if "delay_seconds" in data:
                        cfg["delay_seconds"] = int(data["delay_seconds"])
                    if "headless" in data:
                        cfg["headless"] = bool(data["headless"])
                    save_config(cfg, a_id)

                root_cfg = load_config()
                if "message" in data:
                    root_cfg["message"] = data["message"]
                if "delay_seconds" in data:
                    root_cfg["delay_seconds"] = int(data["delay_seconds"])
                if "headless" in data:
                    root_cfg["headless"] = bool(data["headless"])
                save_config(root_cfg)

                add_log(f"Đã cập nhật cài đặt chung cho toàn bộ {len(accounts)} tài khoản.")
                self.send_json({"success": True, "applied_all": True})
                return

            acc_id = data.get("account_id", ACTIVE_ACCOUNT_ID)
            cfg = load_config(acc_id)
            if "message" in data:
                cfg["message"] = data["message"]
            if "delay_seconds" in data:
                cfg["delay_seconds"] = int(data["delay_seconds"])
            if "headless" in data:
                cfg["headless"] = bool(data["headless"])
            save_config(cfg, acc_id)
            acc = get_account(acc_id)
            acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
            add_log(f"[{acc_name}] Đã cập nhật cài đặt riêng.")
            self.send_json({"success": True})
            return

        # API: Toggle Friend Enabled cho tài khoản
        if path == "/api/friends/toggle":
            data = self.read_json_body()
            acc_id = data.get("account_id", ACTIVE_ACCOUNT_ID)
            username = data.get("username", "").lower()
            friends = load_friends(acc_id)
            for f in friends:
                if f.get("username", "").lower() == username:
                    f["enabled"] = not f.get("enabled", True)
                    break
            save_friends(friends, acc_id)
            self.send_json({"success": True})
            return

        # API: Select All / Deselect All bạn bè cho tài khoản
        if path == "/api/friends/select-all":
            data = self.read_json_body()
            acc_id = data.get("account_id", ACTIVE_ACCOUNT_ID)
            state = bool(data.get("state", True))
            friends = load_friends(acc_id)
            for f in friends:
                f["enabled"] = state
            save_friends(friends, acc_id)
            acc = get_account(acc_id)
            acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
            add_log(f"[{acc_name}] Đã {'chọn tất cả' if state else 'bỏ chọn tất cả'} bạn bè.")
            self.send_json({"success": True})
            return

        # API: Add Friend cho tài khoản
        if path == "/api/friends/add":
            data = self.read_json_body()
            acc_id = data.get("account_id", ACTIVE_ACCOUNT_ID)
            u = data.get("username", "").strip().replace("@", "")
            nick = data.get("nickname", "").strip() or u
            if not u:
                self.send_json({"success": False, "error": "Username không hợp lệ"}, 400)
                return
            friends = load_friends(acc_id)
            if any(f.get("username", "").lower() == u.lower() for f in friends):
                self.send_json({"success": False, "error": "Bạn bè này đã có trong danh sách"}, 400)
                return
            friends.append({
                "username": u,
                "nickname": nick,
                "enabled": True,
                "status": "Chưa gửi"
            })
            save_friends(friends, acc_id)
            acc = get_account(acc_id)
            acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
            add_log(f"[{acc_name}] Đã thêm bạn bè thủ công: {nick} (@{u})")
            self.send_json({"success": True})
            return

        # API: Delete Friend của tài khoản
        if path == "/api/friends/delete":
            data = self.read_json_body()
            acc_id = data.get("account_id", ACTIVE_ACCOUNT_ID)
            username = data.get("username", "").lower()
            friends = load_friends(acc_id)
            friends = [f for f in friends if f.get("username", "").lower() != username]
            save_friends(friends, acc_id)
            add_log(f"Đã xóa bạn bè: @{username}")
            self.send_json({"success": True})
            return

        # API: Start Scan bạn bè cho 1 tài khoản
        if path == "/api/scan":
            data = self.read_json_body()
            acc_id = data.get("account_id", ACTIVE_ACCOUNT_ID)
            acc = get_account(acc_id)
            acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
            ok, msg = run_background_task(f"Quét bạn bè ({acc_name})", task_scan_friends, acc_id)
            self.send_json({"success": ok, "message": msg})
            return

        # API: Start Sequential Streak Send (hỗ trợ chọn nhiều tài khoản)
        if path == "/api/send":
            data = self.read_json_body()
            account_ids = data.get("account_ids")
            if not account_ids:
                # Mặc định lấy các tài khoản được tick chọn
                accounts = load_accounts()
                account_ids = [a["id"] for a in accounts if a.get("enabled", True)]

            if not account_ids:
                self.send_json({"success": False, "error": "Vui lòng tích chọn ít nhất 1 tài khoản để chạy!"}, 400)
                return

            # Nếu người dùng muốn đồng bộ nội dung tin nhắn hiện tại cho các tài khoản chạy
            sync_message = data.get("sync_message")
            if sync_message:
                for a_id in account_ids:
                    cfg = load_config(a_id)
                    cfg["message"] = sync_message
                    save_config(cfg, a_id)
                add_log(f"Đã áp dụng mẫu tin nhắn mới cho {len(account_ids)} tài khoản trước khi gửi.")

            task_title = f"Chạy tuần tự {len(account_ids)} tài khoản"
            ok, msg = run_background_task(task_title, task_send_messages_sequential, account_ids)
            self.send_json({"success": ok, "message": msg})
            return

        # API: Stop Task
        if path == "/api/stop":
            STOP_EVENT.set()
            add_log("[Yêu cầu] Đang gửi tín hiệu dừng tác vụ khẩn cấp...")
            self.send_json({"success": True})
            return

        # API: Login & Save Cookies cho 1 tài khoản
        if path == "/api/login-cookies":
            data = self.read_json_body()
            acc_id = data.get("account_id", ACTIVE_ACCOUNT_ID)
            acc = get_account(acc_id)
            acc_name = acc.get("name", "Tài khoản") if acc else "Tài khoản"
            ok, msg = run_background_task(f"Đăng nhập TikTok ({acc_name})", task_login_and_save_cookies, acc_id)
            self.send_json({"success": ok, "message": msg})
            return

        # API: Reset Data
        if path == "/api/reset-data":
            if CURRENT_TASK["is_running"]:
                self.send_json({"success": False, "error": "Không thể xóa dữ liệu khi đang có tác vụ chạy!"}, 400)
                return
            data = self.read_json_body()
            acc_id = data.get("account_id")
            reset_account_data(acc_id)
            self.send_json({"success": True})
            return

        # API: Clear Logs
        if path == "/api/logs/clear":
            clear_logs()
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
    print(" TIKTOK STREAK MANAGER - MULTI-ACCOUNT LOCAL DASHBOARD")
    print("=" * 65)
    print(f"-> Máy chủ local đang chạy tại: {url}")
    print("-> Đang tự động mở Google Chrome...")
    print("-> Nhấn Ctrl + C để dừng máy chủ bất cứ lúc nào.")
    print("-" * 65)

    add_log(f"Máy chủ cục bộ đã khởi động tại {url}")

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
