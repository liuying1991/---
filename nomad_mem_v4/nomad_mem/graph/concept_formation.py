"""
ConceptFormation - 概念形成
从向量空间聚类生成符号层节点
"""
import sqlite3
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter


class ConceptFormation:
    """概念形成器"""

    def __init__(self, conn: sqlite3.Connection, config: Dict[str, Any]):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.config = config
        self.discovery_config = config.get("discovery", {})
        self.eps = self.discovery_config.get("clustering_eps", 0.5)
        self.min_samples = self.discovery_config.get("clustering_min_samples", 2)
        self._ensure_tables()

    def _ensure_tables(self):
        """确保nodes和vector_to_node表存在"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT,
                node_type TEXT DEFAULT 'concept',
                centroid_vector_id INTEGER,
                member_vector_ids TEXT DEFAULT '[]',
                importance_score REAL DEFAULT 0.5,
                tags_json TEXT DEFAULT '{}',
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_to_node (
                vector_id INTEGER,
                node_id INTEGER,
                membership_strength REAL DEFAULT 1.0,
                assigned_at TIMESTAMP,
                PRIMARY KEY (vector_id, node_id)
            )
        """)
        self.conn.commit()

    def run_clustering(self) -> Dict[str, Any]:
        """
        执行向量聚类形成概念
        返回: {
            "clusters": {cluster_id: [vector_ids]},
            "new_concepts": [{"name": "...", "centroid_id": ...}],
            "mapping": {vector_id: node_id}
        }
        """
        cursor = self.conn.cursor()

        # 获取所有向量
        cursor.execute("SELECT id, raw_content FROM vectors")
        vectors = []
        vector_ids = []
        contents = []

        for row in cursor.fetchall():
            embedding = self._get_embedding(row["id"])
            if embedding is not None:
                vectors.append(embedding)
                vector_ids.append(row["id"])
                contents.append(row["raw_content"] or "")

        if len(vectors) < self.min_samples:
            return {"clusters": {}, "new_concepts": [], "mapping": {}}

        # DBSCAN聚类
        vectors_np = np.array(vectors)
        try:
            from sklearn.cluster import DBSCAN
            clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric='cosine')
            labels = clustering.fit_predict(vectors_np)
        except ImportError:
            # 简单聚类：按相似度阈值
            labels = self._simple_cluster(vectors_np)

        # 处理聚类结果
        clusters = {}
        new_concepts = []
        mapping = {}

        for i, label in enumerate(labels):
            if label == -1:
                continue  # 噪声点

            if label not in clusters:
                clusters[label] = []
            clusters[label].append(vector_ids[i])

        # 为每个簇创建概念节点
        for cluster_id, vec_ids in clusters.items():
            # 计算簇中心向量ID（最接近所有点的向量）
            centroid_id = self._find_centroid(vec_ids)

            # 提取节点名（簇内高频词）
            cluster_contents = [contents[vector_ids.index(vid)] for vid in vec_ids if vid in [v for v in vector_ids]]
            node_name = self._extract_concept_name(cluster_contents)

            # 创建节点
            cursor.execute("""
                INSERT INTO nodes (name, content, node_type, centroid_vector_id, member_vector_ids, importance_score, created_at, updated_at)
                VALUES (?, ?, 'concept', ?, ?, 0.5, ?, ?)
            """, (node_name, f"概念簇包含{len(vec_ids)}个向量",
                  centroid_id, json.dumps(vec_ids), datetime.now(), datetime.now()))
            node_id = cursor.lastrowid

            # 建立映射
            for vec_id in vec_ids:
                cursor.execute("""
                    INSERT OR REPLACE INTO vector_to_node (vector_id, node_id, membership_strength, assigned_at)
                    VALUES (?, ?, ?, ?)
                """, (vec_id, node_id, 1.0, datetime.now()))
                mapping[vec_id] = node_id

            new_concepts.append({
                "name": node_name,
                "centroid_id": centroid_id,
                "node_id": node_id,
                "member_count": len(vec_ids)
            })

        self.conn.commit()

        return {
            "clusters": clusters,
            "new_concepts": new_concepts,
            "mapping": mapping
        }

    def _find_centroid(self, vector_ids: List[int]) -> int:
        """找到簇的中心向量"""
        import numpy as np
        cursor = self.conn.cursor()

        embeddings = []
        for vec_id in vector_ids:
            cursor.execute("SELECT embedding FROM vectors WHERE id = ?", (vec_id,))
            row = cursor.fetchone()
            if row:
                embedding = np.frombuffer(row["embedding"], dtype=np.float32)
                embeddings.append((vec_id, embedding))

        if not embeddings:
            return vector_ids[0] if vector_ids else 0

        # 计算中心点
        vec_array = np.array([e[1] for e in embeddings])
        center = np.mean(vec_array, axis=0)

        # 找到最接近中心的向量
        min_dist = float('inf')
        centroid_id = embeddings[0][0]

        for vec_id, embedding in embeddings:
            dist = np.linalg.norm(embedding - center)
            if dist < min_dist:
                min_dist = dist
                centroid_id = vec_id

        return centroid_id

    def _extract_concept_name(self, contents: List[str]) -> str:
        """从内容中提取概念名"""
        try:
            import jieba
        except ImportError:
            # 简单分词
            all_words = []
            for content in contents:
                words = content.replace("，", " ").replace("。", " ").split()
                all_words.extend([w for w in words if len(w) >= 2])
        else:
            all_words = []
            for content in contents:
                words = jieba.lcut(content)
                all_words.extend([w for w in words if len(w) >= 2])

        # 统计词频
        word_counts = Counter(all_words)
        top_words = word_counts.most_common(3)

        if top_words:
            return "概念:" + "+".join([w[0] for w in top_words])

        return "概念:未命名"

    def _simple_cluster(self, vectors: np.ndarray) -> np.ndarray:
        """简单聚类算法（无sklearn时）"""
        n = len(vectors)
        labels = np.zeros(n, dtype=int)
        cluster_count = 0

        for i in range(n):
            assigned = False
            for j in range(i):
                if labels[j] != -1:  # 不是噪声点
                    similarity = self._cosine_similarity(vectors[i], vectors[j])
                    if similarity >= (1 - self.eps):
                        labels[i] = labels[j]
                        assigned = True
                        break
            if not assigned:
                labels[i] = cluster_count
                cluster_count += 1

        return labels

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _get_embedding(self, vector_id: int) -> np.ndarray:
        """获取向量嵌入"""
        import numpy as np
        cursor = self.conn.cursor()
        cursor.execute("SELECT embedding FROM vectors WHERE id = ?", (vector_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return np.frombuffer(row["embedding"], dtype=np.float32)
