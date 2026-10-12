# 📡 TÀI LIỆU TOÀN BỘ REST API (API REFERENCE)

Máy chủ cục bộ chạy qua lớp `DashboardHandler(BaseHTTPRequestHandler)` trong `app.py`. Mọi phản hồi API đều trả về định dạng `application/json; charset=utf-8` kèm header chống bộ nhớ đệm `Cache-Control: no-cache`.

---

## 1. Nhóm API Lấy Dữ Liệu (GET Requests)

### 1.1. `GET /api/status`
Lấy trạng thái tổng quan hệ thống, trạng thái tác vụ nền và danh sách đầy đủ các tài khoản.
* **Query Params:** Không có.
* **Response Output:**
```json
{
  "is_running": false,
  "task_name": "",
  "active_account_id": "acc_1791483598488",
  "accounts": [
    {
      "id": "acc_1791483598488",
      "name": "Tài khoản 1",
      "username": "hoathang34",
      "last_login": "14:20:15 12/10/2026",
      "last_run": "Hoàn thành (5/5 bạn)",
      "status": "Sẵn sàng",
      "enabled": true,
      "has_cookies": true,
      "cookies_count": 28,
      "friends_count": 12,
      "selected_friends_count": 5
    }
  ]
}
```

---

### 1.2. `GET /api/accounts`
Lấy danh sách các tài khoản trong `accounts.json`.
* **Response Output:** Mảng các object tài khoản (tương tự trường `accounts` ở `/api/status`).

---

### 1.3. `GET /api/config?account_id=<id>`
Lấy cấu hình riêng của một tài khoản.
* **Query Params:**
  * `account_id` *(tùy chọn)*: ID của tài khoản. Nếu không truyền, mặc định lấy theo `ACTIVE_ACCOUNT_ID`.
* **Response Output:**
```json
{
  "message": "Chào {nickname}, rep chuỗi streak nè {time}!",
  "delay_seconds": 3,
  "headless": true
}
```

---

### 1.4. `GET /api/friends?account_id=<id>`
Lấy danh sách bạn bè của một tài khoản.
* **Query Params:**
  * `account_id` *(tùy chọn)*: ID tài khoản cần xem bạn bè.
* **Response Output:**
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

---

### 1.5. `GET /api/logs?since=<index>`
Lấy các dòng log mới phát sinh từ chỉ mục `since`.
* **Query Params:**
  * `since` *(int)*: Vị trí dòng log cuối cùng client đã nhận (mặc định 0).
* **Response Output:**
```json
{
  "logs": [
    "[14:20:15] Máy chủ cục bộ đã khởi động tại http://localhost:5000",
    "[14:20:20] [Tài khoản 1] Bắt đầu gửi streak..."
  ],
  "next_index": 2
}
```

---

## 2. Nhóm API Quản Lý Tài Khoản (POST Requests)

### 2.1. `POST /api/accounts/create`
Tạo một tài khoản mới (hỗ trợ nạp kèm cookies ban đầu).
* **Request Body:**
```json
{
  "name": "Tài khoản 2",
  "cookies_raw": "[{\"name\": \"sessionid\", \"value\": \"...\"}]"
}
```
* **Response Output:**
```json
{
  "success": true,
  "account": {
    "id": "acc_1791483944504",
    "name": "Tài khoản 2",
    "username": "",
    "last_login": "14:25:44 12/10/2026",
    "last_run": "Chưa chạy",
    "status": "Sẵn sàng",
    "enabled": true
  }
}
```

---

### 2.2. `POST /api/accounts/import-cookies`
Nạp/Cập nhật cookies cho một tài khoản (qua dán text hoặc file JSON).
* **Request Body:**
```json
{
  "account_id": "acc_1791483944504",
  "cookies_raw": "sessionid=7b58...; sid_tt=...;"
}
```
* **Response Output:**
```json
{
  "success": true,
  "count": 28
}
```

---

### 2.3. `POST /api/accounts/update`
Cập nhật thông tin cơ bản của tài khoản (đổi tên hoặc bật/tắt chọn chạy).
* **Request Body:**
```json
{
  "id": "acc_1791483944504",
  "name": "Nick Phụ VIP",
  "enabled": true
}
```
* **Response Output:** `{"success": true}`

---

### 2.4. `POST /api/accounts/delete`
Xóa hoàn toàn tài khoản và thư mục dữ liệu `accounts/<id>/`.
* **Ràng buộc:** Không thể xóa khi `CURRENT_TASK["is_running"] == true`.
* **Request Body:** `{"id": "acc_1791483944504"}`
* **Response Output:** `{"success": true}`

---

### 2.5. `POST /api/accounts/toggle-all`
Bật hoặc tắt chọn toàn bộ danh sách tài khoản để chuẩn bị chạy tuần tự.
* **Request Body:** `{"state": true}` (hoặc `false`)
* **Response Output:** `{"success": true}`

---

### 2.6. `POST /api/accounts/select-active`
Đặt tài khoản đang được chọn để cấu hình trên giao diện Web.
* **Request Body:** `{"id": "acc_1791483944504"}`
* **Response Output:** `{"success": true, "active_account_id": "acc_1791483944504"}`

---

## 3. Nhóm API Cấu Hình & Bạn Bè (POST Requests)

### 3.1. `POST /api/config`
Lưu mẫu tin nhắn, thời gian giãn cách và chế độ chạy ẩn.
* **Request Body:**
```json
{
  "account_id": "acc_1791483944504",
  "message": "Chào {nickname}, rep streak nha {time}",
  "delay_seconds": 3,
  "headless": true,
  "apply_to_all": false
}
```
* **Tham số đặc biệt:** Nếu `apply_to_all: true`, hệ thống sẽ ghi đè cấu hình này vào **TẤT CẢ** các tài khoản hiện có trong hệ thống.
* **Response Output:** `{"success": true}` (hoặc `{"success": true, "applied_all": true}`)

---

### 3.2. `POST /api/friends/toggle`
Bật/tắt trạng thái gửi (`enabled`) của 1 người bạn cụ thể trong danh bạ.
* **Request Body:**
```json
{
  "account_id": "acc_1791483944504",
  "username": "hoathang34"
}
```
* **Response Output:** `{"success": true}`

---

### 3.3. `POST /api/friends/select-all`
Chọn hoặc bỏ chọn tất cả bạn bè của tài khoản đang thao tác.
* **Request Body:**
```json
{
  "account_id": "acc_1791483944504",
  "state": true
}
```
* **Response Output:** `{"success": true}`

---

### 3.4. `POST /api/friends/add`
Thêm thủ công một người bạn vào danh sách.
* **Request Body:**
```json
{
  "account_id": "acc_1791483944504",
  "username": "hoathang34",
  "nickname": "Hoa Thắng"
}
```
* **Response Output:** `{"success": true}` (hoặc lỗi 400 nếu trùng username).

---

### 3.5. `POST /api/friends/delete`
Xóa một người bạn khỏi danh sách bạn bè của tài khoản.
* **Request Body:**
```json
{
  "account_id": "acc_1791483944504",
  "username": "hoathang34"
}
```
* **Response Output:** `{"success": true}`

---

## 4. Nhóm API Điều Khiển Tác Vụ Tự Động Hóa (POST Automation)

### 4.1. `POST /api/send`
Khởi động tác vụ nền gửi tin nhắn streak tuần tự cho các tài khoản được chọn.
* **Request Body:**
```json
{
  "account_ids": ["acc_1791483598488", "acc_1791483944504"],
  "sync_message": "Nội dung áp dụng đồng bộ trước khi gửi (tùy chọn)"
}
```
* **Response Output:**
```json
{
  "success": true,
  "message": "Đã khởi chạy tác vụ."
}
```

---

### 4.2. `POST /api/scan`
Khởi động tác vụ nền quét danh bạ bạn bè từ hộp thư TikTok cho một tài khoản.
* **Request Body:** `{"account_id": "acc_1791483598488"}`
* **Response Output:** `{"success": true, "message": "Đã khởi chạy tác vụ."}`

---

### 4.3. `POST /api/login-cookies`
Khởi động tác vụ nền mở Google Chrome để người dùng quét mã QR trên điện thoại.
* **Request Body:** `{"account_id": "acc_1791483598488"}`
* **Response Output:** `{"success": true, "message": "Đã khởi chạy tác vụ."}`

---

### 4.4. `POST /api/stop`
Gửi tín hiệu ngắt khẩn cấp (`STOP_EVENT.set()`) để dừng ngay lập tức bất kỳ tác vụ nào đang chạy.
* **Request Body:** `{}`
* **Response Output:** `{"success": true}`

---

### 4.5. `POST /api/reset-data`
Xóa trắng cookies, danh sách bạn bè và khôi phục cài đặt mặc định của 1 tài khoản (hoặc toàn bộ).
* **Ràng buộc:** Không thể gọi khi đang có tác vụ chạy.
* **Request Body:** `{"account_id": "acc_1791483598488"}` (để trống nếu muốn reset toàn bộ).
* **Response Output:** `{"success": true}`

---

### 4.6. `POST /api/logs/clear`
Xóa trắng bộ đệm log trên server và khung hiển thị log trên web.
* **Request Body:** `{}`
* **Response Output:** `{"success": true}`
