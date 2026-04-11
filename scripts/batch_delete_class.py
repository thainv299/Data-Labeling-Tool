import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pathlib
import threading

class BatchDeleteClassApp:
    def __init__(self, root, initial_folder=None, initial_class=0):
        self.root = root
        self.root.title("Công cụ Xoá Class hàng loạt (YOLO)")
        self.root.geometry("500x450")
        
        self.folder_path = tk.StringVar(value=initial_folder or "")
        self.class_id = tk.IntVar(value=initial_class)
        self.range_mode = tk.StringVar(value="all") # "all" or "range"
        self.start_idx = tk.IntVar(value=1)
        self.end_idx = tk.IntVar(value=100)
        
        self.setup_ui()

    def setup_ui(self):
        # 1. Folder Selection
        frame_folder = tk.LabelFrame(self.root, text="1. Chọn thư mục Dataset (Gốc hoặc /images)", padx=10, pady=10)
        frame_folder.pack(fill="x", padx=10, pady=5)
        
        tk.Entry(frame_folder, textvariable=self.folder_path, width=45).pack(side="left", padx=5)
        tk.Button(frame_folder, text="Duyệt", command=self.browse_folder).pack(side="left")

        # 2. Class Selection
        frame_class = tk.LabelFrame(self.root, text="2. Nhập ID Class cần xoá", padx=10, pady=10)
        frame_class.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_class, text="Class ID:").pack(side="left")
        tk.Entry(frame_class, textvariable=self.class_id, width=10).pack(side="left", padx=5)
        tk.Label(frame_class, text="(Ví dụ: 0 cho person)", fg="gray", font=("Arial", 8)).pack(side="left")

        # 3. Range Selection
        frame_range = tk.LabelFrame(self.root, text="3. Phạm vi áp dụng", padx=10, pady=10)
        frame_range.pack(fill="x", padx=10, pady=5)
        
        tk.Radiobutton(frame_range, text="Toàn bộ thư mục (Quét đệ quy)", variable=self.range_mode, value="all").grid(row=0, column=0, sticky="w", columnspan=4)
        
        tk.Radiobutton(frame_range, text="Chỉ trong dải ảnh (Số thứ tự):", variable=self.range_mode, value="range").grid(row=1, column=0, sticky="w", columnspan=4, pady=(5,0))
        
        tk.Label(frame_range, text="Từ ảnh số:").grid(row=2, column=0, padx=5, pady=5)
        tk.Entry(frame_range, textvariable=self.start_idx, width=8).grid(row=2, column=1, padx=5)
        
        tk.Label(frame_range, text="đến ảnh số:").grid(row=2, column=2, padx=5)
        tk.Entry(frame_range, textvariable=self.end_idx, width=8).grid(row=2, column=3, padx=5)

        # 4. Status and Start
        self.btn_start = tk.Button(self.root, text="BẮT ĐẦU XOÁ HÀNG LOẠT", font=("Arial", 12, "bold"), bg="#e74c3c", fg="white", command=self.start_process)
        self.btn_start.pack(pady=15)
        
        self.lbl_progress = tk.Label(self.root, text="Sẵn sàng...", fg="blue")
        self.lbl_progress.pack()
        
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.pack(pady=5)

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)

    def start_process(self):
        if not self.folder_path.get() or not os.path.exists(self.folder_path.get()):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục dataset hợp lệ!")
            return

        msg = (f"CẢNH BÁO: Bạn đang chuẩn bị xoá TẤT CẢ các đối tượng có Class ID {self.class_id.get()}.\n\n"
               "Hành động này sẽ thay đổi các file .txt gốc.\n"
               "Bạn nên backup dữ liệu trước khi thực hiện.\n\n"
               "Bạn có chắc chắn muốn tiếp tục?")
        
        if not messagebox.askyesno("Xác nhận xoá hàng loạt", msg):
            return

        self.btn_start.config(state="disabled")
        threading.Thread(target=self.process_deletion, daemon=True).start()

    def process_deletion(self):
        try:
            folder = self.folder_path.get()
            target_class = str(self.class_id.get())
            mode = self.range_mode.get()
            
            self.update_status("Đang quét ảnh...")
            # Quét ảnh để có danh sách/thứ tự ảnh
            all_images = []
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                all_images.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
            
            all_images = sorted(all_images)
            
            if not all_images:
                self.update_status("Không tìm thấy ảnh nào!")
                self.root.after(0, lambda: messagebox.showinfo("Kết quả", "Không tìm thấy file ảnh nào trong thư mục!"))
                return

            # Xác định dải ảnh cần xử lý
            if mode == "all":
                target_images = all_images
            else:
                s = max(0, self.start_idx.get() - 1)
                e = min(len(all_images), self.end_idx.get())
                target_images = all_images[s:e]

            if not target_images:
                self.update_status("Dải ảnh đã chọn không có dữ liệu!")
                return

            total = len(target_images)
            self.root.after(0, lambda: self.progress.config(maximum=total))
            
            modified_count = 0
            box_removed_total = 0
            
            for i, img_path in enumerate(target_images):
                # Tìm file nhãn tương ứng
                # Giả lập logic get_label_path đơn giản tại đây
                txt_path = self.get_label_path(img_path)
                
                if os.path.exists(txt_path):
                    with open(txt_path, "r") as f:
                        lines = f.readlines()
                    
                    new_lines = []
                    removed_in_file = 0
                    
                    for line in lines:
                        parts = line.strip().split()
                        if not parts: continue
                        
                        if parts[0] == target_class:
                            removed_in_file += 1
                            box_removed_total += 1
                        else:
                            new_lines.append(line)
                    
                    if removed_in_file > 0:
                        modified_count += 1
                        if not new_lines:
                            os.remove(txt_path)
                        else:
                            with open(txt_path, "w") as f:
                                f.writelines(new_lines)

                # Update Progress
                if i % 10 == 0 or i == total - 1:
                    self.update_progress(i + 1, f"Đang xử lý: {i+1} / {total} ảnh...")

            self.update_status("Hoàn tất!")
            self.root.after(0, lambda: messagebox.showinfo(
                "Thành công", 
                f"Đã xử lý xong {total} ảnh.\n\n"
                f"- Số file nhãn đã thay đổi: {modified_count}\n"
                f"- Tổng số box class {target_class} bị xoá: {box_removed_total}"
            ))

        except Exception as e:
            err = str(e)
            self.update_status(f"Lỗi: {err}")
            self.root.after(0, lambda: messagebox.showerror("Lỗi hệ thống", err))
        finally:
            self.root.after(0, lambda: self.btn_start.config(state="normal"))

    def get_label_path(self, img_path):
        """Phân giải đường dẫn nhãn đơn giản (images -> labels hoặc cùng thư mục)."""
        p = pathlib.Path(img_path)
        parts = list(p.parts)
        
        # YOLO structure check
        idx = None
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].lower() == "images":
                idx = i
                break
        
        if idx is not None:
            parts[idx] = "labels"
            return str(pathlib.Path(*parts).with_suffix(".txt"))
        else:
            return str(pathlib.Path(img_path).with_suffix(".txt"))

    def update_status(self, text):
        self.root.after(0, lambda: self.lbl_progress.config(text=text))

    def update_progress(self, val, text):
        self.root.after(0, lambda: self.progress.config(value=val))
        self.update_status(text)

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchDeleteClassApp(root)
    root.mainloop()
