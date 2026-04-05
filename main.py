# ============================================================
# main.py — Application entry point
# ============================================================
import tkinter as tk
from app import YoloReviewerApp


def main():
    root = tk.Tk()
    app = YoloReviewerApp(root)

    # Ensure window geometry is calculated before first image load
    root.update()

    root.mainloop()


if __name__ == "__main__":
    main()
