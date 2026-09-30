# TikTok Streak Manager v2.0 (Giao Diện Trực Quan & Chọn Lọc Bạn Bè)

Công cụ tự động gửi tin nhắn hàng ngày để duy trì chuỗi tương tác (**TikTok Streak**) với bạn bè đã chọn:
* **Không gửi bừa bãi**: Chủ động chọn lọc ai được nhận tin nhắn, ai bỏ qua.
* **Giao diện trực quan**: Quản lý danh sách bạn bè, cấu hình nội dung tin nhắn, độ trễ và theo dõi tiến trình trực tiếp.
* **Đăng nhập bằng Cookies**: Không cần nhập mật khẩu, không dính Captcha, không sợ OTP.

---

## 1. Cài đặt môi trường

Mở Terminal và cài đặt thư viện cần thiết:
```powershell
pip install -r requirements.txt
```

---

## 2. Khởi chạy Tool Quản Lý

Bạn có 2 cách để mở ứng dụng:
* **Cách 1 (Nhanh nhất trên Windows):** Click đúp vào file `run.bat`.
* **Cách 2:** Chạy lệnh:
  ```powershell
  python app.py
  ```

---

## 3. Các tính năng chính trong Tool

### 🔑 Quản lý Cookies
* Nếu trạng thái báo `🔴 Cookies: Chưa có`, bấm nút **"🔑 Đăng nhập & Lưu Cookies Mới"**.
* Trình duyệt sẽ mở ra trang TikTok, bạn chỉ cần dùng app TikTok trên điện thoại quét mã QR hoặc đăng nhập tài khoản một lần duy nhất.

### ⚙️ Cấu hình tin nhắn & Giãn cách
* **Nội dung gửi:** Nhập icon hoặc lời chào (mặc định: `🔥`).
* **Giãn cách (giây):** Thời gian chờ giữa 2 lần gửi tin nhắn (khuyên dùng 3 - 5 giây để an toàn cho tài khoản).
* **Chạy ẩn Chrome (Headless):** Tích chọn để bot chạy ngầm không chiếm màn hình.

### 👥 Quét & Lựa chọn bạn bè
* **Nút `[🔍 Quét bạn bè từ TikTok]`**: Tự động mở hộp thư và lấy danh sách các bạn bè gần đây kèm Nickname và Username.
* **Lựa chọn người nhận**:
  * Nhấn đúp chuột (hoặc phím Space) vào bất kỳ dòng nào để chuyển đổi giữa `☑ GỬI` và `☐ BỎ QUA`.
  * Có các nút tiện ích: `[☑ Chọn tất cả]`, `[☐ Bỏ chọn tất cả]`.
  * Thêm bạn bè thủ công qua nút `[➕ Thêm thủ công]`.
  * Tìm kiếm nhanh bằng ô `🔍 Tìm`.

### 🚀 Bắt đầu gửi
* Nhấn nút lớn **`[🚀 BẮT ĐẦU GỬI TIN NHẮN (CHỈ GỬI CHO BẠN BÈ ĐÃ CHỌN)]`**.
* Khung nhật ký bên dưới sẽ hiển thị chi tiết từng người được gửi kèm thời gian thực.
* Có thể bấm **`[⏹️ DỪNG LẠI]`** bất cứ lúc nào.

---

## 4. Chạy qua dòng lệnh (CLI - Nếu không muốn mở giao diện)

* Quét bạn bè:
  ```powershell
  python my-friends.py
  ```
* Gửi tin nhắn cho danh sách đã cấu hình:
  ```powershell
  python main.py
  ```
*(Lưu ý: Ngay cả khi chạy bằng lệnh `main.py`, bot vẫn đọc cài đặt từ file và **chỉ gửi cho những người bạn đã chọn bật `Enabled = True`**, tuyệt đối không gửi bừa bãi).*
