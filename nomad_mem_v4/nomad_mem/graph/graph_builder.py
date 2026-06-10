"""
GraphBuilder - 图构建器
基于nodes和edges构建NetworkX图
"""
import sqlite3
import json
import networkx as nx
from typing import Dict, Any, List, Optional


class GraphBuilder:
    """图构建器"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.graph = nx.Graph()
        self.rebuild()

    def rebuild(self):
        """重建图"""
        self.graph = nx.Graph()
        cursor = self.conn.cursor()

        # 加载所有节点
        cursor.execute("SELECT * FROM nodes")
        for row in cursor.fetchall():
            self.graph.add_node(
                row["id"],
                name=row["name"],
                node_type=row["node_type"],
                content=row["content"],
                tags=json.loads(row["tags_json"] or "{}"),
                importance_score=row["importance_score"]
            )

        # 加载所有边
        cursor.execute("SELECT * FROM edges")
        for row in cursor.fetchall():
            self.graph.add_edge(
                row["source_node_id"],
                row["target_node_id"],
                edge_type=row["edge_type"],
                strength=row["strength"],
                metadata=json.loads(row["metadata_json"] or "{}")
            )

    def get_graph(self) -> nx.Graph:
        """返回图对象"""
        return self.graph

    def find_path(self, source_name: str, target_name: str) -> Optional[List[str]]:
        """查找最短路径"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT id FROM nodes WHERE name = ?", (source_name,))
        source_row = cursor.fetchone()
        if not source_row:
            return None

        cursor.execute("SELECT id FROM nodes WHERE name = ?", (target_name,))
        target_row = cursor.fetchone()
        if not target_row:
            return None

        source_id = source_row["id"]
        target_id = target_row["id"]

        if source_id not in self.graph or target_id not in self.graph:
            return None

        try:
            path_ids = nx.shortest_path(self.graph, source_id, target_id)
            path_names = []
            for node_id in path_ids:
                node_data = self.graph.nodes[node_id]
                path_names.append(node_data.get("name", f"#{node_id}"))
            return path_names
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_hub_nodes(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """获取枢纽节点"""
        if len(self.graph) == 0:
            return []

        centrality = nx.degree_centrality(self.graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)

        results = []
        for node_id, cent in sorted_nodes[:top_k]:
            node_data = self.graph.nodes[node_id]
            results.append({
                "id": node_id,
                "name": node_data.get("name"),
                "centrality": cent
            })

        return results
