import os
import cv2

def process_batch_video_logic(model, frames, metas, images_dir, labels_dir, resize=True, save_background=False):
    """
    Logic xử lý AI cho một batch frame từ video.
    Duyệt qua TOÀN BỘ batch và lưu từng ảnh/nhãn theo cấu hình.
    """
    saved_count = 0
    # Inference cả batch để tối ưu tốc độ (TensorRT/GPU)
    results = model.predict(frames, imgsz=640, half=True, verbose=False)
    
    # Duyệt qua từng kết quả trong batch (ví dụ duyệt đủ 4 kết quả nếu batch=4)
    for i, result in enumerate(results):
        frame = frames[i]
        meta = metas[i]
        has_objects = len(result.boxes) > 0
        
        # Quyết định lưu: Có vật thể HOẶC người dùng muốn lưu cả ảnh trống (Background)
        if has_objects or save_background:
            video_name = meta['video_name']
            frame_count = meta['frame_count']
            base_filename = f"{video_name}_frame_{frame_count:06d}"
            
            img_path = os.path.join(images_dir, f"{base_filename}.jpg")
            txt_path = os.path.join(labels_dir, f"{base_filename}.txt")

            # 1. Xử lý Resize ảnh (nếu được bật)
            if resize:
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

            # 2. Xử lý ghi nhãn YOLO
            if has_objects:
                with open(txt_path, "w") as f:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        # Lấy tọa độ chuẩn hóa [x_center, y_center, width, height]
                        x_center, y_center, width, height = box.xywhn[0].tolist()
                        
                        f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            else:
                # Nếu lưu background (không có vật thể) thì tạo file txt rỗng
                open(txt_path, 'w').close()
            
            saved_count += 1
            
    return saved_count
