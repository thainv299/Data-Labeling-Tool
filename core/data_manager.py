# ============================================================
# data_manager.py — Logic xử lý dữ liệu (không phụ thuộc vào giao diện)
# ============================================================
import os
import glob
import pathlib


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
            # Nhãn nằm ngay cạnh ảnh
            return os.path.splitext(img_path)[0] + ".txt"

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
