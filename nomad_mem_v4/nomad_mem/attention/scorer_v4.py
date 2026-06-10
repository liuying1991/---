"""
AttentionScorerV4 - v4.0注意力评分
注意力 = 新颖性 × 情绪强度 × 关联潜力
"""
import numpy as np
from typing import Dict, Any, List


class AttentionScorerV4:
    """v4.0注意力评分器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.attention_config = config.get("attention", {})
        self.novelty_weight = self.attention_config.get("novelty_weight", 0.3)
        self.emotion_weight = self.attention_config.get("emotion_weight", 0.3)
        self.association_weight = self.attention_config.get("association_weight", 0.4)

    def score(self, embedding: np.ndarray, emotion: float,
              working_memory_embeddings: List[np.ndarray] = None,
              cortex_embeddings: List[np.ndarray] = None) -> float:
        """
        计算注意力分数
        注意力 = 新颖性 × 情绪强度 × 关联潜力
        """
        # 1. 新颖性：与工作记忆当前内容的余弦距离
        novelty = self._compute_novelty(embedding, working_memory_embeddings)

        # 2. 情绪强度：直接传入
        emotion_score = emotion

        # 3. 关联潜力：与皮层已有概念的相似度
        association = self._compute_association(embedding, cortex_embeddings)

        # 加权求和
        total_score = (
            self.novelty_weight * novelty +
            self.emotion_weight * emotion_score +
            self.association_weight * association
        )

        return max(0.0, min(1.0, total_score))

    def _compute_novelty(self, embedding: np.ndarray,
                        working_memory_embeddings: List[np.ndarray]) -> float:
        """
        计算新颖性：与工作记忆的余弦距离
        距离越大越新颖
        """
        if not working_memory_embeddings:
            return 1.0  # 没有工作记忆，完全新颖

        max_similarity = 0.0
        for wm_embedding in working_memory_embeddings:
            similarity = self._cosine_similarity(embedding, wm_embedding)
            max_similarity = max(max_similarity, similarity)

        # 新颖性 = 1 - 最大相似度
        return 1.0 - max_similarity

    def _compute_association(self, embedding: np.ndarray,
                           cortex_embeddings: List[np.ndarray]) -> float:
        """
        计算关联潜力：与皮层概念的平均相似度
        """
        if not cortex_embeddings:
            return 0.0  # 没有皮层概念，无关联潜力

        similarities = []
        for cortex_embedding in cortex_embeddings:
            similarity = self._cosine_similarity(embedding, cortex_embedding)
            similarities.append(similarity)

        # 返回平均相似度
        return sum(similarities) / len(similarities)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
