import os
import cv2
from ultralytics import YOLO

def process_batch_video_logic(model, frames, metas, images_dir, labels_dir):
    """
    Logic xử lý AI cho một batch frame từ video và lưu kết quả.
    Tách biệt hoàn toàn khỏi UI.
    """
    saved_count = 0
    # Inference cả batch
    results = model.predict(frames, imgsz=640, half=True, verbose=False)
    
    for i, result in enumerate(results):
        frame = frames[i]
        meta = metas[i]
        
        # Chỉ lưu nếu phát hiện vật thể
        if len(result.boxes) > 0:
            video_name = meta['video_name']
            frame_count = meta['frame_count']
            
            file_name = f"{video_name}_frame_{frame_count:06d}.jpg"
            img_path = os.path.join(images_dir, file_name)
            cv2.imwrite(img_path, frame)
            
            # Lưu file nhãn YOLO
            txt_name = f"{video_name}_frame_{frame_count:06d}.txt"
            txt_path = os.path.join(labels_dir, txt_name)
            
            with open(txt_path, "w") as f:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    xywh = box.xywhn[0].tolist() # [x, y, w, h] chuẩn hoá
                    f.write(f"{cls} {' '.join(map(str, xywh))}\n")
            
            saved_count += 1
            
    return saved_count
