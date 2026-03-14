"""
统计引擎 - 数据分析与报表生成
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from data.repository import TaskRepository
from models.task import Task
from models.pomodoro_record import PomodoroRecord


class DailyReport:
    """日报数据对象"""
    
    def __init__(self, report_date: date):
        self.date = report_date
        self.total_pomodoros: int = 0
        self.completed_pomodoros: int = 0
        self.interrupted_pomodoros: int = 0
        self.total_tasks_completed: int = 0
        self.total_tasks_created: int = 0
        self.total_interruptions: int = 0
        self.focus_minutes: int = 0
        self.tasks_by_tag: Dict[str, int] = defaultdict(int)
        self.hourly_distribution: Dict[int, int] = defaultdict(int)  # 小时->番茄数
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "total_pomodoros": self.total_pomodoros,
            "completed_pomodoros": self.completed_pomodoros,
            "interrupted_pomodoros": self.interrupted_pomodoros,
            "total_tasks_completed": self.total_tasks_completed,
            "total_tasks_created": self.total_tasks_created,
            "total_interruptions": self.total_interruptions,
            "focus_minutes": self.focus_minutes,
            "tasks_by_tag": dict(self.tasks_by_tag),
            "hourly_distribution": dict(self.hourly_distribution),
        }


class WeeklyReport:
    """周报数据对象"""
    
    def __init__(self, week_start: date):
        self.week_start = week_start
        self.week_end = week_start + timedelta(days=6)
        self.daily_reports: List[DailyReport] = []
        self.total_pomodoros: int = 0
        self.total_focus_hours: float = 0
        self.avg_pomodoros_per_day: float = 0
        self.best_day: Optional[date] = None
        self.best_day_pomodoros: int = 0
        self.tag_distribution: Dict[str, int] = defaultdict(int)
        self.completion_rate: float = 0  # 任务完成率
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_start": self.week_start.isoformat(),
            "week_end": self.week_end.isoformat(),
            "total_pomodoros": self.total_pomodoros,
            "total_focus_hours": self.total_focus_hours,
            "avg_pomodoros_per_day": self.avg_pomodoros_per_day,
            "best_day": self.best_day.isoformat() if self.best_day else None,
            "best_day_pomodoros": self.best_day_pomodoros,
            "tag_distribution": dict(self.tag_distribution),
            "completion_rate": self.completion_rate,
        }


class StatisticsEngine:
    """统计引擎 - 负责数据分析与报表生成"""
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
    
    def daily_report(self, report_date: Optional[date] = None) -> DailyReport:
        """生成日报"""
        if report_date is None:
            report_date = date.today()
        
        report = DailyReport(report_date)
        
        # 获取当天的番茄记录
        records = self.repository.get_pomodoro_records_by_date_range(
            report_date, report_date
        )
        
        for record in records:
            report.total_pomodoros += 1
            report.focus_minutes += record.duration_minutes() or 0
            report.total_interruptions += record.interruption_count()
            
            if record.was_completed():
                report.completed_pomodoros += 1
            else:
                report.interrupted_pomodoros += 1
            
            # 小时分布
            if record.started_at:
                hour = record.started_at.hour
                report.hourly_distribution[hour] += 1
            
            # 标签统计
            task = self.repository.get_task_by_id(record.task_id)
            if task:
                for tag in task.tags:
                    report.tasks_by_tag[tag] += 1
        
        # 统计完成的任务
        all_tasks = self.repository.get_all_tasks()
        for task in all_tasks:
            if task.completed_at and task.completed_at.date() == report_date:
                report.total_tasks_completed += 1
            if task.created_at and task.created_at.date() == report_date:
                report.total_tasks_created += 1
        
        return report
    
    def weekly_report(self, week_start: Optional[date] = None) -> WeeklyReport:
        """生成周报"""
        if week_start is None:
            # 默认本周一
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        
        report = WeeklyReport(week_start)
        
        # 生成每天的日报
        for i in range(7):
            day = week_start + timedelta(days=i)
            daily = self.daily_report(day)
            report.daily_reports.append(daily)
            
            report.total_pomodoros += daily.total_pomodoros
            report.total_focus_hours += daily.focus_minutes / 60
            
            # 找出最佳一天
            if daily.total_pomodoros > report.best_day_pomodoros:
                report.best_day_pomodoros = daily.total_pomodoros
                report.best_day = day
            
            # 累加标签分布
            for tag, count in daily.tasks_by_tag.items():
                report.tag_distribution[tag] += count
        
        # 计算平均值
        report.avg_pomodoros_per_day = report.total_pomodoros / 7
        
        # 计算任务完成率
        week_end = week_start + timedelta(days=6)
        tasks = self.repository.get_all_tasks()
        tasks_created_this_week = [
            t for t in tasks 
            if t.created_at and week_start <= t.created_at.date() <= week_end
        ]
        tasks_completed_this_week = [
            t for t in tasks_created_this_week 
            if t.completed_at and week_start <= t.completed_at.date() <= week_end
        ]
        
        if tasks_created_this_week:
            report.completion_rate = len(tasks_completed_this_week) / len(tasks_created_this_week)
        
        return report
    
    def productivity_curve(
        self, 
        date_range: Tuple[date, date],
        granularity: str = "hour"
    ) -> Dict[str, List[int]]:
        """时段效率曲线"""
        records = self.repository.get_pomodoro_records_by_date_range(
            date_range[0], date_range[1]
        )
        
        if granularity == "hour":
            distribution = defaultdict(int)
            for record in records:
                if record.started_at:
                    hour = record.started_at.hour
                    distribution[hour] += 1
            return {
                "labels": [f"{h}:00" for h in range(24)],
                "data": [distribution[h] for h in range(24)],
            }
        
        elif granularity == "day":
            distribution = defaultdict(int)
            for record in records:
                if record.started_at:
                    day = record.started_at.date().isoformat()
                    distribution[day] += 1
            
            # 填充所有日期
            current = date_range[0]
            labels = []
            data = []
            while current <= date_range[1]:
                labels.append(current.isoformat())
                data.append(distribution[current.isoformat()])
                current += timedelta(days=1)
            
            return {"labels": labels, "data": data}
        
        return {"labels": [], "data": []}
    
    def estimation_accuracy(
        self,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """预估准确度分析"""
        tasks = self.repository.get_all_tasks()
        
        if date_range:
            tasks = [
                t for t in tasks 
                if t.created_at and date_range[0] <= t.created_at.date() <= date_range[1]
            ]
        
        # 只统计有番茄记录的任务
        tasks_with_records = [t for t in tasks if t.completed_pomodoros]
        
        if not tasks_with_records:
            return {
                "accuracy_rate": 0,
                "avg_estimation_error": 0,
                "underestimated_count": 0,
                "overestimated_count": 0,
                "accurate_count": 0,
            }
        
        underestimated = 0  # 实际 > 预估
        overestimated = 0   # 实际 < 预估
        accurate = 0        # 实际 == 预估
        total_error = 0
        
        for task in tasks_with_records:
            actual = task.get_actual_pomodoro_count()
            estimated = task.estimated_pomodoros
            
            if actual > estimated:
                underestimated += 1
            elif actual < estimated:
                overestimated += 1
            else:
                accurate += 1
            
            if estimated > 0:
                error = abs(actual - estimated) / estimated
                total_error += error
        
        total = len(tasks_with_records)
        
        return {
            "accuracy_rate": accurate / total if total > 0 else 0,
            "avg_estimation_error": total_error / total if total > 0 else 0,
            "underestimated_count": underestimated,
            "overestimated_count": overestimated,
            "accurate_count": accurate,
            "total_analyzed": total,
        }
    
    def tag_distribution(
        self,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, int]:
        """标签占比统计"""
        records = self.repository.get_pomodoro_records_by_date_range(
            date_range[0] if date_range else date.today() - timedelta(days=30),
            date_range[1] if date_range else date.today(),
        )
        
        distribution = defaultdict(int)
        
        for record in records:
            task = self.repository.get_task_by_id(record.task_id)
            if task:
                for tag in task.tags:
                    distribution[tag] += 1
        
        return dict(distribution)
    
    def streak_calculation(self) -> Dict[str, Any]:
        """连续工作天数计算"""
        # 获取所有有番茄记录的日期
        all_records = self.repository.get_pomodoro_records_by_date_range(
            date.today() - timedelta(days=365),
            date.today(),
        )
        
        # 提取有记录的日期
        dates_with_pomodoros = set()
        for record in all_records:
            if record.started_at:
                dates_with_pomodoros.add(record.started_at.date())
        
        if not dates_with_pomodoros:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "total_active_days": 0,
            }
        
        # 计算当前连续天数
        current_streak = 0
        check_date = date.today()
        
        while check_date in dates_with_pomodoros:
            current_streak += 1
            check_date -= timedelta(days=1)
        
        # 计算最长连续天数
        sorted_dates = sorted(dates_with_pomodoros)
        longest_streak = 1
        current_count = 1
        
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_count += 1
                longest_streak = max(longest_streak, current_count)
            else:
                current_count = 1
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_active_days": len(dates_with_pomodoros),
        }
    
    def best_working_hours(self) -> Dict[str, Any]:
        """高效时段识别算法"""
        # 获取最近30天的数据
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        records = self.repository.get_pomodoro_records_by_date_range(
            start_date, end_date
        )
        
        # 按小时统计
        hourly_stats = defaultdict(lambda: {"count": 0, "completed": 0})
        
        for record in records:
            if record.started_at:
                hour = record.started_at.hour
                hourly_stats[hour]["count"] += 1
                if record.was_completed():
                    hourly_stats[hour]["completed"] += 1
        
        # 找出最佳时段（番茄数最多且完成率高的时段）
        best_hours = []
        for hour, stats in hourly_stats.items():
            if stats["count"] >= 3:  # 至少3个番茄
                completion_rate = stats["completed"] / stats["count"]
                best_hours.append({
                    "hour": hour,
                    "count": stats["count"],
                    "completion_rate": completion_rate,
                    "score": stats["count"] * completion_rate,
                })
        
        # 按得分排序
        best_hours.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "best_hours": best_hours[:3],  # 前3个最佳时段
            "hourly_stats": dict(hourly_stats),
        }
    
    def get_task_stats(self, task_id: str) -> Dict[str, Any]:
        """获取单个任务的统计信息"""
        task = self.repository.get_task_by_id(task_id)
        if not task:
            return {}
        
        return {
            "estimated_pomodoros": task.estimated_pomodoros,
            "actual_pomodoros": task.get_actual_pomodoro_count(),
            "completion_rate": task.get_completion_rate(),
            "estimation_accuracy": task.get_estimation_accuracy(),
            "total_focus_minutes": task.get_actual_duration(),
            "interruptions": sum(p.interruption_count() for p in task.completed_pomodoros),
            "is_overdue": task.is_overdue(),
        }
