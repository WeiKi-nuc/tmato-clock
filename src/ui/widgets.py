import tkinter as tk
from tkinter import ttk
import math
from typing import Callable


class CircularTimer(tk.Canvas):
    def __init__(self, parent, size: int = 200, **kwargs):
        super().__init__(parent, width=size, height=size, **kwargs)
        self.size = size
        self.center = size // 2
        self.radius = size // 2 - 10
        self.progress = 0
        self.configure(bg='white', highlightthickness=0)
        
    def set_progress(self, percentage: float, remaining_text: str = ""):
        self.delete("all")
        
        self.create_oval(
            self.center - self.radius,
            self.center - self.radius,
            self.center + self.radius,
            self.center + self.radius,
            fill='#f0f0f0',
            outline='#e0e0e0',
            width=2
        )
        
        if percentage > 0:
            angle = percentage * 3.6
            start_angle = 90
            end_angle = start_angle - angle
            
            self.create_arc(
                self.center - self.radius + 5,
                self.center - self.radius + 5,
                self.center + self.radius - 5,
                self.center + self.radius - 5,
                start=start_angle,
                extent=-angle,
                fill='#4CAF50',
                outline='',
                style='pieslice'
            )
        
        self.create_text(
            self.center,
            self.center - 20,
            text=remaining_text,
            font=('Arial', 36, 'bold'),
            fill='#333333'
        )


class TaskCard(tk.Frame):
    def __init__(self, parent, task, on_click: Callable = None, on_move: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.task = task
        self.on_click = on_click
        self.on_move = on_move
        
        self.configure(bg='white', bd=1, relief=tk.RAISED)
        
        title_frame = tk.Frame(self, bg='white')
        title_frame.pack(fill=tk.X, padx=8, pady=4)
        
        title_label = tk.Label(
            title_frame,
            text=task.title,
            bg='white',
            font=('Arial', 10, 'bold'),
            wraplength=180
        )
        title_label.pack(anchor=tk.W)
        
        info_frame = tk.Frame(self, bg='white')
        info_frame.pack(fill=tk.X, padx=8, pady=2)
        
        pomo_count = len(task.completed_pomodoros)
        pomo_text = f"🍅 {pomo_count}/{task.estimated_pomodoros}" if task.estimated_pomodoros > 0 else f"🍅 {pomo_count}"
        
        pomo_label = tk.Label(
            info_frame,
            text=pomo_text,
            bg='white',
            font=('Arial', 9),
            fg='#666666'
        )
        pomo_label.pack(side=tk.LEFT)
        
        if task.tags:
            tag_frame = tk.Frame(self, bg='white')
            tag_frame.pack(fill=tk.X, padx=8, pady=2)
            
            for tag in task.tags[:3]:
                tag_label = tk.Label(
                    tag_frame,
                    text=tag,
                    bg='#e3f2fd',
                    fg='#1565c0',
                    font=('Arial', 8),
                    padx=4,
                    pady=1
                )
                tag_label.pack(side=tk.LEFT, padx=1)
        
        move_frame = tk.Frame(self, bg='white')
        move_frame.pack(fill=tk.X, padx=8, pady=2)
        
        for col in ['todo', 'in_progress', 'done']:
            if task.column_id != col:
                col_names = {'todo': '待办', 'in_progress': '进行中', 'done': '完成'}
                btn = tk.Button(
                    move_frame,
                    text=col_names[col],
                    font=('Arial', 7),
                    padx=3,
                    pady=1,
                    command=lambda c=col: self._move_to(c)
                )
                btn.pack(side=tk.LEFT, padx=1)
        
        self.bind("<Button-1>", self._on_click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._on_click)
        
    def _move_to(self, column_id):
        if self.on_move:
            self.on_move(self.task, column_id)
        
    def _on_click(self, event):
        if self.on_click:
            self.on_click(self.task)


class KanbanColumnWidget(tk.Frame):
    def __init__(self, parent, column, on_task_click: Callable = None, on_task_move: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.column = column
        self.on_task_click = on_task_click
        self.on_task_move = on_task_move
        self.task_widgets = {}
        
        self.configure(bg='#f5f5f5')
        
        header = tk.Frame(self, bg=column.color, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header,
            text=column.name,
            bg=column.color,
            font=('Arial', 12, 'bold'),
            fg='white'
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        self.tasks_container = tk.Frame(self, bg='#f5f5f5')
        self.tasks_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
    def add_task(self, task):
        card = TaskCard(
            self.tasks_container,
            task,
            on_click=self.on_task_click,
            on_move=self.on_task_move,
            width=200,
            height=100
        )
        card.pack(fill=tk.X, pady=2)
        card.pack_propagate(False)
        self.task_widgets[task.id] = card
        
    def clear_tasks(self):
        for widget in self.task_widgets.values():
            widget.destroy()
        self.task_widgets.clear()
