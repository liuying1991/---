"""
回复优化器模块
基于反馈优化回复策略，追踪回复模板表现并自动选择最佳模板
"""
import sqlite3
import uuid
import time
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class ResponseTemplate:
    template_id: str
    intent_category: str
    pattern: str
    template_text: str
    success_rate: float
    usage_count: int


@dataclass
class FeedbackRecord:
    record_id: str
    response_text: str
    feedback_type: str  # positive / negative / neutral
    timestamp: float
    context: str


class ResponseOptimizer:
    """回复优化器 - 基于反馈优化回复策略"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS response_templates (
                    template_id TEXT PRIMARY KEY,
                    intent_category TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    template_text TEXT NOT NULL,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    usage_count INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL
                )
            """)
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_template_intent ON response_templates(intent_category)"
            )

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_records (
                    record_id TEXT PRIMARY KEY,
                    response_text TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    context TEXT,
                    template_id TEXT,
                    FOREIGN KEY(template_id) REFERENCES response_templates(template_id)
                )
            """)
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback_records(feedback_type)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_feedback_time ON feedback_records(timestamp)"
            )

    def add_template(self, intent_category: str, pattern: str, template_text: str) -> str:
        """添加回复模板"""
        template_id = str(uuid.uuid4())
        now = time.time()
        with self.conn:
            self.conn.execute(
                "INSERT INTO response_templates VALUES (?, ?, ?, ?, 0, 0, 0, ?)",
                (template_id, intent_category, pattern, template_text, now),
            )
        return template_id

    def record_feedback(self, response_text: str, feedback_type: str, context: str = "", template_id: str = None) -> str:
        """记录反馈"""
        record_id = str(uuid.uuid4())
        now = time.time()
        with self.conn:
            self.conn.execute(
                "INSERT INTO feedback_records VALUES (?, ?, ?, ?, ?, ?)",
                (record_id, response_text, feedback_type, now, context, template_id),
            )
        return record_id

    def get_best_template(self, intent_category: str) -> Optional[str]:
        """返回成功率最高的模板文本"""
        row = self.conn.execute(
            """
            SELECT template_text, success_count, failure_count
            FROM response_templates
            WHERE intent_category = ? AND usage_count > 0
            ORDER BY
                CASE WHEN (success_count + failure_count) > 0
                    THEN success_count * 1.0 / (success_count + failure_count)
                    ELSE 0 END DESC,
                usage_count DESC
            LIMIT 1
            """,
            (intent_category,),
        ).fetchone()

        if row:
            return row["template_text"]

        # 如果没有使用过的模板，返回最新创建的
        row = self.conn.execute(
            "SELECT template_text FROM response_templates WHERE intent_category=? ORDER BY created_at DESC LIMIT 1",
            (intent_category,),
        ).fetchone()
        if row:
            return row["template_text"]
        return None

    def update_template_success(self, template_id: str, success: bool) -> None:
        """追踪模板表现"""
        with self.conn:
            if success:
                self.conn.execute(
                    "UPDATE response_templates SET success_count = success_count + 1, usage_count = usage_count + 1 WHERE template_id = ?",
                    (template_id,),
                )
            else:
                self.conn.execute(
                    "UPDATE response_templates SET failure_count = failure_count + 1, usage_count = usage_count + 1 WHERE template_id = ?",
                    (template_id,),
                )

    def get_feedback_summary(self) -> Dict:
        """获取反馈摘要"""
        row = self.conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN feedback_type='positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN feedback_type='negative' THEN 1 ELSE 0 END) as negative,
                SUM(CASE WHEN feedback_type='neutral' THEN 1 ELSE 0 END) as neutral
            FROM feedback_records
            """
        ).fetchone()

        total = row["total"] or 0
        positive = row["positive"] or 0
        negative = row["negative"] or 0
        neutral = row["neutral"] or 0

        # 趋势：最近 vs 之前
        now = time.time()
        half = total // 2 if total > 1 else 0
        recent_row = self.conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN feedback_type='positive' THEN 1 ELSE 0 END) as positive
            FROM feedback_records
            WHERE timestamp > (
                SELECT timestamp FROM feedback_records ORDER BY timestamp ASC LIMIT 1 OFFSET ?
            )
            """,
            (half,),
        ).fetchone()

        recent_positive_ratio = 0
        if recent_row and recent_row["total"] > 0:
            recent_positive_ratio = recent_row["positive"] / recent_row["total"]

        overall_positive_ratio = positive / total if total > 0 else 0

        trend = "stable"
        if recent_positive_ratio > overall_positive_ratio + 0.1:
            trend = "improving"
        elif recent_positive_ratio < overall_positive_ratio - 0.1:
            trend = "declining"

        return {
            "total_feedback": total,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "positive_ratio": round(overall_positive_ratio, 4),
            "trend": trend,
        }

    def optimize_response(self, current_response: str, intent_category: str, user_context: Dict = None) -> str:
        """对当前回复应用优化"""
        if not intent_category:
            return current_response

        best = self.get_best_template(intent_category)
        if not best:
            return current_response

        # 如果模板中有占位符，尝试替换
        user_context = user_context or {}
        optimized = best
        for key, value in user_context.items():
            placeholder = f"{{{key}}}"
            if placeholder in optimized:
                optimized = optimized.replace(placeholder, str(value))

        # 如果最佳模板成功率低于50%，返回当前回复
        row = self.conn.execute(
            """
            SELECT success_count, failure_count FROM response_templates
            WHERE template_text = ? AND intent_category = ?
            """,
            (best, intent_category),
        ).fetchone()

        if row:
            total = row["success_count"] + row["failure_count"]
            if total > 0:
                rate = row["success_count"] / total
                if rate >= 0.5:
                    return optimized

        return current_response

    def learn_from_conversation(self, message: str, response: str, user_feedback: str = None) -> None:
        """从对话 + 反馈中自动学习"""
        # 推断意图类别
        intent = self._infer_intent(message)

        # 如果用户给出了反馈
        if user_feedback:
            feedback_type = self._classify_feedback(user_feedback)
            self.record_feedback(response, feedback_type, message)

            # 尝试找到匹配的模板并更新
            row = self.conn.execute(
                "SELECT template_id, template_text FROM response_templates WHERE intent_category = ?",
                (intent,),
            ).fetchall()

            for r in row:
                if r["template_text"] in response or self._text_similarity(r["template_text"], response) > 0.7:
                    self.update_template_success(r["template_id"], feedback_type == "positive")

        # 如果没有模板，尝试从回复中自动创建
        existing = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM response_templates WHERE intent_category = ?",
            (intent,),
        ).fetchone()

        if existing and existing["cnt"] == 0:
            # 自动创建模板：提取回复中常见模式
            pattern = self._extract_pattern(response)
            if pattern:
                self.add_template(intent, pattern, response)

    def get_templates(self, intent_category: str) -> List[ResponseTemplate]:
        """列出某个意图的所有模板"""
        rows = self.conn.execute(
            """
            SELECT template_id, intent_category, pattern, template_text,
                   CASE WHEN (success_count + failure_count) > 0
                       THEN success_count * 1.0 / (success_count + failure_count)
                       ELSE 0 END as success_rate,
                   usage_count
            FROM response_templates
            WHERE intent_category = ?
            ORDER BY success_rate DESC, usage_count DESC
            """,
            (intent_category,),
        ).fetchall()

        return [
            ResponseTemplate(
                template_id=r["template_id"],
                intent_category=r["intent_category"],
                pattern=r["pattern"],
                template_text=r["template_text"],
                success_rate=round(r["success_rate"], 4),
                usage_count=r["usage_count"],
            )
            for r in rows
        ]

    # ─── Internal helpers ─────────────────────────────────────────────

    def _infer_intent(self, message: str) -> str:
        """根据消息内容推断意图类别"""
        message_lower = message.lower()

        intent_keywords = {
            "greeting": ["你好", "hello", "hi", "早上好", "晚上好", "嗨"],
            "query": ["什么", "怎么", "如何", "为什么", "who", "what", "how", "where"],
            "request": ["帮我", "请", "能不能", "可以", "please", "do"],
            "confirm": ["确认", "确定", "是的", "对的", "yes", "confirm", "ok"],
            "deny": ["不", "不要", "取消", "no", "cancel", "stop"],
            "thanks": ["谢谢", "感谢", "thanks", "thank you"],
            "complaint": ["不好", "错误", "问题", "bug", "错", "差"],
        }

        for intent, keywords in intent_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return intent

        return "general"

    def _classify_feedback(self, feedback: str) -> str:
        """分类用户反馈"""
        feedback_lower = feedback.lower()

        positive_words = ["好", "棒", "喜欢", "谢谢", "满意", "正确", "great", "good", "nice", "thanks", "yes", "对"]
        negative_words = ["不好", "差", "错", "讨厌", "垃圾", "wrong", "bad", "no", "不", "错"]

        pos_count = sum(1 for w in positive_words if w in feedback_lower)
        neg_count = sum(1 for w in negative_words if w in feedback_lower)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"

    def _extract_pattern(self, text: str) -> str:
        """从回复文本中提取模式"""
        # 将具体名词替换为占位符
        pattern = text
        # 替换数字
        pattern = re.sub(r'\b\d+\b', '{number}', pattern)
        # 替换日期模式
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}', '{date}', pattern)
        return pattern

    def _text_similarity(self, text1: str, text2: str) -> float:
        """简单文本相似度计算"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def close(self):
        self.conn.close()
