# 📖 TỔNG QUAN DỰ ÁN (PROJECT OVERVIEW)

## 1. Giới Thiệu & Mục Tiêu Dự Án

**TikTok Streak Manager** là ứng dụng tự động hóa cục bộ (Desktop Web Automation Tool) chạy trên máy tính cá nhân. Mục đích chính:
1. **Duy trì chuỗi Streak tin nhắn TikTok tự động**, an toàn và không bị gián đoạn.
2. **Hỗ trợ quản lý và chạy đa tài khoản (Multi-Account, Multi-Cookie)** trên cùng một máy mà không bị xung đột phiên đăng nhập hay chiếm dụng tài nguyên kéo dài.
3. **Cung cấp Web Dashboard trực quan, thẩm mỹ cao (Shadcn UI Light Mode)** để người dùng dễ dàng theo dõi trạng thái, cấu hình tin nhắn động, quản lý bạn bè và điều khiển các tác vụ chỉ bằng một cú nhấp chuột.

---

## 2. Công Nghệ Sử Dụng (Tech Stack)

Dự án được xây dựng theo định hướng **nhẹ tối đa (Ultra Lightweight), di động (Portable), không phụ thuộc vào hệ thống phức tạp**:

| Thành Phần | Công Nghệ Sử Dụng | Lý Do Lựa Chọn & Đặc Điểm |
| :--- | :--- | :--- |
| **Backend Core** | **Python (Standard Library)**: `http.server`, `threading`, `json`, `csv`, `socket`, `webbrowser` | Không cần cài đặt framework cồng kềnh (Flask, FastAPI, Django). Giúp ứng dụng khởi động tức thì trong < 1 giây. |
| **Trình Tự Động Hóa** | **Selenium WebDriver** (`selenium>=4.20.0`) | Điều khiển Google Chrome chính hãng trên máy người dùng, vượt qua các cơ chế kiểm tra bot thông thường nhờ giữ profile và cookie chuẩn. |
| **Frontend UI** | **Vanilla HTML5, CSS3, JavaScript (ES6+)** | Không dùng bundler (Webpack, Vite), không dùng framework (React/Vue), không dùng Tailwind CDN. Toàn bộ gói gọn trong 1 file `web/index.html` siêu tốc. |
| **Design System** | **Shadcn UI Light Mode** | Thiết kế thanh lịch, màu nền slate/zinc, 100% SVG inline icons, micro-transitions tinh tế, trải nghiệm người dùng cao cấp. |
| **Môi Trường Portable** | **Embedded Python 3.14 (`python_embed/`)** | Cho phép người dùng chạy ngay trên Windows bằng `run.bat` mà không cần cài đặt Python vào hệ điều hành. |

---

## 3. Sơ Đồ Kiến Trúc Toàn Cục

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          NGƯỜI DÙNG (TRÌNH DUYỆT WEB)                  │
│                     http://localhost:5000 (web/index.html)             │
│   - Bảng tài khoản      - Cài đặt tin nhắn riêng    - Quản lý bạn bè   │
│   - Nút chạy tuần tự    - Nhật ký trực tiếp (Logs)  - Modal nạp Cookie │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │ HTTP REST APIs (JSON)
                                     ▼ Polling 1.8s
┌────────────────────────────────────────────────────────────────────────┐
│                         MÁY CHỦ CỤC BỘ (app.py)                         │
│   - ThreadingHTTPServer & BaseHTTPRequestHandler                       │
│   - Quản lý trạng thái tác vụ nền (Background Thread & STOP_EVENT)     │
│   - Bộ đệm nhật ký LOG_BUFFER (tối đa 800 dòng, Thread-Safe)           │
│   - Định tuyến 17 REST API Endpoints                                   │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │ Gọi hàm nghiệp vụ
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       MODULE NGHIỆP VỤ LÕI (utils.py)                  │
│                                                                        │
│   [Quản Lý Đa Tài Khoản]       [Xử Lý Cookie & Config]                │
│   - load_accounts / save_...   - parse_cookie_data (JSON/Header/Net..) │
│   - create_account / delete    - render_message_template ({time},...)  │
│   - ensure_data_migration      - load_friends / save_friends (JSON/CSV)│
│                                                                        │
│   [Tự Động Hóa Trình Duyệt (Selenium)]                                 │
│   - init_browser (Headless / Hiển thị)                                 │
│   - login_with_cookies (Bơm cookie vào session Chrome)                 │
│   - extract_current_chat_username & extract_logged_in_username         │
│   - scan_friends (Quét danh bạ hộp thư TikTok)                         │
│   - send_messages_to_selected (Duyệt gửi tin nhắn streak tuần tự)      │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │ Đọc / Ghi tệp
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        HỆ THỐNG LƯU TRỮ CỤC BỘ                         │
│   - accounts.json                  (Danh bạ tài khoản & trạng thái)    │
│   - accounts/<acc_id>/cookies.json (Phiên đăng nhập độc lập)           │
│   - accounts/<acc_id>/config.json  (Cấu hình tin nhắn & delay riêng)   │
│   - accounts/<acc_id>/friends.json (Danh sách bạn bè & status gửi)     │
│   - accounts/<acc_id>/friends.csv  (Đồng bộ bạn bè dạng bảng tính)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Cơ Chế Chạy Tuần Tự Tuyệt Đối An Toàn (Sequential Runner)

Một trong những thiết kế quan trọng nhất của hệ thống là **chạy tuần tự từng tài khoản, không chạy đồng thời (concurrency)**:

```text
[Bắt đầu đợt chạy]
       │
       ▼
[Tài khoản 1]: Khởi chạy Chrome -> Nạp cookies -> Gửi tin streak cho các bạn bè được chọn
       │
       ▼
   Tắt HOÀN TOÀN cửa sổ Chrome (browser.quit) -> Giải phóng 100% RAM & Cookies
       │
       ▼
   Nghỉ an toàn 3 giây (Kiểm tra STOP_EVENT)
       │
       ▼
[Tài khoản 2]: Khởi chạy Chrome mới -> Nạp cookies riêng -> Gửi streak -> Tắt Chrome
       │
       ▼
[Lặp lại đến hết danh sách tài khoản đã chọn]
```

### Tại sao lại áp dụng mô hình này?
1. **Tránh xung đột phiên làm việc**: TikTok sử dụng cơ chế bảo mật phiên rất chặt. Nếu mở nhiều tab hoặc nhiều phiên Chrome cùng lúc với các tài khoản khác nhau, cookie dễ bị ghi đè chéo hoặc bị TikTok phát hiện bất thường và khóa tài khoản.
2. **Tiết kiệm RAM máy tính**: Mỗi phiên Chrome chiếm từ 300MB - 800MB RAM. Chạy tuần tự và tắt sau mỗi nick đảm bảo ứng dụng chạy mượt mà ngay cả trên máy cấu hình yếu.
3. **An toàn chống spam**: Khoảng nghỉ ngắn giữa các tài khoản giúp hành vi tự động tự nhiên hơn.

---

## 5. Cơ Chế Đăng Nhập & Nạp Cookie Linh Hoạt

Ứng dụng hỗ trợ 3 phương thức nạp phiên làm việc cho từng tài khoản:
1. **Quét mã QR trực tiếp**: Tự động mở Google Chrome tới `https://www.tiktok.com/login/qrcode`. Người dùng dùng app TikTok trên điện thoại quét mã QR. Ứng dụng tự động phát hiện `sessionid` / `sid_tt`, lưu vào `accounts/<acc_id>/cookies.json`, nhận diện username và đóng trình duyệt.
2. **Dán Cookies (Raw text)**: Hỗ trợ dán mảng JSON (xuất từ Cookie-Editor, EditThisCookie) hoặc chuỗi Header `sessionid=...; sid_tt=...;`. Hàm `parse_cookie_data()` tự động bóc tách và chuẩn hóa theo chuẩn Selenium.
3. **Nạp file `.json`**: Người dùng tải trực tiếp file cookie đã lưu trên máy tính.
