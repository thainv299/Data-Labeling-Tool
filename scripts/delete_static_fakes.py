import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

def delete_labels_at_point_logic(ds_dir, target_cls, target_x, target_y, start_idx=0, end_idx=None):
    """
    Logic cốt lõi để xóa nhãn tại một tọa độ chỉ định trong một phạm vi ảnh nhất định.
    """
    # Tìm file nhãn
    labels_dir = os.path.join(ds_dir, "labels")
    if os.path.isdir(labels_dir):
        label_files = glob.glob(os.path.join(labels_dir, "**", "*.txt"), recursive=True)
    else:
        label_files = glob.glob(os.path.join(ds_dir, "**", "*.txt"), recursive=True)

    # YOLO labels thường đi kèm images. Ta cần sort để khớp với thứ tự hiển thị của App.
    # Tuy nhiên, App hiển thị theo image_paths. Ở đây ta sort theo tên file để đảm bảo tính nhất quán.
    label_files = sorted([f for f in label_files if os.path.basename(f) not in ["classes.txt", "data.yaml"]])

    if not label_files:
        messagebox.showinfo("Thông báo", "Không tìm thấy file nhãn nào.")
        return

    # Xác định phạm vi xử lý
    total_files = len(label_files)
    if end_idx is None or end_idx >= total_files:
        end_idx = total_files - 1
    
    start_idx = max(0, start_idx)
    target_files = label_files[start_idx : end_idx + 1]

    if not target_files:
        messagebox.showwarning("Cảnh báo", "Phạm vi ảnh không hợp lệ!")
        return

    # Cửa sổ tiến trình
    progress_win = tk.Toplevel()
    progress_win.title("Đang xử lý...")
    progress_win.geometry("400x120")
    tk.Label(progress_win, text=f"Đang xóa Class {target_cls} (Ảnh {start_idx+1} đến {end_idx+1})...").pack(pady=10)
    progress = ttk.Progressbar(progress_win, length=300, mode='determinate')
    progress.pack(pady=10)
    progress["maximum"] = len(target_files)

    removed_count = 0
    modified_files = 0

    for i, txt_path in enumerate(target_files):
        lines_to_keep = []
        changed = False
        
        if not os.path.exists(txt_path): continue
        
        with open(txt_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 5:
                cid = int(parts[0])
                xc, yc, w, h = map(float, parts[1:])
                
                # Kiểm tra xem điểm (target_x, target_y) có nằm trong box không
                if cid == target_cls:
                    x1, y1 = xc - w/2, yc - h/2
                    x2, y2 = xc + w/2, yc + h/2
                    
                    if x1 <= target_x <= x2 and y1 <= target_y <= y2:
                        removed_count += 1
                        changed = True
                        continue # Bỏ qua dòng này (xóa)
                
                lines_to_keep.append(line)
        
        if changed:
            if not lines_to_keep:
                try: os.remove(txt_path)
                except: pass
            else:
                with open(txt_path, 'w') as f:
                    f.writelines(lines_to_keep)
            modified_files += 1

        if i % 50 == 0 or i == len(target_files) - 1:
            progress["value"] = i + 1
            progress_win.update()

    # Đảm bảo hiển thị đầy đủ 100%
    progress["value"] = len(target_files)
    progress_win.update()

    messagebox.showinfo("Hoàn tất", f"Đã dọn dẹp xong dải ảnh chỉ định!\n"
                                     f"- Số nhãn đã xoá: {removed_count}\n"
                                     f"- Số file đã cập nhật: {modified_files}", parent=progress_win)
    progress_win.destroy()

def delete_labels_at_point():
    """Hàm chạy độc lập (Hỏi người dùng toàn bộ thông tin)."""
    root = tk.Tk()
    root.withdraw()
    
    ds_dir = filedialog.askdirectory(title="Chọn thư mục Dataset cần dọn dẹp")
    if not ds_dir: return

    target_cls = simpledialog.askinteger("Cấu hình", "Nhập Class ID muốn xóa:", initialvalue=4)
    if target_cls is None: return

    target_x = simpledialog.askfloat("Cấu hình", "Tọa độ X chuẩn hóa (0.0 - 1.0):", initialvalue=0.5)
    if target_x is None: return

    target_y = simpledialog.askfloat("Cấu hình", "Tọa độ Y chuẩn hóa (0.0 - 1.0):", initialvalue=0.5)
    if target_y is None: return

    delete_labels_at_point_logic(ds_dir, target_cls, target_x, target_y)

if __name__ == "__main__":
    delete_labels_at_point()
