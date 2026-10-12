# 🛠️ HƯỚNG DẪN PHẠM VI CHỈNH SỬA KHI UPDATE TÍNH NĂNG MỚI

> **Dành riêng cho AI Agents:** Đây là tài liệu quan trọng nhất giúp bạn **tiết kiệm 80-90% lượng token phân tích mã nguồn**. Khi nhận được yêu cầu thêm hoặc sửa tính năng, hãy đối chiếu ngay với các kịch bản bên dưới để biết chính xác cần sửa ở đâu, không cần quét toàn bộ project.

---

## 🎯 Danh Sách Các Kịch Bản Thường Gặp

* [Kịch bản 1: Thêm trường dữ liệu hoặc quản lý Tài khoản](#kịch-bản-1-thêm-trường-dữ-liệu-hoặc-quản-lý-tài-khoản)
* [Kịch bản 2: Thay đổi hoặc bổ sung cơ chế gửi tin nhắn Streak](#kịch-bản-2-thay-đổi-hoặc-bổ-sung-cơ-chế-gửi-tin-nhắn-streak)
* [Kịch bản 3: Thêm tùy chọn Cấu hình (Config) mới](#kịch-bản-3-thêm-tùy-chọn-cấu-hình-config-mới)
* [Kịch bản 4: Bổ sung Tác vụ nền mới (Background Task)](#kịch-bản-4-bổ-sung-tác-vụ-nền-mới-background-task)
* [Kịch bản 5: Nâng cấp / Tinh chỉnh Selenium TikTok Automation](#kịch-bản-5-nâng-cấp--tinh-chỉnh-selenium-tiktok-automation)
* [Kịch bản 6: Thêm hỗ trợ Proxy riêng cho từng tài khoản](#kịch-bản-6-thêm-hỗ-trợ-proxy-riêng-cho-từng-tài-khoản)
* [Kịch bản 7: Chỉnh sửa Giao diện (UI/UX) trong `web/index.html`](#kịch-bản-7-chỉnh-sửa-giao-diện-uiux-trong-webindexhtml)
* [Checklist Kiểm Tra An Toàn Trước Khi Hoàn Thành](#checklist-kiểm-tra-an-toàn-bắt-buộc)

---

### Kịch bản 1: Thêm trường dữ liệu hoặc quản lý Tài khoản
*Ví dụ: Thêm ghi chú (`note`), thêm phân nhóm (`group`), thêm proxy (`proxy`), hoặc thêm thời gian hẹn giờ (`schedule_time`).*

#### 1. File Backend: `utils.py`
1. **`save_accounts(accounts)` (Dòng ~197)**:
   * ⚠️ **BẮT BUỘC:** Hàm này có danh sách lọc thuộc tính sạch (`clean_list`). Nếu bạn không thêm trường mới vào dict này, **dữ liệu sẽ bị mất khi lưu vào `accounts.json`**.
   * Bổ sung: `"new_field": acc.get("new_field", default_value)`.
2. **`create_account(...)` (Dòng ~356)**:
   * Thêm tham số `new_field=...` và gán vào `new_acc` trước khi gọi `save_accounts()`.
3. **`load_accounts()` (Dòng ~139)**:
   * Thêm giá trị mặc định cho `new_field` nếu tài khoản cũ chưa có trường này.

#### 2. File Backend: `app.py`
1. **`POST /api/accounts/create` (Dòng ~437)**:
   * Đọc `new_field` từ `self.read_json_body()` và truyền vào `create_account()`.
2. **`POST /api/accounts/update` (Dòng ~472)**:
   * Thêm `if "new_field" in data: kwargs["new_field"] = data["new_field"]`.

#### 3. File Frontend: `web/index.html`
1. **Bảng tài khoản (`renderAccountsTable()`, Dòng ~984)**:
   * Thêm cột `<th>` mới trong `<table>` và thêm `<td>` hiển thị `acc.new_field`.
2. **Modal tạo tài khoản (`modalCreateAccount`, Dòng ~734)**:
   * Thêm `<input id="txtNewAccount..." class="form-input">`.
   * Cập nhật hàm `submitCreateAccount()` để gửi trường mới lên server.

---

### Kịch bản 2: Thay đổi hoặc bổ sung cơ chế gửi tin nhắn Streak
*Ví dụ: Thêm biến động mới (`{day_of_week}`, `{random_emoji}`), cơ chế Spintax `{Chào|Hi|Hello}`, hoặc đính kèm sticker/hình ảnh.*

#### 1. File Backend: `utils.py`
1. **`render_message_template(template, friend)` (Dòng ~497)**:
   * Khai báo biến mới trong dict `tags = {...}` (ví dụ: `"{random_emoji}": random.choice([...])`).
   * Nếu làm Spintax: Dùng biểu thức chính quy `re.sub(r'\{([^{}]+)\}', ...)` để tráo từ ngẫu nhiên trước khi thay thế tags.
2. **`send_messages_to_selected(...)` (Dòng ~828)**:
   * Nếu có gửi sticker / ảnh: Bổ sung bước upload file vào ô chat TikTok trước khi nhấn phím Enter (`Keys.RETURN`).

#### 2. File Frontend: `web/index.html`
1. **Chip gợi ý tag (`.template-chips`, Dòng ~597)**:
   * Thêm thẻ `<span class="template-chip" onclick="insertTag('{tên_tag}')">...</span>`.
2. **Hàm xem trước trực tiếp (`updateMessagePreview()`, Dòng ~1160)**:
   * Cập nhật logic JavaScript giả lập tag mới để người dùng nhìn thấy nội dung thực tế đổi màu trên màn hình theo thời gian thực.

---

### Kịch bản 3: Thêm tùy chọn Cấu hình (Config) mới
*Ví dụ: Thêm khoảng nghỉ ngẫu nhiên `delay_max`, số lượng bạn bè tối đa mỗi lần chạy `max_friends_per_run`, hoặc chế độ tự động thả tim tin nhắn cuối.*

#### 1. File Backend: `utils.py`
1. **`load_config(account_id)` (Dòng ~456)**:
   * Bổ sung giá trị mặc định vào dictionary `default_config`.
2. **`create_account()` (Dòng ~363), `delete_account()` (Dòng ~423), `reset_account_data()` (Dòng ~330 trong `app.py`)**:
   * Bổ sung key mới vào `default_cfg`.
3. **Sử dụng trong tác vụ (`send_messages_to_selected`)**:
   * Đọc `cfg.get("new_key", default)` và áp dụng vào logic chạy.

#### 2. File Backend: `app.py`
1. **`POST /api/config` (Dòng ~527)**:
   * Trong nhánh `if apply_to_all:` -> thêm logic gán `cfg["new_key"] = data["new_key"]`.
   * Trong nhánh lưu tài khoản đơn lẻ -> thêm `cfg["new_key"] = data["new_key"]`.

#### 3. File Frontend: `web/index.html`
1. **Khu vực HTML Cài Đặt Riêng (Dòng ~611)**:
   * Thêm input mới: `<input type="number" id="cfgNewKey" onchange="markConfigDirtyAndAutoSave()">`.
2. **Hàm nạp cấu hình (`loadActiveAccountDetails()`, Dòng ~1115)**:
   * Đọc `document.getElementById("cfgNewKey").value = cfg.new_key ?? default;`.
3. **Hàm lưu cấu hình (`saveActiveAccountConfig()`, Dòng ~1130)**:
   * Thêm `new_key: document.getElementById("cfgNewKey").value` vào payload gửi lên API.

---

### Kịch bản 4: Bổ sung Tác vụ nền mới (Background Task)
*Ví dụ: Thêm tác vụ "Kiểm tra tình trạng cookie hàng loạt (Check Live)", "Sao lưu dữ liệu ra file ZIP", hoặc "Hủy kết bạn không tương tác".*

#### 1. File Backend: `app.py`
1. **Viết hàm tác vụ worker**:
   ```python
   def task_custom_action(account_id, ...):
       acc = get_account(account_id)
       add_log(f"[{acc['name']}] Bắt đầu thực hiện tác vụ...")
       browser = None
       try:
           browser, wait = init_browser(headless=True)
           # LUÔN KIỂM TRA STOP_EVENT
           if STOP_EVENT.is_set():
               add_log("Tác vụ đã dừng.")
               return
           # Thực hiện nghiệp vụ...
       except Exception as e:
           add_log(f"[Lỗi]: {e}")
       finally:
           if browser:
               browser.quit()
               add_log("Đã đóng trình duyệt.")
   ```
2. **Đăng ký HTTP Endpoint trong `DashboardHandler.do_POST()`**:
   ```python
   if path == "/api/custom-action":
       data = self.read_json_body()
       acc_id = data.get("account_id")
       ok, msg = run_background_task("Tên tác vụ", task_custom_action, acc_id)
       self.send_json({"success": ok, "message": msg})
       return
   ```

#### 2. File Frontend: `web/index.html`
1. Thêm nút bấm `<button class="btn btn-secondary btn-sm" onclick="triggerCustomAction()">` vào vị trí phù hợp.
2. Viết hàm JavaScript:
   ```javascript
   async function triggerCustomAction() {
     if (isTaskRunning) return;
     try {
       const res = await fetch("/api/custom-action", {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ account_id: activeAccountId })
       });
       const data = await res.json();
       showToast(data.message);
       fetchStatus(false);
     } catch(e) {
       showToast("Lỗi: " + e, "error");
     }
   }
   ```

---

### Kịch bản 5: Nâng cấp / Tinh chỉnh Selenium TikTok Automation
*Ví dụ: TikTok cập nhật giao diện web làm thay đổi cấu trúc DOM, xuất hiện captcha hoặc cơ chế chặn tự động.*

👉 **TOÀN BỘ LOGIC NẰM TRONG FILE `utils.py` (Không cần đụng đến `app.py` hay `index.html`):**

1. **Khởi tạo trình duyệt chống bot (`init_browser`, Dòng ~598)**:
   * Để ẩn dấu vết tự động hóa: `--disable-blink-features=AutomationControlled`, tùy biến `user-agent` hoặc thêm extension hỗ trợ bypass.
2. **Nhận diện cuộc trò chuyện & Nhóm chat (`extract_chat_details`, Dòng ~696)**:
   * **Chat 1-1:** Trích xuất `@username` cá nhân từ thẻ `<a>` hoặc text trong Chat Header.
   * **Nhóm chat (Group Chat):** Nhóm không có `@handle` cá nhân mà có tiêu đề nhóm và số lượng thành viên (`thành viên`, `members`,...). Được định danh là `[Nhóm] <Tên nhóm>`, cờ `is_group=True`.
   * **Đối chiếu thông minh (`find_matching_target`, Dòng ~790):** Chat 1-1 đối chiếu theo `@username`, Nhóm chat đối chiếu theo Tên nhóm (`nickname`). Đảm bảo không bao giờ bỏ qua nhóm dù dữ liệu cũ hay mới.
3. **Bộ chọn danh sách cuộc trò chuyện (`scan_friends` & `send_messages_to_selected`)**:
   * Danh sách class hiện tại: `PInfoNickname`, `Nickname`, `[data-e2e='conversation-item']`, `[data-e2e='chat-list-item']`.
   * Tự động bỏ qua các mục hệ thống như `"Yêu cầu tin nhắn"` / `"Message requests"`.
4. **Ô nhập tin nhắn chat (`send_messages_to_selected`, Dòng ~910)**:
   * TikTok dùng Draft.js (`contenteditable="true"`, `public-DraftStyleDefault-block`).
   * Quy trình gửi chuẩn: Click ô nhập -> Sleep 0.4s -> `send_keys(msg)` -> `send_keys(Keys.RETURN)` -> Click nút Send dự phòng nếu còn hiển thị.

---

### Kịch bản 6: Thêm hỗ trợ Proxy riêng cho từng tài khoản
*Ví dụ: Mỗi tài khoản chạy qua 1 Proxy HTTP/SOCKS5 riêng để tránh bị quét chung dải IP.*

1. **`utils.py` -> `init_browser(headless=True, proxy=None)`**:
   * Bổ sung `if proxy: chrome_options.add_argument(f'--proxy-server={proxy}')`.
2. **`utils.py` -> `save_accounts`**:
   * Đảm bảo lưu trường `"proxy": acc.get("proxy", "")`.
3. **`app.py` -> `task_send_messages_sequential` & `task_scan_friends`**:
   * Lấy `acc_proxy = acc.get("proxy")` và truyền vào `init_browser(proxy=acc_proxy)`.
4. **`web/index.html`**:
   * Thêm ô nhập Proxy vào modal Tạo/Sửa tài khoản và bảng danh sách.

---

### Kịch bản 7: Chỉnh sửa Giao diện (UI/UX) trong `web/index.html`

1. **Quy tắc thiết kế Shadcn UI Light Mode**:
   * Toàn bộ màu sắc dùng biến CSS `:root` (Dòng ~9-47):
     * Nền chính: `--background: #f8fafc`
     * Thẻ Card: `--card: #ffffff`, viền: `--border: #e2e8f0`
     * Chữ: `--foreground: #0f172a`, chữ mờ: `--muted-foreground: #64748b`
     * Nút chính: `--primary: #0f172a`, viền bo: `--radius: 8px`
2. **Quy tắc Icon SVG**:
   * Tuyệt đối không nhúng font bên ngoài. Sử dụng thẻ `<svg class="icon" viewBox="0 0 24 24">` chuẩn Feather/Lucide.
3. **Quy tắc Modal & Toast**:
   * Mở modal: thêm class `active` vào thẻ overlay (VD: `modalCreateAccount.classList.add("active")`).
   * Hiển thị thông báo nổi: gọi hàm `showToast("Nội dung thông báo", "success" | "error")`.
4. **Cơ chế Auto-save chống spam API**:
   * Dùng hàm `markConfigDirtyAndAutoSave()`: tự động debounce 1.5 giây sau khi người dùng ngừng gõ trước khi gửi POST request.

---

## 🛡️ Checklist Kiểm Tra An Toàn (Bắt Buộc)

Mỗi khi Agent hoàn thành chỉnh sửa một tính năng, hãy tự kiểm tra theo checklist sau:

- [ ] **1. Không phá vỡ cấu trúc đa tài khoản**: Dữ liệu tài khoản A không bao giờ được ghi đè lên tài khoản B.
- [ ] **2. Kiểm tra `STOP_EVENT`**: Mọi vòng lặp duyệt bạn bè hoặc tài khoản đều phải có điều kiện ngắt khi người dùng bấm "Dừng lại khẩn cấp".
- [ ] **3. Luôn đóng Chrome trong `finally`**: Mọi khối `try` mở trình duyệt đều phải có `finally: if browser: browser.quit()`.
- [ ] **4. Giữ trường dữ liệu trong `save_accounts()`**: Nếu có trường mới trong tài khoản, đã khai báo trong hàm `save_accounts()` ở `utils.py` chưa?
- [ ] **5. Không thêm thư viện nặng**: Giữ nguyên tính độc lập nhẹ nhàng của ứng dụng.
- [ ] **6. Không rò rỉ dữ liệu cá nhân**: Đảm bảo các file cookies và tài khoản luôn được loại trừ trong `.gitignore`.
