import os
import cv2
import glob
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ultralytics import YOLO

# Import Logic Modules from scripts
from scripts.video_annotator import process_batch_video_logic
from scripts.dataset_annotator import process_image_upgrade_logic, process_image_supplemental_logic, get_label_path_universal
from scripts.label_validator import validate_and_clean_labels

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
        # --- MODEL SELECTION ---
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
        tk.Checkbutton(self.tab_video, text="Tương thích 640px: Tự động resize ảnh", variable=self.resize_var, fg="#c0392b", font=("Arial", 9, "bold")).pack(pady=2)

        self.save_background_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.tab_video, text="Lưu ảnh Background (Không có đối tượng)", variable=self.save_background_var, fg="#2980b9", font=("Arial", 9, "bold")).pack(pady=2)

        self.btn_start_video = tk.Button(self.tab_video, text="BẮT ĐẦU GÁN NHÃN", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.start_processing_video)
        self.btn_start_video.pack(pady=10)
        self.lbl_status_video = tk.Label(self.tab_video, text="Sẵn sàng...", fg="blue")
        self.lbl_status_video.pack()

        # ====== TAB 2: NÂNG CẤP DATASET ======
        self.tab_dataset = tk.Frame(self.notebook)
        self.notebook.add(self.tab_dataset, text="Nâng cấp Dataset")

        frame_ds = tk.LabelFrame(self.tab_dataset, text="Chọn Thư mục Dataset", padx=10, pady=10)
        frame_ds.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_ds, textvariable=self.dataset_dir, width=58, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_ds, text="Browse", command=self.browse_dataset).pack(side="left")

        frame_map = tk.LabelFrame(self.tab_dataset, text="Class Mapping", padx=10, pady=10)
        frame_map.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_map, textvariable=self.class_mapping, width=65).pack(side="left", padx=5)

        self.btn_start_dataset = tk.Button(self.tab_dataset, text="BẮT ĐẦU CẬP NHẬT DATASET", font=("Arial", 12, "bold"), bg="#e67e22", fg="white", command=self.start_processing_dataset)
        self.btn_start_dataset.pack(pady=10)
        self.lbl_status_dataset = tk.Label(self.tab_dataset, text="Sẵn sàng...", fg="blue")
        self.lbl_status_dataset.pack()

        # ====== TAB 3: GÁN NHÃN BỔ SUNG ======
        self.tab_supp = tk.Frame(self.notebook)
        self.notebook.add(self.tab_supp, text="Gán nhãn bổ sung")

        frame_supp = tk.LabelFrame(self.tab_supp, text="Chọn Thư mục Dataset vẽ bù nhãn", padx=10, pady=10)
        frame_supp.pack(fill="x", padx=10, pady=5)
        self.supp_dir = tk.StringVar()
        tk.Entry(frame_supp, textvariable=self.supp_dir, width=58, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_supp, text="Browse", command=lambda: self.supp_dir.set(filedialog.askdirectory())).pack(side="left")

        self.class_mapping_supp = tk.Entry(self.tab_supp, width=50)
        self.class_mapping_supp.insert(0, "0:4")
        self.class_mapping_supp.pack(padx=10, pady=5)

        self.btn_start_supp = tk.Button(self.tab_supp, text="BẮT ĐẦU VẼ BÙ NHÃN", font=("Arial", 12, "bold"), bg="#3498db", fg="white", command=self.start_processing_supplemental)
        self.btn_start_supp.pack(pady=10)
        self.lbl_status_supp = tk.Label(self.tab_supp, text="Sẵn sàng...", fg="blue")
        self.lbl_status_supp.pack()

        # ====== TAB 4: AI VALIDATOR ======
        self.tab_val = tk.Frame(self.notebook)
        self.notebook.add(self.tab_val, text="AI Validator")

        frame_val = tk.LabelFrame(self.tab_val, text="Dọn dẹp nhãn sai", padx=10, pady=10)
        frame_val.pack(fill="x", padx=10, pady=5)
        self.val_dir = tk.StringVar()
        tk.Entry(frame_val, textvariable=self.val_dir, width=50, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_val, text="Browse", command=lambda: self.val_dir.set(filedialog.askdirectory())).pack(side="left")

        self.target_cls_val = tk.Entry(frame_val, width=10); self.target_cls_val.insert(0, "4"); self.target_cls_val.pack()
        self.conf_val = tk.Entry(frame_val, width=10); self.conf_val.insert(0, "0.25"); self.conf_val.pack()

        self.btn_start_val = tk.Button(self.tab_val, text="BẮT ĐẦU DỌN DẸP NHÃN SAI", font=("Arial", 12, "bold"), bg="#e74c3c", fg="white", command=self.start_processing_validator)
        self.btn_start_val.pack(pady=10)
        self.lbl_status_val = tk.Label(self.tab_val, text="Sẵn sàng...", fg="blue")
        self.lbl_status_val.pack()

    # --- BROWSER METHODS ---
    def browse_model(self):
        path = filedialog.askopenfilename(filetypes=[("YOLO Model", "*.pt *.engine")])
        if path: self.model_path.set(path)

    def browse_video(self):
        paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov")])
        if paths: self.video_paths = list(paths); self.video_display.set(f"Đã chọn {len(self.video_paths)} video")

    def browse_output(self):
        path = filedialog.askdirectory()
        if path: self.output_dir.set(path)
        
    def browse_dataset(self):
        path = filedialog.askdirectory()
        if path: self.dataset_dir.set(path)

    # --- PROCESSING METHODS ---
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
            images_dir = os.path.join(output_base, "images"); labels_dir = os.path.join(output_base, "labels")
            os.makedirs(images_dir, exist_ok=True); os.makedirs(labels_dir, exist_ok=True)
            
            total_saved_count = 0; num_videos = len(self.video_paths)
            for idx, video_path in enumerate(self.video_paths):
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS); total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                frames_to_skip = int(fps * 3); frame_count = 0; video_saved_count = 0
                batch_frames = []; batch_metas = []; batch_size = 4

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        if batch_frames: total_saved_count += process_batch_video_logic(model, batch_frames, batch_metas, images_dir, labels_dir)
                        break
                    if frame_count % frames_to_skip == 0:
                        batch_frames.append(frame.copy())
                        batch_metas.append({'frame_count': frame_count, 'video_name': video_name})
                    if len(batch_frames) >= batch_size:
                        saved = process_batch_video_logic(model, batch_frames, batch_metas, images_dir, labels_dir)
                        video_saved_count += saved; total_saved_count += saved
                        self.update_status_video(f"Video {idx+1}/{num_videos}: {video_name} | {int((frame_count/total_frames)*100)}% | Đã lưu: {video_saved_count}")
                        batch_frames = []; batch_metas = []
                    frame_count += 1
                cap.release()
            messagebox.showinfo("Thành công", f"Xử lý xong! Tổng cộng {total_saved_count} ảnh đã được lưu.")
        except Exception as e:
            self.update_status_video("Lỗi xử lý!"); messagebox.showerror("Lỗi", str(e))
        finally:
            self.root.after(0, lambda: self.btn_start_video.config(state="normal", text="BẮT ĐẦU GÁN NHÃN"))

    def start_processing_dataset(self):
        # Logic Tab 2
        mapping_dict = {}
        try:
            for part in self.class_mapping.get().split(','):
                if ':' in part: k, v = part.split(':'); mapping_dict[int(k.strip())] = int(v.strip())
        except: messagebox.showerror("Lỗi Cú Pháp", "Class Mapping sai!"); return

        self.btn_start_dataset.config(state="disabled", text="ĐANG QUÉT..."); threading.Thread(target=self.process_dataset, args=(mapping_dict,), daemon=True).start()

    def process_dataset(self, mapping):
        try:
            self.update_status_dataset("Đang tải mô hình..."); model = YOLO(self.model_path.get(), task="detect")
            ds_dir = self.dataset_dir.get(); image_paths = []
            for ext in ("*.jpg", "*.jpeg", "*.png"): image_paths.extend(glob.glob(os.path.join(ds_dir, "**", ext), recursive=True))
            
            total_added = 0; total_images = len(image_paths); batch_size = 4
            for i in range(0, total_images, batch_size):
                batch_paths = image_paths[i : i + batch_size]
                results = model.predict(source=batch_paths, imgsz=640, half=True, verbose=False)
                for j, result in enumerate(results):
                    if process_image_upgrade_logic(batch_paths[j], result, mapping, ds_dir): total_added += 1
                self.update_status_dataset(f"Tiến độ: {int((min(i+batch_size, total_images)/total_images)*100)}% | Đã thêm: {total_added}")
            messagebox.showinfo("Thành công", f"Đã nâng cấp xong {total_images} ảnh.")
        except Exception as e:
            self.update_status_dataset("Lỗi!"); messagebox.showerror("Lỗi", str(e))
        finally:
            self.root.after(0, lambda: self.btn_start_dataset.config(state="normal", text="BẮT ĐẦU CẬP NHẬT DATASET"))

    def start_processing_supplemental(self):
        # Logic Tab 3
        mapping_supp = {}
        try:
            for part in self.class_mapping_supp.get().split(','):
                if ':' in part: k, v = part.split(':'); mapping_supp[int(k.strip())] = int(v.strip())
        except: messagebox.showerror("Lỗi", "Mapping sai!"); return
        self.btn_start_supp.config(state="disabled", text="ĐANG XỬ LÝ..."); threading.Thread(target=self.process_supplemental, args=(mapping_supp,), daemon=True).start()

    def process_supplemental(self, mapping):
        try:
            self.update_status_supp("Đang tải mô hình..."); model = YOLO(self.model_path.get(), task="detect")
            ds_dir = self.supp_dir.get(); image_paths = []
            for ext in ("*.jpg", "*.jpeg", "*.png"): image_paths.extend(glob.glob(os.path.join(ds_dir, "**", ext), recursive=True))
            
            total_added = 0; total_images = len(image_paths); batch_size = 4
            for i in range(0, total_images, batch_size):
                batch_paths = image_paths[i : i + batch_size]
                results = model.predict(source=batch_paths, imgsz=640, half=True, verbose=False)
                for j, result in enumerate(results):
                    total_added += process_image_supplemental_logic(batch_paths[j], result, mapping, ds_dir)
                self.update_status_supp(f"Tiến độ: {int((min(i+batch_size, total_images)/total_images)*100)}% | Đã vẽ bù: {total_added}")
            messagebox.showinfo("Thành công", f"Đã vẽ bù thêm {total_added} nhãn mới.")
        except Exception as e:
            self.update_status_supp("Lỗi!"); messagebox.showerror("Lỗi", str(e))
        finally:
            self.root.after(0, lambda: self.btn_start_supp.config(state="normal", text="BẮT ĐẦU VẼ BÙ NHÃN"))

    def start_processing_validator(self):
        # Logic Tab 4
        try: target_cls = int(self.target_cls_val.get()); min_conf = float(self.conf_val.get())
        except: messagebox.showerror("Lỗi", "ID/Conf sai!"); return
        if not messagebox.askyesno("Xác nhận", "Xoá nhãn sai?"): return
        self.btn_start_val.config(state="disabled", text="ĐANG QUÉT..."); threading.Thread(target=self.process_validator, args=(target_cls, min_conf), daemon=True).start()

    def process_validator(self, target_cls, min_conf):
        try:
            self.update_status_val("Đang tải mô hình..."); model = YOLO(self.model_path.get(), task="detect")
            ds_dir = self.val_dir.get(); image_paths = []
            for ext in ("*.jpg", "*.jpeg", "*.png"): image_paths.extend(glob.glob(os.path.join(ds_dir, "**", ext), recursive=True))
            
            total = len(image_paths); cleaned_count = 0; removed_labels_count = 0
            for i, img_path in enumerate(image_paths):
                if i % 10 == 0 or i == total - 1: self.update_status_val(f"Quét: {i+1}/{total} | Đã xoá: {removed_labels_count}")
                results = model.predict(img_path, imgsz=640, conf=min_conf, verbose=False)
                txt_path = get_label_path_universal(img_path, ds_dir)
                removed = validate_and_clean_labels(txt_path, results[0].boxes if results else [], target_cls, min_conf)
                if removed > 0: removed_labels_count += removed; cleaned_count += 1
            messagebox.showinfo("Thành công", f"Xoá xong {removed_labels_count} nhãn sai trên {cleaned_count} ảnh.")
        except Exception as e:
            self.update_status_val("Lỗi!"); messagebox.showerror("Lỗi", str(e))
        finally:
            self.root.after(0, lambda: self.btn_start_val.config(state="normal", text="BẮT ĐẦU DỌN DẸP NHÃN SAI"))

    # --- STATUS UPDATES ---
    def update_status_dataset(self, text): 
        if self.lbl_status_dataset.winfo_exists(): self.root.after(0, lambda: self.lbl_status_dataset.config(text=text))
    def update_status_video(self, text): 
        if self.lbl_status_video.winfo_exists(): self.root.after(0, lambda: self.lbl_status_video.config(text=text))
    def update_status_supp(self, text): 
        if self.lbl_status_supp.winfo_exists(): self.root.after(0, lambda: self.lbl_status_supp.config(text=text))
    def update_status_val(self, text): 
        if self.lbl_status_val.winfo_exists(): self.root.after(0, lambda: self.lbl_status_val.config(text=text))

if __name__ == "__main__":
    root = tk.Tk(); app = AutoAnnotatorApp(root); root.mainloop()