"""
智能调度器 - 任务推荐与计划优化
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

from models.task import Task
from models.kanban_board import KanbanBoard
from data.repository import TaskRepository
from core.statistics import StatisticsEngine


class SmartScheduler:
    """智能调度器 - 负责任务推荐与计划优化"""
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
        self.statistics = StatisticsEngine(repository)
    
    def suggest_next_task(
        self,
        current_time: Optional[datetime] = None,
        energy_level: str = "medium",  # high / medium / low
    ) -> Optional[Task]:
        """
        基于截止时间、优先级、历史效率推荐下一个任务
        
        评分因素：
        1. 紧急度（截止日期临近程度）
        2. 重要性（优先级）
        3. 时间匹配度（当前时段历史效率）
        4. 预估工作量匹配度
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 获取待办和进行中的任务
        todo_tasks = self.repository.get_tasks_by_column("todo")
        in_progress_tasks = self.repository.get_tasks_by_column("in_progress")
        
        # 优先推荐进行中的任务
        if in_progress_tasks:
            # 按截止日期排序
            in_progress_tasks.sort(
                key=lambda t: (t.due_date or date.max, self._priority_weight(t.priority)),
                reverse=True
            )
            return in_progress_tasks[0]
        
        if not todo_tasks:
            return None
        
        # 计算每个任务的得分
        task_scores = []
        for task in todo_tasks:
            score = self._calculate_task_score(task, current_time, energy_level)
            task_scores.append((task, score))
        
        # 按得分排序
        task_scores.sort(key=lambda x: x[1], reverse=True)
        
        return task_scores[0][0] if task_scores else None
    
    def _calculate_task_score(
        self,
        task: Task,
        current_time: datetime,
        energy_level: str,
    ) -> float:
        """计算任务推荐得分"""
        score = 0.0
        
        # 1. 紧急度得分（截止日期）
        if task.due_date:
            days_until_due = (task.due_date - current_time.date()).days
            if days_until_due < 0:
                score += 100  # 已逾期，最高优先级
            elif days_until_due == 0:
                score += 80   # 今天到期
            elif days_until_due == 1:
                score += 60   # 明天到期
            elif days_until_due <= 3:
                score += 40   # 3天内到期
            elif days_until_due <= 7:
                score += 20   # 一周内到期
        
        # 2. 优先级得分
        priority_weights = {
            "urgent_important": 50,
            "urgent_not_important": 30,
            "not_urgent_important": 20,
            "not_urgent_not_important": 5,
        }
        score += priority_weights.get(task.priority, 0)
        
        # 3. 精力匹配度
        estimated_minutes = task.estimated_pomodoros * 25
        if energy_level == "high":
            # 精力充沛时推荐较难/较长的任务
            if estimated_minutes >= 50:
                score += 15
        elif energy_level == "low":
            # 精力低时推荐简单/短的任务
            if estimated_minutes <= 25:
                score += 15
        else:
            # 中等精力，适中任务
            if 25 <= estimated_minutes <= 50:
                score += 10
        
        # 4. 预估准确度加成（如果之前完成过类似任务）
        accuracy = task.get_estimation_accuracy()
        if accuracy is not None:
            # 预估准确的任务更可靠
            if 0.8 <= accuracy <= 1.2:
                score += 5
        
        return score
    
    def _priority_weight(self, priority: str) -> int:
        """获取优先级权重"""
        weights = {
            "urgent_important": 4,
            "urgent_not_important": 3,
            "not_urgent_important": 2,
            "not_urgent_not_important": 1,
        }
        return weights.get(priority, 0)
    
    def optimal_sequence(self, task_ids: List[str]) -> List[str]:
        """
        对选定任务排序以最小化上下文切换成本
        
        策略：
        1. 相同标签的任务放在一起
        2. 相似预估时长的任务放在一起
        3. 高优先级任务优先
        """
        tasks = []
        for task_id in task_ids:
            task = self.repository.get_task_by_id(task_id)
            if task:
                tasks.append(task)
        
        if not tasks:
            return []
        
        # 按优先级分组
        priority_groups = {
            "urgent_important": [],
            "urgent_not_important": [],
            "not_urgent_important": [],
            "not_urgent_not_important": [],
        }
        
        for task in tasks:
            if task.priority in priority_groups:
                priority_groups[task.priority].append(task)
        
        # 对每个优先级组内的任务进行排序
        result = []
        for priority in ["urgent_important", "not_urgent_important", "urgent_not_important", "not_urgent_not_important"]:
            group = priority_groups[priority]
            
            # 按标签和预估时长排序
            group.sort(key=lambda t: (
                tuple(sorted(t.tags)) if t.tags else (),
                t.estimated_pomodoros,
            ))
            
            result.extend([t.id for t in group])
        
        return result
    
    def daily_plan_suggestion(
        self,
        available_pomodoros: int,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        给定番茄数分配任务建议
        
        返回：
        - 建议执行的任务列表
        - 预估完成率
        - 风险提示
        """
        if target_date is None:
            target_date = date.today()
        
        # 获取待办任务
        todo_tasks = self.repository.get_tasks_by_column("todo")
        
        # 过滤出今天到期的和优先级高的任务
        urgent_tasks = []
        important_tasks = []
        other_tasks = []
        
        for task in todo_tasks:
            if task.due_date and task.due_date <= target_date:
                urgent_tasks.append(task)
            elif task.priority in ["urgent_important", "not_urgent_important"]:
                important_tasks.append(task)
            else:
                other_tasks.append(task)
        
        # 按优先级排序
        urgent_tasks.sort(key=lambda t: self._priority_weight(t.priority), reverse=True)
        important_tasks.sort(key=lambda t: self._priority_weight(t.priority), reverse=True)
        
        # 分配番茄
        suggested_tasks = []
        remaining_pomodoros = available_pomodoros
        
        # 先分配紧急任务
        for task in urgent_tasks:
            if remaining_pomodoros <= 0:
                break
            needed = task.estimated_pomodoros
            if needed <= remaining_pomodoros:
                suggested_tasks.append({
                    "task": task,
                    "planned_pomodoros": needed,
                })
                remaining_pomodoros -= needed
            else:
                # 部分完成
                suggested_tasks.append({
                    "task": task,
                    "planned_pomodoros": remaining_pomodoros,
                })
                remaining_pomodoros = 0
        
        # 再分配重要任务
        for task in important_tasks:
            if remaining_pomodoros <= 0:
                break
            needed = task.estimated_pomodoros
            if needed <= remaining_pomodoros:
                suggested_tasks.append({
                    "task": task,
                    "planned_pomodoros": needed,
                })
                remaining_pomodoros -= needed
        
        # 计算预估完成率
        total_estimated = sum(t["planned_pomodoros"] for t in suggested_tasks)
        completion_rate = total_estimated / available_pomodoros if available_pomodoros > 0 else 0
        
        # 生成风险提示
        risks = []
        if remaining_pomodoros < 0:
            risks.append("任务量可能超出今日可用时间")
        
        overdue_count = len([t for t in urgent_tasks if t.is_overdue()])
        if overdue_count > 0:
            risks.append(f"有 {overdue_count} 个任务已逾期")
        
        # 检查WIP限制
        in_progress = self.repository.get_tasks_by_column("in_progress")
        wip_limit = 3  # 默认WIP限制
        if len(in_progress) >= wip_limit:
            risks.append(f"进行中任务已达上限({wip_limit})，建议先完成现有任务")
        
        return {
            "suggested_tasks": [
                {
                    "task_id": t["task"].id,
                    "title": t["task"].title,
                    "planned_pomodoros": t["planned_pomodoros"],
                    "priority": t["task"].priority,
                    "due_date": t["task"].due_date.isoformat() if t["task"].due_date else None,
                }
                for t in suggested_tasks
            ],
            "total_planned_pomodoros": total_estimated,
            "remaining_pomodoros": remaining_pomodoros,
            "completion_rate": completion_rate,
            "risks": risks,
        }
    
    def detect_overload(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """检测某天任务是否超负荷"""
        if target_date is None:
            target_date = date.today()
        
        # 获取当天到期的任务
        all_tasks = self.repository.get_all_tasks()
        due_tasks = [
            t for t in all_tasks 
            if t.due_date == target_date and t.column_id != "done"
        ]
        
        # 计算需要的番茄数
        total_pomodoros_needed = sum(t.estimated_pomodoros for t in due_tasks)
        
        # 假设一天最多8个番茄（约4小时深度工作）
        max_daily_pomodoros = 8
        
        is_overloaded = total_pomodoros_needed > max_daily_pomodoros
        
        return {
            "date": target_date.isoformat(),
            "total_tasks": len(due_tasks),
            "total_pomodoros_needed": total_pomodoros_needed,
            "max_daily_pomodoros": max_daily_pomodoros,
            "is_overloaded": is_overloaded,
            "overload_ratio": total_pomodoros_needed / max_daily_pomodoros if max_daily_pomodoros > 0 else 0,
            "suggestions": [
                "考虑将部分任务延期" if is_overloaded else "今日任务量适中",
                "优先完成高优先级任务",
                "可考虑拆分大任务",
            ],
        }
    
    def get_similar_tasks(self, task_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """获取与指定任务相似的任务（用于番茄配对）"""
        target_task = self.repository.get_task_by_id(task_id)
        if not target_task:
            return []
        
        # 获取待办任务
        todo_tasks = self.repository.get_tasks_by_column("todo")
        
        # 计算相似度
        similar_tasks = []
        for task in todo_tasks:
            if task.id == task_id:
                continue
            
            score = 0
            # 标签相似度
            common_tags = set(target_task.tags) & set(task.tags)
            score += len(common_tags) * 10
            
            # 优先级相似度
            if task.priority == target_task.priority:
                score += 5
            
            # 预估时长相似度
            diff = abs(task.estimated_pomodoros - target_task.estimated_pomodoros)
            score += max(0, 5 - diff)
            
            similar_tasks.append({
                "task": task,
                "similarity_score": score,
            })
        
        # 按相似度排序
        similar_tasks.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return [
            {
                "task_id": t["task"].id,
                "title": t["task"].title,
                "similarity_score": t["similarity_score"],
            }
            for t in similar_tasks[:limit]
        ]
