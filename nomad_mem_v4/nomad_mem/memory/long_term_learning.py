"""
Long Term Learning - 长期学习系统

核心能力:
1. 模式提取：从历史交互中提取行为模式
2. 知识进化：将重复验证的信息固化为知识
3. 行为预测：基于历史预测用户下一步行为
4. 偏好学习：持续学习和适应用户偏好
5. 错误学习：从错误中学习避免重复

参考:
- 强化学习中的经验回放(Experience Replay)
- 在线学习(Online Learning)算法
- 贝叶斯更新模型
"""
import time
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class LearningType(Enum):
    """学习类型"""
    PATTERN = "pattern"           # 行为模式
    PREFERENCE = "preference"     # 用户偏好
    KNOWLEDGE = "knowledge"       # 知识
    ERROR_AVOIDANCE = "error_avoidance"  # 错误避免
    CONTEXT = "context"           # 上下文关联


@dataclass
class LearnedItem:
    """学习到的项目"""
    item_id: str
    learning_type: LearningType
    content: str
    confidence: float = 0.5
    occurrence_count: int = 1
    last_updated: float = field(default_factory=time.time)
    first_seen: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionPattern:
    """交互模式"""
    pattern_id: str
    description: str
    trigger_conditions: List[str] = field(default_factory=list)
    typical_response: str = ""
    frequency: float = 0.0
    confidence: float = 0.5
    last_observed: float = field(default_factory=time.time)


class LongTermLearning:
    """长期学习系统"""

    def __init__(self, db_path: str = "data/long_term_learning.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self.interaction_buffer: List[Dict] = []
        self.min_confidence_for_knowledge = 0.7

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_items (
                item_id TEXT PRIMARY KEY,
                learning_type TEXT,
                content TEXT,
                confidence REAL DEFAULT 0.5,
                occurrence_count INTEGER DEFAULT 1,
                last_updated REAL,
                first_seen REAL,
                context TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp REAL,
                user_message TEXT,
                ai_response TEXT,
                outcome TEXT,
                tags TEXT DEFAULT '[]',
                context TEXT DEFAULT '{}'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                description TEXT,
                trigger_conditions TEXT DEFAULT '[]',
                typical_response TEXT,
                frequency REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.5,
                last_observed REAL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_time ON interaction_log(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_user ON interaction_log(user_id)")
        self.conn.commit()

    def log_interaction(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        outcome: str = "neutral",
        tags: List[str] = None,
        context: Dict = None,
    ):
        """
        记录交互用于学习

        Args:
            user_id: 用户ID
            user_message: 用户消息
            ai_response: AI回复
            outcome: 结果（success/failure/neutral）
            tags: 标签
            context: 上下文
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO interaction_log (user_id, timestamp, user_message, ai_response, outcome, tags, context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, time.time(), user_message, ai_response, outcome,
            json.dumps(tags or []), json.dumps(context or {})
        ))
        self.conn.commit()

        # 添加到学习缓冲区
        self.interaction_buffer.append({
            "user_id": user_id,
            "message": user_message,
            "response": ai_response,
            "outcome": outcome,
            "tags": tags or [],
            "context": context or {},
            "timestamp": time.time(),
        })

        # 缓冲区满时触发学习
        if len(self.interaction_buffer) >= 10:
            self._process_buffer()

    def learn_pattern(self, user_id: str) -> Optional[InteractionPattern]:
        """
        从用户历史中学习模式

        Args:
            user_id: 用户ID

        Returns:
            学习到的模式或None
        """
        import uuid

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT user_message, outcome, tags, context
            FROM interaction_log
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (user_id,))

        rows = cursor.fetchall()
        if len(rows) < 5:
            return None

        # 分析高频话题
        tag_counts = {}
        message_patterns = {}

        for row in rows:
            tags = json.loads(row["tags"])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # 分析消息模式
            msg = row["user_message"]
            first_word = msg.split()[0] if msg.split() else ""
            if first_word:
                message_patterns[first_word] = message_patterns.get(first_word, 0) + 1

        if not tag_counts:
            return None

        # 提取最高频的模式
        top_tag = max(tag_counts, key=tag_counts.get)
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"

        pattern = InteractionPattern(
            pattern_id=pattern_id,
            description=f"用户经常讨论 {top_tag}",
            trigger_conditions=[top_tag],
            frequency=tag_counts[top_tag] / len(rows),
            confidence=min(0.95, tag_counts[top_tag] / len(rows) * 2),
        )

        # 保存模式
        cursor.execute("""
            INSERT OR REPLACE INTO patterns
            (pattern_id, description, trigger_conditions, typical_response, frequency, confidence, last_observed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id, pattern.description,
            json.dumps(pattern.trigger_conditions), pattern.typical_response,
            pattern.frequency, pattern.confidence, pattern.last_observed
        ))
        self.conn.commit()

        return pattern

    def extract_knowledge(self, user_id: str) -> List[LearnedItem]:
        """
        从交互中提取知识

        Args:
            user_id: 用户ID

        Returns:
            提取的知识列表
        """
        import uuid

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT user_message, ai_response, outcome, COUNT(*) as count
            FROM interaction_log
            WHERE user_id = ? AND outcome = 'success'
            GROUP BY user_message
            HAVING count >= 3
            ORDER BY count DESC
            LIMIT 10
        """, (user_id,))

        knowledge_items = []
        for row in cursor.fetchall():
            item_id = f"knowledge_{uuid.uuid4().hex[:8]}"
            item = LearnedItem(
                item_id=item_id,
                learning_type=LearningType.KNOWLEDGE,
                content=row["ai_response"][:200],
                confidence=min(0.95, row["count"] * 0.15),
                occurrence_count=row["count"],
                context={"user_message": row["user_message"]},
            )
            knowledge_items.append(item)

            # 保存知识
            self._save_learned_item(item)

        return knowledge_items

    def predict_next_action(self, user_id: str) -> List[Dict]:
        """
        预测用户下一步行为

        Args:
            user_id: 用户ID

        Returns:
            预测的行为列表（按概率排序）
        """
        cursor = self.conn.cursor()

        # 获取最近的交互
        cursor.execute("""
            SELECT tags, context FROM interaction_log
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (user_id,))

        rows = cursor.fetchall()
        if not rows:
            return []

        # 分析标签共现
        tag_sequences = []
        for row in rows:
            tags = json.loads(row["tags"])
            if tags:
                tag_sequences.append(tags)

        if not tag_sequences:
            return []

        # 简单预测：最近频繁出现的标签
        recent_tags = tag_sequences[0] if tag_sequences else []
        predictions = []

        for tag in recent_tags:
            predictions.append({
                "action": f"可能涉及 {tag}",
                "confidence": 0.5,
                "based_on": tag,
            })

        return predictions[:5]

    def learn_from_error(
        self,
        user_id: str,
        error_context: str,
        correct_response: str = ""
    ):
        """
        从错误中学习

        Args:
            user_id: 用户ID
            error_context: 错误上下文
            correct_response: 正确的回复（如果已知）
        """
        import uuid

        item = LearnedItem(
            item_id=f"error_{uuid.uuid4().hex[:8]}",
            learning_type=LearningType.ERROR_AVOIDANCE,
            content=error_context,
            confidence=0.8,
            metadata={"correct_response": correct_response},
        )
        self._save_learned_item(item)

    def get_learned_items(
        self,
        user_id: str,
        learning_type: LearningType = None,
        min_confidence: float = 0.0,
        limit: int = 20,
    ) -> List[LearnedItem]:
        """
        获取学习到的项目

        Args:
            user_id: 用户ID
            learning_type: 学习类型过滤
            min_confidence: 最低置信度
            limit: 数量限制

        Returns:
            学习到的项目列表
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM learned_items WHERE confidence >= ?"
        params = [min_confidence]

        if learning_type:
            query += " AND learning_type = ?"
            params.append(learning_type.value)

        query += " ORDER BY confidence DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        items = []
        for row in cursor.fetchall():
            items.append(LearnedItem(
                item_id=row["item_id"],
                learning_type=LearningType(row["learning_type"]),
                content=row["content"],
                confidence=row["confidence"],
                occurrence_count=row["occurrence_count"],
                last_updated=row["last_updated"],
                first_seen=row["first_seen"],
                context=json.loads(row["context"]),
                metadata=json.loads(row["metadata"]),
            ))
        return items

    def update_item_confidence(self, item_id: str, delta: float):
        """
        更新项目置信度

        Args:
            item_id: 项目ID
            delta: 变化量（正数增加，负数减少）
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE learned_items
            SET confidence = MIN(1.0, MAX(0.0, confidence + ?)),
                last_updated = ?
            WHERE item_id = ?
        """, (delta, time.time(), item_id))
        self.conn.commit()

    def get_learning_stats(self, user_id: str = None) -> Dict[str, Any]:
        """获取学习统计"""
        cursor = self.conn.cursor()

        if user_id:
            cursor.execute("SELECT COUNT(*) as total FROM interaction_log WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) as total FROM interaction_log")

        total_interactions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM learned_items")
        total_learned = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM patterns")
        total_patterns = cursor.fetchone()["total"]

        # 各类型分布
        cursor.execute("""
            SELECT learning_type, COUNT(*) as count
            FROM learned_items GROUP BY learning_type
        """)
        type_distribution = {row["learning_type"]: row["count"] for row in cursor.fetchall()}

        return {
            "total_interactions": total_interactions,
            "total_learned_items": total_learned,
            "total_patterns": total_patterns,
            "type_distribution": type_distribution,
            "buffer_size": len(self.interaction_buffer),
        }

    def _save_learned_item(self, item: LearnedItem):
        """保存学习项目"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO learned_items
            (item_id, learning_type, content, confidence, occurrence_count,
             last_updated, first_seen, context, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.item_id, item.learning_type.value, item.content,
            item.confidence, item.occurrence_count,
            item.last_updated, item.first_seen,
            json.dumps(item.context), json.dumps(item.metadata)
        ))
        self.conn.commit()

    def _process_buffer(self):
        """处理学习缓冲区"""
        if len(self.interaction_buffer) < 10:
            return

        # 分析最近10条交互
        recent = self.interaction_buffer[-10:]

        # 统计成功交互
        success_count = sum(1 for item in recent if item["outcome"] == "success")
        failure_count = sum(1 for item in recent if item["outcome"] == "failure")

        # 如果成功率低，触发错误学习
        if failure_count > success_count:
            common_errors = [item for item in recent if item["outcome"] == "failure"]
            if common_errors:
                error_ctx = common_errors[0]["message"][:100]
                self.learn_from_error(
                    user_id=common_errors[0]["user_id"],
                    error_context=error_ctx,
                )

        # 清空缓冲区
        self.interaction_buffer = []

    def close(self):
        self.conn.close()
