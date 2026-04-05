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
        
        self.video_path = tk.StringVar()
        self.model_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        self.setup_ui()

    def setup_ui(self):
        frame_model = tk.LabelFrame(self.root, text="1. Chọn Model YOLO (.pt)", padx=10, pady=10)
        frame_model.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_model, textvariable=self.model_path, width=50, state='readonly').pack(side="left", padx=5)
        tk.Button(frame_model, text="Browse", command=self.browse_model).pack(side="left")

        frame_video = tk.LabelFrame(self.root, text="2. Chọn Video đầu vào", padx=10, pady=10)
        frame_video.pack(fill="x", padx=10, pady=5)
        tk.Entry(frame_video, textvariable=self.video_path, width=50, state='readonly').pack(side="left", padx=5)
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
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov")])
        if path: self.video_path.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path: self.output_dir.set(path)

    def start_processing(self):
        if not self.model_path.get() or not self.video_path.get() or not self.output_dir.get():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ Model, Video và Thư mục lưu!")
            return

        self.btn_start.config(state="disabled", text="ĐANG XỬ LÝ...")
        threading.Thread(target=self.process_video, daemon=True).start()

    def process_video(self):
        try:
            self.update_status("Đang tải mô hình YOLO...")
            model = YOLO(self.model_path.get())
            cap = cv2.VideoCapture(self.video_path.get())
            if not cap.isOpened():
                raise Exception("Không thể mở video!")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frames_to_skip = int(fps * 3) 
            
            frame_count = 0
            saved_count = 0

            self.update_status(f"Bắt đầu xử lý. Nhảy cóc mỗi {frames_to_skip} frames (3 giây).")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frames_to_skip == 0:
                    results = model.predict(frame, verbose=False)
                    
                    base_filename = f"frame_{frame_count:06d}"
                    img_path = os.path.join(self.output_dir.get(), f"{base_filename}.jpg")
                    txt_path = os.path.join(self.output_dir.get(), f"{base_filename}.txt")
                    
                    cv2.imwrite(img_path, frame)
                    
                    with open(txt_path, 'w') as f:
                        for box in results[0].boxes:
                            cls_id = int(box.cls[0])
                            # xywhn trả về tọa độ đã chuẩn hóa (từ 0.0 đến 1.0) 
                            x_center, y_center, width, height = box.xywhn[0]
                            f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                    
                    saved_count += 1
                    
                    progress_percent = int((frame_count / total_frames) * 100)
                    self.update_status(f"Đang xử lý: {progress_percent}% | Đã lưu: {saved_count} ảnh")

                frame_count += 1

            cap.release()
            self.update_status(f"Hoàn thành! Đã lưu tổng cộng {saved_count} ảnh và file nhãn.")
            messagebox.showinfo("Thành công", f"Xử lý xong!\nĐã trích xuất {saved_count} ảnh vào thư mục đích.")

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