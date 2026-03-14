"""
侧边栏组件
"""
import tkinter as tk
from tkinter import ttk


class Sidebar(tk.Frame):
    """侧边栏导航"""
    
    def __init__(
        self,
        parent,
        on_kanban_click=None,
        on_timer_click=None,
        on_stats_click=None,
        **kwargs
    ):
        super().__init__(parent, bg="#2d3436", width=200, **kwargs)
        
        self.on_kanban_click = on_kanban_click
        self.on_timer_click = on_timer_click
        self.on_stats_click = on_stats_click
        
        self.buttons = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建组件"""
        # 标题
        title_label = tk.Label(
            self,
            text="番茄钟+看板",
            font=("Microsoft YaHei", 16, "bold"),
            bg="#2d3436",
            fg="#dfe6e9",
            pady=20,
        )
        title_label.pack(fill=tk.X)
        
        # 分隔线
        separator = tk.Frame(self, height=2, bg="#636e72")
        separator.pack(fill=tk.X, padx=15, pady=10)
        
        # 导航按钮
        self._create_nav_button("kanban", "📋 看板", self._on_kanban_click)
        self._create_nav_button("timer", "⏱️ 番茄钟", self._on_timer_click)
        self._create_nav_button("stats", "📊 统计", self._on_stats_click)
        
        # 底部填充
        tk.Frame(self, bg="#2d3436").pack(fill=tk.BOTH, expand=True)
        
        # 版本信息
        version_label = tk.Label(
            self,
            text="v1.0.0",
            font=("Microsoft YaHei", 9),
            bg="#2d3436",
            fg="#b2bec3",
            pady=10,
        )
        version_label.pack(fill=tk.X)
    
    def _create_nav_button(self, key: str, text: str, command):
        """创建导航按钮"""
        btn = tk.Button(
            self,
            text=text,
            font=("Microsoft YaHei", 12),
            bg="#2d3436",
            fg="#dfe6e9",
            activebackground="#636e72",
            activeforeground="#ffffff",
            bd=0,
            padx=20,
            pady=12,
            anchor=tk.W,
            cursor="hand2",
            command=command,
        )
        btn.pack(fill=tk.X, padx=10, pady=2)
        self.buttons[key] = btn
    
    def _on_kanban_click(self):
        """看板按钮点击"""
        if self.on_kanban_click:
            self.on_kanban_click()
    
    def _on_timer_click(self):
        """番茄钟按钮点击"""
        if self.on_timer_click:
            self.on_timer_click()
    
    def _on_stats_click(self):
        """统计按钮点击"""
        if self.on_stats_click:
            self.on_stats_click()
    
    def set_active_button(self, key: str):
        """设置活动按钮"""
        for k, btn in self.buttons.items():
            if k == key:
                btn.config(bg="#636e72", fg="#ffffff")
            else:
                btn.config(bg="#2d3436", fg="#dfe6e9")
