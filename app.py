# ============================================================
# app.py — Controller chính của ứng dụng
# ============================================================
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

from core.config import APP_TITLE, APP_GEOMETRY, CLASSES as DEFAULT_CLASSES
from core.data_manager import DataManager
from ui.toolbar import Toolbar
from ui.class_panel import ClassPanel
from ui.canvas_panel import CanvasPanel
from ui.status_bar import StatusBar
from auto_annotator import AutoAnnotatorApp


class YoloReviewerApp:
    """Điều phối toàn bộ ứng dụng, kết nối các Panel giao diện với DataManager."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)

        # --- Trạng thái ---
        self.dataset_dir = ""
        self.image_paths: list[str] = []
        self.current_idx = 0

        # --- Biến chung Tk ---
        self.mode_var = tk.StringVar(value="same_folder")
        self.rename_var = tk.StringVar()
        self.selected_class = tk.IntVar(value=0)

        # --- Lớp dữ liệu ---
        self.data_manager = DataManager()

        # --- Khởi tạo giao diện ---
        self._setup_ui()
        self._bind_keys()

    # ----------------------------------------------------------
    # Khởi tạo giao diện
    # ----------------------------------------------------------
    def _setup_ui(self):
        # Thanh công cụ trên cùng
        self.toolbar = Toolbar(
            self.root,
            mode_var=self.mode_var,
            rename_var=self.rename_var,
            on_load_dataset=self.load_dataset,
            on_save_labels=self.save_labels,
            on_search=self.on_search_selected,
            on_rename=self.rename_current_item,
            on_delete=self.delete_current_item,
            on_auto_annotate=self.launch_auto_annotator,
        )
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Bảng chọn nhãn bên trái
        self.class_panel = ClassPanel(
            self.root, 
            selected_class=self.selected_class,
            on_visibility_change=self.on_visibility_change
        )
        self.class_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.class_panel.update_classes(DEFAULT_CLASSES)

        # Thanh trạng thái dưới cùng
        self.status_bar = StatusBar(
            self.root,
            text="Phím tắt: Enter (Chốt), Ctrl+Z (Hoàn tác), Left/Right (Chuyển ảnh), Ctrl+S (Lưu), Del (Xoá)",
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bảng hiển thị ảnh trung tâm
        self.canvas_panel = CanvasPanel(
            self.root,
            selected_class=self.selected_class,
            on_prev=self.prev_image,
            on_next=self.next_image,
            on_label_selected=self.on_label_selected
        )
        self.canvas_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_panel.set_class_panel(self.class_panel)

        # Lắng nghe thay đổi lớp để cập nhật nhãn đang chọn
        self.selected_class.trace_add("write", self.on_class_radio_changed)

    def _bind_keys(self):
        # Gắn phím tắt hệ thống
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Return>", lambda e: self.canvas_panel.confirm_draft())
        self.root.bind("<Control-z>", lambda e: self.canvas_panel.undo_label())
        self.root.bind("<Control-s>", lambda e: self.save_labels())
        self.root.bind("<Control-r>", lambda e: self.toolbar.entry_rename.focus_set())
        self.root.bind("<Delete>", lambda e: self.delete_hotkey_handler())
        self.root.bind("<Escape>", lambda e: self.canvas_panel.deselect_label())
        self.root.bind("x", lambda e: self.canvas_panel.delete_selected_label())

    def delete_hotkey_handler(self):
        """Xử lý phím Delete: Ưu tiên xoá nhãn đang chọn, nếu không có thì xoá ảnh."""
        if self.canvas_panel.selected_label_idx != -1:
            self.canvas_panel.delete_selected_label()
        else:
            self.delete_current_item()

    # ----------------------------------------------------------
    # Tải tập dữ liệu
    # ----------------------------------------------------------
    def load_dataset(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        # Tự động tìm file YAML
        config = self.data_manager.load_dataset_config(folder)
        if config:
            self.mode_var.set("yolo_dataset")
            self.class_panel.update_classes(config)
            self.status_bar.set_text(f"Đã tải cấu hình từ file YAML. Chế độ: Review YOLO Dataset")
        else:
            self.class_panel.update_classes(DEFAULT_CLASSES)

        mode = self.mode_var.get()

        try:
            image_paths = self.data_manager.scan_folder(folder, mode)
        except FileNotFoundError as e:
            messagebox.showwarning("Thiếu thư mục", str(e))
            return

        if not image_paths:
            messagebox.showwarning("Trống", "Không tìm thấy ảnh (.jpg/.png) trong thư mục này!")
            return

        self.dataset_dir = folder
        self.image_paths = image_paths
        self.current_idx = 0
        
        # Cập nhật danh sách gợi ý tìm kiếm
        basenames = [os.path.basename(p) for p in self.image_paths]
        self.toolbar.update_search_list(basenames)
        
        self.load_image()

    # ----------------------------------------------------------
    # Tải hình ảnh và nhãn
    # ----------------------------------------------------------
    def load_image(self):
        if not self.image_paths:
            return

        img_path = self.image_paths[self.current_idx]
        file_name = os.path.basename(img_path)
        
        # Cập nhật thanh công cụ
        self.toolbar.set_info(f"Ảnh {self.current_idx + 1}/{len(self.image_paths)}: {file_name}")
        self.toolbar.set_search_value(file_name)
        
        # Cập nhật ô đổi tên (không lấy phần mở rộng)
        base, _ = os.path.splitext(file_name)
        self.rename_var.set(base)

        try:
            # Mở và hiển thị hình ảnh
            pil_image = Image.open(img_path)
            self.canvas_panel.display_image(pil_image)

            # Tải các nhãn hiện có
            mode = self.mode_var.get()
            txt_path = self.data_manager.get_label_path(img_path, mode)
            labels = self.data_manager.load_labels(txt_path)
            self.canvas_panel.set_labels(labels)
            
        except OSError as e:
            messagebox.showerror("Lỗi ảnh", f"Không thể tải ảnh: {file_name}\nẢnh có thể bị hỏng (Truncated).\nError: {str(e)}")
            return

    # ----------------------------------------------------------
    # Chức năng tìm kiếm và Nhảy đến ảnh
    # ----------------------------------------------------------
    def on_search_selected(self, event=None):
        """Xử lý khi người dùng chọn tên ảnh trong ô tìm kiếm."""
        target_name = self.toolbar.get_search_value()
        if not target_name:
            return
            
        # Tìm chỉ số ảnh có tên khớp (tìm chính xác hoặc gợi ý)
        for idx, path in enumerate(self.image_paths):
            if os.path.basename(path) == target_name:
                self.current_idx = idx
                self.load_image()
                return
        
        # Nếu không tìm thấy chính xác, báo lỗi nhẹ
        self.status_bar.set_text(f"Không tìm thấy ảnh: {target_name}")

    # ----------------------------------------------------------
    # Đổi tên & Xoá
    # ----------------------------------------------------------
    def rename_current_item(self):
        """Thực hiện đổi tên ảnh và nhãn hiện tại."""
        if not self.image_paths:
            return

        old_path = self.image_paths[self.current_idx]
        new_name = self.rename_var.get().strip()
        mode = self.mode_var.get()

        if not new_name:
            return

        try:
            new_path = self.data_manager.rename_dataset_item(old_path, new_name, mode)
            if new_path == old_path:
                return

            self.image_paths[self.current_idx] = new_path
            basenames = [os.path.basename(p) for p in self.image_paths]
            self.toolbar.update_search_list(basenames)
            self.load_image()
            self.status_bar.set_text(f"Đã đổi tên thành: {os.path.basename(new_path)}")
            
        except Exception as e:
            messagebox.showerror("Lỗi đổi tên", str(e))

    def delete_current_item(self):
        """Xoá vĩnh viễn ảnh và nhãn hiện tại."""
        if not self.image_paths:
            return

        img_path = self.image_paths[self.current_idx]
        file_name = os.path.basename(img_path)

        if not messagebox.askyesno("Xác nhận xoá", f"Bạn có chắc muốn xoá vĩnh viễn file:\n{file_name}?\n(Sẽ xoá cả file nhãn .txt tương ứng)"):
            return

        mode = self.mode_var.get()
        if self.data_manager.delete_dataset_item(img_path, mode):
            # Xoá khỏi danh sách bộ nhớ
            self.image_paths.pop(self.current_idx)
            
            # Điều chỉnh index
            if self.current_idx >= len(self.image_paths):
                self.current_idx = max(0, len(self.image_paths) - 1)
            
            if self.image_paths:
                self.load_image()
            else:
                self.toolbar.set_info("Dữ liệu trống")
                self.canvas_panel.canvas.delete("all")
            
            self.status_bar.set_text(f"Đã xoá: {file_name}")
        else:
            messagebox.showerror("Lỗi", "Không thể xoá file. Vui lòng kiểm tra quyền truy cập.")

    # ----------------------------------------------------------
    # Lưu nhãn & Đồng bộ hiển thị
    # ----------------------------------------------------------
    def save_labels(self):
        if not self.image_paths:
            return

        img_path = self.image_paths[self.current_idx]
        mode = self.mode_var.get()
        txt_path = self.data_manager.get_label_path(img_path, mode)

        labels = self.canvas_panel.get_labels()
        self.data_manager.save_labels(txt_path, labels)
        self.status_bar.set_text(f"Đã lưu nhãn: {os.path.basename(img_path)}")

    def on_visibility_change(self):
        """Khi checkbox ẩn/hiện class thay đổi, vẽ lại canvas."""
        self.canvas_panel.draw_all_labels()

    def on_label_selected(self, cls_id):
        """Khi một nhãn được chọn trên Canvas, cập nhật radio button tương ứng."""
        self.selected_class.set(cls_id)

    def on_class_radio_changed(self, *args):
        """Khi người dùng chọn một lớp mới ở bảng bên trái."""
        new_cls_id = self.selected_class.get()
        # Nếu đang có nhãn được chọn trên canvas, cập nhật nó sang lớp mới
        self.canvas_panel.update_selected_label_class(new_cls_id)

    # ----------------------------------------------------------
    # Tích hợp Auto Annotator
    # ----------------------------------------------------------
    def launch_auto_annotator(self):
        """Mở cửa sổ tự động gán nhãn."""
        sub_root = tk.Toplevel(self.root)
        AutoAnnotatorApp(sub_root)

    # ----------------------------------------------------------
    # Điều hướng
    # ----------------------------------------------------------
    def prev_image(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.load_image()

    def next_image(self):
        if self.current_idx < len(self.image_paths) - 1:
            self.current_idx += 1
            self.load_image()
