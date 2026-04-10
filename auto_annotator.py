import os
import cv2
import glob
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ultralytics import YOLO

class AutoAnnotatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Auto-Annotation Tool")
        self.root.geometry("650x550")
        
        self.model_path = tk.StringVar()
        
        # Biến Tab 1
        self.video_paths = []
        self.video_display = tk.StringVar(value="Chưa chọn video")
        self.output_dir = tk.StringVar()
        
        # Biến Tab 2
        self.dataset_dir = tk.StringVar()
        self.class_mapping = tk.StringVar(value="0:0, 1:1, 2:2, 3:3, 5:5, 7:6")
        
        self.setup_ui()

    def setup_ui(self):
        # --- MODEL SELECTION (Chung cho 2 tính năng) ---
        frame_model = tk.LabelFrame(self.root, text="1. Chọn Model YOLO Pre-trained (.pt / .engine)", padx=10, pady=10)
        frame_model.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_model, textvariable=self.model_path, width=58, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_model, text="Browse", command=self.browse_model).pack(side="left")

        # --- NOTEBOOK (TABS) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # ====== TAB 1: TỪ VIDEO ======
        self.tab_video = tk.Frame(self.notebook)
        self.notebook.add(self.tab_video, text="Trích xuất từ Video")
        
        frame_video = tk.LabelFrame(self.tab_video, text="Chọn Video đầu vào (Có thể chọn nhiều)", padx=10, pady=10)
        frame_video.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_video, textvariable=self.video_display, width=58, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_video, text="Browse", command=self.browse_video).pack(side="left")

        frame_output = tk.LabelFrame(self.tab_video, text="Chọn Thư mục lưu kết quả ảnh & nhãn", padx=10, pady=10)
        frame_output.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_output, textvariable=self.output_dir, width=58, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_output, text="Browse", command=self.browse_output).pack(side="left")

        self.resize_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.tab_video, 
            text="Tương thích 640px: Tự động resize ảnh để tiết kiệm ổ cứng (Không lệch box)", 
            variable=self.resize_var, fg="#c0392b", font=("Arial", 9, "bold")
        ).pack(pady=2)

        self.save_background_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.tab_video,
            text="Lưu ảnh Background: Lưu cả frame không có đối tượng (để giảm False Positive khi train)",
            variable=self.save_background_var, fg="#2980b9", font=("Arial", 9, "bold")
        ).pack(pady=2)

        self.btn_start_video = tk.Button(self.tab_video, text="BẮT ĐẦU GÁN NHÃN", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.start_processing_video)
        self.btn_start_video.pack(pady=10)
        
        self.lbl_status_video = tk.Label(self.tab_video, text="Sẵn sàng...", fg="blue")
        self.lbl_status_video.pack()

        # ====== TAB 2: DATASET CÓ SẴN ======
        self.tab_dataset = tk.Frame(self.notebook)
        self.notebook.add(self.tab_dataset, text="Nâng cấp Dataset (Thêm nhãn)")

        frame_ds = tk.LabelFrame(self.tab_dataset, text="Chọn Thư mục Dataset (Chứa images/ và labels/)", padx=10, pady=10)
        frame_ds.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_ds, textvariable=self.dataset_dir, width=58, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_ds, text="Browse", command=self.browse_dataset).pack(side="left")

        frame_map = tk.LabelFrame(self.tab_dataset, text="Class Mapping (Chuyển đổi Class ID từ Pre-trained sang Dataset của bạn)", padx=10, pady=10)
        frame_map.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_map, text="Cú pháp: Bản_Gốc:Đích (Ví dụ COCO truck 7 -> biến thành 6 là 7:6)").pack(anchor="w", pady=(0,5))
        tk.Entry(frame_map, textvariable=self.class_mapping, width=65).pack(side="left", padx=5)

        tk.Label(self.tab_dataset, text="* Hành động này sẽ dò toàn bộ ảnh, nhận diện thêm vật thể, quy chuẩn sang ID do bạn map.\n* Sau đó nó LƯU NỐI TIẾP (Append) vào txt cũ, tuyệt đối không làm mất thẻ biển số hiện có.", justify="left", fg="gray", font=("Arial", 8)).pack(pady=5, padx=10, anchor="w")

        self.btn_start_dataset = tk.Button(self.tab_dataset, text="BẮT ĐẦU CẬP NHẬT DATASET", font=("Arial", 12, "bold"), bg="#e67e22", fg="white", command=self.start_processing_dataset)
        self.btn_start_dataset.pack(pady=10)
        
        self.lbl_status_dataset = tk.Label(self.tab_dataset, text="Sẵn sàng...", fg="blue")
        self.lbl_status_dataset.pack()

    # --- BROWSER METHODS ---
    def browse_model(self):
        path = filedialog.askopenfilename(filetypes=[("YOLO Model", "*.pt *.engine")])
        if path: self.model_path.set(path)

    def browse_video(self):
        paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov *.MOV")])
        if paths: 
            self.video_paths = list(paths)
            self.video_display.set(f"Đã chọn {len(self.video_paths)} video")

    def browse_output(self):
        path = filedialog.askdirectory()
        if path: self.output_dir.set(path)
        
    def browse_dataset(self):
        path = filedialog.askdirectory()
        if path: self.dataset_dir.set(path)

    # ========================================================
    # TAB 1: XỬ LÝ VIDEO
    # ========================================================
    def start_processing_video(self):
        if not self.model_path.get() or not self.video_paths or not self.output_dir.get():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ Model, Video và Thư mục lưu!")
            return

        self.btn_start_video.config(state="disabled", text="ĐANG XỬ LÝ...")
        threading.Thread(target=self.process_videos, daemon=True).start()

    def process_videos(self):
        try:
            self.update_status_video("Đang tải mô hình YOLO...")
            model = YOLO(self.model_path.get(), task="detect")
            
            output_base = self.output_dir.get()
            images_dir = os.path.join(output_base, "images")
            labels_dir = os.path.join(output_base, "labels")
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(labels_dir, exist_ok=True)
            
            input_size = 640  # cho engine
            total_saved_count = 0
            num_videos = len(self.video_paths)

            for idx, video_path in enumerate(self.video_paths):
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    print(f"Không thể mở video: {video_path}")
                    continue

                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                frames_to_skip = int(fps * 3) 
                
                frame_count = 0
                video_saved_count = 0

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_count % frames_to_skip == 0:
                        results = model(frame, imgsz=input_size, verbose=False)
                        has_objects = len(results[0].boxes) > 0

                        # Lưu nếu có đối tượng, hoặc bật tuỳ chọn lưu background
                        if has_objects or self.save_background_var.get():
                            base_filename = f"{video_name}_frame_{frame_count:06d}"
                            img_path = os.path.join(images_dir, f"{base_filename}.jpg")
                            txt_path = os.path.join(labels_dir, f"{base_filename}.txt")

                            if self.resize_var.get():
                                h, w = frame.shape[:2]
                                if max(w, h) > 640:
                                    scale = 640.0 / float(max(w, h))
                                    new_w, new_h = int(w * scale), int(h * scale)
                                    frame_to_save = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                                else:
                                    frame_to_save = frame
                                cv2.imwrite(img_path, frame_to_save)
                            else:
                                cv2.imwrite(img_path, frame)

                            if has_objects:
                                # Ghi file nhãn bình thường
                                with open(txt_path, 'w') as f:
                                    for box in results[0].boxes:
                                        cls_id = int(box.cls[0])
                                        x_center, y_center, width, height = box.xywhn[0]
                                        # Lọc box quá lớn (90% frame) trừ Bus(5) và Truck(6) 
                                        # nhằm loại bỏ các nhận diện nhầm bao phủ toàn cảnh.
                                        if (float(width) > 0.9 or float(height) > 0.9) and cls_id not in [5, 6]:
                                            continue
                                        f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                            else:
                                # Ảnh background: tạo file .txt rỗng (chuẩn YOLO)
                                open(txt_path, 'w').close()

                            video_saved_count += 1
                            total_saved_count += 1

                        progress_percent = int((frame_count / total_frames) * 100)
                        self.update_status_video(f"Video {idx+1}/{num_videos}: {video_name} | {progress_percent}% | Đã lưu: {video_saved_count}")

                    frame_count += 1

                cap.release()

            self.update_status_video(f"Hoàn thành! Đã lưu phần trích xuất {total_saved_count} ảnh.")
            messagebox.showinfo("Thành công", f"Xử lý xong {num_videos} video!\nTổng cộng {total_saved_count} ảnh đã được lưu.")

        except Exception as e:
            error_msg = str(e)
            self.update_status_video("Lỗi trong quá trình xử lý!")
            self.root.after(0, lambda: messagebox.showerror("Lỗi", error_msg))
        finally:
            self.root.after(0, lambda: self.btn_start_video.config(state="normal", text="BẮT ĐẦU GÁN NHÃN") if self.btn_start_video.winfo_exists() else None)

    def update_status_video(self, text):
        self.root.after(0, lambda: self.lbl_status_video.config(text=text))

    # ========================================================
    # TAB 2: XỬ LÝ DATASET CÓ SẴN (APPEND)
    # ========================================================
    def start_processing_dataset(self):
        if not self.model_path.get() or not self.dataset_dir.get() or not self.class_mapping.get().strip():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ Model, Thư mục Dataset và nhập Class Mapping!")
            return

        # Parse Class Mapping
        self.mapping_dict = {}
        try:
            parts = self.class_mapping.get().split(',')
            for part in parts:
                if ':' in part:
                    k, v = part.split(':')
                    self.mapping_dict[int(k.strip())] = int(v.strip())
        except Exception:
            messagebox.showerror("Lỗi Cú Pháp", "Class Mapping sai cú pháp! Hãy nhập theo chuẩn ví dụ: 0:0, 1:1, 7:6")
            return

        self.btn_start_dataset.config(state="disabled", text="ĐANG QUÉT DATASET...")
        threading.Thread(target=self.process_dataset, daemon=True).start()

    def process_dataset(self):
        try:
            self.update_status_dataset("Đang tải mô hình YOLO...")
            model = YOLO(self.model_path.get(), task="detect")
            
            ds_dir = self.dataset_dir.get()
            
            # Tìm đệ quy toàn bộ ảnh trong máy
            self.update_status_dataset("Đang quét ảnh trong dataset...")
            image_paths = []
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                image_paths.extend(glob.glob(os.path.join(ds_dir, "**", ext), recursive=True))

            if not image_paths:
                messagebox.showinfo("Trống", "Không tìm thấy file ảnh nào trong thư mục được chọn!")
                self.root.after(0, lambda: self.btn_start_dataset.config(state="normal", text="BẮT ĐẦU CẬP NHẬT DATASET"))
                return

            total_images = len(image_paths)
            total_added_boxes = 0

            for i, img_path in enumerate(image_paths):
                import pathlib
                p = pathlib.Path(img_path)
                parts = list(p.parts)
                idx = None
                for rev_idx in range(len(parts) - 1, -1, -1):
                    if parts[rev_idx].lower() == "images":
                        idx = rev_idx
                        break
                        
                if idx is not None:
                    parts[idx] = "labels"
                    label_path = str(pathlib.Path(*parts).with_suffix(".txt"))
                else:
                    # Chế độ cùng thư mục
                    label_path = os.path.splitext(img_path)[0] + ".txt"

                frame = cv2.imread(img_path)
                if frame is None:
                    continue

                results = model(frame, imgsz=640, verbose=False)
                
                boxes_to_append = []
                for box in results[0].boxes:
                    original_cls_id = int(box.cls[0])
                    if original_cls_id in self.mapping_dict:
                        new_cls_id = self.mapping_dict[original_cls_id]
                        x_center, y_center, width, height = box.xywhn[0]
                        # Lọc box quá lớn (90% frame) trừ Bus(5) và Truck(6) 
                        if (float(width) > 0.9 or float(height) > 0.9) and new_cls_id not in [5, 6]:
                            continue
                        boxes_to_append.append(f"{new_cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                
                if boxes_to_append:
                    os.makedirs(os.path.dirname(label_path), exist_ok=True)
                    # GHI NỐI TIẾP (a+)
                    with open(label_path, 'a') as f:
                        for line_box in boxes_to_append:
                            f.write(line_box)
                    total_added_boxes += len(boxes_to_append)

                if i % 10 == 0 or i == total_images - 1:
                    percent = int((i / total_images) * 100)
                    self.update_status_dataset(f"Tiến độ: {percent}% ({i}/{total_images}) | Đã gán thêm: {total_added_boxes} boxes")

            self.update_status_dataset(f"Hoàn thành! Đã cập nhật xong {total_images} ảnh.")
            messagebox.showinfo("Thành công", f"Quá trình Auto Annotate Dataset hoàn tất!\nĐã quét {total_images} ảnh.\nĐược bổ sung thêm {total_added_boxes} bounding box mới.")

        except Exception as e:
            error_msg = str(e)
            self.update_status_dataset("Lỗi trong quá trình xử lý!")
            self.root.after(0, lambda: messagebox.showerror("Lỗi", error_msg))
        finally:
            self.root.after(0, lambda: self.btn_start_dataset.config(state="normal", text="BẮT ĐẦU CẬP NHẬT DATASET") if self.btn_start_dataset.winfo_exists() else None)

    def update_status_dataset(self, text):
        self.root.after(0, lambda: self.lbl_status_dataset.config(text=text))

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoAnnotatorApp(root)
    root.mainloop()