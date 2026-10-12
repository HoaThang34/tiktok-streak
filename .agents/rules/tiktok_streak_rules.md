---
description: Quy tắc phát triển và bảo trì mã nguồn dự án TikTok Streak Manager
globs: ["**/*"]
---

# 📜 QUY TẮC MÃ NGUỒN DỰ ÁN TIKTOK STREAK MANAGER

Mọi AI Agent khi làm việc trong kho lưu trữ này **BẮT BUỘC** phải tuân thủ nghiêm ngặt các quy tắc sau:

## 1. Nguyên Tắc Tiết Kiệm Token (Token Efficiency)
* **KHÔNG đọc toàn bộ** `web/index.html` (gần 2000 dòng) hay `utils.py` (hơn 900 dòng) nếu chỉ cần sửa một hàm hoặc một thành phần cụ thể.
* **Tra cứu nhanh:** Trước khi phân tích mã nguồn, đọc file [.agents/README.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/README.md) và [.agents/FEATURE_MODIFICATION_GUIDE.md](file:///c:/Users/hoath/OneDrive/Desktop/tiktok-streak/.agents/FEATURE_MODIFICATION_GUIDE.md) để xác định đúng phạm vi cần chỉnh sửa.

## 2. Nguyên Tắc Kiến Trúc & Công Nghệ
* **Giữ ứng dụng siêu nhẹ (Ultra Lightweight):**
  * Không cài đặt các web framework nặng (Flask, FastAPI, Django, Tornado) trừ khi người dùng yêu cầu rõ ràng. Backend duy trì sử dụng thư viện chuẩn của Python (`http.server`, `threading`, `json`, `csv`).
  * Không đưa vào các framework frontend (React, Vue, Angular) hay bundler (Vite, Webpack). Toàn bộ giao diện nằm trong file duy nhất `web/index.html`.
  * Không dùng CDN Tailwind CSS nặng. Giữ nguyên Vanilla CSS với hệ thống biến màu Shadcn UI Light Mode trong `:root`.
* **Môi trường Windows Portable:**
  * Luôn đảm bảo tương thích với môi trường Python Portable trong thư mục `python_embed/`.
  * File `run.bat` là điểm khởi chạy chính cho người dùng cuối trên Windows.

## 3. Nguyên Tắc An Toàn Đa Tài Khoản & Selenium
* **Cách ly dữ liệu:**
  * Mỗi tài khoản sở hữu thư mục riêng `accounts/<account_id>/` chứa `cookies.json`, `config.json`, `friends.json`, `friends.csv`.
  * Không để dữ liệu giữa các tài khoản bị lẫn lộn hoặc ghi đè chéo.
* **Bắt buộc hỗ trợ nút Dừng khẩn cấp:**
  * Trong mọi vòng lặp (duyệt danh sách bạn bè, duyệt danh sách tài khoản), **BẮT BUỘC** phải kiểm tra `STOP_EVENT.is_set()` hoặc `should_stop()`.
  * Nếu người dùng yêu cầu dừng, tiến trình phải dừng ngay lập tức và ghi log thông báo.
* **Giải phóng tài nguyên trình duyệt:**
  * Mọi khối mã khởi tạo Selenium `browser = init_browser(...)` đều phải nằm trong cấu trúc `try ... finally: if browser: browser.quit()`.
  * Tuyệt đối không để sót tiến trình Chrome chạy ngầm gây tràn bộ nhớ RAM của máy người dùng.

## 4. Nguyên Tắc Bảo Toàn Dữ Liệu Khi Cập Nhật Schema
* Khi bổ sung trường dữ liệu mới vào tài khoản:
  * **BẮT BUỘC** cập nhật danh sách thuộc tính sạch trong hàm `save_accounts()` tại `utils.py`. Nếu quên, dữ liệu trường mới sẽ bị xóa sạch khi ứng dụng lưu `accounts.json`.
  * Cung cấp giá trị mặc định (fallback) cho các tài khoản cũ trong `load_accounts()`.

## 5. Nguyên Tắc Giao Diện (UI/UX)
* Giữ phong cách **Shadcn UI Light Mode**: tối giản, tinh tế, bo góc 8px (`--radius: 8px`), màu nền dịu mắt (`#f8fafc`), chữ tương phản cao (`#0f172a`).
* Sử dụng 100% **Inline SVG Icons** (Feather/Lucide style). Không dùng link CDN font icon ngoài.
* Mọi hành động bất đồng bộ quan trọng đều phải có phản hồi thị giác: Toast thông báo (`showToast()`) hoặc cập nhật nhật ký (`Live Logs`).
