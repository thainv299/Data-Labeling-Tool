# ============================================================
# class_panel.py — Bảng bên trái: chọn lớp nhãn YOLO
# ============================================================
import tkinter as tk

from core.config import CLASSES, COLORS


class ClassPanel(tk.Frame):
    """Bảng chọn nhãn YOLO là danh sách các nút radio buttons."""

    def __init__(self, parent, selected_class: tk.IntVar):
        super().__init__(parent, width=150, padx=10, pady=10)

        self.selected_class = selected_class
        self._build()

    def _build(self):
        # Tiêu đề bảng nhãn
        tk.Label(self, text="Danh sách nhãn", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        # Hiển thị các nhãn từ cấu hình CLASS
        for class_id, class_name in CLASSES.items():
            color = COLORS[class_id % len(COLORS)]
            rb = tk.Radiobutton(
                self,
                text=f"{class_id}: {class_name}",
                variable=self.selected_class,
                value=class_id,
                fg=color,
                font=("Arial", 11, "bold"),
            )
            rb.pack(anchor=tk.W, pady=2)
