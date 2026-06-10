"""
EmotionSystem - 情绪系统
杏仁核调制、情绪门控、情感衰减
"""
import math
from typing import Dict, Any, List


class EmotionSystem:
    """情绪系统"""

    # 基本情绪维度
    EMOTIONS = ["joy", "sadness", "fear", "anger", "surprise", "disgust", "love"]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bio_config = config.get("bio", {})
        self.emotion_config = self.bio_config.get("emotion", {})

        self.base_arousal = self.emotion_config.get("base_arousal", 0.5)
        self.max_intensity = self.emotion_config.get("max_intensity", 1.0)
        self.decay_rate = self.emotion_config.get("decay_rate", 0.01)

        # 情绪向量 [joy, sadness, fear, anger, surprise, disgust, love]
        self.emotion_state = [0.0] * len(self.EMOTIONS)

        # 唤醒度
        self.arousal = self.base_arousal

    def trigger_emotion(self, emotion_type: str, intensity: float):
        """触发情绪"""
        if emotion_type in self.EMOTIONS:
            idx = self.EMOTIONS.index(emotion_type)
            self.emotion_state[idx] = min(self.max_intensity,
                                          self.emotion_state[idx] + intensity)

    def update(self, dt: float = 0.1, perception_system=None):
        """更新情绪状态（衰减）"""
        decay = self.decay_rate * dt * 10
        for i in range(len(self.emotion_state)):
            self.emotion_state[i] = max(0.0,
                                        self.emotion_state[i] - decay)

        # 唤醒度 = 情绪强度总和
        self.arousal = sum(self.emotion_state) / len(self.emotion_state)

    def get_emotion_state(self) -> Dict[str, Any]:
        """获取情绪状态字典"""
        state = {}
        for i, emotion in enumerate(self.EMOTIONS):
            state[emotion] = self.emotion_state[i]
        state["arousal"] = self.arousal
        state["valence"] = (
            self.emotion_state[0]  # joy
            - self.emotion_state[1]  # sadness
            - self.emotion_state[3]  # anger
        )
        return state

    def get_current_emotion_score(self) -> float:
        """获取当前情绪分数 (0-1)"""
        return self.arousal

    def get_emotion_score(self) -> float:
        """获取综合情绪分数（0-1）"""
        return self.arousal

    def get_dominant_emotion(self) -> str:
        """获取主导情绪"""
        max_idx = self.emotion_state.index(max(self.emotion_state))
        return self.EMOTIONS[max_idx]

    def get_emotion_vector(self) -> List[float]:
        """获取情绪向量"""
        return list(self.emotion_state)

    def emotion_gate_learning_rate(self, base_lr: float) -> float:
        """
        情绪门控学习率
        learning_rate = base_lr * (1 + emotion_score * emotion_multiplier)
        """
        emotion_multiplier = self.config.get("consciousness", {}).get("memory", {}).get("emotion_multiplier", 2.0)
        return base_lr * (1 + self.arousal * emotion_multiplier)

    def describe_emotion(self) -> str:
        """描述当前情绪状态"""
        dominant = self.get_dominant_emotion()
        intensity = max(self.emotion_state)

        if intensity < 0.1:
            return "平静"
        elif intensity < 0.3:
            return f"轻微{dominant}"
        elif intensity < 0.6:
            return f"{dominant}"
        else:
            return f"强烈{dominant}"
