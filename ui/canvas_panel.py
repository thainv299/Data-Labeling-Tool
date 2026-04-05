# ============================================================
# canvas_panel.py — Center panel: navigation buttons + canvas + drawing logic
# ============================================================
import tkinter as tk
from PIL import Image, ImageTk

from core.config import CLASSES, COLORS


class CanvasPanel(tk.Frame):
    """Center panel containing ◀ prev | Canvas | ▶ next and all drawing/bbox logic."""

    def __init__(self, parent, selected_class: tk.IntVar, on_prev=None, on_next=None):
        super().__init__(parent, bg="#2c3e50")

        self.selected_class = selected_class
        self._on_prev = on_prev
        self._on_next = on_next

        # Drawing state
        self.draft_rect = None
        self.draft_coords = None  # (x1, y1, x2, y2)
        self.start_x = 0
        self.start_y = 0

        # Image display properties
        self.img_w_disp = 1
        self.img_h_disp = 1
        self.photo = None

        # Current labels: list of (cls_id, xc, yc, w, h)
        self.current_labels: list[tuple] = []

        self._build()
        self._bind_mouse()

    # ----------------------------------------------------------
    # Build UI
    # ----------------------------------------------------------
    def _build(self):
        # Previous button
        self.btn_prev = tk.Button(
            self, text="◀", font=("Arial", 20, "bold"),
            command=self._on_prev, width=3,
            bg="#34495e", fg="white",
            activebackground="#2c3e50", activeforeground="white",
            relief=tk.FLAT,
        )
        self.btn_prev.pack(side=tk.LEFT, fill=tk.Y)

        # Canvas container (expand=True, NO fill → centers the canvas)
        canvas_container = tk.Frame(self, bg="#2c3e50")
        canvas_container.pack(side=tk.LEFT, expand=True)

        self.canvas = tk.Canvas(
            canvas_container, bg="black", cursor="cross", highlightthickness=0,
        )
        self.canvas.pack()

        # Next button
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

    # ----------------------------------------------------------
    # Image Display
    # ----------------------------------------------------------
    def display_image(self, pil_image: Image.Image):
        """Scale and display a PIL Image on the canvas. Returns (img_w_disp, img_h_disp)."""
        real_w, real_h = pil_image.size

        # Calculate available space (subtract approx button widths)
        self.update_idletasks()
        frame_w = self.winfo_width() - 100
        frame_h = self.winfo_height()
        if frame_w < 100:
            frame_w, frame_h = 800, 600  # Fallback

        scale = min(frame_w / real_w, frame_h / real_h)
        self.img_w_disp = int(real_w * scale)
        self.img_h_disp = int(real_h * scale)

        # Resize canvas to exactly match the scaled image
        self.canvas.config(width=self.img_w_disp, height=self.img_h_disp)

        img_resized = pil_image.resize(
            (self.img_w_disp, self.img_h_disp), Image.Resampling.LANCZOS,
        )
        self.photo = ImageTk.PhotoImage(img_resized)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Reset draft
        self.draft_rect = None
        self.draft_coords = None

    # ----------------------------------------------------------
    # Label Drawing
    # ----------------------------------------------------------
    def set_labels(self, labels: list[tuple]):
        """Set the current label list and redraw."""
        self.current_labels = list(labels)
        self.draw_all_labels()

    def get_labels(self) -> list[tuple]:
        """Return the current label list."""
        return list(self.current_labels)

    def draw_all_labels(self):
        """Redraw all confirmed bounding boxes on the canvas."""
        self.canvas.delete("label_box")

        for cls_id, xc, yc, w, h in self.current_labels:
            # Convert YOLO format (0.0-1.0) to canvas pixels
            px = xc * self.img_w_disp
            py = yc * self.img_h_disp
            bw = w * self.img_w_disp
            bh = h * self.img_h_disp

            x1, y1 = px - bw / 2, py - bh / 2
            x2, y2 = px + bw / 2, py + bh / 2

            color = COLORS[cls_id % len(COLORS)]
            self.canvas.create_rectangle(
                x1, y1, x2, y2, outline=color, width=2, tags="label_box",
            )
            self.canvas.create_text(
                x1, y1 - 5,
                text=CLASSES.get(cls_id, "Unknown"),
                fill=color, anchor=tk.SW,
                font=("Arial", 10, "bold"),
                tags="label_box",
            )

    # ----------------------------------------------------------
    # Mouse Events (Box Drawing)
    # ----------------------------------------------------------
    def _on_mouse_down(self, event):
        self.start_x = min(max(event.x, 0), self.img_w_disp)
        self.start_y = min(max(event.y, 0), self.img_h_disp)

    def _on_mouse_drag(self, event):
        cur_x = min(max(event.x, 0), self.img_w_disp)
        cur_y = min(max(event.y, 0), self.img_h_disp)

        if self.draft_rect:
            self.canvas.delete(self.draft_rect)

        color = COLORS[self.selected_class.get() % len(COLORS)]
        # Vẽ box tạm thời (nét đứt)
        self.draft_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, cur_x, cur_y,
            outline=color, width=2, dash=(4, 4),
        )
        self.draft_coords = (self.start_x, self.start_y, cur_x, cur_y)

    def _on_mouse_up(self, event):
        # Mouse thả ra, box vẫn ở dạng nháp chờ bấm Enter
        pass

    # ----------------------------------------------------------
    # Draft Confirmation & Undo
    # ----------------------------------------------------------
    def confirm_draft(self):
        """Confirm the draft rectangle as a new label (called on Enter)."""
        if self.draft_coords:
            x1, y1, x2, y2 = self.draft_coords

            # Tính toán tọa độ YOLO (0.0 - 1.0)
            xc = ((x1 + x2) / 2) / self.img_w_disp
            yc = ((y1 + y2) / 2) / self.img_h_disp
            w = abs(x2 - x1) / self.img_w_disp
            h = abs(y2 - y1) / self.img_h_disp

            if w > 0.01 and h > 0.01:  # Chống box quá nhỏ do click nhầm
                self.current_labels.append((self.selected_class.get(), xc, yc, w, h))

            self.canvas.delete(self.draft_rect)
            self.draft_rect = None
            self.draft_coords = None
            self.draw_all_labels()

    def undo_label(self):
        """Remove the last label (called on Ctrl+Z)."""
        if self.current_labels:
            self.current_labels.pop()
            self.draw_all_labels()
