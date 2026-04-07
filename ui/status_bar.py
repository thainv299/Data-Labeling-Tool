# ============================================================
# status_bar.py — Thanh trạng thái phía dưới cùng
# ============================================================
import tkinter as tk


class StatusBar(tk.Frame):
    """Thanh trạng thái mỏng ở cuối cửa sổ hiển thị gợi ý hoặc thông báo."""

    def __init__(self, parent, text: str = "", on_reset_zoom=None):
        super().__init__(parent, bg="#ecf0f1", pady=2)

        self.on_reset_zoom = on_reset_zoom

        self.lbl = tk.Label(
            self,
            text=text,
            font=("Arial", 9),
            bg="#ecf0f1",
            fg="#7f8c8d",
        )
        self.lbl.pack(side=tk.LEFT, padx=10)

        # Hiển thị Zoom
        self.zoom_frame = tk.Frame(self, bg="#ecf0f1")
        self.zoom_frame.pack(side=tk.RIGHT, padx=10)

        self.lbl_zoom = tk.Label(
            self.zoom_frame, text="Zoom: 100%", font=("Arial", 9, "bold"),
            bg="#ecf0f1", fg="#2c3e50", cursor="hand2"
        )
        self.lbl_zoom.pack(side=tk.LEFT)
        
        if self.on_reset_zoom:
            self.lbl_zoom.bind("<Button-1>", lambda e: self.on_reset_zoom())

    def set_text(self, text: str):
        """Cập nhật nội dung hiển thị thanh trạng thái."""
        self.lbl.config(text=text)

    def set_zoom(self, level: float):
        """Cập nhật hiển thị mức zoom (vd: 1.5 -> 150%)."""
        percent = int(level * 100)
        self.lbl_zoom.config(text=f"Zoom: {percent}%")
