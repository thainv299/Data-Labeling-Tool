import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def filter_outlier_boxes(folder_path, multiplier=5.0):
    """
    Lọc bỏ các box có diện tích lớn bất thường (outlier) dựa trên diện tích trung bình của TỪNG lớp.
    Công thức: Diện tích > (Diện tích trung bình của lớp đó * multiplier)
    """
    # 1. Tìm tất cả file nhãn
    labels_dir = os.path.join(folder_path, "labels")
    if os.path.isdir(labels_dir):
        label_files = glob.glob(os.path.join(labels_dir, "**", "*.txt"), recursive=True)
    else:
        label_files = glob.glob(os.path.join(folder_path, "**", "*.txt"), recursive=True)

    label_files = [f for f in label_files if os.path.basename(f) not in ["classes.txt", "data.yaml"]]

    if not label_files:
        messagebox.showinfo("Thông báo", "Không tìm thấy file nhãn (.txt) nào!")
        return

    # 2. Tính toán diện tích trung bình cho TẤT CẢ các lớp có trong Dataset
    areas_by_class = {}
    
    print("Đang phân tích dữ liệu để tính diện tích trung bình...")
    for txt_path in label_files:
        if not os.path.exists(txt_path): continue
        with open(txt_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    cid = int(parts[0])
                    w, h = float(parts[3]), float(parts[4])
                    if cid not in areas_by_class:
                        areas_by_class[cid] = []
                    areas_by_class[cid].append(w * h)

    if not areas_by_class:
        messagebox.showinfo("Thông báo", "Không có dữ liệu nhãn để phân tích.")
        return

    # Tính ngưỡng xoá cho từng class
    class_stats = {}
    summary_msg = f"Phân tích ngưỡng xoá (Gấp {multiplier} lần trung bình):\n\n"
    
    for cid in sorted(areas_by_class.keys()):
        areas = areas_by_class[cid]
        if areas:
            avg_area = sum(areas) / len(areas)
            threshold = avg_area * multiplier
            # Nếu diện tích quá nhỏ (như biển số), ngưỡng tối thiểu nên là 0.1 để tránh xoá nhầm
            # Nhưng ở đây ta tuân thủ tuyệt đối quy tắc "5 lần trung bình" của người dùng.
            class_stats[cid] = threshold
            summary_msg += f"- Class {cid}: TB {avg_area:.5f} -> Ngưỡng xoá: >{threshold:.5f}\n"

    summary_msg += "\nBạn có muốn tiến hành xoá các nhãn vượt ngưỡng này không?"
    
    if not messagebox.askyesno("Xác nhận lọc nhãn to bất thường", summary_msg):
        return

    # 3. Tiến hành lọc
    progress_win = tk.Toplevel()
    progress_win.title("Đang xử lý")
    progress_win.geometry("400x120")
    
    tk.Label(progress_win, text="Đang dọn dẹp các nhãn to bất thường...").pack(pady=10)
    progress = ttk.Progressbar(progress_win, length=300, mode='determinate')
    progress.pack(pady=10)
    progress["maximum"] = len(label_files)
    
    total_removed = 0
    files_modified = 0

    for i, txt_path in enumerate(label_files):
        lines_to_keep = []
        file_changed = False
        
        with open(txt_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 5:
                cid = int(parts[0])
                w, h = float(parts[3]), float(parts[4])
                area = w * h
                
                # Kiểm tra outlier dựa trên ngưỡng của từng class
                if cid in class_stats and area > class_stats[cid]:
                    total_removed += 1
                    file_changed = True
                    continue
                
                lines_to_keep.append(line)
        
        if file_changed:
            if not lines_to_keep:
                try: os.remove(txt_path)
                except: pass
            else:
                with open(txt_path, 'w') as f:
                    f.writelines(lines_to_keep)
            files_modified += 1

        if i % 50 == 0 or i == len(label_files) - 1:
            progress["value"] = i + 1
            progress_win.update()

    progress_win.destroy()
    messagebox.showinfo("Hoàn tất", f"Đã dọn dẹp xong!\n- Số nhãn to bất thường bị xoá: {total_removed}\n- Số file đã cập nhật: {files_modified}")

def main():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Chọn thư mục Dataset để lọc Outlier")
    if folder_path:
        filter_outlier_boxes(folder_path)

if __name__ == "__main__":
    main()
