"""
任务选择器对话框
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.kanban_board import KanbanBoard


class TaskSelector:
    """任务选择对话框"""
    
    def __init__(self, parent: tk.Widget, board: KanbanBoard):
        self.parent = parent
        self.board = board
        self.selected_task_id: Optional[str] = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("选择任务")
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # 等待对话框关闭
        self.parent.wait_window(self.dialog)
    
    def _create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = tk.Frame(self.dialog, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        tk.Label(
            main_frame,
            text="选择一个任务开始番茄钟",
            font=("Microsoft YaHei", 12, "bold"),
        ).pack(pady=(0, 10))
        
        # 搜索框
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Entry(
            search_frame,
            font=("Microsoft YaHei", 10),
        ).pack(fill=tk.X)
        
        # 任务列表
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.task_listbox = tk.Listbox(
            list_frame,
            font=("Microsoft YaHei", 11),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            height=15,
        )
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.task_listbox.yview)
        
        # 加载任务
        self._load_tasks()
        
        # 绑定双击事件
        self.task_listbox.bind("<Double-Button-1>", self._on_select)
        
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
            text="选择",
            font=("Microsoft YaHei", 10),
            width=10,
            bg="#00b894",
            fg="white",
            command=self._on_select,
        ).pack(side=tk.RIGHT, padx=5)
    
    def _load_tasks(self):
        """加载任务列表"""
        self.task_ids = []
        
        # 先加载进行中的任务
        in_progress = self.board.get_tasks_by_column("in_progress")
        if in_progress:
            self.task_listbox.insert(tk.END, "=== 进行中 ===")
            for task in in_progress:
                display_text = f"  {task.title} ({task.get_actual_pomodoro_count()}/{task.estimated_pomodoros})"
                self.task_listbox.insert(tk.END, display_text)
                self.task_ids.append(task.id)
        
        # 再加载待办任务
        todo = self.board.get_tasks_by_column("todo")
        if todo:
            self.task_listbox.insert(tk.END, "=== 待办 ===")
            for task in todo:
                display_text = f"  {task.title} ({task.get_actual_pomodoro_count()}/{task.estimated_pomodoros})"
                self.task_listbox.insert(tk.END, display_text)
                self.task_ids.append(task.id)
        
        if not in_progress and not todo:
            self.task_listbox.insert(tk.END, "没有可用的任务")
    
    def _on_select(self, event=None):
        """选择任务"""
        selection = self.task_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        # 跳过标题行
        text = self.task_listbox.get(index)
        if text.startswith("==="):
            return
        
        # 计算实际的任务索引
        task_index = 0
        for i in range(index + 1):
            if not self.task_listbox.get(i).startswith("==="):
                task_index += 1
        
        if task_index > 0 and task_index <= len(self.task_ids):
            self.selected_task_id = self.task_ids[task_index - 1]
            self.dialog.destroy()
