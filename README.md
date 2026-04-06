# 🏷️ Data Labeling Tool

Bộ công cụ hỗ trợ **gán nhãn dữ liệu YOLO** chuyên nghiệp — tự động trích xuất & gán nhãn từ video, đánh giá và chỉnh sửa nhãn thủ công trên giao diện trực quan.

## 📸 Demo

![Giao diện chính của ứng dụng](assets/demo1.png)

![Gán nhãn và chỉnh sửa bounding box](assets/demo2.png)

## ✨ Tính năng

| Tính năng | Mô tả |
|---|---|
| 🤖 **Auto-Annotation** | Trích xuất frame từ video và dùng model YOLO (`.pt`) để gán nhãn tự động |
| 🔍 **Review & Edit** | Giao diện kéo-thả để vẽ, chỉnh sửa và xóa bounding box |
| 📂 **Dual-Mode** | Hỗ trợ cả thư mục đơn lẫn cấu trúc YOLO chuẩn (`images/` + `labels/` với `train/val/test`) |
| 🔎 **Tìm kiếm ảnh** | Ô tìm kiếm với gợi ý tự động (autocomplete) để nhảy nhanh đến ảnh bất kỳ |
| ✏️ **Đổi tên đồng bộ** | Đổi tên ảnh → tệp nhãn `.txt` tự động đổi theo, giữ tính nhất quán dữ liệu |
| 🛡️ **Xử lý ảnh lỗi** | Tự động phát hiện ảnh bị hỏng (truncated) mà không làm crash ứng dụng |

## 🗂️ Cấu trúc dự án

```
DataLabelingTool/
├── main.py                ← Điểm khởi chạy ứng dụng
├── app.py                 ← Controller điều phối chính
├── auto_annotator.py      ← Tự động gán nhãn từ video
├── auto_rename.py         ← Script đổi tên ảnh (standalone)
│
├── core/                  ← Logic nghiệp vụ (không phụ thuộc giao diện)
│   ├── config.py          ← Cấu hình: CLASSES, COLORS, hằng số
│   └── data_manager.py    ← Quét thư mục, đọc/ghi/đổi tên nhãn
│
├── ui/                    ← Giao diện Tkinter
│   ├── toolbar.py         ← Thanh công cụ: chế độ, tải, tìm kiếm, đổi tên
│   ├── class_panel.py     ← Bảng chọn nhãn bên trái
│   ├── canvas_panel.py    ← Vùng vẽ trung tâm + điều hướng ◀ ▶
│   └── status_bar.py      ← Thanh trạng thái phía dưới
│
└── assets/                ← Ảnh demo và tài nguyên
```

## 🚀 Cài đặt

### Yêu cầu
- Python 3.8+

### Cài đặt thư viện

```bash
pip install Pillow opencv-python ultralytics
```

## 📖 Hướng dẫn sử dụng

### Review & Chỉnh sửa nhãn

```bash
python main.py
```

1. Chọn **Chế độ** phù hợp với cấu trúc thư mục của bạn.
2. Nhấn **"Chọn thư mục Dataset"** để tải ảnh.
3. Kéo chuột trên ảnh để vẽ bounding box → nhấn **Enter** để chốt.
4. Nhấn **Ctrl+S** để lưu nhãn.

### Tự động gán nhãn từ video

```bash
python auto_annotator.py
```

## ⌨️ Phím tắt

| Phím | Chức năng |
|---|---|
| `Enter` | Chốt khung nhãn vừa vẽ |
| `Ctrl + Z` | Hoàn tác nhãn cuối cùng |
| `Ctrl + S` | Lưu nhãn |
| `Ctrl + R` | Trỏ vào ô đổi tên ảnh |
| `←` / `→` | Chuyển ảnh trước / sau |

---

*Vibecode by thainv299 😁*
