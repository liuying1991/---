"""
情感追踪器 (Emotion Tracker)

追踪用户情感变化，提供情感响应策略
设计原则：基于关键词/启发式的简单情感检测，趋势分析，共情回复生成
第一性原理：情商意味着识别情感并适当回应，而非假装情感
"""
import os
import re
import sqlite3
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import Counter


class Emotion(Enum):
    """情感类型"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    BORED = "bored"
    CONFUSED = "confused"


@dataclass
class EmotionRecord:
    """情感记录"""
    timestamp: str
    emotion: str
    intensity: float  # 0-1
    trigger_message: str
    context: Optional[str] = None


@dataclass
class EmotionalTrend:
    """情感趋势"""
    avg_emotion: str  # 平均情感标签
    dominant_emotion: str  # 主导情感
    volatility: float  # 波动性 (0-1)
    trend_direction: str  # improving / stable / declining


# 情感分值映射（用于趋势计算）
EMOTION_SCORES = {
    Emotion.HAPPY: 0.8,
    Emotion.EXCITED: 1.0,
    Emotion.NEUTRAL: 0.5,
    Emotion.BORED: 0.3,
    Emotion.CONFUSED: 0.35,
    Emotion.ANXIOUS: 0.2,
    Emotion.SAD: 0.1,
    Emotion.FRUSTRATED: 0.15,
    Emotion.ANGRY: 0.0,
}

# 情感响应策略
RESPONSE_STRATEGIES = {
    Emotion.HAPPY: "分享喜悦，积极回应，适当延伸话题",
    Emotion.EXCITED: "热情回应，鼓励探索，提供更多信息",
    Emotion.SAD: "表达同理心，温和回应，提供支持和建议",
    Emotion.ANGRY: "保持冷静，倾听理解，不争论，帮助解决问题",
    Emotion.ANXIOUS: "安抚情绪，提供确定性，逐步引导",
    Emotion.NEUTRAL: "保持专业，高效回应",
    Emotion.FRUSTRATED: "表达理解，提供明确帮助，简化问题",
    Emotion.BORED: "引入新话题，增加互动性，提供有趣内容",
    Emotion.CONFUSED: "耐心解释，使用简单语言，举例说明",
}


class EmotionTracker:
    """情感追踪器"""

    # 关键词 → 情感映射
    KEYWORD_MAP: Dict[str, Emotion] = {
        # 开心
        "开心": Emotion.HAPPY, "高兴": Emotion.HAPPY, "快乐": Emotion.HAPPY,
        "太好了": Emotion.HAPPY, "棒": Emotion.HAPPY, "好耶": Emotion.HAPPY,
        "哈哈": Emotion.HAPPY, "嘻嘻": Emotion.HAPPY, "笑": Emotion.HAPPY,
        "nice": Emotion.HAPPY, "great": Emotion.HAPPY, "awesome": Emotion.HAPPY,
        "谢谢": Emotion.HAPPY, "感谢": Emotion.HAPPY,
        # 兴奋
        "激动": Emotion.EXCITED, "期待": Emotion.EXCITED, "兴奋": Emotion.EXCITED,
        "哇": Emotion.EXCITED, "wow": Emotion.EXCITED,
        # 悲伤
        "难过": Emotion.SAD, "伤心": Emotion.SAD, "悲伤": Emotion.SAD,
        "哭": Emotion.SAD, "泪": Emotion.SAD, "失落": Emotion.SAD,
        "sad": Emotion.SAD, "unhappy": Emotion.SAD,
        # 愤怒
        "生气": Emotion.ANGRY, "愤怒": Emotion.ANGRY, "恼火": Emotion.ANGRY,
        "混蛋": Emotion.ANGRY, "垃圾": Emotion.ANGRY, "可恶": Emotion.ANGRY,
        "angry": Emotion.ANGRY, "furious": Emotion.ANGRY,
        # 焦虑
        "焦虑": Emotion.ANXIOUS, "担心": Emotion.ANXIOUS, "害怕": Emotion.ANXIOUS,
        "紧张": Emotion.ANXIOUS, "不安": Emotion.ANXIOUS,
        "anxious": Emotion.ANXIOUS, "worried": Emotion.ANXIOUS,
        # 沮丧
        "沮丧": Emotion.FRUSTRATED, "郁闷": Emotion.FRUSTRATED, "烦躁": Emotion.FRUSTRATED,
        "无语": Emotion.FRUSTRATED, "烦": Emotion.FRUSTRATED,
        "frustrated": Emotion.FRUSTRATED, "annoyed": Emotion.FRUSTRATED,
        # 无聊
        "无聊": Emotion.BORED, "没意思": Emotion.BORED, "乏味": Emotion.BORED,
        "bored": Emotion.BORED, "dull": Emotion.BORED,
        # 困惑
        "困惑": Emotion.CONFUSED, "不明白": Emotion.CONFUSED, "不懂": Emotion.CONFUSED,
        "什么": Emotion.CONFUSED, "怎么回事": Emotion.CONFUSED,
        "confused": Emotion.CONFUSED, "don't understand": Emotion.CONFUSED,
    }

    # 强度修饰词
    INTENSITY_BOOSTERS = ["非常", "特别", "极其", "超级", "太", "很", "真的",
                          "extremely", "very", "really", "so", "super"]
    INTENSITY_REDUCE = ["有点", "稍微", "少许", "一点",
                        "a bit", "a little", "slightly"]

    def __init__(self, db_path: str = ":memory:"):
        """
        初始化情感追踪器

        Args:
            db_path: SQLite 数据库路径，默认内存
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._custom_patterns: List[Dict] = []

    def _init_schema(self):
        """初始化数据库表"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS emotion_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    emotion TEXT NOT NULL,
                    intensity REAL NOT NULL DEFAULT 0.5,
                    trigger_message TEXT NOT NULL DEFAULT '',
                    context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_emotion_user ON emotion_records(user_id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_emotion_time ON emotion_records(timestamp)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_emotion_type ON emotion_records(emotion)"
            )

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS emotion_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keywords TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    response_strategy TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def detect_emotion(self, message: str) -> Emotion:
        """
        基于关键词/启发式检测情感

        Args:
            message: 用户消息

        Returns:
            检测到的情感类型
        """
        if not message:
            return Emotion.NEUTRAL

        msg_lower = message.lower()
        emotions_found = []
        intensity_mod = 1.0

        # 检查强度修饰词
        for booster in self.INTENSITY_BOOSTERS:
            if booster in msg_lower:
                intensity_mod = 1.3
                break
        for reducer in self.INTENSITY_REDUCE:
            if reducer in msg_lower:
                intensity_mod = 0.6
                break

        # 检查自定义模式
        for pattern in self._custom_patterns:
            keywords = pattern.get("keywords", [])
            if any(kw.lower() in msg_lower for kw in keywords):
                try:
                    return Emotion(pattern.get("emotion", "neutral"))
                except ValueError:
                    pass

        # 检查关键词映射
        for keyword, emotion in self.KEYWORD_MAP.items():
            if keyword.lower() in msg_lower:
                emotions_found.append(emotion)

        if not emotions_found:
            # 检查标点符号暗示
            if message.count("!") >= 3:
                return Emotion.EXCITED
            if message.count("?") >= 2:
                return Emotion.CONFUSED
            return Emotion.NEUTRAL

        # 选择最强烈的情感（按强度排序）
        emotion_counts = Counter(emotions_found)
        most_common_emotion = emotion_counts.most_common(1)[0][0]

        return most_common_emotion

    def record_emotion(self, user_id: str, emotion: Emotion,
                       intensity: float = 0.5, trigger: str = "",
                       context: Optional[str] = None) -> int:
        """
        记录用户情感

        Args:
            user_id: 用户ID
            emotion: 情感类型
            intensity: 情感强度 (0-1)
            trigger: 触发消息
            context: 上下文信息

        Returns:
            记录ID
        """
        intensity = max(0.0, min(1.0, intensity))
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO emotion_records (user_id, emotion, intensity, trigger_message, context, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, emotion.value, intensity, trigger, context, now))
        self.conn.commit()

        return cursor.lastrowid

    def get_current_emotion(self, user_id: str) -> Optional[EmotionRecord]:
        """
        获取用户最新情感记录

        Args:
            user_id: 用户ID

        Returns:
            最新情感记录，无则返回 None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT timestamp, emotion, intensity, trigger_message, context
            FROM emotion_records
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return EmotionRecord(
            timestamp=row["timestamp"],
            emotion=row["emotion"],
            intensity=row["intensity"],
            trigger_message=row["trigger_message"],
            context=row["context"],
        )

    def get_emotional_trend(self, user_id: str, hours: int = 24) -> EmotionalTrend:
        """
        获取用户情感趋势

        Args:
            user_id: 用户ID
            hours: 时间范围（小时）

        Returns:
            情感趋势
        """
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT emotion, intensity, timestamp
            FROM emotion_records
            WHERE user_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (user_id, cutoff))

        rows = cursor.fetchall()
        if not rows:
            return EmotionalTrend(
                avg_emotion="neutral",
                dominant_emotion="neutral",
                volatility=0.0,
                trend_direction="stable",
            )

        # 主导情感
        emotion_list = [row["emotion"] for row in rows]
        emotion_counter = Counter(emotion_list)
        dominant = emotion_counter.most_common(1)[0][0]

        # 平均情感分值
        scores = [EMOTION_SCORES.get(Emotion(e), 0.5) for e in emotion_list]
        avg_score = sum(scores) / len(scores) if scores else 0.5

        # 平均情感标签（最接近平均分值的情感）
        avg_emotion = min(Emotion, key=lambda e: abs(EMOTION_SCORES.get(e, 0.5) - avg_score))

        # 波动性（分值标准差）
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            volatility = min(1.0, variance ** 0.5 * 2)  # 归一化到 0-1
        else:
            volatility = 0.0

        # 趋势方向：比较前半段和后半段
        mid = len(scores) // 2
        if mid > 0:
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
            diff = second_half_avg - first_half_avg
            if diff > 0.1:
                trend_direction = "improving"
            elif diff < -0.1:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"

        return EmotionalTrend(
            avg_emotion=avg_emotion.value,
            dominant_emotion=dominant,
            volatility=round(volatility, 4),
            trend_direction=trend_direction,
        )

    def get_emotional_response_strategy(self, emotion: Emotion) -> str:
        """
        获取情感对应的响应策略

        Args:
            emotion: 情感类型

        Returns:
            响应策略描述
        """
        return RESPONSE_STRATEGIES.get(emotion, "保持专业，高效回应")

    def get_empathetic_response(self, user_id: str, jarvis_response: str) -> str:
        """
        基于用户情感调整 Jarvis 回复

        Args:
            user_id: 用户ID
            jarvis_response: 原始 Jarvis 回复

        Returns:
            调整后的回复
        """
        current = self.get_current_emotion(user_id)
        if not current:
            return jarvis_response

        try:
            emotion = Emotion(current.emotion)
        except ValueError:
            return jarvis_response

        intensity = current.intensity

        # 根据情感和前缀调整回复
        prefix_map = {
            Emotion.HAPPY: ["太好了！😊 ", "很高兴能帮到你！"],
            Emotion.EXCITED: ["哇，确实很有趣！✨ ", "太棒了！"],
            Emotion.SAD: ["我理解你的感受。", "抱歉听到这个。"],
            Emotion.ANGRY: ["我理解你的不满。", "让我们来解决这个问题。"],
            Emotion.ANXIOUS: ["别担心，", "慢慢来，"],
            Emotion.FRUSTRATED: ["我明白这很让人沮丧。", "我们一步步来解决。"],
            Emotion.BORED: ["要不要试试这个？", "这里有个有趣的东西。"],
            Emotion.CONFUSED: ["让我来解释清楚。", "简单来说，"],
        }

        prefixes = prefix_map.get(emotion, [])
        if prefixes and intensity > 0.4:
            prefix = prefixes[0]
            # 避免重复前缀
            if not any(jarvis_response.startswith(p[:-1]) for p in prefixes):
                return prefix + jarvis_response

        return jarvis_response

    def add_emotion_pattern(self, trigger_keywords: List[str],
                            emotion: Emotion, response_strategy: str) -> int:
        """
        添加自定义情感模式

        Args:
            trigger_keywords: 触发关键词列表
            emotion: 情感类型
            response_strategy: 响应策略

        Returns:
            模式ID
        """
        # 保存到内存
        pattern = {
            "keywords": trigger_keywords,
            "emotion": emotion.value,
            "response_strategy": response_strategy,
        }
        self._custom_patterns.append(pattern)

        # 保存到数据库
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO emotion_patterns (keywords, emotion, response_strategy)
            VALUES (?, ?, ?)
        """, (",".join(trigger_keywords), emotion.value, response_strategy))
        self.conn.commit()

        return cursor.lastrowid

    def get_emotion_history(self, user_id: str, limit: int = 50) -> List[EmotionRecord]:
        """
        获取用户情感历史

        Args:
            user_id: 用户ID
            limit: 最大返回条数

        Returns:
            情感记录列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT timestamp, emotion, intensity, trigger_message, context
            FROM emotion_records
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))

        records = []
        for row in cursor.fetchall():
            records.append(EmotionRecord(
                timestamp=row["timestamp"],
                emotion=row["emotion"],
                intensity=row["intensity"],
                trigger_message=row["trigger_message"],
                context=row["context"],
            ))

        return records

    def get_stats(self) -> Dict[str, Any]:
        """
        获取情感追踪统计

        Returns:
            统计字典
        """
        cursor = self.conn.cursor()

        # 总记录数
        cursor.execute("SELECT COUNT(*) as cnt FROM emotion_records")
        total = cursor.fetchone()["cnt"]

        # 按情感分类
        cursor.execute("""
            SELECT emotion, COUNT(*) as cnt
            FROM emotion_records
            GROUP BY emotion
            ORDER BY cnt DESC
        """)
        by_emotion = {row["emotion"]: row["cnt"] for row in cursor.fetchall()}

        # 按用户分类
        cursor.execute("""
            SELECT user_id, COUNT(*) as cnt
            FROM emotion_records
            GROUP BY user_id
            ORDER BY cnt DESC
        """)
        by_user = {row["user_id"]: row["cnt"] for row in cursor.fetchall()}

        # 平均强度
        cursor.execute("SELECT AVG(intensity) as avg_int FROM emotion_records")
        avg_intensity = cursor.fetchone()["avg_int"] or 0.0

        # 自定义模式数
        cursor.execute("SELECT COUNT(*) as cnt FROM emotion_patterns")
        pattern_count = cursor.fetchone()["cnt"]

        # 趋势（所有用户）
        cursor.execute("SELECT DISTINCT user_id FROM emotion_records")
        users = [row["user_id"] for row in cursor.fetchall()]
        trends = {}
        for uid in users:
            trend = self.get_emotional_trend(uid)
            trends[uid] = trend.trend_direction

        return {
            "total_records": total,
            "by_emotion": by_emotion,
            "by_user": by_user,
            "avg_intensity": round(avg_intensity, 4),
            "custom_patterns": pattern_count,
            "user_trends": trends,
        }

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
