# ============================================================
# status_bar.py — Thanh trạng thái phía dưới cùng
# ============================================================
import tkinter as tk


class StatusBar(tk.Frame):
    """Thanh trạng thái mỏng ở cuối cửa sổ hiển thị gợi ý hoặc thông báo."""

    def __init__(self, parent, text: str = ""):
        super().__init__(parent, bg="#ecf0f1", pady=2)

        self.lbl = tk.Label(
            self,
            text=text,
            font=("Arial", 9),
            bg="#ecf0f1",
            fg="#7f8c8d",
        )
        self.lbl.pack()

    def set_text(self, text: str):
        """Cập nhật nội dung hiển thị thanh trạng thái."""
        self.lbl.config(text=text)
