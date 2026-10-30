# TikTok Streak Manager (Multi-Account Web Automation Dashboard)

> 🇻🇳 **Tiếng Việt** • 🇬🇧 [English](#-tiktok-streak-manager-english)

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

---

## Giấy Phép (License)

Dự án này được phát hành theo giấy phép **MIT License** — xem chi tiết tại file [`LICENSE`](./LICENSE).

Bạn hoàn toàn có thể sử dụng, sao chép, chỉnh sửa, phân phối dự án (kể cả mục đích thương mại) miễn là giữ nguyên thông báo bản quyền và giấy phép.

---
---
---

<a id="-tiktok-streak-manager-english"></a>

# 🇬🇧 TikTok Streak Manager (English)

A local web application that runs on your personal computer to safely and conveniently automate sending **Streak** messages on TikTok, with support for **managing and running multiple accounts (multiple cookies)**.

The interface follows the **Shadcn UI Light Mode** style: minimal, elegant, 100% SVG icons, instant feedback, and no unnecessary animations.

---

## Highlights

* **Multi-Account & Multi-Cookie Support**:
  * Add, rename, delete, and manage unlimited TikTok accounts.
  * Each account has its own session (cookies), message config, delay interval, and friend list.
* **Safe Sequential Execution Per Account**:
  * Optionally tick the accounts you want to run in each batch.
  * Sequential mechanism: **Launch account -> load cookies -> send streak messages -> fully close the Chrome window -> short pause -> move to the next account**.
  * Frees up memory and completely avoids login-session conflicts between accounts.
* **Detailed Per-Account Status**:
  * Records and clearly displays the **last login time** (`last_login`).
  * Session status (`Ready (N cookies)` / `No cookies yet`).
  * Status and last-run time (`Done (X/Y friends)`, `Running...`, `Error...`).
* **Flexible Login via Cookies / QR Code**:
  * Log in by scanning a QR code directly from the mobile TikTok app for each separate account. No password entry, no blocks or captchas.
* **Per-Account Dynamic Time Message Templates**:
  * Supported variables: `{time}`, `{date}`, `{datetime}`, `{hour}`, `{minute}`, `{second}`, `{nickname}`, `{username}`.
  * Live Preview panel with a real-time clock.
* **High Safety Mechanism**:
  * Customize the pause (seconds) between send rounds to avoid spam.
  * Per-account choice of headless mode or visible browser.
  * Emergency stop button at any time (automatically closes the browser immediately).

---

## Project Structure

```text
tiktok-streak/
├── app.py             # Local HTTP server serving the Web Dashboard & multi-account API
├── utils.py           # Core Selenium module & multi-account, cookies, friends manager
├── web/
│   └── index.html     # Web Dashboard UI (Shadcn Light Mode, SVG icons)
├── accounts.json      # Account list, last login times, statuses
├── accounts/          # Independent data folder per account (secured in .gitignore)
│   ├── acc_1/
│   │   ├── cookies.json       # Account 1's own session
│   │   ├── config.json        # Account 1's message config
│   │   ├── friends.json       # Account 1's friend list
│   │   └── friends.csv        # Friend list as a CSV spreadsheet
│   └── acc_2/...
├── requirements.txt   # Required Python libraries
├── run.bat            # Quick-launch shortcut on Windows
├── .env               # Environment variables
├── .gitignore         # Excludes sensitive and junk files
└── README.md          # Documentation
```

---

## System Requirements

1. **Operating System**: Windows 10/11 (or macOS / Linux).
2. **Python**: Version 3.8 or newer.
3. **Browser**: Google Chrome installed on your machine.

---

## Installation & Launch

### 1. Install dependencies
Open a terminal in the project folder and run:
```powershell
pip install -r requirements.txt
```

### 2. Launch the app
* **Option 1 (Fastest on Windows):** Double-click the `run.bat` file.
* **Option 2 (Via command line):**
  ```powershell
  python app.py
  ```

The system will start a local server and automatically open the admin dashboard in Google Chrome at:
```
http://localhost:5000
```

---

## Multi-Account Usage Guide

### Step 1: Manage & log in / load cookies for accounts
1. In the **"Manage TikTok Account List"** section:
   * Click the **"+ Add new account"** button:
     * You can create an empty account (log in later), OR paste cookies right away, OR select an existing cookie `.json` file on your machine.
   * To load/update cookies for any account, click the **"Cookie / Login"** button on that account row. There are 3 flexible options:
     * **Option 1 - Scan QR code**: Open Chrome, scan the QR code from the mobile TikTok app; cookies are saved automatically after scanning.
     * **Option 2 - Paste cookies**: Paste a JSON cookie array (exported from Cookie-Editor / EditThisCookie) or a Header string `sessionid=...; sid_tt=...;` and click Save.
     * **Option 3 - Load a .json file**: Choose a `cookies.json` file on your computer to load into the account instantly.
   * After successfully loading cookies, the account switches to **"Ready"** status and records the **last login time**.

### Step 2: Set up message template & friend list per account
1. Click the **"Manage"** button on the account you want to configure.
2. In the **"Personal Settings"** area:
   * Customize the streak message template (using tags like `{time}`, `{nickname}`, etc.).
   * Set the safe pause interval and headless mode.
   * Click **"Save this account's settings"**.
3. In the **"Inbox Friend List"** area:
   * Click **"Scan friends from TikTok"** to load this account's inbox contacts.
   * Tick the friends you want to send streaks to; untick those you don't.

### Step 3: Run multiple accounts sequentially
1. In the account table, tick the **"Run"** checkbox of the accounts you want in this batch (or click **"Select all to run"**).
2. Click the big button: **"▶ Start running selected accounts sequentially"**.
3. The automatic process proceeds:
   * **Account 1**: Open Chrome -> Load cookies -> Send streak messages to selected friends -> Update status & send time -> **Fully close the Chrome window**.
   * Short 3-second pause.
   * **Account 2**: Open Chrome -> Load cookies -> Send streak messages -> **Fully close the Chrome window** -> ...
4. Monitor every detail in the **Live Logs** panel.
5. You can click **"Emergency stop"** at any time to immediately halt the process and close the browser.

---

## Security
* All cookie data for every account is stored safely in the `accounts/` folder and `cookies.json` file.
* This folder is automatically excluded in `.gitignore` to avoid data-leak risks when pushing to Git.

---

## License

This project is released under the **MIT License** — see the [`LICENSE`](./LICENSE) file for details.

You are free to use, copy, modify, and distribute the project (including for commercial purposes) as long as the copyright notice and license are preserved.
