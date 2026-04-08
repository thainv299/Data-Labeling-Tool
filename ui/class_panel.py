import tkinter as tk
import random

class ClassPanel(tk.Frame):
    """Bảng chọn nhãn YOLO với khả năng lọc hiển thị và màu ngẫu nhiên."""

    def __init__(self, parent, selected_class: tk.IntVar, on_visibility_change=None, on_select_all_class=None):
        super().__init__(parent, width=200, padx=5, pady=5)
        self.pack_propagate(False) # Giữ kích thước cố định

        self.selected_class = selected_class
        self.on_visibility_change = on_visibility_change
        self.on_select_all_class = on_select_all_class
        
        self.classes = {}
        self.colors = {}
        self.visibility_vars = {} # {cls_id: tk.BooleanVar}
        self.all_visible_var = tk.BooleanVar(value=True)

        self._setup_ui()

    def _setup_ui(self):
        # Tiêu đề
        tk.Label(self, text="DANH SÁCH LỚP", font=("Arial", 11, "bold")).pack(pady=5)

        # Nút bật/tắt tất cả
        self.chk_all = tk.Checkbutton(
            self, text="Hiển thị tất cả", 
            variable=self.all_visible_var,
            command=self._toggle_all,
            font=("Arial", 9, "italic")
        )
        self.chk_all.pack(anchor=tk.W, padx=5)

        tk.Frame(self, height=2, bg="#ddd").pack(fill=tk.X, pady=5)

        # Khu vực scrollable cho danh sách lớp
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def update_classes(self, classes_dict: dict):
        """Cập nhật danh sách lớp từ file YAML và tạo màu ngẫu nhiên."""
        self.classes = classes_dict
        self.colors = {}
        self.visibility_vars = {}
        
        # Xoá UI cũ
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.classes:
            return

        for cls_id, name in self.classes.items():
            # Tạo màu ngẫu nhiên
            color = "#"+''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
            self.colors[cls_id] = color
            
            # Biến hiển thị
            var = tk.BooleanVar(value=True)
            self.visibility_vars[cls_id] = var

            # Frame cho mỗi dòng
            row = tk.Frame(self.scrollable_frame)
            row.pack(fill=tk.X, pady=1)

            # Checkbox hiển thị (Mắt)
            cb = tk.Checkbutton(row, variable=var, command=self._notify_change)
            cb.pack(side=tk.LEFT)

            # Radiobutton chọn lớp
            rb = tk.Radiobutton(
                row, text=f"{cls_id}: {name}",
                variable=self.selected_class,
                value=cls_id,
                fg=color,
                font=("Arial", 10, "bold")
            )
            rb.pack(side=tk.LEFT, padx=2)

            # Nút chọn tất cả
            btn_select_all = tk.Button(
                row, text="[Chọn tất cả]", font=("Arial", 8),
                command=lambda c=cls_id: self._on_select_all_class(c)
            )
            btn_select_all.pack(side=tk.RIGHT, padx=2)

        self.all_visible_var.set(True)

    def _on_select_all_class(self, cls_id):
        if self.on_select_all_class:
            self.on_select_all_class(cls_id)

    def _toggle_all(self):
        state = self.all_visible_var.get()
        for var in self.visibility_vars.values():
            var.set(state)
        self._notify_change()

    def _notify_change(self):
        if self.on_visibility_change:
            self.on_visibility_change()

    def is_visible(self, cls_id):
        return self.visibility_vars.get(cls_id, tk.BooleanVar(value=True)).get()

    def get_color(self, cls_id):
        return self.colors.get(cls_id, "#FF0000")
