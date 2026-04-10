import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def filter_large_boxes(folder_path, threshold=0.9, exclude_ids=[5, 6]):
    """
    Quét toàn bộ thư mục labels, lọc bỏ các box quá lớn (>90% frame)
    trừ các class bus(5) và truck(6).
    """
    # Tìm tất cả file .txt trong thư mục labels/ (nếu là yolo_dataset) hoặc trực tiếp
    label_files = []
    
    # Thử tìm trong thư mục labels/ nếu folder được chọn là gốc
    labels_dir = os.path.join(folder_path, "labels")
    if os.path.isdir(labels_dir):
        label_files = glob.glob(os.path.join(labels_dir, "**", "*.txt"), recursive=True)
    else:
        label_files = glob.glob(os.path.join(folder_path, "**", "*.txt"), recursive=True)

    label_files = [f for f in label_files if os.path.basename(f) not in ["classes.txt", "data.yaml"]]

    if not label_files:
        messagebox.showinfo("Thông báo", "Không tìm thấy file nhãn (.txt) nào!")
        return

    msg = (f"Tìm thấy {len(label_files)} file nhãn.\n"
           f"Chương trình sẽ xoá các box có Chiều rộng hoặc Chiều cao > {int(threshold*100)}%\n"
           f"Ngoại trừ: Class ID {exclude_ids} (Bus, Truck).\n\n"
           "Bạn có muốn tiếp tục?")
    
    if not messagebox.askyesno("Xác nhận", msg):
        return

    # Giao diện Progress UI
    progress_win = tk.Toplevel()
    progress_win.title("Đang lọc box")
    progress_win.geometry("400x120")
    
    tk.Label(progress_win, text="Đang quét và lọc các bounding box 'nhầm'...", font=("Arial", 10)).pack(pady=10)
    progress = ttk.Progressbar(progress_win, length=300, mode='determinate')
    progress.pack(pady=10)
    progress["maximum"] = len(label_files)
    progress_win.update()

    total_removed = 0
    files_modified = 0

    try:
        for i, txt_path in enumerate(label_files):
            lines_to_keep = []
            file_changed = False
            
            if not os.path.exists(txt_path): continue

            with open(txt_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 5:
                    cls_id = int(parts[0])
                    w = float(parts[3])
                    h = float(parts[4])
                    
                    # Điều kiện lọc: Rộng hoặc Cao quá 90% và không phải xe bus/xe tải
                    if (w > threshold or h > threshold) and cls_id not in exclude_ids:
                        total_removed += 1
                        file_changed = True
                        continue
                    
                    lines_to_keep.append(line)
            
            if file_changed:
                with open(txt_path, 'w') as f:
                    f.writelines(lines_to_keep)
                files_modified += 1

            if i % 20 == 0 or i == len(label_files) - 1:
                progress["value"] = i + 1
                progress_win.update()

    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
    finally:
        progress_win.destroy()

    messagebox.showinfo("Hoàn tất", f"Đã quét xong {len(label_files)} file.\n"
                                     f"- Số box bị xoá: {total_removed}\n"
                                     f"- Số file đã cập nhật: {files_modified}")

def main():
    root = tk.Tk()
    root.withdraw()
    
    folder_path = filedialog.askdirectory(title="Chọn thư mục Dataset (quét đệ quy file .txt)")
    if folder_path:
        filter_large_boxes(folder_path)

if __name__ == "__main__":
    main()
