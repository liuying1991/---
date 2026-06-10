"""
Cortex - 皮层慢固层
低可塑性，长期稳定
"""
import sqlite3
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any


class Cortex:
    """皮层：慢固层"""

    def __init__(self, conn: sqlite3.Connection, config: Dict[str, Any]):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.config = config
        self.sleep_config = config.get("sleep", {})
        self.importance_threshold = self.sleep_config.get("importance_threshold", 0.5)
        self.max_consolidation_count = self.sleep_config.get("consolidation_count_max", 3)

    def consolidate(self, vector_id: int, importance_score: float) -> int:
        """
        将向量巩固到皮层
        返回: cortex_id
        """
        cursor = self.conn.cursor()

        # 检查是否已在皮层
        cursor.execute("SELECT id FROM cortex WHERE vector_id = ?", (vector_id,))
        row = cursor.fetchone()

        if row:
            # 已在皮层，更新重要性
            cortex_id = row["id"]
            cursor.execute("""
                UPDATE cortex SET importance_score = ?, last_accessed_at = ?
                WHERE id = ?
            """, (importance_score, datetime.now(), cortex_id))
        else:
            # 新巩固到皮层
            cursor.execute("""
                INSERT INTO cortex (vector_id, importance_score, consolidated_at, last_accessed_at)
                VALUES (?, ?, ?, ?)
            """, (vector_id, importance_score, datetime.now(), datetime.now()))
            cortex_id = cursor.lastrowid

        # 降低可塑性（皮层低可塑性）
        cursor.execute("""
            UPDATE vectors SET plasticity = 0.1 WHERE id = ?
        """, (vector_id,))

        self.conn.commit()
        return cortex_id

    def update_access(self, vector_id: int):
        """更新皮层向量访问时间"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE cortex SET last_accessed_at = ? WHERE vector_id = ?
        """, (datetime.now(), vector_id))
        self.conn.commit()

    def get_by_vector_id(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """通过向量ID获取皮层记录"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cortex WHERE vector_id = ?", (vector_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "vector_id": row["vector_id"],
            "importance_score": row["importance_score"],
            "consolidated_at": row["consolidated_at"],
            "last_accessed_at": row["last_accessed_at"],
        }

    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有皮层向量"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.*, c.importance_score, c.consolidated_at
            FROM cortex c
            JOIN vectors v ON v.id = c.vector_id
            ORDER BY c.importance_score DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def get_low_importance(self, threshold: float = None) -> List[int]:
        """获取低重要性的皮层向量"""
        if threshold is None:
            threshold = self.importance_threshold

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.vector_id FROM cortex c
            WHERE c.importance_score < ?
        """, (threshold,))

        return [row["vector_id"] for row in cursor.fetchall()]
