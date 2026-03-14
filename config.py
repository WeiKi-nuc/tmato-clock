"""
应用程序配置
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 数据库路径
DATABASE_PATH = os.path.join(DATA_DIR, "pomodoro.db")

# 配置文件路径
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

# 默认番茄钟设置（分钟）
DEFAULT_POMODORO_SETTINGS = {
    "focus_duration": 25,
    "short_break_duration": 5,
    "long_break_duration": 15,
    "pomodoros_until_long_break": 4,
    "auto_start_breaks": False,
    "auto_start_pomodoros": False,
    "strict_mode": False,  # 严格模式下不可暂停
}

# 预设方案
TIMER_PRESETS = {
    "标准番茄": {
        "focus_duration": 25,
        "short_break_duration": 5,
        "long_break_duration": 15,
        "pomodoros_until_long_break": 4,
    },
    "短番茄": {
        "focus_duration": 15,
        "short_break_duration": 3,
        "long_break_duration": 10,
        "pomodoros_until_long_break": 4,
    },
    "长专注": {
        "focus_duration": 50,
        "short_break_duration": 10,
        "long_break_duration": 30,
        "pomodoros_until_long_break": 3,
    },
}

# 看板默认列
DEFAULT_COLUMNS = [
    {"id": "todo", "name": "待办", "color": "#ff6b6b", "wip_limit": None},
    {"id": "in_progress", "name": "进行中", "color": "#4ecdc4", "wip_limit": 3},
    {"id": "done", "name": "完成", "color": "#95e1d3", "wip_limit": None},
]

# 优先级配置
PRIORITY_LEVELS = {
    "urgent_important": {"name": "紧急且重要", "color": "#ff4757"},
    "urgent_not_important": {"name": "紧急不重要", "color": "#ffa502"},
    "not_urgent_important": {"name": "重要不紧急", "color": "#2ed573"},
    "not_urgent_not_important": {"name": "不紧急不重要", "color": "#747d8c"},
}

# 默认标签
DEFAULT_TAGS = [
    {"name": "工作", "color": "#3498db"},
    {"name": "学习", "color": "#9b59b6"},
    {"name": "个人", "color": "#e74c3c"},
    {"name": "健康", "color": "#2ecc71"},
]

# UI主题
THEME = {
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8f9fa",
    "bg_card": "#ffffff",
    "text_primary": "#2d3436",
    "text_secondary": "#636e72",
    "accent_color": "#ff6b6b",
    "success_color": "#00b894",
    "warning_color": "#fdcb6e",
    "danger_color": "#d63031",
    "border_color": "#dfe6e9",
    "shadow_color": "#b2bec3",
}
