"""
SleepConsolidation - 睡眠巩固机制
模拟慢波睡眠中的海马体→皮层迁移
"""
import sqlite3
import numpy as np
from datetime import datetime
from typing import Dict, Any, List


class SleepConsolidation:
    """睡眠巩固引擎"""

    def __init__(self, conn: sqlite3.Connection, config: Dict[str, Any]):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.config = config
        self.sleep_config = config.get("sleep", {})
        self.importance_threshold = self.sleep_config.get("importance_threshold", 0.5)
        self.max_consolidation_count = self.sleep_config.get("consolidation_count_max", 3)

    def run(self) -> Dict[str, Any]:
        """
        执行睡眠巩固
        1. 选择海马体中待巩固的向量
        2. 计算重要性
        3. 重要性高的迁移到皮层
        4. 更新巩固次数
        5. 达到3次后从海马体删除
        """
        cursor = self.conn.cursor()

        stats = {
            "vectors_reviewed": 0,
            "vectors_consolidated": 0,
            "vectors_promoted": 0,
            "vectors_removed": 0,
        }

        # 1. 获取海马体中待巩固的向量
        cursor.execute("""
            SELECT v.id, v.emotion_score, v.novelty_score, v.plasticity,
                   h.consolidation_count, h.decay_factor
            FROM hippocampus h
            JOIN vectors v ON v.id = h.vector_id
            WHERE h.consolidation_count < ?
            ORDER BY (v.emotion_score * v.novelty_score) DESC
        """, (self.max_consolidation_count,))

        hippocampal_vectors = cursor.fetchall()
        stats["vectors_reviewed"] = len(hippocampal_vectors)

        for row in hippocampal_vectors:
            vector_id = row["id"]
            emotion_score = row["emotion_score"]
            novelty_score = row["novelty_score"]
            plasticity = row["plasticity"]
            consolidation_count = row["consolidation_count"]

            # 2. 计算重要性
            importance = self._compute_importance(emotion_score, novelty_score, plasticity)

            # 3. 重要性高的迁移到皮层
            if importance >= self.importance_threshold:
                self._consolidate_to_cortex(vector_id, importance)
                stats["vectors_consolidated"] += 1

            # 4. 更新巩固次数
            cursor.execute("""
                UPDATE hippocampus
                SET consolidation_count = consolidation_count + 1,
                    last_reactivated_at = ?
                WHERE vector_id = ?
            """, (datetime.now(), vector_id))

            # 5. 达到3次后从海马体删除（已巩固）
            if consolidation_count + 1 >= self.max_consolidation_count:
                # 如果还没在皮层，确保进入皮层
                cursor.execute("SELECT id FROM cortex WHERE vector_id = ?", (vector_id,))
                if not cursor.fetchone():
                    self._consolidate_to_cortex(vector_id, importance)
                    stats["vectors_promoted"] += 1

                # 从海马体删除
                cursor.execute("DELETE FROM hippocampus WHERE vector_id = ?", (vector_id,))
                stats["vectors_removed"] += 1

                # 降低可塑性
                cursor.execute("""
                    UPDATE vectors SET plasticity = 0.1 WHERE id = ?
                """, (vector_id,))

        self.conn.commit()

        return stats

    def _compute_importance(self, emotion_score: float, novelty_score: float,
                           plasticity: float) -> float:
        """
        计算重要性
        importance = emotion * novelty * plasticity
        """
        return emotion_score * novelty_score * plasticity

    def _consolidate_to_cortex(self, vector_id: int, importance: float):
        """将向量巩固到皮层"""
        cursor = self.conn.cursor()

        # 检查是否已在皮层
        cursor.execute("SELECT id FROM cortex WHERE vector_id = ?", (vector_id,))
        row = cursor.fetchone()

        if row:
            # 更新重要性
            cursor.execute("""
                UPDATE cortex SET importance_score = ?, last_accessed_at = ?
                WHERE vector_id = ?
            """, (importance, datetime.now(), vector_id))
        else:
            # 新巩固
            cursor.execute("""
                INSERT INTO cortex (vector_id, importance_score, consolidated_at, last_accessed_at)
                VALUES (?, ?, ?, ?)
            """, (vector_id, importance, datetime.now(), datetime.now()))

    def replay_and_reinforce(self):
        """
        睡眠中的回放强化
        重新激活海马体中的向量，增强连接
        """
        cursor = self.conn.cursor()

        # 获取海马体中所有向量
        cursor.execute("""
            SELECT v.id, h.consolidation_count
            FROM hippocampus h
            JOIN vectors v ON v.id = h.vector_id
            ORDER BY v.emotion_score DESC
        """)

        for row in cursor.fetchall():
            vector_id = row["id"]

            # 增加巩固次数（模拟回放）
            cursor.execute("""
                UPDATE hippocampus
                SET consolidation_count = consolidation_count + 1
                WHERE vector_id = ?
            """, (vector_id,))

            # 增加强度
            cursor.execute("""
                UPDATE vectors SET emotion_score = emotion_score * 1.1 WHERE id = ?
            """, (vector_id,))

        self.conn.commit()
