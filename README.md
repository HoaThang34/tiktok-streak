# TikTok Streak Manager (Multi-Account Web Automation Dashboard)

Ứng dụng web cục bộ chạy trên máy tính cá nhân giúp tự động hóa quá trình gửi tin nhắn duy trì chuỗi **Streak** trên TikTok an toàn, tiện lợi, hỗ trợ **quản lý và chạy nhiều tài khoản (nhiều cookies)**.

Giao diện được thiết kế theo phong cách **Shadcn UI Light Mode**: tối giản, thanh lịch, sử dụng 100% biểu tượng SVG, phản hồi tức thì và không có chuyển động rườm rà.

---

## Điểm Nổi Bật

* **Hỗ trợ đa tài khoản (Multi-Account & Multi-Cookie)**:
  * Thêm, đổi tên, xóa và quản lý nhiều tài khoản TikTok không giới hạn.
  * Mỗi tài khoản có phiên làm việc (cookies), cấu hình tin nhắn, thời gian giãn cách và danh sách bạn bè riêng biệt.
* **Chạy tuần tự từng tài khoản an toàn tuyệt đối**:
  * Cho phép người dùng tùy ý tích chọn các tài khoản muốn chạy trong mỗi đợt.
  * Cơ chế thực thi tuần tự: **Khởi chạy tài khoản -> nạp cookies -> gửi tin nhắn streak -> tắt hoàn toàn cửa sổ Chrome -> nghỉ ngắn -> chuyển sang tài khoản tiếp theo**.
  * Giải phóng bộ nhớ và tránh triệt để xung đột phiên đăng nhập giữa các tài khoản.
* **Bổ sung trạng thái chi tiết theo từng tài khoản**:
  * Ghi nhận và hiển thị rõ ràng **thời gian lần cuối đăng nhập** (`last_login`).
  * Trạng thái phiên làm việc (`Sẵn sàng (N cookies)` / `Chưa có cookies`).
  * Trạng thái và thời gian lần cuối chạy (`Hoàn thành (X/Y bạn)`, `Đang chạy...`, `Lỗi...`).
* **Đăng nhập linh hoạt qua Cookies / QR Code**:
  * Đăng nhập quét mã QR trực tiếp từ ứng dụng TikTok điện thoại cho từng tài khoản riêng biệt. Không cần nhập mật khẩu, không lo bị chặn hay gặp captcha.
* **Template tin nhắn thời gian động riêng theo tài khoản**:
  * Hỗ trợ các biến: `{time}`, `{date}`, `{datetime}`, `{hour}`, `{minute}`, `{second}`, `{nickname}`, `{username}`.
  * Khung xem trước trực tiếp (Live Preview) với đồng hồ thời gian thực.
* **Cơ chế an toàn cao**:
  * Tùy chỉnh khoảng nghỉ (giây) giữa các lượt gửi để tránh spam.
  * Hỗ trợ chế độ chạy ẩn (Headless) hoặc hiển thị trình duyệt theo từng tài khoản.
  * Nút dừng khẩn cấp bất cứ lúc nào (tự động đóng trình duyệt ngay lập tức).

---

## Cấu Trúc Thư Mục

```text
tiktok-streak/
├── app.py             # Máy chủ HTTP cục bộ phục vụ Web Dashboard & API đa tài khoản
├── utils.py           # Module Selenium lõi & trình quản lý đa tài khoản, cookies, bạn bè
├── web/
│   └── index.html     # Giao diện Web Dashboard (Shadcn Light Mode, SVG icons)
├── accounts.json      # Danh sách tài khoản, thời gian lần cuối đăng nhập, trạng thái
├── accounts/          # Thư mục lưu dữ liệu độc lập của từng tài khoản (được bảo mật trong .gitignore)
│   ├── acc_1/
│   │   ├── cookies.json       # Phiên đăng nhập riêng của tài khoản 1
│   │   ├── config.json        # Cấu hình tin nhắn riêng của tài khoản 1
│   │   ├── friends.json       # Danh sách bạn bè riêng của tài khoản 1
│   │   └── friends.csv        # Danh sách bạn bè dạng bảng tính CSV
│   └── acc_2/...
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

## Hướng Dẫn Sử Dụng Đa Tài Khoản

### Bước 1: Quản lý & Đăng nhập / Nạp Cookies tài khoản
1. Tại mục **"Quản Lý Danh Sách Tài Khoản TikTok"**:
   * Nhấn nút **"+ Thêm tài khoản mới"**:
     * Bạn có thể tạo tài khoản trống (đăng nhập sau), HOẶC dán cookies ngay, HOẶC chọn file `.json` cookies có sẵn trên máy.
   * Để nạp/cập nhật cookie cho tài khoản bất kỳ, nhấn nút **"Cookie / Đăng nhập"** trên dòng tài khoản đó. Có 3 lựa chọn linh hoạt:
     * **Cách 1 - Quét mã QR**: Mở Chrome quét mã QR từ app TikTok điện thoại, tự động lưu cookies sau khi quét xong.
     * **Cách 2 - Dán Cookies**: Dán mảng JSON cookies (xuất từ Cookie-Editor / EditThisCookie) hoặc chuỗi Header `sessionid=...; sid_tt=...;` và nhấn Lưu.
     * **Cách 3 - Tải file .json**: Bấm chọn file `cookies.json` trên máy tính để nạp vào tài khoản ngay lập tức.
   * Sau khi nạp cookie thành công, tài khoản sẽ chuyển sang trạng thái **"Sẵn sàng"** và ghi nhận **thời gian lần cuối đăng nhập**.

### Bước 2: Thiết lập mẫu tin nhắn & danh sách bạn bè riêng
1. Nhấn nút **"Quản lý"** trên tài khoản bạn muốn thiết lập.
2. Tại khu vực **"Cài Đặt Riêng"**:
   * Tùy chỉnh mẫu tin nhắn streak (sử dụng các tag `{time}`, `{nickname}`, v.v.).
   * Cài đặt khoảng nghỉ an toàn và chế độ chạy ẩn (Headless).
   * Nhấn **"Lưu cài đặt tài khoản này"**.
3. Tại khu vực **"Danh Sách Bạn Bè Hộp Thư"**:
   * Nhấn **"Quét bạn bè từ TikTok"** để tool nạp danh bạ hộp thư của tài khoản này.
   * Tích chọn những bạn bè muốn gửi streak, bỏ tích những bạn bè không muốn gửi.

### Bước 3: Khởi chạy tuần tự nhiều tài khoản
1. Tại bảng danh sách tài khoản, tích chọn vào ô vuông **"Chạy"** của những tài khoản bạn muốn chạy đợt này (hoặc bấm **"Chọn tất cả để chạy"**).
2. Nhấn nút lớn: **"▶ Bắt đầu chạy tuần tự các tài khoản đã chọn"**.
3. Quy trình tự động diễn ra:
   * **Tài khoản 1**: Mở Chrome -> Nạp cookies -> Gửi tin nhắn streak cho bạn bè được chọn -> Cập nhật trạng thái & thời gian gửi -> **Tắt hoàn toàn cửa sổ Chrome**.
   * Nghỉ ngắn 3 giây.
   * **Tài khoản 2**: Mở Chrome -> Nạp cookies -> Gửi tin nhắn streak -> **Tắt hoàn toàn cửa sổ Chrome** -> ...
4. Theo dõi chi tiết mọi diễn biến tại khung **Nhật ký hoạt động (Live Logs)**.
5. Bạn có thể nhấn **"Dừng lại khẩn cấp"** bất cứ lúc nào để lập tức ngắt tiến trình và đóng trình duyệt.

---

## Bảo Mật Thông Tin
* Toàn bộ dữ liệu cookie của mọi tài khoản được lưu trữ an toàn trong thư mục `accounts/` và file `cookies.json`.
* Thư mục này đã được tự động loại trừ trong file `.gitignore` để tránh rủi ro rò rỉ dữ liệu khi đẩy lên Git.
