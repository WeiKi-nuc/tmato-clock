"""
中断记录对话框
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any


class InterruptionDialog:
    """中断记录对话框"""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.result: Optional[Dict[str, Any]] = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("记录中断")
        self.dialog.geometry("350x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # 等待对话框关闭
        self.parent.wait_window(self.dialog)
    
    def _create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        tk.Label(
            main_frame,
            text="记录中断",
            font=("Microsoft YaHei", 14, "bold"),
        ).pack(pady=(0, 15))
        
        # 中断类型
        tk.Label(
            main_frame,
            text="中断类型",
            font=("Microsoft YaHei", 11),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 5))
        
        self.interruption_type = tk.StringVar(value="internal")
        
        type_frame = tk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(
            type_frame,
            text="内部中断（走神、分心）",
            variable=self.interruption_type,
            value="internal",
            font=("Microsoft YaHei", 10),
        ).pack(anchor=tk.W)
        
        tk.Radiobutton(
            type_frame,
            text="外部中断（被打扰）",
            variable=self.interruption_type,
            value="external",
            font=("Microsoft YaHei", 10),
        ).pack(anchor=tk.W)
        
        # 备注
        tk.Label(
            main_frame,
            text="备注（可选）",
            font=("Microsoft YaHei", 11),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(10, 5))
        
        self.note_entry = tk.Entry(
            main_frame,
            font=("Microsoft YaHei", 10),
        )
        self.note_entry.pack(fill=tk.X, pady=(0, 15))
        
        # 按钮
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            btn_frame,
            text="取消",
            font=("Microsoft YaHei", 10),
            width=10,
            command=self.dialog.destroy,
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="记录",
            font=("Microsoft YaHei", 10),
            width=10,
            bg="#e17055",
            fg="white",
            command=self._on_save,
        ).pack(side=tk.RIGHT, padx=5)
    
    def _on_save(self):
        """保存"""
        self.result = {
            "type": self.interruption_type.get(),
            "note": self.note_entry.get().strip(),
        }
        self.dialog.destroy()
