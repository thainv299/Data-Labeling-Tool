# ============================================================
# toolbar.py — Thanh công cụ phía trên: chọn chế độ, tải/lưu, tìm kiếm
# ============================================================
import tkinter as tk
from tkinter import ttk


class Toolbar(tk.Frame):
    """Thanh công cụ trên cùng chứa chọn chế độ, bộ tải, tìm kiếm và nút lưu."""

    def __init__(self, parent, mode_var: tk.StringVar, rename_var: tk.StringVar = None, 
                 on_load_dataset=None, on_save_labels=None, on_search=None, on_rename=None,
                 on_delete=None, on_auto_annotate=None, on_filter_boxes=None, on_clean_labels=None,
                 on_copy_static=None):
        super().__init__(parent, pady=5)

        self.mode_var = mode_var
        self.rename_var = rename_var
        self._on_load_dataset = on_load_dataset
        self._on_save_labels = on_save_labels
        self._on_search = on_search
        self._on_rename = on_rename
        self._on_delete = on_delete
        self._on_auto_annotate = on_auto_annotate
        self._on_filter_boxes = on_filter_boxes
        self._on_clean_labels = on_clean_labels
        self._on_copy_static = on_copy_static

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

        # --- Nút Auto Annotate ---
        tk.Button(
            self,
            text="AI Auto-Annotate ✨",
            font=("Arial", 10, "bold"),
            bg="#8e44ad", fg="white",
            command=self._on_auto_annotate,
        ).pack(side=tk.LEFT, padx=5)

        # --- Nút Lọc Box Trùng ---
        if self._on_filter_boxes:
            tk.Button(
                self,
                text="Lọc Box Trùng",
                font=("Arial", 10, "bold"),
                bg="#e67e22", fg="white",
                command=self._on_filter_boxes,
            ).pack(side=tk.LEFT, padx=5)

        # --- Nút Dọn Label Rác ---
        if self._on_clean_labels:
            tk.Button(
                self,
                text="Dọn Label Rác",
                font=("Arial", 10, "bold"),
                bg="#c0392b", fg="white",
                command=self._on_clean_labels,
            ).pack(side=tk.LEFT, padx=5)

        # --- Nút Sao chép Box tĩnh ---
        if self._on_copy_static:
            tk.Button(
                self,
                text="Sao chép Box tĩnh 📋",
                font=("Arial", 10, "bold"),
                bg="#2980b9", fg="white",
                command=self._on_copy_static,
            ).pack(side=tk.LEFT, padx=5)

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

        # --- Đổi tên (Rename) ---
        rename_frame = tk.Frame(self)
        rename_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(rename_frame, text="Đổi tên:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.entry_rename = tk.Entry(rename_frame, textvariable=self.rename_var, width=20)
        self.entry_rename.pack(side=tk.LEFT, padx=2)
        
        # Nút Đổi tên
        tk.Button(
            rename_frame, 
            text="Ok", 
            command=self._on_rename,
            bg="#f39c12", fg="white",
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT)

        # --- Nút Xoá ---
        tk.Button(
            self,
            text="XOÁ (Del)",
            font=("Arial", 10, "bold"),
            bg="#e74c3c", fg="white",
            command=self._on_delete,
        ).pack(side=tk.LEFT, padx=10)

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
