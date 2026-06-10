"""
MultimodalEncoder - 多模态编码器
从原始输入到向量嵌入空间
"""
import hashlib
import numpy as np
from typing import Dict, Any, Optional, Tuple


class MultimodalEncoder:
    """多模态编码器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.encoder_config = config.get("encoder", {})
        self.embedding_dim = self.encoder_config.get("embedding_dim", 384)
        self.text_model = self.encoder_config.get("text_model", "all-MiniLM-L6-v2")

        self.text_model_instance = None
        self.whisper_model_instance = None

    def _load_text_model(self):
        """延迟加载文本编码器"""
        if self.text_model_instance is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.text_model_instance = SentenceTransformer(self.text_model)
                self.embedding_dim = self.text_model_instance.get_sentence_embedding_dimension()
            except (ImportError, Exception) as e:
                print(f"[WARNING] sentence-transformers加载失败({e})，使用模拟编码器")
                self.text_model_instance = "mock"

    def _load_whisper_model(self):
        """延迟加载Whisper模型"""
        if self.whisper_model_instance is None:
            try:
                import whisper
                whisper_config = self.config.get("whisper", {})
                model_size = whisper_config.get("model_size", "base")
                self.whisper_model_instance = whisper.load_model(model_size)
            except ImportError:
                print("[WARNING] Whisper未安装，使用模拟编码器")
                self.whisper_model_instance = "mock"

    def encode_text(self, text: str) -> np.ndarray:
        """
        编码文本为向量
        返回: 384维numpy数组（all-MiniLM-L6-v2）
        """
        self._load_text_model()

        if self.text_model_instance == "mock":
            # 模拟编码：使用哈希生成伪向量
            return self._mock_encode(text, self.embedding_dim)

        # 使用SentenceTransformer编码
        embedding = self.text_model_instance.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)

    def encode_audio(self, audio_path: str) -> Tuple[np.ndarray, str, float]:
        """
        编码音频为向量
        返回: (向量, 转写文本, 情绪分数)
        """
        self._load_whisper_model()

        if self.whisper_model_instance == "mock":
            text = "这是一个模拟的音频转写结果"
            return self._mock_encode(text, self.embedding_dim), text, 0.5

        # Whisper转写
        result = self.whisper_model_instance.transcribe(audio_path)
        text = result.get("text", "")

        # 编码转写文本
        embedding = self.encode_text(text)

        # 计算情绪分数
        from .emotion_detector import EmotionDetector
        emotion_score = EmotionDetector.compute_emotion(text)

        return embedding, text, emotion_score

    def encode_image(self, image_path: str) -> np.ndarray:
        """编码图像为向量"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

            from PIL import Image
            image = Image.open(image_path)
            inputs = clip_processor(images=image, return_tensors="pt")
            embedding = clip_model.get_image_features(**inputs)

            return embedding.detach().numpy().flatten().astype(np.float32)
        except ImportError:
            return self._mock_encode(image_path, self.embedding_dim)

    def compute_content_hash(self, content: str) -> str:
        """计算内容哈希（用于去重）"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _mock_encode(self, content: str, dim: int) -> np.ndarray:
        """模拟编码器"""
        hash_bytes = hashlib.sha256(content.encode()).digest()
        vec = np.zeros(dim, dtype=np.float32)
        for i in range(dim):
            vec[i] = (hash_bytes[i % 32] / 255.0 - 0.5) * 2
        # 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec
