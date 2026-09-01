import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Dict

from app.config import GAME_MODE, BUFF_POOL, EVENT_POOL
from app.utils import format_money
from app.profile_manager import load_saved_profiles, save_profiles, create_profile, get_leaderboard_data
from app.game_logic import apply_interest, record_round, roll_dice, determine_result, calculate_payout
from app.cau_analyzer import get_cau_signal


class SonBacApp(tk.Tk):
    """Main application window for the Sòng Bạc game."""
    
    def __init__(self):
        super().__init__()
        self.title("Sòng Bạc Giao Diện")
        self.geometry("760x620")
        self.resizable(False, False)

        self.profiles = load_saved_profiles()
        self.current_profile: Optional[Dict] = None
        self.current_round = 1
        self.pending_bet: Optional[int] = None
        self.pending_multiplier: Optional[float] = None
        self.pending_choice: Optional[str] = None
        self.cau_hint: Optional[str] = None
        self.cau_window: Optional[tk.Toplevel] = None
        self.countdown_remaining: int = 0

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        self.menu_frame = ttk.Frame(self.main_frame)
        self.profile_frame = ttk.Frame(self.main_frame)
        self.leaderboard_frame = ttk.Frame(self.main_frame)
        self.rules_frame = ttk.Frame(self.main_frame)

        self.build_main_menu()
        self.build_profile_view()
        self.build_leaderboard_view()
        self.build_rules_view()

        self.show_frame(self.menu_frame)

    def show_frame(self, frame: ttk.Frame) -> None:
        """Show the specified frame and hide all others."""
        for child in self.main_frame.winfo_children():
            child.pack_forget()
        frame.pack(fill="both", expand=True)

    def build_main_menu(self) -> None:
        """Build the main menu screen."""
        title = ttk.Label(self.menu_frame, text="SÒNG BẠC", font=("Segoe UI", 22, "bold"))
        title.pack(pady=18)

        buttons = [
            ("Bắt đầu chơi mới", self.start_new_game),
            ("Tải hồ sơ đã lưu", self.load_profile_dialog),
            ("Xem lịch sử toàn bộ", self.show_all_history),
            ("Bảng xếp hạng", lambda: self.show_frame(self.leaderboard_frame)),
            ("Luật chơi", lambda: self.show_frame(self.rules_frame)),
            ("Thoát", self.quit),
        ]

        for text, command in buttons:
            btn = ttk.Button(self.menu_frame, text=text, command=command)
            btn.pack(pady=8, ipadx=24, ipady=10)

    def build_profile_view(self) -> None:
        """Build the game profile/playing screen."""
        top_bar = ttk.Frame(self.profile_frame)
        top_bar.pack(fill="x", pady=4)

        self.profile_label = ttk.Label(top_bar, text="Người chơi: -", font=("Segoe UI", 14, "bold"))
        self.profile_label.pack(side="left", padx=16)

        self.back_button = ttk.Button(top_bar, text="Về menu", command=self.return_to_menu)
        self.back_button.pack(side="right", padx=8)
        ttk.Button(top_bar, text="Lưu hồ sơ", command=self.save_current_profile).pack(side="right", padx=8)

        status_bar = ttk.Frame(self.profile_frame)
        status_bar.pack(fill="x", pady=4, padx=16)
        self.balance_label = ttk.Label(status_bar, text="Số dư: -", font=("Segoe UI", 12))
        self.balance_label.grid(row=0, column=0, padx=10, pady=4, sticky="w")
        self.debt_label = ttk.Label(status_bar, text="Nợ: -", font=("Segoe UI", 12))
        self.debt_label.grid(row=0, column=1, padx=10, pady=4, sticky="w")

        self.special_info_frame = ttk.Frame(self.profile_frame)
        self.special_info_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.buff_label = ttk.Label(self.special_info_frame, text="Bùa: Chưa có", foreground="darkgreen", font=("Segoe UI", 10, "bold"))
        self.buff_label.pack(anchor="w", pady=2)
        self.event_label = ttk.Label(self.special_info_frame, text="Sự kiện: Không có", foreground="darkorange", font=("Segoe UI", 10, "bold"))
        self.event_label.pack(anchor="w", pady=2)
        self.quest_label = ttk.Label(self.special_info_frame, text="Nhiệm vụ: Chưa có", foreground="royalblue", font=("Segoe UI", 10, "bold"))
        self.quest_label.pack(anchor="w", pady=2)
        self.trend_label = ttk.Label(self.special_info_frame, text="Xu hướng: -", foreground="purple", font=("Segoe UI", 10, "bold"))
        self.trend_label.pack(anchor="w", pady=2)

        betting_frame = ttk.LabelFrame(self.profile_frame, text="Cược và lựa chọn")
        betting_frame.pack(fill="x", padx=16, pady=8)

        ttk.Label(betting_frame, text="Cược tùy chọn:").grid(row=0, column=0, padx=8, pady=10, sticky="w")
        self.bet_entry = ttk.Entry(betting_frame, width=14)
        self.bet_entry.grid(row=0, column=1, padx=8, pady=10)

        self.bet_info_label = ttk.Label(betting_frame, text="", foreground="blue")
        self.bet_info_label.grid(row=1, column=0, columnspan=5, padx=8, pady=4, sticky="w")

        self.all_button = ttk.Button(betting_frame, text="All-in", command=self.select_all_bet)
        self.all_button.grid(row=0, column=2, padx=10, pady=10)
        self.half_button = ttk.Button(betting_frame, text="Nửa", command=self.select_half_bet)
        self.half_button.grid(row=0, column=3, padx=10, pady=10)
        self.custom_button = ttk.Button(betting_frame, text="Cược", command=self.select_custom_bet)
        self.custom_button.grid(row=0, column=4, padx=10, pady=10)
        self.cau_button = ttk.Button(betting_frame, text="Cầu", command=self.open_cau_window)
        self.cau_button.grid(row=1, column=2, padx=10, pady=6)
        self.loan_button = ttk.Button(betting_frame, text="Vay nợ", command=self.borrow_debt)
        self.loan_button.grid(row=1, column=3, columnspan=1, padx=10, pady=6)
        self.repay_button = ttk.Button(betting_frame, text="Trả nợ", command=self.repay_debt)
        self.repay_button.grid(row=1, column=4, columnspan=1, padx=10, pady=6)

        self.cau_label = ttk.Label(betting_frame, text="Cầu: Chưa có", foreground="darkviolet", font=("Segoe UI", 10, "bold"))
        self.cau_label.grid(row=2, column=0, columnspan=5, padx=8, pady=(0, 6), sticky="w")

        result_frame = ttk.LabelFrame(self.profile_frame, text="Chọn Tài / Xỉu")
        result_frame.pack(fill="x", padx=16, pady=8)

        self.tai_button = ttk.Button(result_frame, text="Tài", command=lambda: self.play_round("t"))
        self.tai_button.grid(row=0, column=0, padx=40, pady=12)
        self.xiu_button = ttk.Button(result_frame, text="Xỉu", command=lambda: self.play_round("x"))
        self.xiu_button.grid(row=0, column=1, padx=40, pady=12)

        self.round_label = ttk.Label(self.profile_frame, text="Ván: 0", font=("Segoe UI", 12, "bold"))
        self.round_label.pack(pady=6)

        self.message_label = ttk.Label(self.profile_frame, text="Chọn cược trước khi chơi.", font=("Segoe UI", 11))
        self.message_label.pack(pady=4)

        result_display = ttk.Frame(self.profile_frame)
        result_display.pack(fill="both", expand=True, padx=16, pady=6)

        self.result_text = tk.Text(result_display, height=18, wrap="word", state="disabled", font=("Segoe UI", 10))
        self.result_text.pack(fill="both", expand=True)

        self.update_profile_controls(active=False)

    def build_leaderboard_view(self) -> None:
        """Build the leaderboard screen."""
        title = ttk.Label(self.leaderboard_frame, text="Bảng xếp hạng", font=("Segoe UI", 18, "bold"))
        title.pack(pady=14)
        self.rankings_text = tk.Text(self.leaderboard_frame, height=22, wrap="word", state="disabled", font=("Segoe UI", 10))
        self.rankings_text.pack(fill="both", expand=True, padx=16, pady=4)
        ttk.Button(self.leaderboard_frame, text="Quay về menu", command=self.return_to_menu).pack(pady=8)

    def build_rules_view(self) -> None:
        """Build the rules screen."""
        title = ttk.Label(self.rules_frame, text="Luật chơi", font=("Segoe UI", 18, "bold"))
        title.pack(pady=14)
        text = (
            "• Gieo 3 viên xúc xắc, tổng ≥ 11 là Tài, else Xỉu.\n"
            "• All-in thắng x2.\n"
            "• Cược nửa thắng x1.5.\n"
            "• Nợ tăng 20% mỗi ván nếu còn nợ.\n"
            "• Nợ không được trả tự động khi thắng.\n"
            "• Tính năng Cầu: xem xu hướng gần nhất để đoán Tài/Xỉu.\n"
            "• Nếu cược đúng theo cầu, bạn được thưởng thêm 10%.\n"
        )
        ttk.Label(self.rules_frame, text=text, justify="left", font=("Segoe UI", 11)).pack(padx=20, pady=8)
        ttk.Button(self.rules_frame, text="Quay về menu", command=self.return_to_menu).pack(pady=8)

    def update_profile_controls(self, active: bool) -> None:
        """Update the state of all game control buttons."""
        if active and self.current_profile is not None and self.current_profile["balance"] > 0:
            self.all_button.state(["!disabled"])
            self.custom_button.state(["!disabled"])
            self.tai_button.state(["!disabled"])
            self.xiu_button.state(["!disabled"])
        else:
            self.all_button.state(["disabled"])
            self.custom_button.state(["disabled"])
            self.tai_button.state(["disabled"])
            self.xiu_button.state(["disabled"])

        if self.current_profile is None:
            self.half_button.state(["disabled"])
        elif active and self.current_profile is not None and self.current_profile["balance"] > 0:
            self.half_button.state(["!disabled"])
        else:
            self.half_button.state(["disabled"])

        if self.current_profile is None:
            self.loan_button.state(["disabled"])
        elif active:
            self.loan_button.state(["!disabled"])
        else:
            self.loan_button.state(["disabled"])

        if self.current_profile is None or self.current_profile["debt"] <= 0 or self.current_profile["balance"] <= 0:
            self.repay_button.state(["disabled"])
        elif active:
            self.repay_button.state(["!disabled"])
        else:
            self.repay_button.state(["disabled"])

        if self.current_profile is None:
            self.cau_button.state(["disabled"])
        elif active:
            self.cau_button.state(["!disabled"])
        else:
            self.cau_button.state(["disabled"])

        if self.current_profile is None or self.current_profile["debt"] <= 0:
            self.back_button.state(["!disabled"])
        else:
            self.back_button.state(["disabled"])

    def start_new_game(self) -> None:
        """Show dialog to start a new game."""
        modal = tk.Toplevel(self)
        modal.title("Bắt đầu chơi mới")
        modal.geometry("360x140")
        modal.resizable(False, False)

        ttk.Label(modal, text="Tên người chơi:", font=("Segoe UI", 11)).pack(pady=(18, 8))
        name_entry = ttk.Entry(modal, width=32)
        name_entry.pack()

        def create_and_start() -> None:
            name = name_entry.get().strip() or "Người chơi"
            profile = create_profile(name)
            self.current_profile = profile
            self.profiles[name] = profile
            self.current_round = 1
            self.pending_bet = None
            self.pending_multiplier = None
            self.show_profile_screen()
            modal.destroy()

        ttk.Button(modal, text="Bắt đầu", command=create_and_start).pack(pady=18, ipadx=16)

    def load_profile_dialog(self) -> None:
        """Show dialog to load a saved profile."""
        if not self.profiles:
            messagebox.showinfo("Thông báo", "Chưa có hồ sơ nào được lưu.")
            return
        modal = tk.Toplevel(self)
        modal.title("Tải hồ sơ")
        modal.geometry("360x260")
        modal.resizable(False, False)

        ttk.Label(modal, text="Chọn hồ sơ:", font=("Segoe UI", 11)).pack(pady=(18, 10))
        listbox = tk.Listbox(modal, height=8, width=30)
        for name in sorted(self.profiles.keys()):
            listbox.insert("end", name)
        listbox.pack(padx=12)

        def load_selected() -> None:
            if not listbox.curselection():
                messagebox.showwarning("Lỗi", "Vui lòng chọn hồ sơ.")
                return
            name = listbox.get(listbox.curselection())
            self.current_profile = self.profiles[name]
            self.current_round = len(self.current_profile["history"]) + 1
            self.pending_bet = None
            self.pending_multiplier = None
            self.show_profile_screen()
            modal.destroy()

        ttk.Button(modal, text="Tải hồ sơ", command=load_selected).pack(pady=14, ipadx=16)

    def show_all_history(self) -> None:
        """Show history of all profiles."""
        if not self.profiles:
            messagebox.showinfo("Thông báo", "Chưa có hồ sơ nào được lưu.")
            return
        summary = []
        for name, profile in self.profiles.items():
            stats = profile["stats"]
            summary.append(
                f"Tên: {name}\n"
                f"Số dư: {format_money(profile['balance'])} | Nợ: {format_money(profile['debt'])}\n"
                f"Ván: {stats['rounds']} | Thắng: {stats['wins']} | Thua: {stats['losses']}\n"
                "――――――――――――――――――――――――――――――\n"
            )
        messagebox.showinfo("Lịch sử toàn bộ", "\n".join(summary))

    def show_profile_screen(self) -> None:
        """Show the main game screen for the current profile."""
        if self.current_profile is None:
            return
        self.update_status_labels()
        self.show_frame(self.profile_frame)
        self.update_profile_controls(active=True)
        self.bet_info_label.config(text=self.get_bet_info())
        self.show_message("Chọn cược trước khi chơi.")
        self.clear_result_text()

    def update_status_labels(self) -> None:
        """Update all status labels to reflect current profile state."""
        if self.current_profile is None:
            return
        self.profile_label.config(text=f"Người chơi: {self.current_profile['name']}")
        self.balance_label.config(text=f"Số dư: {format_money(self.current_profile['balance'])}")
        self.debt_label.config(text=f"Nợ: {format_money(self.current_profile['debt'])}")
        self.round_label.config(text=f"Ván: {self.current_round}")

        buff_text = self.current_profile.get("buff")
        if buff_text:
            self.buff_label.config(text=f"Bùa: {buff_text['name']} ({buff_text['desc']})")
        else:
            self.buff_label.config(text="Bùa: Chưa có")

        event_text = self.current_profile.get("event")
        if event_text:
            self.event_label.config(text=f"Sự kiện: {event_text['name']} ({event_text['desc']})")
        else:
            self.event_label.config(text="Sự kiện: Không có")

        quest_entries = []
        for quest in self.current_profile.get("quests", []):
            status = "✓" if quest["completed"] else "•"
            quest_entries.append(f"{status} {quest['title']} ({min(quest['progress'], quest['target'])}/{quest['target']})")
        self.quest_label.config(text="Nhiệm vụ: " + (" | ".join(quest_entries) if quest_entries else "Chưa có"))

        recent = self.current_profile.get("recent_results", [])
        trend_text = "Xu hướng: " + " ".join(recent[-5:]) if recent else "Xu hướng: -"
        self.trend_label.config(text=trend_text)

    def get_bet_info(self) -> str:
        """Get bet information text for display."""
        if self.current_profile is None:
            return ""
        max_bet = max(1, int(self.current_profile["balance"] * GAME_MODE["max_bet_ratio"]))
        parts = [f"Max cược: {format_money(max_bet)}"]
        parts.append(f"Nửa: x{GAME_MODE['multiplier_half']}")
        parts.append(f"All-in: x{GAME_MODE['multiplier_all']}")
        return " | ".join(parts)

    def apply_cau_hint(self) -> None:
        """Apply the current cầu (betting trend) hint."""
        if self.current_profile is None:
            return
        signal = get_cau_signal(self.current_profile)
        if signal is None:
            self.cau_hint = None
            self.cau_label.config(text="Cầu: Chưa có đủ dữ liệu")
            self.show_message("Cầu chưa có đủ dữ liệu. Chơi thêm vài ván để xem xu hướng.")
            return
        self.cau_hint = signal["value"]
        self.cau_label.config(text=f"Cầu: {signal['label']} ({signal['detail']})")
        self.show_message(f"Cầu đang nóng: {signal['label']}. Hãy theo cầu nếu muốn cược theo xu hướng.")

    def refresh_cau_window(self) -> None:
        """Refresh the cầu window display."""
        if self.cau_window is None or not self.cau_window.winfo_exists():
            return

        signal = get_cau_signal(self.current_profile) if self.current_profile else None
        recent = [entry["result"] for entry in self.current_profile.get("history", [])[-8:]] if self.current_profile else []
        if not recent:
            recent = ["t", "x", "t", "x"]

        self.cau_canvas.delete("all")
        bar_w = 30
        gap = 8
        start_x = 25
        for idx, value in enumerate(recent):
            x0 = start_x + idx * (bar_w + gap)
            y0 = 90 if value == "t" else 40
            rect_color = "#1aa85f" if value == "t" else "#d9485f"
            self.cau_canvas.create_rectangle(x0, y0, x0 + bar_w, 100, fill=rect_color, outline="")
            self.cau_canvas.create_text(x0 + bar_w / 2, y0 - 10, text="T" if value == "t" else "X", fill="black", font=("Segoe UI", 9, "bold"))

        cue_text = signal["label"] if signal else "Chưa có"
        cue_detail = signal["detail"] if signal else "Cần ít nhất 3 ván để nhận dạng cầu"
        cue_color = "#0f7c5f" if cue_text == "TÀI" else "#b3261e"
        self.cau_status_label.config(text=f"Cầu hiện tại: {cue_text}", foreground=cue_color)
        self.cau_detail_label.config(text=cue_detail)

    def open_cau_window(self) -> None:
        """Open the cầu (betting trend) visualization window."""
        if self.current_profile is None:
            return

        if self.cau_window is not None and self.cau_window.winfo_exists():
            self.refresh_cau_window()
            self.cau_window.focus_set()
            return

        window = tk.Toplevel(self)
        window.title("Cầu giang hồ")
        window.geometry("430x300")
        window.resizable(False, False)
        self.cau_window = window

        ttk.Label(window, text="Biểu đồ cầu gần đây", font=("Segoe UI", 14, "bold")).pack(pady=(14, 6))

        self.cau_canvas = tk.Canvas(window, width=360, height=120, bg="#fffaf0", highlightthickness=0)
        self.cau_canvas.pack(pady=6)

        self.cau_status_label = ttk.Label(window, text="Cầu hiện tại: ...", font=("Segoe UI", 12, "bold"))
        self.cau_status_label.pack(pady=6)
        self.cau_detail_label = ttk.Label(window, text="", wraplength=360, justify="center", font=("Segoe UI", 10))
        self.cau_detail_label.pack(pady=(0, 8))

        ttk.Button(window, text="Áp dụng cầu", command=self.apply_cau_hint).pack(ipadx=18)
        self.refresh_cau_window()

    def select_all_bet(self) -> None:
        """Select all-in betting option."""
        if self.current_profile is None:
            return
        self.pending_bet = self.current_profile["balance"]
        self.pending_multiplier = GAME_MODE["multiplier_all"]
        self.show_message(f"Chọn All-in: {format_money(self.pending_bet)}")

    def select_half_bet(self) -> None:
        """Select half betting option."""
        if self.current_profile is None:
            return
        if not GAME_MODE["allow_half"]:
            messagebox.showinfo("Không hợp lệ", "Chế độ này không cho phép cược nửa.")
            return
        self.pending_bet = max(1, self.current_profile["balance"] // 2)
        self.pending_multiplier = GAME_MODE["multiplier_half"]
        self.show_message(f"Chọn cược nửa: {format_money(self.pending_bet)}")

    def select_custom_bet(self) -> None:
        """Select custom betting amount."""
        if self.current_profile is None:
            return
        bet_text = self.bet_entry.get().strip()
        try:
            bet_value = int(bet_text)
        except ValueError:
            messagebox.showwarning("Lỗi", "Nhập số tiền cược hợp lệ.")
            return
        balance = self.current_profile["balance"]
        max_bet = max(1, int(balance * GAME_MODE["max_bet_ratio"]))
        if bet_value <= 0:
            messagebox.showwarning("Lỗi", "Cược phải lớn hơn 0.")
            return
        if bet_value > balance:
            messagebox.showwarning("Lỗi", "Bạn không có đủ tiền để cược số đó.")
            return
        if bet_value > max_bet:
            messagebox.showwarning("Lỗi", f"Chế độ này chỉ được cược tối đa {format_money(max_bet)}.")
            return
        self.pending_bet = bet_value
        self.pending_multiplier = (
            GAME_MODE["multiplier_all"] if bet_value == balance else GAME_MODE["multiplier_half"]
        )
        if self.pending_multiplier == 0:
            messagebox.showwarning("Lỗi", "Chế độ này không cho phép cược nửa.")
            return
        self.show_message(f"Chọn cược: {format_money(self.pending_bet)}")

    def borrow_debt(self) -> None:
        """Borrow 50K in debt to continue playing."""
        if self.current_profile is None:
            return
        if not GAME_MODE["allow_debt"]:
            messagebox.showinfo("Không được vay nợ", "Chế độ này không cho vay nợ mới.")
            return
        self.current_profile["debt"] += 50
        self.current_profile["balance"] += 50
        self.update_status_labels()
        self.update_profile_controls(active=True)
        self.bet_info_label.config(text=self.get_bet_info())
        self.show_message("Đã vay 50K VND để tiếp tục chơi.")
        self.save_current_profile()

    def repay_debt(self) -> None:
        """Repay some or all of the current debt."""
        if self.current_profile is None:
            return
        debt = self.current_profile["debt"]
        if debt <= 0:
            messagebox.showinfo("Không có nợ", "Bạn hiện không còn nợ.")
            return
        balance = self.current_profile["balance"]
        if balance <= 0:
            messagebox.showwarning("Không đủ tiền", "Bạn không có đủ tiền để trả nợ.")
            return
        payment = min(balance, debt)
        self.current_profile["balance"] -= payment
        self.current_profile["debt"] -= payment
        self.update_status_labels()
        self.update_profile_controls(active=True)
        self.bet_info_label.config(text=self.get_bet_info())
        if self.current_profile["debt"] <= 0:
            self.show_message("Đã trả hết nợ.")
        else:
            self.show_message(f"Đã trả {format_money(payment)}. Nợ còn lại {format_money(self.current_profile['debt'])}.")
        self.save_current_profile()

    def play_round(self, choice: str) -> None:
        """Start a new game round with the given choice (t or x)."""
        if self.current_profile is None:
            return
        if self.pending_bet is None or self.pending_multiplier is None:
            messagebox.showinfo("Chưa chọn cược", "Vui lòng chọn mức cược trước khi chọn Tài/Xỉu.")
            return

        profile = self.current_profile
        if profile["balance"] <= 0:
            if profile["debt"] > 0 and not GAME_MODE["allow_debt"]:
                self.show_message("Bạn hết tiền và chế độ không cho vay nợ thêm.")
                self.update_profile_controls(active=True)
                return
            if GAME_MODE["allow_debt"]:
                self.show_message("Bạn hết tiền. Nhấn Vay nợ để tiếp tục chơi.")
            else:
                self.show_message("Bạn hết tiền và không thể vay thêm. Trò chơi tạm dừng.")
            self.update_profile_controls(active=True)
            return

        if not profile.get("buff") and self.current_round % 3 == 0:
            profile["buff"] = random.choice(BUFF_POOL)
        if not profile.get("event") and self.current_round % 5 == 0:
            profile["event"] = random.choice(EVENT_POOL)
        self.update_status_labels()

        signal = get_cau_signal(profile)
        if signal is not None:
            self.cau_hint = signal["value"]
            self.cau_label.config(text=f"Cầu: {signal['label']} ({signal['detail']})")
        else:
            self.cau_hint = None
            self.cau_label.config(text="Cầu: Chưa có đủ dữ liệu")

        self.pending_choice = choice
        self.countdown_remaining = 5
        self.update_profile_controls(active=False)
        self.start_countdown()

    def start_countdown(self) -> None:
        """Start the countdown before resolving the round."""
        if self.pending_choice is None:
            return
        if self.countdown_remaining <= 0:
            self.resolve_round()
            return
        self.show_message(f"Đang chờ kết quả... vui lòng đợi {self.countdown_remaining} giây.")
        self.countdown_remaining -= 1
        self.after(1000, self.start_countdown)

    def resolve_round(self) -> None:
        """Resolve the current round and update profile."""
        if self.current_profile is None or self.pending_choice is None:
            return

        choice = self.pending_choice
        self.pending_choice = None
        profile = self.current_profile

        if profile["debt"] > 0:
            apply_interest(profile)

        x1, x2, x3 = roll_dice()
        total = x1 + x2 + x3
        result = determine_result(total)

        force_loss = profile["balance"] > 750 and random.random() < 0.5
        payout, bonus_message = calculate_payout(
            choice, result, self.pending_bet, self.pending_multiplier,
            self.cau_hint, profile.get("buff"), profile.get("event"), force_loss
        )

        if payout > 0:
            self.show_message(f"THẮNG! Bạn nhận được {format_money(payout)}{bonus_message}.")
        else:
            self.show_message(f"THUA! Mất {format_money(-payout)}{bonus_message}.")

        profile["balance"] += payout
        if profile["balance"] < 0:
            profile["balance"] = 0

        event = profile.get("event")
        if event and event["kind"] == "lucky_pick" and choice == result:
            profile["balance"] += event["value"]
            self.show_message(f"THẮNG! Bạn nhận được {format_money(event['value'])} thêm từ sự kiện Đêm lạ.")

        round_info = {
            "round": self.current_round,
            "bet": self.pending_bet,
            "choice": choice,
            "dice": f"{x1},{x2},{x3}",
            "total": total,
            "result": result,
            "payout": payout,
            "balance": profile["balance"],
            "debt": profile["debt"],
        }

        profile["recent_results"].append("TÀI" if result == "t" else "XỈU")
        profile["recent_results"] = profile["recent_results"][-5:]

        record_round(profile, round_info)
        for quest in profile.get("quests", []):
            if quest["completed"]:
                continue
            if quest["type"] == "win" and round_info["payout"] > 0:
                quest["progress"] += 1
            elif quest["type"] == "rounds":
                quest["progress"] += 1
            elif quest["type"] == "balance" and profile["balance"] >= quest["target"]:
                quest["progress"] = quest["target"]
            if quest["progress"] >= quest["target"]:
                quest["completed"] = True
                profile["balance"] += quest["reward"]
                self.show_message(f"Nhiệm vụ hoàn thành: {quest['title']} +{format_money(quest['reward'])}.")

        self.current_round += 1
        self.pending_bet = None
        self.pending_multiplier = None
        self.cau_hint = None
        profile["buff"] = None
        profile["event"] = None

        self.append_result_text(
            f"Ván {round_info['round']}: cược {format_money(round_info['bet'])} | "
            f"{choice.upper()} -> {x1},{x2},{x3} ({total}) => {'TÀI' if result == 't' else 'XỈU'} | "
            f"{format_money(round_info['payout'])} | Dư: {format_money(profile['balance'])} | Nợ: {format_money(profile['debt'])}\n"
        )

        self.update_status_labels()
        self.update_profile_controls(active=True)
        self.bet_entry.delete(0, "end")
        self.bet_info_label.config(text=self.get_bet_info())
        if self.cau_window is not None and self.cau_window.winfo_exists():
            self.refresh_cau_window()
        self.save_current_profile()

    def append_result_text(self, message: str) -> None:
        """Append text to the result display."""
        self.result_text.config(state="normal")
        self.result_text.insert("end", message)
        self.result_text.see("end")
        self.result_text.config(state="disabled")

    def clear_result_text(self) -> None:
        """Clear the result display."""
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.config(state="disabled")

    def show_message(self, message: str) -> None:
        """Display a message to the player."""
        self.message_label.config(text=message)

    def save_current_profile(self) -> None:
        """Save the current profile to file."""
        if self.current_profile is None:
            return
        self.profiles[self.current_profile["name"]] = self.current_profile
        save_profiles(self.profiles)

    def return_to_menu(self) -> None:
        """Return to main menu."""
        if self.current_profile is not None and self.current_profile["debt"] > 0:
            messagebox.showwarning("Không thể về menu", "Bạn còn nợ. Vui lòng trả hết nợ trước khi về menu.")
            return
        self.save_current_profile()
        self.update_leaderboard_text()
        self.show_frame(self.menu_frame)

    def update_leaderboard_text(self) -> None:
        """Update the leaderboard display."""
        self.rankings_text.config(state="normal")
        self.rankings_text.delete("1.0", "end")
        profiles = load_saved_profiles()
        leaderboard_text = get_leaderboard_data(profiles)
        self.rankings_text.insert("end", leaderboard_text)
        self.rankings_text.config(state="disabled")
