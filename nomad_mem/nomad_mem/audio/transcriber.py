"""
AudioTranscriber - 音频转写模块
使用Whisper进行语音识别
"""
import os
from typing import Dict, Any, List


class AudioTranscriber:
    """音频转写器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Whisper模型
        从config['whisper']['model_size']读取模型大小
        """
        self.config = config
        self.whisper_config = config.get("whisper", {})
        self.model_size = self.whisper_config.get("model_size", "base")
        self.language = self.whisper_config.get("language", "zh")
        self.model = None

    def _load_model(self):
        """延迟加载Whisper模型"""
        if self.model is None:
            try:
                import whisper
                self.model = whisper.load_model(self.model_size)
            except ImportError:
                print("[WARNING] Whisper未安装，使用模拟转写")
                self.model = "mock"

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        转写单个音频文件
        返回: {
            "text": "转写后的文本",
            "segments": [{"start": 0.0, "end": 2.5, "text": "..."}],
            "duration": 10.5,
            "emotion_score": 0.73
        }
        """
        self._load_model()

        if self.model == "mock":
            # 模拟模式
            return {
                "text": "这是一个模拟的转写结果。",
                "segments": [{"start": 0.0, "end": 2.0, "text": "这是一个模拟的转写结果。"}],
                "duration": 2.0,
                "emotion_score": 0.5
            }

        # 使用Whisper转写
        result = self.model.transcribe(audio_path, language=self.language)

        # 计算时长
        duration = 0.0
        if result.get("segments"):
            duration = result["segments"][-1].get("end", 0.0)

        # 计算情感分数（简单实现）
        emotion_score = self._estimate_emotion(result.get("text", ""))

        return {
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
            "duration": duration,
            "emotion_score": emotion_score
        }

    def extract_audio_features(self, audio_path: str) -> Dict[str, float]:
        """
        提取音频特征
        返回: {"duration": 10.5, "rms_mean": 0.03, "rms_std": 0.01}
        """
        try:
            import librosa
            y, sr = librosa.load(audio_path)

            duration = len(y) / sr
            rms = librosa.feature.rms(y=y)[0]

            return {
                "duration": duration,
                "rms_mean": float(rms.mean()),
                "rms_std": float(rms.std())
            }
        except ImportError:
            # 简单实现
            return {
                "duration": 0.0,
                "rms_mean": 0.0,
                "rms_std": 0.0
            }
        except Exception as e:
            print(f"[ERROR] 提取音频特征失败: {e}")
            return {
                "duration": 0.0,
                "rms_mean": 0.0,
                "rms_std": 0.0
            }

    def _estimate_emotion(self, text: str) -> float:
        """
        简单的情感估计
        返回0-1之间的分数
        """
        # 积极词汇
        positive_words = ["开心", "高兴", "快乐", "喜欢", "爱", "好", "棒", "优秀", "成功"]
        # 消极词汇
        negative_words = ["难过", "悲伤", "痛苦", "讨厌", "恨", "坏", "差", "失败", "恐惧"]

        text_lower = text.lower()

        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)

        if positive_count + negative_count == 0:
            return 0.5  # 中性

        # 计算情感分数
        score = 0.5 + 0.3 * (positive_count - negative_count) / (positive_count + negative_count)
        return max(0.0, min(1.0, score))
