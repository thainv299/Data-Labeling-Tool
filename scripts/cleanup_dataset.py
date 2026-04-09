import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

def cleanup_unmatched(folder_path):
    """
    Quét đệ quy toàn bộ thư mục và so khớp song phương (Bidirectional Sync):
    1. Tìm tất cả ảnh (.jpg, .png), nếu không có file .txt cùng cơ sở -> Xoá ảnh (cân nhắc vì YOLO coi đây là ảnh background).
    2. Tìm tất cả file .txt, nếu không có ảnh đi kèm -> Xoá .txt rác.
    """
    # Lấy toàn bộ ảnh và labels
    all_images = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        all_images.extend(glob.glob(os.path.join(folder_path, "**", ext), recursive=True))
        
    all_txts = glob.glob(os.path.join(folder_path, "**", "*.txt"), recursive=True)
    all_txts = [f for f in all_txts if os.path.basename(f) not in ["classes.txt", "data.yaml"]]

    # So khớp nhanh qua Set với Stem (Đường dẫn cơ sở không đuôi, để trong cùng 1 folder chung hoặc lệch logic)
    # Tuy nhiên, an toàn nhất là kiểm tra chéo theo đường dẫn: images <-> labels
    
    orphan_images = []
    orphan_txts = []

    # 1. Tìm ảnh dư (Không có nhãn)
    for img_path in all_images:
        p = Path(img_path)
        parts = list(p.parts)
        idx = None
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].lower() == "images":
                idx = i
                break
        
        label_path = None
        if idx is not None:
            parts[idx] = "labels"
            label_path = Path(*parts).with_suffix(".txt")
        else:
            label_path = p.with_suffix(".txt")

        if not os.path.exists(label_path):
            orphan_images.append(img_path)

    # 2. Tìm nhãn rác (Không có ảnh)
    for txt_path in all_txts:
        p = Path(txt_path)
        parts = list(p.parts)
        idx = None
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].lower() == "labels":
                idx = i
                break
        
        if idx is not None:
            parts[idx] = "images"
            
        img_base = Path(*parts).with_suffix("")
        if not (os.path.exists(str(img_base) + ".jpg") or 
                os.path.exists(str(img_base) + ".png") or 
                os.path.exists(str(img_base) + ".jpeg")):
            orphan_txts.append(txt_path)

    if not orphan_images and not orphan_txts:
        messagebox.showinfo("Hoàn hảo", "Tuyệt vời! Số lượng file Ảnh và Nhãn đã song phẳng 1-1. Không có file nào rác.")
        return

    msg = f"Phát hiện sự lệch pha dữ liệu:\n"
    if orphan_images:
        msg += f"👉 {len(orphan_images)} Ảnh KHÔNG CÓ file nhãn (.txt)\n"
    if orphan_txts:
        msg += f"👉 {len(orphan_txts)} Nhãn (.txt) KHÔNG CÓ file ảnh đi kèm\n"
        
    msg += "\nTool sẽ xoá toàn bộ những file dư thừa này để làm sạch dataset. Bạn có đồng ý không?"
    
    if not messagebox.askyesno("Xác nhận dọn dẹp", msg):
        return

    # Tiến hành xoá
    deleted_imgs = 0
    deleted_txts = 0
    try:
        for f in orphan_images:
            try:
                os.remove(f)
                deleted_imgs += 1
            except: pass
            
        for f in orphan_txts:
            try:
                os.remove(f)
                deleted_txts += 1
            except: pass
            
        messagebox.showinfo("Thành công", f"Đã dọn dẹp xong!\n- Xoá {deleted_imgs} ảnh thừa.\n- Xoá {deleted_txts} file nhãn rác.\nDataset hiện tại đã cân bằng 1-1.")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi khi xoá: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    target_folder = filedialog.askdirectory(title="Chọn thư mục chứa dataset bị lệch pha (sẽ quét đệ quy)")
    if target_folder:
        cleanup_unmatched(target_folder)
