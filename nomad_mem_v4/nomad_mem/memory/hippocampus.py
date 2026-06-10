"""
Hippocampus - 海马体快写层
高可塑性，快速编码，快速衰减
"""
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class Hippocampus:
    """海马体：快写层"""

    def __init__(self, conn: sqlite3.Connection, config: Dict[str, Any]):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.config = config
        self.learning_config = config.get("learning", {})
        self.base_lr = self.learning_config.get("base_lr", 0.1)
        self.emotion_multiplier = self.learning_config.get("emotion_multiplier", 2.0)

    def encode(self, vector_id: int, emotion_score: float) -> Dict[str, Any]:
        """
        海马体编码（快写）
        1. 计算情绪门控学习率
        2. 更新可塑性系数
        3. 返回编码信息
        """
        cursor = self.conn.cursor()

        # 计算情绪门控学习率
        learning_rate = self.base_lr * (1 + emotion_score * self.emotion_multiplier)

        # 获取向量
        cursor.execute("""
            SELECT id, emotion_score, novelty_score FROM vectors WHERE id = ?
        """, (vector_id,))
        vec_row = cursor.fetchone()

        if not vec_row:
            return {"error": "Vector not found"}

        # 更新海马体中的可塑性
        cursor.execute("""
            UPDATE hippocampus
            SET last_reactivated_at = ?, consolidation_count = consolidation_count + 1
            WHERE vector_id = ?
        """, (datetime.now(), vector_id))

        # 更新向量的情绪分数（加权平均）
        new_emotion = (vec_row["emotion_score"] + emotion_score) / 2
        cursor.execute("""
            UPDATE vectors SET emotion_score = ? WHERE id = ?
        """, (new_emotion, vector_id))

        self.conn.commit()

        return {
            "vector_id": vector_id,
            "learning_rate": learning_rate,
            "emotion_score": new_emotion,
            "consolidation_count": cursor.rowcount,
        }

    def get_vectors_for_consolidation(self, max_count: int = 3) -> List[Dict[str, Any]]:
        """获取待巩固的向量"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.id, v.emotion_score, v.novelty_score, h.consolidation_count,
                   h.decay_factor, h.last_reactivated_at
            FROM hippocampus h
            JOIN vectors v ON v.id = h.vector_id
            WHERE h.consolidation_count < 3
            ORDER BY (v.emotion_score * v.novelty_score) DESC
            LIMIT ?
        """, (max_count,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "vector_id": row["id"],
                "emotion_score": row["emotion_score"],
                "novelty_score": row["novelty_score"],
                "consolidation_count": row["consolidation_count"],
                "decay_factor": row["decay_factor"],
                "last_reactivated_at": row["last_reactivated_at"],
            })

        return results

    def apply_decay(self, vector_id: int, decay_factor: float = 0.95):
        """应用衰减（主动遗忘）"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE hippocampus
            SET decay_factor = decay_factor * ?
            WHERE vector_id = ?
        """, (decay_factor, vector_id))

        # 更新可塑性
        cursor.execute("""
            UPDATE vectors
            SET plasticity = plasticity * ?
            WHERE id = ?
        """, (decay_factor, vector_id))

        self.conn.commit()

    def remove_consolidated(self, vector_id: int):
        """从海马体删除已巩固的向量"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM hippocampus WHERE vector_id = ?", (vector_id,))
        self.conn.commit()

    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有海马体向量"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.*, h.consolidation_count, h.decay_factor
            FROM hippocampus h
            JOIN vectors v ON v.id = h.vector_id
        """)

        return [dict(row) for row in cursor.fetchall()]
