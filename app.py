import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText

from utils import (
    load_config,
    save_config,
    load_friends,
    save_friends,
    init_browser,
    login_with_cookies,
    save_cookies,
    scan_friends,
    send_messages_to_selected
)

# ----------------- GIAO DIỆN DARK THEME -----------------
BG_COLOR = "#1e1e2e"
CARD_BG = "#282a36"
TEXT_COLOR = "#f8f8f2"
TEXT_MUTED = "#6272a4"
ACCENT_GREEN = "#50fa7b"
ACCENT_RED = "#ff5555"
ACCENT_BLUE = "#8be9fd"
ACCENT_YELLOW = "#f1fa8c"
ACCENT_PURPLE = "#bd93f9"
INPUT_BG = "#44475a"


class TikTokStreakApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TikTok Streak Manager - Tự Động & Lựa Chọn Bạn Bè")
        self.geometry("960x780")
        self.minsize(850, 650)
        self.configure(bg=BG_COLOR)

        self.running_thread = None
        self.stop_event = threading.Event()
        self.friends_data = []

        self._setup_styles()
        self._build_ui()
        self._load_initial_data()
        self.check_cookie_status()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Cấu hình Treeview
        style.configure(
            "Treeview",
            background=CARD_BG,
            foreground=TEXT_COLOR,
            fieldbackground=CARD_BG,
            rowheight=28,
            font=("Segoe UI", 10)
        )
        style.map("Treeview", background=[("selected", "#44475a")])
        style.configure(
            "Treeview.Heading",
            background="#383a59",
            foreground=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview.Heading", background=[("active", "#44475a")])

    def _build_ui(self):
        # 1. HEADER & COOKIE STATUS
        header_frame = tk.Frame(self, bg=CARD_BG, padx=16, pady=12)
        header_frame.pack(fill="x", padx=12, pady=(10, 6))

        title_lbl = tk.Label(
            header_frame,
            text="🔥 TIKTOK STREAK AUTO MANAGER",
            font=("Segoe UI", 14, "bold"),
            fg=ACCENT_PURPLE,
            bg=CARD_BG
        )
        title_lbl.pack(side="left")

        self.cookie_status_lbl = tk.Label(
            header_frame,
            text="Đang kiểm tra cookies...",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_MUTED,
            bg=CARD_BG
        )
        self.cookie_status_lbl.pack(side="left", padx=20)

        btn_relogin = tk.Button(
            header_frame,
            text="🔑 Đăng nhập & Lưu Cookies Mới",
            font=("Segoe UI", 9, "bold"),
            bg="#6272a4",
            fg="white",
            relief="flat",
            activebackground="#44475a",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.open_cookie_login
        )
        btn_relogin.pack(side="right")

        # 2. CẤU HÌNH GỬI (SETTINGS CARD)
        config_frame = tk.LabelFrame(
            self,
            text=" ⚙️ Cấu hình tin nhắn ",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
            padx=12,
            pady=8
        )
        config_frame.pack(fill="x", padx=12, pady=6)

        # Message Entry
        tk.Label(config_frame, text="Nội dung gửi:", fg=TEXT_COLOR, bg=CARD_BG, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.entry_message = tk.Entry(config_frame, bg=INPUT_BG, fg=TEXT_COLOR, insertbackground="white", font=("Segoe UI", 10), width=24)
        self.entry_message.grid(row=0, column=1, sticky="w", padx=6, pady=4)

        # Delay
        tk.Label(config_frame, text="Giãn cách (giây):", fg=TEXT_COLOR, bg=CARD_BG, font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(16, 4), pady=4)
        self.entry_delay = tk.Spinbox(config_frame, from_=1, to=60, width=5, bg=INPUT_BG, fg=TEXT_COLOR, insertbackground="white", font=("Segoe UI", 10))
        self.entry_delay.grid(row=0, column=3, sticky="w", padx=4, pady=4)

        # Headless
        self.var_headless = tk.BooleanVar(value=True)
        chk_headless = tk.Checkbutton(
            config_frame,
            text="Chạy ẩn Chrome (Headless)",
            variable=self.var_headless,
            fg=TEXT_COLOR,
            bg=CARD_BG,
            selectcolor=INPUT_BG,
            activebackground=CARD_BG,
            activeforeground=TEXT_COLOR,
            font=("Segoe UI", 10)
        )
        chk_headless.grid(row=0, column=4, sticky="w", padx=(16, 8), pady=4)

        # Save config button
        btn_save_config = tk.Button(
            config_frame,
            text="💾 Lưu Cấu Hình",
            bg="#44475a",
            fg="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            command=self.save_user_config
        )
        btn_save_config.grid(row=0, column=5, sticky="e", padx=(12, 4), pady=4)

        # 3. QUẢN LÝ BẠN BÈ (FRIENDS MANAGER CARD)
        friends_frame = tk.LabelFrame(
            self,
            text=" 👥 Danh sách bạn bè & Lựa chọn gửi tin nhắn ",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_YELLOW,
            bg=CARD_BG,
            padx=12,
            pady=8
        )
        friends_frame.pack(fill="both", expand=True, padx=12, pady=6)

        # Thanh công cụ bạn bè
        toolbar = tk.Frame(friends_frame, bg=CARD_BG)
        toolbar.pack(fill="x", pady=(0, 8))

        # Tìm kiếm
        tk.Label(toolbar, text="🔍 Tìm:", fg=TEXT_COLOR, bg=CARD_BG, font=("Segoe UI", 10)).pack(side="left", padx=(0, 4))
        self.entry_search = tk.Entry(toolbar, bg=INPUT_BG, fg=TEXT_COLOR, insertbackground="white", font=("Segoe UI", 9), width=18)
        self.entry_search.pack(side="left", padx=(0, 12))
        self.entry_search.bind("<KeyRelease>", lambda e: self.filter_friends())

        # Nút chức năng bạn bè
        btn_scan = tk.Button(
            toolbar,
            text="🔍 Quét bạn bè từ TikTok",
            bg=ACCENT_BLUE,
            fg="#282a36",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8,
            cursor="hand2",
            command=self.start_scan_friends
        )
        btn_scan.pack(side="left", padx=4)

        btn_add = tk.Button(
            toolbar,
            text="➕ Thêm thủ công",
            bg="#44475a",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            padx=8,
            command=self.add_friend_dialog
        )
        btn_add.pack(side="left", padx=4)

        btn_del = tk.Button(
            toolbar,
            text="🗑️ Xóa đã chọn",
            bg="#ff5555",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            padx=8,
            command=self.delete_selected_friends
        )
        btn_del.pack(side="left", padx=4)

        # Chọn tất cả / Bỏ chọn
        btn_sel_all = tk.Button(
            toolbar,
            text="☑ Chọn tất cả",
            bg="#44475a",
            fg=ACCENT_GREEN,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8,
            command=lambda: self.set_all_selection(True)
        )
        btn_sel_all.pack(side="right", padx=2)

        btn_desel_all = tk.Button(
            toolbar,
            text="☐ Bỏ chọn tất cả",
            bg="#44475a",
            fg="#ffb86c",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8,
            command=lambda: self.set_all_selection(False)
        )
        btn_desel_all.pack(side="right", padx=2)

        # Bảng danh sách bạn bè
        table_frame = tk.Frame(friends_frame, bg=CARD_BG)
        table_frame.pack(fill="both", expand=True)

        columns = ("selected", "username", "nickname", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

        self.tree.heading("selected", text="Gửi tin?")
        self.tree.heading("username", text="TikTok Username (@handle)")
        self.tree.heading("nickname", text="Tên hiển thị (Nickname)")
        self.tree.heading("status", text="Trạng thái gửi gần nhất")

        self.tree.column("selected", width=85, anchor="center")
        self.tree.column("username", width=220, anchor="w")
        self.tree.column("nickname", width=240, anchor="w")
        self.tree.column("status", width=200, anchor="w")

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Click đúp hoặc nhấn phím Space để bật/tắt chọn
        self.tree.bind("<Double-1>", self.on_tree_toggle)
        self.tree.bind("<space>", self.on_tree_toggle)

        # Thống kê dưới bảng
        self.lbl_stats = tk.Label(
            friends_frame,
            text="Đang chọn: 0 / 0 bạn bè",
            fg=ACCENT_GREEN,
            bg=CARD_BG,
            font=("Segoe UI", 9, "bold")
        )
        self.lbl_stats.pack(anchor="w", pady=(6, 0))

        # 4. ĐIỀU KHIỂN & CONSOLE LOGS
        action_frame = tk.Frame(self, bg=CARD_BG, padx=12, pady=10)
        action_frame.pack(fill="x", padx=12, pady=6)

        self.btn_start = tk.Button(
            action_frame,
            text="🚀 BẮT ĐẦU GỬI TIN NHẮN (CHỈ GỬI CHO BẠN BÈ ĐÃ CHỌN)",
            bg=ACCENT_GREEN,
            fg="#1e1e2e",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
            command=self.start_send_messages
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_stop = tk.Button(
            action_frame,
            text="⏹️ DỪNG LẠI",
            bg=ACCENT_RED,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=20,
            pady=6,
            state="disabled",
            cursor="hand2",
            command=self.stop_current_task
        )
        self.btn_stop.pack(side="right")

        # Log console
        log_frame = tk.LabelFrame(
            self,
            text=" 📝 Nhật ký hoạt động ",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            padx=8,
            pady=4
        )
        log_frame.pack(fill="both", expand=False, padx=12, pady=(0, 10))

        self.log_text = ScrolledText(
            log_frame,
            height=7,
            bg="#181825",
            fg=TEXT_COLOR,
            insertbackground="white",
            font=("Consolas", 9),
            relief="flat"
        )
        self.log_text.pack(fill="both", expand=True)

    # ----------------- HÀM TIỆN ÍCH & LOGS -----------------

    def log(self, message):
        """Ghi log vào khung nhật ký có mốc thời gian."""
        timestamp = time.strftime("[%H:%M:%S] ")
        def append():
            self.log_text.insert("end", timestamp + message + "\n")
            self.log_text.see("end")
        self.after(0, append)

    def check_cookie_status(self):
        """Kiểm tra sự tồn tại của file cookies.json."""
        if os.path.exists("cookies.json") and os.path.getsize("cookies.json") > 50:
            self.cookie_status_lbl.config(
                text="🟢 Cookies: Đã sẵn sàng",
                fg=ACCENT_GREEN
            )
        else:
            self.cookie_status_lbl.config(
                text="🔴 Cookies: Chưa có (Hãy bấm Đăng nhập)",
                fg=ACCENT_RED
            )

    def _load_initial_data(self):
        """Nạp cấu hình và danh sách bạn bè lên giao diện."""
        # 1. Config
        cfg = load_config()
        self.entry_message.delete(0, "end")
        self.entry_message.insert(0, cfg.get("message", "🔥"))

        self.entry_delay.delete(0, "end")
        self.entry_delay.insert(0, str(cfg.get("delay_seconds", 3)))

        self.var_headless.set(cfg.get("headless", True))

        # 2. Friends
        self.friends_data = load_friends()
        self.refresh_table()

    def save_user_config(self):
        """Lưu lại cấu hình người dùng vừa chỉnh sửa."""
        try:
            delay = int(self.entry_delay.get())
        except ValueError:
            delay = 3

        cfg = {
            "message": self.entry_message.get().strip() or "🔥",
            "delay_seconds": delay,
            "headless": self.var_headless.get()
        }
        save_config(cfg)
        self.log("[Cấu hình] Đã lưu cấu hình thành công!")
        messagebox.showinfo("Thành công", "Đã lưu cài đặt cấu hình thành công!")

    # ----------------- QUẢN LÝ BẢNG BẠN BÈ -----------------

    def refresh_table(self, filter_kw=""):
        """Vẽ lại bảng dữ liệu bạn bè."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_count = 0
        total_count = len(self.friends_data)
        kw = filter_kw.lower().strip()

        for idx, friend in enumerate(self.friends_data):
            u = friend.get("username", "")
            nick = friend.get("nickname", "")
            enabled = friend.get("enabled", True)
            status = friend.get("status", "Chưa gửi")

            if enabled:
                selected_count += 1

            if kw and (kw not in u.lower() and kw not in nick.lower()):
                continue

            icon = "☑  GỬI" if enabled else "☐  BỎ QUA"
            item_id = self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(icon, f"@{u}", nick, status)
            )

        self.lbl_stats.config(
            text=f"📊 Đang chọn gửi: {selected_count} / {total_count} bạn bè"
        )

    def filter_friends(self):
        kw = self.entry_search.get()
        self.refresh_table(kw)

    def on_tree_toggle(self, event):
        """Bật/tắt trạng thái chọn gửi khi người dùng click."""
        selection = self.tree.selection()
        if not selection:
            return

        for item_id in selection:
            idx = int(item_id)
            if 0 <= idx < len(self.friends_data):
                current = self.friends_data[idx].get("enabled", True)
                self.friends_data[idx]["enabled"] = not current

        save_friends(self.friends_data)
        self.refresh_table(self.entry_search.get())

    def set_all_selection(self, state=True):
        """Chọn tất cả hoặc bỏ chọn tất cả."""
        for friend in self.friends_data:
            friend["enabled"] = state
        save_friends(self.friends_data)
        self.refresh_table(self.entry_search.get())
        self.log(f"Đã {'CHỌN TẤT CẢ' if state else 'BỎ CHỌN TẤT CẢ'} bạn bè.")

    def add_friend_dialog(self):
        """Thêm bạn bè thủ công."""
        username = simpledialog.askstring("Thêm bạn bè", "Nhập TikTok Username (@username):", parent=self)
        if not username:
            return
        username = username.strip().replace("@", "")
        nickname = simpledialog.askstring("Thêm bạn bè", "Nhập Nickname (tên gợi nhớ):", initialvalue=username, parent=self)
        nickname = (nickname or username).strip()

        # Kiểm tra trùng
        for f in self.friends_data:
            if f.get("username", "").lower() == username.lower():
                messagebox.showwarning("Trùng lặp", f"Người dùng @{username} đã có trong danh sách!")
                return

        new_item = {
            "username": username,
            "nickname": nickname,
            "enabled": True,
            "status": "Chưa gửi"
        }
        self.friends_data.append(new_item)
        save_friends(self.friends_data)
        self.refresh_table(self.entry_search.get())
        self.log(f"Đã thêm thủ công bạn bè: {nickname} (@{username})")

    def delete_selected_friends(self):
        """Xóa bạn bè được chọn khỏi danh sách."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Thông báo", "Vui lòng click chọn một hoặc nhiều dòng trong bảng để xóa!")
            return

        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa {len(selection)} người khỏi danh sách?"):
            return

        indices_to_delete = sorted([int(i) for i in selection], reverse=True)
        for idx in indices_to_delete:
            if 0 <= idx < len(self.friends_data):
                deleted = self.friends_data.pop(idx)
                self.log(f"Đã xóa: @{deleted.get('username')}")

        save_friends(self.friends_data)
        self.refresh_table(self.entry_search.get())

    # ----------------- CÁC TÁC VỤ CHẠY THREAD -----------------

    def open_cookie_login(self):
        """Mở cửa sổ Chrome đăng nhập để lấy cookies mới."""
        if self.running_thread and self.running_thread.is_alive():
            messagebox.showwarning("Bận", "Đang có một tiến trình khác đang chạy!")
            return

        def task():
            self.log("[Đăng nhập] Đang khởi động Chrome...")
            browser = None
            try:
                browser, wait = init_browser(headless=False)
                browser.get("https://www.tiktok.com/login")
                self.log("[Đăng nhập] Trình duyệt đã mở. Hãy quét mã QR trên điện thoại hoặc đăng nhập.")
                
                # Hiện popup nhắc nhở
                messagebox.showinfo(
                    "Đăng nhập TikTok",
                    "Trình duyệt Chrome đã mở!\n\n"
                    "1. Hãy đăng nhập tài khoản TikTok của bạn (Quét mã QR là nhanh nhất).\n"
                    "2. Sau khi đã vào được trang cá nhân TikTok, hãy bấm OK tại hộp thoại này để lưu Cookies.",
                    parent=self
                )
                save_cookies(browser, "cookies.json")
                self.log("[Đăng nhập] Lưu cookies thành công!")
                self.after(0, self.check_cookie_status)
            except Exception as e:
                self.log(f"[Đăng nhập] Lỗi: {e}")
            finally:
                if browser:
                    browser.quit()

        threading.Thread(target=task, daemon=True).start()

    def start_scan_friends(self):
        """Bắt đầu quét bạn bè từ TikTok."""
        if not os.path.exists("cookies.json"):
            messagebox.showerror("Thiếu Cookies", "Chưa có cookies! Vui lòng bấm 'Đăng nhập & Lưu Cookies' trước.")
            return

        if self.running_thread and self.running_thread.is_alive():
            messagebox.showwarning("Bận", "Đang có tiến trình khác đang chạy!")
            return

        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.stop_event.clear()

        def task():
            browser = None
            try:
                self.log("--- BẮT ĐẦU QUÉT BẠN BÈ TỪ TIKTOK ---")
                is_headless = self.var_headless.get()
                browser, wait = init_browser(headless=is_headless)
                login_with_cookies(browser, wait, log_cb=self.log)
                
                updated = scan_friends(
                    browser, wait,
                    log_cb=self.log,
                    should_stop=lambda: self.stop_event.is_set()
                )
                self.friends_data = updated
                self.after(0, lambda: self.refresh_table(self.entry_search.get()))
            except Exception as e:
                self.log(f"[Lỗi quét bạn bè]: {e}")
            finally:
                if browser:
                    browser.quit()
                self.after(0, self._on_task_finished)

        self.running_thread = threading.Thread(target=task, daemon=True)
        self.running_thread.start()

    def start_send_messages(self):
        """Bắt đầu gửi tin nhắn duy trì streak cho những bạn bè được chọn."""
        if not os.path.exists("cookies.json"):
            messagebox.showerror("Thiếu Cookies", "Chưa có cookies! Vui lòng bấm 'Đăng nhập & Lưu Cookies' trước.")
            return

        selected_count = sum(1 for f in self.friends_data if f.get("enabled", True))
        if selected_count == 0:
            messagebox.showwarning("Chưa chọn", "Bạn chưa tích chọn người bạn nào để gửi tin nhắn!\nHãy tích chọn [☑ GỬI] trong bảng.")
            return

        if self.running_thread and self.running_thread.is_alive():
            messagebox.showwarning("Bận", "Đang có tiến trình khác đang chạy!")
            return

        # Lưu lại cấu hình mới nhất
        self.save_user_config()

        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.stop_event.clear()

        def task():
            browser = None
            try:
                self.log("--- BẮT ĐẦU GỬI TIN NHẮN GIỮ STREAK ---")
                is_headless = self.var_headless.get()
                browser, wait = init_browser(headless=is_headless)
                login_with_cookies(browser, wait, log_cb=self.log)

                msg = self.entry_message.get().strip() or "🔥"
                try:
                    delay = int(self.entry_delay.get())
                except ValueError:
                    delay = 3

                send_messages_to_selected(
                    browser, wait,
                    message=msg,
                    delay_sec=delay,
                    log_cb=self.log,
                    should_stop=lambda: self.stop_event.is_set()
                )

                # Nạp lại dữ liệu trạng thái mới
                self.friends_data = load_friends()
                self.after(0, lambda: self.refresh_table(self.entry_search.get()))
            except Exception as e:
                self.log(f"[Lỗi gửi tin nhắn]: {e}")
            finally:
                if browser:
                    browser.quit()
                self.after(0, self._on_task_finished)

        self.running_thread = threading.Thread(target=task, daemon=True)
        self.running_thread.start()

    def stop_current_task(self):
        """Yêu cầu dừng tiến trình đang chạy."""
        self.stop_event.set()
        self.log("[Yêu cầu] Đang gửi tín hiệu dừng... Vui lòng chờ vài giây.")

    def _on_task_finished(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")


if __name__ == "__main__":
    app = TikTokStreakApp()
    app.mainloop()
