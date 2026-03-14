"""
任务编辑对话框
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Dict, Any, List

from models.task import Task
from config import PRIORITY_LEVELS, DEFAULT_TAGS


class TaskDialog:
    """任务编辑对话框"""
    
    def __init__(self, parent: tk.Widget, title: str, task: Optional[Task] = None):
        self.parent = parent
        self.task = task
        self.result: Optional[Dict[str, Any]] = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        if task:
            self._load_task_data()
        
        # 等待对话框关闭
        self.parent.wait_window(self.dialog)
    
    def _create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 任务标题
        tk.Label(
            main_frame,
            text="任务标题 *",
            font=("Microsoft YaHei", 10),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 5))
        
        self.title_entry = tk.Entry(
            main_frame,
            font=("Microsoft YaHei", 11),
        )
        self.title_entry.pack(fill=tk.X, pady=(0, 15))
        
        # 任务描述
        tk.Label(
            main_frame,
            text="描述",
            font=("Microsoft YaHei", 10),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 5))
        
        self.desc_text = tk.Text(
            main_frame,
            font=("Microsoft YaHei", 10),
            height=4,
            wrap=tk.WORD,
        )
        self.desc_text.pack(fill=tk.X, pady=(0, 15))
        
        # 预估番茄数
        tk.Label(
            main_frame,
            text="预估番茄数",
            font=("Microsoft YaHei", 10),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 5))
        
        self.pomodoro_var = tk.IntVar(value=1)
        pomodoro_frame = tk.Frame(main_frame)
        pomodoro_frame.pack(fill=tk.X, pady=(0, 15))
        
        for i in range(1, 9):
            rb = tk.Radiobutton(
                pomodoro_frame,
                text=str(i),
                variable=self.pomodoro_var,
                value=i,
                font=("Microsoft YaHei", 10),
            )
            rb.pack(side=tk.LEFT, padx=5)
        
        # 优先级
        tk.Label(
            main_frame,
            text="优先级",
            font=("Microsoft YaHei", 10),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 5))
        
        self.priority_var = tk.StringVar(value="not_urgent_important")
        priority_frame = tk.Frame(main_frame)
        priority_frame.pack(fill=tk.X, pady=(0, 15))
        
        priorities = [
            ("urgent_important", "紧急重要"),
            ("urgent_not_important", "紧急不重要"),
            ("not_urgent_important", "重要不紧急"),
            ("not_urgent_not_important", "不紧急不重要"),
        ]
        
        for key, name in priorities:
            rb = tk.Radiobutton(
                priority_frame,
                text=name,
                variable=self.priority_var,
                value=key,
                font=("Microsoft YaHei", 9),
            )
            rb.pack(side=tk.LEFT, padx=5)
        
        # 截止日期
        tk.Label(
            main_frame,
            text="截止日期",
            font=("Microsoft YaHei", 10),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 5))
        
        date_frame = tk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.has_due_date = tk.BooleanVar(value=False)
        self.due_date_check = tk.Checkbutton(
            date_frame,
            text="设置截止日期",
            variable=self.has_due_date,
            font=("Microsoft YaHei", 10),
            command=self._toggle_date_entry,
        )
        self.due_date_check.pack(side=tk.LEFT)
        
        # 日期输入
        self.date_frame = tk.Frame(date_frame)
        self.date_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        self.year_var = tk.StringVar(value=str(date.today().year))
        self.month_var = tk.StringVar(value=str(date.today().month))
        self.day_var = tk.StringVar(value=str(date.today().day))
        
        tk.Spinbox(
            self.date_frame,
            from_=2024,
            to=2030,
            width=6,
            textvariable=self.year_var,
        ).pack(side=tk.LEFT)
        tk.Label(self.date_frame, text="-").pack(side=tk.LEFT)
        tk.Spinbox(
            self.date_frame,
            from_=1,
            to=12,
            width=4,
            textvariable=self.month_var,
        ).pack(side=tk.LEFT)
        tk.Label(self.date_frame, text="-").pack(side=tk.LEFT)
        tk.Spinbox(
            self.date_frame,
            from_=1,
            to=31,
            width=4,
            textvariable=self.day_var,
        ).pack(side=tk.LEFT)
        
        self.date_frame.pack_forget()  # 默认隐藏
        
        # 标签
        tk.Label(
            main_frame,
            text="标签",
            font=("Microsoft YaHei", 10),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 5))
        
        self.tag_vars = {}
        tags_frame = tk.Frame(main_frame)
        tags_frame.pack(fill=tk.X, pady=(0, 15))
        
        for tag_info in DEFAULT_TAGS:
            var = tk.BooleanVar(value=False)
            self.tag_vars[tag_info["name"]] = var
            cb = tk.Checkbutton(
                tags_frame,
                text=tag_info["name"],
                variable=var,
                font=("Microsoft YaHei", 9),
            )
            cb.pack(side=tk.LEFT, padx=5)
        
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
            text="保存",
            font=("Microsoft YaHei", 10),
            width=10,
            bg="#00b894",
            fg="white",
            command=self._on_save,
        ).pack(side=tk.RIGHT, padx=5)
    
    def _toggle_date_entry(self):
        """切换日期输入显示"""
        if self.has_due_date.get():
            self.date_frame.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.date_frame.pack_forget()
    
    def _load_task_data(self):
        """加载任务数据"""
        if not self.task:
            return
        
        self.title_entry.insert(0, self.task.title)
        self.desc_text.insert("1.0", self.task.description)
        self.pomodoro_var.set(self.task.estimated_pomodoros)
        self.priority_var.set(self.task.priority)
        
        if self.task.due_date:
            self.has_due_date.set(True)
            self._toggle_date_entry()
            self.year_var.set(str(self.task.due_date.year))
            self.month_var.set(str(self.task.due_date.month))
            self.day_var.set(str(self.task.due_date.day))
        
        for tag in self.task.tags:
            if tag in self.tag_vars:
                self.tag_vars[tag].set(True)
    
    def _on_save(self):
        """保存"""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("警告", "请输入任务标题")
            return
        
        description = self.desc_text.get("1.0", tk.END).strip()
        estimated_pomodoros = self.pomodoro_var.get()
        priority = self.priority_var.get()
        
        due_date = None
        if self.has_due_date.get():
            try:
                due_date = date(
                    int(self.year_var.get()),
                    int(self.month_var.get()),
                    int(self.day_var.get()),
                ).isoformat()
            except ValueError:
                messagebox.showwarning("警告", "日期格式不正确")
                return
        
        tags = [name for name, var in self.tag_vars.items() if var.get()]
        
        self.result = {
            "title": title,
            "description": description,
            "estimated_pomodoros": estimated_pomodoros,
            "priority": priority,
            "due_date": due_date,
            "tags": tags,
        }
        
        self.dialog.destroy()
