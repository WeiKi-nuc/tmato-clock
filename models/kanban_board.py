"""
看板数据模型
"""
from typing import Dict, List, Optional, Any
from .task import Task


class KanbanColumn:
    """看板列定义"""
    
    def __init__(
        self,
        column_id: str,
        name: str,
        color: str = "#3498db",
        wip_limit: Optional[int] = None,
        position: int = 0,
    ):
        self.id = column_id
        self.name = name
        self.color = color
        self.wip_limit = wip_limit  # 在制品限制
        self.position = position
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "wip_limit": self.wip_limit,
            "position": self.position,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KanbanColumn":
        return cls(
            column_id=data["id"],
            name=data["name"],
            color=data.get("color", "#3498db"),
            wip_limit=data.get("wip_limit"),
            position=data.get("position", 0),
        )


class KanbanBoard:
    """看板管理器 - 看板布局与任务流转控制"""
    
    def __init__(self, board_id: str = "default"):
        self.id = board_id
        self.columns: List[KanbanColumn] = []
        self.tasks: Dict[str, Task] = {}
        self.swimlane_mode: str = "none"  # none / tag / priority / project
        self._initialize_default_columns()
    
    def _initialize_default_columns(self):
        """初始化默认列"""
        from config import DEFAULT_COLUMNS
        for i, col_data in enumerate(DEFAULT_COLUMNS):
            self.columns.append(KanbanColumn(
                column_id=col_data["id"],
                name=col_data["name"],
                color=col_data["color"],
                wip_limit=col_data["wip_limit"],
                position=i,
            ))
    
    def add_column(self, name: str, wip_limit: Optional[int] = None, color: str = "#3498db") -> KanbanColumn:
        """添加自定义列"""
        column_id = f"col_{len(self.columns)}"
        column = KanbanColumn(
            column_id=column_id,
            name=name,
            color=color,
            wip_limit=wip_limit,
            position=len(self.columns),
        )
        self.columns.append(column)
        return column
    
    def remove_column(self, column_id: str):
        """删除列（该列中的任务会移到待办列）"""
        self.columns = [c for c in self.columns if c.id != column_id]
        # 将该列中的任务移到待办列
        for task in self.tasks.values():
            if task.column_id == column_id:
                task.move_to("todo")
        # 重新排序
        for i, col in enumerate(self.columns):
            col.position = i
    
    def reorder_columns(self, order_list: List[str]):
        """调整列顺序"""
        column_map = {c.id: c for c in self.columns}
        self.columns = []
        for i, col_id in enumerate(order_list):
            if col_id in column_map:
                column_map[col_id].position = i
                self.columns.append(column_map[col_id])
    
    def create_task(self, title: str, column_id: str = "todo") -> Optional[Task]:
        """新建任务到指定列"""
        # 检查WIP限制
        if not self.check_wip_limit(column_id):
            return None
        
        # 计算新位置
        column_tasks = self.get_tasks_by_column(column_id)
        position = len(column_tasks)
        
        task = Task(title=title, column_id=column_id, position=position)
        self.tasks[task.id] = task
        return task
    
    def move_task(self, task_id: str, target_column: str, target_position: int = 0) -> bool:
        """移动任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        source_column = task.column_id
        
        # 检查WIP限制
        if target_column != source_column and not self.check_wip_limit(target_column):
            return False
        
        # 更新原列中其他任务的位置
        if source_column != target_column:
            column_tasks = self.get_tasks_by_column(source_column)
            for i, t in enumerate(column_tasks):
                if t.id != task_id:
                    t.position = i if i < task.position else i - 1
        
        # 更新目标列中其他任务的位置
        column_tasks = self.get_tasks_by_column(target_column)
        for t in column_tasks:
            if t.id != task_id and t.position >= target_position:
                t.position += 1
        
        # 移动任务
        task.move_to(target_column, target_position)
        return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_tasks_by_column(self, column_id: str) -> List[Task]:
        """获取列内任务（按position排序）"""
        tasks = [t for t in self.tasks.values() if t.column_id == column_id and not t.is_archived]
        return sorted(tasks, key=lambda t: t.position)
    
    def get_all_tasks(self, include_archived: bool = False) -> List[Task]:
        """获取所有任务"""
        tasks = self.tasks.values()
        if not include_archived:
            tasks = [t for t in tasks if not t.is_archived]
        return list(tasks)
    
    def get_tasks_by_filter(
        self,
        column: Optional[str] = None,
        tag: Optional[str] = None,
        priority: Optional[str] = None,
        due_date_before: Optional[str] = None,
    ) -> List[Task]:
        """复合筛选任务"""
        result = self.get_all_tasks()
        
        if column:
            result = [t for t in result if t.column_id == column]
        if tag:
            result = [t for t in result if tag in t.tags]
        if priority:
            result = [t for t in result if t.priority == priority]
        if due_date_before:
            from datetime import date
            cutoff = date.fromisoformat(due_date_before)
            result = [t for t in result if t.due_date and t.due_date <= cutoff]
        
        return result
    
    def get_overdue_tasks(self) -> List[Task]:
        """获取逾期任务"""
        return [t for t in self.get_all_tasks() if t.is_overdue()]
    
    def get_tasks_by_pomodoro_date(self, date_str: str) -> List[Task]:
        """查找某天有番茄记录的任务"""
        from datetime import datetime
        target_date = datetime.fromisoformat(date_str).date()
        result = []
        for task in self.get_all_tasks():
            for p in task.completed_pomodoros:
                if p.started_at and p.started_at.date() == target_date:
                    result.append(task)
                    break
        return result
    
    def check_wip_limit(self, column_id: str) -> bool:
        """检查是否超在制品限制"""
        column = next((c for c in self.columns if c.id == column_id), None)
        if not column or column.wip_limit is None:
            return True
        
        current_count = len(self.get_tasks_by_column(column_id))
        return current_count < column.wip_limit
    
    def get_swimlane_groups(self) -> Dict[str, List[Task]]:
        """返回泳道分组后的任务"""
        if self.swimlane_mode == "none":
            return {"所有任务": self.get_all_tasks()}
        elif self.swimlane_mode == "priority":
            groups = {}
            for task in self.get_all_tasks():
                key = task.priority
                if key not in groups:
                    groups[key] = []
                groups[key].append(task)
            return groups
        elif self.swimlane_mode == "tag":
            groups = {}
            for task in self.get_all_tasks():
                if not task.tags:
                    key = "无标签"
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(task)
                else:
                    for tag in task.tags:
                        if tag not in groups:
                            groups[tag] = []
                        groups[tag].append(task)
            return groups
        else:
            return {"所有任务": self.get_all_tasks()}
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务（级联删除子任务）"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        # 删除子任务
        for subtask_id in task.subtasks:
            self.delete_task(subtask_id)
        
        # 从父任务的子任务列表中移除
        if task.parent_id and task.parent_id in self.tasks:
            self.tasks[task.parent_id].remove_subtask(task_id)
        
        del self.tasks[task_id]
        return True
    
    def archive_task(self, task_id: str) -> bool:
        """归档任务"""
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].archive()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "columns": [c.to_dict() for c in self.columns],
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "swimlane_mode": self.swimlane_mode,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KanbanBoard":
        """从字典反序列化"""
        board = cls(board_id=data.get("id", "default"))
        board.columns = [KanbanColumn.from_dict(c) for c in data.get("columns", [])]
        board.tasks = {
            tid: Task.from_dict(t) for tid, t in data.get("tasks", {}).items()
        }
        board.swimlane_mode = data.get("swimlane_mode", "none")
        return board
