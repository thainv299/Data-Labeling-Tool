# ============================================================
# toolbar.py — Top toolbar: mode selector, load/save, info label
# ============================================================
import tkinter as tk


class Toolbar(tk.Frame):
    """Top toolbar containing mode selector, dataset loader, info label, and save button."""

    def __init__(self, parent, mode_var: tk.StringVar, on_load_dataset=None, on_save_labels=None):
        super().__init__(parent, pady=5)

        self.mode_var = mode_var
        self._on_load_dataset = on_load_dataset
        self._on_save_labels = on_save_labels

        self._build()

    def _build(self):
        # --- Mode Selection ---
        mode_frame = tk.LabelFrame(self, text="Chế độ", font=("Arial", 9, "bold"), padx=5, pady=2)
        mode_frame.pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            mode_frame,
            text="Gán nhãn mới (Same Folder)",
            variable=self.mode_var,
            value="same_folder",
            font=("Arial", 9),
        ).pack(side=tk.LEFT, padx=2)

        tk.Radiobutton(
            mode_frame,
            text="Review YOLO Dataset (images/ & labels/)",
            variable=self.mode_var,
            value="yolo_dataset",
            font=("Arial", 9),
        ).pack(side=tk.LEFT, padx=2)

        # --- Load Dataset Button ---
        tk.Button(
            self,
            text="Chọn thư mục Dataset",
            font=("Arial", 10, "bold"),
            command=self._on_load_dataset,
        ).pack(side=tk.LEFT, padx=10)

        # --- Info Label ---
        self.lbl_info = tk.Label(self, text="Chưa tải thư mục nào", font=("Arial", 10))
        self.lbl_info.pack(side=tk.LEFT, padx=10)

        # --- Save Button ---
        tk.Button(
            self,
            text="LƯU NHÃN",
            font=("Arial", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self._on_save_labels,
        ).pack(side=tk.RIGHT, padx=10)

    def set_info(self, text: str):
        """Update the info label text."""
        self.lbl_info.config(text=text)
