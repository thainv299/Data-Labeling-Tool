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

def get_label_path_universal(img_path, ds_dir):
    """Xác định đường dẫn nhãn tự động cho cả 2 chế độ thư mục."""
    parts = list(pathlib.Path(img_path).parts)
    idx = None
    for rev_idx in range(len(parts) - 1, -1, -1):
        if parts[rev_idx].lower() == "images":
            idx = rev_idx
            break
    if idx is not None:
        parts[idx] = "labels"
        return str(pathlib.Path(*parts).with_suffix(".txt"))
    else:
        return os.path.splitext(img_path)[0] + ".txt"

def process_image_upgrade_logic(img_path, result, mapping, ds_dir):
    """Logic cho Tab 2: Nâng cấp nhãn (Append mode)."""
    label_path = get_label_path_universal(img_path, ds_dir)
    os.makedirs(os.path.dirname(label_path), exist_ok=True)

    boxes_to_add = []
    for res_box in result.boxes:
        cls_ori = int(res_box.cls[0])
        if cls_ori in mapping:
            new_cls = mapping[cls_ori]
            bn = [float(x) for x in res_box.xywhn[0]]
            boxes_to_add.append([new_cls] + bn)

    if boxes_to_add:
        with open(label_path, 'a') as f:
            for b in boxes_to_add:
                f.write(f"{int(b[0])} {' '.join(map(str, b[1:]))}\n")
        return True
    return False

def process_image_supplemental_logic(img_path, result, mapping, ds_dir):
    """Logic cho Tab 3: Vẽ bù nhãn còn thiếu (Supplemental)."""
    label_path = get_label_path_universal(img_path, ds_dir)
    
    # Đọc nhãn cũ
    existing_boxes = []
    if os.path.exists(label_path):
        with open(label_path, 'r') as f:
            for line in f:
                parts_split = line.strip().split()
                if len(parts_split) == 5:
                    existing_boxes.append([int(parts_split[0])] + [float(x) for x in parts_split[1:]])

    boxes_to_add = []
    for res_box in result.boxes:
        cls_ori = int(res_box.cls[0])
        if cls_ori in mapping:
            new_cls = mapping[cls_ori]
            bn = [float(x) for x in res_box.xywhn[0]] # [xc, yc, w, h]
            
            # Chỉ thêm nếu chưa có nhãn nào tại đó (IoU < 0.3)
            is_new = True
            for eb in existing_boxes:
                if eb[0] == new_cls:
                    if calculate_iou(bn, eb[1:]) > 0.3:
                        is_new = False
                        break
            
            if is_new:
                boxes_to_add.append([new_cls] + bn)

    if boxes_to_add:
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        with open(label_path, 'a') as f:
            for b in boxes_to_add:
                f.write(f"{int(b[0])} {' '.join(map(str, b[1:]))}\n")
        return len(boxes_to_add)
    return 0
