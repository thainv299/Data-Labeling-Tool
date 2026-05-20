import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from core.config import CLASSES as DEFAULT_CLASSES
from core.label_manager import LabelManager
import yaml

class LabelSelectionDialog(tk.Toplevel):
    """
    Hộp thoại yêu cầu người dùng cấu hình nhãn khi tải một thư mục không có file cấu hình.
    Cũng dùng để chỉnh sửa nhãn khi đã load dataset (edit mode).
    """
    def __init__(self, parent, target_folder, existing_classes=None):
        super().__init__(parent)
        self.geometry("500x550")
        self.transient(parent)
        self.grab_set()

        self.target_folder = target_folder
        self.custom_classes = {}  # {id: "name"}
        self.current_custom_id = 0
        self.result_classes = None # Sẽ chứa dictionary các lớp nếu người dùng xác nhận
        self.edit_mode = existing_classes is not None

        if self.edit_mode:
            self.title("Chỉnh sửa danh sách nhãn")
            self.label_mode = tk.StringVar(value="custom")
            # Nạp nhãn hiện tại vào custom_classes
            self.custom_classes = dict(existing_classes)
            if self.custom_classes:
                self.current_custom_id = max(self.custom_classes.keys()) + 1
        else:
            self.title("Cấu hình nhãn cho Dataset")
            self.label_mode = tk.StringVar(value="default")

        self._build_ui()
        
        # Chặn đóng cửa sổ bằng dấu X (bắt buộc chọn hoặc Hủy)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self):
        main_frame = tk.Frame(self, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        if self.edit_mode:
            tk.Label(main_frame, text="Chỉnh sửa danh sách nhãn hiện tại.\nThêm, xoá hoặc nhập nhãn từ file JSON:", justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 15))
        else:
            tk.Label(main_frame, text="Không tìm thấy cấu hình nhãn (dataset.yaml) trong thư mục này.\nVui lòng chọn cấu hình nhãn để tiếp tục:", justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 15))

        # --- Chọn chế độ nhãn ---
        mode_frame = tk.LabelFrame(main_frame, text="Cấu hình Nhãn (Classes)", padx=10, pady=10)
        mode_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        if not self.edit_mode:
            tk.Radiobutton(mode_frame, text="Dùng 7 nhãn mặc định (person, car, ...)", 
                           variable=self.label_mode, value="default", command=self._toggle_custom_ui).pack(anchor=tk.W)
            tk.Radiobutton(mode_frame, text="Tự khai báo nhãn", 
                           variable=self.label_mode, value="custom", command=self._toggle_custom_ui).pack(anchor=tk.W)

        # Vùng tuỳ chỉnh nhãn
        self.custom_frame = tk.Frame(mode_frame)
        self.custom_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Nhập nhãn mới
        input_f = tk.Frame(self.custom_frame)
        input_f.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(input_f, text="Tên nhãn:").pack(side=tk.LEFT)
        self.entry_new_label = tk.Entry(input_f)
        self.entry_new_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_new_label.bind("<Return>", lambda e: self._add_label())
        tk.Button(input_f, text="Thêm", command=self._add_label).pack(side=tk.LEFT)

        # Danh sách nhãn
        list_f = tk.Frame(self.custom_frame)
        list_f.pack(fill=tk.BOTH, expand=True)
        
        self.tree_labels = ttk.Treeview(list_f, columns=("ID", "Name"), show="headings", height=8)
        self.tree_labels.heading("ID", text="ID")
        self.tree_labels.heading("Name", text="Tên Nhãn")
        self.tree_labels.column("ID", width=50, anchor=tk.CENTER)
        self.tree_labels.column("Name", width=300)
        self.tree_labels.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_f, orient="vertical", command=self.tree_labels.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_labels.configure(yscrollcommand=scrollbar.set)

        # Nút quản lý nhãn custom
        btn_f = tk.Frame(self.custom_frame)
        btn_f.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(btn_f, text="Xoá chọn", command=self._remove_selected_label).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(btn_f, text="Xoá tất cả", command=self._clear_labels).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(btn_f, text="Nhập từ JSON", command=self._import_json).pack(side=tk.RIGHT)
        tk.Button(btn_f, text="Xuất ra JSON", command=self._export_json).pack(side=tk.RIGHT, padx=(0, 5))

        # Nạp sẵn nhãn nếu ở chế độ edit
        if self.edit_mode and self.custom_classes:
            for k, v in sorted(self.custom_classes.items()):
                self.tree_labels.insert("", tk.END, values=(k, v))

        self._toggle_custom_ui() # Cập nhật trạng thái UI ban đầu

        # --- Nút hành động ---
        action_f = tk.Frame(main_frame)
        action_f.pack(fill=tk.X, pady=(10, 0))
        tk.Button(action_f, text="Hủy bỏ", command=self._on_cancel, width=10).pack(side=tk.RIGHT, padx=(10, 0))
        tk.Button(action_f, text="Xác nhận", command=self._on_confirm, width=15, 
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side=tk.RIGHT)

    def _toggle_custom_ui(self):
        if self.label_mode.get() == "default":
            for child in self.custom_frame.winfo_children():
                self._set_state(child, tk.DISABLED)
        else:
            for child in self.custom_frame.winfo_children():
                self._set_state(child, tk.NORMAL)

    def _set_state(self, widget, state):
        try:
            widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_state(child, state)

    def _add_label(self):
        name = self.entry_new_label.get().strip()
        if not name: return
        
        if name in self.custom_classes.values():
            messagebox.showwarning("Trùng lặp", f"Nhãn '{name}' đã tồn tại!")
            return
            
        self.custom_classes[self.current_custom_id] = name
        self.tree_labels.insert("", tk.END, values=(self.current_custom_id, name))
        self.current_custom_id += 1
        self.entry_new_label.delete(0, tk.END)

    def _remove_selected_label(self):
        selected = self.tree_labels.selection()
        if not selected: return
        for item in selected:
            vals = self.tree_labels.item(item, "values")
            cls_id = int(vals[0])
            if cls_id in self.custom_classes:
                del self.custom_classes[cls_id]
            self.tree_labels.delete(item)
        self._reindex_labels()

    def _clear_labels(self):
        self.custom_classes.clear()
        self.current_custom_id = 0
        for item in self.tree_labels.get_children():
            self.tree_labels.delete(item)

    def _reindex_labels(self):
        old_classes = [name for id, name in sorted(self.custom_classes.items())]
        self._clear_labels()
        for name in old_classes:
            self.custom_classes[self.current_custom_id] = name
            self.tree_labels.insert("", tk.END, values=(self.current_custom_id, name))
            self.current_custom_id += 1

    def _import_json(self):
        filepath = filedialog.askopenfilename(title="Chọn file JSON", filetypes=[("JSON files", "*.json")])
        if not filepath: return
        
        loaded = LabelManager.load_labels_from_json(filepath)
        if not loaded:
            messagebox.showerror("Lỗi", "Không thể tải nhãn từ file này hoặc file rỗng.")
            return
            
        self._clear_labels()
        for k, v in loaded.items():
            self.custom_classes[k] = v
        
        if self.custom_classes:
            self.current_custom_id = max(self.custom_classes.keys()) + 1
        
        for k, v in sorted(self.custom_classes.items()):
            self.tree_labels.insert("", tk.END, values=(k, v))
            
        messagebox.showinfo("Thành công", f"Đã nhập {len(loaded)} nhãn.")

    def _export_json(self):
        if not self.custom_classes:
            messagebox.showwarning("Trống", "Không có nhãn nào để xuất.")
            return
            
        filepath = filedialog.asksaveasfilename(title="Lưu file JSON", defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not filepath: return
        
        if LabelManager.save_labels_to_json(filepath, self.custom_classes):
            messagebox.showinfo("Thành công", f"Đã lưu danh sách nhãn vào {os.path.basename(filepath)}")

    def _on_confirm(self):
        classes_dict = DEFAULT_CLASSES
        if self.label_mode.get() == "custom":
            if not self.custom_classes:
                messagebox.showwarning("Lỗi", "Bạn chọn 'Tự khai báo nhãn' nhưng danh sách nhãn đang trống.")
                return
            classes_dict = self.custom_classes

        # Lưu lại vào dataset.yaml
        yaml_path = os.path.join(self.target_folder, "dataset.yaml")
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml_data = {'names': classes_dict}
                yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        except Exception as e:
            print(f"Lỗi khi lưu dataset.yaml: {e}")
            # Vẫn cho phép tiếp tục dù lỗi lưu file

        self.result_classes = classes_dict
        self.destroy()

    def _on_cancel(self):
        self.result_classes = None
        self.destroy()
