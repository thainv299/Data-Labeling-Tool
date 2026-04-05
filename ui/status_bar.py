# ============================================================
# status_bar.py — Bottom status/hint bar
# ============================================================
import tkinter as tk


class StatusBar(tk.Frame):
    """Thin status bar at the bottom of the window showing hints or status messages."""

    def __init__(self, parent, text: str = ""):
        super().__init__(parent, bg="#ecf0f1", pady=2)

        self.lbl = tk.Label(
            self,
            text=text,
            font=("Arial", 9),
            bg="#ecf0f1",
            fg="#7f8c8d",
        )
        self.lbl.pack()

    def set_text(self, text: str):
        """Update the status bar text."""
        self.lbl.config(text=text)
