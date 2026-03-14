"""
看板视图 - 任务看板界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Optional

from models.kanban_board import KanbanBoard
from models.task import Task
from data.repository import TaskRepository
from config import PRIORITY_LEVELS, DEFAULT_TAGS


class KanbanView:
    """看板视图"""
    
    def __init__(
        self,
        parent: tk.Widget,
        board: KanbanBoard,
        repository: TaskRepository,
        on_start_timer: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self.board = board
        self.repository = repository
        self.on_start_timer = on_start_timer
        
        self.frame = tk.Frame(parent, bg="#f5f6fa")
        self.columns_frames = {}
        self.tasks_frames = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 顶部工具栏
        self.toolbar = tk.Frame(self.frame, bg="#ffffff", height=50)
        self.toolbar.pack(fill=tk.X, pady=(0, 10))
        self.toolbar.pack_propagate(False)
        
        # 标题
        title_label = tk.Label(
            self.toolbar,
            text="任务看板",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#ffffff",
            fg="#2d3436",
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # 添加任务按钮
        add_btn = tk.Button(
            self.toolbar,
            text="+ 新建任务",
            font=("Microsoft YaHei", 10),
            bg="#00b894",
            fg="white",
            activebackground="#00a885",
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self._on_add_task,
        )
        add_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # 看板容器（带滚动条）
        self.canvas_container = tk.Frame(self.frame, bg="#f5f6fa")
        self.canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="#f5f6fa", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.canvas_container,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 看板内容框架
        self.board_frame = tk.Frame(self.canvas, bg="#f5f6fa")
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.board_frame,
            anchor=tk.NW,
        )
        
        # 绑定事件
        self.board_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
    
    def _on_frame_configure(self, event=None):
        """框架大小改变时更新canvas滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Canvas大小改变时更新内部框架宽度"""
        min_width = len(self.board.columns) * 320
        width = max(event.width, min_width)
        self.canvas.itemconfig(self.canvas_window, width=width)
    
    def _create_column(self, column):
        """创建看板列"""
        col_frame = tk.Frame(self.board_frame, bg="#dfe6e9", width=300)
        col_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        col_frame.pack_propagate(False)
        
        # 列标题
        header = tk.Frame(col_frame, bg=column.color, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header,
            text=column.name,
            font=("Microsoft YaHei", 12, "bold"),
            bg=column.color,
            fg="white",
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        # 任务数量
        tasks = self.board.get_tasks_by_column(column.id)
        count_label = tk.Label(
            header,
            text=str(len(tasks)),
            font=("Microsoft YaHei", 10),
            bg=column.color,
            fg="white",
        )
        count_label.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # 任务列表容器
        tasks_container = tk.Frame(col_frame, bg="#dfe6e9")
        tasks_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.columns_frames[column.id] = {
            "frame": col_frame,
            "tasks_container": tasks_container,
            "count_label": count_label,
        }
        
        # 渲染任务
        self._render_column_tasks(column.id, tasks_container)
    
    def _render_column_tasks(self, column_id: str, container: tk.Frame):
        """渲染列中的任务"""
        # 清除旧的任务卡片
        for widget in container.winfo_children():
            widget.destroy()
        
        tasks = self.board.get_tasks_by_column(column_id)
        
        for task in tasks:
            self._create_task_card(container, task)
    
    def _create_task_card(self, parent: tk.Frame, task: Task):
        """创建任务卡片"""
        # 卡片框架
        card = tk.Frame(
            parent,
            bg="white",
            highlightbackground="#dfe6e9",
            highlightthickness=1,
        )
        card.pack(fill=tk.X, pady=3, padx=2)
        
        # 优先级颜色条
        priority_color = PRIORITY_LEVELS.get(task.priority, {}).get("color", "#747d8c")
        priority_bar = tk.Frame(card, bg=priority_color, width=4)
        priority_bar.pack(side=tk.LEFT, fill=tk.Y)
        
        # 内容区
        content = tk.Frame(card, bg="white", padx=8, pady=8)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 任务标题
        title_label = tk.Label(
            content,
            text=task.title,
            font=("Microsoft YaHei", 11),
            bg="white",
            fg="#2d3436",
            wraplength=230,
            justify=tk.LEFT,
        )
        title_label.pack(anchor=tk.W)
        
        # 底部信息
        footer = tk.Frame(content, bg="white")
        footer.pack(fill=tk.X, pady=(5, 0))
        
        # 番茄数
        actual = task.get_actual_pomodoro_count()
        estimated = task.estimated_pomodoros
        pomodoro_text = f"🍅 {actual}/{estimated}"
        pomodoro_label = tk.Label(
            footer,
            text=pomodoro_text,
            font=("Microsoft YaHei", 9),
            bg="white",
            fg="#636e72" if actual < estimated else "#00b894",
        )
        pomodoro_label.pack(side=tk.LEFT)
        
        # 截止日期
        if task.due_date:
            due_text = task.due_date.strftime("%m/%d")
            due_color = "#ff4757" if task.is_overdue() else "#636e72"
            due_label = tk.Label(
                footer,
                text=f"📅 {due_text}",
                font=("Microsoft YaHei", 9),
                bg="white",
                fg=due_color,
            )
            due_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 操作按钮
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 开始番茄钟按钮
        if task.column_id != "done":
            start_btn = tk.Label(
                btn_frame,
                text="▶ 开始",
                font=("Microsoft YaHei", 9),
                bg="#74b9ff",
                fg="white",
                padx=8,
                pady=2,
                cursor="hand2",
            )
            start_btn.pack(side=tk.LEFT)
            start_btn.bind("<Button-1>", lambda e, tid=task.id: self._on_start_timer(tid))
        
        # 编辑按钮
        edit_btn = tk.Label(
            btn_frame,
            text="✏️",
            font=("Microsoft YaHei", 9),
            bg="white",
            fg="#636e72",
            cursor="hand2",
        )
        edit_btn.pack(side=tk.RIGHT)
        edit_btn.bind("<Button-1>", lambda e, t=task: self._on_edit_task(t))
        
        # 存储引用
        self.tasks_frames[task.id] = card
    
    def _on_add_task(self):
        """添加新任务"""
        from .components.task_dialog import TaskDialog
        dialog = TaskDialog(self.parent, "新建任务")
        if dialog.result:
            task = self.board.create_task(
                title=dialog.result["title"],
                column_id="todo",
            )
            if task:
                task.description = dialog.result.get("description", "")
                task.estimated_pomodoros = dialog.result.get("estimated_pomodoros", 1)
                task.priority = dialog.result.get("priority", "not_urgent_important")
                task.tags = dialog.result.get("tags", [])
                if dialog.result.get("due_date"):
                    from datetime import date
                    task.due_date = date.fromisoformat(dialog.result["due_date"])
                
                self.repository.save_task(task)
                self.refresh()
    
    def _on_edit_task(self, task: Task):
        """编辑任务"""
        from .components.task_dialog import TaskDialog
        dialog = TaskDialog(self.parent, "编辑任务", task)
        if dialog.result:
            task.title = dialog.result["title"]
            task.description = dialog.result.get("description", "")
            task.estimated_pomodoros = dialog.result.get("estimated_pomodoros", 1)
            task.priority = dialog.result.get("priority", "not_urgent_important")
            task.tags = dialog.result.get("tags", [])
            if dialog.result.get("due_date"):
                from datetime import date
                task.due_date = date.fromisoformat(dialog.result["due_date"])
            else:
                task.due_date = None
            
            self.repository.save_task(task)
            self.refresh()
    
    def _on_start_timer(self, task_id: str):
        """开始番茄钟"""
        if self.on_start_timer:
            self.on_start_timer(task_id)
    
    def refresh(self):
        """刷新看板"""
        # 清除现有列
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        
        self.columns_frames.clear()
        self.tasks_frames.clear()
        
        # 重新创建列
        for column in self.board.columns:
            self._create_column(column)
        
        # 更新滚动区域
        self.board_frame.update_idletasks()
        self._on_frame_configure()
    
    def show(self):
        """显示视图"""
        self.refresh()
        self.frame.pack(fill=tk.BOTH, expand=True)
    
    def hide(self):
        """隐藏视图"""
        self.frame.pack_forget()
