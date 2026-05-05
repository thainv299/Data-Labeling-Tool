# 🚀 YOLO Data Labeling & Auto-Annotation Tool

Công cụ gán nhãn dữ liệu thông minh chuyên dụng cho các bài toán Computer Vision (YOLO). Được tích hợp AI mạnh mẽ để tự động hóa quy trình gán nhãn, giúp giảm 80% thời gian làm việc so với các phương pháp truyền thống.

---

## ✨ Tính năng nổi bật

### 1. Gán nhãn thủ công chuyên nghiệp
- **Giao diện tối ưu:** Kéo thả mượt mà, hỗ trợ Zoom thông minh, Panning.
- **Quản lý thông minh:** Tìm kiếm ảnh theo tên, lọc ảnh theo trạng thái.
- **Thao tác nhanh:** Đổi tên, xóa ảnh/nhãn trực tiếp với hệ thống phím tắt mạnh mẽ.

### 2. Auto-Annotation (AI Hỗ trợ gán nhãn tự động)
Hệ thống hỗ trợ 3 chế độ AI cực mạnh:
- **Trích xuất từ Video:** Tự động cắt frame video và chạy AI để gán nhãn. Chỉ lưu lại những ảnh thực sự có vật thể, giúp tiết kiệm dung lượng lưu trữ.
- **Nâng cấp Dataset (Append Mode):** Chạy AI trên bộ dữ liệu đã có nhãn để bổ sung thêm các lớp mới (Class Mapping) mà không làm mất dữ liệu cũ.
- **Vẽ bù nhãn (Supplemental Mode):** Quét toàn bộ Dataset, AI sẽ tự động "vẽ bù" vào những vật thể còn sót chưa được gán nhãn.
- **Tối ưu Batch Inference:** Xử lý hàng loạt ảnh cùng lúc (Batch Size = 4) kết hợp công nghệ TensorRT (FP16) cho tốc độ xử lý "siêu tốc".

### 3. Bộ công cụ tối ưu Dataset (Tools Menu)
- **Chia nhỏ Dataset (Split into N parts):** Chia bộ dữ liệu lớn thành N phần cho nhiều người cùng tham gia gán nhãn.
- **Chia Train/Val/Test:** Tự động phân bổ dữ liệu theo tỷ lệ chuẩn cho quá trình huấn luyện.
- **Lọc nhãn trùng (Deduplication):** Tự động phát hiện và xóa các khung nhãn bị chồng chéo (Ưu tiên giữ lại nhãn nhỏ nhất để ôm sát vật thể).
- **Đồng bộ Cleanup:** Tự động tìm và xóa các file nhãn rác hoặc ảnh không có nhãn.
- **Batch Edit:** Xóa nhãn theo dải ảnh hoặc đổi Class ID hàng loạt.

---

## 🛠 Hướng dẫn cài đặt

1. **Yêu cầu hệ thống:** 
   - Python 3.9 trở lên.
   - GPU NVIDIA (khuyên dùng) để đạt hiệu năng AI tốt nhất.
2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Chạy ứng dụng:**
   ```bash
   python main.py
   ```

---

## 📖 Hướng dẫn sử dụng chi tiết

### 1. Tự động gán nhãn từ Video
- Mở **Auto-Annotator** -> Chọn Tab 1.
- Chọn danh sách video đầu vào và thư mục đích.
- Chọn Model YOLO (`.pt` hoặc `.engine`).
- Nhấn **Bắt đầu**. AI sẽ tự động trích xuất các khoảnh khắc có vật thể và tạo file nhãn YOLO chuẩn.

### 2. Chia nhỏ dữ liệu cho nhiều người (N parts)
- Vào menu **Công cụ** -> **Chia nhỏ Dataset thành N phần**.
- Nhập số lượng phần muốn chia (N).
- Nhập tên các thư mục đích cho từng phần.
- Hệ thống sẽ tự động tính toán và di chuyển (Move) ảnh + nhãn sang các thư mục mới theo thứ tự.

### 3. Lọc nhãn trùng lặp
- Khi gán nhãn tự động hoặc gán nhãn thủ công bị chồng chéo, hãy sử dụng tính năng **Lọc Bounding Box Trùng**.
- Hệ thống sẽ sử dụng thuật toán **IoU (Intersection over Union)** với ngưỡng 0.45 để xác định các nhãn trùng.
- Nhãn có diện tích **nhỏ hơn** sẽ được ưu tiên giữ lại để đảm bảo độ chính xác cao nhất cho Dataset.

---

## ⌨️ Hệ thống phím tắt (Hotkeys)

| Phím | Chức năng |
| :--- | :--- |
| `Enter` | Chốt khung nhãn vừa vẽ (Draft) |
| `A / D` hoặc `Left / Right` | Chuyển sang ảnh Trước / Sau |
| `Ctrl + S` | Lưu tất cả thay đổi hiện tại |
| `Ctrl + Z` | Hoàn tác (Undo) khung nhãn vừa vẽ |
| `Delete` | Xóa vĩnh viễn ảnh hiện tại khỏi ổ cứng |
| `X` | Xóa khung nhãn đang được chọn |
| `Ctrl + Wheel` | Phóng to / Thu nhỏ ảnh |
| `Ctrl + B` | Mở công cụ sao chép Box tĩnh (Copy Static Box) |
| `Ctrl + R` | Đổi tên nhanh file ảnh hiện tại |

---

## 💡 Mẹo tối ưu hóa
- **Sử dụng TensorRT:** Luôn ưu tiên dùng file `.engine` để tốc độ gán nhãn nhanh hơn 5-10 lần so với file `.pt`.
- **Export Engine đúng cách:** Sử dụng tham số `dynamic=True` khi export model để hỗ trợ xử lý hàng loạt (Batch Inference).
- **Class Mapping:** Khi nâng cấp Dataset, hãy kiểm tra kỹ ID của Model AI và ID của Dataset hiện tại để map cho chính xác.

---
*Phát triển bởi: Thainv299 + Antigravity*
