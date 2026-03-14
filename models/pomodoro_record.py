"""
番茄记录数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


class PomodoroRecord:
    """单个番茄完成的详细数据记录"""
    
    def __init__(
        self,
        task_id: str,
        planned_duration: int,  # 计划时长（分钟）
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        actual_duration: Optional[int] = None,
        interruptions: Optional[List[Dict]] = None,
        completion_type: str = "completed",  # completed / interrupted / cancelled
        notes: str = "",
        record_id: Optional[str] = None,
    ):
        self.id = record_id or str(uuid.uuid4())
        self.task_id = task_id
        self.planned_duration = planned_duration
        self.started_at = started_at or datetime.now()
        self.ended_at = ended_at
        self.actual_duration = actual_duration
        self.interruptions = interruptions or []
        self.completion_type = completion_type
        self.notes = notes
    
    def duration_minutes(self) -> Optional[int]:
        """计算实际分钟数"""
        if self.actual_duration is not None:
            return self.actual_duration
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None
    
    def was_completed(self) -> bool:
        """是否正常完成"""
        return self.completion_type == "completed"
    
    def interruption_count(self) -> int:
        """中断次数统计"""
        return len(self.interruptions)
    
    def add_interruption(self, interruption_type: str, note: str = ""):
        """添加中断记录"""
        self.interruptions.append({
            "timestamp": datetime.now().isoformat(),
            "type": interruption_type,  # internal / external
            "note": note,
        })
    
    def complete(self, notes: str = ""):
        """标记为完成"""
        self.ended_at = datetime.now()
        self.completion_type = "completed"
        self.notes = notes
        if self.started_at:
            delta = self.ended_at - self.started_at
            self.actual_duration = int(delta.total_seconds() / 60)
    
    def interrupt(self, reason: str = ""):
        """标记为中断"""
        self.ended_at = datetime.now()
        self.completion_type = "interrupted"
        self.notes = reason
        if self.started_at:
            delta = self.ended_at - self.started_at
            self.actual_duration = int(delta.total_seconds() / 60)
    
    def cancel(self, reason: str = ""):
        """标记为取消"""
        self.ended_at = datetime.now()
        self.completion_type = "cancelled"
        self.notes = reason
        if self.started_at:
            delta = self.ended_at - self.started_at
            self.actual_duration = int(delta.total_seconds() / 60)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "planned_duration": self.planned_duration,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "actual_duration": self.actual_duration,
            "interruptions": self.interruptions,
            "completion_type": self.completion_type,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PomodoroRecord":
        """从字典反序列化"""
        return cls(
            record_id=data.get("id"),
            task_id=data["task_id"],
            planned_duration=data["planned_duration"],
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
            actual_duration=data.get("actual_duration"),
            interruptions=data.get("interruptions", []),
            completion_type=data.get("completion_type", "completed"),
            notes=data.get("notes", ""),
        )
