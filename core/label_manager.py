import json
import os

class LabelManager:
    """Quản lý các nhãn tùy chỉnh (Lưu và tải từ file JSON)."""

    @staticmethod
    def save_labels_to_json(filepath: str, labels_dict: dict) -> bool:
        """
        Lưu một từ điển nhãn (ví dụ: {0: 'person', 1: 'car'}) vào file JSON.
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(labels_dict, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu nhãn: {e}")
            return False

    @staticmethod
    def load_labels_from_json(filepath: str) -> dict:
        """
        Tải nhãn từ file JSON và trả về một từ điển {int_id: str_name}.
        Trả về dictionary rỗng nếu có lỗi.
        """
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Chuyển đổi key từ string về int
            return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"Lỗi khi tải nhãn: {e}")
            return {}
