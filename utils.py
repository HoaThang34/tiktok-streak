from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import csv
import os
import json
import sys
import shutil
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

LEGACY_CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LEGACY_FRIENDS_FILE = os.path.join(BASE_DIR, "friends.json")
LEGACY_FRIENDS_CSV = os.path.join(BASE_DIR, "friends.csv")
LEGACY_COOKIES_FILE = os.path.join(BASE_DIR, "cookies.json")


# ----------------------------
# QUẢN LÝ THƯ MỤC & ĐƯỜNG DẪN TÀI KHOẢN
# ----------------------------

def get_account_dir(account_id: str) -> str:
    path = os.path.join(ACCOUNTS_DIR, account_id)
    os.makedirs(path, exist_ok=True)
    return path


def get_account_cookie_path(account_id: str) -> str:
    return os.path.join(get_account_dir(account_id), "cookies.json")


def get_account_config_path(account_id: str) -> str:
    return os.path.join(get_account_dir(account_id), "config.json")


def get_account_friends_path(account_id: str) -> str:
    return os.path.join(get_account_dir(account_id), "friends.json")


def get_account_friends_csv_path(account_id: str) -> str:
    return os.path.join(get_account_dir(account_id), "friends.csv")


def ensure_data_migration():
    """
    Tự động di chuyển dữ liệu cũ (cookies.json, config.json, friends.json)
    sang hệ thống đa tài khoản (accounts/) mà không làm mất dữ liệu hiện tại.
    """
    os.makedirs(ACCOUNTS_DIR, exist_ok=True)

    if not os.path.exists(ACCOUNTS_FILE):
        accounts = []
        has_legacy = (
            (os.path.exists(LEGACY_COOKIES_FILE) and os.path.getsize(LEGACY_COOKIES_FILE) > 50) or
            (os.path.exists(LEGACY_FRIENDS_FILE) and os.path.getsize(LEGACY_FRIENDS_FILE) > 10)
        )
        acc_id = "acc_1"
        get_account_dir(acc_id)

        if has_legacy:
            if os.path.exists(LEGACY_COOKIES_FILE):
                try:
                    shutil.copy2(LEGACY_COOKIES_FILE, get_account_cookie_path(acc_id))
                except Exception:
                    pass
            if os.path.exists(LEGACY_CONFIG_FILE):
                try:
                    shutil.copy2(LEGACY_CONFIG_FILE, get_account_config_path(acc_id))
                except Exception:
                    pass
            if os.path.exists(LEGACY_FRIENDS_FILE):
                try:
                    shutil.copy2(LEGACY_FRIENDS_FILE, get_account_friends_path(acc_id))
                except Exception:
                    pass
            if os.path.exists(LEGACY_FRIENDS_CSV):
                try:
                    shutil.copy2(LEGACY_FRIENDS_CSV, get_account_friends_csv_path(acc_id))
                except Exception:
                    pass

            last_time = ""
            try:
                with open(LEGACY_FRIENDS_FILE, "r", encoding="utf-8") as f:
                    fdata = json.load(f)
                    for item in fdata:
                        st = item.get("status", "")
                        if "Đã gửi (" in st:
                            last_time = st.split("Đã gửi (")[1].rstrip(")")
                            break
            except Exception:
                pass

            accounts.append({
                "id": acc_id,
                "name": "Tài khoản 1",
                "username": "",
                "last_login": last_time if last_time else "Đã nạp phiên cũ",
                "last_run": last_time if last_time else "Chưa chạy",
                "status": "Sẵn sàng",
                "enabled": True
            })
        else:
            accounts.append({
                "id": acc_id,
                "name": "Tài khoản 1",
                "username": "",
                "last_login": "Chưa đăng nhập",
                "last_run": "Chưa chạy",
                "status": "Chưa có cookies",
                "enabled": True
            })

        save_accounts(accounts)


# ----------------------------
# QUẢN LÝ DANH SÁCH TÀI KHOẢN (ACCOUNTS)
# ----------------------------

def load_accounts():
    """
    Tải danh sách tài khoản từ accounts.json.
    Bổ sung thông tin động: has_cookies, cookies_count, friends_count, selected_friends_count.
    """
    ensure_data_migration()
    accounts = []
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
        except Exception:
            accounts = []

    if not accounts:
        accounts = [{
            "id": "acc_1",
            "name": "Tài khoản 1",
            "username": "",
            "last_login": "Chưa đăng nhập",
            "last_run": "Chưa chạy",
            "status": "Chưa có cookies",
            "enabled": True
        }]
        save_accounts(accounts)

    # Làm giàu thông tin trạng thái
    for acc in accounts:
        acc_id = acc.get("id", "acc_1")
        cookie_path = get_account_cookie_path(acc_id)
        has_cookies = os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 50
        cookies_count = 0
        if has_cookies:
            try:
                with open(cookie_path, "r", encoding="utf-8") as f:
                    cookies_count = len(json.load(f))
            except Exception:
                has_cookies = False

        acc["has_cookies"] = has_cookies
        acc["cookies_count"] = cookies_count

        friends = load_friends(acc_id)
        acc["friends_count"] = len(friends)
        acc["selected_friends_count"] = len([f for f in friends if f.get("enabled", True)])

        if "last_login" not in acc:
            acc["last_login"] = "Chưa đăng nhập"
        if "last_run" not in acc:
            acc["last_run"] = "Chưa chạy"
        if "status" not in acc:
            acc["status"] = "Sẵn sàng" if has_cookies else "Chưa có cookies"
        if "enabled" not in acc:
            acc["enabled"] = True

    return accounts


def save_accounts(accounts):
    """Lưu danh sách tài khoản vào accounts.json."""
    # Chỉ lưu các trường dữ liệu cần thiết
    clean_list = []
    for acc in accounts:
        clean_list.append({
            "id": acc.get("id"),
            "name": acc.get("name", "Tài khoản"),
            "username": acc.get("username", ""),
            "last_login": acc.get("last_login", "Chưa đăng nhập"),
            "last_run": acc.get("last_run", "Chưa chạy"),
            "status": acc.get("status", "Sẵn sàng"),
            "enabled": bool(acc.get("enabled", True))
        })
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_list, f, indent=4, ensure_ascii=False)


def get_account(account_id: str):
    """Tìm tài khoản theo id."""
    accounts = load_accounts()
    for acc in accounts:
        if acc.get("id") == account_id:
            return acc
    return accounts[0] if accounts else None


def parse_cookie_data(raw_data):
    """
    Phân tích và chuẩn hóa cookies từ nhiều định dạng:
    1. JSON array (chuẩn Cookie-Editor, EditThisCookie, Selenium)
    2. JSON object {name: value}
    3. Chuỗi Header (name1=val1; name2=val2)
    4. Netscape format (tab-separated)
    Trả về danh sách dict hợp lệ cho Selenium.
    """
    if not raw_data:
        raise ValueError("Dữ liệu cookie trống.")

    cookies = []

    # 1. Nếu là list sẵn
    if isinstance(raw_data, list):
        parsed_list = raw_data
    elif isinstance(raw_data, dict):
        parsed_list = [{"name": k, "value": str(v), "domain": ".tiktok.com", "path": "/"} for k, v in raw_data.items()]
    else:
        raw_str = str(raw_data).strip()
        # Thử parse JSON
        if raw_str.startswith("[") or raw_str.startswith("{"):
            try:
                loaded = json.loads(raw_str)
                if isinstance(loaded, list):
                    parsed_list = loaded
                elif isinstance(loaded, dict):
                    parsed_list = [{"name": k, "value": str(v), "domain": ".tiktok.com", "path": "/"} for k, v in loaded.items()]
                else:
                    parsed_list = []
            except Exception:
                parsed_list = []
        else:
            parsed_list = []

        # Nếu không phải JSON, thử Netscape format hoặc cookie header string
        if not parsed_list:
            lines = raw_str.splitlines()
            netscape_found = False
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    netscape_found = True
                    domain, flag, path, secure, exp, name, val = parts[:7]
                    cookie_dict = {
                        "name": name.strip(),
                        "value": val.strip(),
                        "domain": domain.strip(),
                        "path": path.strip() or "/"
                    }
                    try:
                        cookie_dict["expiry"] = int(float(exp.strip()))
                    except Exception:
                        pass
                    cookie_dict["secure"] = secure.strip().lower() == "true"
                    cookies.append(cookie_dict)

            # Nếu không phải Netscape, thử dạng Header: name1=val1; name2=val2
            if not netscape_found:
                single_line = " ".join(lines)
                pairs = single_line.split(";")
                for p in pairs:
                    if "=" in p:
                        k, v = p.strip().split("=", 1)
                        if k.strip():
                            cookies.append({
                                "name": k.strip(),
                                "value": v.strip(),
                                "domain": ".tiktok.com",
                                "path": "/"
                            })
                return cookies

    # Chuẩn hóa parsed_list
    for c in parsed_list:
        if isinstance(c, dict) and "name" in c and "value" in c:
            clean = {
                "name": str(c["name"]).strip(),
                "value": str(c["value"]).strip(),
                "domain": str(c.get("domain") or ".tiktok.com").strip(),
                "path": str(c.get("path") or "/").strip(),
            }
            if "expiry" in c:
                try:
                    clean["expiry"] = int(c["expiry"])
                except Exception:
                    pass
            elif "expirationDate" in c:
                try:
                    clean["expiry"] = int(c["expirationDate"])
                except Exception:
                    pass
            if "secure" in c:
                clean["secure"] = bool(c["secure"])
            if "httpOnly" in c:
                clean["httpOnly"] = bool(c["httpOnly"])
            if "sameSite" in c and c["sameSite"] in ["Strict", "Lax", "None"]:
                clean["sameSite"] = c["sameSite"]
            cookies.append(clean)

    if not cookies:
        raise ValueError("Không tìm thấy cookies hợp lệ trong dữ liệu cung cấp.")

    return cookies


def import_cookies_to_account(account_id: str, raw_cookies):
    """
    Nạp cookies vào tài khoản từ văn bản dán (JSON hoặc chuỗi header) hoặc nội dung file JSON.
    Cập nhật trạng thái và thời gian đăng nhập.
    """
    parsed = parse_cookie_data(raw_cookies)
    if not parsed:
        raise ValueError("Không tìm thấy cookies hợp lệ.")

    cookie_path = get_account_cookie_path(account_id)
    with open(cookie_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=4)

    now_str = time.strftime("%H:%M:%S %d/%m/%Y")
    update_account(
        account_id,
        last_login=now_str,
        status="Sẵn sàng"
    )
    return parsed


def create_account(name="Tài khoản mới", raw_cookies=None):
    """Tạo tài khoản mới và thiết lập thư mục riêng (hỗ trợ kèm cookies nạp sẵn)."""
    accounts = load_accounts()
    acc_id = f"acc_{int(time.time() * 1000)}"
    get_account_dir(acc_id)

    # Khởi tạo config mặc định riêng
    default_cfg = {
        "message": "Chào {nickname}, rep chuỗi streak nè {time}!",
        "delay_seconds": 3,
        "headless": True
    }
    with open(get_account_config_path(acc_id), "w", encoding="utf-8") as f:
        json.dump(default_cfg, f, indent=4, ensure_ascii=False)

    # Khởi tạo friends rỗng
    with open(get_account_friends_path(acc_id), "w", encoding="utf-8") as f:
        json.dump([], f, indent=4, ensure_ascii=False)

    last_login = "Chưa đăng nhập"
    status = "Chưa có cookies"

    if raw_cookies:
        try:
            parsed = parse_cookie_data(raw_cookies)
            if parsed:
                with open(get_account_cookie_path(acc_id), "w", encoding="utf-8") as f:
                    json.dump(parsed, f, indent=4)
                last_login = time.strftime("%H:%M:%S %d/%m/%Y")
                status = "Sẵn sàng"
        except Exception:
            pass

    new_acc = {
        "id": acc_id,
        "name": name,
        "username": "",
        "last_login": last_login,
        "last_run": "Chưa chạy",
        "status": status,
        "enabled": True
    }
    accounts.append(new_acc)
    save_accounts(accounts)
    return new_acc


def update_account(account_id: str, **kwargs):
    """Cập nhật các trường thông tin của một tài khoản."""
    accounts = load_accounts()
    for acc in accounts:
        if acc.get("id") == account_id:
            for k, v in kwargs.items():
                acc[k] = v
            break
    save_accounts(accounts)


def delete_account(account_id: str):
    """Xóa tài khoản và thư mục dữ liệu của tài khoản đó."""
    accounts = load_accounts()
    accounts = [a for a in accounts if a.get("id") != account_id]

    # Nếu xóa hết tất cả tài khoản, tự động tạo 1 tài khoản mới trắng tinh
    if not accounts:
        new_id = f"acc_{int(time.time() * 1000)}"
        get_account_dir(new_id)
        default_cfg = {
            "message": "Chào {nickname}, rep chuỗi streak nè {time}!",
            "delay_seconds": 3,
            "headless": True
        }
        with open(get_account_config_path(new_id), "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=4, ensure_ascii=False)
        with open(get_account_friends_path(new_id), "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        accounts = [{
            "id": new_id,
            "name": "Tài khoản 1",
            "username": "",
            "last_login": "Chưa đăng nhập",
            "last_run": "Chưa chạy",
            "status": "Chưa có cookies",
            "enabled": True
        }]

    save_accounts(accounts)

    target_dir = os.path.join(ACCOUNTS_DIR, account_id)
    if os.path.exists(target_dir):
        try:
            shutil.rmtree(target_dir)
        except Exception:
            pass


# ----------------------------
# CẤU HÌNH & BẠN BÈ THEO TÀI KHOẢN
# ----------------------------

def load_config(account_id: str = None):
    """Tải cấu hình riêng của một tài khoản."""
    default_config = {
        "message": os.getenv("MESSAGE", "Chào {nickname}, rep chuỗi streak nè {time}!"),
        "delay_seconds": 3,
        "headless": True
    }

    config_path = get_account_config_path(account_id) if account_id else LEGACY_CONFIG_FILE
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass
    elif os.path.exists(LEGACY_CONFIG_FILE):
        try:
            with open(LEGACY_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass

    return default_config


def save_config(config: dict, account_id: str = None):
    """Lưu cấu hình riêng cho tài khoản và đồng bộ nhẹ."""
    config_path = get_account_config_path(account_id) if account_id else LEGACY_CONFIG_FILE
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    # Đồng bộ sang root config.json để các tác vụ cũ luôn đọc được
    try:
        with open(LEGACY_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def render_message_template(template: str, friend: dict = None) -> str:
    """
    Thay thế các thẻ template thời gian và thông tin bạn bè vào nội dung tin nhắn.
    Hỗ trợ:
      - {time}: Giờ:Phút:Giây (VD: 15:30:45)
      - {date}: Ngày/Tháng/Năm (VD: 30/09/2026)
      - {datetime}: Ngày giờ đầy đủ (VD: 15:30:45 30/09/2026)
      - {hour}: Giờ hiện tại (VD: 15)
      - {minute}: Phút hiện tại (VD: 30)
      - {second}: Giây hiện tại (VD: 45)
      - {nickname}: Tên hiển thị của người nhận
      - {username}: TikTok Handle của người nhận
    """
    if not template:
        return ""

    now = time.localtime()
    friend = friend or {}
    nick = friend.get("nickname") or friend.get("username") or ""
    uname = friend.get("username") or ""
    clean_uname = uname.replace("[Nhóm]", "").strip() if uname.startswith("[Nhóm]") else uname

    tags = {
        "{time}": time.strftime("%H:%M:%S", now),
        "{date}": time.strftime("%d/%m/%Y", now),
        "{datetime}": time.strftime("%H:%M:%S %d/%m/%Y", now),
        "{hour}": time.strftime("%H", now),
        "{minute}": time.strftime("%M", now),
        "{second}": time.strftime("%S", now),
        "{nickname}": nick,
        "{username}": clean_uname if clean_uname else nick,
    }

    result = template
    for tag, val in tags.items():
        result = result.replace(tag, str(val))
    return result


def load_friends(account_id: str = None):
    """
    Tải danh sách bạn bè riêng của tài khoản.
    Trả về danh sách dict: [{'username': str, 'nickname': str, 'enabled': bool, 'status': str}]
    """
    friends = []
    friends_path = get_account_friends_path(account_id) if account_id else LEGACY_FRIENDS_FILE

    if os.path.exists(friends_path):
        try:
            with open(friends_path, "r", encoding="utf-8") as f:
                friends = json.load(f)
                return friends
        except Exception:
            pass

    # Fallback legacy friends
    if not account_id and os.path.exists(LEGACY_FRIENDS_FILE):
        try:
            with open(LEGACY_FRIENDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return friends


def save_friends(friends: list, account_id: str = None):
    """Lưu danh sách bạn bè vào cả JSON và CSV của tài khoản."""
    friends_path = get_account_friends_path(account_id) if account_id else LEGACY_FRIENDS_FILE
    friends_csv_path = get_account_friends_csv_path(account_id) if account_id else LEGACY_FRIENDS_CSV

    # 1. Lưu JSON
    with open(friends_path, "w", encoding="utf-8") as f:
        json.dump(friends, f, indent=4, ensure_ascii=False)

    # 2. Đồng bộ sang CSV
    try:
        with open(friends_csv_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Username", "Nickname", "Enabled", "Status"])
            for item in friends:
                writer.writerow([
                    item.get("username", ""),
                    item.get("nickname", item.get("username", "")),
                    item.get("enabled", True),
                    item.get("status", "Chưa gửi")
                ])
    except Exception:
        pass

    # Chỉ lưu ra file root nếu không có account_id (chế độ legacy đơn tài khoản)
    if not account_id:
        try:
            with open(LEGACY_FRIENDS_FILE, "w", encoding="utf-8") as f:
                json.dump(friends, f, indent=4, ensure_ascii=False)
        except Exception:
            pass


# ----------------------------
# SELENIUM & BROWSER HELPER
# ----------------------------

def init_browser(headless=True):
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        chrome_options.add_argument("--headless=new")
    browser = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(browser, 20)
    return browser, wait


def save_cookies(browser, cookie_file="cookies.json"):
    cookies = browser.get_cookies()
    with open(cookie_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4)
    print(f"[OK] Đã lưu {len(cookies)} cookies vào file '{cookie_file}' thành công!")


def login_with_cookies(browser, wait, cookie_file="cookies.json", log_cb=print):
    if not os.path.exists(cookie_file):
        raise FileNotFoundError(f"Không tìm thấy file cookies: '{cookie_file}'. Vui lòng đăng nhập trước.")

    log_cb("[1/3] Đang mở trang TikTok...")
    browser.get("https://www.tiktok.com")
    time.sleep(2)

    log_cb(f"[2/3] Đang nạp cookies...")
    with open(cookie_file, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    for c in cookies:
        clean_cookie = {
            "name": c["name"],
            "value": c["value"],
            "path": c.get("path", "/"),
        }
        if "domain" in c and c["domain"]:
            clean_cookie["domain"] = c["domain"]
        if "secure" in c:
            clean_cookie["secure"] = bool(c["secure"])
        if "httpOnly" in c:
            clean_cookie["httpOnly"] = bool(c["httpOnly"])
        if "expiry" in c:
            clean_cookie["expiry"] = int(c["expiry"])
        elif "expirationDate" in c:
            clean_cookie["expiry"] = int(c["expirationDate"])
        if "sameSite" in c and c["sameSite"] in ["Strict", "Lax", "None"]:
            clean_cookie["sameSite"] = c["sameSite"]

        try:
            browser.add_cookie(clean_cookie)
        except Exception:
            pass

    log_cb("[3/3] Đang chuyển đến hộp thư TikTok để xác thực phiên đăng nhập...")
    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)
    log_cb("[OK] Đăng nhập bằng cookies thành công!")


def extract_logged_in_username(browser):
    """Trích xuất username của tài khoản đang đăng nhập trên TikTok."""
    try:
        # Thử tìm avatar/link profile
        selectors = [
            "//a[contains(@href, '/@') and (@data-e2e='profile-icon' or contains(@class, 'avatar') or contains(@class, 'Avatar'))]",
            "//header//a[contains(@href, '/@')]",
            "//nav//a[contains(@href, '/@')]"
        ]
        for sel in selectors:
            try:
                elems = browser.find_elements(By.XPATH, sel)
                for el in elems:
                    href = el.get_attribute("href") or ""
                    m = re.search(r"/@([^/?#]+)", href)
                    if m and m.group(1).lower() not in ["login", "tiktokstudio"]:
                        return m.group(1)
            except Exception:
                continue

        # Thử JavaScript
        u = browser.execute_script("""
            try {
                const link = document.querySelector('header a[href*="/@"], nav a[href*="/@"], a[data-e2e="profile-icon"]');
                if (link && link.href) {
                    const m = link.href.match(/\\/@([^/?#]+)/);
                    if (m) return m[1];
                }
            } catch(e) {}
            return '';
        """)
        if u and u.lower() not in ["login", "tiktokstudio"]:
            return u
    except Exception:
        pass
    return ""


def extract_chat_details(browser, fallback_nickname=""):
    """
    Trích xuất thông tin chi tiết của cuộc trò chuyện đang mở trên TikTok.
    Trả về dict:
    {
        "is_group": bool,        # True nếu là nhóm chat
        "username": str,         # TikTok @handle nếu là người, hoặc [Nhóm] <Tên nhóm>
        "title": str             # Tiêu đề chat trong Header hoặc fallback nickname
    }
    """
    info = {
        "is_group": False,
        "username": "",
        "title": fallback_nickname.strip()
    }

    # 1. Tìm Header của khung chat bên phải
    header_selectors = [
        "//*[contains(@class, 'ChatHeader')]",
        "//*[contains(@class, 'chat-header')]",
        "//*[contains(@class, 'HeaderWrapper')]",
        "//*[contains(@class, 'ConversationHeader')]",
        "//*[@data-e2e='chat-header']"
    ]
    header = None
    for h_sel in header_selectors:
        try:
            h_elems = browser.find_elements(By.XPATH, h_sel)
            for h in h_elems:
                if h.is_displayed():
                    header = h
                    break
            if header:
                break
        except Exception:
            continue

    header_text = header.text.strip() if header else ""
    if header_text:
        lines = [line.strip() for line in header_text.splitlines() if line.strip()]
        if lines:
            info["title"] = lines[0]

    # 2. Kiểm tra dấu hiệu NHÓM CHAT (Group Chat)
    is_group = False
    lower_header = header_text.lower()
    group_keywords = ["thành viên", "members", "member", "người", "participants"]
    if any(kw in lower_header for kw in group_keywords):
        is_group = True

    if not is_group and header:
        try:
            # Nhóm chat thường có icon nhóm hoặc avatar nhóm đặc thù
            group_indicators = header.find_elements(
                By.XPATH,
                ".//*[contains(@class, 'Group') or contains(@class, 'group') or contains(@aria-label, 'nhóm') or contains(@aria-label, 'group')]"
            )
            if group_indicators:
                is_group = True
        except Exception:
            pass

    # 3. Trích xuất username người nhận từ Header
    extracted_user = ""
    if header:
        try:
            # Ưu tiên thẻ a có href chứa /@ trong Header
            header_links = header.find_elements(By.XPATH, ".//a[contains(@href, '/@')]")
            for l in reversed(header_links):
                href = l.get_attribute("href") or ""
                m = re.search(r"/@([^/?#]+)", href)
                if m:
                    u = m.group(1).strip()
                    if u.lower() not in ["login", "tiktokstudio"] and not href.endswith(("/video/", "/photo/")):
                        extracted_user = u
                        break
        except Exception:
            pass

        # Nếu chưa tìm thấy thẻ a, tìm cú pháp @handle trong text của Header
        if not extracted_user:
            m = re.search(r"@([a-zA-Z0-9._]+)", header_text)
            if m:
                extracted_user = m.group(1).strip()

    # Nếu trong Header hoàn toàn không có link profile cá nhân /@ và không có @handle:
    # -> Đây là NHÓM CHAT!
    if not extracted_user:
        is_group = True

    info["is_group"] = is_group
    chat_title = info["title"] or fallback_nickname.strip() or "Nhóm TikTok"
    info["title"] = chat_title

    if is_group:
        info["username"] = f"[Nhóm] {chat_title}"
    else:
        info["username"] = extracted_user

    return info


def extract_current_chat_username(browser):
    """
    Trích xuất username hoặc định danh của cuộc trò chuyện đang mở (tương thích ngược).
    """
    details = extract_chat_details(browser)
    return details.get("username", "")


def find_matching_target(all_friends, chat_details, elem_nickname):
    """
    Tìm target trong danh sách bạn bè được chọn (enabled == True) khớp với cuộc trò chuyện hiện tại.
    Hỗ trợ đối chiếu chuẩn xác cho cả:
      - Chat 1-1 (ưu tiên theo @username cá nhân)
      - Nhóm chat (ưu tiên theo Tên nhóm / Nickname)
      - Nhóm chat đã quét từ phiên bản cũ (vẫn khớp theo Nickname)
    """
    selected_targets = [f for f in all_friends if f.get("enabled", True)]
    if not selected_targets:
        return None

    elem_nick_clean = elem_nickname.strip().lower()
    chat_title_clean = chat_details.get("title", "").strip().lower()
    chat_user_clean = chat_details.get("username", "").strip().lower()
    is_group = chat_details.get("is_group", False)

    # 1. Nếu là người bình thường và có username cá nhân chuẩn
    if not is_group and chat_user_clean and not chat_user_clean.startswith("[nhóm]"):
        for target in selected_targets:
            t_user = target.get("username", "").strip().lower()
            if t_user and t_user == chat_user_clean:
                return target

    # 2. Nếu là Nhóm Chat: So sánh theo TÊN NHÓM (Nickname)
    for target in selected_targets:
        t_nick = target.get("nickname", "").strip().lower()
        t_user = target.get("username", "").strip().lower()

        # Khớp theo Tên nhóm với elem_nickname hoặc title trong header
        if t_nick and (t_nick == elem_nick_clean or t_nick == chat_title_clean):
            return target

        # Khớp theo Username có dạng [Nhóm] <Tên>
        if t_user and (t_user == f"[nhóm] {elem_nick_clean}" or t_user == f"[nhóm] {chat_title_clean}"):
            return target

        # Khớp nếu username của target trùng với username trích xuất được
        if chat_user_clean and t_user == chat_user_clean:
            return target

    # 3. Dự phòng cho trường hợp tên nhóm có chứa ký tự phụ hoặc khoảng trắng lệch nhẹ
    if is_group and elem_nick_clean:
        for target in selected_targets:
            t_nick = target.get("nickname", "").strip().lower()
            if t_nick and (t_nick in elem_nick_clean or elem_nick_clean in t_nick) and len(t_nick) >= 3:
                return target

    # 4. Dự phòng cho chat cá nhân nếu đổi username nhưng nickname giữ nguyên
    if not is_group and elem_nick_clean:
        for target in selected_targets:
            t_nick = target.get("nickname", "").strip().lower()
            if t_nick and (t_nick == elem_nick_clean or t_nick == chat_title_clean):
                return target

    return None


# ----------------------------
# QUÉT BẠN BÈ & NHÓM CHAT (SCAN FRIENDS & GROUPS)
# ----------------------------

def scroll_chat_list_container(browser, step_pixels=800):
    """
    Cuộn thanh cuộn của danh sách cuộc trò chuyện bên trái xuống dưới để kích hoạt TikTok nạp thêm tin nhắn.
    Trả về dict thông tin kết quả: {"found": bool, "scrolled": bool, "at_bottom": bool}.
    """
    script = """
    let container = null;
    const selectors = [
        '[data-e2e="chat-list"]',
        '[data-e2e="conversation-list"]',
        '[class*="ChatList"]',
        '[class*="ConversationList"]',
        '[class*="MessageList"]',
        'aside [class*="list"]',
        'div[role="list"]'
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && (el.scrollHeight > el.clientHeight || window.getComputedStyle(el).overflowY === 'auto' || window.getComputedStyle(el).overflowY === 'scroll')) {
            container = el;
            break;
        }
    }
    if (!container) {
        const items = document.querySelectorAll('[data-e2e="conversation-item"], [data-e2e="chat-list-item"], [class*="PInfoNickname"], [class*="Nickname"]');
        if (items.length > 0) {
            let p = items[items.length - 1].parentElement;
            while (p && p !== document.body) {
                const st = window.getComputedStyle(p);
                if ((st.overflowY === 'auto' || st.overflowY === 'scroll') && p.scrollHeight > p.clientHeight) {
                    container = p;
                    break;
                }
                p = p.parentElement;
            }
        }
    }
    if (container) {
        const oldTop = container.scrollTop;
        container.scrollTop = container.scrollHeight;
        const scrolled = container.scrollTop > oldTop;
        const atBottom = (container.scrollTop + container.clientHeight >= container.scrollHeight - 30);
        return { found: true, scrolled: scrolled, at_bottom: atBottom };
    }
    const oldY = window.scrollY;
    window.scrollBy(0, arguments[0] || 800);
    return { found: false, scrolled: window.scrollY > oldY, at_bottom: false };
    """
    try:
        res = browser.execute_script(script, step_pixels)
        return res or {"found": False, "scrolled": False, "at_bottom": True}
    except Exception:
        return {"found": False, "scrolled": False, "at_bottom": True}


def get_conversation_elements(browser):
    """
    Tìm danh sách các phần tử cuộc trò chuyện hiện có trong DOM hộp thư TikTok.
    """
    selectors = [
        "//*[@data-e2e='conversation-item']",
        "//*[@data-e2e='chat-list-item']",
        "//*[contains(@class, 'PInfoNickname')]",
        "//p[contains(@class, 'Nickname')]",
        "//div[contains(@class, 'Nickname')]"
    ]
    for sel in selectors:
        try:
            elems = browser.find_elements(By.XPATH, sel)
            if elems:
                return elems
        except Exception:
            continue
    return []


def auto_load_all_conversations(browser, log_cb=print, should_stop=None, max_scrolls=35):
    """
    Tự động cuộn danh sách cuộc trò chuyện bên trái để nạp đầy đủ toàn bộ bạn bè và nhóm chat
    từ cơ chế infinite scroll của TikTok (vượt qua giới hạn mặc định ~30 cuộc trò chuyện).
    """
    log_cb("Đang tự động cuộn để nạp toàn bộ danh sách bạn bè & nhóm chat từ TikTok...")
    no_growth_count = 0
    last_count = 0

    for scroll_idx in range(1, max_scrolls + 1):
        if should_stop and should_stop():
            log_cb("[Dừng] Đã dừng quá trình cuộn nạp danh sách.")
            break

        scroll_chat_list_container(browser)
        time.sleep(1.2)

        current_elems = get_conversation_elements(browser)
        current_count = len(current_elems)

        if current_count > last_count:
            log_cb(f"   -> Đã tải được {current_count} cuộc trò chuyện (lượt cuộn {scroll_idx})...")
            last_count = current_count
            no_growth_count = 0
        else:
            no_growth_count += 1
            if current_elems:
                try:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'end'});", current_elems[-1])
                    time.sleep(1.0)
                    recheck_elems = get_conversation_elements(browser)
                    if len(recheck_elems) > current_count:
                        current_count = len(recheck_elems)
                        last_count = current_count
                        no_growth_count = 0
                        log_cb(f"   -> Đã tải được {current_count} cuộc trò chuyện...")
                except Exception:
                    pass

            if no_growth_count >= 3:
                log_cb(f"   -> Đã tải hết danh sách hộp thư (Tổng cộng: {current_count} cuộc trò chuyện).")
                break

    return get_conversation_elements(browser)


def close_story_if_open(browser, log_cb=print):
    """
    Kiểm tra và tự động đóng ngay lập tức nếu vô tình bị mở Story của TikTok,
    đảm bảo luôn duy trì ở giao diện hộp thư tin nhắn.
    """
    try:
        current_url = (browser.current_url or "").lower()
        is_story_url = "/story/" in current_url or "/photo/" in current_url or "story_id=" in current_url

        script_check = """
        const storyIndicators = [
            '[data-e2e="story-player"]',
            '[class*="StoryPlayer"]',
            '[class*="StoryViewer"]',
            '[class*="story-container"]',
            '[aria-label*="story" i]'
        ];
        for (const sel of storyIndicators) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) return true;
        }
        return false;
        """
        is_story_dom = False
        try:
            is_story_dom = bool(browser.execute_script(script_check))
        except Exception:
            pass

        if is_story_url or is_story_dom:
            log_cb("   -> [Phát hiện Story đang mở] Đang tự động đóng Story...")
            # 1. Nhấn ESC
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.4)
            except Exception:
                pass

            # 2. Tìm nút Close của Story và click
            script_close = """
            const closeBtns = [
                '[data-e2e="close-button"]',
                'button[aria-label*="close" i]',
                'button[aria-label*="đóng" i]',
                '[class*="CloseButton"]',
                '[class*="close-btn"]',
                'button.close'
            ];
            for (const sel of closeBtns) {
                const btn = document.querySelector(sel);
                if (btn && btn.offsetParent !== null) {
                    btn.click();
                    return true;
                }
            }
            return false;
            """
            try:
                browser.execute_script(script_close)
                time.sleep(0.5)
            except Exception:
                pass

            # 3. Nếu vẫn còn ở URL story, điều hướng quay lại messages
            new_url = (browser.current_url or "").lower()
            if "/story/" in new_url or "/photo/" in new_url:
                browser.get("https://www.tiktok.com/messages?lang=vi")
                time.sleep(2.5)
            return True
    except Exception:
        pass
    return False


def click_conversation_chat_safe(browser, elem):
    """
    Click an toàn vào một cuộc trò chuyện để mở hộp chat:
    ƯU TIÊN click vào Nickname/Text ở bên phải,
    TUYỆT ĐỐI KHÔNG click vào Avatar chứa viền Story bên trái để tránh tự bật Story.
    """
    try:
        script = """
        const card = arguments[0];
        if (!card) return false;

        // Vô hiệu hóa liên kết story hoặc avatar nếu có trong card này
        const storyLinks = card.querySelectorAll('a[href*="/story/"], a[href*="/photo/"], [class*="Story"], [class*="Avatar"] a');
        storyLinks.forEach(a => {
            a.style.pointerEvents = 'none';
        });

        // Tìm phần tử Nickname / Text để click trực tiếp vào text
        const textSelectors = [
            '[class*="PInfoNickname"]',
            'p[class*="Nickname"]',
            'div[class*="Nickname"]',
            '[class*="Info"]',
            '[class*="Content"]',
            'p',
            'span'
        ];
        for (const sel of textSelectors) {
            const textEl = card.querySelector(sel);
            if (textEl && textEl.offsetParent !== null && !textEl.closest('a[href*="/story/"]')) {
                textEl.scrollIntoView({block: 'center', inline: 'nearest'});
                textEl.click();
                return true;
            }
        }

        // Fallback: click vào mép phải của card (tránh avatar bên trái)
        card.scrollIntoView({block: 'center', inline: 'nearest'});
        const rect = card.getBoundingClientRect();
        const evt = new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            view: window,
            clientX: rect.left + Math.max(80, rect.width * 0.6),
            clientY: rect.top + rect.height / 2
        });
        card.dispatchEvent(evt);
        return true;
        """
        res = browser.execute_script(script, elem)
        return bool(res)
    except Exception:
        try:
            elem.click()
            return True
        except Exception:
            return False


def find_next_conversation(browser, current_elem=None, current_sig=None):
    """
    Tìm phần tử cuộc trò chuyện tiếp theo (ngay sau current_elem) trong danh sách bên trái.
    Tự động xử lý Virtual Scrolling của TikTok: định vị chính xác vị trí của người vừa quét
    trong DOM và lấy đúng người liền kề tiếp theo (curIdx + 1), khắc phục triệt để lỗi nhảy cóc
    (như 10 -> 15 bỏ qua 11->14) do phần tử trên cùng bị unmount khi cuộn trang.
    Trả về:
      - WebElement: Phần tử tiếp theo cần quét.
      - "AT_END": Đã duyệt đến phần tử cuối cùng hiện có trong DOM, cần cuộn để nạp thêm.
      - None: Không tìm thấy (cần dùng fallback).
    """
    script = """
    const currentElem = arguments[0];
    const currentSig = (arguments[1] || '').trim().toLowerCase();

    // 1. Tìm tất cả các phần tử cuộc trò chuyện trong DOM
    const selectors = [
        '[data-e2e="conversation-item"]',
        '[data-e2e="chat-list-item"]',
        '[class*="PInfoNickname"]',
        'p[class*="Nickname"]',
        'div[class*="Nickname"]'
    ];

    let items = [];
    for (const sel of selectors) {
        const found = Array.from(document.querySelectorAll(sel));
        if (found.length > 0) {
            items = found;
            break;
        }
    }

    if (items.length === 0) return null;

    // 2. Nếu chưa có currentElem (bắt đầu quét): lấy phần tử đầu tiên
    if (!currentElem && !currentSig) {
        return items[0];
    }

    // 3. Ưu tiên tìm theo cờ data-streak-current được gán ở lượt trước
    let curIdx = items.findIndex(el => el.getAttribute('data-streak-current') === 'true' || (el.querySelector && el.querySelector('[data-streak-current="true"]')));

    // 4. Nếu không tìm thấy bằng cờ, so khớp bằng tham chiếu DOM node
    if (curIdx === -1 && currentElem) {
        curIdx = items.indexOf(currentElem);
        if (curIdx === -1) {
            curIdx = items.findIndex(el => el === currentElem || el.contains(currentElem) || currentElem.contains(el));
        }
    }

    // 5. Nếu DOM node bị tái chế (recycled), so khớp bằng chữ ký text
    if (curIdx === -1 && currentSig) {
        const firstLine = currentSig.split('\\n')[0].trim();
        curIdx = items.findIndex(el => {
            const txt = (el.innerText || '').trim().toLowerCase();
            return txt === currentSig || (firstLine && txt.startsWith(firstLine));
        });
    }

    // 6. Trả về phần tử kế tiếp liền kề
    if (curIdx !== -1) {
        if (curIdx + 1 < items.length) {
            // Xóa cờ data-streak-current ở phần tử cũ
            try {
                items[curIdx].removeAttribute('data-streak-current');
                const sub = items[curIdx].querySelector('[data-streak-current="true"]');
                if (sub) sub.removeAttribute('data-streak-current');
            } catch(e) {}
            return items[curIdx + 1];
        } else {
            return "AT_END";
        }
    }

    return null;
    """
    try:
        res = browser.execute_script(script, current_elem, current_sig)
        return res
    except Exception:
        return None


def scan_friends(browser, wait, log_cb=print, should_stop=None, account_id=None):
    """
    Quét danh sách bạn bè và nhóm chat từ hộp thư TikTok cho tài khoản cụ thể.
    Thuật toán: Quét tuần tự từ trên xuống dưới, từng người một (không đếm trước số lượng).
    Sử dụng định vị liền kề để không bao giờ bị nhảy cóc (ví dụ 10 -> 15 bỏ qua 11->14).
    Chỉ dừng lại nếu ID người trước == ID người hiện tại (đã đến cuộc trò chuyện cuối cùng của hộp thư).
    Trả về danh sách bạn bè & nhóm cập nhật.
    """
    log_cb("Đang truy cập hộp thư tin nhắn TikTok...")
    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)

    selectors = [
        "//*[@data-e2e='conversation-item']",
        "//*[@data-e2e='chat-list-item']",
        "//*[contains(@class, 'PInfoNickname')]",
        "//p[contains(@class, 'Nickname')]",
        "//div[contains(@class, 'Nickname')]"
    ]
    initial_found = False
    for sel in selectors:
        try:
            found = wait.until(EC.presence_of_all_elements_located((By.XPATH, sel)))
            if found:
                initial_found = True
                break
        except Exception:
            continue

    if not initial_found:
        log_cb("[Cảnh báo] Không tìm thấy cuộc trò chuyện nào trong hộp thư.")
        return load_friends(account_id)

    # Cuộn container danh sách cuộc trò chuyện lên trên cùng (scrollTop = 0)
    try:
        browser.execute_script("""
            const selectors = ['[data-e2e="chat-list"]', '[data-e2e="conversation-list"]', '[class*="ChatList"]', 'aside [class*="list"]'];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) { el.scrollTop = 0; break; }
            }
        """)
        time.sleep(0.5)
    except Exception:
        pass

    log_cb("Bắt đầu quét danh sách bạn bè từ trên xuống dưới (quét từng người một)...")
    current_friends = load_friends(account_id)

    # Bản đồ tra cứu bạn bè đã có
    user_map = {f["username"].lower(): f for f in current_friends if f.get("username")}
    nick_map = {f["nickname"].strip().lower(): f for f in current_friends if f.get("nickname")}

    count_scanned = 0
    count_new = 0
    count_group = 0

    prev_id = None
    current_elem = None
    current_sig = None
    scanned_identities = set()
    consecutive_at_end = 0

    while True:
        if should_stop and should_stop():
            log_cb("[Dừng] Người dùng yêu cầu dừng quá trình quét.")
            break

        # 1. Tìm phần tử cuộc trò chuyện kế tiếp liền kề (ngay sau current_elem)
        next_target = find_next_conversation(browser, current_elem, current_sig)

        # 2. Xử lý trường hợp đã đến cuối DOM hiện tại ("AT_END") hoặc không tìm thấy bằng JS
        if next_target == "AT_END" or next_target is None:
            # Cuộn container xuống một bước vừa phải (350px) để TikTok nạp thêm item tiếp theo
            scroll_chat_list_container(browser, step_pixels=350)
            time.sleep(1.0)

            # Đưa phần tử hiện tại vào giữa tầm nhìn nếu có
            if current_elem:
                try:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", current_elem)
                    time.sleep(0.4)
                except Exception:
                    pass

            # Thử tìm lại phần tử kế tiếp sau khi cuộn
            retry_target = find_next_conversation(browser, current_elem, current_sig)
            if retry_target and retry_target != "AT_END":
                next_target = retry_target
                consecutive_at_end = 0
            else:
                # Fallback: nếu JS không tìm được, duyệt DOM tìm phần tử đầu tiên chưa quét
                if next_target is None:
                    elems = get_conversation_elements(browser)
                    for el in elems:
                        try:
                            t = el.text.strip().lower()
                            first_l = t.splitlines()[0] if t else ""
                            if first_l and first_l not in scanned_identities:
                                next_target = el
                                break
                        except Exception:
                            continue

                if next_target and next_target != "AT_END":
                    consecutive_at_end = 0
                else:
                    consecutive_at_end += 1
                    # Nếu đã cuộn 2 lần mà không có phần tử mới nào xuất hiện ở phía dưới
                    if consecutive_at_end >= 2:
                        log_cb(f"   -> [Dừng quét] ID người trước ('{prev_id}') trùng với người cuối cùng của hộp thư (không thể quét thêm)!")
                        break
                    else:
                        time.sleep(1.0)
                        continue
        else:
            consecutive_at_end = 0

        user_elem = next_target

        # Đưa phần tử vào giữa màn hình trước khi thao tác
        try:
            browser.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", user_elem)
            time.sleep(0.2)
        except Exception:
            pass

        raw_text = ""
        try:
            raw_text = user_elem.text.strip()
        except Exception:
            time.sleep(0.3)
            continue

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        raw_nickname = lines[0] if lines else f"Mục {count_scanned + 1}"

        # Đánh dấu cờ data-streak-current lên phần tử này để vòng lặp sau định vị chính xác
        try:
            browser.execute_script("arguments[0].setAttribute('data-streak-current', 'true');", user_elem)
        except Exception:
            pass

        # Cập nhật phần tử hiện tại và chữ ký text
        current_elem = user_elem
        current_sig = raw_text

        # Bỏ qua các mục hệ thống như 'Yêu cầu tin nhắn' (Message Requests)
        if any(sys_kw in raw_nickname.lower() for sys_kw in ["yêu cầu tin nhắn", "message requests", "tin nhắn yêu cầu"]):
            log_cb(f"   -> [Bỏ qua mục hệ thống] {raw_nickname}")
            continue

        # Click an toàn CHỈ VÀO TEXT/NICKNAME để mở chat (TUYỆT ĐỐI TRÁNH AVATAR STORY)
        clicked = click_conversation_chat_safe(browser, user_elem)
        if not clicked:
            try:
                user_elem.click()
            except Exception:
                try:
                    browser.execute_script("arguments[0].click();", user_elem)
                except Exception:
                    pass

        time.sleep(0.8)

        # Đóng Story nếu vô tình bị mở
        close_story_if_open(browser, log_cb=log_cb)

        # Trích xuất thông tin cuộc trò chuyện ở khung bên phải
        chat_info = extract_chat_details(browser, fallback_nickname=raw_nickname)
        is_group = chat_info.get("is_group", False)
        chat_title = chat_info.get("title") or raw_nickname
        username = chat_info.get("username", "")

        # Định danh ID duy nhất của người / cuộc trò chuyện hiện tại
        if is_group:
            current_id = f"[nhóm] {chat_title}".strip().lower()
        else:
            current_id = (username or chat_title or raw_nickname).strip().lower()

        # =========================================================================
        # ĐIỀU KIỆN DỪNG: CHỈ DỪNG LẠI NẾU ID NGƯỜI TRƯỚC == ID NGƯỜI HIỆN TẠI
        # =========================================================================
        if prev_id is not None and current_id == prev_id:
            # Chờ thêm 1.0s và kiểm tra lại một lần nữa để tránh dừng nhầm nếu mạng lag
            time.sleep(1.0)
            recheck_info = extract_chat_details(browser, fallback_nickname=raw_nickname)
            recheck_is_group = recheck_info.get("is_group", False)
            recheck_title = recheck_info.get("title") or raw_nickname
            recheck_user = recheck_info.get("username", "")
            if recheck_is_group:
                recheck_id = f"[nhóm] {recheck_title}".strip().lower()
            else:
                recheck_id = (recheck_user or recheck_title or raw_nickname).strip().lower()

            if recheck_id == prev_id:
                log_cb(f"   -> [Dừng quét] ID người trước ('{prev_id}') == ID người hiện tại ('{current_id}'). Đã đến cuộc trò chuyện cuối cùng của hộp thư!")
                break
            else:
                current_id = recheck_id
                chat_info = recheck_info
                is_group = recheck_is_group
                chat_title = recheck_title
                username = recheck_user

        # Cập nhật ID người trước
        prev_id = current_id
        count_scanned += 1
        scanned_identities.add(current_id)
        if username:
            scanned_identities.add(username.lower())
        scanned_identities.add(chat_title.strip().lower())
        scanned_identities.add(raw_nickname.strip().lower())

        # XỬ LÝ NHÓM CHAT
        if is_group:
            title_lower = chat_title.lower()
            matched_group = nick_map.get(title_lower)

            if matched_group:
                matched_group["nickname"] = chat_title
                if not matched_group.get("username", "").startswith("[Nhóm]"):
                    matched_group["username"] = f"[Nhóm] {chat_title}"
                log_cb(f"[{count_scanned}] [Nhóm đã có] {chat_title}")
            else:
                new_item = {
                    "username": f"[Nhóm] {chat_title}",
                    "nickname": chat_title,
                    "enabled": True,
                    "status": "Chưa gửi"
                }
                current_friends.append(new_item)
                nick_map[title_lower] = new_item
                count_new += 1
                count_group += 1
                log_cb(f"[{count_scanned}] [Nhóm mới] Đã thêm nhóm: {chat_title}")

        # XỬ LÝ NGƯỜI DÙNG CÁ NHÂN (1-1)
        else:
            u_lower = username.lower() if username else ""
            if u_lower and u_lower in user_map:
                user_map[u_lower]["nickname"] = chat_title
                log_cb(f"[{count_scanned}] Đã có: {chat_title} (@{username})")
            elif not u_lower and chat_title.lower() in nick_map:
                nick_map[chat_title.lower()]["nickname"] = chat_title
                log_cb(f"[{count_scanned}] Đã có: {chat_title}")
            else:
                new_friend = {
                    "username": username or chat_title,
                    "nickname": chat_title,
                    "enabled": True,
                    "status": "Chưa gửi"
                }
                current_friends.append(new_friend)
                if u_lower:
                    user_map[u_lower] = new_friend
                nick_map[chat_title.lower()] = new_friend
                count_new += 1
                user_display = f" (@{username})" if username else ""
                log_cb(f"[{count_scanned}] [Bạn mới] Đã thêm: {chat_title}{user_display}")

        # Lưu tạm định kỳ mỗi 5 bạn bè
        if count_scanned % 5 == 0:
            save_friends(current_friends, account_id)

    save_friends(current_friends, account_id)
    log_cb(f"[Hoàn tất] Đã quét xong toàn bộ danh sách! Tổng cộng: {count_scanned} cuộc trò chuyện ({count_new} mục mới, trong đó có {count_group} nhóm).")
    return current_friends


# ----------------------------
# GỬI TIN NHẮN THEO DANH SÁCH CHỌN (BẠN BÈ & NHÓM CHAT)
# ----------------------------

def is_friend_replied_today(friend, today_date_str=None):
    """
    Kiểm tra xem bạn bè hoặc nhóm này đã được gửi tin nhắn chuỗi trong ngày hôm nay chưa.
    Status thường có dạng: 'Đã gửi (10:15:30 13/10/2026)'
    """
    if not today_date_str:
        today_date_str = time.strftime("%d/%m/%Y")
    status = str(friend.get("status") or "").strip()
    return status.startswith("Đã gửi") and (today_date_str in status)


def send_messages_to_selected(browser, wait, message=None, delay_sec=3, log_cb=print, should_stop=None, account_id=None):
    """
    Gửi tin nhắn chuỗi (streak) cho danh sách bạn bè và nhóm chat đã chọn (enabled == True).
    Áp dụng thuật toán quét từ trên xuống dưới tương tự như quét bạn bè (scan_friends):
      - Quét tuần tự từng cuộc trò chuyện từ trên xuống dưới bằng định vị liền kề.
      - Nếu ID cuộc trò chuyện thuộc danh sách rep chuỗi (enabled == True)
        VÀ ID này chưa được rep chuỗi trong ngày hôm nay -> Gửi tin nhắn chuỗi.
      - Nếu số lượng ID đã rep chuỗi trong ngày == số người cần rep chuỗi -> Dừng ngay lập tức.
      - Nếu ID người trước == ID người hiện tại (đã đến cuối hộp thư) -> Dừng.
    Trả về (sent_count, total_count).
    """
    config = load_config(account_id)
    msg_text = message or config.get("message", "Chào {nickname}, rep chuỗi streak nè {time}!")

    all_friends = load_friends(account_id)
    selected_targets = [f for f in all_friends if f.get("enabled", True)]

    if not selected_targets:
        log_cb("[Thông báo] Không có bạn bè hoặc nhóm nào trong danh sách rep chuỗi được chọn (enabled = True).")
        return 0, 0

    today_str = time.strftime("%d/%m/%Y")

    def get_friend_key(f):
        u = (f.get("username") or "").strip().lower()
        n = (f.get("nickname") or "").strip().lower()
        return u or n

    # Tập hợp các mục tiêu đã được rep chuỗi trong ngày hôm nay
    replied_ids_today = set()
    for f in selected_targets:
        if is_friend_replied_today(f, today_str):
            replied_ids_today.add(get_friend_key(f))

    total_need_count = len(selected_targets)
    already_sent_count = len(replied_ids_today)

    log_cb(f"Bắt đầu quy trình gửi chuỗi cho {total_need_count} mục đã chọn...")
    log_cb(f"Ngày hiện tại: {today_str} | Đã rep hôm nay: {already_sent_count}/{total_need_count} mục")
    log_cb(f"Nội dung gửi: \"{msg_text}\" | Giãn cách an toàn: {delay_sec}s")

    # Kiểm tra điều kiện dừng: nếu số lượng id đã rep chuỗi == số người cần rep chuỗi -> dừng
    if len(replied_ids_today) >= total_need_count:
        log_cb(f"[Hoàn tất] Toàn bộ {total_need_count} mục trong danh sách rep chuỗi đều đã được gửi trong ngày hôm nay ({today_str})! Không cần gửi thêm.")
        return len(replied_ids_today), total_need_count

    log_cb("Đang truy cập hộp thư tin nhắn TikTok...")
    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)

    selectors = [
        "//*[@data-e2e='conversation-item']",
        "//*[@data-e2e='chat-list-item']",
        "//*[contains(@class, 'PInfoNickname')]",
        "//p[contains(@class, 'Nickname')]",
        "//div[contains(@class, 'Nickname')]"
    ]
    initial_found = False
    for sel in selectors:
        try:
            found = wait.until(EC.presence_of_all_elements_located((By.XPATH, sel)))
            if found:
                initial_found = True
                break
        except Exception:
            continue

    if not initial_found:
        log_cb("[Cảnh báo] Không tìm thấy cuộc trò chuyện nào trong hộp thư.")
        return len(replied_ids_today), total_need_count

    # Cuộn container danh sách cuộc trò chuyện lên trên cùng (scrollTop = 0)
    try:
        browser.execute_script("""
            const selectors = ['[data-e2e="chat-list"]', '[data-e2e="conversation-list"]', '[class*="ChatList"]', 'aside [class*="list"]'];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) { el.scrollTop = 0; break; }
            }
        """)
        time.sleep(0.5)
    except Exception:
        pass

    log_cb("Bắt đầu quét hộp thư từ trên xuống dưới để gửi chuỗi...")
    newly_sent_count = 0
    count_scanned = 0

    prev_id = None
    current_elem = None
    current_sig = None
    scanned_identities = set()
    consecutive_at_end = 0

    while True:
        if should_stop and should_stop():
            log_cb("[Dừng] Người dùng yêu cầu dừng quá trình gửi chuỗi.")
            break

        # Điều kiện dừng: nếu số lượng id đã rep chuỗi == số người cần rep chuỗi -> dừng
        if len(replied_ids_today) >= total_need_count:
            log_cb(f"[Hoàn tất] Số lượng ID đã rep chuỗi ({len(replied_ids_today)}) đã đạt đủ số người cần rep chuỗi ({total_need_count}). Dừng tiến trình!")
            break

        # 1. Tìm phần tử cuộc trò chuyện kế tiếp liền kề (ngay sau current_elem)
        next_target = find_next_conversation(browser, current_elem, current_sig)

        # Kiểm tra nếu next_target đã nằm trong scanned_identities (do danh sách có thể nhảy lên đầu khi vừa gửi tin)
        if next_target and next_target != "AT_END":
            try:
                t = next_target.text.strip().lower()
                first_l = t.splitlines()[0] if t else ""
                if first_l and first_l in scanned_identities:
                    next_target = None
            except Exception:
                pass

        # 2. Xử lý trường hợp đã đến cuối DOM hiện tại ("AT_END") hoặc không tìm thấy bằng JS
        if next_target == "AT_END" or next_target is None:
            # Cuộn container xuống một bước vừa phải (350px) để TikTok nạp thêm item tiếp theo
            scroll_chat_list_container(browser, step_pixels=350)
            time.sleep(1.0)

            # Đưa phần tử hiện tại vào giữa tầm nhìn nếu có
            if current_elem:
                try:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", current_elem)
                    time.sleep(0.4)
                except Exception:
                    pass

            # Thử tìm lại phần tử kế tiếp sau khi cuộn
            retry_target = find_next_conversation(browser, current_elem, current_sig)
            if retry_target and retry_target != "AT_END":
                try:
                    t = retry_target.text.strip().lower()
                    first_l = t.splitlines()[0] if t else ""
                    if first_l and first_l not in scanned_identities:
                        next_target = retry_target
                        consecutive_at_end = 0
                except Exception:
                    pass

            if not next_target or next_target == "AT_END":
                # Fallback: duyệt DOM tìm phần tử đầu tiên chưa quét
                elems = get_conversation_elements(browser)
                for el in elems:
                    try:
                        t = el.text.strip().lower()
                        first_l = t.splitlines()[0] if t else ""
                        if first_l and first_l not in scanned_identities:
                            next_target = el
                            break
                    except Exception:
                        continue

                if next_target and next_target != "AT_END":
                    consecutive_at_end = 0
                else:
                    consecutive_at_end += 1
                    # Nếu đã cuộn 2 lần mà không có phần tử mới nào xuất hiện ở phía dưới
                    if consecutive_at_end >= 2:
                        log_cb(f"   -> [Dừng quét] ID người trước ('{prev_id}') trùng với người cuối cùng của hộp thư (không thể quét thêm)!")
                        break
                    else:
                        time.sleep(1.0)
                        continue
        else:
            consecutive_at_end = 0

        user_elem = next_target

        # Đưa phần tử vào giữa màn hình trước khi thao tác
        try:
            browser.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", user_elem)
            time.sleep(0.2)
        except Exception:
            pass

        raw_text = ""
        try:
            raw_text = user_elem.text.strip()
        except Exception:
            time.sleep(0.3)
            continue

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        raw_nickname = lines[0] if lines else f"Mục {count_scanned + 1}"

        # Đánh dấu cờ data-streak-current lên phần tử này để vòng lặp sau định vị chính xác
        try:
            browser.execute_script("arguments[0].setAttribute('data-streak-current', 'true');", user_elem)
        except Exception:
            pass

        # Cập nhật phần tử hiện tại và chữ ký text
        current_elem = user_elem
        current_sig = raw_text

        # Bỏ qua các mục hệ thống như 'Yêu cầu tin nhắn' (Message Requests)
        if any(sys_kw in raw_nickname.lower() for sys_kw in ["yêu cầu tin nhắn", "message requests", "tin nhắn yêu cầu"]):
            continue

        # Click an toàn CHỈ VÀO TEXT/NICKNAME để mở chat (TUYỆT ĐỐI TRÁNH AVATAR STORY)
        clicked = click_conversation_chat_safe(browser, user_elem)
        if not clicked:
            try:
                user_elem.click()
            except Exception:
                try:
                    browser.execute_script("arguments[0].click();", user_elem)
                except Exception:
                    pass

        time.sleep(0.8)

        # Đóng Story nếu vô tình bị mở
        close_story_if_open(browser, log_cb=log_cb)

        # Trích xuất thông tin cuộc trò chuyện ở khung bên phải
        chat_info = extract_chat_details(browser, fallback_nickname=raw_nickname)
        is_group = chat_info.get("is_group", False)
        chat_title = chat_info.get("title") or raw_nickname
        username = chat_info.get("username", "")

        # Định danh ID duy nhất của người / cuộc trò chuyện hiện tại
        if is_group:
            current_id = f"[nhóm] {chat_title}".strip().lower()
        else:
            current_id = (username or chat_title or raw_nickname).strip().lower()

        # =========================================================================
        # ĐIỀU KIỆN DỪNG: CHỈ DỪNG LẠI NẾU ID NGƯỜI TRƯỚC == ID NGƯỜI HIỆN TẠI
        # =========================================================================
        if prev_id is not None and current_id == prev_id:
            time.sleep(1.0)
            recheck_info = extract_chat_details(browser, fallback_nickname=raw_nickname)
            recheck_is_group = recheck_info.get("is_group", False)
            recheck_title = recheck_info.get("title") or raw_nickname
            recheck_user = recheck_info.get("username", "")
            if recheck_is_group:
                recheck_id = f"[nhóm] {recheck_title}".strip().lower()
            else:
                recheck_id = (recheck_user or recheck_title or raw_nickname).strip().lower()

            if recheck_id == prev_id:
                log_cb(f"   -> [Dừng quét] ID người trước ('{prev_id}') == ID người hiện tại ('{current_id}'). Đã đến cuộc trò chuyện cuối cùng của hộp thư!")
                break
            else:
                current_id = recheck_id
                chat_info = recheck_info
                is_group = recheck_is_group
                chat_title = recheck_title
                username = recheck_user

        prev_id = current_id
        count_scanned += 1
        scanned_identities.add(current_id)
        if username:
            scanned_identities.add(username.lower())
        scanned_identities.add(chat_title.strip().lower())
        scanned_identities.add(raw_nickname.strip().lower())

        # =========================================================================
        # KIỂM TRA ĐIỀU KIỆN GỬI CHUỖI:
        # Nếu id == id trong danh sách rep chuỗi && id chưa được rep chuỗi trong ngày hôm nay
        # -> gửi tin nhắn chuỗi
        # =========================================================================
        target_friend = find_matching_target(selected_targets, chat_info, elem_nickname=raw_nickname)
        if not target_friend:
            # Thử đối chiếu trực tiếp qua ID với danh sách rep chuỗi
            for tf in selected_targets:
                u_tf = (tf.get("username") or "").strip().lower()
                n_tf = (tf.get("nickname") or "").strip().lower()
                if current_id in [u_tf, n_tf, f"[nhóm] {n_tf}", f"[nhóm] {u_tf}"]:
                    target_friend = tf
                    break
                if u_tf and u_tf in [current_id, username.lower(), raw_nickname.lower(), chat_title.lower()]:
                    target_friend = tf
                    break

        if not target_friend:
            # Không nằm trong danh sách rep chuỗi -> tiếp tục quét người kế tiếp
            continue

        target_key = get_friend_key(target_friend)

        # Kiểm tra nếu id đã được rep chuỗi trong ngày hôm nay
        if is_friend_replied_today(target_friend, today_str) or target_key in replied_ids_today:
            log_cb(f"[{count_scanned}] [Bỏ qua] {target_friend['nickname']}: Đã rep chuỗi trong ngày hôm nay ({today_str}) rồi.")
            replied_ids_today.add(target_key)
            # Điều kiện dừng: nếu số lượng id đã rep chuỗi == số người cần rep chuỗi -> dừng
            if len(replied_ids_today) >= total_need_count:
                log_cb(f"[Hoàn tất] Số lượng ID đã rep chuỗi ({len(replied_ids_today)}) đã đạt đủ số người cần rep chuỗi ({total_need_count}). Dừng tiến trình!")
                break
            continue

        # ID nằm trong danh sách và CHƯA được rep chuỗi hôm nay -> GỬI TIN NHẮN CHUỖI
        actual_msg = render_message_template(msg_text, target_friend)

        if is_group:
            log_cb(f"[{count_scanned}] -> Đang gửi tin nhắn vào nhóm '{target_friend['nickname']}': \"{actual_msg}\"")
        else:
            log_cb(f"[{count_scanned}] -> Đang gửi tin nhắn cho: {target_friend['nickname']} (@{target_friend.get('username', '')}): \"{actual_msg}\"")

        input_selectors = [
            "//div[contains(@class, 'public-DraftStyleDefault-block')]",
            "//div[@contenteditable='true']",
            "//*[@data-e2e='chat-input']"
        ]
        message_box = None
        for i_sel in input_selectors:
            try:
                boxes = browser.find_elements(By.XPATH, i_sel)
                for b in boxes:
                    if b.is_displayed():
                        message_box = b
                        break
                if message_box:
                    break
            except Exception:
                continue

        if message_box:
            try:
                message_box.click()
                time.sleep(0.4)
                message_box.send_keys(actual_msg)
                time.sleep(0.3)
                message_box.send_keys(Keys.RETURN)
                time.sleep(0.5)

                # Nút Send dự phòng nếu phím Enter chưa gửi được
                try:
                    send_buttons = browser.find_elements(By.XPATH, "//*[@data-e2e='chat-send-btn'] | //button[contains(@class, 'send')]")
                    for btn in send_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(0.4)
                            break
                except Exception:
                    pass

                current_time = time.strftime("%H:%M:%S %d/%m/%Y")
                target_friend["status"] = f"Đã gửi ({current_time})"
                save_friends(all_friends, account_id)

                newly_sent_count += 1
                replied_ids_today.add(target_key)

                target_display = f"nhóm '{target_friend['nickname']}'" if is_group else f"@{target_friend.get('username', '')}"
                log_cb(f"   [Thành công] Đã gửi tới {target_display}! ({len(replied_ids_today)}/{total_need_count}) | Nghỉ {delay_sec}s...")

                # Điều kiện dừng: nếu số lượng id đã rep chuỗi == số người cần rep chuỗi -> dừng
                if len(replied_ids_today) >= total_need_count:
                    log_cb(f"[Hoàn tất] Số lượng ID đã rep chuỗi ({len(replied_ids_today)}) đã đạt đủ số người cần rep chuỗi ({total_need_count}). Dừng tiến trình!")
                    break

                time.sleep(delay_sec)
            except Exception as send_err:
                log_cb(f"   [Lỗi khi gửi] {send_err}")
        else:
            log_cb(f"   [Thất bại] Không tìm thấy ô nhập tin nhắn của mục '{raw_nickname}'")
            target_friend["status"] = "Lỗi ô chat"
            save_friends(all_friends, account_id)

    log_cb(f"[Hoàn tất] Đã gửi {newly_sent_count} tin nhắn mới. Tổng cộng hôm nay đã rep chuỗi: {len(replied_ids_today)}/{total_need_count} mục.")
    return len(replied_ids_today), total_need_count
