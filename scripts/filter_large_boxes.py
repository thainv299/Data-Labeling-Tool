import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def filter_outlier_boxes(folder_path, target_ids=[0, 1, 3], multiplier=5.0):
    """
    Lọc bỏ các box có diện tích lớn bất thường (outlier) dựa trên diện tích trung bình.
    Áp dụng cho các class cụ thể (person, bicycle, motorcycle).
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

    # 2. Bước lấy mẫu (Sampling) để tính diện tích trung bình
    # Chúng ta lấy khoảng 300 nhãn đầu tiên của mỗi class mục tiêu
    areas_by_class = {cid: [] for cid in target_ids}
    sample_limit = 300
    
    for txt_path in label_files:
        if all(len(areas) >= sample_limit for areas in areas_by_class.values()):
            break
        
        if not os.path.exists(txt_path): continue
        with open(txt_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    cid = int(parts[0])
                    if cid in target_ids and len(areas_by_class[cid]) < sample_limit:
                        w, h = float(parts[3]), float(parts[4])
                        areas_by_class[cid].append(w * h)

    # Tính toán diện tích trung bình và ngưỡng xoá cho từng class
    class_stats = {}
    for cid, areas in areas_by_class.items():
        if areas:
            avg_area = sum(areas) / len(areas)
            # Ngưỡng xoá = trung bình * hệ số
            threshold = avg_area * multiplier
            class_stats[cid] = {
                'avg': avg_area,
                'threshold': threshold
            }
        else:
            # Nếu class này không có trong mẫu, dùng ngưỡng mặc định an toàn (80% frame)
            class_stats[cid] = {'avg': 0, 'threshold': 0.8}

    # Hiển thị thông tin thống kê cho người dùng
    summary_msg = "Kết quả phân tích trung bình diện tích:\n"
    class_names = {0: "Person", 1: "Bicycle", 3: "Motorcycle"}
    for cid, stats in class_stats.items():
        if stats['avg'] > 0:
            summary_msg += f"- {class_names.get(cid, cid)}: TB {stats['avg']:.4f} -> Ngưỡng xoá: >{stats['threshold']:.4f}\n"
    
    summary_msg += "\n(Lưu ý: Chỉ xoá các box thuộc 3 lớp trên có diện tích lớn hơn ngưỡng thống kê).\nBạn có muốn tiếp tục?"
    
    if not messagebox.askyesno("Xác nhận lọc Outlier", summary_msg):
        return

    # 3. Tiến hành lọc thực tế
    progress_win = tk.Toplevel()
    progress_win.title("Đang xử lý Outlier")
    progress_win.geometry("400x120")
    
    tk.Label(progress_win, text="Đang lọc các box có diện tích bất thường...", font=("Arial", 10)).pack(pady=10)
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
            
            with open(txt_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 5:
                    cid = int(parts[0])
                    w, h = float(parts[3]), float(parts[4])
                    area = w * h
                    
                    if cid in class_stats:
                        # Kiểm tra xem có phải outlier không
                        if area > class_stats[cid]['threshold']:
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
                                     f"- Số box outlier bị xoá: {total_removed}\n"
                                     f"- Số file đã cập nhật: {files_modified}")

def main():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Chọn thư mục Dataset để lọc Outlier")
    if folder_path:
        filter_outlier_boxes(folder_path)

if __name__ == "__main__":
    main()
