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
        self.selected_label_idx = -1 # Lưu chỉ số nhãn đang chọn

        # Trạng thái vẽ (Draft)
        self.draft_rect = None
        self.draft_coords = None  # (x1, y1, x2, y2)
        self.start_x = 0
        self.start_y = 0

        # Thuộc tính hiển thị ảnh
        self.img_w_disp = 1
        self.img_h_disp = 1
        self.photo = None

        # Danh sách nhãn hiện tại: (cls_id, xc, yc, w, h)
        self.current_labels: list[tuple] = []

        self._build()
        self._bind_mouse()

    def set_class_panel(self, class_panel):
        """Kết nối với ClassPanel để lấy thông tin màu và ẩn hiện."""
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

        # Container chứa Canvas (expand=True để căn giữa)
        canvas_container = tk.Frame(self, bg="#2c3e50")
        canvas_container.pack(side=tk.LEFT, expand=True)

        self.canvas = tk.Canvas(
            canvas_container, bg="black", cursor="cross", highlightthickness=0,
            takefocus=1  # Cho phép Canvas nhận tiêu điểm từ bàn phím
        )
        self.canvas.pack()

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
        # Gắn sự kiện chuột trên Canvas
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    # ----------------------------------------------------------
    # Hiển thị hình ảnh
    # ----------------------------------------------------------
    def display_image(self, pil_image: Image.Image):
        """Tỷ lệ và hiển thị ảnh PIL lên canvas. Trả về kích thước thực hiển thị."""
        real_w, real_h = pil_image.size

        # Tính toán không gian trống có sẵn
        self.update_idletasks()
        frame_w = self.winfo_width() - 100
        frame_h = self.winfo_height()
        if frame_w < 100:
            frame_w, frame_h = 800, 600

        scale = min(frame_w / real_w, frame_h / real_h)
        self.img_w_disp = int(real_w * scale)
        self.img_h_disp = int(real_h * scale)

        # Cập nhật Canvas khớp với kích thước ảnh hiển thị
        self.canvas.config(width=self.img_w_disp, height=self.img_h_disp)

        img_resized = pil_image.resize(
            (self.img_w_disp, self.img_h_disp), Image.Resampling.LANCZOS,
        )
        self.photo = ImageTk.PhotoImage(img_resized)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Reset nháp vẽ
        self.draft_rect = None
        self.draft_coords = None
        self.selected_label_idx = -1

    # ----------------------------------------------------------
    # Quản lý nhãn
    # ----------------------------------------------------------
    def set_labels(self, labels: list[tuple]):
        """Gán danh sách nhãn hiện tại và vẽ lại."""
        self.current_labels = list(labels)
        self.selected_label_idx = -1
        self.draw_all_labels()

    def get_labels(self) -> list[tuple]:
        """Trả về danh sách các nhãn đang hiển thị."""
        return list(self.current_labels)

    def draw_all_labels(self):
        """Vẽ lại toàn bộ bounding box lên canvas."""
        self.canvas.delete("label_box")

        for i, (cls_id, xc, yc, w, h) in enumerate(self.current_labels):
            if self.class_panel and not self.class_panel.is_visible(cls_id):
                continue

            px, py = xc * self.img_w_disp, yc * self.img_h_disp
            bw, bh = w * self.img_w_disp, h * self.img_h_disp
            x1, y1, x2, y2 = px - bw/2, py - bh/2, px + bw/2, py + bh/2

            is_selected = (i == self.selected_label_idx)
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
        """Xoá nhãn đang được chọn."""
        if 0 <= self.selected_label_idx < len(self.current_labels):
            self.current_labels.pop(self.selected_label_idx)
            self.selected_label_idx = -1
            self.draw_all_labels()
            return True
        return False

    def deselect_label(self):
        """Bỏ chọn nhãn."""
        self.selected_label_idx = -1
        self.draw_all_labels()

    def update_selected_label_class(self, new_cls_id):
        """Cập nhật lớp cho nhãn đang chọn."""
        if 0 <= self.selected_label_idx < len(self.current_labels):
            cls_id, xc, yc, w, h = self.current_labels[self.selected_label_idx]
            self.current_labels[self.selected_label_idx] = (new_cls_id, xc, yc, w, h)
            self.draw_all_labels()

    # ----------------------------------------------------------
    # Sự kiện chuột (Vẽ Box & Chọn Box)
    # ----------------------------------------------------------
    def _on_mouse_down(self, event):
        self.canvas.focus_set()
        
        # Thử chọn nhãn hiện có
        clicked_idx = -1
        min_area = float('inf')
        for i, (cls_id, xc, yc, w, h) in enumerate(self.current_labels):
            if self.class_panel and not self.class_panel.is_visible(cls_id):
                continue
                
            px, py = xc * self.img_w_disp, yc * self.img_h_disp
            bw, bh = w * self.img_w_disp, h * self.img_h_disp
            x1, y1, x2, y2 = px - bw/2, py - bh/2, px + bw/2, py + bh/2
            
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                area = w * h
                if area < min_area:
                    min_area = area
                    clicked_idx = i
        
        if clicked_idx != -1:
            self.selected_label_idx = clicked_idx
            self.draw_all_labels()
            if self._on_label_selected:
                self._on_label_selected(self.current_labels[clicked_idx][0])
            self.start_x = -1 # Tạm ngưng vẽ nhãn mới khi vừa chọn
            return

        # Nếu không chọn được nhãn nào -> Bỏ chọn và bắt đầu vẽ mới
        self.selected_label_idx = -1
        self.draw_all_labels()
        self.start_x = min(max(event.x, 0), self.img_w_disp)
        self.start_y = min(max(event.y, 0), self.img_h_disp)

    def _on_mouse_drag(self, event):
        if self.start_x == -1: return

        cur_x = min(max(event.x, 0), self.img_w_disp)
        cur_y = min(max(event.y, 0), self.img_h_disp)

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
            self.selected_label_idx = -1
            self.draw_all_labels()
