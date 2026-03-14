import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.task import Task, PomodoroRecord


class TaskRepository:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "pomodoro.db")
        
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                column_id TEXT,
                position INTEGER,
                estimated_pomodoros INTEGER,
                priority TEXT,
                tags TEXT,
                due_date REAL,
                parent_id TEXT,
                is_archived INTEGER,
                created_at REAL,
                completed_at REAL,
                subtasks TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pomodoro_records (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                started_at REAL,
                ended_at REAL,
                planned_duration INTEGER,
                actual_duration INTEGER,
                completion_type TEXT,
                notes TEXT,
                interruptions TEXT,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_task(self, task: Task) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            tags_json = json.dumps(task.tags)
            subtasks_json = json.dumps([st.to_dict() for st in task.subtasks])
            priority_str = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
            
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, title, description, column_id, position, estimated_pomodoros, 
                 priority, tags, due_date, parent_id, is_archived, created_at, 
                 completed_at, subtasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.title, task.description, task.column_id,
                task.position, task.estimated_pomodoros, priority_str,
                tags_json, task.due_date, task.parent_id,
                1 if task.is_archived else 0, task.created_at,
                task.completed_at, subtasks_json
            ))
            
            for record in task.completed_pomodoros:
                self._save_pomodoro_record(record, cursor)
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def _save_pomodoro_record(self, record: PomodoroRecord, cursor):
        interruptions_json = json.dumps([
            {'type': i.type.value if hasattr(i.type, 'value') else str(i.type),
             'note': i.note, 'timestamp': i.timestamp}
            for i in record.interruptions
        ])
        
        cursor.execute('''
            INSERT OR REPLACE INTO pomodoro_records
            (id, task_id, started_at, ended_at, planned_duration,
             actual_duration, completion_type, notes, interruptions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.id, record.task_id, record.started_at,
            record.ended_at, record.planned_duration,
            record.actual_duration, record.completion_type,
            record.notes, interruptions_json
        ))

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        
        if row is None:
            conn.close()
            return None
        
        task = self._row_to_task(row)
        
        cursor.execute('SELECT * FROM pomodoro_records WHERE task_id = ?', (task_id,))
        for record_row in cursor.fetchall():
            task.completed_pomodoros.append(self._row_to_pomodoro(record_row))
        
        conn.close()
        return task

    def _row_to_task(self, row) -> Task:
        task = Task(
            title=row['title'],
            description=row['description'] or '',
            column_id=row['column_id'] or 'todo',
            position=row['position'] or 0,
            estimated_pomodoros=row['estimated_pomodoros'] or 1,
            due_date=row['due_date']
        )
        task.id = row['id']
        task.priority = row['priority']
        task.tags = json.loads(row['tags'] or '[]')
        task.parent_id = row['parent_id']
        task.is_archived = row['is_archived'] == 1
        task.created_at = row['created_at']
        task.completed_at = row['completed_at']
        task.subtasks = json.loads(row['subtasks'] or '[]')
        return task

    def _row_to_pomodoro(self, row) -> PomodoroRecord:
        record = PomodoroRecord(
            task_id=row['task_id'],
            started_at=row['started_at'],
            ended_at=row['ended_at'],
            planned_duration=row['planned_duration'],
            actual_duration=row['actual_duration'],
            completion_type=row['completion_type'],
            notes=row['notes'] or ''
        )
        record.id = row['id']
        record.interruptions = json.loads(row['interruptions'] or '[]')
        return record

    def get_all_tasks(self, include_archived: bool = False) -> Dict[str, Task]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if include_archived:
            cursor.execute('SELECT * FROM tasks')
        else:
            cursor.execute('SELECT * FROM tasks WHERE is_archived = 0')
        
        tasks = {}
        for row in cursor.fetchall():
            task = self._row_to_task(row)
            tasks[task.id] = task
        
        cursor.execute('SELECT * FROM pomodoro_records')
        for row in cursor.fetchall():
            if row['task_id'] in tasks:
                tasks[row['task_id']].completed_pomodoros.append(self._row_to_pomodoro(row))
        
        conn.close()
        return tasks

    def delete_task(self, task_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM pomodoro_records WHERE task_id = ?', (task_id,))
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()

    def save_setting(self, key: str, value: Any):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            value_json = json.dumps(value)
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                          (key, value_json))
            conn.commit()
        finally:
            conn.close()

    def get_setting(self, key: str, default: Any = None) -> Any:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return default
        
        return json.loads(row[0])
