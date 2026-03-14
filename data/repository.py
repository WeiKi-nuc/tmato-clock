"""
任务仓库 - 任务数据的持久化与查询
"""
import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from models.task import Task
from models.pomodoro_record import PomodoroRecord
from models.kanban_board import KanbanBoard, KanbanColumn
from config import DATABASE_PATH


class TaskRepository:
    """任务仓库 - 负责数据的持久化"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                column_id TEXT DEFAULT 'todo',
                position INTEGER DEFAULT 0,
                estimated_pomodoros INTEGER DEFAULT 1,
                priority TEXT DEFAULT 'not_urgent_important',
                tags TEXT DEFAULT '[]',
                due_date TEXT,
                parent_id TEXT,
                subtasks TEXT DEFAULT '[]',
                is_archived INTEGER DEFAULT 0,
                created_at TEXT,
                completed_at TEXT
            )
        """)
        
        # 番茄记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_records (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                planned_duration INTEGER NOT NULL,
                started_at TEXT,
                ended_at TEXT,
                actual_duration INTEGER,
                interruptions TEXT DEFAULT '[]',
                completion_type TEXT DEFAULT 'completed',
                notes TEXT DEFAULT '',
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        # 看板列配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kanban_columns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#3498db',
                wip_limit INTEGER,
                position INTEGER DEFAULT 0
            )
        """)
        
        # 应用配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # 插入默认列
        cursor.execute("SELECT COUNT(*) FROM kanban_columns")
        if cursor.fetchone()[0] == 0:
            default_columns = [
                ("todo", "待办", "#ff6b6b", None, 0),
                ("in_progress", "进行中", "#4ecdc4", 3, 1),
                ("done", "完成", "#95e1d3", None, 2),
            ]
            cursor.executemany(
                "INSERT INTO kanban_columns VALUES (?, ?, ?, ?, ?)",
                default_columns
            )
        
        conn.commit()
        conn.close()
    
    # ==================== 任务操作 ====================
    
    def save_task(self, task: Task) -> bool:
        """插入或更新任务"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO tasks (
                    id, title, description, column_id, position,
                    estimated_pomodoros, priority, tags, due_date,
                    parent_id, subtasks, is_archived, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.title,
                task.description,
                task.column_id,
                task.position,
                task.estimated_pomodoros,
                task.priority,
                json.dumps(task.tags),
                task.due_date.isoformat() if task.due_date else None,
                task.parent_id,
                json.dumps(task.subtasks),
                1 if task.is_archived else 0,
                task.created_at.isoformat() if task.created_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
            ))
            
            # 保存番茄记录
            for record in task.completed_pomodoros:
                self._save_pomodoro_record(cursor, record)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Save task error: {e}")
            return False
        finally:
            conn.close()
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """通过ID获取任务"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        task = self._row_to_task(row)
        
        # 加载番茄记录
        cursor.execute("SELECT * FROM pomodoro_records WHERE task_id = ?", (task_id,))
        for row in cursor.fetchall():
            task.completed_pomodoros.append(self._row_to_pomodoro_record(row))
        
        conn.close()
        return task
    
    def get_all_tasks(self, include_archived: bool = False) -> List[Task]:
        """获取所有任务"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if include_archived:
            cursor.execute("SELECT * FROM tasks ORDER BY position")
        else:
            cursor.execute("SELECT * FROM tasks WHERE is_archived = 0 ORDER BY position")
        
        tasks = []
        for row in cursor.fetchall():
            task = self._row_to_task(row)
            # 加载番茄记录
            cursor.execute("SELECT * FROM pomodoro_records WHERE task_id = ?", (task.id,))
            for p_row in cursor.fetchall():
                task.completed_pomodoros.append(self._row_to_pomodoro_record(p_row))
            tasks.append(task)
        
        conn.close()
        return tasks
    
    def get_tasks_by_column(self, column_id: str) -> List[Task]:
        """获取列内任务"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM tasks WHERE column_id = ? AND is_archived = 0 ORDER BY position",
            (column_id,)
        )
        
        tasks = []
        for row in cursor.fetchall():
            task = self._row_to_task(row)
            cursor.execute("SELECT * FROM pomodoro_records WHERE task_id = ?", (task.id,))
            for p_row in cursor.fetchall():
                task.completed_pomodoros.append(self._row_to_pomodoro_record(p_row))
            tasks.append(task)
        
        conn.close()
        return tasks
    
    def get_tasks_by_filter(
        self,
        column: Optional[str] = None,
        tag: Optional[str] = None,
        priority: Optional[str] = None,
        date_range: Optional[tuple] = None,
    ) -> List[Task]:
        """复合筛选任务"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM tasks WHERE is_archived = 0"
        params = []
        
        if column:
            query += " AND column_id = ?"
            params.append(column)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if date_range:
            query += " AND due_date >= ? AND due_date <= ?"
            params.extend([date_range[0].isoformat(), date_range[1].isoformat()])
        
        query += " ORDER BY position"
        
        cursor.execute(query, params)
        tasks = []
        for row in cursor.fetchall():
            task = self._row_to_task(row)
            # 标签筛选在内存中进行（因为tags是JSON存储）
            if tag and tag not in task.tags:
                continue
            tasks.append(task)
        
        conn.close()
        return tasks
    
    def get_overdue_tasks(self) -> List[Task]:
        """获取逾期任务"""
        today = date.today().isoformat()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE due_date < ? AND column_id != 'done' AND is_archived = 0
        """, (today,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(self._row_to_task(row))
        
        conn.close()
        return tasks
    
    def get_tasks_by_pomodoro_date(self, target_date: date) -> List[Task]:
        """查找某天有番茄记录的任务"""
        date_str = target_date.isoformat()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT task_id FROM pomodoro_records 
            WHERE date(started_at) = ?
        """, (date_str,))
        
        task_ids = [row[0] for row in cursor.fetchall()]
        tasks = []
        for task_id in task_ids:
            task = self.get_task_by_id(task_id)
            if task:
                tasks.append(task)
        
        conn.close()
        return tasks
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务（级联删除子任务和番茄记录）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取子任务并递归删除
            cursor.execute("SELECT id FROM tasks WHERE parent_id = ?", (task_id,))
            for row in cursor.fetchall():
                self.delete_task(row[0])
            
            # 删除番茄记录
            cursor.execute("DELETE FROM pomodoro_records WHERE task_id = ?", (task_id,))
            
            # 删除任务
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Delete task error: {e}")
            return False
        finally:
            conn.close()
    
    def batch_update(self, task_ids: List[str], field: str, value: Any) -> bool:
        """批量更新属性"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join('?' * len(task_ids))
            query = f"UPDATE tasks SET {field} = ? WHERE id IN ({placeholders})"
            cursor.execute(query, [value] + task_ids)
            conn.commit()
            return True
        except Exception as e:
            print(f"Batch update error: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== 番茄记录操作 ====================
    
    def _save_pomodoro_record(self, cursor: sqlite3.Cursor, record: PomodoroRecord):
        """保存番茄记录"""
        cursor.execute("""
            INSERT OR REPLACE INTO pomodoro_records (
                id, task_id, planned_duration, started_at, ended_at,
                actual_duration, interruptions, completion_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.task_id,
            record.planned_duration,
            record.started_at.isoformat() if record.started_at else None,
            record.ended_at.isoformat() if record.ended_at else None,
            record.actual_duration,
            json.dumps(record.interruptions),
            record.completion_type,
            record.notes,
        ))
    
    def get_pomodoro_records_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[PomodoroRecord]:
        """获取日期范围内的番茄记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pomodoro_records 
            WHERE date(started_at) >= ? AND date(started_at) <= ?
            ORDER BY started_at
        """, (start_date.isoformat(), end_date.isoformat()))
        
        records = [self._row_to_pomodoro_record(row) for row in cursor.fetchall()]
        conn.close()
        return records
    
    # ==================== 看板列操作 ====================
    
    def get_columns(self) -> List[KanbanColumn]:
        """获取所有列"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM kanban_columns ORDER BY position")
        columns = []
        for row in cursor.fetchall():
            columns.append(KanbanColumn(
                column_id=row["id"],
                name=row["name"],
                color=row["color"],
                wip_limit=row["wip_limit"],
                position=row["position"],
            ))
        
        conn.close()
        return columns
    
    def save_column(self, column: KanbanColumn) -> bool:
        """保存列配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO kanban_columns (id, name, color, wip_limit, position)
                VALUES (?, ?, ?, ?, ?)
            """, (column.id, column.name, column.color, column.wip_limit, column.position))
            conn.commit()
            return True
        except Exception as e:
            print(f"Save column error: {e}")
            return False
        finally:
            conn.close()
    
    def delete_column(self, column_id: str) -> bool:
        """删除列"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM kanban_columns WHERE id = ?", (column_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Delete column error: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== 配置操作 ====================
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row["value"])
            except:
                return row["value"]
        return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """设置配置项"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            json_value = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute("""
                INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)
            """, (key, json_value))
            conn.commit()
            return True
        except Exception as e:
            print(f"Set setting error: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== 辅助方法 ====================
    
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """将数据库行转换为Task对象"""
        return Task(
            task_id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            column_id=row["column_id"],
            position=row["position"],
            estimated_pomodoros=row["estimated_pomodoros"],
            priority=row["priority"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
            parent_id=row["parent_id"],
            is_archived=bool(row["is_archived"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )
    
    def _row_to_pomodoro_record(self, row: sqlite3.Row) -> PomodoroRecord:
        """将数据库行转换为PomodoroRecord对象"""
        return PomodoroRecord(
            record_id=row["id"],
            task_id=row["task_id"],
            planned_duration=row["planned_duration"],
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
            actual_duration=row["actual_duration"],
            interruptions=json.loads(row["interruptions"]) if row["interruptions"] else [],
            completion_type=row["completion_type"],
            notes=row["notes"] or "",
        )
    
    def load_board(self) -> KanbanBoard:
        """加载看板数据"""
        board = KanbanBoard()
        
        # 加载列配置
        columns = self.get_columns()
        if columns:
            board.columns = columns
        
        # 加载任务
        tasks = self.get_all_tasks()
        for task in tasks:
            board.tasks[task.id] = task
        
        return board
    
    def save_board(self, board: KanbanBoard) -> bool:
        """保存看板数据"""
        # 保存列
        for column in board.columns:
            self.save_column(column)
        
        # 保存任务
        for task in board.tasks.values():
            self.save_task(task)
        
        return True
