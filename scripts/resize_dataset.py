import os
import glob
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

def resize_images(folder_path, max_size=640):
    """
    Quét tìm tất cả ảnh trong thư mục và resize sao cho cạnh lớn nhất <= max_size
    mà vẫn giữ nguyên tỷ lệ khung hình (aspect ratio).
    """
    # Tìm tất cả ảnh
    image_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        image_paths.extend(glob.glob(os.path.join(folder_path, "**", ext), recursive=True))

    if not image_paths:
        messagebox.showinfo("Thông báo", "Không tìm thấy ảnh nào trong thư mục này!")
        return

    msg = (f"Tìm thấy {len(image_paths)} ảnh.\n"
           f"Chương trình sẽ tự động thay đổi kích thước toàn bộ ảnh về chuẩn dài nhất = {max_size}px.\n"
           "Các file nhãn (.txt) không bị ảnh hưởng do dùng toạ độ tương đối.\n\n"
           "QUAN TRỌNG: Ảnh gốc sẽ bị GHI ĐÈ để giảm dung lượng lưu trữ.\n"
           "Bạn có muốn tiếp tục?")
    
    if not messagebox.askyesno("Xác nhận", msg):
        return

    # Giao diện Progress UI
    progress_win = tk.Toplevel()
    progress_win.title("Đang xử lý")
    progress_win.geometry("350x120")
    
    tk.Label(progress_win, text=f"Đang resize về {max_size}px (Chất lượng cao)...", font=("Arial", 10)).pack(pady=10)
    progress = ttk.Progressbar(progress_win, length=280, mode='determinate')
    progress.pack(pady=10)
    progress["maximum"] = len(image_paths)
    
    lbl_status = tk.Label(progress_win, text=f"0 / {len(image_paths)}", font=("Arial", 9))
    lbl_status.pack()

    progress_win.update()

    processed_count = 0
    saved_size = 0  # Bytes
    
    try:
        for i, img_path in enumerate(image_paths):
            original_size = os.path.getsize(img_path)
            
            with Image.open(img_path) as img:
                w, h = img.size
                if max(w, h) > max_size:
                    # Tính toán tỷ lệ
                    scale = max_size / float(max(w, h))
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    
                    # Resize dùng PIL LANCZOS (Chất lượng cao nhất khi thu nhỏ)
                    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    # Ghi đè (Sử dụng format gốc)
                    img_resized.save(img_path, quality=90, optimize=True)
                    processed_count += 1
                    
                    new_size = os.path.getsize(img_path)
                    saved_size += (original_size - new_size)

            # Cập nhật progress
            if i % 10 == 0 or i == len(image_paths) - 1:
                progress["value"] = i + 1
                lbl_status.config(text=f"{i + 1} / {len(image_paths)}")
                progress_win.update()

    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
    finally:
        progress_win.destroy()

    saved_mb = saved_size / (1024 * 1024)
    messagebox.showinfo("Hoàn tất", f"Đã resize thành công {processed_count} bức ảnh.\nTiết kiệm được khoảng {saved_mb:.2f} MB dung lượng.")


def main():
    root = tk.Tk()
    root.withdraw() # Ẩn cửa sổ chính
    
    folder_path = filedialog.askdirectory(title="Chọn thư mục chứa hình ảnh Dataset")
    if folder_path:
        resize_images(folder_path, max_size=640)


if __name__ == "__main__":
    main()
