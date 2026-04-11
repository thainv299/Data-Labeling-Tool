# ============================================================
# canvas_panel.py — Bảng trung tâm: nút điều hướng + Canvas + vẽ
# ============================================================
import tkinter as tk
from PIL import Image, ImageTk

from core.config import CLASSES, COLORS


class CanvasPanel(tk.Frame):
    """Bảng trung tâm chứa ◀ prev | Canvas | ▶ next và toàn bộ logic vẽ khung nhãn."""

    def __init__(self, parent, selected_class: tk.IntVar, on_prev=None, on_next=None, on_label_selected=None):
        super().__init__(parent, bg="#2c3e50")

        self.selected_class = selected_class
        self._on_prev = on_prev
        self._on_next = on_next
        self._on_label_selected = on_label_selected
        self.class_panel = None # Sẽ được gán từ app.py
        
        # Trạng thái hiển thị & Zoom
        self.zoom_level = 1.0 # 1.0 = 100% (Fit)
        self.base_w = 1
        self.base_h = 1
        self.original_image = None # PIL Image gốc để resize chất lượng cao
        self.photo = None

        # Trạng thái vẽ (Draft)
        self.selected_label_indices = set()
        self.draft_rect = None
        self.draft_coords = None  # (x1, y1, x2, y2)
        self.start_x = 0
        self.start_y = 0

        # Danh sách nhãn hiện tại: (cls_id, xc, yc, w, h)
        self.current_labels: list[tuple] = []

        self._build()
        self._bind_mouse()

    def set_class_panel(self, class_panel):
        self.class_panel = class_panel

    # ----------------------------------------------------------
    # Khởi tạo giao diện
    # ----------------------------------------------------------
    def _build(self):
        # Nút Ảnh Trước
        self.btn_prev = tk.Button(
            self, text="◀", font=("Arial", 20, "bold"),
            command=self._on_prev, width=3,
            bg="#34495e", fg="white",
            activebackground="#2c3e50", activeforeground="white",
            relief=tk.FLAT,
        )
        self.btn_prev.pack(side=tk.LEFT, fill=tk.Y)

        # Container chứa Canvas và Scrollbars
        canvas_container = tk.Frame(self, bg="#2c3e50")
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll = tk.Scrollbar(canvas_container, orient="vertical")
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scroll = tk.Scrollbar(canvas_container, orient="horizontal")
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(
            canvas_container, bg="black", cursor="cross", highlightthickness=0,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
            takefocus=1
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Nút Ảnh Sau
        self.btn_next = tk.Button(
            self, text="▶", font=("Arial", 20, "bold"),
            command=self._on_next, width=3,
            bg="#34495e", fg="white",
            activebackground="#2c3e50", activeforeground="white",
            relief=tk.FLAT,
        )
        self.btn_next.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_mouse(self):
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        # Panning (Chuột giữa)
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_drag)
        
        # Zoom (Ctrl + Wheel) - Gắn ở App.py thực chất tốt hơn để bắt toàn cục,
        # nhưng bind ở canvas cũng được nếu nó có focus.

    # ----------------------------------------------------------
    # Hiển thị hình ảnh & Zoom
    # ----------------------------------------------------------
    def display_image(self, pil_image: Image.Image, reset_zoom=True):
        """Hiển thị ảnh và tính toán tỷ lệ Fit ban đầu."""
        if pil_image:
            self.original_image = pil_image
            
        if not self.original_image:
            return

        real_w, real_h = self.original_image.size

        if reset_zoom:
            self.zoom_level = 1.0
            self.update_idletasks()
            frame_w = self.canvas.winfo_width()
            frame_h = self.canvas.winfo_height()
            if frame_w < 100: frame_w, frame_h = 800, 600

            scale = min(frame_w / real_w, frame_h / real_h)
            self.base_w = int(real_w * scale)
            self.base_h = int(real_h * scale)

        # Tính toán kích thước hiển thị hiện tại
        self.img_w_disp = int(self.base_w * self.zoom_level)
        self.img_h_disp = int(self.base_h * self.zoom_level)

        # Resize ảnh
        img_resized = self.original_image.resize(
            (self.img_w_disp, self.img_h_disp), Image.Resampling.LANCZOS,
        )
        self.photo = ImageTk.PhotoImage(img_resized)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags="image")
        self.canvas.config(scrollregion=(0, 0, self.img_w_disp, self.img_h_disp))

        # Vẽ lại nhãn
        self.draw_all_labels()
        
        # Reset draft
        self.draft_rect = None
        self.draft_coords = None

    def change_zoom(self, delta_factor, center_x=None, center_y=None):
        """Thay đổi mức phóng to."""
        old_zoom = self.zoom_level
        self.zoom_level *= delta_factor
        
        # Giới hạn zoom 10% - 1000%
        self.zoom_level = min(max(self.zoom_level, 0.1), 10.0)
        
        if self.zoom_level == old_zoom:
            return

        # Lưu lại toạ độ trung tâm (canvas coordinates) để giữ vị trí nhìn
        if center_x is None:
            center_x = self.canvas.winfo_width() / 2
        if center_y is None:
            center_y = self.canvas.winfo_height() / 2
            
        canvas_x = self.canvas.canvasx(center_x)
        canvas_y = self.canvas.canvasy(center_y)

        self.display_image(None, reset_zoom=False)
        
        # Điều chỉnh view của canvas để tập trung vào điểm cũ
        new_canvas_x = canvas_x * (self.zoom_level / old_zoom)
        new_canvas_y = canvas_y * (self.zoom_level / old_zoom)
        
        self.canvas.xview_moveto((new_canvas_x - center_x) / self.img_w_disp)
        self.canvas.yview_moveto((new_canvas_y - center_y) / self.img_h_disp)

    def reset_zoom(self):
        self.display_image(None, reset_zoom=True)

    # ----------------------------------------------------------
    # Panning (Kéo ảnh)
    # ----------------------------------------------------------
    def _on_pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _on_pan_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    # ----------------------------------------------------------
    # Quản lý nhãn
    # ----------------------------------------------------------
    def set_labels(self, labels: list[tuple]):
        self.current_labels = list(labels)
        self.selected_label_indices.clear()
        self.draw_all_labels()

    def get_labels(self) -> list[tuple]:
        return list(self.current_labels)

    def draw_all_labels(self):
        self.canvas.delete("label_box")

        for i, (cls_id, xc, yc, w, h) in enumerate(self.current_labels):
            if self.class_panel and not self.class_panel.is_visible(cls_id):
                continue

            px, py = xc * self.img_w_disp, yc * self.img_h_disp
            bw, bh = w * self.img_w_disp, h * self.img_h_disp
            x1, y1, x2, y2 = px - bw/2, py - bh/2, px + bw/2, py + bh/2

            is_selected = (i in self.selected_label_indices)
            color = self.class_panel.get_color(cls_id) if self.class_panel else "#FF0000"
            class_name = self.class_panel.classes.get(cls_id, "Unknown") if self.class_panel else f"ID: {cls_id}"

            border_width = 4 if is_selected else 2
            
            self.canvas.create_rectangle(
                x1, y1, x2, y2, outline=color, width=border_width, tags="label_box",
            )
            self.canvas.create_text(
                x1, y1 - 5,
                text=class_name,
                fill=color, anchor=tk.SW,
                font=("Arial", 10, "bold"),
                tags="label_box",
            )

    def delete_selected_label(self):
        if self.selected_label_indices:
            # Xoá ngược danh sách để index không bị sai lệch
            for idx in sorted(self.selected_label_indices, reverse=True):
                self.current_labels.pop(idx)
            self.selected_label_indices.clear()
            self.draw_all_labels()
            return True
        return False

    def deselect_label(self):
        self.selected_label_indices.clear()
        self.draw_all_labels()

    def update_selected_label_class(self, new_cls_id):
        if self.selected_label_indices:
            for idx in self.selected_label_indices:
                cls_id, xc, yc, w, h = self.current_labels[idx]
                self.current_labels[idx] = (new_cls_id, xc, yc, w, h)
            self.draw_all_labels()

    def select_all_by_class(self, cls_id):
        """Chọn tất cả nhãn thuộc về 1 class_id cụ thể."""
        self.selected_label_indices = {i for i, label in enumerate(self.current_labels) if label[0] == cls_id}
        self.draw_all_labels()

    def get_selected_label(self) -> tuple:
        """Trả về nhãn đầu tiên đang được chọn (cls_id, xc, yc, w, h)."""
        if self.selected_label_indices:
            idx = next(iter(self.selected_label_indices))
            return self.current_labels[idx]
        return None

    # ----------------------------------------------------------
    # Sự kiện chuột
    # ----------------------------------------------------------
    def _on_mouse_down(self, event):
        self.canvas.focus_set()
        
        # Toạ độ thực tế trên Canvas (đã tính scroll)
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        
        # Thử chọn nhãn hiện có
        clicked_idx = -1
        min_area = float('inf')
        for i, (cls_id, xc, yc, w, h) in enumerate(self.current_labels):
            if self.class_panel and not self.class_panel.is_visible(cls_id):
                continue
                
            px, py = xc * self.img_w_disp, yc * self.img_h_disp
            bw, bh = w * self.img_w_disp, h * self.img_h_disp
            x1, y1, x2, y2 = px - bw/2, py - bh/2, px + bw/2, py + bh/2
            
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                area = w * h
                if area < min_area:
                    min_area = area
                    clicked_idx = i
        
        if clicked_idx != -1:
            self.selected_label_indices = {clicked_idx}
            self.draw_all_labels()
            if self._on_label_selected:
                self._on_label_selected(self.current_labels[clicked_idx][0])
            self.start_x = -1
            return

        self.selected_label_indices.clear()
        self.draw_all_labels()
        self.start_x = min(max(cx, 0), self.img_w_disp)
        self.start_y = min(max(cy, 0), self.img_h_disp)

    def _on_mouse_drag(self, event):
        if self.start_x == -1: return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        cur_x = min(max(cx, 0), self.img_w_disp)
        cur_y = min(max(cy, 0), self.img_h_disp)

        if self.draft_rect:
            self.canvas.delete(self.draft_rect)

        cls_id = self.selected_class.get()
        color = self.class_panel.get_color(cls_id) if self.class_panel else "#FF0000"
        
        self.draft_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, cur_x, cur_y,
            outline=color, width=2, dash=(4, 4),
        )
        self.draft_coords = (self.start_x, self.start_y, cur_x, cur_y)

    def _on_mouse_up(self, event):
        pass

    def confirm_draft(self):
        if self.draft_coords:
            x1, y1, x2, y2 = self.draft_coords
            xc = ((x1 + x2) / 2) / self.img_w_disp
            yc = ((y1 + y2) / 2) / self.img_h_disp
            w = abs(x2 - x1) / self.img_w_disp
            h = abs(y2 - y1) / self.img_h_disp

            if w > 0.005 and h > 0.005:
                self.current_labels.append((self.selected_class.get(), xc, yc, w, h))

            self.canvas.delete(self.draft_rect)
            self.draft_rect = None
            self.draft_coords = None
            self.draw_all_labels()

    def undo_label(self):
        if self.current_labels:
            self.current_labels.pop()
            self.selected_label_indices.clear()
            self.draw_all_labels()
