"""
PatternDiscovery - 模式发现模块
发现节点间的隐藏关联和社区结构
"""
from typing import Dict, Any, List
from collections import Counter


class PatternDiscovery:
    """模式发现器"""

    def __init__(self, store, graph, config: Dict[str, Any]):
        self.store = store
        self.graph = graph
        self.config = config
        self.discovery_config = config.get("discovery", {})

    def run(self) -> Dict[str, Any]:
        """
        运行模式发现
        返回: {
            "hub_nodes": [...],
            "clusters": {...},
            "communities": {...},
            "new_edge_suggestions": [...]
        }
        """
        # 1. 发现枢纽节点
        hub_nodes = self._find_hub_nodes()

        # 2. 发现聚类
        clusters = self._find_clusters()

        # 3. 社区发现
        communities = self._find_communities()

        # 4. 建议新关联
        new_edge_suggestions = self._suggest_new_edges(communities)

        return {
            "hub_nodes": hub_nodes,
            "clusters": clusters,
            "communities": communities,
            "new_edge_suggestions": new_edge_suggestions
        }

    def _find_hub_nodes(self) -> List[Dict[str, Any]]:
        """发现枢纽节点（高中心性节点）"""
        return self.graph.get_hub_nodes(top_k=10)

    def _find_clusters(self) -> Dict[str, List[str]]:
        """
        发现聚类
        基于节点类型和标签进行简单聚类
        """
        nodes = self.store.get_all_nodes()

        # 按类型聚类
        type_clusters = {}
        for node in nodes:
            node_type = node.get("node_type", "general")
            if node_type not in type_clusters:
                type_clusters[node_type] = []
            type_clusters[node_type].append(node["name"])

        # 按标签聚类
        tag_clusters = {}
        for node in nodes:
            tags = node.get("tags", {})
            for tag_name, tag_value in tags.items():
                cluster_key = f"tag:{tag_name}={tag_value}"
                if cluster_key not in tag_clusters:
                    tag_clusters[cluster_key] = []
                tag_clusters[cluster_key].append(node["name"])

        # 合并
        clusters = {}
        clusters.update(type_clusters)
        clusters.update(tag_clusters)

        return clusters

    def _find_communities(self) -> Dict[str, int]:
        """社区发现"""
        communities = self.graph.get_communities()

        # 转换为节点名 -> 社区ID
        result = {}
        for node_id, community_id in communities.items():
            node = self.store.get_node(node_id)
            if node:
                result[node["name"]] = community_id

        return result

    def _suggest_new_edges(self, communities: Dict[str, int]) -> List[Dict[str, str]]:
        """
        建议新关联
        基于社区发现：同一社区但无直接边的节点
        """
        suggestions = []

        # 按社区分组
        community_nodes = {}
        for node_name, community_id in communities.items():
            if community_id not in community_nodes:
                community_nodes[community_id] = []
            community_nodes[community_id].append(node_name)

        # 检查每个社区
        for community_id, nodes in community_nodes.items():
            if len(nodes) < 2:
                continue

            # 检查节点对是否有直接边
            for i, node_a in enumerate(nodes):
                for node_b in nodes[i+1:]:
                    # 检查是否已有边
                    node_a_data = self.store.get_node_by_name(node_a)
                    node_b_data = self.store.get_node_by_name(node_b)

                    if not node_a_data or not node_b_data:
                        continue

                    # 获取连接的节点
                    connected = self.store.get_connected_nodes(node_a_data["id"])

                    # 如果没有直接连接，建议建立关联
                    connected_ids = {n["id"] for n in connected}
                    if node_b_data["id"] not in connected_ids:
                        # 推测关联类型
                        suggested_type = self._infer_edge_type(node_a_data, node_b_data)
                        suggestions.append({
                            "source": node_a,
                            "target": node_b,
                            "suggested_type": suggested_type
                        })

        # 限制建议数量
        return suggestions[:20]

    def _infer_edge_type(self, node_a: Dict, node_b: Dict) -> str:
        """推测关联类型"""
        type_a = node_a.get("node_type", "")
        type_b = node_b.get("node_type", "")

        # 基于节点类型推测
        if type_a == "person" and type_b == "person":
            return "可能认识"
        elif type_a == "person" and type_b == "object":
            return "可能拥有"
        elif type_a == "person" and type_b == "spatial":
            return "可能位于"
        elif type_a == "concept" and type_b == "concept":
            return "概念关联"
        elif type_a == "sensory_audio" or type_b == "sensory_audio":
            return "提到"
        else:
            return "潜在关联"

    def _find_color_matches(self) -> List[Dict[str, str]]:
        """发现颜色匹配的物体"""
        suggestions = []

        nodes = self.store.get_all_nodes()
        color_groups = {}

        for node in nodes:
            tags = node.get("tags", {})
            color = tags.get("涉及颜色") or tags.get("衣服颜色")
            if color:
                if color not in color_groups:
                    color_groups[color] = []
                color_groups[color].append(node["name"])

        for color, nodes in color_groups.items():
            if len(nodes) >= 2:
                for i, node_a in enumerate(nodes):
                    for node_b in nodes[i+1:]:
                        suggestions.append({
                            "source": node_a,
                            "target": node_b,
                            "suggested_type": "颜色相同"
                        })

        return suggestions
