"""
EmotionDetector - 情绪检测器
多模态情绪识别
"""
from typing import Dict, Any
import re


class EmotionDetector:
    """情绪检测器"""

    # 情绪关键词
    EMOTION_KEYWORDS = {
        'positive': ['开心', '高兴', '快乐', '喜欢', '爱', '好', '棒', '优秀', '成功', '幸福', '满足', '兴奋'],
        'negative': ['难过', '悲伤', '痛苦', '讨厌', '恨', '坏', '差', '失败', '恐惧', '害怕', '愤怒', '生气'],
        'high_arousal': ['激动', '疯狂', '爆发', '爆炸', '大声', '尖叫', '奔跑', '冲'],
        'low_arousal': ['平静', '安静', '安静', '慢慢', '轻声', '沉睡', '休息'],
    }

    @classmethod
    def compute_emotion(cls, text: str) -> float:
        """
        计算文本情绪分数
        返回: 0-1之间的情绪强度（越高越积极/强烈）
        """
        text = text.lower()

        positive_count = sum(1 for w in cls.EMOTION_KEYWORDS['positive'] if w in text)
        negative_count = sum(1 for w in cls.EMOTION_KEYWORDS['negative'] if w in text)
        high_arousal_count = sum(1 for w in cls.EMOTION_KEYWORDS['high_arousal'] if w in text)
        low_arousal_count = sum(1 for w in cls.EMOTION_KEYWORDS['low_arousal'] if w in text)

        # 计算效价（正面-负面）
        valence = (positive_count - negative_count) / max(1, positive_count + negative_count)

        # 计算唤醒度（高唤醒-低唤醒）
        arousal = (high_arousal_count - low_arousal_count) / max(1, high_arousal_count + low_arousal_count)

        # 综合情绪强度
        intensity = (abs(valence) + abs(arousal)) / 2

        # 归一化到0-1
        score = 0.5 + intensity * valence

        return max(0.0, min(1.0, score))

    @classmethod
    def compute_audio_emotion(cls, audio_features: Dict[str, float]) -> float:
        """
        从音频特征计算情绪
        audio_features应包含:
        - rms_mean: 平均能量
        - rms_std: 能量变化
        - pitch_mean: 平均音高
        - pitch_std: 音高变化
        """
        # 高能量 + 高音高变化 = 高唤醒
        energy = audio_features.get("rms_mean", 0)
        pitch_var = audio_features.get("pitch_std", 0)

        arousal = min(1.0, energy * 2 + pitch_var * 0.5)

        # 简化：假设高唤醒=强情绪
        return arousal
