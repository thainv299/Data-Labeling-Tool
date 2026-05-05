# 🏷️ Data Labeling Tool

Bộ công cụ hỗ trợ **gán nhãn dữ liệu YOLO** chuyên nghiệp — tự động trích xuất & gán nhãn từ video, đánh giá và chỉnh sửa nhãn thủ công trên giao diện trực quan, kèm đầy đủ công cụ quản lý dataset.

## 📸 Demo

![Giao diện chính của ứng dụng](assets/giaodien.png)

![Gán nhãn và chỉnh sửa bounding box](assets/demo1.png)

![Công cụ chia dataset](assets/demo2.png)

![Công cụ đánh nhãn tự động bằng model yolo](assets/demo3.png)

## ✨ Tính năng

| Tính năng | Mô tả |
|---|---|
| 🤖 **Auto-Annotation** | 3 chế độ: Trích xuất Video, Nâng cấp Dataset (Append), Vẽ bù nhãn còn thiếu (Supplemental) |
| ⚡ **Batch & TensorRT** | Tối ưu Batch Inference (xử lý 4 ảnh/lần) và hỗ trợ TensorRT cho tốc độ siêu nhanh |
| 🔍 **Review & Edit** | Giao diện kéo-thả để vẽ, chỉnh sửa và xóa bounding box; hỗ trợ Zoom/Panning |
| 📂 **Dual-Mode** | Hỗ trợ cả thư mục đơn lẫn cấu trúc YOLO chuẩn (`images/` + `labels/`) |
| 🔎 **Tìm kiếm ảnh** | Ô tìm kiếm với gợi ý tự động (autocomplete) để nhảy nhanh đến ảnh bất kỳ |
| ✏️ **Đổi tên đồng bộ** | Đổi tên ảnh → tệp nhãn `.txt` tự động đổi theo |
| 💾 **Auto-Save** | Tự động lưu nhãn khi chuyển ảnh bằng phím mũi tên hoặc A/D |
| 🧹 **Lọc Box Trùng** | Tự động xoá box trùng lặp (IoU > 0.45), ưu tiên giữ nhãn nhỏ nhất ôm sát vật thể |
| 🗑️ **Dọn Label Rác** | Xoá file nhãn hoặc ảnh không có nhãn để đồng bộ dataset |

## 🛠️ Công cụ tích hợp (Menu → Công cụ)

| Công cụ | Mô tả |
|---|---|
| ✂️ **Chia Dataset** | Chia ảnh+nhãn thành `train/valid/test` theo tỉ lệ tuỳ chọn |
| 📦 **Chia nhỏ N phần** | Chia bộ dữ liệu lớn thành N phần cho nhiều người cùng làm (di chuyển file vật lý) |
| 📐 **Resize ảnh hàng loạt** | Resize toàn bộ ảnh về kích thước chuẩn (mặc định 640px) |
| 🔢 **Đổi Class ID hàng loạt** | Chuyển đổi Class ID trong file nhãn (VD: đổi class `0` → `4`) |
| 🔄 **Đồng bộ Ảnh ↔ Nhãn** | Quét và xoá file ảnh/nhãn không có cặp để cân bằng dataset 1-1 |

## 📖 Hướng dẫn sử dụng

### 1. Review & Chỉnh sửa nhãn
- Chạy `python main.py`.
- Chọn thư mục Dataset.
- Vẽ khung nhãn trên ảnh -> nhấn **Enter** để chốt.
- Nhấn `←`/`→` hoặc `A`/`D` để chuyển ảnh (tự động lưu).

### 2. Sử dụng Auto-Annotator (AI)
- Nhấn nút **Auto Annotator** trên thanh công cụ.
- **Tab 1:** Cắt video -> AI tự gán nhãn -> Lưu ảnh có vật thể.
- **Tab 2:** Nâng cấp Dataset cũ (dùng Class Mapping để thêm lớp mới).
- **Tab 3:** Quét toàn bộ ảnh và vẽ bù vào các vật thể AI phát hiện nhưng chưa có nhãn.
- *Tip: Nên dùng file `.engine` (TensorRT) và bật `half=True` để đạt tốc độ cao nhất.*

### 3. Chia nhỏ Dataset cho Team
- Vào **Công cụ -> Chia nhỏ Dataset thành N phần**.
- Nhập số phần, nhập tên các folder đích. Chương trình sẽ tự động Move dữ liệu.

## ⌨️ Phím tắt

| Phím | Chức năng |
|---|---|
| `Enter` | Chốt khung nhãn vừa vẽ |
| `A` / `D` hoặc `←` / `→` | Chuyển ảnh trước / sau (tự động lưu) |
| `Ctrl + Z` | Hoàn tác (Undo) nhãn cuối cùng |
| `Ctrl + S` | Lưu nhãn thủ công |
| `Ctrl + R` | Trỏ vào ô đổi tên ảnh |
| `Del` | Xoá ảnh hiện tại (nếu không chọn nhãn) |
| `X` | Xóa khung nhãn đang được chọn |
| `Esc` | Bỏ chọn nhãn |
| `Ctrl + Wheel` | Zoom in / Zoom out |
| `Ctrl + B` | Mở công cụ sao chép Box tĩnh |

---

*Vibecode by thainv299😁*
