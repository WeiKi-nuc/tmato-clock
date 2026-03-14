"""
任务数据模型
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import uuid

from .pomodoro_record import PomodoroRecord


class Task:
    """单个任务的完整数据与行为"""
    
    def __init__(
        self,
        title: str,
        description: str = "",
        column_id: str = "todo",
        position: int = 0,
        estimated_pomodoros: int = 1,
        priority: str = "not_urgent_important",  # urgent_important / urgent_not_important / not_urgent_important / not_urgent_not_important
        tags: Optional[List[str]] = None,
        due_date: Optional[date] = None,
        parent_id: Optional[str] = None,
        is_archived: bool = False,
        task_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self.id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.column_id = column_id
        self.position = position
        self.estimated_pomodoros = estimated_pomodoros
        self.completed_pomodoros: List[PomodoroRecord] = []
        self.priority = priority
        self.tags = tags or []
        self.due_date = due_date
        self.parent_id = parent_id
        self.subtasks: List[str] = []  # 子任务ID列表
        self.is_archived = is_archived
        self.created_at = created_at or datetime.now()
        self.completed_at = completed_at
    
    def add_pomodoro(self, pomodoro_record: PomodoroRecord):
        """关联完成的番茄"""
        self.completed_pomodoros.append(pomodoro_record)
    
    def get_actual_pomodoro_count(self) -> int:
        """获取实际完成的番茄数（只统计正常完成的）"""
        return sum(1 for p in self.completed_pomodoros if p.was_completed())
    
    def get_actual_duration(self) -> int:
        """计算实际耗时总和（分钟）"""
        total = 0
        for p in self.completed_pomodoros:
            duration = p.duration_minutes()
            if duration:
                total += duration
        return total
    
    def get_completion_rate(self) -> float:
        """获取完成百分比（基于番茄数）"""
        if self.estimated_pomodoros <= 0:
            return 0.0
        actual = self.get_actual_pomodoro_count()
        return min(100.0, (actual / self.estimated_pomodoros) * 100)
    
    def move_to(self, column_id: str, position: int = 0):
        """变更看板位置"""
        self.column_id = column_id
        self.position = position
        # 如果移动到完成列，标记完成时间
        if column_id == "done" and not self.completed_at:
            self.completed_at = datetime.now()
        # 如果从完成列移出，清除完成时间
        elif column_id != "done" and self.completed_at:
            self.completed_at = None
    
    def archive(self):
        """归档任务"""
        self.is_archived = True
    
    def unarchive(self):
        """取消归档"""
        self.is_archived = False
    
    def add_subtask(self, subtask_id: str):
        """添加子任务"""
        if subtask_id not in self.subtasks:
            self.subtasks.append(subtask_id)
    
    def remove_subtask(self, subtask_id: str):
        """移除子任务"""
        if subtask_id in self.subtasks:
            self.subtasks.remove(subtask_id)
    
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if not self.due_date:
            return False
        return self.due_date < date.today() and self.column_id != "done"
    
    def get_estimation_accuracy(self) -> Optional[float]:
        """预估准确度（实际/预估，>1表示超时）"""
        if self.estimated_pomodoros <= 0:
            return None
        actual = self.get_actual_pomodoro_count()
        if actual == 0:
            return None
        return actual / self.estimated_pomodoros
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "column_id": self.column_id,
            "position": self.position,
            "estimated_pomodoros": self.estimated_pomodoros,
            "completed_pomodoros": [p.to_dict() for p in self.completed_pomodoros],
            "priority": self.priority,
            "tags": self.tags,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "parent_id": self.parent_id,
            "subtasks": self.subtasks,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """从字典反序列化"""
        task = cls(
            task_id=data.get("id"),
            title=data["title"],
            description=data.get("description", ""),
            column_id=data.get("column_id", "todo"),
            position=data.get("position", 0),
            estimated_pomodoros=data.get("estimated_pomodoros", 1),
            priority=data.get("priority", "not_urgent_important"),
            tags=data.get("tags", []),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            parent_id=data.get("parent_id"),
            is_archived=data.get("is_archived", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
        # 反序列化番茄记录
        for p_data in data.get("completed_pomodoros", []):
            task.completed_pomodoros.append(PomodoroRecord.from_dict(p_data))
        task.subtasks = data.get("subtasks", [])
        return task
