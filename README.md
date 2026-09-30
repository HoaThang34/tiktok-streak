# TikTok Streak Manager (Local Web Automation Dashboard)

Ứng dụng web cục bộ chạy trên máy tính cá nhân giúp tự động hóa quá trình gửi tin nhắn duy trì chuỗi **Streak** trên TikTok an toàn, tiện lợi và không bị gửi bừa bãi.

Giao diện được thiết kế theo phong cách **Shadcn UI Light Mode**: tối giản, thanh lịch, sử dụng 100% biểu tượng SVG, phản hồi tức thì và không có chuyển động rườm rà.

---

## Điểm Nổi Bật

* **Chạy cục bộ 100% (Local Server)**: Hoạt động trực tiếp trên máy của bạn (`http://localhost:5000`), không phụ thuộc server trung gian, đảm bảo an toàn tuyệt đối cho tài khoản và dữ liệu cá nhân.
* **Đăng nhập linh hoạt qua Cookies / QR Code**: Đăng nhập quét mã QR trực tiếp từ ứng dụng TikTok điện thoại hoặc lưu session cookies một lần duy nhất. Không cần nhập mật khẩu, không lo bị chặn hay gặp captcha.
* **Chọn lọc người nhận thông minh (Không gửi bừa bãi)**: Tự động quét danh sách hộp thư, trích xuất chính xác Nickname và TikTok Handle (`@username`). Bạn chủ động tích chọn từng người nhận hoặc bỏ qua.
* **Template tin nhắn thời gian động**:
  * Hỗ trợ các biến: `{time}`, `{date}`, `{datetime}`, `{hour}`, `{minute}`, `{second}`, `{nickname}`, `{username}`.
  * Tích hợp các nút bấm chèn nhanh một chạm (Click-to-insert).
  * Khung xem trước trực tiếp (Live Preview) với đồng hồ thời gian thực.
* **Lưu vết trạng thái chi tiết**: Cột trạng thái ghi nhận rõ ràng cả thời gian và ngày gửi lần cuối dạng `Đã gửi (HH:MM:SS DD/MM/YYYY)`.
* **Cơ chế an toàn cao**:
  * Tùy chỉnh khoảng nghỉ (giây) giữa các lượt gửi để tránh spam.
  * Hỗ trợ chế độ chạy ẩn (Headless) để không chiếm màn hình.
  * Nút dừng khẩn cấp bất cứ lúc nào.
* **Xóa dữ liệu trắng một click**: Nút "Xóa toàn bộ dữ liệu" giúp đưa công cụ về trạng thái ban đầu khi cần thiết lập lại.

---

## Cấu Trúc Thư Mục

```text
tiktok-streak/
├── app.py             # Máy chủ HTTP cục bộ phục vụ Web Dashboard & API
├── utils.py           # Module Selenium lõi xử lý quét bạn bè, template và gửi tin
├── web/
│   └── index.html     # Giao diện Web Dashboard (Shadcn Light Mode, SVG icons)
├── config.json        # Cấu hình tin nhắn, thời gian giãn cách, chế độ chạy ẩn
├── friends.json       # Danh sách bạn bè và trạng thái chọn lọc (JSON)
├── friends.csv        # Danh sách bạn bè định dạng bảng tính (CSV)
├── cookies.json       # Phiên làm việc TikTok (được bảo mật trong .gitignore)
├── requirements.txt   # Danh sách thư viện Python cần thiết
├── run.bat            # Phím tắt khởi chạy nhanh trên Windows
├── .env               # Biến môi trường
├── .gitignore         # Cấu hình loại trừ file nhạy cảm và file rác
└── README.md          # Tài liệu hướng dẫn sử dụng
```

---

## Yêu Cầu Hệ Thống

1. **Hệ điều hành**: Windows 10/11 (hoặc macOS / Linux).
2. **Python**: Phiên bản 3.8 trở lên.
3. **Trình duyệt**: Google Chrome đã được cài đặt trên máy.

---

## Cài Đặt & Khởi Chạy

### 1. Cài đặt thư viện phụ thuộc
Mở terminal tại thư mục dự án và chạy lệnh:
```powershell
pip install -r requirements.txt
```

### 2. Khởi chạy ứng dụng
* **Cách 1 (Nhanh nhất trên Windows):** Nhấp đúp chuột vào file `run.bat`.
* **Cách 2 (Qua dòng lệnh):**
  ```powershell
  python app.py
  ```

Hệ thống sẽ khởi động máy chủ cục bộ và tự động mở giao diện quản trị trên Google Chrome tại:
```
http://localhost:5000
```

---

## Hướng Dẫn Sử Dụng

### Bước 1: Đăng nhập & Lưu Cookies
* Nếu thanh trạng thái góc phải hiển thị `Cookies: Chưa có`, nhấn vào nút **"Đăng nhập / Cập nhật Cookies"**.
* Cửa sổ trình duyệt Chrome sẽ mở ra trang đăng nhập TikTok. Bạn chỉ cần dùng ứng dụng TikTok trên điện thoại quét mã QR để đăng nhập.
* Sau khi đăng nhập thành công, hệ thống tự động lưu cookies vào máy và sẵn sàng hoạt động.

### Bước 2: Quét & Lọc danh sách bạn bè
* Nhấn nút **"Quét bạn bè từ TikTok"** để tool tự động mở hộp thư và nạp danh sách các bạn bè gần đây.
* Tại bảng danh sách bạn bè:
  * Tích chọn ô vuông phía trước những bạn bè muốn gửi tin nhắn duy trì Streak.
  * Bỏ tích những bạn bè không muốn gửi.
  * Có thể sử dụng các nút **"Chọn tất cả"**, **"Bỏ chọn tất cả"** hoặc ô **"Tìm kiếm"** theo tên / username.
  * Bổ sung người nhận mới qua nút **"Thêm thủ công"**.

### Bước 3: Soạn nội dung tin nhắn với Template
* Nhập mẫu tin nhắn vào ô **"Nội dung tin nhắn"**.
* Bạn có thể bấm vào các thẻ template bên dưới để chèn nhanh:
  * `{time}`: Thời gian hiện tại (`15:30:45`)
  * `{date}`: Ngày hiện tại (`30/09/2026`)
  * `{datetime}`: Cả ngày và giờ (`15:30:45 30/09/2026`)
  * `{hour}`: Giờ hiện tại (`15`)
  * `{minute}`: Phút hiện tại (`30`)
  * `{nickname}`: Tên hiển thị của bạn bè
  * `{username}`: TikTok Handle của bạn bè (`@handle`)
* Khung **Xem trước (Live Preview)** sẽ hiển thị ngay tức thì câu tin nhắn mẫu theo thời gian thực.
* Nhấn **"Lưu cấu hình"**.

### Bước 4: Khởi chạy gửi tin nhắn
* Nhấn nút **"Bắt đầu gửi tin nhắn Streak"**.
* Hệ thống sẽ tự động duyệt qua các bạn bè được chọn, soạn tin nhắn theo đúng template thời gian và gửi đi.
* Cột **Trạng thái** sẽ được cập nhật ngày giờ gửi lần cuối (ví dụ: `Đã gửi (15:22:58 30/09/2026)`).
* Theo dõi chi tiết từng thao tác tại khung **Nhật ký hoạt động (Live Logs)**.
* Có thể nhấn nút **"Dừng lại"** bất cứ lúc nào để ngắt tiến trình an toàn.

---

## Lưu Ý Về An Toàn & Bảo Mật

* **Không chia sẻ file `cookies.json`**: File này chứa phiên đăng nhập tài khoản TikTok của bạn và đã được cấu hình tự động loại trừ trong `.gitignore`.
* **Giãn cách an toàn**: Nên duy trì khoảng cách từ `3 - 5 giây` trở lên giữa mỗi lượt gửi tin nhắn để tránh bị TikTok cảnh báo tần suất gửi.
