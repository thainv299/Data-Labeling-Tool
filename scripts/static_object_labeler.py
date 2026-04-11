import tkinter as tk
from tkinter import messagebox, ttk

class StaticObjectLabelerApp:
    def __init__(self, parent, box_data, current_idx, image_paths, data_manager, mode, on_complete=None):
        self.root = tk.Toplevel(parent)
        self.root.title("Sao chép Bounding Box tĩnh")
        self.root.geometry("400x320")
        self.root.resizable(False, False)
        self.root.grab_set() # Giữ focus

        self.box_data = box_data # (cls_id, xc, yc, w, h)
        self.current_idx = current_idx
        self.image_paths = image_paths
        self.data_manager = data_manager
        self.mode = mode
        self.on_complete = on_complete

        self._setup_ui()

    def _setup_ui(self):
        # Thông tin nhãn đang chọn
        cls_id, xc, yc, w, h = self.box_data
        info_frame = tk.LabelFrame(self.root, text="Nhãn đang chọn", padx=10, pady=10)
        info_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(info_frame, text=f"Class ID: {cls_id}", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=f"Vị trí: ({xc:.3f}, {yc:.3f}) | Size: {w:.3f}x{h:.3f}", font=("Arial", 9)).pack(anchor="w")

        # Chọn dải ảnh
        range_frame = tk.LabelFrame(self.root, text="Phạm vi sao chép (Index)", padx=10, pady=10)
        range_frame.pack(fill="x", padx=15, pady=10)

        row1 = tk.Frame(range_frame)
        row1.pack(fill="x", pady=5)
        tk.Label(row1, text="Từ ảnh số:").pack(side="left")
        self.start_idx_var = tk.IntVar(value=self.current_idx + 1)
        tk.Entry(row1, textvariable=self.start_idx_var, width=10).pack(side="left", padx=10)
        tk.Label(row1, text=f"(Min: 1)").pack(side="left")

        row2 = tk.Frame(range_frame)
        row2.pack(fill="x", pady=5)
        tk.Label(row2, text="Đến ảnh số:").pack(side="left")
        self.end_idx_var = tk.IntVar(value=len(self.image_paths))
        tk.Entry(row2, textvariable=self.end_idx_var, width=10).pack(side="left", padx=10)
        tk.Label(row2, text=f"(Max: {len(self.image_paths)})").pack(side="left")

        # Nút thực hiện
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="THỰC HIỆN SAO CHÉP", 
            font=("Arial", 10, "bold"), bg="#27ae60", fg="white",
            command=self.run_batch_process,
            padx=20, pady=5
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame, text="Huỷ", 
            command=self.root.destroy,
            padx=15, pady=5
        ).pack(side="left")

    def run_batch_process(self):
        try:
            start = self.start_idx_var.get() - 1
            end = self.end_idx_var.get() - 1
        except Exception:
            messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ!")
            return

        # Kiểm tra dải hợp lệ
        if start < 0 or end >= len(self.image_paths) or start > end:
            messagebox.showerror("Lỗi", f"Phạm vi không hợp lệ! (1 - {len(self.image_paths)})")
            return

        confirm_msg = f"Hệ thống sẽ thêm nhãn này vào {end - start + 1} ảnh.\nHành động này tự động lưu xuống file .txt.\nBạn có chắc chắn?"
        if not messagebox.askyesno("Xác nhận", confirm_msg):
            return

        count_success = 0
        for i in range(start, end + 1):
            img_path = self.image_paths[i]
            txt_path = self.data_manager.get_label_path(img_path, self.mode)
            
            # Tải nhãn hiện có
            labels = self.data_manager.load_labels(txt_path)
            
            # Kiểm tra xem box đã tồn tại chưa (Point-in-box check)
            # Nếu tâm của box mới nằm trong một box đã có cùng loại -> coi như đã có.
            exists = False
            c_cls, c_xc, c_yc, c_w, c_h = self.box_data
            for l_cls, l_xc, l_yc, l_w, l_h in labels:
                if l_cls == c_cls:
                    # Tính biên của box hiện tại trong file
                    lx1, ly1 = l_xc - l_w / 2, l_yc - l_h / 2
                    lx2, ly2 = l_xc + l_w / 2, l_yc + l_h / 2
                    # Kiểm tra tâm box sắp copy (c_xc, c_yc) có lọt vào dải này không
                    if lx1 <= c_xc <= lx2 and ly1 <= c_yc <= ly2:
                        exists = True
                        break
            
            if not exists:
                labels.append(self.box_data)
                self.data_manager.save_labels(txt_path, labels)
                count_success += 1

        messagebox.showinfo("Thành công", f"Đã sao chép và lưu thành công nhãn vào {count_success} ảnh!")
        if self.on_complete:
            self.on_complete()
        self.root.destroy()
