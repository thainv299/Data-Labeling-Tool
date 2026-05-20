import tkinter as tk
from tkinter import messagebox, simpledialog
import random

class ClassPanel(tk.Frame):
    """Bảng chọn nhãn YOLO với khả năng lọc hiển thị và màu ngẫu nhiên."""

    def __init__(self, parent, selected_class: tk.IntVar, on_visibility_change=None, on_select_all_class=None, on_edit_labels=None, on_classes_modified=None, on_class_deleted=None, on_class_id_changed=None):
        super().__init__(parent, width=200, padx=5, pady=5)
        self.pack_propagate(False) # Giữ kích thước cố định

        self.selected_class = selected_class
        self.on_visibility_change = on_visibility_change
        self.on_select_all_class = on_select_all_class
        self.on_edit_labels = on_edit_labels
        self.on_classes_modified = on_classes_modified
        self.on_class_deleted = on_class_deleted
        self.on_class_id_changed = on_class_id_changed
        
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

        # Khung thêm nhãn nhanh dưới cùng (pack trước để không bị canvas chiếm chỗ)
        quick_add_frame = tk.Frame(self, pady=5, bd=1, relief=tk.GROOVE)
        quick_add_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(5, 5))
        
        tk.Label(quick_add_frame, text="THÊM NHÃN MỚI", font=("Arial", 9, "bold"), fg="#2c3e50").pack(anchor=tk.W, padx=5, pady=(2, 2))
        
        self.entry_add = tk.Entry(quick_add_frame, font=("Arial", 10))
        self.entry_add.pack(fill=tk.X, padx=5, pady=(2, 5))
        self.entry_add.bind("<Return>", lambda e: self._add_class_inline())
        
        self.btn_add = tk.Button(
            quick_add_frame, text="➕ Thêm Nhãn", font=("Arial", 9, "bold"),
            bg="#2ecc71", fg="white", activebackground="#27ae60",
            command=self._add_class_inline
        )
        self.btn_add.pack(fill=tk.X, padx=5, pady=(0, 2))

        # Nút sửa nhãn ở trên khung thêm nhanh
        self.btn_edit_labels = tk.Button(
            self, text="⚙️ Quản lý nhãn nâng cao", font=("Arial", 9, "bold"),
            bg="#3498db", fg="white",
            command=self._on_edit_labels_clicked
        )
        self.btn_edit_labels.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(5, 0))

        # Cuối cùng pack canvas chiếm toàn bộ diện tích còn lại ở giữa
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
                row, text="🔍", font=("Arial", 8),
                command=lambda c=cls_id: self._on_select_all_class(c)
            )
            btn_select_all.pack(side=tk.RIGHT, padx=2)

            # Bind chuột phải vào toàn bộ dòng để hiển thị menu ngữ cảnh
            for widget in (row, cb, rb, btn_select_all):
                widget.bind("<Button-3>", lambda e, c=cls_id: self._show_context_menu(e, c))

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

    def _on_edit_labels_clicked(self):
        if self.on_edit_labels:
            self.on_edit_labels()

    def _show_context_menu(self, event, cls_id):
        """Hiển thị menu chuột phải cho một lớp nhãn."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏️ Đổi tên nhãn...", command=lambda: self._rename_class_inline(cls_id))
        menu.add_command(label="🔢 Đổi ID (Index)...", command=lambda: self._change_class_id_inline(cls_id))
        menu.add_command(label="❌ Xoá nhãn này", command=lambda: self._delete_class_inline(cls_id))
        menu.add_separator()
        menu.add_command(label="🔍 Chọn tất cả đối tượng nhãn này", command=lambda: self._on_select_all_class(cls_id))
        menu.post(event.x_root, event.y_root)

    def _add_class_inline(self):
        """Thêm nhãn nhanh từ ô nhập phía dưới."""
        name = self.entry_add.get().strip()
        if not name:
            return
        
        # Kiểm tra trùng lặp
        if name in self.classes.values():
            messagebox.showwarning("Trùng lặp", f"Nhãn '{name}' đã tồn tại!")
            return
        
        # Tạo ID mới
        new_id = max(self.classes.keys()) + 1 if self.classes else 0
        
        new_classes = dict(self.classes)
        new_classes[new_id] = name
        
        self.entry_add.delete(0, tk.END)
        
        if self.on_classes_modified:
            self.on_classes_modified(new_classes)

    def _rename_class_inline(self, cls_id):
        """Đổi tên nhãn nhanh."""
        old_name = self.classes.get(cls_id, "")
        new_name = simpledialog.askstring("Đổi tên nhãn", f"Nhập tên mới cho nhãn '{old_name}':", initialvalue=old_name)
        if new_name is None:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        
        if new_name == old_name:
            return
            
        if new_name in self.classes.values():
            messagebox.showwarning("Trùng lặp", f"Nhãn '{new_name}' đã tồn tại!")
            return
            
        new_classes = dict(self.classes)
        new_classes[cls_id] = new_name
        
        if self.on_classes_modified:
            self.on_classes_modified(new_classes)

    def _delete_class_inline(self, cls_id):
        """Xoá nhãn."""
        name = self.classes.get(cls_id, "")
        confirm = messagebox.askyesno(
            "Xoá nhãn", 
            f"Bạn có chắc chắn muốn xoá nhãn '{name}'?\n\n"
            "⚠️ CHÚ Ý QUAN TRỌNG:\n"
            "- Hành động này sẽ XOÁ TẤT CẢ các box gán nhãn thuộc lớp này trong TOÀN BỘ các file nhãn của dataset.\n"
            "- Các lớp nhãn có chỉ số (ID) lớn hơn lớp bị xoá sẽ tự động giảm ID đi 1 đơn vị để tránh bị đứt gãy chỉ số.\n"
            "- Hành động này không thể hoàn tác!"
        )
        if not confirm:
            return
            
        if self.on_class_deleted:
            self.on_class_deleted(cls_id)

    def _change_class_id_inline(self, cls_id):
        """Đổi ID (Index) của nhãn."""
        old_name = self.classes.get(cls_id, "")
        new_id = simpledialog.askinteger(
            "Đổi chỉ số nhãn (Index ID)", 
            f"Nhập ID mới (số nguyên >= 0) cho nhãn '{old_name}' (ID cũ: {cls_id}):",
            minvalue=0
        )
        if new_id is None:
            return
            
        if new_id == cls_id:
            return
            
        # Kiểm tra xem ID mới đã có chưa
        if new_id in self.classes:
            merge_confirm = messagebox.askyesno(
                "Trùng chỉ số nhãn",
                f"Chỉ số nhãn ID {new_id} đang thuộc về nhãn '{self.classes[new_id]}'.\n"
                f"Bạn có muốn GỘP nhãn '{old_name}' vào nhãn '{self.classes[new_id]}' không?\n"
                "Tất cả các box có ID cũ sẽ được đổi thành ID mới."
            )
            if not merge_confirm:
                return

        if self.on_class_id_changed:
            self.on_class_id_changed(cls_id, new_id)
