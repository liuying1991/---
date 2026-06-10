"""
MemoryGraph - 基于 nodes + edges 构建全图
万物皆节点，万物皆关联
"""
import networkx as nx
from typing import List, Dict, Any, Optional
from .store import MemoryStore


class MemoryGraph:
    """记忆图构建器"""

    def __init__(self, store: MemoryStore):
        """
        从MemoryStore加载所有nodes和edges，构建NetworkX图
        """
        self.store = store
        self.graph = nx.Graph()
        self.rebuild()

    def rebuild(self):
        """重新从数据库全量加载nodes + edges，构建图"""
        self.graph = nx.Graph()

        # 加载所有节点
        nodes = self.store.get_all_nodes()
        for node in nodes:
            self.graph.add_node(
                node["id"],
                name=node["name"],
                node_type=node["node_type"],
                content=node["content"],
                tags=node["tags"],
                importance_score=node["importance_score"]
            )

        # 加载所有边
        edges = self.store.get_all_edges()
        for edge in edges:
            self.graph.add_edge(
                edge["source_node_id"],
                edge["target_node_id"],
                edge_type=edge["edge_type"],
                strength=edge["strength"],
                metadata=edge["metadata"]
            )

    def get_graph(self) -> nx.Graph:
        """返回当前图对象"""
        return self.graph

    def find_connected(self, node_name: str, max_depth: int = 2) -> Dict[str, List]:
        """
        BFS查找指定节点max_depth层内的所有邻居
        返回: {"nodes": [...], "edges": [...]}
        """
        # 查找节点ID
        node = self.store.get_node_by_name(node_name)
        if not node:
            return {"nodes": [], "edges": []}

        node_id = node["id"]

        if node_id not in self.graph:
            return {"nodes": [], "edges": []}

        # BFS遍历
        visited_nodes = {node_id}
        visited_edges = set()
        current_level = {node_id}

        for _ in range(max_depth):
            next_level = set()
            for n in current_level:
                for neighbor in self.graph.neighbors(n):
                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        next_level.add(neighbor)

                    # 记录边
                    edge_key = tuple(sorted([n, neighbor]))
                    visited_edges.add(edge_key)

            current_level = next_level

        # 构建结果
        nodes = []
        for nid in visited_nodes:
            node_data = self.store.get_node(nid)
            if node_data:
                nodes.append(node_data)

        edges = []
        for src, tgt in visited_edges:
            edge_data = self.graph.get_edge_data(src, tgt)
            if edge_data:
                edges.append({
                    "source": src,
                    "target": tgt,
                    "edge_type": edge_data.get("edge_type"),
                    "strength": edge_data.get("strength")
                })

        return {"nodes": nodes, "edges": edges}

    def find_by_tag(self, tag_name: str, tag_value: Optional[str] = None) -> List[str]:
        """在图节点中按标签搜索，返回匹配的节点名列表"""
        nodes = self.store.get_nodes_by_tag(tag_name, tag_value)
        return [node["name"] for node in nodes]

    def find_path(self, source_name: str, target_name: str) -> Optional[List[str]]:
        """
        查找两个节点之间的最短路径
        返回节点名列表，不存在路径则返回None
        """
        source = self.store.get_node_by_name(source_name)
        target = self.store.get_node_by_name(target_name)

        if not source or not target:
            return None

        source_id = source["id"]
        target_id = target["id"]

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

    def get_node_centrality(self) -> Dict[int, float]:
        """计算所有节点的度中心性"""
        if len(self.graph) == 0:
            return {}
        return nx.degree_centrality(self.graph)

    def get_hub_nodes(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """获取枢纽节点（按中心性排序）"""
        centrality = self.get_node_centrality()

        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)

        results = []
        for node_id, cent in sorted_nodes[:top_k]:
            node_data = self.graph.nodes[node_id]
            results.append({
                "id": node_id,
                "name": node_data.get("name"),
                "node_type": node_data.get("node_type"),
                "centrality": cent
            })

        return results

    def get_communities(self) -> Dict[int, int]:
        """
        社区发现（使用Louvain算法）
        返回: {node_id: community_id}
        """
        if len(self.graph) == 0:
            return {}

        try:
            import community as community_louvain
            return community_louvain.best_partition(self.graph)
        except ImportError:
            # 如果没有安装python-louvain，返回简单划分
            return {node: 0 for node in self.graph.nodes()}
