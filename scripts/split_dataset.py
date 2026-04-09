import os
import glob
import shutil
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pathlib

class DatasetSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ chia YOLO Dataset (Train/Val/Test)")
        self.root.geometry("500x420")
        
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        self.train_pct = tk.IntVar(value=70)
        self.val_pct = tk.IntVar(value=20)
        self.test_pct = tk.IntVar(value=10)
        
        self.setup_ui()

    def setup_ui(self):
        # 1. Input
        frame_in = tk.LabelFrame(self.root, text="1. Thư mục Dataset gốc (Nơi chứa ảnh & nhãn chung)", padx=10, pady=10)
        frame_in.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_in, textvariable=self.input_dir, width=45, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_in, text="Browse", command=self.browse_input).pack(side="left")

        # 2. Output
        frame_out = tk.LabelFrame(self.root, text="2. Thư mục xuất ra (Chuẩn cấu trúc YOLOv8)", padx=10, pady=10)
        frame_out.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_out, textvariable=self.output_dir, width=45, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_out, text="Browse", command=self.browse_output).pack(side="left")

        # 3. Ratio
        frame_ratio = tk.LabelFrame(self.root, text="3. Tỷ lệ phân chia (%)", padx=10, pady=10)
        frame_ratio.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_ratio, text="Train:").grid(row=0, column=0, padx=5)
        tk.Entry(frame_ratio, textvariable=self.train_pct, width=8).grid(row=0, column=1, padx=5)
        
        tk.Label(frame_ratio, text="Val:").grid(row=0, column=2, padx=5)
        tk.Entry(frame_ratio, textvariable=self.val_pct, width=8).grid(row=0, column=3, padx=5)
        
        tk.Label(frame_ratio, text="Test:").grid(row=0, column=4, padx=5)
        tk.Entry(frame_ratio, textvariable=self.test_pct, width=8).grid(row=0, column=5, padx=5)

        tk.Label(frame_ratio, text="* Lưu ý: Tổng 3 ô phải bằng tròn 100", fg="gray", font=("Arial", 8)).grid(row=1, column=0, columnspan=6, pady=(10,0))

        # Start button
        self.btn_start = tk.Button(self.root, text="BẮT ĐẦU CHIA DATASET", font=("Arial", 12, "bold"), bg="#27ae60", fg="white", command=self.start_split)
        self.btn_start.pack(pady=15)
        
        self.lbl_status = tk.Label(self.root, text="Sẵn sàng...", fg="blue")
        self.lbl_status.pack()

    def browse_input(self):
        path = filedialog.askdirectory()
        if path: self.input_dir.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path: self.output_dir.set(path)

    def start_split(self):
        total = self.train_pct.get() + self.val_pct.get() + self.test_pct.get()
        if total != 100:
            messagebox.showerror("Lỗi", f"Tổng tỉ lệ phân chia phải là 100%. Hiện tại là {total}%")
            return
            
        if not self.input_dir.get() or not self.output_dir.get():
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn đủ thư mục nguồn và đích!")
            return

        self.btn_start.config(state="disabled")
        threading.Thread(target=self.process_split, daemon=True).start()

    def process_split(self):
        try:
            in_dir = self.input_dir.get()
            out_dir = self.output_dir.get()

            self.update_status("Đang tìm file ảnh...")
            # Quét ảnh
            all_images = []
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                all_images.extend(glob.glob(os.path.join(in_dir, "**", ext), recursive=True))

            if not all_images:
                self.root.after(0, lambda: messagebox.showinfo("Lỗi", "Không tìm thấy ảnh nào trong thư mục nguồn!"))
                return

            valid_pairs = []
            
            # Liệt kê nhãn
            for img_path in all_images:
                p = pathlib.Path(img_path)
                parts = list(p.parts)
                idx = None
                for rev_idx in range(len(parts) - 1, -1, -1):
                    if parts[rev_idx].lower() == "images":
                        idx = rev_idx
                        break
                        
                label_path = None
                if idx is not None:
                    parts[idx] = "labels"
                    label_path = str(pathlib.Path(*parts).with_suffix(".txt"))
                else:
                    label_path = os.path.splitext(img_path)[0] + ".txt"

                if os.path.exists(label_path):
                    valid_pairs.append((img_path, label_path))

            if not valid_pairs:
                self.root.after(0, lambda: messagebox.showinfo("Lỗi", "Không tìm thấy CẶP ẢNH-NHÃN nào hợp lệ. Vui lòng kiểm tra lại."))
                return

            self.update_status(f"Tìm được {len(valid_pairs)} cặp file hợp lệ. Đang chia tỉ lệ...")
            
            # Xáo trộn
            random.seed(42)
            random.shuffle(valid_pairs)

            total_pairs = len(valid_pairs)
            train_end = int(total_pairs * self.train_pct.get() / 100)
            val_end = train_end + int(total_pairs * self.val_pct.get() / 100)

            train_set = valid_pairs[:train_end]
            val_set = valid_pairs[train_end:val_end]
            test_set = valid_pairs[val_end:]

            # Cấu trúc tạo folder: train/images, train/labels, valid/images, ...
            sub_dirs = [("train", train_set), ("valid", val_set), ("test", test_set)]

            copied = 0
            for split_name, dataset in sub_dirs:
                if not dataset:
                    continue
                
                # Tạo folder đích chuẩn: split/images, split/labels
                im_out = os.path.join(out_dir, split_name, "images")
                lb_out = os.path.join(out_dir, split_name, "labels")
                os.makedirs(im_out, exist_ok=True)
                os.makedirs(lb_out, exist_ok=True)

                for img_src, lbl_src in dataset:
                    # Chép ảnh
                    shutil.copy2(img_src, os.path.join(im_out, os.path.basename(img_src)))
                    # Chép label
                    shutil.copy2(lbl_src, os.path.join(lb_out, os.path.basename(lbl_src)))
                    copied += 1

                    if copied % 50 == 0:
                        self.update_status(f"Đang copy tiến trình: {copied} / {total_pairs} files...")

            # Tạo file data.yaml mini cho tiện
            yaml_path = os.path.join(out_dir, "data.yaml")
            with open(yaml_path, "w", encoding="utf-8") as f:
                f.write(f"path: {os.path.abspath(out_dir).replace(os.path.sep, '/')}\n")
                f.write("train: train/images\n")
                f.write("val: valid/images\n")
                if test_set:
                    f.write("test: test/images\n")
                f.write("\n")
                f.write("nc: 7\n")
                f.write("names: ['person', 'bicycle', 'car', 'motorcycle', 'license_plate', 'bus', 'truck']\n")

            self.update_status(f"Thành công! Đã chia và copy xong {total_pairs} khung hình.")
            self.root.after(0, lambda: messagebox.showinfo(
                "Hoàn tất", 
                f"Đã xuất YOLO Dataset hoàn chỉnh thành công tại:\n{out_dir}\n\n"
                f"- Train: {len(train_set)}\n- Valid: {len(val_set)}\n- Test: {len(test_set)}"
            ))

        except Exception as e:
            error_msg = str(e)
            self.update_status("Có lỗi xảy ra!")
            self.root.after(0, lambda: messagebox.showerror("Lỗi", error_msg))
        finally:
            self.root.after(0, lambda: self.btn_start.config(state="normal"))

    def update_status(self, text):
        self.root.after(0, lambda: self.lbl_status.config(text=text))

if __name__ == "__main__":
    root = tk.Tk()
    app = DatasetSplitterApp(root)
    root.mainloop()
