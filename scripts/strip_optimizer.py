import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

def strip_model_checkpoint(checkpoint_path, output_path=None):
    """
    Loại bỏ optimizer, EMA, scaler và loss criterion từ checkpoint PyTorch/YOLO
    đang train dở (last.pt, epoch*.pt) để giảm dung lượng đáng kể và chuẩn bị cho inference.

    Returns:
        (success: bool, message: str, orig_mb: float, new_mb: float)
    """
    if not os.path.isfile(checkpoint_path):
        return False, f"Tệp không tồn tại: {checkpoint_path}", 0, 0

    orig_size = os.path.getsize(checkpoint_path) / (1024 * 1024)
    save_path = output_path if output_path else checkpoint_path

    # Cách 1: Thử dùng strip_optimizer chính thức của Ultralytics
    try:
        from ultralytics.utils.torch_utils import strip_optimizer
        result = strip_optimizer(checkpoint_path, s=save_path if save_path != checkpoint_path else "")
        if result and os.path.exists(save_path):
            new_size = os.path.getsize(save_path) / (1024 * 1024)
            return True, "Thành công bằng Ultralytics strip_optimizer", orig_size, new_size
    except Exception as e_ultra:
        pass

    # Cách 2: Fallback trực tiếp bằng PyTorch
    try:
        import torch
        ckpt = torch.load(checkpoint_path, map_location="cpu")
        if not isinstance(ckpt, dict) or "model" not in ckpt:
            return False, "File không phải định dạng checkpoint PyTorch/YOLO hợp lệ (thiếu khóa 'model').", orig_size, 0

        # Nếu có EMA weights (trọng số mượt), ưu tiên dùng làm trọng số chính
        if ckpt.get("ema"):
            ckpt["model"] = ckpt["ema"]

        # Xoá loss criterion
        if hasattr(ckpt["model"], "criterion"):
            ckpt["model"].criterion = None

        # Chuyển model sang nửa độ chính xác (FP16) để tiết kiệm thêm 50% dung lượng
        try:
            ckpt["model"].half()
            for p in ckpt["model"].parameters():
                p.requires_grad = False
        except Exception:
            pass

        # Xoá optimizer và các trường training nặng
        for k in ("optimizer", "best_fitness", "ema", "updates", "scaler"):
            ckpt[k] = None
        ckpt["epoch"] = -1

        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        torch.save(ckpt, save_path)
        new_size = os.path.getsize(save_path) / (1024 * 1024)
        return True, "Thành công bằng PyTorch fallback", orig_size, new_size
    except Exception as e:
        return False, f"Lỗi xử lý checkpoint: {str(e)}", orig_size, 0


class StripOptimizerApp:
    def __init__(self, root, initial_model_path=""):
        self.root = root
        self.root.title("Strip Optimizer - Tối ưu Model (.pt)")
        self.root.geometry("620x460")
        self.root.minsize(580, 420)

        self.input_path = tk.StringVar(value=initial_model_path)
        self.output_path = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=False)
        self.orig_size_str = tk.StringVar(value="Chưa chọn file")

        self._setup_ui()
        if initial_model_path and os.path.isfile(initial_model_path):
            self._on_model_selected(initial_model_path)

    def _setup_ui(self):
        # Header banner
        header_frame = tk.Frame(self.root, bg="#2c3e50", padx=15, pady=12)
        header_frame.pack(fill="x")
        tk.Label(
            header_frame,
            text="STRIP OPTIMIZER",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#2c3e50"
        ).pack(anchor="w")
        tk.Label(
            header_frame,
            text="Loại bỏ Optimizer, EMA, scaler khỏi file checkpoint (last.pt, epoch*.pt)\nđể giảm 50% - 80% dung lượng và tối ưu cho Inference / Auto-Annotate.",
            font=("Arial", 9),
            fg="#bdc3c7",
            bg="#2c3e50",
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

        content = tk.Frame(self.root, padx=15, pady=10)
        content.pack(fill="both", expand=True)

        # 1. Chọn file checkpoint đầu vào
        grp_in = tk.LabelFrame(content, text="1. File Model Checkpoint cần Strip (.pt)", padx=10, pady=8, font=("Arial", 9, "bold"))
        grp_in.pack(fill="x", pady=5)

        row_in = tk.Frame(grp_in)
        row_in.pack(fill="x")
        tk.Entry(row_in, textvariable=self.input_path, width=48).pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(row_in, text="Browse...", command=self.browse_input, width=10).pack(side="right")

        tk.Label(grp_in, textvariable=self.orig_size_str, fg="#7f8c8d", font=("Arial", 9, "italic")).pack(anchor="w", pady=(4, 0))

        # 2. Tuỳ chọn lưu đầu ra
        grp_out = tk.LabelFrame(content, text="2. Tùy chọn lưu file sau khi Strip", padx=10, pady=8, font=("Arial", 9, "bold"))
        grp_out.pack(fill="x", pady=8)

        tk.Radiobutton(
            grp_out,
            text="Lưu thành file mới (Khuyên dùng để giữ lại checkpoint train tiếp)",
            variable=self.overwrite_var,
            value=False,
            command=self._toggle_output_mode
        ).pack(anchor="w")

        self.row_out = tk.Frame(grp_out)
        self.row_out.pack(fill="x", padx=20, pady=4)
        tk.Entry(self.row_out, textvariable=self.output_path, width=42).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_browse_out = tk.Button(self.row_out, text="Browse...", command=self.browse_output, width=10)
        self.btn_browse_out.pack(side="right")

        tk.Radiobutton(
            grp_out,
            text="Ghi đè trực tiếp lên file gốc (Cảnh báo: không thể dùng để train tiếp tục)",
            variable=self.overwrite_var,
            value=True,
            fg="#c0392b",
            command=self._toggle_output_mode
        ).pack(anchor="w", pady=(4, 0))

        # 3. Tiến trình & Nút xử lý
        self.lbl_status = tk.Label(content, text="Sẵn sàng...", fg="#2980b9", font=("Arial", 9, "bold"))
        self.lbl_status.pack(pady=4)

        self.btn_start = tk.Button(
            content,
            text="BẮT ĐẦU STRIP OPTIMIZER",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#2ecc71",
            activeforeground="white",
            padx=15,
            pady=6,
            command=self.start_processing
        )
        self.btn_start.pack(pady=6)

    def _on_model_selected(self, path):
        if not os.path.isfile(path):
            return
        size_mb = os.path.getsize(path) / (1024 * 1024)
        self.orig_size_str.set(f"Dung lượng hiện tại: {size_mb:.2f} MB")

        # Đặt tên mặc định cho file stripped
        p = Path(path)
        suggested_out = str(p.with_stem(p.stem + "_stripped"))
        self.output_path.set(suggested_out)

    def browse_input(self):
        path = filedialog.askopenfilename(
            title="Chọn file checkpoint YOLO (.pt)",
            filetypes=[("PyTorch Checkpoint", "*.pt"), ("All Files", "*.*")]
        )
        if path:
            self.input_path.set(path)
            self._on_model_selected(path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu model sau khi strip",
            defaultextension=".pt",
            filetypes=[("PyTorch Model", "*.pt")]
        )
        if path:
            self.output_path.set(path)

    def _toggle_output_mode(self):
        if self.overwrite_var.get():
            self.btn_browse_out.config(state="disabled")
        else:
            self.btn_browse_out.config(state="normal")

    def start_processing(self):
        in_path = self.input_path.get().strip()
        if not in_path or not os.path.isfile(in_path):
            messagebox.showwarning("Thiếu file", "Vui lòng chọn file checkpoint (.pt) cần strip!")
            return

        if self.overwrite_var.get():
            out_path = in_path
            if not messagebox.askyesno(
                "Xác nhận ghi đè",
                "Ghi đè trực tiếp sẽ xóa sạch optimizer và không thể dùng checkpoint này để resume training.\nBạn có chắc chắn không?"
            ):
                return
        else:
            out_path = self.output_path.get().strip()
            if not out_path:
                messagebox.showwarning("Thiếu đường dẫn", "Vui lòng chọn đường dẫn lưu file model mới!")
                return

        self.btn_start.config(state="disabled", text="ĐANG XỬ LÝ (STRIPPING)...")
        self.lbl_status.config(text="Đang đọc checkpoint và loại bỏ optimizer...", fg="#e67e22")

        threading.Thread(target=self._worker, args=(in_path, out_path), daemon=True).start()

    def _worker(self, in_path, out_path):
        success, msg, orig_mb, new_mb = strip_model_checkpoint(in_path, out_path)
        self.root.after(0, lambda: self._on_finished(success, msg, orig_mb, new_mb, out_path))

    def _on_finished(self, success, msg, orig_mb, new_mb, out_path):
        self.btn_start.config(state="normal", text="BẮT ĐẦU STRIP OPTIMIZER ⚡")
        if success:
            saved_mb = max(0.0, orig_mb - new_mb)
            pct = (saved_mb / orig_mb * 100) if orig_mb > 0 else 0
            self.lbl_status.config(text=f"Hoàn thành! Giảm từ {orig_mb:.1f} MB xuống {new_mb:.1f} MB (-{pct:.1f}%)", fg="#27ae60")

            detail_msg = (
                f"Strip Optimizer thành công ✅!\n\n"
                f"• Dung lượng gốc: {orig_mb:.2f} MB\n"
                f"• Dung lượng mới: {new_mb:.2f} MB\n"
                f"• Tiết kiệm: {saved_mb:.2f} MB ({pct:.1f}%)\n\n"
                f"Tệp đã lưu tại:\n{out_path}\n\n"
                f"Model hiện đã nhẹ và sẵn sàng cho việc nhận diện / gán nhãn tự động!"
            )
            messagebox.showinfo("Thành công", detail_msg)
        else:
            self.lbl_status.config(text="Lỗi xử lý!", fg="#c0392b")
            messagebox.showerror("Thất bại", f"Không thể strip optimizer:\n{msg}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StripOptimizerApp(root)
    root.mainloop()
