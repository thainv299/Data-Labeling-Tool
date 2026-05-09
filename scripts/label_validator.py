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
    Trả về số nhãn đã bị xóa.
    """
    if not os.path.exists(txt_path):
        return 0

    existing_labels = []
    try:
        with open(txt_path, 'r') as f:
            for line in f:
                parts = list(map(float, line.strip().split()))
                if parts: existing_labels.append(parts)
    except: return 0

    target_labels = [l for l in existing_labels if int(l[0]) == target_cls]
    if not target_labels:
        return 0

    new_labels = [l for l in existing_labels if int(l[0]) != target_cls]
    keep_targets = []
    removed_count = 0

    for old_label in target_labels:
        is_valid = False
        for ai_box in ai_boxes:
            # ai_box format: ultralytics result boxes
            if calculate_iou(old_label[1:], ai_box.xywhn[0].tolist()) > 0.45:
                is_valid = True
                break
        
        if is_valid:
            keep_targets.append(old_label)
        else:
            removed_count += 1

    if removed_count > 0:
        final_labels = new_labels + keep_targets
        if not final_labels:
            try: os.remove(txt_path)
            except: pass
        else:
            with open(txt_path, 'w') as f:
                for l in final_labels:
                    f.write(f"{int(l[0])} {' '.join(map(str, l[1:]))}\n")
    
    return removed_count
