# ============================================================
# config.py — Application constants and class definitions
# ============================================================

# Danh sách nhãn chuẩn (class_id -> class_name)
CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "license_plate",
    5: "bus",
    6: "truck",
}

# Bảng màu cho từng class (dùng khi vẽ bounding box)
COLORS = [
    "#FF3838",  # person — đỏ
    "#FF9D97",  # bicycle — hồng
    "#FF701F",  # car — cam
    "#FFB21D",  # motorcycle — vàng cam
    "#CFD231",  # license_plate — vàng xanh
    "#48F90A",  # bus — xanh lá
    "#92CC17",  # truck — xanh olive
]

# Định dạng ảnh được hỗ trợ
SUPPORTED_EXTENSIONS = (".jpg", ".png")

# App window defaults
APP_TITLE = "YOLO Label Review & Editor"
APP_GEOMETRY = "1100x750"
