# ============================================================
# toolbar.py — Thanh công cụ phía trên: chọn chế độ, tải/lưu, tìm kiếm
# ============================================================
import tkinter as tk
from tkinter import ttk


class Toolbar(tk.Frame):
    """Thanh công cụ trên cùng chứa chọn chế độ, bộ tải, tìm kiếm và nút lưu."""

    def __init__(self, parent, mode_var: tk.StringVar, on_load_dataset=None, on_save_labels=None, on_search=None):
        super().__init__(parent, pady=5)

        self.mode_var = mode_var
        self._on_load_dataset = on_load_dataset
        self._on_save_labels = on_save_labels
        self._on_search = on_search

        self._build()

    def _build(self):
        # --- Chế độ (Mode) ---
        mode_frame = tk.LabelFrame(self, text="Chế độ", font=("Arial", 9, "bold"), padx=5, pady=2)
        mode_frame.pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            mode_frame,
            text="Gán nhãn mới (Cùng thư mục)",
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

        # --- Nút tải dữ liệu ---
        tk.Button(
            self,
            text="Chọn thư mục Dataset",
            font=("Arial", 10, "bold"),
            command=self._on_load_dataset,
        ).pack(side=tk.LEFT, padx=10)

        # --- Tìm kiếm ảnh ---
        search_frame = tk.Frame(self)
        search_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(search_frame, text="Tìm ảnh:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.combo_search = ttk.Combobox(search_frame, width=30)
        self.combo_search.pack(side=tk.LEFT, padx=5)
        
        if self._on_search:
            self.combo_search.bind("<<ComboboxSelected>>", self._on_search)
            # Cho phép nhấn Enter để tìm
            self.combo_search.bind("<Return>", self._on_search)

        # --- Thông tin ảnh hiện tại ---
        self.lbl_info = tk.Label(self, text="Chưa tải thư mục nào", font=("Arial", 10, "bold"), fg="#2980b9")
        self.lbl_info.pack(side=tk.LEFT, padx=10)

        # --- Nút Lưu ---
        tk.Button(
            self,
            text="LƯU NHÃN (S)",
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=self._on_save_labels,
        ).pack(side=tk.RIGHT, padx=10)

    def set_info(self, text: str):
        """Cập nhật văn bản hiển thị thông tin ảnh."""
        self.lbl_info.config(text=text)

    def update_search_list(self, names: list[str]):
        """Cập nhật danh sách gợi ý trong ô tìm kiếm."""
        self.combo_search['values'] = names
        if names:
            self.combo_search.set("")

    def set_search_value(self, name: str):
        """Đồng bộ giá trị ô tìm kiếm với ảnh hiện tại."""
        self.combo_search.set(name)

    def get_search_value(self) -> str:
        """Lấy giá trị hiện tại người dùng đang nhập/chọn."""
        return self.combo_search.get()
