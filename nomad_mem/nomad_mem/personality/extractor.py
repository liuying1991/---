"""
PersonalityExtractor - 人格提取模块
从记忆网络中提取人格特征
"""
from typing import Dict, Any, List
from collections import Counter


class PersonalityExtractor:
    """人格提取器"""

    def __init__(self, store, graph):
        self.store = store
        self.graph = graph

    def extract(self) -> Dict[str, Any]:
        """
        提取人格特征
        返回: {
            "thinking_patterns": [...],
            "values": [...],
            "decision_style": "...",
            "language_style": "...",
            "hub_nodes": [...],
            "tag_statistics": {...},
            "edge_type_statistics": {...}
        }
        """
        # 1. 思维模式
        thinking_patterns = self._extract_thinking_patterns()

        # 2. 价值观
        values = self._extract_values()

        # 3. 决策风格
        decision_style = self._extract_decision_style()

        # 4. 语言风格
        language_style = self._extract_language_style()

        # 5. 枢纽节点
        hub_nodes = self.graph.get_hub_nodes(top_k=5)

        # 6. 标签统计
        tag_statistics = self._compute_tag_statistics()

        # 7. 关联类型统计
        edge_type_statistics = self._compute_edge_type_statistics()

        return {
            "thinking_patterns": thinking_patterns,
            "values": values,
            "decision_style": decision_style,
            "language_style": language_style,
            "hub_nodes": hub_nodes,
            "tag_statistics": tag_statistics,
            "edge_type_statistics": edge_type_statistics
        }

    def _extract_thinking_patterns(self) -> List[str]:
        """提取思维模式"""
        patterns = []

        # 分析概念节点
        nodes = self.store.get_all_nodes()
        concept_nodes = [n for n in nodes if n.get("node_type") == "concept"]

        # 基于概念类型推测思维模式
        concept_names = [n["name"] for n in concept_nodes]

        # 检测思维模式关键词
        if any("因果" in c or "逻辑" in c for c in concept_names):
            patterns.append("因果思维")
        if any("系统" in c or "整体" in c for c in concept_names):
            patterns.append("系统思维")
        if any("联想" in c or "关联" in c for c in concept_names):
            patterns.append("联想思维")
        if any("对比" in c or "比较" in c for c in concept_names):
            patterns.append("对比思维")
        if any("第一性" in c or "本质" in c for c in concept_names):
            patterns.append("本质思维")

        # 默认模式
        if not patterns:
            patterns.append("综合思维")

        return patterns

    def _extract_values(self) -> List[str]:
        """提取价值观"""
        values = []

        # 分析标签中的价值观线索
        nodes = self.store.get_all_nodes()
        all_tags = {}
        for node in nodes:
            all_tags.update(node.get("tags", {}))

        # 基于标签推测价值观
        if "效率" in str(all_tags) or "快速" in str(all_tags):
            values.append("效率优先")
        if "创新" in str(all_tags) or "新" in str(all_tags):
            values.append("创新导向")
        if "稳定" in str(all_tags) or "安全" in str(all_tags):
            values.append("稳健优先")
        if "质量" in str(all_tags) or "优秀" in str(all_tags):
            values.append("追求卓越")

        # 默认价值观
        if not values:
            values.append("实用主义")

        return values

    def _extract_decision_style(self) -> str:
        """提取决策风格"""
        # 分析边类型分布
        edges = self.store.get_all_edges()
        edge_types = [e["edge_type"] for e in edges]
        type_counts = Counter(edge_types)

        # 基于关联类型推测决策风格
        if type_counts.get("因果", 0) > 3:
            return "因果分析型决策"
        elif type_counts.get("对比", 0) > 3:
            return "对比评估型决策"
        elif type_counts.get("直觉", 0) > 3:
            return "直觉型决策"
        else:
            return "综合型决策"

    def _extract_language_style(self) -> str:
        """提取语言风格"""
        # 分析节点内容
        nodes = self.store.get_all_nodes()
        all_content = " ".join([n.get("content", "") for n in nodes])

        if not all_content:
            return "简洁"

        # 简单的语言风格分析
        avg_sentence_length = len(all_content) / max(1, all_content.count("。") + all_content.count("，") + 1)

        if avg_sentence_length > 50:
            return "详细、解释性强"
        elif avg_sentence_length > 30:
            return "中等、平衡"
        else:
            return "简洁、直接"

    def _compute_tag_statistics(self) -> Dict[str, Any]:
        """计算标签统计"""
        nodes = self.store.get_all_nodes()

        # 统计所有标签
        tag_counts = Counter()
        tag_value_counts = Counter()

        for node in nodes:
            tags = node.get("tags", {})
            for tag_name, tag_value in tags.items():
                tag_counts[tag_name] += 1
                tag_value_counts[f"{tag_name}={tag_value}"] += 1

        # 最常用标签
        top_tags = tag_counts.most_common(5)

        return {
            "总标签种类数": len(tag_counts),
            "最常用标签Top5": [
                {"name": name, "count": count}
                for name, count in top_tags
            ]
        }

    def _compute_edge_type_statistics(self) -> Dict[str, Any]:
        """计算关联类型统计"""
        edges = self.store.get_all_edges()

        # 统计关联类型
        type_counts = Counter([e["edge_type"] for e in edges])

        # 最常用关联
        top_types = type_counts.most_common(5)

        return {
            "总关联类型数": len(type_counts),
            "最常用关联Top5": [
                {"type": t, "count": count}
                for t, count in top_types
            ]
        }
