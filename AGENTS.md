# 🤖 AGENTS.MD - TIKTOK STREAK MANAGER

> **Dành cho AI Agents (Antigravity, Claude, Copilot, Cursor,...):**  
> Dự án này đã được phân tích toàn diện và hệ thống hóa tài liệu chi tiết trong thư mục [/.agents/](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/).  
> **Để tiết kiệm token và tránh phân tích lại toàn bộ mã nguồn lớn**, bạn hãy đọc trực tiếp các tài liệu chuyên biệt dưới đây:

---

## ⚡ Bản Đồ Tài Liệu & Chỉ Mục Tra Cứu

| Tài Liệu Chuyên Biệt | Nội Dung & Mục Đích |
| :--- | :--- |
| 📍 **[Mục lục & Tra cứu nhanh](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/README.md)** | Bảng tra cứu tác vụ: "Muốn làm X thì sửa file nào ở đâu" |
| 📍 **[Hướng dẫn sửa đổi tính năng](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md)** | **BẮT BUỘC ĐỌC:** 7 kịch bản chỉnh sửa cụ thể (Account, Config, Message, Task, Selenium, UI) kèm checklist an toàn |
| 📍 **[Tổng quan kiến trúc](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/PROJECT_OVERVIEW.md)** | Tech stack, nghiệp vụ multi-account, sơ đồ luồng dữ liệu & cơ chế chạy tuần tự |
| 📍 **[Kiến trúc & Lưu trữ dữ liệu](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/ARCHITECTURE_AND_STORAGE.md)** | Chi tiết schemas (`accounts.json`, `cookies.json`, `config.json`, `friends.json`), đa luồng & Logs |
| 📍 **[Danh mục 17 REST APIs](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/API_REFERENCE.md)** | Chi tiết đầy đủ Request/Response của tất cả endpoints trong `app.py` |
| 📍 **[Quy tắc mã nguồn Workspace](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/rules/tiktok_streak_rules.md)** | Các nguyên tắc không được phá vỡ khi code (Clean accounts, `STOP_EVENT`, `browser.quit`) |

---

## 🚀 Tóm Tắt Nhanh Tech Stack
* **Backend:** Python Standard Library (`http.server.ThreadingHTTPServer`, `threading`, `json`, `csv`) - Cực nhẹ, không dùng Flask/FastAPI.
* **Tự động hóa:** `selenium>=4.20.0` (Điều khiển Google Chrome).
* **Frontend:** Vanilla HTML/CSS/JS duy nhất trong `web/index.html` (Shadcn UI Light Mode, 100% SVG icons).
* **Môi trường chạy:** Hỗ trợ Python Portable (`python_embed/`) chạy trực tiếp qua `run.bat` trên Windows.
* **Cách ly dữ liệu:** Mỗi tài khoản có thư mục riêng trong `accounts/<account_id>/`.
