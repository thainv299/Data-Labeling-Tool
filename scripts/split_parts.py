import os
import shutil
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class DatasetPartSplitterApp:
    def __init__(self, root, initial_dir=""):
        self.root = root
        self.root.title("Chia nhỏ Dataset thành N phần")
        self.root.geometry("500x550")
        
        self.source_dir = tk.StringVar(value=initial_dir)
        self.num_parts = tk.IntVar(value=2)
        self.folder_names = [] # Danh sách các Entry chứa tên folder từ phần 2 trở đi
        
        self._setup_ui()

    def _setup_ui(self):
        # 1. Chọn thư mục gốc
        frame_top = tk.LabelFrame(self.root, text="1. Chọn thư mục Dataset gốc", padx=10, pady=10)
        frame_top.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_top, textvariable=self.source_dir, width=45).pack(side="left", padx=5)
        tk.Button(frame_top, text="Browse", command=self.browse_dir).pack(side="left")

        # 2. Chọn số phần
        frame_mid = tk.Frame(self.root, padx=10, pady=10)
        frame_mid.pack(fill="x", padx=10)
        tk.Label(frame_mid, text="Số lượng phần muốn chia (N):").pack(side="left")
        spin = tk.Spinbox(frame_mid, from_=2, to=20, textvariable=self.num_parts, width=5, command=self.generate_fields)
        spin.pack(side="left", padx=10)
        tk.Button(frame_mid, text="Cập nhật ô nhập", command=self.generate_fields).pack(side="left")

        # 3. Danh sách tên các folder mới
        self.scroll_frame = tk.LabelFrame(self.root, text="2. Tên các thư mục con (Phần 2 trở đi)", padx=10, pady=10)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(self.scroll_frame)
        self.scrollbar = ttk.Scrollbar(self.scroll_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_content = tk.Frame(self.canvas)

        self.scrollable_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 4. Nút thực hiện
        self.btn_run = tk.Button(self.root, text="BẮT ĐẦU CHIA DỮ LIỆU", font=("Arial", 12, "bold"), 
                                 bg="#27ae60", fg="white", pady=10, command=self.run_split)
        self.btn_run.pack(fill="x", padx=10, pady=10)

        # Khởi tạo mặc định
        self.generate_fields()

    def browse_dir(self):
        path = filedialog.askdirectory()
        if path: self.source_dir.set(path)

    def generate_fields(self):
        # Xoá các ô cũ
        for widget in self.scrollable_content.winfo_children():
            widget.destroy()
        self.folder_names = []

        try:
            n = int(self.num_parts.get())
        except:
            return

        tk.Label(self.scrollable_content, text="Phần 1: Giữ nguyên tại thư mục gốc", fg="#2980b9", font=("Arial", 9, "bold")).pack(pady=5, anchor="w")
        
        for i in range(2, n + 1):
            frame = tk.Frame(self.scrollable_content)
            frame.pack(fill="x", pady=2)
            tk.Label(frame, text=f"Phần {i} - Tên folder:", width=15, anchor="w").pack(side="left")
            entry = tk.Entry(frame, width=30)
            entry.insert(0, f"dataset_part_{i}")
            entry.pack(side="left", padx=5)
            self.folder_names.append(entry)

    def run_split(self):
        src = self.source_dir.get()
        if not src or not os.path.exists(src):
            messagebox.showerror("Lỗi", "Thư mục gốc không hợp lệ!")
            return

        # 1. Tìm tất cả ảnh (không quét đệ quy sâu vào các thư mục con khác, chỉ images/ hoặc trực tiếp)
        all_images = []
        for ext in (".jpg", ".jpeg", ".png"):
            # Quét thư mục gốc
            for f in os.listdir(src):
                if f.lower().endswith(ext):
                    all_images.append(os.path.join(src, f))
            
            # Quét images/ nếu là cấu trúc YOLO
            img_sub = os.path.join(src, "images")
            if os.path.exists(img_sub):
                for f in os.listdir(img_sub):
                    if f.lower().endswith(ext):
                        all_images.append(os.path.join(img_sub, f))
        
        # Sắp xếp theo tên để chia cho đúng thứ tự
        all_images.sort()
        total = len(all_images)
        if total == 0:
            messagebox.showwarning("Trống", "Không tìm thấy ảnh nào trong thư mục này!")
            return

        n = self.num_parts.get()
        per_part = math.ceil(total / n)
        
        confirm = messagebox.askyesno("Xác nhận", f"Tìm thấy {total} ảnh.\nSẽ chia thành {n} phần, mỗi phần ~{per_part} ảnh.\n\n"
                                                 f"LƯU Ý: Thao tác này sẽ DI CHUYỂN file vật lý từ thư mục gốc sang các thư mục mới.\n"
                                                 f"Bạn có chắc chắn?")
        if not confirm: return

        try:
            # Bắt đầu chia từ phần 2 (vì phần 1 giữ nguyên)
            current_idx = per_part # Bỏ qua các ảnh của phần 1
            
            for i in range(n - 1):
                dest_folder_name = self.folder_names[i].get().strip()
                if not dest_folder_name: continue
                
                # Tạo thư mục đích (nằm cùng cấp với thư mục gốc)
                parent_dir = os.path.dirname(src)
                dest_base = os.path.join(parent_dir, dest_folder_name)
                
                # Lấy danh sách ảnh cho phần này
                end_idx = min(current_idx + per_part, total)
                batch = all_images[current_idx:end_idx]
                
                if not batch: break

                for img_path in batch:
                    self._move_file_pair(img_path, src, dest_base)
                
                current_idx = end_idx

            messagebox.showinfo("Thành công", f"Đã chia nhỏ dataset thành công!\nCác phần mới đã được tạo tại: {parent_dir}")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

    def _move_file_pair(self, img_path, src_base, dest_base):
        """Di chuyển cả ảnh và file nhãn tương ứng."""
        # Xác định đường dẫn tương đối từ src_base
        rel_path = os.path.relpath(img_path, src_base)
        dest_img_path = os.path.join(dest_base, rel_path)
        os.makedirs(os.path.dirname(dest_img_path), exist_ok=True)
        
        # 1. Di chuyển ảnh
        shutil.move(img_path, dest_img_path)
        
        # 2. Tìm và di chuyển nhãn (.txt)
        # Thử thay 'images' thành 'labels' trong đường dẫn nếu có
        if "images" in rel_path:
            label_rel = rel_path.replace("images", "labels")
        else:
            # Nếu không có cấu trúc images/labels, giả định nhãn nằm cùng thư mục ảnh
            label_rel = rel_path
            
        # Đổi đuôi thành .txt
        label_rel = os.path.splitext(label_rel)[0] + ".txt"
        
        src_label = os.path.join(src_base, label_rel)
        if os.path.exists(src_label):
            dest_label = os.path.join(dest_base, label_rel)
            os.makedirs(os.path.dirname(dest_label), exist_ok=True)
            shutil.move(src_label, dest_label)

if __name__ == "__main__":
    root = tk.Tk()
    app = DatasetPartSplitterApp(root)
    root.mainloop()
