from typing import Dict, List, Any, Optional
from .task import Task


class KanbanColumn:
    def __init__(self, id: str, name: str, color: str = "#CCCCCC", wip_limit: Optional[int] = None):
        self.id = id
        self.name = name
        self.color = color
        self.wip_limit = wip_limit


class SwimlaneMode:
    NONE = "none"
    TAG = "tag"
    PRIORITY = "priority"
    PROJECT = "project"


class KanbanBoard:
    def __init__(self):
        self.columns: List[KanbanColumn] = [
            KanbanColumn("todo", "待办", "#FF9AA2"),
            KanbanColumn("in_progress", "进行中", "#FFDAC1"),
            KanbanColumn("done", "完成", "#E2F0CB")
        ]
        self.tasks: Dict[str, Task] = {}
        self.swimlane_mode = SwimlaneMode.NONE

    def add_column(self, name: str, wip_limit: Optional[int] = None, color: str = "#CCCCCC") -> KanbanColumn:
        column_id = name.lower().replace(" ", "_")
        while column_id in [c.id for c in self.columns]:
            column_id += "_new"
        column = KanbanColumn(column_id, name, color, wip_limit)
        self.columns.append(column)
        return column

    def reorder_columns(self, order_list: List[str]):
        new_columns = []
        for col_id in order_list:
            column = next((c for c in self.columns if c.id == col_id), None)
            if column:
                new_columns.append(column)
        remaining = [c for c in self.columns if c.id not in order_list]
        self.columns = new_columns + remaining

    def create_task(self, title: str, column_id: str = "todo") -> Task:
        position = len(self.get_tasks_by_column(column_id))
        task = Task(title, column_id=column_id, position=position)
        self.tasks[task.id] = task
        return task

    def move_task(self, task_id: str, target_column: str, target_position: int = None):
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        source_column = task.column_id
        source_tasks = self.get_tasks_by_column(source_column)
        
        for t in source_tasks:
            if t.position > task.position and t.id != task.id:
                t.position -= 1
        
        target_tasks = self.get_tasks_by_column(target_column)
        if target_position is None:
            target_position = len(target_tasks)
        
        for t in target_tasks:
            if t.position >= target_position:
                t.position += 1
        
        task.column_id = target_column
        task.position = target_position
        return True

    def get_tasks_by_column(self, column_id: str) -> List[Task]:
        column_tasks = [t for t in self.tasks.values() if t.column_id == column_id and not t.is_archived]
        return sorted(column_tasks, key=lambda t: t.position)

    def get_swimlane_groups(self) -> Dict[str, List[Task]]:
        groups = {}
        if self.swimlane_mode == SwimlaneMode.NONE:
            groups["all"] = list(self.tasks.values())
        elif self.swimlane_mode == SwimlaneMode.TAG:
            for task in self.tasks.values():
                if not task.tags:
                    key = "无标签"
                else:
                    key = task.tags[0]
                if key not in groups:
                    groups[key] = []
                groups[key].append(task)
        elif self.swimlane_mode == SwimlaneMode.PRIORITY:
            for task in self.tasks.values():
                key = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
                if key not in groups:
                    groups[key] = []
                groups[key].append(task)
        return groups

    def check_wip_limit(self, column_id: str) -> bool:
        column = next((c for c in self.columns if c.id == column_id), None)
        if not column or column.wip_limit is None:
            return True
        tasks_in_column = len(self.get_tasks_by_column(column_id))
        return tasks_in_column < column.wip_limit

    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'columns': [{'id': c.id, 'name': c.name, 'color': c.color, 'wip_limit': c.wip_limit} for c in self.columns],
            'tasks': {tid: task.to_dict() for tid, task in self.tasks.items()},
            'swimlane_mode': self.swimlane_mode
        }
