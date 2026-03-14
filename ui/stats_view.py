"""
统计视图 - 数据统计与报表界面
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta

from data.repository import TaskRepository
from core.statistics import StatisticsEngine


class StatsView:
    """统计视图"""
    
    def __init__(
        self,
        parent: tk.Widget,
        repository: TaskRepository,
    ):
        self.parent = parent
        self.repository = repository
        self.statistics = StatisticsEngine(repository)
        
        self.frame = tk.Frame(parent, bg="#f5f6fa")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 顶部工具栏
        self.toolbar = tk.Frame(self.frame, bg="#ffffff", height=50)
        self.toolbar.pack(fill=tk.X, pady=(0, 10))
        self.toolbar.pack_propagate(False)
        
        # 标题
        title_label = tk.Label(
            self.toolbar,
            text="数据统计",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#ffffff",
            fg="#2d3436",
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # 刷新按钮
        refresh_btn = tk.Button(
            self.toolbar,
            text="🔄 刷新",
            font=("Microsoft YaHei", 10),
            bg="#74b9ff",
            fg="white",
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.refresh,
        )
        refresh_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # 内容区（带滚动条）
        content_container = tk.Frame(self.frame, bg="#f5f6fa")
        content_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(content_container, bg="#f5f6fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            content_container,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.content_frame = tk.Frame(canvas, bg="#f5f6fa")
        canvas_window = canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor=tk.NW,
        )
        
        # 绑定滚动
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        self.content_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # 初始化显示
        self.refresh()
    
    def _create_stat_card(self, parent, title, value, subtitle="", color="#3498db"):
        """创建统计卡片"""
        card = tk.Frame(
            parent,
            bg="white",
            highlightbackground="#dfe6e9",
            highlightthickness=1,
            padx=20,
            pady=15,
        )
        
        tk.Label(
            card,
            text=title,
            font=("Microsoft YaHei", 11),
            bg="white",
            fg="#636e72",
        ).pack(anchor=tk.W)
        
        tk.Label(
            card,
            text=str(value),
            font=("Microsoft YaHei", 28, "bold"),
            bg="white",
            fg=color,
        ).pack(anchor=tk.W, pady=5)
        
        if subtitle:
            tk.Label(
                card,
                text=subtitle,
                font=("Microsoft YaHei", 9),
                bg="white",
                fg="#b2bec3",
            ).pack(anchor=tk.W)
        
        return card
    
    def _render_daily_stats(self):
        """渲染今日统计"""
        # 获取今日报告
        daily_report = self.statistics.daily_report()
        
        # 今日统计区域
        section = tk.LabelFrame(
            self.content_frame,
            text=" 今日概览 ",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#f5f6fa",
            fg="#2d3436",
            padx=15,
            pady=10,
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        # 卡片容器
        cards_frame = tk.Frame(section, bg="#f5f6fa")
        cards_frame.pack(fill=tk.X)
        
        # 番茄数卡片
        card1 = self._create_stat_card(
            cards_frame,
            "完成番茄",
            daily_report.completed_pomodoros,
            f"总计 {daily_report.total_pomodoros} 个",
            "#00b894",
        )
        card1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 专注时间卡片
        focus_hours = daily_report.focus_minutes / 60
        card2 = self._create_stat_card(
            cards_frame,
            "专注时间",
            f"{focus_hours:.1f}",
            "小时",
            "#3498db",
        )
        card2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 完成任务卡片
        card3 = self._create_stat_card(
            cards_frame,
            "完成任务",
            daily_report.total_tasks_completed,
            f"新建 {daily_report.total_tasks_created} 个",
            "#9b59b6",
        )
        card3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 中断次数卡片
        card4 = self._create_stat_card(
            cards_frame,
            "中断次数",
            daily_report.total_interruptions,
            "今天",
            "#e74c3c" if daily_report.total_interruptions > 5 else "#f39c12",
        )
        card4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _render_weekly_stats(self):
        """渲染本周统计"""
        weekly_report = self.statistics.weekly_report()
        
        section = tk.LabelFrame(
            self.content_frame,
            text=" 本周概览 ",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#f5f6fa",
            fg="#2d3436",
            padx=15,
            pady=10,
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        # 卡片容器
        cards_frame = tk.Frame(section, bg="#f5f6fa")
        cards_frame.pack(fill=tk.X)
        
        # 本周番茄
        card1 = self._create_stat_card(
            cards_frame,
            "本周番茄",
            weekly_report.total_pomodoros,
            f"日均 {weekly_report.avg_pomodoros_per_day:.1f} 个",
            "#00b894",
        )
        card1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 专注时长
        card2 = self._create_stat_card(
            cards_frame,
            "专注时长",
            f"{weekly_report.total_focus_hours:.1f}",
            "小时",
            "#3498db",
        )
        card2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 最佳一天
        best_day_text = weekly_report.best_day.strftime("%m月%d日") if weekly_report.best_day else "无"
        card3 = self._create_stat_card(
            cards_frame,
            "最佳一天",
            best_day_text,
            f"{weekly_report.best_day_pomodoros} 个番茄",
            "#f39c12",
        )
        card3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 任务完成率
        completion_rate = weekly_report.completion_rate * 100
        card4 = self._create_stat_card(
            cards_frame,
            "任务完成率",
            f"{completion_rate:.0f}%",
            "本周创建的任务",
            "#9b59b6" if completion_rate >= 80 else "#e74c3c",
        )
        card4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _render_streak_stats(self):
        """渲染连续记录统计"""
        streak_data = self.statistics.streak_calculation()
        
        section = tk.LabelFrame(
            self.content_frame,
            text=" 连续记录 ",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#f5f6fa",
            fg="#2d3436",
            padx=15,
            pady=10,
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        # 卡片容器
        cards_frame = tk.Frame(section, bg="#f5f6fa")
        cards_frame.pack(fill=tk.X)
        
        # 当前连续
        card1 = self._create_stat_card(
            cards_frame,
            "当前连续",
            f"{streak_data['current_streak']} 天",
            "保持下去！" if streak_data['current_streak'] > 0 else "开始今天的第一番茄吧",
            "#e74c3c" if streak_data['current_streak'] > 7 else "#f39c12",
        )
        card1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 最长连续
        card2 = self._create_stat_card(
            cards_frame,
            "最长连续",
            f"{streak_data['longest_streak']} 天",
            "历史记录",
            "#9b59b6",
        )
        card2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 活跃天数
        card3 = self._create_stat_card(
            cards_frame,
            "活跃天数",
            streak_data['total_active_days'],
            "总计",
            "#3498db",
        )
        card3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _render_estimation_accuracy(self):
        """渲染预估准确度"""
        accuracy_data = self.statistics.estimation_accuracy()
        
        section = tk.LabelFrame(
            self.content_frame,
            text=" 预估准确度 ",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#f5f6fa",
            fg="#2d3436",
            padx=15,
            pady=10,
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        if accuracy_data.get('total_analyzed', 0) == 0:
            tk.Label(
                section,
                text="暂无足够数据进行预估准确度分析",
                font=("Microsoft YaHei", 11),
                bg="#f5f6fa",
                fg="#636e72",
            ).pack(pady=20)
            return
        
        # 卡片容器
        cards_frame = tk.Frame(section, bg="#f5f6fa")
        cards_frame.pack(fill=tk.X)
        
        # 准确度
        accuracy_rate = accuracy_data.get('accuracy_rate', 0) * 100
        card1 = self._create_stat_card(
            cards_frame,
            "预估准确",
            f"{accuracy_rate:.0f}%",
            f"{accuracy_data.get('accurate_count', 0)}/{accuracy_data.get('total_analyzed', 0)} 个任务",
            "#00b894" if accuracy_rate >= 70 else "#f39c12",
        )
        card1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 低估数量
        card2 = self._create_stat_card(
            cards_frame,
            "低估任务",
            accuracy_data.get('underestimated_count', 0),
            "实际耗时超过预估",
            "#e74c3c",
        )
        card2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 高估数量
        card3 = self._create_stat_card(
            cards_frame,
            "高估任务",
            accuracy_data.get('overestimated_count', 0),
            "实际耗时少于预估",
            "#3498db",
        )
        card3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _render_productivity_tips(self):
        """渲染生产力提示"""
        best_hours_data = self.statistics.best_working_hours()
        
        section = tk.LabelFrame(
            self.content_frame,
            text=" 生产力洞察 ",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#f5f6fa",
            fg="#2d3436",
            padx=15,
            pady=10,
        )
        section.pack(fill=tk.X, padx=10, pady=10)
        
        tips_frame = tk.Frame(section, bg="#f5f6fa")
        tips_frame.pack(fill=tk.X, pady=10)
        
        # 最佳工作时段
        if best_hours_data['best_hours']:
            best = best_hours_data['best_hours'][0]
            tip_text = f"💡 您的最佳工作时段是 {best['hour']}:00-{best['hour']+1}:00，平均完成 {best['count']:.1f} 个番茄"
            tk.Label(
                tips_frame,
                text=tip_text,
                font=("Microsoft YaHei", 11),
                bg="#f5f6fa",
                fg="#2d3436",
                wraplength=800,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=5)
        
        # 通用提示
        tips = [
            "🎯 将大任务拆分为多个番茄，更容易开始",
            "⏰ 在最佳工作时段安排最重要的任务",
            "📝 记录中断有助于识别干扰源",
            "🔄 定期回顾预估准确度，提升时间感知",
        ]
        
        for tip in tips:
            tk.Label(
                tips_frame,
                text=tip,
                font=("Microsoft YaHei", 10),
                bg="#f5f6fa",
                fg="#636e72",
                wraplength=800,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=3)
    
    def refresh(self):
        """刷新统计"""
        # 清除现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 渲染各个统计区域
        self._render_daily_stats()
        self._render_weekly_stats()
        self._render_streak_stats()
        self._render_estimation_accuracy()
        self._render_productivity_tips()
    
    def show(self):
        """显示视图"""
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.refresh()
    
    def hide(self):
        """隐藏视图"""
        self.frame.pack_forget()
