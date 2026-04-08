import os
import cv2
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ultralytics import YOLO

class AutoAnnotatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Auto-Annotation Tool")
        self.root.geometry("550x350")
        
        self.video_paths = []
        self.video_display = tk.StringVar(value="Chưa chọn video")
        self.model_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        self.setup_ui()

    def setup_ui(self):
        frame_model = tk.LabelFrame(self.root, text="1. Chọn Model YOLO (.pt)", padx=10, pady=10)
        frame_model.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_model, textvariable=self.model_path, width=50, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_model, text="Browse", command=self.browse_model).pack(side="left")

        frame_video = tk.LabelFrame(self.root, text="2. Chọn Video đầu vào (Có thể chọn nhiều)", padx=10, pady=10)
        frame_video.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_video, textvariable=self.video_display, width=50, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_video, text="Browse", command=self.browse_video).pack(side="left")

        frame_output = tk.LabelFrame(self.root, text="3. Chọn Thư mục lưu kết quả", padx=10, pady=10)
        frame_output.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_output, textvariable=self.output_dir, width=50, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_output, text="Browse", command=self.browse_output).pack(side="left")

        self.btn_start = tk.Button(self.root, text="BẮT ĐẦU GÁN NHÃN", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.start_processing)
        self.btn_start.pack(pady=15)
        
        self.lbl_status = tk.Label(self.root, text="Sẵn sàng...", fg="blue")
        self.lbl_status.pack()

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

    def start_processing(self):
        if not self.model_path.get() or not self.video_paths or not self.output_dir.get():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ Model, Video và Thư mục lưu!")
            return

        self.btn_start.config(state="disabled", text="ĐANG XỬ LÝ...")
        threading.Thread(target=self.process_videos, daemon=True).start()

    def process_videos(self):
        try:
            self.update_status("Đang tải mô hình YOLO...")
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
                        frame_resized = cv2.resize(frame, (input_size, input_size))
                        results = model(frame_resized, verbose=False)

                        # Chỉ lưu nếu có phát hiện đối tượng
                        if len(results[0].boxes) > 0:
                            # Đặt tên file có tiền tố video_name
                            base_filename = f"{video_name}_frame_{frame_count:06d}"
                            img_path = os.path.join(images_dir, f"{base_filename}.jpg")
                            txt_path = os.path.join(labels_dir, f"{base_filename}.txt")

                            cv2.imwrite(img_path, frame)

                            with open(txt_path, 'w') as f:
                                for box in results[0].boxes:
                                    cls_id = int(box.cls[0])
                                    x_center, y_center, width, height = box.xywhn[0]
                                    f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

                            video_saved_count += 1
                            total_saved_count += 1

                        progress_percent = int((frame_count / total_frames) * 100)
                        self.update_status(f"Video {idx+1}/{num_videos}: {video_name} | {progress_percent}% | Đã lưu: {video_saved_count}")

                    frame_count += 1

                cap.release()

            self.update_status(f"Hoàn thành! Đã lưu tổng cộng {total_saved_count} ảnh.")
            messagebox.showinfo("Thành công", f"Xử lý xong {num_videos} video!\nTổng cộng {total_saved_count} ảnh đã được lưu.")

        except Exception as e:
            self.update_status("Lỗi trong quá trình xử lý!")
            messagebox.showerror("Lỗi", str(e))
        finally:
            self.root.after(0, lambda: self.btn_start.config(state="normal", text="▶ BẮT ĐẦU GÁN NHÃN"))

    def update_status(self, text):
        self.root.after(0, lambda: self.lbl_status.config(text=text))

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoAnnotatorApp(root)
    root.mainloop()