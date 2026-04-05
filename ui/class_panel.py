# ============================================================
# class_panel.py — Left panel: label class selector
# ============================================================
import tkinter as tk

from core.config import CLASSES, COLORS


class ClassPanel(tk.Frame):
    """Left sidebar showing the list of YOLO classes as radio buttons."""

    def __init__(self, parent, selected_class: tk.IntVar):
        super().__init__(parent, width=150, padx=10, pady=10)

        self.selected_class = selected_class
        self._build()

    def _build(self):
        tk.Label(self, text="Danh sách nhãn", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

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
