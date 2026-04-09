import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def change_label_id(folder_path, old_id=0, new_id=4):
    """
    Quét toàn bộ thư mục và các thư mục con chứa file .txt.
    Mở từng file, nếu dòng nào bắt đầu bằng old_id, chuyển đổi thành new_id.
    Thao tác thực hiện cực kì an toàn do chỉ update dòng được nhắm mục tiêu.
    """
    txt_files = glob.glob(os.path.join(folder_path, "**", "*.txt"), recursive=True)
    
    # Loại trừ classes.txt bảo đảm an toàn hệ thống
    txt_files = [f for f in txt_files if os.path.basename(f) not in ["classes.txt", "data.yaml"]]

    if not txt_files:
        messagebox.showinfo("Thông báo", "Không tìm thấy file label (.txt) nào trong thư mục!")
        return

    msg = (f"Tìm thấy {len(txt_files)} file nhãn YOLO.\n\n"
           f"Chương trình sẽ tự động dò tìm các thẻ có ID là {old_id} (Biển số cũ)\n"
           f"Và đổi thay thế thành ID {new_id} (Biển số mới chuẩn).\n\n"
           "Hành động này sẽ xoá đè dòng sửa lên file hiện tại (Tốc độ rất nhanh).\n"
           "Bạn đã copy 1 bản để dự phòng chưa? Bạn có muốn thực hiện không?")
           
    if not messagebox.askyesno("Xác nhận", msg):
        return

    # Popup thông báo quá trình chạy
    progress_win = tk.Toplevel()
    progress_win.title("Đang xử lý Convert ID")
    progress_win.geometry("350x120")
    
    tk.Label(progress_win, text=f"Đang đổi hàng loạt class {old_id} -> {new_id}...", font=("Arial", 10)).pack(pady=10)
    progress = ttk.Progressbar(progress_win, length=280, mode='determinate')
    progress.pack(pady=5)
    progress["maximum"] = len(txt_files)
    
    lbl_status = tk.Label(progress_win, text=f"0 / {len(txt_files)}", font=("Arial", 9))
    lbl_status.pack()
    progress_win.update()

    modified_files = 0
    total_modified_lines = 0

    try:
        str_old = str(old_id)
        str_new = str(new_id)

        for i, txt_path in enumerate(txt_files):
            with open(txt_path, "r") as f:
                lines = f.readlines()
            
            changed = False
            new_lines = []
            
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue
                # Chỉ soi class ID (số đầu tiên), nếu chuẩn xác thì sửa
                if parts[0] == str_old:
                    parts[0] = str_new
                    new_lines.append(" ".join(parts) + "\n")
                    changed = True
                    total_modified_lines += 1
                else:
                    new_lines.append(line)
            
            if changed:
                with open(txt_path, "w") as f:
                    f.writelines(new_lines)
                modified_files += 1

            if i % 100 == 0 or i == len(txt_files) - 1:
                progress["value"] = i + 1
                lbl_status.config(text=f"{i + 1} / {len(txt_files)}")
                progress_win.update()
                
    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra trong quá trình sửa file: {e}")
    finally:
        if progress_win.winfo_exists():
            progress_win.destroy()

    messagebox.showinfo(
        "Thành công", 
        f"Hoàn tất dọn dẹp ID trên dataset!\n\n"
        f"- Tổng file đã quét: {len(txt_files)}\n"
        f"- Tổng file có chứa biển số cần đổi: {modified_files}\n"
        f"- Số nhãn (box) đã được chuyển sang id {new_id}: {total_modified_lines} nhãn."
    )

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # Ẩn cửa sổ TK
    
    # Mở folder dialog
    target_folder = filedialog.askdirectory(title="Chọn thư mục chứa dataset biển số cũ để đổi Class 0 -> 4")
    if target_folder:
        change_label_id(target_folder, old_id=0, new_id=4)
