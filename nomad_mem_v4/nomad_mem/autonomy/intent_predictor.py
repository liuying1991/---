"""
Intent Predictor - 主动意图预测引擎

基于历史交互模式预测用户下一步意图，让 Jarvis 能在用户开口前预判需求。

核心特性:
- 意图共现矩阵: 统计意图间的转移概率（马尔可夫链）
- 时间模式: 识别时间段与意图的关联
- 场景上下文: 结合当前场景调整预测权重
- 个性化学习: 每个用户独立的预测模型
- SQLite 持久化: 轻量级本地存储

设计原则:
- 预测基于数据，而非猜测
- 概率透明: 每个预测都有置信度
- 可解释: 能说明为什么做出这个预测
- 渐进改进: 随着交互增多，预测越来越准

数学基础:
- 一阶马尔可夫链: P(next|current) = count(current->next) / count(current)
- 时间权重: 最近交互权重更高
- 场景权重: 当前场景相关的意图有额外加分
"""
import sqlite3
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class IntentPrediction:
    """意图预测结果

    Attributes:
        predicted_intent: 预测的意图
        confidence: 置信度 (0.0-1.0)
        reason: 预测原因
        supporting_evidence: 支撑证据
    """
    predicted_intent: str
    confidence: float
    reason: str
    supporting_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "predicted_intent": self.predicted_intent,
            "confidence": self.confidence,
            "reason": self.reason,
            "supporting_evidence": self.supporting_evidence,
        }


class IntentPredictor:
    """
    意图预测引擎

    使用意图共现矩阵和时间模式预测用户下一步意图。

    使用示例:
        >>> predictor = IntentPredictor(db_path="intent_predictor.db")
        >>> predictor.record_transition("user1", "greeting", "query")
        >>> predictions = predictor.predict_next("user1", current_intent="query")
        >>> for p in predictions:
        ...     print(f"{p.predicted_intent}: {p.confidence:.2f}")
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS intent_transitions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         TEXT NOT NULL DEFAULT 'default',
                from_intent     TEXT NOT NULL,
                to_intent       TEXT NOT NULL,
                timestamp       REAL NOT NULL,
                scene_context   TEXT NOT NULL DEFAULT '',
                success         INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS time_patterns (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         TEXT NOT NULL DEFAULT 'default',
                intent          TEXT NOT NULL,
                hour_of_day     INTEGER NOT NULL,
                day_of_week     INTEGER NOT NULL,
                count           INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_trans_user ON intent_transitions(user_id);
            CREATE INDEX IF NOT EXISTS idx_trans_from ON intent_transitions(from_intent);
            CREATE INDEX IF NOT EXISTS idx_trans_time ON intent_transitions(timestamp);
            CREATE INDEX IF NOT EXISTS idx_time_user ON time_patterns(user_id, intent);
        """)
        conn.commit()
        conn.close()

    # ── Recording ─────────────────────────────────────────────────────────

    def record_transition(
        self,
        user_id: str,
        from_intent: str,
        to_intent: str,
        scene_context: str = "",
        success: bool = True,
    ):
        """
        记录意图转换

        Args:
            user_id: 用户ID
            from_intent: 当前意图
            to_intent: 下一个意图
            scene_context: 场景上下文
            success: 转换是否成功
        """
        now = time.time()
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO intent_transitions 
            (user_id, from_intent, to_intent, timestamp, scene_context, success)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, from_intent, to_intent, now, scene_context, int(success)),
        )
        conn.commit()
        conn.close()

    def record_time_pattern(
        self,
        user_id: str,
        intent: str,
        hour_of_day: int,
        day_of_week: int,
    ):
        """
        记录时间模式

        Args:
            user_id: 用户ID
            intent: 意图
            hour_of_day: 小时 (0-23)
            day_of_week: 星期几 (0=周一, 6=周日)
        """
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO time_patterns (user_id, intent, hour_of_day, day_of_week, count)
            VALUES (?, ?, ?, ?, 1)""",
            (user_id, intent, hour_of_day, day_of_week),
        )
        conn.commit()
        conn.close()

    # ── Prediction ────────────────────────────────────────────────────────

    def predict_next(
        self,
        user_id: str,
        current_intent: str = "",
        scene_context: str = "",
        k: int = 5,
    ) -> List[IntentPrediction]:
        """
        预测用户的下一个意图

        Args:
            user_id: 用户ID
            current_intent: 当前意图
            scene_context: 当前场景
            k: 返回预测数量

        Returns:
            预测列表，按置信度降序
        """
        predictions = {}

        # 1. 基于意图共现矩阵的预测
        if current_intent:
            cooccurrence_preds = self._predict_by_cooccurrence(user_id, current_intent, k)
            for p in cooccurrence_preds:
                predictions[p.predicted_intent] = p

        # 2. 基于时间模式的预测
        time_preds = self._predict_by_time(user_id, k)
        for p in time_preds:
            intent = p.predicted_intent
            if intent in predictions:
                # 融合: 加权平均
                old_conf = predictions[intent].confidence
                new_conf = 0.6 * old_conf + 0.4 * p.confidence
                predictions[intent] = IntentPrediction(
                    predicted_intent=intent,
                    confidence=min(new_conf, 1.0),
                    reason=f"{predictions[intent].reason}; {p.reason}",
                    supporting_evidence=predictions[intent].supporting_evidence + p.supporting_evidence,
                )
            else:
                predictions[intent] = p

        # 3. 场景上下文加成
        if scene_context:
            for intent, pred in predictions.items():
                scene_bonus = self._get_scene_bonus(user_id, intent, scene_context)
                pred.confidence = min(pred.confidence + scene_bonus, 1.0)

        # 排序并返回
        sorted_preds = sorted(predictions.values(), key=lambda x: -x.confidence)
        return sorted_preds[:k]

    def _predict_by_cooccurrence(
        self, user_id: str, current_intent: str, k: int
    ) -> List[IntentPrediction]:
        """基于意图共现矩阵预测"""
        conn = self._get_conn()

        # 获取所有从当前意图出发的转换及其计数
        rows = conn.execute(
            """SELECT to_intent, COUNT(*) as cnt,
               AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
               MAX(timestamp) as last_seen
               FROM intent_transitions
               WHERE user_id = ? AND from_intent = ?
               GROUP BY to_intent
               ORDER BY cnt DESC
               LIMIT ?""",
            (user_id, current_intent, k),
        ).fetchall()

        conn.close()

        if not rows:
            return []

        total = sum(r["cnt"] for r in rows)
        now = time.time()
        predictions = []

        for row in rows:
            # 基础概率 = 转换频率
            base_prob = row["cnt"] / total

            # 时间衰减: 最近交互权重更高
            time_diff = now - row["last_seen"]
            time_weight = max(0.3, 1.0 - (time_diff / (30 * 24 * 3600)))  # 30天衰减

            # 成功率加权
            success_weight = row["success_rate"]

            # 综合置信度
            confidence = base_prob * time_weight * success_weight

            predictions.append(IntentPrediction(
                predicted_intent=row["to_intent"],
                confidence=round(confidence, 4),
                reason=f"历史共现: {current_intent} → {row['to_intent']} ({row['cnt']}次)",
                supporting_evidence=[
                    f"共现{row['cnt']}次",
                    f"成功率{row['success_rate']:.0%}",
                ],
            ))

        return predictions

    def _predict_by_time(self, user_id: str, k: int) -> List[IntentPrediction]:
        """基于时间模式预测"""
        conn = self._get_conn()
        now = time.time()
        current_hour = int(time.localtime(now).tm_hour)
        current_dow = int(time.localtime(now).tm_wday)

        # 查找当前时间段最常见的意图
        rows = conn.execute(
            """SELECT intent, SUM(count) as total_count
               FROM time_patterns
               WHERE user_id = ?
                 AND (ABS(hour_of_day - ?) <= 2 OR ABS(day_of_week - ?) <= 1)
               GROUP BY intent
               ORDER BY total_count DESC
               LIMIT ?""",
            (user_id, current_hour, current_dow, k),
        ).fetchall()

        conn.close()

        if not rows:
            return []

        total = sum(r["total_count"] for r in rows)
        predictions = []

        for row in rows:
            confidence = row["total_count"] / total
            predictions.append(IntentPrediction(
                predicted_intent=row["intent"],
                confidence=round(confidence * 0.5, 4),  # 时间模式权重较低
                reason=f"时间模式: {current_hour}点常见意图",
                supporting_evidence=[f"该时段出现{row['total_count']}次"],
            ))

        return predictions

    def _get_scene_bonus(
        self, user_id: str, intent: str, scene_context: str
    ) -> float:
        """获取场景上下文加成"""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT COUNT(*) as cnt
               FROM intent_transitions
               WHERE user_id = ? AND to_intent = ? AND scene_context = ?""",
            (user_id, intent, scene_context),
        ).fetchone()
        conn.close()

        cnt = row["cnt"] if row else 0
        # 每有1次场景匹配，加成0.05，最多0.2
        return min(cnt * 0.05, 0.2)

    # ── Analytics ─────────────────────────────────────────────────────────

    def get_intent_flow(self, user_id: str, from_intent: str = "") -> List[Dict]:
        """
        获取意图流转统计

        Args:
            user_id: 用户ID
            from_intent: 可选，从指定意图出发

        Returns:
            流转统计列表
        """
        conn = self._get_conn()
        if from_intent:
            rows = conn.execute(
                """SELECT from_intent, to_intent, COUNT(*) as cnt,
                   AVG(success) as success_rate
                   FROM intent_transitions
                   WHERE user_id = ? AND from_intent = ?
                   GROUP BY from_intent, to_intent
                   ORDER BY cnt DESC""",
                (user_id, from_intent),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT from_intent, to_intent, COUNT(*) as cnt,
                   AVG(success) as success_rate
                   FROM intent_transitions
                   WHERE user_id = ?
                   GROUP BY from_intent, to_intent
                   ORDER BY cnt DESC
                   LIMIT 20""",
                (user_id,),
            ).fetchall()
        conn.close()

        return [
            {
                "from": r["from_intent"],
                "to": r["to_intent"],
                "count": r["cnt"],
                "success_rate": r["success_rate"],
            }
            for r in rows
        ]

    def get_user_intent_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户意图画像

        Args:
            user_id: 用户ID

        Returns:
            意图画像字典
        """
        conn = self._get_conn()

        # 最频繁意图
        top_intents = conn.execute(
            """SELECT to_intent as intent, COUNT(*) as cnt
               FROM intent_transitions WHERE user_id = ?
               GROUP BY to_intent ORDER BY cnt DESC LIMIT 5""",
            (user_id,),
        ).fetchall()

        # 总转换数
        total = conn.execute(
            "SELECT COUNT(*) FROM intent_transitions WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]

        # 成功率
        success_rate = conn.execute(
            """SELECT AVG(success) FROM intent_transitions WHERE user_id = ?""",
            (user_id,),
        ).fetchone()[0]

        conn.close()

        return {
            "user_id": user_id,
            "total_transitions": total,
            "overall_success_rate": success_rate or 0.0,
            "top_intents": [
                {"intent": r["intent"], "count": r["cnt"]}
                for r in top_intents
            ],
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取系统整体统计"""
        conn = self._get_conn()
        total_transitions = conn.execute(
            "SELECT COUNT(*) FROM intent_transitions"
        ).fetchone()[0]
        total_patterns = conn.execute(
            "SELECT COUNT(*) FROM time_patterns"
        ).fetchone()[0]
        unique_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM intent_transitions"
        ).fetchone()[0]
        conn.close()

        return {
            "total_transitions": total_transitions,
            "total_time_patterns": total_patterns,
            "unique_users": unique_users,
        }

    def close(self):
        pass  # SQLite short-lived connections
