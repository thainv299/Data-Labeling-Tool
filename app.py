# ============================================================
# app.py — Main application controller
# ============================================================
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

from core.config import APP_TITLE, APP_GEOMETRY
from core.data_manager import DataManager
from ui.toolbar import Toolbar
from ui.class_panel import ClassPanel
from ui.canvas_panel import CanvasPanel
from ui.status_bar import StatusBar


class YoloReviewerApp:
    """Application controller that wires all UI panels with the DataManager."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)

        # --- State ---
        self.dataset_dir = ""
        self.image_paths: list[str] = []
        self.current_idx = 0

        # --- Shared Tk variables ---
        self.mode_var = tk.StringVar(value="same_folder")
        self.selected_class = tk.IntVar(value=0)

        # --- Data layer ---
        self.data_manager = DataManager()

        # --- Build UI ---
        self._setup_ui()
        self._bind_keys()

    # ----------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------
    def _setup_ui(self):
        # Top toolbar
        self.toolbar = Toolbar(
            self.root,
            mode_var=self.mode_var,
            on_load_dataset=self.load_dataset,
            on_save_labels=self.save_labels,
        )
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Left class panel
        self.class_panel = ClassPanel(self.root, selected_class=self.selected_class)
        self.class_panel.pack(side=tk.LEFT, fill=tk.Y)

        # Bottom status bar (pack BEFORE center so it stays at the bottom)
        self.status_bar = StatusBar(
            self.root,
            text="Hướng dẫn: Kéo chuột để vẽ Box → Bấm Enter để chốt → Ctrl+Z để Undo → Left/Right để chuyển ảnh",
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Center canvas panel
        self.canvas_panel = CanvasPanel(
            self.root,
            selected_class=self.selected_class,
            on_prev=self.prev_image,
            on_next=self.next_image,
        )
        self.canvas_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _bind_keys(self):
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Return>", lambda e: self.canvas_panel.confirm_draft())
        self.root.bind("<Control-z>", lambda e: self.canvas_panel.undo_label())

    # ----------------------------------------------------------
    # Dataset Loading
    # ----------------------------------------------------------
    def load_dataset(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

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
        self.load_image()

    # ----------------------------------------------------------
    # Image & Label Loading
    # ----------------------------------------------------------
    def load_image(self):
        if not self.image_paths:
            return

        img_path = self.image_paths[self.current_idx]
        self.toolbar.set_info(
            f"Ảnh {self.current_idx + 1}/{len(self.image_paths)}: {os.path.basename(img_path)}"
        )

        # Open and display image
        pil_image = Image.open(img_path)
        self.canvas_panel.display_image(pil_image)

        # Load existing labels
        mode = self.mode_var.get()
        txt_path = self.data_manager.get_label_path(img_path, mode)
        labels = self.data_manager.load_labels(txt_path)
        self.canvas_panel.set_labels(labels)

    # ----------------------------------------------------------
    # Label Saving
    # ----------------------------------------------------------
    def save_labels(self):
        if not self.image_paths:
            return

        img_path = self.image_paths[self.current_idx]
        mode = self.mode_var.get()
        txt_path = self.data_manager.get_label_path(img_path, mode)

        labels = self.canvas_panel.get_labels()
        self.data_manager.save_labels(txt_path, labels)

        messagebox.showinfo("Đã lưu", f"Đã lưu nhãn cho ảnh: {os.path.basename(img_path)}")

    # ----------------------------------------------------------
    # Navigation
    # ----------------------------------------------------------
    def prev_image(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.load_image()

    def next_image(self):
        if self.current_idx < len(self.image_paths) - 1:
            self.current_idx += 1
            self.load_image()
