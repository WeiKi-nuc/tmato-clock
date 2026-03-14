"""
番茄钟视图 - 计时器界面
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from core.pomodoro_timer import PomodoroTimer, TimerState, TimerType
from models.kanban_board import KanbanBoard
from models.task import Task
from data.repository import TaskRepository
from config import TIMER_PRESETS


class TimerView:
    """番茄钟视图"""
    
    def __init__(
        self,
        parent: tk.Widget,
        timer: PomodoroTimer,
        board: KanbanBoard,
        repository: TaskRepository,
    ):
        self.parent = parent
        self.timer = timer
        self.board = board
        self.repository = repository
        self.current_task: Optional[Task] = None
        
        self.frame = tk.Frame(parent, bg="#f5f6fa")
        
        # 绑定计时器事件
        self.timer.on_tick(self._on_timer_tick)
        self.timer.on_state_change(self._on_state_change)
        self.timer.on_complete(self._on_timer_complete)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 主容器
        main_container = tk.Frame(self.frame, bg="#f5f6fa")
        main_container.pack(expand=True)
        
        # 任务选择区
        self.task_frame = tk.Frame(main_container, bg="#f5f6fa")
        self.task_frame.pack(pady=20)
        
        tk.Label(
            self.task_frame,
            text="当前任务",
            font=("Microsoft YaHei", 12),
            bg="#f5f6fa",
            fg="#636e72",
        ).pack()
        
        self.task_label = tk.Label(
            self.task_frame,
            text="未选择任务",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#f5f6fa",
            fg="#2d3436",
        )
        self.task_label.pack(pady=5)
        
        # 选择任务按钮
        self.select_task_btn = tk.Button(
            self.task_frame,
            text="选择任务",
            font=("Microsoft YaHei", 10),
            bg="#74b9ff",
            fg="white",
            bd=0,
            padx=15,
            pady=5,
            command=self._on_select_task,
        )
        self.select_task_btn.pack()
        
        # 计时器显示区
        self.timer_frame = tk.Frame(main_container, bg="#f5f6fa")
        self.timer_frame.pack(pady=30)
        
        # 状态标签
        self.state_label = tk.Label(
            self.timer_frame,
            text="准备开始",
            font=("Microsoft YaHei", 14),
            bg="#f5f6fa",
            fg="#636e72",
        )
        self.state_label.pack()
        
        # 时间显示
        self.time_label = tk.Label(
            self.timer_frame,
            text="25:00",
            font=("Microsoft YaHei", 72, "bold"),
            bg="#f5f6fa",
            fg="#2d3436",
        )
        self.time_label.pack(pady=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.timer_frame,
            variable=self.progress_var,
            maximum=100,
            length=300,
            mode="determinate",
        )
        self.progress_bar.pack(pady=10)
        
        # 控制按钮区
        self.controls_frame = tk.Frame(main_container, bg="#f5f6fa")
        self.controls_frame.pack(pady=20)
        
        # 开始/暂停按钮
        self.start_btn = tk.Button(
            self.controls_frame,
            text="▶ 开始专注",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#00b894",
            fg="white",
            activebackground="#00a885",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self._on_start,
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # 暂停按钮
        self.pause_btn = tk.Button(
            self.controls_frame,
            text="⏸ 暂停",
            font=("Microsoft YaHei", 12),
            bg="#fdcb6e",
            fg="#2d3436",
            activebackground="#f1c40f",
            bd=0,
            padx=25,
            pady=12,
            cursor="hand2",
            command=self._on_pause,
            state=tk.DISABLED,
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮
        self.stop_btn = tk.Button(
            self.controls_frame,
            text="⏹ 停止",
            font=("Microsoft YaHei", 12),
            bg="#ff6b6b",
            fg="white",
            activebackground="#ee5a5a",
            bd=0,
            padx=25,
            pady=12,
            cursor="hand2",
            command=self._on_stop,
            state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 中断记录按钮
        self.interrupt_btn = tk.Button(
            self.controls_frame,
            text="⚠️ 记录中断",
            font=("Microsoft YaHei", 12),
            bg="#e17055",
            fg="white",
            activebackground="#d63031",
            bd=0,
            padx=20,
            pady=12,
            cursor="hand2",
            command=self._on_record_interruption,
            state=tk.DISABLED,
        )
        self.interrupt_btn.pack(side=tk.LEFT, padx=5)
        
        # 设置区
        self.settings_frame = tk.Frame(main_container, bg="#f5f6fa")
        self.settings_frame.pack(pady=20)
        
        tk.Label(
            self.settings_frame,
            text="时长预设",
            font=("Microsoft YaHei", 11),
            bg="#f5f6fa",
            fg="#636e72",
        ).pack()
        
        self.preset_var = tk.StringVar(value="标准番茄")
        preset_frame = tk.Frame(self.settings_frame, bg="#f5f6fa")
        preset_frame.pack(pady=5)
        
        for preset_name in TIMER_PRESETS.keys():
            rb = tk.Radiobutton(
                preset_frame,
                text=preset_name,
                variable=self.preset_var,
                value=preset_name,
                font=("Microsoft YaHei", 10),
                bg="#f5f6fa",
                command=self._on_preset_change,
            )
            rb.pack(side=tk.LEFT, padx=10)
        
        # 统计信息
        self.stats_frame = tk.Frame(main_container, bg="#f5f6fa")
        self.stats_frame.pack(pady=20)
        
        self.stats_label = tk.Label(
            self.stats_frame,
            text="今日完成: 0 个番茄",
            font=("Microsoft YaHei", 12),
            bg="#f5f6fa",
            fg="#636e72",
        )
        self.stats_label.pack()
        
        # 提示信息
        self.tip_label = tk.Label(
            main_container,
            text="💡 提示: 专注时保持单一任务，避免多任务切换",
            font=("Microsoft YaHei", 10),
            bg="#f5f6fa",
            fg="#b2bec3",
            wraplength=400,
        )
        self.tip_label.pack(pady=20)
    
    def _on_select_task(self):
        """选择任务"""
        from .components.task_selector import TaskSelector
        selector = TaskSelector(self.parent, self.board)
        if selector.selected_task_id:
            task = self.board.get_task(selector.selected_task_id)
            if task:
                self.set_task(task)
    
    def set_task(self, task: Task):
        """设置当前任务"""
        self.current_task = task
        self.task_label.config(text=task.title)
        self.timer.current_task = task
    
    def _on_preset_change(self):
        """预设改变"""
        preset_name = self.preset_var.get()
        if preset_name in TIMER_PRESETS:
            self.timer.update_settings(TIMER_PRESETS[preset_name])
            # 更新显示
            if self.timer.state == TimerState.IDLE:
                focus_duration = TIMER_PRESETS[preset_name]["focus_duration"]
                self.time_label.config(text=f"{focus_duration:02d}:00")
    
    def _on_start(self):
        """开始计时"""
        if not self.current_task:
            messagebox.showwarning("提示", "请先选择一个任务")
            return
        
        if self.timer.state == TimerState.PAUSED:
            self.timer.resume()
        else:
            self.timer.start(self.current_task, TimerType.FOCUS)
    
    def start_focus(self):
        """外部调用：开始专注"""
        self._on_start()
    
    def _on_pause(self):
        """暂停"""
        self.timer.pause()
    
    def _on_stop(self):
        """停止"""
        if messagebox.askyesno("确认", "确定要停止当前番茄钟吗？"):
            self.timer.stop("用户手动停止")
    
    def _on_record_interruption(self):
        """记录中断"""
        from .components.interruption_dialog import InterruptionDialog
        dialog = InterruptionDialog(self.parent)
        if dialog.result:
            self.timer.record_interruption(
                dialog.result["type"],
                dialog.result.get("note", "")
            )
            messagebox.showinfo("提示", "中断已记录")
    
    def _on_timer_tick(self, remaining: int, total: int):
        """计时器每秒回调"""
        minutes = remaining // 60
        seconds = remaining % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        progress = ((total - remaining) / total) * 100 if total > 0 else 0
        self.progress_var.set(progress)
    
    def _on_state_change(self, new_state: TimerState, old_state: TimerState):
        """状态变化回调"""
        state_texts = {
            TimerState.IDLE: "准备开始",
            TimerState.FOCUS: "专注中...",
            TimerState.SHORT_BREAK: "短休息",
            TimerState.LONG_BREAK: "长休息",
            TimerState.PAUSED: "已暂停",
        }
        
        self.state_label.config(text=state_texts.get(new_state, "未知状态"))
        
        # 更新按钮状态
        if new_state == TimerState.IDLE:
            self.start_btn.config(state=tk.NORMAL, text="▶ 开始专注")
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.interrupt_btn.config(state=tk.DISABLED)
            self.select_task_btn.config(state=tk.NORMAL)
            self.time_label.config(fg="#2d3436")
        
        elif new_state == TimerState.FOCUS:
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.interrupt_btn.config(state=tk.NORMAL)
            self.select_task_btn.config(state=tk.DISABLED)
            self.time_label.config(fg="#00b894")
        
        elif new_state == TimerState.PAUSED:
            self.start_btn.config(state=tk.NORMAL, text="▶ 继续")
            self.pause_btn.config(state=tk.DISABLED)
            self.time_label.config(fg="#fdcb6e")
        
        elif new_state in [TimerState.SHORT_BREAK, TimerState.LONG_BREAK]:
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.interrupt_btn.config(state=tk.DISABLED)
            self.time_label.config(fg="#74b9ff")
    
    def _on_timer_complete(self):
        """计时完成回调"""
        # 播放提示音
        self._play_notification_sound()
        
        # 显示完成提示
        if self.timer.timer_type == TimerType.FOCUS:
            messagebox.showinfo("番茄完成", "恭喜！专注时间结束，休息一下吧~")
            
            # 保存数据
            if self.current_task:
                self.repository.save_task(self.current_task)
                self._update_stats()
            
            # 询问是否开始休息
            next_type = self.timer.get_next_timer_type()
            if next_type == TimerType.LONG_BREAK:
                if messagebox.askyesno("长休息", "已完成4个番茄，开始长休息（15分钟）？"):
                    self.timer.start(None, TimerType.LONG_BREAK)
            else:
                if messagebox.askyesno("短休息", "开始短休息（5分钟）？"):
                    self.timer.start(None, TimerType.SHORT_BREAK)
        else:
            messagebox.showinfo("休息结束", "休息结束，准备开始新的番茄！")
    
    def _play_notification_sound(self):
        """播放提示音"""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except:
            pass
    
    def _update_stats(self):
        """更新统计信息"""
        count = self.timer.completed_pomodoros_count
        self.stats_label.config(text=f"今日完成: {count} 个番茄")
    
    def show(self):
        """显示视图"""
        self.frame.pack(fill=tk.BOTH, expand=True)
        self._update_stats()
    
    def hide(self):
        """隐藏视图"""
        self.frame.pack_forget()
