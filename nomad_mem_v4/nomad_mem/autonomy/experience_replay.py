"""
Experience Replay - 经验回放系统

Jarvis 从历史交互中提取、存储和检索经验的核心模块。
灵感来自强化学习的 Experience Replay，但工程化为对话经验系统。

核心特性:
- 经验存储: 记录每次交互的关键要素（意图、工具使用、结果、用户反馈）
- 模式提取: 自动识别重复的成功/失败模式
- 经验检索: 根据当前上下文检索最相关的历史经验
- 教训提取: 从失败中提取可操作的教训
- SQLite 持久化: 轻量级本地存储

设计原则:
- 每次有价值的交互都是一条经验
- 经验包含成功和失败两种类型
- 经验可被检索、聚合、学习
- 系统自动从历史中改进，不需要显式训练
"""
import sqlite3
import time
import json
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter


# ─── Enums ───────────────────────────────────────────────────────────────────


class ExperienceType(Enum):
    """经验类型"""
    SUCCESS = "success"           # 成功经验
    FAILURE = "failure"           # 失败经验
    INSIGHT = "insight"           # 洞察/发现
    PREFERENCE = "preference"     # 用户偏好
    PATTERN = "pattern"           # 重复模式


class ExperienceOutcome(Enum):
    """经验结果"""
    POSITIVE = "positive"         # 正面结果
    NEGATIVE = "negative"         # 负面结果
    NEUTRAL = "neutral"           # 中性结果


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class Experience:
    """一条交互经验

    Attributes:
        exp_id: 经验唯一标识
        exp_type: 经验类型
        outcome: 经验结果
        user_id: 用户ID
        intent: 用户意图
        context: 交互上下文
        action_taken: 采取的行动
        result: 结果描述
        lesson_learned: 学到的教训/经验
        tags: 经验标签
        importance: 重要程度 (0.0-1.0)
        created_at: 创建时间戳
        usage_count: 被引用次数
    """
    exp_id: str
    exp_type: ExperienceType
    outcome: ExperienceOutcome
    user_id: str
    intent: str
    context: str
    action_taken: str
    result: str
    lesson_learned: str = ""
    tags: str = ""
    importance: float = 0.5
    created_at: float = field(default_factory=time.time)
    usage_count: int = 0

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["exp_type"] = self.exp_type.value
        d["outcome"] = self.outcome.value
        d["tags"] = list(self.tags) if isinstance(self.tags, str) else self.tags
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "Experience":
        data = dict(data)
        if isinstance(data.get("exp_type"), str):
            data["exp_type"] = ExperienceType(data["exp_type"])
        if isinstance(data.get("outcome"), str):
            data["outcome"] = ExperienceOutcome(data["outcome"])
        if isinstance(data.get("tags"), str):
            data["tags"] = data["tags"]
        allowed = {
            "exp_id", "exp_type", "outcome", "user_id", "intent",
            "context", "action_taken", "result", "lesson_learned",
            "tags", "importance", "created_at", "usage_count",
        }
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


@dataclass
class ExperiencePattern:
    """从经验中提取的模式

    Attributes:
        pattern_id: 模式唯一标识
        pattern_type: 模式类型
        description: 模式描述
        frequency: 出现频率
        success_rate: 成功率
        related_intents: 相关意图列表
        lessons: 相关教训列表
        created_at: 创建时间戳
    """
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    success_rate: float
    related_intents: str = ""
    lessons: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ExperiencePattern":
        data = dict(data)
        allowed = {
            "pattern_id", "pattern_type", "description", "frequency",
            "success_rate", "related_intents", "lessons", "created_at",
        }
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


# ─── ExperienceReplay ────────────────────────────────────────────────────────


class ExperienceReplay:
    """
    经验回放系统

    记录、检索和学习历史交互经验，帮助 Jarvis 从过去中学习。

    使用示例:
        >>> replay = ExperienceReplay(db_path="experiences.db")
        >>> exp_id = replay.record_experience(
        ...     user_id="user1",
        ...     intent="schedule_meeting",
        ...     context='{"time": "morning"}',
        ...     action_taken="used calendar tool",
        ...     result="meeting scheduled successfully",
        ...     exp_type=ExperienceType.SUCCESS,
        ...     outcome=ExperienceOutcome.POSITIVE,
        ...     importance=0.8,
        ... )
        >>> experiences = replay.retrieve_similar("schedule", k=3)
        >>> patterns = replay.extract_patterns()
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._persistent_conn = None
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._persistent_conn:
            return self._persistent_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _maybe_close(self, conn):
        """Close connection only if not using persistent in-memory DB"""
        if not self._persistent_conn:
            conn.close()

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS experiences (
                exp_id         TEXT PRIMARY KEY,
                exp_type       TEXT NOT NULL,
                outcome        TEXT NOT NULL,
                user_id        TEXT NOT NULL DEFAULT 'default',
                intent         TEXT NOT NULL,
                context        TEXT NOT NULL DEFAULT '{}',
                action_taken   TEXT NOT NULL DEFAULT '',
                result         TEXT NOT NULL DEFAULT '',
                lesson_learned TEXT NOT NULL DEFAULT '',
                tags           TEXT NOT NULL DEFAULT '[]',
                importance     REAL NOT NULL DEFAULT 0.5,
                created_at     REAL NOT NULL,
                usage_count    INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id      TEXT PRIMARY KEY,
                pattern_type    TEXT NOT NULL,
                description     TEXT NOT NULL,
                frequency       INTEGER NOT NULL DEFAULT 1,
                success_rate    REAL NOT NULL DEFAULT 0.0,
                related_intents TEXT NOT NULL DEFAULT '[]',
                lessons         TEXT NOT NULL DEFAULT '',
                created_at      REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_exp_intent ON experiences(intent);
            CREATE INDEX IF NOT EXISTS idx_exp_user ON experiences(user_id);
            CREATE INDEX IF NOT EXISTS idx_exp_type ON experiences(exp_type);
            CREATE INDEX IF NOT EXISTS idx_exp_importance ON experiences(importance DESC);
            CREATE INDEX IF NOT EXISTS idx_exp_created ON experiences(created_at DESC);
        """)
        conn.commit()
        self._maybe_close(conn)

    # ── Experience Recording ──────────────────────────────────────────────

    def record_experience(
        self,
        user_id: str,
        intent: str,
        context: str,
        action_taken: str,
        result: str,
        exp_type: ExperienceType = ExperienceType.SUCCESS,
        outcome: ExperienceOutcome = ExperienceOutcome.POSITIVE,
        lesson_learned: str = "",
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
    ) -> str:
        """
        记录一条新经验

        Args:
            user_id: 用户ID
            intent: 用户意图
            context: 交互上下文（JSON字符串）
            action_taken: 采取的行动
            result: 结果描述
            exp_type: 经验类型
            outcome: 经验结果
            lesson_learned: 学到的教训
            tags: 经验标签
            importance: 重要程度 (0.0-1.0)

        Returns:
            exp_id: 新经验的ID
        """
        exp_id = f"exp_{uuid.uuid4().hex[:12]}"
        now = time.time()
        tags_str = json.dumps(tags or [], ensure_ascii=False)

        conn = self._get_conn()
        conn.execute(
            """INSERT INTO experiences 
            (exp_id, exp_type, outcome, user_id, intent, context, 
             action_taken, result, lesson_learned, tags, importance, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (exp_id, exp_type.value, outcome.value, user_id, intent,
             context, action_taken, result, lesson_learned, tags_str,
             min(max(importance, 0.0), 1.0), now),
        )
        conn.commit()
        self._maybe_close(conn)
        return exp_id

    def get_experience(self, exp_id: str) -> Optional[Experience]:
        """
        获取指定经验

        Args:
            exp_id: 经验ID

        Returns:
            经验对象，不存在则返回 None
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM experiences WHERE exp_id = ?", (exp_id,)
        ).fetchone()
        self._maybe_close(conn)
        if row is None:
            return None
        return Experience.from_dict(dict(row))

    def increment_usage(self, exp_id: str):
        """
        增加经验的使用次数

        Args:
            exp_id: 经验ID
        """
        conn = self._get_conn()
        conn.execute(
            "UPDATE experiences SET usage_count = usage_count + 1 WHERE exp_id = ?",
            (exp_id,),
        )
        conn.commit()
        self._maybe_close(conn)

    # ── Experience Retrieval ──────────────────────────────────────────────

    def retrieve_similar(self, keyword: str, k: int = 5) -> List[Experience]:
        """
        检索与关键词相关的经验

        Args:
            keyword: 搜索关键词
            k: 返回数量限制

        Returns:
            相关经验列表
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM experiences 
            WHERE intent LIKE ? OR result LIKE ? OR lesson_learned LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", k),
        ).fetchall()
        self._maybe_close(conn)
        return [Experience.from_dict(dict(r)) for r in rows]

    def retrieve_by_intent(self, intent: str, k: int = 5) -> List[Experience]:
        """
        按意图检索经验

        Args:
            intent: 意图字符串
            k: 返回数量限制

        Returns:
            经验列表
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM experiences 
            WHERE intent = ?
            ORDER BY importance DESC, usage_count DESC, created_at DESC
            LIMIT ?""",
            (intent, k),
        ).fetchall()
        self._maybe_close(conn)
        return [Experience.from_dict(dict(r)) for r in rows]

    def retrieve_by_user(self, user_id: str, k: int = 10) -> List[Experience]:
        """
        按用户检索经验

        Args:
            user_id: 用户ID
            k: 返回数量限制

        Returns:
            经验列表
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM experiences 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?""",
            (user_id, k),
        ).fetchall()
        self._maybe_close(conn)
        return [Experience.from_dict(dict(r)) for r in rows]

    def retrieve_recent_failures(self, k: int = 5) -> List[Experience]:
        """
        检索最近的失败经验

        Args:
            k: 返回数量限制

        Returns:
            失败经验列表
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM experiences 
            WHERE outcome = 'negative'
            ORDER BY created_at DESC
            LIMIT ?""",
            (k,),
        ).fetchall()
        self._maybe_close(conn)
        return [Experience.from_dict(dict(r)) for r in rows]

    def retrieve_lessons(self, intent: str = "", k: int = 5) -> List[str]:
        """
        检索相关教训

        Args:
            intent: 可选，按意图过滤
            k: 返回数量限制

        Returns:
            教训列表
        """
        conn = self._get_conn()
        if intent:
            rows = conn.execute(
                """SELECT lesson_learned FROM experiences 
                WHERE lesson_learned != '' AND intent = ?
                ORDER BY importance DESC
                LIMIT ?""",
                (intent, k),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT lesson_learned FROM experiences 
                WHERE lesson_learned != ''
                ORDER BY importance DESC
                LIMIT ?""",
                (k,),
            ).fetchall()
        self._maybe_close(conn)
        return [r["lesson_learned"] for r in rows if r["lesson_learned"]]

    # ── Pattern Extraction ────────────────────────────────────────────────

    def extract_patterns(self) -> List[ExperiencePattern]:
        """
        从经验中提取模式

        识别:
        - 高频意图
        - 常见失败原因
        - 成功行动模式
        - 用户偏好

        Returns:
            模式列表
        """
        conn = self._get_conn()

        patterns = []

        # 1. 高频意图模式
        intent_rows = conn.execute(
            """SELECT intent, COUNT(*) as cnt,
               AVG(CASE WHEN outcome = 'positive' THEN 1.0 ELSE 0.0 END) as success_rate
               FROM experiences
               GROUP BY intent
               HAVING cnt >= 2
               ORDER BY cnt DESC"""
        ).fetchall()

        for row in intent_rows[:10]:
            pattern_id = f"pat_intent_{row['intent']}"
            # 获取相关教训
            lesson_rows = conn.execute(
                """SELECT lesson_learned FROM experiences 
                WHERE intent = ? AND lesson_learned != '' LIMIT 3""",
                (row["intent"],),
            ).fetchall()
            lessons = " | ".join(r["lesson_learned"] for r in lesson_rows if r["lesson_learned"])

            patterns.append(ExperiencePattern(
                pattern_id=pattern_id,
                pattern_type="intent_frequency",
                description=f"意图 '{row['intent']}' 出现 {row['cnt']} 次",
                frequency=row["cnt"],
                success_rate=row["success_rate"],
                related_intents=row["intent"],
                lessons=lessons,
            ))

        # 2. 常见失败模式
        failure_rows = conn.execute(
            """SELECT result, COUNT(*) as cnt
               FROM experiences
               WHERE outcome = 'negative'
               GROUP BY result
               HAVING cnt >= 2
               ORDER BY cnt DESC"""
        ).fetchall()

        for row in failure_rows[:5]:
            pattern_id = f"pat_failure_{uuid.uuid4().hex[:8]}"
            patterns.append(ExperiencePattern(
                pattern_id=pattern_id,
                pattern_type="failure_pattern",
                description=f"失败结果 '{row['result']}' 出现 {row['cnt']} 次",
                frequency=row["cnt"],
                success_rate=0.0,
                lessons="需要改进此场景的处理",
            ))

        self._maybe_close(conn)
        return patterns

    def save_patterns(self, patterns: List[ExperiencePattern]):
        """
        保存模式到数据库

        Args:
            patterns: 模式列表
        """
        conn = self._get_conn()
        for p in patterns:
            conn.execute(
                """INSERT OR REPLACE INTO patterns 
                (pattern_id, pattern_type, description, frequency, 
                 success_rate, related_intents, lessons, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (p.pattern_id, p.pattern_type, p.description, p.frequency,
                 p.success_rate, p.related_intents, p.lessons, p.created_at),
            )
        conn.commit()
        self._maybe_close(conn)

    def get_patterns(self) -> List[ExperiencePattern]:
        """获取所有已保存的模式"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM patterns ORDER BY frequency DESC"
        ).fetchall()
        self._maybe_close(conn)
        return [ExperiencePattern.from_dict(dict(r)) for r in rows]

    # ── Analytics ─────────────────────────────────────────────────────────

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的经验统计

        Args:
            user_id: 用户ID

        Returns:
            统计字典
        """
        conn = self._get_conn()
        row = conn.execute(
            """SELECT 
               COUNT(*) as total,
               SUM(CASE WHEN outcome = 'positive' THEN 1 ELSE 0 END) as positive,
               SUM(CASE WHEN outcome = 'negative' THEN 1 ELSE 0 END) as negative,
               SUM(CASE WHEN outcome = 'neutral' THEN 1 ELSE 0 END) as neutral,
               AVG(importance) as avg_importance
               FROM experiences WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        self._maybe_close(conn)

        if row is None or row["total"] == 0:
            return {
                "total_experiences": 0,
                "positive_rate": 0.0,
                "avg_importance": 0.0,
            }

        total = row["total"]
        return {
            "total_experiences": total,
            "positive_count": row["positive"] or 0,
            "negative_count": row["negative"] or 0,
            "neutral_count": row["neutral"] or 0,
            "positive_rate": (row["positive"] or 0) / total,
            "avg_importance": row["avg_importance"] or 0.0,
        }

    def get_top_intents(self, k: int = 10) -> List[Tuple[str, int]]:
        """
        获取最频繁的意图

        Args:
            k: 返回数量

        Returns:
            (意图, 次数) 列表
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT intent, COUNT(*) as cnt
               FROM experiences
               GROUP BY intent
               ORDER BY cnt DESC
               LIMIT ?""",
            (k,),
        ).fetchall()
        self._maybe_close(conn)
        return [(r["intent"], r["cnt"]) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        """获取系统整体统计"""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT 
               COUNT(*) as total,
               COUNT(DISTINCT user_id) as users,
               COUNT(DISTINCT intent) as intents,
               SUM(CASE WHEN outcome = 'positive' THEN 1 ELSE 0 END) as positive
               FROM experiences"""
        ).fetchone()
        pattern_count = conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
        self._maybe_close(conn)

        total = row["total"] or 0
        return {
            "total_experiences": total,
            "total_users": row["users"] or 0,
            "total_intents": row["intents"] or 0,
            "positive_experiences": row["positive"] or 0,
            "total_patterns": pattern_count,
            "positive_rate": (row["positive"] or 0) / total if total > 0 else 0.0,
        }

    def close(self):
        """关闭数据库连接（清理）"""
        if self._persistent_conn:
            self._persistent_conn.close()
            self._persistent_conn = None
