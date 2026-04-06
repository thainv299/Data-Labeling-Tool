
import tkinter as tk
from app import YoloReviewerApp


def main():
    """Hàm khởi kháp ứng dụng."""
    root = tk.Tk()
    
    # Khởi tạo đối tượng ứng dụng chính
    app = YoloReviewerApp(root)

    # Đảm bảo hình học cửa sổ được tính toán trước khi tải ảnh đầu tiên
    root.update()

    # Vòng lặp giao diện chính
    root.mainloop()


if __name__ == "__main__":
    main()
