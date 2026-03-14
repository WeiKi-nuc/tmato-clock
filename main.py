"""
番茄钟 + 任务看板 应用程序
Pomodoro Timer + Kanban Board Application
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main():
    """应用程序入口"""
    root = tk.Tk()
    root.title("番茄钟 + 任务看板")
    root.geometry("1400x900")
    root.minsize(1200, 700)
    
    # 设置DPI感知
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 创建主窗口
    app = MainWindow(root)
    
    # 启动应用
    root.mainloop()


if __name__ == "__main__":
    main()
