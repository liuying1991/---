"""
Context Awareness - 情境感知系统

核心能力:
1. 时间感知：时段/星期/季节/节假日判断
2. 习惯感知：用户行为模式学习与识别
3. 环境感知：设备/位置/活动状态
4. 用户状态感知：情绪/注意力/疲劳度

设计原则:
- 从用户交互历史中自动学习模式
- 根据情境动态调整Jarvis行为
- 轻量级，不依赖外部模型

参考:
- 情境计算理论(Dey & Abowd)
- 用户习惯学习模型
- 注意力资源管理
"""
import time
import sqlite3
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from collections import defaultdict


class TimeOfDay(Enum):
    """时段"""
    EARLY_MORNING = "early_morning"    # 05-08
    MORNING = "morning"                # 08-12
    AFTERNOON = "afternoon"            # 12-14
    LATE_AFTERNOON = "late_afternoon"  # 14-18
    EVENING = "evening"                # 18-22
    NIGHT = "night"                    # 22-01
    LATE_NIGHT = "late_night"          # 01-05


class DayType(Enum):
    """日类型"""
    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


class ActivityState(Enum):
    """活动状态"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    FOCUSED = "focused"
    DISTRACTED = "distracted"


class UserMood(Enum):
    """用户情绪倾向"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    STRESSED = "stressed"
    RELAXED = "relaxed"


@dataclass
class ContextSnapshot:
    """情境快照"""
    timestamp: float
    time_of_day: TimeOfDay
    day_type: DayType
    activity_state: ActivityState
    user_mood: UserMood
    interaction_count: int = 0
    recent_topics: List[str] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HabitPattern:
    """习惯模式"""
    pattern_id: str
    name: str
    trigger_conditions: Dict[str, Any]
    frequency: float
    confidence: float
    last_seen: float
    created_at: float


@dataclass
class EnvironmentInfo:
    """环境信息"""
    device: str = "unknown"
    location: str = "unknown"
    is_moving: bool = False
    ambient_noise: str = "quiet"  # quiet/moderate/loud
    network_quality: str = "good"  # good/fair/poor


class TimeAwareness:
    """时间感知"""

    # 自定义节假日
    CUSTOM_HOLIDAYS: Dict[str, str] = {}

    def get_time_of_day(self, hour: int = None) -> TimeOfDay:
        """获取当前时段"""
        if hour is None:
            hour = datetime.now().hour

        if 5 <= hour < 8:
            return TimeOfDay.EARLY_MORNING
        elif 8 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 14:
            return TimeOfDay.AFTERNOON
        elif 14 <= hour < 18:
            return TimeOfDay.LATE_AFTERNOON
        elif 18 <= hour < 22:
            return TimeOfDay.EVENING
        elif 22 <= hour or hour < 1:
            return TimeOfDay.NIGHT
        else:
            return TimeOfDay.LATE_NIGHT

    def get_day_type(self, dt: datetime = None) -> DayType:
        """获取日类型"""
        if dt is None:
            dt = datetime.now()

        weekday = dt.weekday()
        if weekday >= 5:
            return DayType.WEEKEND

        # 检查自定义节假日
        date_str = dt.strftime("%Y-%m-%d")
        if date_str in self.CUSTOM_HOLIDAYS:
            return DayType.HOLIDAY

        return DayType.WEEKDAY

    def get_greeting(self, hour: int = None) -> str:
        """获取时段问候语"""
        tod = self.get_time_of_day(hour)
        greetings = {
            TimeOfDay.EARLY_MORNING: "早上好，新的一天开始了",
            TimeOfDay.MORNING: "上午好",
            TimeOfDay.AFTERNOON: "中午好，注意休息",
            TimeOfDay.LATE_AFTERNOON: "下午好",
            TimeOfDay.EVENING: "晚上好",
            TimeOfDay.NIGHT: "夜深了，注意早点休息",
            TimeOfDay.LATE_NIGHT: "很晚了，您还好吗？注意休息",
        }
        return greetings.get(tod, "你好")

    def is_work_hours(self, hour: int = None) -> bool:
        """是否工作时间（9-18点，工作日）"""
        if hour is None:
            now = datetime.now()
            hour = now.hour
            day_type = self.get_day_type(now)
        else:
            day_type = DayType.WEEKDAY

        return (9 <= hour < 18) and (day_type == DayType.WEEKDAY)

    def is_sleep_time(self, hour: int = None) -> bool:
        """是否睡眠时间（23-7点）"""
        if hour is None:
            hour = datetime.now().hour
        return hour >= 23 or hour < 7

    def get_context_description(self, hour: int = None, dt: datetime = None) -> str:
        """获取情境描述"""
        tod = self.get_time_of_day(hour)
        day_type = self.get_day_type(dt)

        descriptions = {
            TimeOfDay.EARLY_MORNING: "清晨",
            TimeOfDay.MORNING: "上午",
            TimeOfDay.AFTERNOON: "中午",
            TimeOfDay.LATE_AFTERNOON: "下午",
            TimeOfDay.EVENING: "傍晚",
            TimeOfDay.NIGHT: "夜晚",
            TimeOfDay.LATE_NIGHT: "深夜",
        }

        day_desc = {
            DayType.WEEKDAY: "工作日",
            DayType.WEEKEND: "周末",
            DayType.HOLIDAY: "节假日",
        }

        return f"{descriptions.get(tod, '')}，{day_desc.get(day_type, '')}"


class HabitTracker:
    """习惯追踪器"""

    def __init__(self, db_path: str = "data/habits.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._interaction_log: List[Dict] = []

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                topic TEXT DEFAULT '',
                hour INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_patterns (
                pattern_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                trigger_conditions TEXT NOT NULL,
                frequency REAL DEFAULT 0,
                confidence REAL DEFAULT 0,
                last_seen REAL NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_interaction_time ON interaction_log(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_interaction_user ON interaction_log(user_id)
        """)
        self.conn.commit()

    def log_interaction(self, user_id: str, action_type: str,
                        topic: str = "", timestamp: float = None):
        """
        记录交互

        Args:
            user_id: 用户ID
            action_type: 操作类型 (chat/query/command/learn)
            topic: 话题
            timestamp: 时间戳
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)

        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO interaction_log
               (timestamp, user_id, action_type, topic, hour, day_of_week)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ts, user_id, action_type, topic, dt.hour, dt.weekday())
        )
        self.conn.commit()

        self._interaction_log.append({
            "timestamp": ts,
            "user_id": user_id,
            "action_type": action_type,
            "topic": topic,
            "hour": dt.hour,
            "day_of_week": dt.weekday(),
        })

    def get_active_hours(self, user_id: str, days: int = 7) -> List[int]:
        """
        获取用户活跃时段

        Args:
            user_id: 用户ID
            days: 分析天数

        Returns:
            活跃小时列表（按频率降序）
        """
        cutoff = time.time() - (days * 86400)
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT hour, COUNT(*) as cnt
               FROM interaction_log
               WHERE user_id = ? AND timestamp > ?
               GROUP BY hour
               ORDER BY cnt DESC""",
            (user_id, cutoff)
        )
        return [row["hour"] for row in cursor.fetchall()]

    def get_active_days(self, user_id: str, days: int = 30) -> List[int]:
        """
        获取用户活跃日

        Args:
            user_id: 用户ID
            days: 分析天数

        Returns:
            活跃星期列表（0=周一，按频率降序）
        """
        cutoff = time.time() - (days * 86400)
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT day_of_week, COUNT(*) as cnt
               FROM interaction_log
               WHERE user_id = ? AND timestamp > ?
               GROUP BY day_of_week
               ORDER BY cnt DESC""",
            (user_id, cutoff)
        )
        return [row["day_of_week"] for row in cursor.fetchall()]

    def get_top_topics(self, user_id: str, days: int = 7, limit: int = 5) -> List[str]:
        """
        获取热门话题

        Args:
            user_id: 用户ID
            days: 分析天数
            limit: 返回数量

        Returns:
            热门话题列表
        """
        cutoff = time.time() - (days * 86400)
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT topic, COUNT(*) as cnt
               FROM interaction_log
               WHERE user_id = ? AND timestamp > ? AND topic != ''
               GROUP BY topic
               ORDER BY cnt DESC
               LIMIT ?""",
            (user_id, cutoff, limit)
        )
        return [row["topic"] for row in cursor.fetchall()]

    def get_interaction_count(self, user_id: str, hours: int = 24) -> int:
        """获取指定时间内的交互次数"""
        cutoff = time.time() - (hours * 3600)
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT COUNT(*) as cnt FROM interaction_log
               WHERE user_id = ? AND timestamp > ?""",
            (user_id, cutoff)
        )
        return cursor.fetchone()["cnt"]

    def detect_patterns(self, user_id: str, min_frequency: int = 3) -> List[HabitPattern]:
        """
        检测习惯模式

        Args:
            user_id: 用户ID
            min_frequency: 最小出现次数

        Returns:
            检测到的习惯模式列表
        """
        patterns = []

        # 检测活跃时段模式
        active_hours = self.get_active_hours(user_id, days=7)
        if len(active_hours) >= min_frequency:
            patterns.append(HabitPattern(
                pattern_id=f"{user_id}_active_hours",
                name="活跃时段",
                trigger_conditions={"hours": active_hours[:3]},
                frequency=len(active_hours),
                confidence=min(1.0, len(active_hours) / 7),
                last_seen=time.time(),
                created_at=time.time(),
            ))

        # 检测活跃日模式
        active_days = self.get_active_days(user_id, days=30)
        if active_days:
            is_weekend_lover = 5 in active_days[:2] or 6 in active_days[:2]
            patterns.append(HabitPattern(
                pattern_id=f"{user_id}_day_preference",
                name="日偏好",
                trigger_conditions={
                    "preferred_days": active_days[:3],
                    "is_weekend_lover": is_weekend_lover,
                },
                frequency=len(active_days),
                confidence=min(1.0, len(active_days) / 5),
                last_seen=time.time(),
                created_at=time.time(),
            ))

        # 检测话题模式
        top_topics = self.get_top_topics(user_id, days=7)
        if top_topics:
            patterns.append(HabitPattern(
                pattern_id=f"{user_id}_topic_preference",
                name="话题偏好",
                trigger_conditions={"topics": top_topics},
                frequency=len(top_topics),
                confidence=min(1.0, len(top_topics) / 3),
                last_seen=time.time(),
                created_at=time.time(),
            ))

        return patterns

    def get_user_activity_summary(self, user_id: str) -> Dict:
        """获取用户活动摘要"""
        return {
            "interactions_24h": self.get_interaction_count(user_id, hours=24),
            "interactions_7d": self.get_interaction_count(user_id, hours=168),
            "active_hours": self.get_active_hours(user_id),
            "active_days": self.get_active_days(user_id),
            "top_topics": self.get_top_topics(user_id),
        }


class EnvironmentTracker:
    """环境追踪器"""

    def __init__(self):
        self._environments: Dict[str, EnvironmentInfo] = {}

    def set_environment(self, user_id: str, info: EnvironmentInfo):
        """设置用户环境"""
        self._environments[user_id] = info

    def get_environment(self, user_id: str) -> EnvironmentInfo:
        """获取用户环境"""
        return self._environments.get(user_id, EnvironmentInfo())

    def simulate_context(self, hour: int = None, day_type: DayType = None,
                         activity: ActivityState = None,
                         mood: UserMood = None) -> ContextSnapshot:
        """
        模拟情境（用于测试）

        Args:
            hour: 小时
            day_type: 日类型
            activity: 活动状态
            mood: 情绪倾向

        Returns:
            情境快照
        """
        time_awareness = TimeAwareness()
        return ContextSnapshot(
            timestamp=time.time(),
            time_of_day=time_awareness.get_time_of_day(hour),
            day_type=day_type or time_awareness.get_day_type(),
            activity_state=activity or ActivityState.ACTIVE,
            user_mood=mood or UserMood.NEUTRAL,
        )


class ContextAwarenessEngine:
    """情境感知引擎

    整合时间感知、习惯追踪、环境追踪，
    为Jarvis提供全面的情境感知能力。
    """

    def __init__(self, data_dir: str = "data"):
        os.makedirs(data_dir, exist_ok=True)
        self.time_awareness = TimeAwareness()
        self.habit_tracker = HabitTracker(
            db_path=os.path.join(data_dir, "habits.db")
        )
        self.environment_tracker = EnvironmentTracker()
        self._context_history: Dict[str, List[ContextSnapshot]] = defaultdict(list)

    def get_current_context(self, user_id: str) -> ContextSnapshot:
        """
        获取当前情境

        Args:
            user_id: 用户ID

        Returns:
            情境快照
        """
        now = datetime.now()
        time_of_day = self.time_awareness.get_time_of_day(now.hour)
        day_type = self.time_awareness.get_day_type(now)

        # 估算活动状态
        interaction_count = self.habit_tracker.get_interaction_count(user_id, hours=1)
        if interaction_count > 10:
            activity = ActivityState.BUSY
        elif interaction_count > 3:
            activity = ActivityState.ACTIVE
        else:
            activity = ActivityState.IDLE

        snapshot = ContextSnapshot(
            timestamp=time.time(),
            time_of_day=time_of_day,
            day_type=day_type,
            activity_state=activity,
            user_mood=UserMood.NEUTRAL,
            interaction_count=interaction_count,
            recent_topics=self.habit_tracker.get_top_topics(user_id, days=1, limit=3),
            environment={
                "device": self.environment_tracker.get_environment(user_id).device,
                "location": self.environment_tracker.get_environment(user_id).location,
            },
        )

        self._context_history[user_id].append(snapshot)
        return snapshot

    def log_interaction(self, user_id: str, action_type: str,
                        topic: str = ""):
        """记录交互到习惯追踪器"""
        self.habit_tracker.log_interaction(user_id, action_type, topic)

    def get_habit_patterns(self, user_id: str) -> List[HabitPattern]:
        """获取用户习惯模式"""
        return self.habit_tracker.detect_patterns(user_id)

    def get_adaptive_greeting(self, user_id: str) -> str:
        """
        获取个性化问候

        Args:
            user_id: 用户ID

        Returns:
            问候语
        """
        context = self.get_current_context(user_id)
        base_greeting = self.time_awareness.get_greeting()

        # 根据时段调整
        if context.time_of_day == TimeOfDay.LATE_NIGHT:
            return f"{base_greeting}。这么晚了还在忙吗？"
        elif context.time_of_day == TimeOfDay.EARLY_MORNING:
            return f"{base_greeting}！今天有什么计划？"

        # 根据活动状态调整
        if context.activity_state == ActivityState.BUSY:
            return f"{base_greeting}。看起来您很忙，需要我帮忙处理什么吗？"
        elif context.activity_state == ActivityState.IDLE:
            return f"{base_greeting}。最近有什么新的想法？"

        return base_greeting

    def should_proactive_alert(self, user_id: str) -> bool:
        """
        判断是否应该主动提醒

        Args:
            user_id: 用户ID

        Returns:
            是否应该提醒
        """
        context = self.get_current_context(user_id)

        # 睡眠时间不打扰
        if self.time_awareness.is_sleep_time():
            return False

        # 忙碌时不打扰
        if context.activity_state == ActivityState.BUSY:
            return False

        # 深夜不打扰
        if context.time_of_day in (TimeOfDay.LATE_NIGHT, TimeOfDay.NIGHT):
            return False

        # 周末早晨不打扰
        if context.day_type == DayType.WEEKEND and context.time_of_day == TimeOfDay.EARLY_MORNING:
            return False

        return True

    def get_user_activity_summary(self, user_id: str) -> Dict:
        """获取用户活动摘要"""
        return self.habit_tracker.get_user_activity_summary(user_id)

    def close(self):
        """关闭数据库连接"""
        if self.habit_tracker.conn:
            self.habit_tracker.conn.close()
