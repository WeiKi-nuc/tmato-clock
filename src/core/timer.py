import time
import threading
from enum import Enum
from typing import Callable, List, Optional


class TimerState(Enum):
    IDLE = "idle"
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    PAUSED = "paused"


class InterruptionType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class Interruption:
    def __init__(self, type: InterruptionType, note: str = "", timestamp: float = None):
        self.type = type
        self.note = note
        self.timestamp = timestamp or time.time()


class PomodoroTimer:
    def __init__(self, focus_duration: int = 25 * 60, short_break: int = 5 * 60, long_break: int = 15 * 60):
        self.state = TimerState.IDLE
        self.duration_remaining = 0
        self.current_task = None
        self.interruptions: List[Interruption] = []
        self.settings = {
            'focus': focus_duration,
            'short_break': short_break,
            'long_break': long_break
        }
        self._tick_callbacks: List[Callable] = []
        self._state_callbacks: List[Callable] = []
        self._timer_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._pomodoros_completed = 0

    def start(self, task, timer_type: TimerState = TimerState.FOCUS):
        if self.state not in [TimerState.IDLE, TimerState.PAUSED]:
            return False
        
        if timer_type == TimerState.PAUSED:
            timer_type = TimerState.FOCUS
            
        self.state = timer_type
        self.current_task = task
        
        if self.duration_remaining == 0:
            self.duration_remaining = self.settings.get(timer_type.value, 25 * 60)
            
        self._is_running = True
        self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self._timer_thread.start()
        
        for callback in self._state_callbacks:
            callback(self.state)
            
        return True

    def pause(self):
        if self.state not in [TimerState.FOCUS, TimerState.SHORT_BREAK, TimerState.LONG_BREAK]:
            return False
        
        self._is_running = False
        old_state = self.state
        self.state = TimerState.PAUSED
        
        for callback in self._state_callbacks:
            callback(self.state, old_state=old_state)
            
        return True

    def resume(self):
        if self.state != TimerState.PAUSED:
            return False
        
        self._is_running = True
        self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self._timer_thread.start()
        
        for callback in self._state_callbacks:
            callback(self.state)
            
        return True

    def stop(self, cancel_reason: str = ""):
        self._is_running = False
        self.state = TimerState.IDLE
        self.duration_remaining = 0
        self.interruptions = []
        self.current_task = None
        
        for callback in self._state_callbacks:
            callback(self.state)
            
        return True

    def complete(self):
        completed_state = self.state
        self._is_running = False
        
        if completed_state == TimerState.FOCUS:
            self._pomodoros_completed += 1
            
        self.state = TimerState.IDLE
        self.duration_remaining = 0
        
        for callback in self._state_callbacks:
            callback(self.state, completed=True)
            
        return {
            'type': completed_state,
            'interruptions': self.interruptions.copy(),
            'task': self.current_task
        }

    def record_interruption(self, type: InterruptionType, note: str = ""):
        interruption = Interruption(type, note)
        self.interruptions.append(interruption)
        return interruption

    def get_progress_percentage(self):
        if self.state == TimerState.IDLE:
            return 0
            
        total = self.settings.get(self.state.value, 25 * 60)
        if self.state == TimerState.PAUSED:
            total = self.settings.get(TimerState.FOCUS.value, 25 * 60)
            
        if total == 0:
            return 0
            
        return (total - self.duration_remaining) / total * 100

    def on_tick(self, callback: Callable[[int], None]):
        self._tick_callbacks.append(callback)

    def on_state_change(self, callback: Callable):
        self._state_callbacks.append(callback)

    def _run_timer(self):
        while self._is_running and self.duration_remaining > 0:
            for callback in self._tick_callbacks:
                callback(self.duration_remaining)
            
            time.sleep(1)
            self.duration_remaining -= 1
            
            if self.duration_remaining <= 0:
                break
        
        if self._is_running and self.duration_remaining <= 0:
            self.complete()
