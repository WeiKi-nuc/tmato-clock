import uuid
import time
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT_IMPORTANT = "urgent_important"
    URGENT_NOT_IMPORTANT = "urgent_not_important"
    NOT_URGENT_IMPORTANT = "not_urgent_important"
    NOT_URGENT_NOT_IMPORTANT = "not_urgent_not_important"


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class PomodoroRecord:
    def __init__(
        self,
        task_id: str,
        started_at: float = None,
        ended_at: float = None,
        planned_duration: int = 25 * 60,
        actual_duration: int = 0,
        completion_type: str = "completed",
        notes: str = ""
    ):
        self.id = str(uuid.uuid4())
        self.task_id = task_id
        self.started_at = started_at or time.time()
        self.ended_at = ended_at
        self.planned_duration = planned_duration
        self.actual_duration = actual_duration
        self.interruptions = []
        self.completion_type = completion_type
        self.notes = notes

    def duration_minutes(self) -> float:
        return self.actual_duration / 60

    def was_completed(self) -> bool:
        return self.completion_type == "completed"

    def interruption_count(self) -> int:
        return len(self.interruptions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'task_id': self.task_id,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'planned_duration': self.planned_duration,
            'actual_duration': self.actual_duration,
            'interruptions': [i.to_dict() if hasattr(i, 'to_dict') else str(i) for i in self.interruptions],
            'completion_type': self.completion_type,
            'notes': self.notes
        }


class SubTask:
    def __init__(self, title: str, parent_id: str, completed: bool = False):
        self.id = str(uuid.uuid4())
        self.title = title
        self.parent_id = parent_id
        self.completed = completed
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'parent_id': self.parent_id,
            'completed': self.completed,
            'created_at': self.created_at
        }


class Task:
    def __init__(
        self,
        title: str,
        description: str = "",
        column_id: str = "todo",
        position: int = 0,
        estimated_pomodoros: int = 1,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[float] = None,
        parent_id: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.column_id = column_id
        self.position = position
        self.estimated_pomodoros = estimated_pomodoros
        self.completed_pomodoros: List[PomodoroRecord] = []
        self.priority = priority
        self.tags: List[str] = []
        self.due_date = due_date
        self.parent_id = parent_id
        self.subtasks: List[SubTask] = []
        self.is_archived = False
        self.created_at = time.time()
        self.completed_at: Optional[float] = None

    def add_pomodoro(self, pomodoro_record: PomodoroRecord):
        self.completed_pomodoros.append(pomodoro_record)

    def get_actual_duration(self) -> int:
        return sum(p.actual_duration for p in self.completed_pomodoros)

    def get_completion_rate(self) -> float:
        if not self.subtasks:
            return 1.0 if self.column_id == "done" else 0.0
        completed = sum(1 for st in self.subtasks if st.completed)
        return completed / len(self.subtasks) if self.subtasks else 0.0

    def move_to(self, column_id: str, position: int = None):
        self.column_id = column_id
        if position is not None:
            self.position = position
        if column_id == "done" and self.completed_at is None:
            self.completed_at = time.time()
        elif column_id != "done":
            self.completed_at = None

    def archive(self):
        self.is_archived = True

    def add_subtask(self, title: str) -> SubTask:
        subtask = SubTask(title, self.id)
        self.subtasks.append(subtask)
        return subtask

    def add_tag(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'column_id': self.column_id,
            'position': self.position,
            'estimated_pomodoros': self.estimated_pomodoros,
            'priority': self.priority.value if hasattr(self.priority, 'value') else self.priority,
            'tags': self.tags,
            'due_date': self.due_date,
            'parent_id': self.parent_id,
            'subtasks': [st.to_dict() for st in self.subtasks],
            'is_archived': self.is_archived,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'completed_pomodoros': [p.to_dict() for p in self.completed_pomodoros]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        task = cls(
            title=data['title'],
            description=data.get('description', ''),
            column_id=data.get('column_id', 'todo'),
            position=data.get('position', 0),
            estimated_pomodoros=data.get('estimated_pomodoros', 1),
            due_date=data.get('due_date')
        )
        task.id = data['id']
        if 'priority' in data:
            task.priority = TaskPriority(data['priority']) if isinstance(data['priority'], str) else data['priority']
        task.tags = data.get('tags', [])
        task.parent_id = data.get('parent_id')
        task.is_archived = data.get('is_archived', False)
        task.created_at = data.get('created_at', time.time())
        task.completed_at = data.get('completed_at')
        return task
