# ============================================================
# app.py — Controller chính của ứng dụng
# ============================================================
import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image

from core.config import APP_TITLE, APP_GEOMETRY, CLASSES as DEFAULT_CLASSES
from core.data_manager import DataManager
from ui.toolbar import Toolbar
from ui.class_panel import ClassPanel
from ui.canvas_panel import CanvasPanel
from ui.status_bar import StatusBar
from auto_annotator import AutoAnnotatorApp
from scripts.split_dataset import DatasetSplitterApp
from scripts.resize_dataset import resize_images
from scripts.reindex_license_plates import change_label_id
from scripts.cleanup_dataset import cleanup_unmatched
from scripts.filter_large_boxes import filter_outlier_boxes
from scripts.batch_delete_class import BatchDeleteClassApp
from scripts.static_object_labeler import StaticObjectLabelerApp
from scripts.check_and_resize import check_and_resize_dataset


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
        self._setup_menu()
        self._setup_ui()
        self._bind_keys()

    # ----------------------------------------------------------
    # Menu Bar
    # ----------------------------------------------------------
    def _setup_menu(self):
        """Tạo thanh menu trên cùng chứa các công cụ tiện ích."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu "Công cụ"
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Công cụ", menu=tools_menu)

        tools_menu.add_command(label="Chia Dataset (Train/Valid/Test)", command=self.launch_split_dataset)
        tools_menu.add_command(label="Resize ảnh hàng loạt", command=self.launch_resize_images)
        tools_menu.add_command(label="Đổi Class ID hàng loạt", command=self.launch_reindex_labels)
        tools_menu.add_command(label="Đồng bộ Ảnh ↔ Nhãn (Cleanup)", command=self.launch_cleanup_dataset)
        tools_menu.add_command(label="Chia nhỏ Dataset thành N phần", command=self.launch_split_parts)
        tools_menu.add_separator()
        tools_menu.add_command(label="Xoá Class hàng loạt (theo dải ảnh)", command=self.launch_batch_delete_class)
        tools_menu.add_command(label="Lọc Box 'Nhầm' (Diện tích TB)", command=self.launch_filter_large_boxes)
        tools_menu.add_separator()
        tools_menu.add_command(label="Kiểm tra & Sửa kích thước ảnh (>640px)", command=check_and_resize_dataset)

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
            on_filter_boxes=self.filter_duplicate_boxes,
            on_clean_labels=self.clean_orphan_labels_action,
            on_copy_static=self.launch_static_object_labeler,
            on_filter_class=self.filter_by_class
        )
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Bảng chọn nhãn bên trái
        self.class_panel = ClassPanel(
            self.root, 
            selected_class=self.selected_class,
            on_visibility_change=self.on_visibility_change,
            on_select_all_class=self.on_select_all_class
        )
        self.class_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.class_panel.update_classes(DEFAULT_CLASSES)

        # Thanh trạng thái dưới cùng
        self.status_bar = StatusBar(
            self.root,
            text="Phím tắt: Enter (Chốt), Ctrl+Z (Hoàn tác), Left/Right (Chuyển ảnh), Ctrl+S (Lưu), Del (Xoá), Ctrl+Wheel (Zoom)",
            on_reset_zoom=self.reset_zoom
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
        self.root.bind("a", lambda e: self.prev_image())
        self.root.bind("d", lambda e: self.next_image())
        self.root.bind("<Return>", lambda e: self.canvas_panel.confirm_draft())
        self.root.bind("<Shift_L>", lambda e: self.canvas_panel.confirm_draft())
        self.root.bind("<Shift_R>", lambda e: self.canvas_panel.confirm_draft())
        self.root.bind("<Control-z>", lambda e: self.canvas_panel.undo_label())
        self.root.bind("<Control-s>", lambda e: self.save_labels())
        self.root.bind("<Control-b>", lambda e: self.launch_static_object_labeler())
        self.root.bind("<Control-r>", lambda e: self.toolbar.entry_rename.focus_set())
        self.root.bind("<Delete>", lambda e: self.delete_hotkey_handler())
        self.root.bind("<Escape>", lambda e: self.canvas_panel.deselect_label())
        self.root.bind("x", lambda e: self.canvas_panel.delete_selected_label())
        
        # Zoom binding
        self.root.bind("<Control-MouseWheel>", self.on_zoom_event)

    def on_zoom_event(self, event):
        """Xử lý sự kiện Ctrl + Wheel."""
        if event.delta > 0:
            factor = 1.2
        else:
            factor = 0.8
            
        self.canvas_panel.change_zoom(factor, event.x, event.y)
        self.status_bar.set_zoom(self.canvas_panel.zoom_level)

    def reset_zoom(self):
        """Đặt lại zoom về 100%."""
        self.canvas_panel.reset_zoom()
        self.status_bar.set_zoom(1.0)

    def delete_hotkey_handler(self):
        """Xử lý phím Delete: Ưu tiên xoá nhãn đang chọn, nếu không có thì xoá ảnh."""
        if self.canvas_panel.selected_label_indices:
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
        self.original_image_paths = image_paths # Lưu bản gốc
        self.image_paths = list(image_paths)    # Bản đang hiển thị
        self.current_idx = 0
        
        # Cập nhật danh sách gợi ý tìm kiếm
        basenames = [os.path.basename(p) for p in self.image_paths]
        self.toolbar.update_search_list(basenames)

        # Cập nhật danh sách lớp vào ô Lọc (Filter)
        class_names = []
        if hasattr(self, 'class_panel'):
            # Lấy tên các lớp từ bảng ClassPanel
            for cls_id, name in sorted(self.class_panel.classes.items()):
                class_names.append(f"{cls_id}: {name}")
        self.toolbar.update_filter_classes(class_names)
        
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

    def filter_by_class(self, event=None):
        """Lọc danh sách ảnh theo lớp được chọn (Xử lý đa luồng để tránh treo UI)."""
        selected_filter = self.toolbar.get_filter_class_value()
        
        if selected_filter == "Tất cả":
            self.image_paths = list(self.original_image_paths)
            self.current_idx = 0
            basenames = [os.path.basename(p) for p in self.image_paths]
            self.toolbar.update_search_list(basenames)
            self.load_image()
            return

        # Tách lấy Class ID
        try:
            cls_id = int(selected_filter.split(":")[0])
        except Exception:
            return

        # Hiển thị cửa sổ Progress
        from tkinter import ttk
        import threading

        progress_win = tk.Toplevel(self.root)
        progress_win.title("Đang lọc dữ liệu")
        progress_win.geometry("350x150")
        progress_win.transient(self.root)
        progress_win.grab_set()

        tk.Label(progress_win, text=f"Đang tìm ảnh chứa lớp: {selected_filter}", font=("Arial", 10)).pack(pady=10)
        
        progress = ttk.Progressbar(progress_win, length=280, mode='determinate')
        progress.pack(pady=5)
        progress["maximum"] = len(self.original_image_paths)
        
        lbl_count = tk.Label(progress_win, text="Đang quét: 0 / 0")
        lbl_count.pack()

        def run_filter():
            mode = self.mode_var.get()
            filtered_list = []
            total = len(self.original_image_paths)

            for i, img_path in enumerate(self.original_image_paths):
                # Cập nhật progress sau mỗi 50 ảnh để tránh spam UI thread
                if i % 50 == 0 or i == total - 1:
                    progress_win.after(0, lambda v=i+1: [progress.configure(value=v), lbl_count.configure(text=f"Đang quét: {v} / {total}")])

                txt_path = self.data_manager.get_label_path(img_path, mode)
                labels = self.data_manager.load_labels(txt_path)
                
                if any(label[0] == cls_id for label in labels):
                    filtered_list.append(img_path)

            # Hoàn tất
            def on_finish():
                progress_win.destroy()
                if not filtered_list:
                    messagebox.showinfo("Thông báo", f"Không tìm thấy ảnh nào chứa lớp '{selected_filter}'")
                    self.toolbar.combo_filter_class.set("Tất cả")
                    self.image_paths = list(self.original_image_paths)
                else:
                    self.image_paths = filtered_list
                
                self.current_idx = 0
                basenames = [os.path.basename(p) for p in self.image_paths]
                self.toolbar.update_search_list(basenames)
                self.load_image()

            progress_win.after(0, on_finish)

        # Chạy thread
        threading.Thread(target=run_filter, daemon=True).start()

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

        labels = self.canvas_panel.get_labels()
        if not labels:
            messagebox.showwarning("Không có nhãn", "Ảnh này chưa có đối tượng nào được nhận diện/gán nhãn. Không thể lưu tệp nhãn trống.")
            return

        img_path = self.image_paths[self.current_idx]
        mode = self.mode_var.get()
        txt_path = self.data_manager.get_label_path(img_path, mode)

        self.data_manager.save_labels(txt_path, labels)
        self.status_bar.set_text(f"Đã lưu nhãn: {os.path.basename(img_path)}")

    def on_visibility_change(self):
        """Khi checkbox ẩn/hiện class thay đổi, vẽ lại canvas."""
        self.canvas_panel.draw_all_labels()

    def on_select_all_class(self, cls_id):
        """Khi click nút [Chọn tất cả] trên Class panel."""
        self.selected_class.set(cls_id)
        self.canvas_panel.select_all_by_class(cls_id)

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
    # Lọc Bounding Box Trùng
    # ----------------------------------------------------------
    def filter_duplicate_boxes(self):
        """Lọc và xoá các bounding box trùng lặp (IoU > 0.9) trên toàn bộ dataset."""
        if not self.image_paths:
            messagebox.showinfo("Thông báo", "Vui lòng tải thư mục dữ liệu trước.")
            return
            
        if not messagebox.askyesno("Xác nhận", "Thao tác này sẽ quét toàn bộ ảnh và xoá các bounding box bị trùng lặp (IoU > 0.9).\nBạn có chắc chắn muốn tiếp tục?"):
            return
            
        def calculate_iou(b1, b2):
            _, xc1, yc1, w1, h1 = b1
            _, xc2, yc2, w2, h2 = b2
            xmin1, ymin1 = xc1 - w1/2, yc1 - h1/2
            xmax1, ymax1 = xc1 + w1/2, yc1 + h1/2
            xmin2, ymin2 = xc2 - w2/2, yc2 - h2/2
            xmax2, ymax2 = xc2 + w2/2, yc2 + h2/2
            
            ixmin = max(xmin1, xmin2)
            iymin = max(ymin1, ymin2)
            ixmax = min(xmax1, xmax2)
            iymax = min(ymax1, ymax2)
            
            iw = max(0, ixmax - ixmin)
            ih = max(0, iymax - iymin)
            
            if iw <= 0 or ih <= 0:
                return 0.0
                
            inter_area = iw * ih
            union_area = (w1 * h1) + (w2 * h2) - inter_area
            return inter_area / union_area if union_area > 0 else 0.0

        mode = self.mode_var.get()
        processed_images = 0
        removed_boxes = 0
        total_images = len(self.image_paths)

        # Hiện thanh tiến trình để UI không bị "Not Responding"
        from tkinter import ttk
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Đang xử lý")
        progress_win.geometry("350x120")
        progress_win.transient(self.root)
        progress_win.grab_set()

        tk.Label(progress_win, text="Đang lọc các bounding box trùng lặp...", font=("Arial", 10)).pack(pady=10)
        progress = ttk.Progressbar(progress_win, length=280, mode='determinate')
        progress.pack(pady=10)
        progress["maximum"] = total_images
        
        lbl_status = tk.Label(progress_win, text=f"0 / {total_images}", font=("Arial", 9))
        lbl_status.pack()

        progress_win.update()

        try:
            for i, img_path in enumerate(self.image_paths):
                txt_path = self.data_manager.get_label_path(img_path, mode)
                labels = self.data_manager.load_labels(txt_path)
                if labels:
                    # Ưu tiên nhãn nhỏ: Sắp xếp theo diện tích (w * h) tăng dần
                    labels.sort(key=lambda x: x[3] * x[4])
                    
                    new_labels = []
                    removed_in_this_file = False
                    
                    for current_box in labels:
                        is_duplicate = False
                        for kept_box in new_labels:
                            if calculate_iou(current_box, kept_box) > 0.45:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            new_labels.append(current_box)
                        else:
                            removed_in_this_file = True
                            removed_boxes += 1
                    
                    if removed_in_this_file:
                        if len(new_labels) == 0:
                            if os.path.exists(txt_path):
                                os.remove(txt_path)
                        else:
                            self.data_manager.save_labels(txt_path, new_labels)
                        processed_images += 1

                # Cập nhật thanh tiến trình (cập nhật UI sau mỗi 10 ảnh hoặc ở ảnh cuối cùng)
                if i % 10 == 0 or i == total_images - 1:
                    progress["value"] = i + 1
                    lbl_status.config(text=f"{i + 1} / {total_images}")
                    progress_win.update()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi trong quá trình quét:\n{str(e)}")
        finally:
            if progress_win.winfo_exists():
                progress_win.destroy()

        self.load_image()
        
        messagebox.showinfo(
            "Hoàn tất", 
            f"Đã dọn dẹp bộ dữ liệu.\n"
            f"- Số ảnh phát hiện trùng lặp: {processed_images}\n"
            f"- Tổng số bounding box đã bị xoá: {removed_boxes}"
        )

    # ----------------------------------------------------------
    # Dọn dẹp nhãn
    # ----------------------------------------------------------
    def clean_orphan_labels_action(self):
        """Xoá các file .txt không có ảnh đi kèm."""
        if not self.dataset_dir:
            messagebox.showinfo("Thông báo", "Vui lòng tải thư mục dữ liệu trước.")
            return
            
        if not messagebox.askyesno("Xác nhận", "Thao tác này sẽ quét toàn bộ thư mục và dọn dẹp:\n1. Các file nhãn (.txt) KHÔNG CÓ ảnh đi kèm.\n2. Các file ảnh (.jpg/.png) KHÔNG CÓ bất kỳ tệp nhãn nào đi kèm.\n\n(Ảnh background có file .txt rỗng sẽ được giữ lại).\n\nBạn có chắc chắn muốn thực hiện?"):
            return
            
        # UI Progress
        from tkinter import ttk
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Đang dọn dẹp")
        progress_win.geometry("350x120")
        progress_win.transient(self.root)
        progress_win.grab_set()

        tk.Label(progress_win, text="Đang quét và dọn dẹp dữ liệu...", font=("Arial", 10)).pack(pady=10)
        progress = ttk.Progressbar(progress_win, length=280, mode='indeterminate')
        progress.pack(pady=10)
        progress.start(10)
        progress_win.update()

        try:
            mode = self.mode_var.get()
            deleted_txt, deleted_img = self.data_manager.clean_orphan_labels(self.dataset_dir, mode)
            
            if progress_win.winfo_exists():
                progress_win.destroy()

            messagebox.showinfo(
                "Thành công", 
                f"Đã dọn dẹp xong bộ dữ liệu!\n"
                f"- Xoá {deleted_txt} file nhãn rác.\n"
                f"- Xoá {deleted_img} file ảnh không có nhãn.\n"
                f"Dataset hiện đã được đồng bộ 1-1."
            )
            self.load_dataset(self.dataset_dir) # Tải lại dataset hiện tại để cập nhật danh sách
        except Exception as e:
            if progress_win.winfo_exists():
                progress_win.destroy()
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

    # ----------------------------------------------------------
    # Điều hướng và Tự động Lưu
    # ----------------------------------------------------------
    def _auto_save_current_labels(self):
        """Tự động lưu nhãn của ảnh hiện tại trước khi chuyển sang ảnh khác."""
        if not self.image_paths:
            return

        labels = self.canvas_panel.get_labels()
        img_path = self.image_paths[self.current_idx]
        mode = self.mode_var.get()
        txt_path = self.data_manager.get_label_path(img_path, mode)

        if not labels:
            # Nếu không có nhãn (có thể do xóa hết), đảm bảo xóa file txt cũ nếu tồn tại
            if os.path.exists(txt_path):
                try:
                    os.remove(txt_path)
                except OSError:
                    pass
            return

        # Ghi đè file nếu có nhãn
        self.data_manager.save_labels(txt_path, labels)

    def prev_image(self):
        if self.current_idx > 0:
            self._auto_save_current_labels()
            self.current_idx -= 1
            self.load_image()

    def next_image(self):
        if self.current_idx < len(self.image_paths) - 1:
            self._auto_save_current_labels()
            self.current_idx += 1
            self.load_image()

    # ----------------------------------------------------------
    # Tích hợp Scripts tiện ích
    # ----------------------------------------------------------
    def launch_split_dataset(self):
        """Mở cửa sổ chia dataset Train/Valid/Test."""
        sub_root = tk.Toplevel(self.root)
        DatasetSplitterApp(sub_root)

    def launch_resize_images(self):
        """Mở hộp thoại chọn thư mục rồi resize ảnh hàng loạt."""
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh cần resize")
        if folder:
            resize_images(folder, max_size=640)

    def launch_reindex_labels(self):
        """Mở hộp thoại đổi Class ID hàng loạt."""
        folder = filedialog.askdirectory(title="Chọn thư mục Dataset chứa file nhãn (.txt)")
        if not folder:
            return
        old_id = simpledialog.askinteger("Class ID cũ", "Nhập Class ID cần đổi (VD: 0):", initialvalue=0)
        if old_id is None:
            return
        new_id = simpledialog.askinteger("Class ID mới", f"Đổi Class {old_id} thành ID mới (VD: 4):", initialvalue=4)
        if new_id is None:
            return
        change_label_id(folder, old_id=old_id, new_id=new_id)

    def launch_cleanup_dataset(self):
        """Mở hộp thoại so khớp và dọn dẹp file ảnh/nhãn không có cặp."""
        folder = filedialog.askdirectory(title="Chọn thư mục Dataset cần đồng bộ (quét đệ quy)")
        if folder:
            cleanup_unmatched(folder)

    def launch_split_parts(self):
        """Mở cửa sổ chia nhỏ Dataset thành N phần."""
        sub_root = tk.Toplevel(self.root)
        from scripts.split_parts import DatasetPartSplitterApp
        DatasetPartSplitterApp(sub_root, initial_dir=self.dataset_dir)

    def launch_static_object_labeler(self):
        """Mở hộp thoại sao chép box tĩnh cho dải ảnh."""
        if not self.image_paths:
            return
            
        box_data = self.canvas_panel.get_selected_label()
        if not box_data:
            messagebox.showwarning("Thông báo", "Vui lòng vẽ và CHỌN một khung nhãn (bounding box) trước khi sao chép!")
            return
            
        StaticObjectLabelerApp(
            self.root,
            box_data=box_data,
            current_idx=self.current_idx,
            image_paths=self.image_paths,
            data_manager=self.data_manager,
            mode=self.mode_var.get()
        )

    def launch_filter_large_boxes(self):
        """Mở hộp thoại lọc các box nhận diện nhầm (diện tích bất thường)."""
        if self.dataset_dir:
            filter_outlier_boxes(self.dataset_dir)
        else:
            folder = filedialog.askdirectory(title="Chọn thư mục Dataset để lọc box quá khổ")
            if folder:
                filter_outlier_boxes(folder)

    def launch_batch_delete_class(self):
        """Mở cửa sổ xoá class hàng loạt."""
        sub_root = tk.Toplevel(self.root)
        
        # Truyền thông tin hiện tại vào nếu có
        initial_folder = self.dataset_dir
        initial_class = self.selected_class.get()
        
        app = BatchDeleteClassApp(sub_root, initial_folder=initial_folder, initial_class=initial_class)
        
        # Nếu có dải ảnh hiện tại, tự động gán gợi ý
        if self.image_paths:
            app.start_idx.set(self.current_idx + 1)
            app.end_idx.set(len(self.image_paths))
            app.range_mode.set("range")
