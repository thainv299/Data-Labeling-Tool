# ============================================================
# data_manager.py — Dataset I/O logic (no tkinter dependency)
# ============================================================
import os
import glob
import pathlib


class DataManager:
    """Handles dataset scanning, label path resolution, and label file I/O.

    This class is intentionally free of any tkinter dependency so it can be
    tested and reused independently of the GUI.
    """

    # ----------------------------------------------------------
    # Folder Scanning
    # ----------------------------------------------------------
    @staticmethod
    def scan_folder(folder: str, mode: str) -> list[str]:
        """Scan a folder for image files based on the selected mode.

        Args:
            folder: Root directory chosen by the user.
            mode: "same_folder" or "yolo_dataset".

        Returns:
            Sorted list of absolute image paths.

        Raises:
            FileNotFoundError: If mode is "yolo_dataset" and <folder>/images/ is missing.
        """
        if mode == "yolo_dataset":
            images_dir = os.path.join(folder, "images")
            if not os.path.isdir(images_dir):
                raise FileNotFoundError(
                    f"Không tìm thấy thư mục 'images/' bên trong:\n{folder}\n\n"
                    "Vui lòng chọn thư mục ROOT chứa 'images/' và 'labels/'."
                )
            # Recursively scan all subdirectories (train/, val/, test/, etc.)
            image_paths = sorted(
                glob.glob(os.path.join(images_dir, "**", "*.jpg"), recursive=True)
                + glob.glob(os.path.join(images_dir, "**", "*.png"), recursive=True)
            )
        else:
            # Mode 1: Same Folder — scan directly
            image_paths = sorted(
                glob.glob(os.path.join(folder, "*.jpg"))
                + glob.glob(os.path.join(folder, "*.png"))
            )
        return image_paths

    # ----------------------------------------------------------
    # Label Path Resolution
    # ----------------------------------------------------------
    @staticmethod
    def get_label_path(img_path: str, mode: str) -> str:
        """Return the correct .txt label path based on the current mode.

        Mode 1 (same_folder):
            Label is next to the image: img01.jpg -> img01.txt

        Mode 2 (yolo_dataset):
            Replace 'images' directory component with 'labels':
            dataset/images/train/img01.jpg -> dataset/labels/train/img01.txt
        """
        if mode == "yolo_dataset":
            p = pathlib.Path(img_path)
            parts = list(p.parts)
            # Find the LAST occurrence of 'images' in the path parts
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
            return os.path.splitext(img_path)[0] + ".txt"

    # ----------------------------------------------------------
    # Label File I/O
    # ----------------------------------------------------------
    @staticmethod
    def load_labels(txt_path: str) -> list[tuple]:
        """Read YOLO label file and return a list of (cls_id, xc, yc, w, h) tuples."""
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
        """Write a list of (cls_id, xc, yc, w, h) tuples to a YOLO label file.

        Automatically creates parent directories if they don't exist.
        """
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        with open(txt_path, "w") as f:
            for cls_id, xc, yc, w, h in labels:
                f.write(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
