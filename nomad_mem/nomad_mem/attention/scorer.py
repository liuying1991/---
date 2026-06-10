"""
AttentionScorer - 注意力评分模块
计算信息片段的重要性分数
"""
import networkx as nx
from typing import Dict, Any, List
from collections import Counter
import math


class AttentionScorer:
    """注意力评分器"""

    def __init__(self, config: Dict[str, Any], store):
        """
        从config['attention']读取各权重
        """
        self.config = config
        self.store = store
        attention_config = config.get("attention", {})

        self.novelty_weight = attention_config.get("novelty_weight", 0.3)
        self.pattern_weight = attention_config.get("pattern_weight", 0.3)
        self.emotion_weight = attention_config.get("emotion_weight", 0.2)
        self.association_weight = attention_config.get("association_weight", 0.2)

        # TF-IDF相关
        self.doc_freq = Counter()
        self.doc_count = 0

    def score(self, text: str, memory_graph: nx.Graph, emotion_score: float = 0.0) -> float:
        """
        综合四个因子计算注意力分数（0-1）：
        - novelty: 和已有节点的TF-IDF余弦距离
        - pattern: 文本中高频词的TF-IDF均值
        - emotion: 直接使用传入的emotion_score
        - association: 文本中已有节点在图中的平均度中心性
        """
        # 1. 计算新颖度
        novelty = self._compute_novelty(text)

        # 2. 计算模式分数
        pattern = self._compute_pattern(text)

        # 3. 情感分数直接使用
        emotion = emotion_score

        # 4. 计算关联分数
        association = self._compute_association(text, memory_graph)

        # 加权求和
        total_score = (
            self.novelty_weight * novelty +
            self.pattern_weight * pattern +
            self.emotion_weight * emotion +
            self.association_weight * association
        )

        return max(0.0, min(1.0, total_score))

    def _compute_novelty(self, text: str) -> float:
        """
        计算新颖度：与已有内容的差异度
        使用词汇重叠度来估计
        """
        # 分词
        words = self._tokenize(text)
        if not words:
            return 0.5

        # 获取所有已有节点的内容
        all_nodes = self.store.get_all_nodes()
        if not all_nodes:
            return 1.0  # 没有已有内容，完全新颖

        # 计算与已有内容的重叠度
        existing_words = set()
        for node in all_nodes:
            existing_words.update(self._tokenize(node.get("content", "")))

        new_words = set(words)
        overlap = len(new_words & existing_words)
        total = len(new_words)

        if total == 0:
            return 0.5

        # 新颖度 = 1 - 重叠率
        novelty = 1.0 - (overlap / total)
        return novelty

    def _compute_pattern(self, text: str) -> float:
        """
        计算模式分数：文本中高频词的TF均值
        """
        words = self._tokenize(text)
        if not words:
            return 0.0

        # 计算词频
        word_counts = Counter(words)
        total_words = len(words)

        # 取高频词（出现次数>=2）
        high_freq_words = {w: c for w, c in word_counts.items() if c >= 2}

        if not high_freq_words:
            return 0.0

        # 计算TF均值
        tf_values = [c / total_words for c in high_freq_words.values()]
        avg_tf = sum(tf_values) / len(tf_values)

        return min(1.0, avg_tf * 5)  # 放大并限制到0-1

    def _compute_association(self, text: str, memory_graph: nx.Graph) -> float:
        """
        计算关联分数：文本中已有节点在图中的平均度中心性
        """
        words = self._tokenize(text)
        if not words or len(memory_graph) == 0:
            return 0.0

        # 查找文本中出现的节点
        matched_nodes = []
        for word in words:
            node = self.store.get_node_by_name(word)
            if node and node["id"] in memory_graph:
                matched_nodes.append(node["id"])

        if not matched_nodes:
            return 0.0

        # 计算平均度中心性
        degrees = [memory_graph.degree(n) for n in matched_nodes]
        avg_degree = sum(degrees) / len(degrees)

        # 归一化
        max_degree = max(dict(memory_graph.degree()).values()) if memory_graph.number_of_nodes() > 0 else 1

        if max_degree == 0:
            return 0.0

        return avg_degree / max_degree

    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        try:
            import jieba
            words = jieba.lcut(text)
            return [w for w in words if len(w) >= 2]
        except ImportError:
            # 简单分词
            words = text.replace("，", " ").replace("。", " ").replace("、", " ").split()
            return [w for w in words if len(w) >= 2]

    def update_doc_stats(self, text: str):
        """更新文档统计（用于TF-IDF）"""
        words = set(self._tokenize(text))
        for word in words:
            self.doc_freq[word] += 1
        self.doc_count += 1
