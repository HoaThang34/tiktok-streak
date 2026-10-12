# 🤖 TIKTOK STREAK MANAGER - AGENT KNOWLEDGE HUB & NAVIGATION GUIDE

> **Mục tiêu của tài liệu này:** Cung cấp bản đồ điều hướng dự án đầy đủ, chính xác và có cấu trúc cho AI Coding Agents (Antigravity, Claude, Copilot, Cursor,...).  
> **Nguyên tắc tiết kiệm token:** Đọc trực tiếp các bảng ánh xạ và phạm vi chỉnh sửa trong thư mục `/.agents/` bên dưới, **không cần đọc toàn bộ mã nguồn** `app.py` (~30KB), `utils.py` (~34KB) hay `web/index.html` (~80KB).

---

## 🗺️ Bản Đồ Tài Liệu Trong `/.agents/`

| File Tài Liệu | Nội Dung Chính | Khi Nào Cần Đọc? |
| :--- | :--- | :--- |
| [PROJECT_OVERVIEW.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/PROJECT_OVERVIEW.md) | Tổng quan nghiệp vụ, Tech Stack, triết lý thiết kế & sơ đồ luồng dữ liệu | Khi bắt đầu dự án mới, cần nắm kiến trúc toàn cục |
| [ARCHITECTURE_AND_STORAGE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/ARCHITECTURE_AND_STORAGE.md) | Cấu trúc thư mục, chi tiết module, mô hình dữ liệu (JSON/CSV) & đa luồng | Khi làm việc với lưu trữ dữ liệu, cookies, background threads |
| [API_REFERENCE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/API_REFERENCE.md) | Danh mục toàn bộ 17 REST API Endpoints (Request/Response payload) | Khi thêm/sửa API kết nối giữa Frontend và Backend |
| [FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md) | **Phạm vi tác động & Checklist chỉnh sửa** theo từng nhóm tính năng | **BẮT BUỘC ĐỌC khi cập nhật/phát triển tính năng mới** |
| [rules/tiktok_streak_rules.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/rules/tiktok_streak_rules.md) | Các quy chuẩn cốt lõi (Coding convention, UI Shadcn, an toàn Selenium) | Tự động áp dụng làm luật kiểm soát mã nguồn |

---

## ⚡ Bảng Tra Cứu Tác Vụ Nhanh (Fast Lookup - Tiết Kiệm Token)

Khi người dùng yêu cầu một công việc cụ thể, Agent chỉ cần mở đúng các file được liệt kê dưới đây:

| Nhu Cầu Của Người Dùng | File Cần Sửa (Backend) | File Cần Sửa (Frontend) | Hướng Dẫn Chi Tiết |
| :--- | :--- | :--- | :--- |
| **Thêm trường dữ liệu tài khoản** (VD: proxy, ghi chú, avatar, phân nhóm) | `utils.py` (`load_accounts`, `save_accounts`, `create_account`)<br>`app.py` (API `/api/accounts/...`) | `web/index.html` (`renderAccountsTable`, modal thêm/sửa) | Xem [Kịch bản 1 trong FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md#kịch-bản-1-thêm-trường-dữ-liệu-hoặc-quản-lý-tài-khoản) |
| **Thay đổi cú pháp tin nhắn streak** (VD: thêm biến template `{random}`, `{tag}`) | `utils.py` (`render_message_template`) | `web/index.html` (thêm chip gợi ý, sửa `updateMessagePreview`) | Xem [Kịch bản 2 trong FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md#kịch-bản-2-thay-đổi-hoặc-bổ-sung-cơ-chế-gửi-tin-nhắn-streak) |
| **Thêm tùy chọn cấu hình nick** (VD: random delay, gửi ảnh, tự thả tim) | `utils.py` (`load_config`, `save_config`)<br>`app.py` (`POST /api/config`) | `web/index.html` (UI Card Cài Đặt, `loadActiveAccountDetails`, `saveActiveAccountConfig`) | Xem [Kịch bản 3 trong FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md#kịch-bản-3-thêm-tùy-chọn-cấu-hình-config-mới) |
| **Bổ sung tác vụ nền tự động** (VD: Auto Warm-up nick, kiểm tra cookie sống/chết) | `app.py` (tạo `task_xxx`, wrap bằng `run_background_task`, tạo API POST trigger) | `web/index.html` (thêm button, gắn API trigger, hiển thị loading) | Xem [Kịch bản 4 trong FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md#kịch-bản-4-bổ-sung-tác-vụ-nền-mới-background-task) |
| **Fix selector Selenium do TikTok đổi giao diện** (Khung chat, danh sách bạn bè, avatar) | `utils.py` (`scan_friends`, `send_messages_to_selected`, `extract_current_chat_username`) | Không cần sửa Frontend | Xem [Kịch bản 5 trong FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md#kịch-bản-5-nâng-cấp--tinh-chỉnh-selenium-tiktok-automation) |
| **Cải tiến giao diện Web Dashboard** (Đổi layout, thêm modal, tối ưu UI mobile) | Không cần sửa Backend (trừ khi cần thêm endpoint) | `web/index.html` (CSS `:root`, component HTML, hàm render JS) | Xem [Kịch bản 6 trong FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md#kịch-bản-6-chỉnh-sửa-giao-diện-uiux-trong-webindexhtml) |

---

## 🔑 Nguyên Tắc Sống Còn Cho Agent

1. **Không dùng framework nặng**: Không thêm Flask, FastAPI, Django, React, Vue, Tailwind CSS hay thư viện ngoài nếu không có yêu cầu bắt buộc từ người dùng. Dự án giữ kiến trúc siêu nhẹ (Standard Python Library + Selenium + Vanilla HTML/CSS/JS).
2. **Tuân thủ quy chuẩn Multi-Account**: Dữ liệu cookies, cấu hình, bạn bè của mỗi tài khoản nằm độc lập trong `accounts/<acc_id>/`. Không ghi đè hay đọc nhầm dữ liệu giữa các tài khoản.
3. **An toàn vòng lặp Selenium**: Luôn kiểm tra `STOP_EVENT.is_set()` hoặc `should_stop()` trong mọi vòng lặp duyệt bạn bè/tài khoản. Luôn đặt `browser.quit()` trong khối `finally`.
4. **Bảo toàn phong cách UI**: Giao diện giữ nguyên chuẩn **Shadcn UI Light Mode**, sử dụng 100% SVG icons (không dùng FontAwesome hay font icon ngoài), font hệ thống Inter/Segoe UI, màu sắc tailwind/slate dịu mắt.
