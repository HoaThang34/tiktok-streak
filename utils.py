from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time, re, csv, os, json, sys
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()

CONFIG_FILE = "config.json"
FRIENDS_FILE = "friends.json"
FRIENDS_CSV = "friends.csv"


# ----------------------------
# QUẢN LÝ CẤU HÌNH & BẠN BÈ
# ----------------------------

def load_config():
    """Tải cấu hình từ config.json, nếu chưa có thì nạp mặc định."""
    default_config = {
        "message": os.getenv("MESSAGE", "🔥"),
        "delay_seconds": 3,
        "headless": True
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass
    return default_config


def save_config(config):
    """Lưu cấu hình vào config.json và cập nhật .env."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    # Cập nhật nhẹ biến môi trường nếu cần
    if "message" in config:
        os.environ["MESSAGE"] = config["message"]


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



def load_friends():
    """
    Tải danh sách bạn bè từ friends.json (hoặc friends.csv).
    Trả về danh sách dict: [{'username': str, 'nickname': str, 'enabled': bool, 'status': str}]
    """
    friends = []

    # Ưu tiên đọc friends.json
    if os.path.exists(FRIENDS_FILE):
        try:
            with open(FRIENDS_FILE, "r", encoding="utf-8") as f:
                friends = json.load(f)
                return friends
        except Exception:
            pass

    # Nếu chưa có JSON thì đọc từ friends.csv (tương thích ngược)
    if os.path.exists(FRIENDS_CSV):
        try:
            with open(FRIENDS_CSV, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    u = row.get("Username", "").strip()
                    if not u:
                        continue
                    nick = row.get("Nickname", u).strip()
                    # Mặc định enabled là True
                    enabled_str = str(row.get("Enabled", "True")).strip().lower()
                    enabled = enabled_str not in ["false", "0", "no"]
                    friends.append({
                        "username": u,
                        "nickname": nick or u,
                        "enabled": enabled,
                        "status": "Chưa gửi"
                    })
        except Exception:
            pass

    return friends


def save_friends(friends):
    """Lưu danh sách bạn bè vào cả friends.json và friends.csv."""
    # 1. Lưu friends.json
    with open(FRIENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(friends, f, indent=4, ensure_ascii=False)

    # 2. Đồng bộ sang friends.csv
    with open(FRIENDS_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Nickname", "Enabled", "Status"])
        for item in friends:
            writer.writerow([
                item.get("username", ""),
                item.get("nickname", item.get("username", "")),
                item.get("enabled", True),
                item.get("status", "Chưa gửi")
            ])


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
        raise FileNotFoundError(
            f"Không tìm thấy file '{cookie_file}'. "
            f"Vui lòng bấm 'Đăng nhập / Cập nhật Cookies' trên giao diện Dashboard trước."
        )

    log_cb("[1/3] Đang mở trang TikTok...")
    browser.get("https://www.tiktok.com")
    time.sleep(2)

    log_cb(f"[2/3] Đang nạp cookies từ '{cookie_file}'...")
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

    log_cb("[3/3] Đang làm mới trang để xác thực phiên đăng nhập...")
    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)
    log_cb("[OK] Đăng nhập bằng cookies thành công!")


def extract_current_chat_username(browser):
    """
    Trích xuất chính xác username (@handle) của người bạn trong cuộc trò chuyện đang mở trên TikTok.
    """
    # 1. Ưu tiên thẻ a có chứa '@' trong text (Chat header chuẩn của TikTok: "Tên\n@username")
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

    # 3. Quét ngược danh sách link có href /@ (bỏ qua các link chung và link video)
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

def scan_friends(browser, wait, log_cb=print, should_stop=None):
    """
    Quét danh sách bạn bè từ hộp thư TikTok.
    Trả về danh sách bạn bè cập nhật.
    """
    log_cb("Đang truy cập hộp thư tin nhắn TikTok...")
    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)

    # Tìm phần tử danh sách hội thoại với selector linh hoạt
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
        return load_friends()

    log_cb(f"Tìm thấy {len(all_user)} cuộc trò chuyện. Bắt đầu thu thập thông tin...")
    current_friends = load_friends()
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

            # Lấy username chính xác của cuộc trò chuyện hiện tại
            username = extract_current_chat_username(browser)

            if not username:
                log_cb(f"[{idx}/{len(all_user)}] Không trích xuất được username của: {nickname}")
                continue

            u_lower = username.lower()
            if u_lower in existing_map:
                # Cập nhật nickname nếu có thay đổi
                existing_map[u_lower]["nickname"] = nickname
                log_cb(f"[{idx}/{len(all_user)}] Đã có: {nickname} (@{username})")
            else:
                new_friend = {
                    "username": username,
                    "nickname": nickname,
                    "enabled": True,  # Mặc định người mới được chọn
                    "status": "Chưa gửi"
                }
                current_friends.append(new_friend)
                existing_map[u_lower] = new_friend
                count_new += 1
                log_cb(f"[{idx}/{len(all_user)}] [Mới] Đã thêm: {nickname} (@{username})")

        except Exception as e:
            log_cb(f"[{idx}/{len(all_user)}] Bỏ qua do lỗi: {e}")

    save_friends(current_friends)
    log_cb(f"[Hoàn tất] Đã cập nhật danh sách bạn bè! ({count_new} bạn mới).")
    return current_friends


# ----------------------------
# GỬI TIN NHẮN THEO DANH SÁCH CHỌN
# ----------------------------

def send_messages_to_selected(browser, wait, message=None, delay_sec=3, log_cb=print, should_stop=None):
    """
    Chỉ gửi tin nhắn cho những bạn bè có 'enabled' == True.
    """
    config = load_config()
    msg_text = message or config.get("message", "🔥")

    all_friends = load_friends()
    selected_targets = {f["username"].lower(): f for f in all_friends if f.get("enabled", True)}

    if not selected_targets:
        log_cb("[Thông báo] Không có bạn bè nào được chọn để gửi tin nhắn.")
        return

    log_cb(f"Bắt đầu gửi tin nhắn cho {len(selected_targets)} bạn bè đã được chọn...")
    log_cb(f"Nội dung gửi: \"{msg_text}\" | Giãn cách an toàn: {delay_sec}s")

    browser.get("https://www.tiktok.com/messages?lang=vi")
    time.sleep(3)

    # Tìm danh sách cuộc trò chuyện
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

            # Lấy username chính xác cuộc trò chuyện hiện tại
            username = extract_current_chat_username(browser)

            if not username:
                continue

            u_lower = username.lower()
            if u_lower not in selected_targets:
                # Bỏ qua nếu không được chọn
                continue

            target_friend = selected_targets[u_lower]
            actual_msg = render_message_template(msg_text, target_friend)
            log_cb(f"-> Đang gửi tin nhắn cho: {target_friend['nickname']} (@{username}): \"{actual_msg}\"")

            # Tìm khung soạn thảo tin nhắn
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
                
                # Cập nhật trạng thái kèm thời gian + ngày gửi lần cuối
                current_time = time.strftime("%H:%M:%S %d/%m/%Y")
                target_friend["status"] = f"Đã gửi ({current_time})"
                save_friends(all_friends)
                
                sent_count += 1
                log_cb(f"   [Thành công] Đã gửi tới @{username}! Nghỉ {delay_sec}s...")
                time.sleep(delay_sec)
            else:
                log_cb(f"   [Thất bại] Không tìm thấy ô nhập tin nhắn của @{username}")
                target_friend["status"] = "Lỗi ô chat"
                save_friends(all_friends)

        except Exception as e:
            log_cb(f"   [Lỗi] Không thể gửi cho mục {idx}: {e}")

    log_cb(f"[Hoàn thành] Đã gửi tin nhắn cho {sent_count}/{len(selected_targets)} bạn bè được chọn.")
