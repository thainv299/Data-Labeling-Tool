# ============================================================
# data_manager.py — Logic xử lý dữ liệu (không phụ thuộc vào giao diện)
# ============================================================
import os
import glob
import pathlib
import yaml


class DataManager:
    """Xử lý quét tập dữ liệu, phân giải đường dẫn nhãn và đọc/ghi tệp nhãn."""

    # ----------------------------------------------------------
    # Quét thư mục
    # ----------------------------------------------------------
    @staticmethod
    def scan_folder(folder: str, mode: str) -> list[str]:
        """Tải danh sách các tệp ảnh dựa trên chế độ đã chọn."""
        if mode == "yolo_dataset":
            images_dir = os.path.join(folder, "images")
            if not os.path.isdir(images_dir):
                raise FileNotFoundError(
                    f"Không tìm thấy thư mục 'images/' bên trong:\n{folder}\n\n"
                    "Vui lòng chọn thư mục gốc chứa 'images/' và 'labels/'."
                )
            # Quét đệ quy tất cả các thư mục con (train/, val/, test/, v.v.)
            image_paths = sorted(
                glob.glob(os.path.join(images_dir, "**", "*.jpg"), recursive=True)
                + glob.glob(os.path.join(images_dir, "**", "*.png"), recursive=True)
            )
        else:
            # Chế độ 1: Cùng thư mục — quét trực tiếp trong thư mục được chọn
            image_paths = sorted(
                glob.glob(os.path.join(folder, "*.jpg"))
                + glob.glob(os.path.join(folder, "*.png"))
            )
        return image_paths

    # ----------------------------------------------------------
    # Phân giải đường dẫn nhãn
    # ----------------------------------------------------------
    @staticmethod
    def get_label_path(img_path: str, mode: str) -> str:
        """Trả về đường dẫn tệp .txt tương ứng dựa trên chế độ hiện tại."""
        if mode == "yolo_dataset":
            p = pathlib.Path(img_path)
            parts = list(p.parts)
            # Tìm vị trí CUỐI CÙNG của thành phần 'images' trong đường dẫn
            idx = None
            for i in range(len(parts) - 1, -1, -1):
                if parts[i].lower() == "images":
                    idx = i
                    break
            if idx is not None:
                parts[idx] = "labels"
            label_path = pathlib.Path(*parts).with_suffix(".txt")
            return str(label_path)
        else:
            # Gán nhãn mới: lưu vào thư mục labels/ cùng cấp với ảnh
            img_dir = os.path.dirname(img_path)
            labels_dir = os.path.join(img_dir, "labels")
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            return os.path.join(labels_dir, base_name + ".txt")

    # ----------------------------------------------------------
    # Đọc/Ghi tệp nhãn
    # ----------------------------------------------------------
    @staticmethod
    def load_labels(txt_path: str) -> list[tuple]:
        """Đọc tệp nhãn YOLO và trả về danh sách các bộ (cls_id, xc, yc, w, h)."""
        labels = []
        if os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        labels.append((
                            int(parts[0]),
                            float(parts[1]),
                            float(parts[2]),
                            float(parts[3]),
                            float(parts[4]),
                        ))
        return labels

    @staticmethod
    def save_labels(txt_path: str, labels: list[tuple]) -> None:
        """Ghi danh sách nhãn ra tệp YOLO .txt. Tự động tạo thư mục nếu chưa có."""
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        with open(txt_path, "w") as f:
            for cls_id, xc, yc, w, h in labels:
                f.write(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

    # ----------------------------------------------------------
    # Đổi tên tệp (Đồng bộ Ảnh + Nhãn)
    # ----------------------------------------------------------
    def rename_dataset_item(self, old_img_path: str, new_name: str, mode: str) -> str:
        """Đổi tên tệp ảnh và tệp nhãn tương ứng (nếu có)."""
        # 1. Phân tách đường dẫn cũ
        dir_name = os.path.dirname(old_img_path)
        old_file_name = os.path.basename(old_img_path)
        base, ext = os.path.splitext(old_file_name)

        if not new_name:
            return old_img_path

        # 2. Tạo đường dẫn ảnh mới
        new_img_path = os.path.join(dir_name, new_name + ext)
        if new_img_path == old_img_path:
            return old_img_path

        if os.path.exists(new_img_path):
            raise FileExistsError(f"Tệp đã tồn tại: {os.path.basename(new_img_path)}")

        # 3. Tìm đường dẫn nhãn tương ứng
        old_txt_path = self.get_label_path(old_img_path, mode)
        new_txt_path = os.path.join(os.path.dirname(old_txt_path), new_name + ".txt")

        # 4. Thực hiện đổi tên thực tế
        os.rename(old_img_path, new_img_path)
        if os.path.exists(old_txt_path):
            try:
                os.rename(old_txt_path, new_txt_path)
            except Exception as e:
                # Nếu đổi tên nhãn lỗi, cố gắng hoàn tác đổi tên ảnh? 
                # (Tạm thời chỉ báo lỗi vì hiếm khi xảy ra)
                print(f"Lỗi khi đổi tên nhãn: {e}")

    def delete_dataset_item(self, img_path: str, mode: str) -> bool:
        """Xoá vĩnh viễn tệp ảnh và tệp nhãn tương ứng."""
        try:
            txt_path = self.get_label_path(img_path, mode)
            if os.path.exists(img_path):
                os.remove(img_path)
            if os.path.exists(txt_path):
                os.remove(txt_path)
            return True
        except Exception as e:
            print(f"Lỗi khi xoá tệp: {e}")
            return False

    def delete_class_from_labels(self, folder: str, deleted_cls_id: int) -> int:
        """
        Xoá tất cả các box gán nhãn thuộc class `deleted_cls_id` trong toàn bộ dataset.
        Đồng thời giảm ID của các class > `deleted_cls_id` đi 1 đơn vị.
        Trả về số lượng file nhãn đã được cập nhật.
        """
        import glob
        updated_count = 0
        
        # Tìm tất cả các file .txt trong folder và các thư mục con
        for txt_file in glob.glob(os.path.join(folder, "**", "*.txt"), recursive=True):
            if os.path.basename(txt_file) == "classes.txt":
                continue
                
            if not os.path.isfile(txt_file):
                continue
                
            try:
                modified = False
                new_lines = []
                with open(txt_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            if cls_id == deleted_cls_id:
                                # Xoá box này
                                modified = True
                                continue
                            elif cls_id > deleted_cls_id:
                                # Giảm ID đi 1 đơn vị
                                parts[0] = str(cls_id - 1)
                                modified = True
                            new_lines.append(" ".join(parts))
                        else:
                            new_lines.append(line)
                            
                if modified:
                    with open(txt_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(new_lines) + "\n")
                    updated_count += 1
            except Exception as e:
                print(f"Lỗi khi xử lý file nhãn {txt_file}: {e}")
                
        return updated_count

    def update_class_id_in_labels(self, folder: str, old_id: int, new_id: int) -> int:
        """
        Thay đổi class ID từ `old_id` sang `new_id` trong toàn bộ các file nhãn của dataset.
        Trả về số lượng file nhãn đã được cập nhật.
        """
        import glob
        updated_count = 0
        
        for txt_file in glob.glob(os.path.join(folder, "**", "*.txt"), recursive=True):
            if os.path.basename(txt_file) == "classes.txt":
                continue
                
            if not os.path.isfile(txt_file):
                continue
                
            try:
                modified = False
                new_lines = []
                with open(txt_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            if cls_id == old_id:
                                parts[0] = str(new_id)
                                modified = True
                            new_lines.append(" ".join(parts))
                        else:
                            new_lines.append(line)
                            
                if modified:
                    with open(txt_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(new_lines) + "\n")
                    updated_count += 1
            except Exception as e:
                print(f"Lỗi khi xử lý file nhãn {txt_file}: {e}")
                
        return updated_count

    # ----------------------------------------------------------
    # Dọn dẹp nhãn không có ảnh và ảnh không có nhãn
    # ----------------------------------------------------------
    def clean_orphan_labels(self, folder: str, mode: str) -> tuple:
        """
        Quét và xoá dữ liệu:
        1. Xoá file .txt nếu KHÔNG CÓ ảnh đi kèm.
        2. Xoá file ảnh nếu KHÔNG CÓ file .txt đi kèm (Chỉ xoá nếu mất hoàn toàn file .txt).
        Trả về (số_nhãn_xoá, số_ảnh_xoá).
        """
        deleted_txt = 0
        deleted_img = 0

        # --- 1. Xoá nhãn không có ảnh (TXT without Image) ---
        if mode == "yolo_dataset":
            labels_dir = os.path.join(folder, "labels")
            images_dir = os.path.join(folder, "images")
            if os.path.isdir(labels_dir):
                for txt_file in glob.glob(os.path.join(labels_dir, "**", "*.txt"), recursive=True):
                    if os.path.basename(txt_file) in ["classes.txt", "data.yaml"]:
                        continue
                    
                    p = pathlib.Path(txt_file)
                    parts = list(p.parts)
                    idx = None
                    for i in range(len(parts) - 1, -1, -1):
                        if parts[i].lower() == "labels":
                            idx = i
                            break
                    if idx is not None:
                        parts[idx] = "images"
                    
                    img_base = str(pathlib.Path(*parts).with_suffix(""))
                    if not (os.path.exists(img_base + ".jpg") or os.path.exists(img_base + ".png") or os.path.exists(img_base + ".jpeg")):
                        try:
                            os.remove(txt_file)
                            deleted_txt += 1
                        except Exception: pass
        else:
            labels_dir = os.path.join(folder, "labels")
            if os.path.isdir(labels_dir):
                for txt_file in glob.glob(os.path.join(labels_dir, "*.txt")):
                    if os.path.basename(txt_file) == "classes.txt":
                        continue
                    base_name = os.path.splitext(os.path.basename(txt_file))[0]
                    img_in_folder = os.path.join(folder, base_name)
                    if not (os.path.exists(img_in_folder + ".jpg") or os.path.exists(img_in_folder + ".png") or os.path.exists(img_in_folder + ".jpeg")):
                        try:
                            os.remove(txt_file)
                            deleted_txt += 1
                        except Exception: pass

        # --- 2. Xoá ảnh không có nhãn (Image without TXT) ---
        all_images = []
        if mode == "yolo_dataset":
            images_dir = os.path.join(folder, "images")
            if os.path.isdir(images_dir):
                for ext in ("*.jpg", "*.jpeg", "*.png"):
                    all_images.extend(glob.glob(os.path.join(images_dir, "**", ext), recursive=True))
        else:
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                all_images.extend(glob.glob(os.path.join(folder, ext)))

        for img_path in all_images:
            txt_path = self.get_label_path(img_path, mode)
            if not os.path.exists(txt_path):
                try:
                    os.remove(img_path)
                    deleted_img += 1
                except Exception: pass

        return deleted_txt, deleted_img

    # ----------------------------------------------------------
    # Tải cấu hình YAML (data.yaml)
    # ----------------------------------------------------------
    @staticmethod
    def load_dataset_config(folder: str) -> dict:
        """Tìm và tải file data.yaml hoặc dataset.yaml hoặc *.yaml trong thư mục để lấy danh sách class."""
        yaml_files = glob.glob(os.path.join(folder, "*.yaml"))
        if not yaml_files:
            # Thử tìm trong thư mục cha nếu folder là 'images'
            parent = os.path.dirname(folder)
            yaml_files = glob.glob(os.path.join(parent, "*.yaml"))

        if yaml_files:
            try:
                # Ưu tiên dataset.yaml hoặc data.yaml
                target_yaml = yaml_files[0]
                for yf in yaml_files:
                    basename = os.path.basename(yf).lower()
                    if basename in ["dataset.yaml", "data.yaml"]:
                        target_yaml = yf
                        break
                
                with open(target_yaml, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'names' in data:
                        names = data['names']
                        if isinstance(names, list):
                            return {i: name for i, name in enumerate(names)}
                        elif isinstance(names, dict):
                            return {int(k): v for k, v in names.items()}
            except Exception as e:
                print(f"Lỗi khi đọc file YAML: {e}")
        
        return None

    # ----------------------------------------------------------
    # Khởi tạo dataset YOLO
    # ----------------------------------------------------------
    @staticmethod
    def create_yolo_dataset(base_dir: str, classes_dict: dict) -> bool:
        """Khởi tạo cấu trúc dataset YOLO mới (train/val/test)."""
        try:
            # 1. Tạo các thư mục
            for split in ['train', 'val', 'test']:
                os.makedirs(os.path.join(base_dir, split, 'images'), exist_ok=True)
                os.makedirs(os.path.join(base_dir, split, 'labels'), exist_ok=True)
            
            # 2. Tạo dataset.yaml
            yaml_path = os.path.join(base_dir, 'dataset.yaml')
            yaml_data = {
                'train': 'train/images',
                'val': 'val/images',
                'test': 'test/images',
                'names': classes_dict
            }
            
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
                
            return True
        except Exception as e:
            print(f"Lỗi khi khởi tạo dataset: {e}")
            return False

