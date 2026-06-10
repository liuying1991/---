"""
ForgettingEngine - 主动遗忘算法
定期衰减、修剪、合并
"""
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any


class ForgettingEngine:
    """主动遗忘引擎"""

    def __init__(self, conn: sqlite3.Connection, config: Dict[str, Any]):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.config = config
        self.forgetting_config = config.get("forgetting", {})
        self.decay_rate = self.forgetting_config.get("decay_rate", 0.95)
        self.max_inactive_days = self.forgetting_config.get("max_inactive_days", 7)
        self.merge_similarity_threshold = self.forgetting_config.get("merge_similarity_threshold", 0.9)
        self.edge_pruning_threshold = self.forgetting_config.get("edge_pruning_threshold", 0.1)

    def run(self) -> Dict[str, Any]:
        """执行主动遗忘"""
        stats = {
            "vectors_decayed": 0,
            "vectors_merged": 0,
            "edges_pruned": 0,
            "vectors_removed": 0,
        }

        # 1. 海马体衰减
        stats["vectors_decayed"] = self._decay_hippocampus()

        # 2. 相似向量合并
        stats["vectors_merged"] = self._merge_similar_vectors()

        # 3. 边缘修剪
        stats["edges_pruned"] = self._prune_weak_edges()

        # 4. 长期未访问向量删除
        stats["vectors_removed"] = self._remove_inactive_vectors()

        return stats

    def _decay_hippocampus(self) -> int:
        """海马体衰减"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE hippocampus
            SET decay_factor = decay_factor * ?,
                last_reactivated_at = last_reactivated_at
            WHERE decay_factor > 0.1
        """, (self.decay_rate,))
        self.conn.commit()
        return cursor.rowcount

    def _merge_similar_vectors(self) -> int:
        """合并高度相似的向量"""
        cursor = self.conn.cursor()

        # 获取所有向量
        cursor.execute("SELECT id FROM vectors")
        vector_ids = [row["id"] for row in cursor.fetchall()]

        merged_count = 0
        to_remove = set()

        for i, vec_a_id in enumerate(vector_ids):
            if vec_a_id in to_remove:
                continue

            embedding_a = self._get_embedding(vec_a_id)
            if embedding_a is None:
                continue

            for vec_b_id in vector_ids[i+1:]:
                if vec_b_id in to_remove:
                    continue

                embedding_b = self._get_embedding(vec_b_id)
                if embedding_b is None:
                    continue

                similarity = self._cosine_similarity(embedding_a, embedding_b)

                if similarity >= self.merge_similarity_threshold:
                    # 合并到vec_a
                    self._merge_vectors(vec_a_id, vec_b_id)
                    to_remove.add(vec_b_id)
                    merged_count += 1

        # 删除被合并的向量
        for vec_id in to_remove:
            cursor.execute("DELETE FROM vectors WHERE id = ?", (vec_id,))
            cursor.execute("DELETE FROM hippocampus WHERE vector_id = ?", (vec_id,))
            cursor.execute("DELETE FROM cortex WHERE vector_id = ?", (vec_id,))

        self.conn.commit()
        return merged_count

    def _prune_weak_edges(self) -> int:
        """修剪弱边"""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM vector_similarities
            WHERE cosine_similarity < ?
        """, (self.edge_pruning_threshold,))
        self.conn.commit()
        return cursor.rowcount

    def _remove_inactive_vectors(self) -> int:
        """删除长期未访问的向量"""
        cursor = self.conn.cursor()
        cutoff = datetime.now() - timedelta(days=self.max_inactive_days)

        # 删除长期未访问的海马体向量
        cursor.execute("""
            DELETE FROM hippocampus
            WHERE last_reactivated_at < ?
            AND consolidation_count = 0
        """, (cutoff.isoformat(),))
        removed = cursor.rowcount

        # 更新向量表
        cursor.execute("""
            UPDATE vectors
            SET plasticity = plasticity * 0.5
            WHERE last_accessed_at < ?
            AND plasticity > 0.01
        """, (cutoff.isoformat(),))

        self.conn.commit()
        return removed

    def _get_embedding(self, vector_id: int) -> np.ndarray:
        """获取向量嵌入"""
        import numpy as np
        cursor = self.conn.cursor()
        cursor.execute("SELECT embedding FROM vectors WHERE id = ?", (vector_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return np.frombuffer(row["embedding"], dtype=np.float32)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _merge_vectors(self, target_id: int, source_id: int):
        """合并向量（将source的内容合并到target）"""
        import numpy as np
        cursor = self.conn.cursor()

        # 获取两个向量
        cursor.execute("SELECT raw_content FROM vectors WHERE id = ?", (target_id,))
        target_content = cursor.fetchone()["raw_content"]

        cursor.execute("SELECT raw_content FROM vectors WHERE id = ?", (source_id,))
        source_content = cursor.fetchone()["raw_content"]

        # 合并内容
        new_content = target_content + "\n---\n" + source_content
        cursor.execute("""
            UPDATE vectors SET raw_content = ? WHERE id = ?
        """, (new_content, target_id))
