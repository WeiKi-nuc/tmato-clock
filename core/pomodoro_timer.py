"""
番茄钟引擎 - 计时器核心逻辑与状态管理
"""
import threading
import time
from enum import Enum, auto
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from models.pomodoro_record import PomodoroRecord
from models.task import Task


class TimerState(Enum):
    """计时器状态"""
    IDLE = auto()           # 空闲
    FOCUS = auto()          # 专注中
    SHORT_BREAK = auto()    # 短休息
    LONG_BREAK = auto()     # 长休息
    PAUSED = auto()         # 暂停


class TimerType(Enum):
    """计时器类型"""
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroTimer:
    """番茄钟引擎"""
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        # 设置
        self.settings = settings or {
            "focus_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "pomodoros_until_long_break": 4,
            "auto_start_breaks": False,
            "auto_start_pomodoros": False,
            "strict_mode": False,
        }
        
        # 状态
        self.state = TimerState.IDLE
        self.timer_type: Optional[TimerType] = None
        self.duration_remaining: int = 0  # 剩余秒数
        self.total_duration: int = 0      # 总时长（秒）
        
        # 当前任务
        self.current_task: Optional[Task] = None
        
        # 当前番茄记录
        self.current_record: Optional[PomodoroRecord] = None
        
        # 中断记录
        self.interruptions: List[Dict[str, Any]] = []
        
        # 番茄计数（用于长休息判断）
        self.completed_pomodoros_count: int = 0
        
        # 计时器线程
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 默认不暂停
        
        # 回调函数
        self._tick_callbacks: List[Callable[[int, int], None]] = []
        self._state_change_callbacks: List[Callable[[TimerState, TimerState], None]] = []
        self._complete_callbacks: List[Callable[[], None]] = []
    
    def on_tick(self, callback: Callable[[int, int], None]):
        """注册每秒回调 (remaining, total)"""
        self._tick_callbacks.append(callback)
    
    def on_state_change(self, callback: Callable[[TimerState, TimerState], None]):
        """注册状态变化回调 (new_state, old_state)"""
        self._state_change_callbacks.append(callback)
    
    def on_complete(self, callback: Callable[[], None]):
        """注册完成回调"""
        self._complete_callbacks.append(callback)
    
    def _notify_tick(self):
        """通知 tick 回调"""
        for callback in self._tick_callbacks:
            try:
                callback(self.duration_remaining, self.total_duration)
            except Exception as e:
                print(f"Tick callback error: {e}")
    
    def _notify_state_change(self, new_state: TimerState):
        """通知状态变化"""
        old_state = self.state
        self.state = new_state
        for callback in self._state_change_callbacks:
            try:
                callback(new_state, old_state)
            except Exception as e:
                print(f"State change callback error: {e}")
    
    def _notify_complete(self):
        """通知完成"""
        for callback in self._complete_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Complete callback error: {e}")
    
    def start(self, task: Optional[Task] = None, timer_type: TimerType = TimerType.FOCUS):
        """启动指定类型计时"""
        if self.state in [TimerState.FOCUS, TimerState.SHORT_BREAK, TimerState.LONG_BREAK]:
            return False  # 已经在运行中
        
        self.current_task = task
        self.timer_type = timer_type
        self.interruptions = []
        
        # 设置时长
        if timer_type == TimerType.FOCUS:
            duration_minutes = self.settings.get("focus_duration", 25)
        elif timer_type == TimerType.SHORT_BREAK:
            duration_minutes = self.settings.get("short_break_duration", 5)
        elif timer_type == TimerType.LONG_BREAK:
            duration_minutes = self.settings.get("long_break_duration", 15)
        else:
            duration_minutes = 25
        
        self.total_duration = duration_minutes * 60
        self.duration_remaining = self.total_duration
        
        # 创建番茄记录
        if timer_type == TimerType.FOCUS and task:
            self.current_record = PomodoroRecord(
                task_id=task.id,
                planned_duration=duration_minutes,
            )
        else:
            self.current_record = None
        
        # 设置状态
        if timer_type == TimerType.FOCUS:
            self._notify_state_change(TimerState.FOCUS)
        elif timer_type == TimerType.SHORT_BREAK:
            self._notify_state_change(TimerState.SHORT_BREAK)
        elif timer_type == TimerType.LONG_BREAK:
            self._notify_state_change(TimerState.LONG_BREAK)
        
        # 启动计时线程
        self._stop_event.clear()
        self._pause_event.set()
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()
        
        return True
    
    def _timer_loop(self):
        """计时器主循环"""
        while not self._stop_event.is_set() and self.duration_remaining > 0:
            # 等待暂停事件
            self._pause_event.wait()
            
            if self._stop_event.is_set():
                break
            
            # 每秒更新
            time.sleep(1)
            
            if self._pause_event.is_set() and not self._stop_event.is_set():
                self.duration_remaining -= 1
                self._notify_tick()
        
        # 计时结束
        if self.duration_remaining <= 0 and not self._stop_event.is_set():
            self.complete()
    
    def pause(self) -> bool:
        """暂停"""
        if self.settings.get("strict_mode", False):
            return False  # 严格模式下不可暂停
        
        if self.state not in [TimerState.FOCUS, TimerState.SHORT_BREAK, TimerState.LONG_BREAK]:
            return False
        
        self._pause_event.clear()
        self._previous_state = self.state
        self._notify_state_change(TimerState.PAUSED)
        return True
    
    def resume(self) -> bool:
        """恢复"""
        if self.state != TimerState.PAUSED:
            return False
        
        self._pause_event.set()
        self._notify_state_change(self._previous_state)
        return True
    
    def stop(self, cancel_reason: str = "") -> bool:
        """中止并记录原因"""
        if self.state not in [TimerState.FOCUS, TimerState.SHORT_BREAK, TimerState.LONG_BREAK, TimerState.PAUSED]:
            return False
        
        self._stop_event.set()
        self._pause_event.set()
        
        # 记录取消
        if self.current_record:
            self.current_record.cancel(cancel_reason)
            if self.current_task:
                self.current_task.add_pomodoro(self.current_record)
        
        self._notify_state_change(TimerState.IDLE)
        return True
    
    def complete(self) -> bool:
        """正常完成，触发状态切换"""
        if self.state not in [TimerState.FOCUS, TimerState.SHORT_BREAK, TimerState.LONG_BREAK]:
            return False
        
        self._stop_event.set()
        
        # 记录完成
        if self.timer_type == TimerType.FOCUS:
            self.completed_pomodoros_count += 1
            if self.current_record:
                self.current_record.complete()
                if self.current_task:
                    self.current_task.add_pomodoro(self.current_record)
        
        self._notify_complete()
        self._notify_state_change(TimerState.IDLE)
        return True
    
    def record_interruption(self, interruption_type: str, note: str = ""):
        """记录中断事件"""
        interruption = {
            "timestamp": datetime.now().isoformat(),
            "type": interruption_type,  # internal / external
            "note": note,
        }
        self.interruptions.append(interruption)
        
        if self.current_record:
            self.current_record.add_interruption(interruption_type, note)
    
    def get_progress_percentage(self) -> float:
        """返回完成百分比"""
        if self.total_duration <= 0:
            return 0.0
        elapsed = self.total_duration - self.duration_remaining
        return (elapsed / self.total_duration) * 100
    
    def get_remaining_time_str(self) -> str:
        """获取剩余时间字符串 MM:SS"""
        minutes = self.duration_remaining // 60
        seconds = self.duration_remaining % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def should_take_long_break(self) -> bool:
        """判断是否应该长休息"""
        pomodoros_until_long = self.settings.get("pomodoros_until_long_break", 4)
        return self.completed_pomodoros_count > 0 and self.completed_pomodoros_count % pomodoros_until_long == 0
    
    def get_next_timer_type(self) -> TimerType:
        """获取下一个计时器类型"""
        if self.timer_type == TimerType.FOCUS:
            if self.should_take_long_break():
                return TimerType.LONG_BREAK
            else:
                return TimerType.SHORT_BREAK
        else:
            return TimerType.FOCUS
    
    def reset_pomodoro_count(self):
        """重置番茄计数"""
        self.completed_pomodoros_count = 0
    
    def update_settings(self, settings: Dict[str, Any]):
        """更新设置"""
        self.settings.update(settings)
