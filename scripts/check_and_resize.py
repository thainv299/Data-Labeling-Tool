import os
import cv2
import glob
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def check_and_resize_dataset():
    # Tạo một cửa sổ tạm để chọn thư mục
    temp_root = tk.Tk()
    temp_root.withdraw()
    ds_dir = filedialog.askdirectory(title="Chọn thư mục Dataset cần kiểm tra kích thước")
    temp_root.destroy()
    
    if not ds_dir:
        return

    # Tạo cửa sổ hiển thị tiến trình
    root = tk.Tk()
    root.title("Đang kiểm tra kích thước ảnh")
    root.geometry("400x180")
    root.resizable(False, False)

    lbl_status = tk.Label(root, text="Đang quét tìm ảnh...", font=("Arial", 10))
    lbl_status.pack(pady=10)

    progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=10)

    lbl_count = tk.Label(root, text="Khởi tạo...")
    lbl_count.pack()

    def run_process():
        # 1. Quét tìm ảnh
        image_paths = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            image_paths.extend(glob.glob(os.path.join(ds_dir, "**", ext), recursive=True))

        if not image_paths:
            root.after(0, lambda: [messagebox.showinfo("Trống", "Không tìm thấy ảnh nào!"), root.destroy()])
            return

        total = len(image_paths)
        root.after(0, lambda: progress.configure(maximum=total))
        
        oversized_images = []
        
        # 2. Kiểm tra kích thước
        for i, img_path in enumerate(image_paths):
            if i % 10 == 0 or i == total - 1:
                root.after(0, lambda v=i+1: [
                    progress.configure(value=v),
                    lbl_count.configure(text=f"Đang quét: {v} / {total}"),
                    lbl_status.configure(text=f"Đang kiểm tra: {os.path.basename(img_path)}")
                ])

            # Đọc kích thước
            try:
                img = cv2.imread(img_path)
                if img is not None:
                    h, w = img.shape[:2]
                    if max(h, w) > 640:
                        oversized_images.append((img_path, w, h))
            except:
                continue

        # 3. Kết quả và Resize
        if not oversized_images:
            root.after(0, lambda: [messagebox.showinfo("Kết quả", "Tất cả ảnh đều đã đúng chuẩn <= 640px."), root.destroy()])
        else:
            def ask_and_resize():
                msg = f"Phát hiện {len(oversized_images)} ảnh vượt quá 640px.\n\nBạn có muốn tự động Resize chúng không?"
                if messagebox.askyesno("Phát hiện ảnh lớn", msg):
                    lbl_status.configure(text="Đang thực hiện Resize...")
                    progress.configure(value=0, maximum=len(oversized_images))
                    
                    for k, (img_path, w, h) in enumerate(oversized_images):
                        try:
                            img = cv2.imread(img_path)
                            scale = 640.0 / float(max(w, h))
                            new_w, new_h = int(w * scale), int(h * scale)
                            img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                            cv2.imwrite(img_path, img_resized)
                        except: pass
                        
                        root.after(0, lambda v=k+1: [
                            progress.configure(value=v),
                            lbl_count.configure(text=f"Đã sửa: {v} / {len(oversized_images)}")
                        ])
                    
                    messagebox.showinfo("Thành công", f"Đã resize xong {len(oversized_images)} ảnh!")
                root.destroy()

            root.after(0, ask_and_resize)

    # Chạy logic trong thread riêng để không treo UI
    threading.Thread(target=run_process, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    check_and_resize_dataset()
