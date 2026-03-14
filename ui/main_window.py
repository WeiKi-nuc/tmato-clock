"""
主窗口 - 应用程序主界面
"""
import tkinter as tk
from tkinter import ttk, messagebox

from data.repository import TaskRepository
from models.kanban_board import KanbanBoard
from core.pomodoro_timer import PomodoroTimer

from .kanban_view import KanbanView
from .timer_view import TimerView
from .stats_view import StatsView
from .components.sidebar import Sidebar


class MainWindow:
    """主窗口类"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.configure(bg="#f5f6fa")
        
        # 初始化数据
        self.repository = TaskRepository()
        self.board = self.repository.load_board()
        self.timer = PomodoroTimer()
        
        # 当前视图
        self.current_view = None
        
        # 创建UI
        self._create_widgets()
        self._setup_layout()
        
        # 显示看板视图
        self.show_kanban_view()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """创建UI组件"""
        # 侧边栏
        self.sidebar = Sidebar(
            self.root,
            on_kanban_click=self.show_kanban_view,
            on_timer_click=self.show_timer_view,
            on_stats_click=self.show_stats_view,
        )
        
        # 主内容区容器
        self.content_frame = tk.Frame(self.root, bg="#f5f6fa")
        
        # 视图实例
        self.kanban_view = KanbanView(
            self.content_frame,
            self.board,
            self.repository,
            on_start_timer=self._on_start_timer_from_task,
        )
        
        self.timer_view = TimerView(
            self.content_frame,
            self.timer,
            self.board,
            self.repository,
        )
        
        self.stats_view = StatsView(
            self.content_frame,
            self.repository,
        )
    
    def _setup_layout(self):
        """设置布局"""
        # 侧边栏
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # 内容区
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def show_kanban_view(self):
        """切换到看板视图"""
        self._hide_all_views()
        self.kanban_view.show()
        self.current_view = "kanban"
        self.sidebar.set_active_button("kanban")
    
    def show_timer_view(self):
        """切换到番茄钟视图"""
        self._hide_all_views()
        self.timer_view.show()
        self.current_view = "timer"
        self.sidebar.set_active_button("timer")
    
    def show_stats_view(self):
        """切换到统计视图"""
        self._hide_all_views()
        self.stats_view.show()
        self.current_view = "stats"
        self.sidebar.set_active_button("stats")
    
    def _hide_all_views(self):
        """隐藏所有视图"""
        self.kanban_view.hide()
        self.timer_view.hide()
        self.stats_view.hide()
    
    def _on_start_timer_from_task(self, task_id: str):
        """从任务开始计时"""
        task = self.board.get_task(task_id)
        if task:
            self.timer_view.set_task(task)
            self.show_timer_view()
            self.timer_view.start_focus()
    
    def _on_close(self):
        """窗口关闭处理"""
        # 保存数据
        self.repository.save_board(self.board)
        
        # 停止计时器
        if self.timer.state.value in ["FOCUS", "SHORT_BREAK", "LONG_BREAK", "PAUSED"]:
            if messagebox.askyesno("确认", "番茄钟正在运行，确定要退出吗？"):
                self.timer.stop("应用退出")
            else:
                return
        
        self.root.destroy()
