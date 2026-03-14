import tkinter as tk
from src.ui.main_window import PomodoroApp

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    app.run()
