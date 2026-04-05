# ============================================================
# config.py — Các hằng số và định nghĩa lớp của ứng dụng
# ============================================================

# Danh sách nhãn chuẩn (class_id -> class_name)
# Đây là danh sách các đối tượng mà mô hình YOLO có thể nhận diện
CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "license_plate",
    5: "bus",
    6: "truck",
}

# Bảng màu cho từng lớp (dùng khi vẽ khung bao - bounding box)
COLORS = [
    "#FF3838",  # person — đỏ
    "#FF9D97",  # bicycle — hồng
    "#FF701F",  # car — cam
    "#FFB21D",  # motorcycle — vàng cam
    "#CFD231",  # license_plate — vàng xanh
    "#48F90A",  # bus — xanh lá
    "#92CC17",  # truck — xanh olive
]

# Các định dạng tệp ảnh được hỗ trợ
SUPPORTED_EXTENSIONS = (".jpg", ".png")

# Các thiết lập mặc định cho cửa sổ ứng dụng
APP_TITLE = "YOLO Label Review & Editor - Tự động gán nhãn & Kiểm tra"
APP_GEOMETRY = "1200x800"
