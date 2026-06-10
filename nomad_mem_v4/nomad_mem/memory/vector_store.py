"""
VectorStore - 向量数据库存储层
亚符号层：向量嵌入空间
"""
import sqlite3
import numpy as np
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import hashlib


class VectorStore:
    """向量数据库"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """初始化向量空间表"""
        cursor = self.conn.cursor()

        # 向量存储表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                embedding BLOB NOT NULL,
                content_hash TEXT UNIQUE,
                raw_content TEXT,
                source_type TEXT,
                emotion_score REAL DEFAULT 0.0,
                novelty_score REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                plasticity REAL DEFAULT 1.0
            )
        """)

        # 向量相似度关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_similarities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_a_id INTEGER NOT NULL,
                vector_b_id INTEGER NOT NULL,
                cosine_similarity REAL NOT NULL,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vector_a_id) REFERENCES vectors(id),
                FOREIGN KEY (vector_b_id) REFERENCES vectors(id)
            )
        """)

        # 海马体表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hippocampus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_id INTEGER NOT NULL,
                consolidation_count INTEGER DEFAULT 0,
                decay_factor REAL DEFAULT 0.95,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_reactivated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vector_id) REFERENCES vectors(id)
            )
        """)

        # 皮层表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cortex (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_id INTEGER NOT NULL,
                importance_score REAL DEFAULT 0.0,
                consolidated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vector_id) REFERENCES vectors(id)
            )
        """)

        # 向量→节点映射表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_to_node (
                vector_id INTEGER NOT NULL,
                node_id INTEGER NOT NULL,
                membership_strength REAL DEFAULT 1.0,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (vector_id, node_id),
                FOREIGN KEY (vector_id) REFERENCES vectors(id),
                FOREIGN KEY (node_id) REFERENCES nodes(id)
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectors_hash ON vectors(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectors_source ON vectors(source_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectors_emotion ON vectors(emotion_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vector_similarities_a ON vector_similarities(vector_a_id)")

        self.conn.commit()

    def insert_vector(self, embedding: np.ndarray, content: str,
                     source_type: str, emotion_score: float = 0.0) -> int:
        """插入新向量到海马体"""
        cursor = self.conn.cursor()
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # 检查是否已存在
        cursor.execute("SELECT id FROM vectors WHERE content_hash = ?", (content_hash,))
        row = cursor.fetchone()
        if row:
            return row["id"]

        # 序列化向量
        embedding_bytes = embedding.tobytes()

        cursor.execute("""
            INSERT INTO vectors (embedding, content_hash, raw_content, source_type,
                                emotion_score, novelty_score, plasticity, created_at, last_accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, 1.0, ?, ?)
        """, (embedding_bytes, content_hash, content, source_type,
              emotion_score, 1.0, datetime.now(), datetime.now()))

        vector_id = cursor.lastrowid

        # 同时插入海马体
        cursor.execute("""
            INSERT INTO hippocampus (vector_id, created_at, last_reactivated_at)
            VALUES (?, ?, ?)
        """, (vector_id, datetime.now(), datetime.now()))

        self.conn.commit()
        return vector_id

    def get_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """获取向量"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vectors WHERE id = ?", (vector_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_vector(row)

    def get_all_vectors(self) -> List[Dict[str, Any]]:
        """获取所有向量"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vectors ORDER BY created_at DESC")
        return [self._row_to_vector(row) for row in cursor.fetchall()]

    def get_embedding(self, vector_id: int) -> Optional[np.ndarray]:
        """获取向量嵌入"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT embedding FROM vectors WHERE id = ?", (vector_id,))
        row = cursor.fetchone()

        if not row:
            return None

        embedding_bytes = row["embedding"]
        return np.frombuffer(embedding_bytes, dtype=np.float32)

    def search_similar(self, embedding: np.ndarray, top_k: int = 10,
                      min_similarity: float = 0.0) -> List[Tuple[int, float]]:
        """搜索相似向量"""
        all_vectors = self.get_all_vectors()
        results = []

        for vec in all_vectors:
            vec_embedding = self.get_embedding(vec["id"])
            if vec_embedding is None:
                continue

            similarity = self._cosine_similarity(embedding, vec_embedding)
            if similarity >= min_similarity:
                results.append((vec["id"], similarity))

        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def update_last_accessed(self, vector_id: int):
        """更新最后访问时间"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE vectors SET last_accessed_at = ? WHERE id = ?
        """, (datetime.now(), vector_id))
        self.conn.commit()

    def update_novelty(self, vector_id: int, novelty_score: float):
        """更新新颖性分数"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE vectors SET novelty_score = ? WHERE id = ?
        """, (novelty_score, vector_id))
        self.conn.commit()

    def store_similarity(self, vector_a_id: int, vector_b_id: int, similarity: float):
        """存储向量相似度关系"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO vector_similarities
            (vector_a_id, vector_b_id, cosine_similarity)
            VALUES (?, ?, ?)
        """, (vector_a_id, vector_b_id, similarity))
        self.conn.commit()

    def _row_to_vector(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为向量字典"""
        return {
            "id": row["id"],
            "content_hash": row["content_hash"],
            "raw_content": row["raw_content"] or "",
            "source_type": row["source_type"],
            "emotion_score": row["emotion_score"],
            "novelty_score": row["novelty_score"],
            "plasticity": row["plasticity"],
            "created_at": row["created_at"],
            "last_accessed_at": row["last_accessed_at"],
        }

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
