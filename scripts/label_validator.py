import os
import pathlib

def calculate_iou(box1, box2):
    """Tính IoU giữa 2 box định dạng [x_center, y_center, width, height] chuẩn hoá."""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    b1_x1, b1_y1 = x1 - w1/2, y1 - h1/2
    b1_x2, b1_y2 = x1 + w1/2, y1 + h1/2
    b2_x1, b2_y1 = x2 - w2/2, y2 - h2/2
    b2_x2, b2_y2 = x2 + w2/2, y2 + h2/2
    
    ix1, iy1 = max(b1_x1, b2_x1), max(b1_y1, b2_y1)
    ix2, iy2 = min(b1_x2, b2_x2), min(b1_y2, b2_y2)
    
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    union = (w1 * h1) + (w2 * h2) - inter
    return inter / union if union > 0 else 0

def validate_and_clean_labels(txt_path, ai_boxes, target_cls, min_conf):
    """
    Logic kiểm chứng và dọn dẹp nhãn sai cho 1 file.
    Hỗ trợ:
    1. Xoá nhãn nếu AI không phát hiện thấy vật thể (IoU <= 0.45).
    2. Tự sửa tọa độ (nắn box) theo AI (nếu IoU > 0.45).
    3. Tự sửa Class ID sang nhãn đúng của AI (nếu lệch nhãn nhưng cùng vị trí).
    
    Trả về: (số nhãn đã xóa, số nhãn đã sửa)
    """
    if not os.path.exists(txt_path):
        return 0, 0

    existing_labels = []
    try:
        with open(txt_path, 'r') as f:
            for line in f:
                parts = list(map(float, line.strip().split()))
                if parts: existing_labels.append(parts)
    except: return 0, 0

    if not existing_labels:
        return 0, 0

    final_labels = []
    removed_count = 0
    corrected_count = 0

    # Danh sách các AI boxes đã được map (tránh map trùng)
    matched_ai_indices = set()

    for old_label in existing_labels:
        old_cls = int(old_label[0])
        old_box = old_label[1:]
        
        # Tìm AI box khớp nhất (IoU lớn nhất và > 0.45)
        best_ai_idx = -1
        best_iou = 0.45
        
        for idx, ai_box in enumerate(ai_boxes):
            if idx in matched_ai_indices:
                continue
            iou = calculate_iou(old_box, ai_box.xywhn[0].tolist())
            if iou > best_iou:
                best_iou = iou
                best_ai_idx = idx
        
        if best_ai_idx != -1:
            # Tìm thấy AI box khớp vị trí!
            matched_ai_indices.add(best_ai_idx)
            ai_box = ai_boxes[best_ai_idx]
            ai_cls = int(ai_box.cls[0])
            ai_box_coords = ai_box.xywhn[0].tolist()
            
            # Kiểm tra xem có cần sửa đổi không
            is_corrected = False
            new_label = [old_cls] + old_box
            
            # 1. Tự sửa nhãn (Class ID) nếu lệch nhãn nhưng cùng vị trí
            if old_cls != ai_cls:
                new_label[0] = ai_cls
                is_corrected = True
            
            # 2. Tự nắn tọa độ cho khớp với AI
            if old_box != ai_box_coords:
                new_label[1:] = ai_box_coords
                is_corrected = True
                
            if is_corrected:
                corrected_count += 1
            
            final_labels.append(new_label)
        else:
            # Không tìm thấy AI box khớp vị trí
            # Nếu class trùng với target_cls (hoặc target_cls == -1 tức là check tất cả), ta sẽ xóa nhãn này
            if target_cls == -1 or old_cls == target_cls:
                removed_count += 1
            else:
                # Giữ nguyên nếu không phải class cần lọc
                final_labels.append(old_label)

    # Ghi lại file nhãn nếu có sự thay đổi
    if removed_count > 0 or corrected_count > 0:
        if not final_labels:
            try: os.remove(txt_path)
            except: pass
        else:
            with open(txt_path, 'w') as f:
                for l in final_labels:
                    f.write(f"{int(l[0])} {' '.join(map(str, l[1:]))}\n")
    
    return removed_count, corrected_count
