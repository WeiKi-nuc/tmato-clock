import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, Any

import time
from ..core.timer import PomodoroTimer, TimerState
from ..core.task import PomodoroRecord
from ..core.kanban import KanbanBoard
from ..storage.repository import TaskRepository
from .widgets import CircularTimer, KanbanColumnWidget


class PomodoroApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("番茄钟 + 任务看板")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        self.repository = TaskRepository()
        self.timer = PomodoroTimer()
        self.board = KanbanBoard()
        
        self._load_tasks()
        self._setup_ui()
        self._bind_events()
        
        self.timer.on_tick(self._on_timer_tick)
        self.timer.on_state_change(self._on_timer_state_change)
        
    def _load_tasks(self):
        tasks = self.repository.get_all_tasks()
        self.board.tasks = tasks
        
    def _setup_ui(self):
        self.main_container = tk.Frame(self.root, bg='#f0f0f0')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self._setup_timer_panel()
        self._setup_kanban_view()
        
    def _setup_timer_panel(self):
        timer_frame = tk.Frame(self.main_container, bg='white', height=200, bd=1, relief=tk.SUNKEN)
        timer_frame.pack(fill=tk.X, pady=10, padx=10)
        timer_frame.pack_propagate(False)
        
        left_panel = tk.Frame(timer_frame, bg='white')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.timer_display = CircularTimer(left_panel, size=180)
        self.timer_display.pack(side=tk.LEFT, padx=10)
        
        info_panel = tk.Frame(left_panel, bg='white')
        info_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        self.status_label = tk.Label(
            info_panel,
            text="空闲状态",
            bg='white',
            font=('Arial', 14, 'bold')
        )
        self.status_label.pack(anchor=tk.W, pady=5)
        
        self.current_task_label = tk.Label(
            info_panel,
            text="未选择任务",
            bg='white',
            font=('Arial', 12),
            fg='#666',
            wraplength=300
        )
        self.current_task_label.pack(anchor=tk.W, pady=5)
        
        button_panel = tk.Frame(info_panel, bg='white')
        button_panel.pack(anchor=tk.W, pady=10)
        
        self.start_btn = tk.Button(
            button_panel,
            text="开始专注",
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=5,
            command=self._start_focus
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = tk.Button(
            button_panel,
            text="暂停",
            bg='#FF9800',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=5,
            command=self._pause_timer,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            button_panel,
            text="停止",
            bg='#f44336',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=5,
            command=self._stop_timer,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
    def _setup_kanban_view(self):
        kanban_container = tk.Frame(self.main_container, bg='#f0f0f0')
        kanban_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        toolbar = tk.Frame(kanban_container, bg='white', height=50, bd=1, relief=tk.SUNKEN)
        toolbar.pack(fill=tk.X, pady=5)
        toolbar.pack_propagate(False)
        
        add_task_btn = tk.Button(
            toolbar,
            text="+ 新建任务",
            bg='#2196F3',
            fg='white',
            font=('Arial', 10),
            padx=10,
            pady=5,
            command=self._add_new_task
        )
        add_task_btn.pack(side=tk.LEFT, padx=10, pady=8)
        
        self.kanban_frame = tk.Frame(kanban_container, bg='#f0f0f0')
        self.kanban_frame.pack(fill=tk.BOTH, expand=True)
        
        self.column_widgets: Dict[str, KanbanColumnWidget] = {}
        self._refresh_kanban()
        
    def _refresh_kanban(self):
        for widget in self.kanban_frame.winfo_children():
            widget.destroy()
        self.column_widgets.clear()
        
        for i, column in enumerate(self.board.columns):
            col_widget = KanbanColumnWidget(
                self.kanban_frame,
                column,
                on_task_click=self._on_task_click,
                on_task_move=self._on_task_move
            )
            col_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            self.column_widgets[column.id] = col_widget
            
            tasks = self.board.get_tasks_by_column(column.id)
            for task in tasks:
                col_widget.add_task(task)
                
    def _bind_events(self):
        pass
        
    def _on_timer_tick(self, remaining: int):
        minutes = remaining // 60
        seconds = remaining % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        self.root.after(0, lambda: self.timer_display.set_progress(
            self.timer.get_progress_percentage(),
            time_str
        ))
        
    def _on_timer_state_change(self, state, **kwargs):
        state_texts = {
            TimerState.IDLE: "空闲状态",
            TimerState.FOCUS: "专注中",
            TimerState.SHORT_BREAK: "短休息中",
            TimerState.LONG_BREAK: "长休息中",
            TimerState.PAUSED: "已暂停"
        }
        
        text = state_texts.get(state, str(state))
        self.root.after(0, lambda: self.status_label.config(text=text))
        
        if kwargs.get('completed', False):
            self.root.after(0, self._on_timer_complete)
            
        self._update_button_states()
        
    def _update_button_states(self):
        if self.timer.state == TimerState.IDLE:
            self.start_btn.config(state=tk.NORMAL, text="开始专注")
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
        elif self.timer.state == TimerState.PAUSED:
            self.start_btn.config(state=tk.NORMAL, text="继续")
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            
    def _start_focus(self):
        if not hasattr(self, 'selected_task') or self.selected_task is None:
            messagebox.showinfo("提示", "请先从看板选择一个任务")
            return
            
        if self.timer.state == TimerState.PAUSED:
            self.timer.resume()
        else:
            self.timer.start(self.selected_task, TimerState.FOCUS)
            
    def _pause_timer(self):
        self.timer.pause()
        
    def _stop_timer(self):
        self.timer.stop()
        self.timer_display.set_progress(0, "00:00")
        
    def _on_timer_complete(self):
        if hasattr(self, 'selected_task') and self.selected_task:
            record = PomodoroRecord(
                task_id=self.selected_task.id,
                started_at=time.time() - self.timer.settings.get('focus', 25*60),
                ended_at=time.time(),
                planned_duration=self.timer.settings.get('focus', 25*60),
                actual_duration=self.timer.settings.get('focus', 25*60),
                completion_type="completed"
            )
            self.selected_task.add_pomodoro(record)
            self.repository.save_task(self.selected_task)
            self._refresh_kanban()
        
        messagebox.showinfo("番茄钟完成", "恭喜你完成了一个番茄钟！")
        self.timer_display.set_progress(0, "00:00")
        
    def _on_task_click(self, task):
        self.selected_task = task
        self.current_task_label.config(text=f"当前任务: {task.title}")
        
    def _on_task_move(self, task, target_column):
        self.board.move_task(task.id, target_column)
        task.move_to(target_column)
        self.repository.save_task(task)
        self._refresh_kanban()
        
    def _add_new_task(self):
        title = simpledialog.askstring("新建任务", "请输入任务标题:")
        if title:
            task = self.board.create_task(title)
            self.repository.save_task(task)
            self._refresh_kanban()
            
    def run(self):
        self.root.mainloop()
