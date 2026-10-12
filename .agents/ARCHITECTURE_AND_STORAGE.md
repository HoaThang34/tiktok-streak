# 🏗️ KIẾN TRÚC HỆ THỐNG & MÔ HÌNH LƯU TRỮ DỮ LIỆU

## 1. Cấu Trúc Thư Mục Chi Tiết

```text
tiktok-streak/
├── .agents/                    # [MỚI] Knowledge Hub & Rules cho AI Coding Agents
│   ├── README.md               # Bản đồ điều hướng & tra cứu nhanh
│   ├── PROJECT_OVERVIEW.md     # Tổng quan nghiệp vụ, tech stack, sơ đồ luồng
│   ├── ARCHITECTURE_AND_STORAGE.md # Tài liệu kiến trúc và dữ liệu (File hiện tại)
│   ├── API_REFERENCE.md        # Toàn bộ danh mục 17 REST API Endpoints
│   ├── FEATURE_MODIFICATION_GUIDE.md # Hướng dẫn phạm vi sửa đổi khi cập nhật tính năng
│   └── rules/                  # Workspace Rules tự động kích hoạt
│       └── tiktok_streak_rules.md
├── AGENTS.md                   # Chỉ mục gốc cho các AI Agents khi vừa vào repo
├── app.py                      # Máy chủ HTTP cục bộ, bộ điều phối tác vụ nền & API
├── utils.py                    # Lõi nghiệp vụ: Quản lý accounts, cookies, bạn bè & Selenium
├── web/
│   └── index.html              # Frontend duy nhất (Shadcn UI Light Mode, CSS & JS thuần)
├── accounts.json               # Danh sách tài khoản người dùng, trạng thái và mốc thời gian
├── accounts/                   # Thư mục lưu dữ liệu cách ly của từng tài khoản (đã .gitignore)
│   ├── acc_1791483598488/      # ID tài khoản sinh theo định dạng: acc_<timestamp_ms>
│   │   ├── cookies.json        # Phiên làm việc (danh sách cookie Selenium)
│   │   ├── config.json         # Cấu hình tin nhắn streak và cài đặt chạy riêng
│   │   ├── friends.json        # Danh sách bạn bè và trạng thái gửi riêng
│   │   └── friends.csv         # Bảng tính bạn bè đồng bộ phục vụ người dùng xem ngoài
│   └── acc_.../
├── requirements.txt            # Thư viện phụ thuộc (selenium, python-dotenv)
├── run.bat                     # File thực thi một chạm trên hệ điều hành Windows
├── python_embed/               # Môi trường Python Portable 3.14 nhúng sẵn (không cần cài Python)
├── config.json                 # File config root (đã được .gitignore bảo vệ)
├── config.example.json         # File config mẫu cho người dùng clone mới
├── friends.json                # File friends root (đã được .gitignore bảo vệ)
├── friends.csv                 # File csv root (đã được .gitignore bảo vệ)
├── cookies.json                # File cookies root (đã được .gitignore bảo vệ)
├── .env                        # Biến môi trường tùy biến (nếu có)
└── .gitignore                  # Cấu hình loại trừ file nhạy cảm và môi trường ảo
```

---

## 2. Mô Hình Dữ Liệu & Lưu Trữ (Data Schemas)

Hệ thống sử dụng tệp tĩnh JSON và CSV để lưu trữ cục bộ, không dùng cơ sở dữ liệu SQL hay NoSQL bên ngoài nhằm giữ độ nhẹ và tính độc lập.

### 2.1. File `accounts.json`
Chứa danh bạ toàn bộ tài khoản TikTok mà người dùng đã tạo trong hệ thống.

```json
[
  {
    "id": "acc_1791483598488",
    "name": "Tài khoản chính",
    "username": "hoathang34",
    "last_login": "14:20:15 12/10/2026",
    "last_run": "Hoàn thành (5/5 bạn) - 14:25:00 12/10/2026",
    "status": "Sẵn sàng",
    "enabled": true
  }
]
```

* **Quy ước trường dữ liệu tĩnh (Lưu trong file):**
  * `id` *(string)*: Khóa chính định danh duy nhất (VD: `acc_1791483598488`).
  * `name` *(string)*: Tên gợi nhớ do người dùng đặt (VD: `Tài khoản chính`).
  * `username` *(string)*: TikTok handle trích xuất tự động từ profile (không kèm `@`).
  * `last_login` *(string)*: Chuỗi thời gian lần cuối đăng nhập/nạp cookie.
  * `last_run` *(string)*: Chuỗi thời gian và kết quả lượt chạy streak gần nhất.
  * `status` *(string)*: Trạng thái hiện tại (`Chưa có cookies`, `Sẵn sàng`, `Đang chạy...`, `Hoàn thành...`, `Lỗi...`).
  * `enabled` *(boolean)*: Đánh dấu có được tích chọn để chạy trong đợt chạy tuần tự hay không.

* **Trường dữ liệu động (Được tính toán động trong bộ nhớ khi gọi `load_accounts()`):**
  * `has_cookies` *(boolean)*: `true` nếu tồn tại file `cookies.json` và kích thước > 50 bytes.
  * `cookies_count` *(int)*: Số lượng cookie thực tế có trong file.
  * `friends_count` *(int)*: Tổng số bạn bè trong `friends.json` của tài khoản này.
  * `selected_friends_count` *(int)*: Số bạn bè đang có `enabled == True`.

> **LƯU Ý QUAN TRỌNG:** Trong hàm `save_accounts()` của `utils.py`, các trường động (`has_cookies`, `cookies_count`, `friends_count`, `selected_friends_count`) bị lọc bỏ để tránh làm rác file `accounts.json`. Nếu bạn thêm trường mới vào tài khoản, **BẮT BUỘC** phải khai báo trường đó trong `save_accounts()`.

---

### 2.2. File `accounts/<acc_id>/cookies.json`
Lưu trữ mảng cookie theo chuẩn Selenium WebDriver:
```json
[
  {
    "name": "sessionid",
    "value": "7b58a1...",
    "domain": ".tiktok.com",
    "path": "/",
    "expiry": 1820647890,
    "secure": true,
    "httpOnly": true,
    "sameSite": "None"
  }
]
```

* **Cơ chế nạp thông minh (`parse_cookie_data`):** Tự động nhận diện và chuyển đổi hợp lệ từ 4 nguồn:
  1. JSON mảng (từ các tiện ích Extension Chrome: Cookie-Editor, EditThisCookie).
  2. JSON object key-value dạng `{"sessionid": "..."}`.
  3. Chuỗi Header `sessionid=...; sid_tt=...;`.
  4. Định dạng Netscape Cookie (dạng bảng cách nhau bằng phím Tab).

---

### 2.3. File `accounts/<acc_id>/config.json`
Lưu cấu hình riêng biệt cho từng tài khoản:
```json
{
  "message": "Chào {nickname}, đây là tin nhắn giữ chuỗi được gửi tự động vào lúc {hour}:{minute}. Nếu cậu đọc được, đừng làm mất chuỗi với tớ nhé 😇",
  "delay_seconds": 3,
  "headless": true
}
```

* **Các biến thẻ động được hỗ trợ trong `render_message_template()`:**
  * `{time}`: Giờ:Phút:Giây (VD: `15:30:45`)
  * `{date}`: Ngày/Tháng/Năm (VD: `12/10/2026`)
  * `{datetime}`: Ngày giờ đầy đủ (VD: `15:30:45 12/10/2026`)
  * `{hour}`: Giờ hiện tại (VD: `15`)
  * `{minute}`: Phút hiện tại (VD: `30`)
  * `{second}`: Giây hiện tại (VD: `45`)
  * `{nickname}`: Tên hiển thị người nhận (Fallback sang username nếu không có)
  * `{username}`: TikTok handle người nhận

---

### 2.4. File `accounts/<acc_id>/friends.json` & `friends.csv`
Danh bạ bạn bè trong hộp thư TikTok của tài khoản đó.
* **JSON schema:**
```json
[
  {
    "username": "hoathang34",
    "nickname": "Hoa Thắng",
    "enabled": true,
    "status": "Đã gửi (14:22:10 12/10/2026)"
  }
]
```
* **Đồng bộ song song sang CSV:** Mỗi khi gọi `save_friends()`, hàm tự động ghi cả file `friends.json` và `friends.csv` (các cột: `Username`, `Nickname`, `Enabled`, `Status`).

---

### 2.5. Cơ Chế Di Chuyển Dữ Liệu Tự Động (`ensure_data_migration`)
Để hỗ trợ tương thích ngược với các phiên bản đơn tài khoản cũ (khi cookies, config và friends còn nằm ở thư mục gốc), hàm `ensure_data_migration()` trong `utils.py` sẽ:
1. Kiểm tra xem `accounts.json` đã tồn tại chưa.
2. Nếu chưa, tạo tài khoản đầu tiên `acc_1`.
3. Sao chép toàn bộ dữ liệu từ `cookies.json`, `config.json`, `friends.json`, `friends.csv` ở thư mục gốc vào `accounts/acc_1/`.
4. Khởi tạo `accounts.json` với `acc_1`.

---

## 3. Quản Lý Đa Luồng & Bộ Đệm Nhật Ký (Threading & Logs)

### 3.1. Bộ Điều Phối Tác Vụ Nền (Background Worker)
Trong `app.py`:
* `CURRENT_TASK = {"name": "", "is_running": False}`: Theo dõi trạng thái tác vụ.
* `STOP_EVENT = threading.Event()`: Cờ báo hiệu dừng tác vụ khẩn cấp.
* `TASK_THREAD = None`: Đối tượng thread daemon đang chạy.
* `run_background_task(task_name, target_func, *args, **kwargs)`:
  * Kiểm tra nếu đang có tác vụ chạy -> từ chối chạy đè.
  * Reset `STOP_EVENT.clear()`.
  * Bọc hàm thực thi trong `wrapper()` và chạy ở chế độ `daemon=True`.
  * Khối `finally` đảm bảo reset `CURRENT_TASK["is_running"] = False` và ghi log hoàn thành.

### 3.2. Hệ Thống Nhật Ký An Toàn Luồng (Thread-Safe Logs)
* `LOG_BUFFER = []`
* `LOG_LOCK = threading.Lock()`
* Tối đa lưu trữ 800 dòng log gần nhất. Khi vượt quá 800 dòng, tự động xóa dòng cũ nhất (`pop(0)`).
* UI frontend gọi `GET /api/logs?since=<index>` mỗi 1.8 giây để kéo log mới về hiển thị mượt mà.
