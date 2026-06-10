"""
MemoryStore - 万物皆节点存储核心
v3.0: 统一节点表 + 边表，万物平等关联
"""
import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any


class MemoryStore:
    """万物皆节点的记忆存储"""

    def __init__(self, db_path: str):
        """连接SQLite，初始化nodes和edges表"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """建表：nodes（万物节点）+ edges（万物关联）"""
        cursor = self.conn.cursor()

        # nodes表：万物皆节点
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT DEFAULT '',
                node_type TEXT DEFAULT 'general',
                tags_json TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                importance_score REAL DEFAULT 0.0
            )
        """)

        # edges表：万物关联不受限
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_node_id INTEGER NOT NULL,
                target_node_id INTEGER NOT NULL,
                edge_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                metadata_json TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_node_id) REFERENCES nodes(id),
                FOREIGN KEY (target_node_id) REFERENCES nodes(id)
            )
        """)

        # 创建索引加速查询
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type)")

        self.conn.commit()

    # ========== 节点操作（万物皆节点） ==========

    def upsert_node(self, name: str, content: str = "", node_type: str = "general") -> int:
        """
        创建或更新节点
        - name不存在：INSERT新节点
        - name已存在：追加content，更新updated_at
        返回：node_id
        """
        cursor = self.conn.cursor()

        # 检查是否存在
        cursor.execute("SELECT id, content FROM nodes WHERE name = ?", (name,))
        row = cursor.fetchone()

        if row:
            # 已存在：追加内容
            node_id = row["id"]
            existing_content = row["content"] or ""
            new_content = existing_content + "\n---\n" + content if existing_content else content

            cursor.execute("""
                UPDATE nodes
                SET content = ?, updated_at = ?
                WHERE id = ?
            """, (new_content, datetime.now(), node_id))
        else:
            # 不存在：创建新节点
            cursor.execute("""
                INSERT INTO nodes (name, content, node_type, tags_json, created_at, updated_at)
                VALUES (?, ?, ?, '{}', ?, ?)
            """, (name, content, node_type, datetime.now(), datetime.now()))
            node_id = cursor.lastrowid

        self.conn.commit()
        return node_id

    def get_node(self, node_id: int) -> Optional[Dict[str, Any]]:
        """获取单个节点"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_node(row)

    def get_node_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """按名称获取节点"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_node(row)

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """获取所有节点"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes ORDER BY importance_score DESC")
        return [self._row_to_node(row) for row in cursor.fetchall()]

    def search_nodes(self, keyword: str) -> List[Dict[str, Any]]:
        """模糊搜索节点（name和content）"""
        cursor = self.conn.cursor()
        pattern = f"%{keyword}%"
        cursor.execute("""
            SELECT * FROM nodes
            WHERE name LIKE ? OR content LIKE ?
            ORDER BY importance_score DESC
        """, (pattern, pattern))
        return [self._row_to_node(row) for row in cursor.fetchall()]

    def _row_to_node(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为节点字典"""
        tags_json = row["tags_json"] or "{}"
        return {
            "id": row["id"],
            "name": row["name"],
            "content": row["content"] or "",
            "node_type": row["node_type"],
            "tags": json.loads(tags_json),
            "importance_score": row["importance_score"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    # ========== 标签操作（自由标签系统） ==========

    def set_tag(self, node_id: int, tag_name: str, tag_value: str) -> None:
        """为节点设置标签"""
        cursor = self.conn.cursor()

        # 获取当前标签
        cursor.execute("SELECT tags_json FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()

        if not row:
            return

        tags = json.loads(row["tags_json"] or "{}")
        tags[tag_name] = tag_value

        cursor.execute("""
            UPDATE nodes
            SET tags_json = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(tags, ensure_ascii=False), datetime.now(), node_id))

        self.conn.commit()

    def remove_tag(self, node_id: int, tag_name: str) -> None:
        """删除标签"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT tags_json FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()

        if not row:
            return

        tags = json.loads(row["tags_json"] or "{}")
        if tag_name in tags:
            del tags[tag_name]

        cursor.execute("""
            UPDATE nodes
            SET tags_json = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(tags, ensure_ascii=False), datetime.now(), node_id))

        self.conn.commit()

    def get_tag(self, node_id: int, tag_name: str) -> Optional[str]:
        """获取单个标签值"""
        tags = self.get_all_tags(node_id)
        return tags.get(tag_name)

    def get_all_tags(self, node_id: int) -> Dict[str, str]:
        """获取节点所有标签"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT tags_json FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()

        if not row:
            return {}

        return json.loads(row["tags_json"] or "{}")

    def get_nodes_by_tag(self, tag_name: str, tag_value: Optional[str] = None) -> List[Dict[str, Any]]:
        """按标签搜索节点"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes")
        results = []

        for row in cursor.fetchall():
            node = self._row_to_node(row)
            tags = node["tags"]

            if tag_name in tags:
                if tag_value is None or tags[tag_name] == tag_value:
                    results.append(node)

        return results

    # ========== 边操作（万物关联不受限） ==========

    def upsert_edge(self, source_node_id: int, target_node_id: int,
                    edge_type: str, metadata: Optional[Dict] = None) -> int:
        """
        创建或更新边
        - 已存在：strength += 0.1（上限5.0）
        - 不存在：INSERT strength=1.0
        """
        cursor = self.conn.cursor()
        metadata = metadata or {}

        # 检查是否存在
        cursor.execute("""
            SELECT id, strength, metadata_json FROM edges
            WHERE source_node_id = ? AND target_node_id = ? AND edge_type = ?
        """, (source_node_id, target_node_id, edge_type))
        row = cursor.fetchone()

        if row:
            # 已存在：增加强度
            edge_id = row["id"]
            new_strength = min(5.0, row["strength"] + 0.1)

            # 合并metadata
            existing_meta = json.loads(row["metadata_json"] or "{}")
            existing_meta.update(metadata)

            cursor.execute("""
                UPDATE edges
                SET strength = ?, metadata_json = ?
                WHERE id = ?
            """, (new_strength, json.dumps(existing_meta, ensure_ascii=False), edge_id))
        else:
            # 不存在：创建新边
            cursor.execute("""
                INSERT INTO edges (source_node_id, target_node_id, edge_type, strength, metadata_json, created_at)
                VALUES (?, ?, ?, 1.0, ?, ?)
            """, (source_node_id, target_node_id, edge_type,
                  json.dumps(metadata, ensure_ascii=False), datetime.now()))
            edge_id = cursor.lastrowid

        self.conn.commit()
        return edge_id

    def get_edges(self, node_id: Optional[int] = None,
                  edge_type: Optional[str] = None,
                  min_strength: float = 0.0) -> List[Dict[str, Any]]:
        """查询边"""
        cursor = self.conn.cursor()

        if node_id is not None:
            cursor.execute("""
                SELECT * FROM edges
                WHERE (source_node_id = ? OR target_node_id = ?)
                AND strength >= ?
                ORDER BY strength DESC
            """, (node_id, node_id, min_strength))
        elif edge_type is not None:
            cursor.execute("""
                SELECT * FROM edges
                WHERE edge_type = ? AND strength >= ?
                ORDER BY strength DESC
            """, (edge_type, min_strength))
        else:
            cursor.execute("""
                SELECT * FROM edges
                WHERE strength >= ?
                ORDER BY strength DESC
            """, (min_strength,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "source_node_id": row["source_node_id"],
                "target_node_id": row["target_node_id"],
                "edge_type": row["edge_type"],
                "strength": row["strength"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
                "created_at": row["created_at"]
            })

        return results

    def get_connected_nodes(self, node_id: int,
                           edge_type: Optional[str] = None,
                           min_strength: float = 0.0) -> List[Dict[str, Any]]:
        """获取与指定节点相连的所有邻居节点"""
        edges = self.get_edges(node_id, edge_type, min_strength)
        neighbor_ids = set()

        for edge in edges:
            if edge["source_node_id"] == node_id:
                neighbor_ids.add(edge["target_node_id"])
            else:
                neighbor_ids.add(edge["source_node_id"])

        neighbors = []
        for nid in neighbor_ids:
            node = self.get_node(nid)
            if node:
                neighbors.append(node)

        return neighbors

    def remove_edge(self, source_node_id: int, target_node_id: int, edge_type: str) -> bool:
        """删除边"""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM edges
            WHERE source_node_id = ? AND target_node_id = ? AND edge_type = ?
        """, (source_node_id, target_node_id, edge_type))

        deleted = cursor.rowcount > 0
        self.conn.commit()
        return deleted

    def get_all_edges(self) -> List[Dict[str, Any]]:
        """获取所有边"""
        return self.get_edges()

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
