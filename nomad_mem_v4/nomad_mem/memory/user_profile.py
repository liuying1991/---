"""
User Profile - 用户画像系统

核心能力:
1. 偏好学习：从对话中学习用户偏好（语言风格、话题兴趣、交互方式）
2. 习惯识别：识别用户的行为模式和时间习惯
3. 技能画像：记录用户掌握的技能领域
4. 情感分析：追踪用户的情感倾向
5. 画像进化：随时间更新和完善用户画像

参考:
- 个性化AI助手研究：长期用户建模
- 行为模式识别：基于时间序列分析
"""
import time
import json
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    total_interactions: int = 0
    preferences: Dict[str, Any] = field(default_factory=dict)  # 偏好
    habits: Dict[str, Any] = field(default_factory=dict)       # 习惯
    skills: Dict[str, float] = field(default_factory=dict)     # 技能领域及熟练度
    personality_traits: Dict[str, float] = field(default_factory=dict)  # 个性特征
    emotional_profile: Dict[str, float] = field(default_factory=dict)   # 情感画像
    interaction_patterns: List[Dict] = field(default_factory=list)       # 交互模式


class UserProfileManager:
    """用户画像管理器"""

    def __init__(self, db_path: str = "data/user_profiles.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self.profiles_cache: Dict[str, UserProfile] = {}

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                created_at REAL,
                updated_at REAL,
                total_interactions INTEGER DEFAULT 0,
                preferences TEXT DEFAULT '{}',
                habits TEXT DEFAULT '{}',
                skills TEXT DEFAULT '{}',
                personality_traits TEXT DEFAULT '{}',
                emotional_profile TEXT DEFAULT '{}',
                interaction_patterns TEXT DEFAULT '[]'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp REAL,
                message_type TEXT,
                content TEXT,
                emotion_score REAL,
                topics TEXT DEFAULT '[]',
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_user ON interaction_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_time ON interaction_log(timestamp)")
        self.conn.commit()

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """获取或创建用户画像"""
        if user_id in self.profiles_cache:
            return self.profiles_cache[user_id]

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            profile = UserProfile(
                user_id=row["user_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                total_interactions=row["total_interactions"],
                preferences=json.loads(row["preferences"]),
                habits=json.loads(row["habits"]),
                skills=json.loads(row["skills"]),
                personality_traits=json.loads(row["personality_traits"]),
                emotional_profile=json.loads(row["emotional_profile"]),
                interaction_patterns=json.loads(row["interaction_patterns"]),
            )
        else:
            profile = UserProfile(user_id=user_id)
            self._save_profile(profile)

        self.profiles_cache[user_id] = profile
        return profile

    def update_from_interaction(
        self,
        user_id: str,
        message: str,
        message_type: str = "user",
        emotion_score: float = 0.5,
        topics: List[str] = None,
    ) -> UserProfile:
        """
        从交互更新用户画像

        Args:
            user_id: 用户ID
            message: 消息内容
            message_type: 消息类型（user/assistant/system）
            emotion_score: 情感分数
            topics: 话题列表

        Returns:
            更新后的用户画像
        """
        profile = self.get_or_create_profile(user_id)
        profile.total_interactions += 1
        profile.updated_at = time.time()

        # 更新偏好
        self._update_preferences(profile, message, topics)

        # 更新习惯
        self._update_habits(profile)

        # 更新技能
        if topics:
            self._update_skills(profile, topics)

        # 更新情感画像
        self._update_emotional_profile(profile, emotion_score)

        # 记录交互
        self._log_interaction(user_id, message, message_type, emotion_score, topics)

        # 保存
        self._save_profile(profile)
        return profile

    def get_personalized_context(self, user_id: str) -> Dict[str, Any]:
        """
        获取个性化上下文

        Args:
            user_id: 用户ID

        Returns:
            个性化上下文字典
        """
        profile = self.get_or_create_profile(user_id)

        return {
            "preferences": profile.preferences,
            "top_skills": sorted(profile.skills.items(), key=lambda x: x[1], reverse=True)[:5],
            "emotional_state": self._get_current_emotional_state(profile),
            "interaction_style": self._infer_interaction_style(profile),
            "recommended_topics": self._recommend_topics(profile),
        }

    def get_interaction_stats(self, user_id: str) -> Dict[str, Any]:
        """获取交互统计"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   AVG(emotion_score) as avg_emotion,
                   MIN(timestamp) as first_interaction,
                   MAX(timestamp) as last_interaction
            FROM interaction_log
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()

        return {
            "total_interactions": row["total"] or 0,
            "avg_emotion_score": row["avg_emotion"] or 0.0,
            "first_interaction": row["first_interaction"],
            "last_interaction": row["last_interaction"],
        }

    def get_top_topics(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取用户最常讨论的话题"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT topics FROM interaction_log
            WHERE user_id = ? AND topics != '[]'
        """, (user_id,))

        topic_counts: Dict[str, int] = {}
        for row in cursor.fetchall():
            topics = json.loads(row["topics"])
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"topic": t, "count": c} for t, c in sorted_topics[:limit]]

    def _update_preferences(self, profile: UserProfile, message: str, topics: List[str] = None):
        """更新用户偏好"""
        if not topics:
            return

        if "preferred_topics" not in profile.preferences:
            profile.preferences["preferred_topics"] = []

        for topic in topics:
            if topic not in profile.preferences["preferred_topics"]:
                profile.preferences["preferred_topics"].append(topic)

        # 检测语言风格偏好
        if len(message) > 20:
            profile.preferences["prefers_detail"] = profile.preferences.get("prefers_detail", 0) + 1
        else:
            profile.preferences["prefers_brevity"] = profile.preferences.get("prefers_brevity", 0) + 1

    def _update_habits(self, profile: UserProfile):
        """更新用户习惯"""
        current_hour = time.time() % 86400 / 3600

        if "active_hours" not in profile.habits:
            profile.habits["active_hours"] = []

        profile.habits["active_hours"].append(current_hour)

        # 保持最近100条记录
        if len(profile.habits["active_hours"]) > 100:
            profile.habits["active_hours"] = profile.habits["active_hours"][-100:]

    def _update_skills(self, profile: UserProfile, topics: List[str]):
        """更新用户技能"""
        for topic in topics:
            current_level = profile.skills.get(topic, 0.0)
            # 每次讨论增加熟练度（递减增长）
            increment = 0.1 * (1.0 - current_level)
            profile.skills[topic] = min(1.0, current_level + increment)

    def _update_emotional_profile(self, profile: UserProfile, emotion_score: float):
        """更新情感画像"""
        if "emotion_history" not in profile.emotional_profile:
            profile.emotional_profile["emotion_history"] = []

        profile.emotional_profile["emotion_history"].append({
            "score": emotion_score,
            "timestamp": time.time()
        })

        # 保持最近50条记录
        if len(profile.emotional_profile["emotion_history"]) > 50:
            profile.emotional_profile["emotion_history"] = profile.emotional_profile["emotion_history"][-50:]

    def _log_interaction(
        self, user_id: str, message: str, message_type: str,
        emotion_score: float, topics: List[str] = None
    ):
        """记录交互"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO interaction_log (user_id, timestamp, message_type, content, emotion_score, topics)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id, time.time(), message_type, message,
            emotion_score, json.dumps(topics or [])
        ))
        self.conn.commit()

    def _get_current_emotional_state(self, profile: UserProfile) -> Dict[str, Any]:
        """获取当前情感状态"""
        history = profile.emotional_profile.get("emotion_history", [])
        if not history:
            return {"avg_score": 0.5, "trend": "stable"}

        recent = history[-10:]
        avg_score = sum(e["score"] for e in recent) / len(recent)

        # 计算趋势
        if len(recent) >= 2:
            first_half = sum(e["score"] for e in recent[:len(recent)//2]) / (len(recent)//2)
            second_half = sum(e["score"] for e in recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
            trend = "improving" if second_half > first_half else "declining"
        else:
            trend = "stable"

        return {"avg_score": avg_score, "trend": trend}

    def _infer_interaction_style(self, profile: UserProfile) -> str:
        """推断交互风格"""
        detail = profile.preferences.get("prefers_detail", 0)
        brevity = profile.preferences.get("prefers_brevity", 0)

        if detail > brevity:
            return "detailed"
        elif brevity > detail:
            return "brief"
        return "balanced"

    def _recommend_topics(self, profile: UserProfile) -> List[str]:
        """推荐话题"""
        preferred = profile.preferences.get("preferred_topics", [])
        skills = profile.skills

        # 推荐已喜欢但熟练度不高的话题
        recommendations = []
        for topic in preferred:
            if skills.get(topic, 0) < 0.7:
                recommendations.append(topic)

        return recommendations[:5]

    def _save_profile(self, profile: UserProfile):
        """保存画像"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_profiles
            (user_id, created_at, updated_at, total_interactions,
             preferences, habits, skills, personality_traits, emotional_profile, interaction_patterns)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.user_id, profile.created_at, profile.updated_at,
            profile.total_interactions,
            json.dumps(profile.preferences), json.dumps(profile.habits),
            json.dumps(profile.skills), json.dumps(profile.personality_traits),
            json.dumps(profile.emotional_profile), json.dumps(profile.interaction_patterns)
        ))
        self.conn.commit()

    def close(self):
        self.conn.close()
