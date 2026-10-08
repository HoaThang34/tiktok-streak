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

    tags = {
        "{time}": time.strftime("%H:%M:%S", now),
        "{date}": time.strftime("%d/%m/%Y", now),
        "{datetime}": time.strftime("%H:%M:%S %d/%m/%Y", now),
        "{hour}": time.strftime("%H", now),
        "{minute}": time.strftime("%M", now),
        "{second}": time.strftime("%S", now),
        "{nickname}": nick,
        "{username}": uname,
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

    # Đồng bộ sang file root nếu là tài khoản đang thao tác
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


def extract_current_chat_username(browser):
    """
    Trích xuất chính xác username (@handle) của người bạn trong cuộc trò chuyện đang mở trên TikTok.
    """
    # 1. Ưu tiên thẻ a có chứa '@' trong text
    try:
        links_with_at = browser.find_elements(By.XPATH, "//a[contains(@href, '/@') and contains(., '@')]")
        for l in links_with_at:
            txt = l.text.strip()
            m = re.search(r"@([a-zA-Z0-9._]+)", txt)
            if m:
                return m.group(1)
    except Exception:
        pass

    # 2. Tìm trong khu vực tiêu đề chat (Chat Header)
    try:
        header_links = browser.find_elements(By.XPATH, "//*[contains(@class, 'ChatHeader') or contains(@class, 'chat-header') or contains(@class, 'HeaderWrapper') or contains(@class, 'ConversationHeader')]//a[contains(@href, '/@')]")
        for l in reversed(header_links):
            href = l.get_attribute("href") or ""
            m = re.search(r"/@([^/?#]+)", href)
            if m:
                u = m.group(1)
                if u not in ["login", "tiktokstudio"] and not href.endswith(("/video/", "/photo/")):
                    return u
    except Exception:
        pass

    # 3. Quét ngược danh sách link có href /@
    try:
        all_links = browser.find_elements(By.XPATH, "//a[contains(@href, '/@')]")
        for l in reversed(all_links):
            txt = l.text.strip()
            if "@" in txt:
                m = re.search(r"@([a-zA-Z0-9._]+)", txt)
                if m:
                    return m.group(1)
            href = l.get_attribute("href") or ""
            m = re.search(r"/@([^/?#]+)", href)
            if m:
                u = m.group(1)
                if u not in ["vailuvjk", "login", "tiktokstudio"] and not href.endswith(("/video/", "/photo/")):
                    return u
    except Exception:
        pass

    return ""


# ----------------------------
# QUÉT BẠN BÈ (SCAN FRIENDS)
# ----------------------------

def scan_friends(browser, wait, log_cb=print, should_stop=None, account_id=None):
    """
    Quét danh sách bạn bè từ hộp thư TikTok cho tài khoản cụ thể.
    Trả về danh sách bạn bè cập nhật.
    """
    log_cb("Đang truy cập hộp thư tin nhắn TikTok...")
    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)

    selectors = [
        "//*[contains(@class, 'PInfoNickname')]",
        "//p[contains(@class, 'Nickname')]",
        "//div[contains(@class, 'Nickname')]",
        "//*[@data-e2e='conversation-item']",
        "//*[@data-e2e='chat-list-item']"
    ]
    all_user = []
    for sel in selectors:
        try:
            found = wait.until(EC.presence_of_all_elements_located((By.XPATH, sel)))
            if found:
                all_user = found
                break
        except Exception:
            continue

    if not all_user:
        log_cb("[Cảnh báo] Không tìm thấy cuộc trò chuyện nào trong hộp thư.")
        return load_friends(account_id)

    log_cb(f"Tìm thấy {len(all_user)} cuộc trò chuyện. Bắt đầu thu thập thông tin...")
    current_friends = load_friends(account_id)
    existing_map = {f["username"].lower(): f for f in current_friends}

    count_new = 0
    for idx, user_elem in enumerate(all_user, start=1):
        if should_stop and should_stop():
            log_cb("[Dừng] Người dùng yêu cầu dừng quá trình quét.")
            break

        try:
            nickname = user_elem.text.strip() or f"Bạn bè {idx}"
            user_elem.click()
            time.sleep(1.0)

            username = extract_current_chat_username(browser)

            if not username:
                log_cb(f"[{idx}/{len(all_user)}] Không trích xuất được username của: {nickname}")
                continue

            u_lower = username.lower()
            if u_lower in existing_map:
                existing_map[u_lower]["nickname"] = nickname
                log_cb(f"[{idx}/{len(all_user)}] Đã có: {nickname} (@{username})")
            else:
                new_friend = {
                    "username": username,
                    "nickname": nickname,
                    "enabled": True,
                    "status": "Chưa gửi"
                }
                current_friends.append(new_friend)
                existing_map[u_lower] = new_friend
                count_new += 1
                log_cb(f"[{idx}/{len(all_user)}] [Mới] Đã thêm: {nickname} (@{username})")

        except Exception as e:
            log_cb(f"[{idx}/{len(all_user)}] Bỏ qua do lỗi: {e}")

    save_friends(current_friends, account_id)
    log_cb(f"[Hoàn tất] Đã cập nhật danh sách bạn bè! ({count_new} bạn mới).")
    return current_friends


# ----------------------------
# GỬI TIN NHẮN THEO DANH SÁCH CHỌN
# ----------------------------

def send_messages_to_selected(browser, wait, message=None, delay_sec=3, log_cb=print, should_stop=None, account_id=None):
    """
    Chỉ gửi tin nhắn cho những bạn bè có 'enabled' == True của tài khoản cụ thể.
    Trả về (sent_count, total_count).
    """
    config = load_config(account_id)
    msg_text = message or config.get("message", "Chào {nickname}, rep chuỗi streak nè {time}!")

    all_friends = load_friends(account_id)
    selected_targets = {f["username"].lower(): f for f in all_friends if f.get("enabled", True)}

    if not selected_targets:
        log_cb("[Thông báo] Không có bạn bè nào được chọn để gửi tin nhắn.")
        return 0, 0

    log_cb(f"Bắt đầu gửi tin nhắn cho {len(selected_targets)} bạn bè đã được chọn...")
    log_cb(f"Nội dung gửi: \"{msg_text}\" | Giãn cách an toàn: {delay_sec}s")

    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)

    all_user = []
    selectors = [
        "//*[contains(@class, 'PInfoNickname')]",
        "//p[contains(@class, 'Nickname')]",
        "//div[contains(@class, 'Nickname')]",
        "//*[@data-e2e='conversation-item']",
        "//*[@data-e2e='chat-list-item']"
    ]
    for sel in selectors:
        try:
            found = wait.until(EC.presence_of_all_elements_located((By.XPATH, sel)))
            if found:
                all_user = found
                break
        except Exception:
            continue

    sent_count = 0
    for idx, user_elem in enumerate(all_user, start=1):
        if should_stop and should_stop():
            log_cb("[Dừng] Đã dừng tiến trình gửi tin nhắn.")
            break

        try:
            user_elem.click()
            time.sleep(1.0)

            username = extract_current_chat_username(browser)
            if not username:
                continue

            u_lower = username.lower()
            if u_lower not in selected_targets:
                continue

            target_friend = selected_targets[u_lower]
            actual_msg = render_message_template(msg_text, target_friend)
            log_cb(f"-> Đang gửi tin nhắn cho: {target_friend['nickname']} (@{username}): \"{actual_msg}\"")

            input_selectors = [
                "//div[contains(@class, 'public-DraftStyleDefault-block')]",
                "//div[@contenteditable='true']",
                "//*[@data-e2e='chat-input']"
            ]
            message_box = None
            for i_sel in input_selectors:
                try:
                    boxes = browser.find_elements(By.XPATH, i_sel)
                    if boxes:
                        message_box = boxes[0]
                        break
                except Exception:
                    continue

            if message_box:
                message_box.click()
                time.sleep(0.5)
                message_box.send_keys(actual_msg)
                message_box.send_keys(Keys.RETURN)

                current_time = time.strftime("%H:%M:%S %d/%m/%Y")
                target_friend["status"] = f"Đã gửi ({current_time})"
                save_friends(all_friends, account_id)

                sent_count += 1
                log_cb(f"   [Thành công] Đã gửi tới @{username}! Nghỉ {delay_sec}s...")
                time.sleep(delay_sec)
            else:
                log_cb(f"   [Thất bại] Không tìm thấy ô nhập tin nhắn của @{username}")
                target_friend["status"] = "Lỗi ô chat"
                save_friends(all_friends, account_id)

        except Exception as e:
            log_cb(f"   [Lỗi] Không thể gửi cho mục {idx}: {e}")

    log_cb(f"[Hoàn thành] Đã gửi tin nhắn cho {sent_count}/{len(selected_targets)} bạn bè được chọn.")
    return sent_count, len(selected_targets)
