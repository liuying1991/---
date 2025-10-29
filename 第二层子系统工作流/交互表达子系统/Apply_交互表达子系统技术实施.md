# Apply_交互表达子系统技术实施

## 1. 阶段概述

Apply阶段是交互表达子系统开发的实施阶段，将架构设计转化为具体的技术实现。本阶段基于Analyze阶段的架构设计，详细实现多模态交互处理、情感表达与理解、个性化交互适配和上下文感知交互等核心功能模块，构建一个高效、可扩展、安全的交互表达子系统。

本阶段的主要任务包括：
- 技术实施环境搭建
- 多模态处理模块实现
- 情感处理模块实现
- 个性化模块实现
- 上下文管理模块实现
- 模块集成与测试
- 性能优化与安全加固

## 2. 技术实施环境

### 2.1 开发环境

#### 2.1.1 硬件环境

##### 2.1.1.1 服务器配置
- **CPU**：Intel Xeon Gold 6248R，24核心48线程，基础频率3.0GHz
- **内存**：256GB DDR4 ECC内存，支持内存纠错
- **存储**：2TB NVMe SSD + 10TB SATA HDD，满足高速存储和大容量需求
- **GPU**：4×NVIDIA A100 40GB，支持多GPU并行计算
- **网络**：万兆以太网，低延迟高带宽网络连接

##### 2.1.1.2 开发设备
- **开发主机**：高性能工作站，32GB内存，RTX 3080 GPU
- **测试设备**：多种终端设备，包括PC、平板、手机、智能音箱等
- **网络设备**：千兆交换机，支持多设备同时连接测试

#### 2.1.2 软件环境

##### 2.1.2.1 操作系统
- **服务器系统**：Ubuntu 20.04 LTS，稳定可靠的Linux发行版
- **开发系统**：Windows 11 + WSL2，兼容主流开发工具
- **容器系统**：Docker 20.10+，Kubernetes 1.21+，支持容器化部署

##### 2.1.2.2 开发工具
- **IDE**：PyCharm Professional 2023.1，支持Python全栈开发
- **版本控制**：Git 2.34+，GitLab CE，支持代码版本管理
- **CI/CD**：Jenkins 2.332+，GitLab CI，支持自动化构建部署
- **监控工具**：Prometheus + Grafana，支持系统监控和可视化

##### 2.1.2.3 运行环境
- **Python**：Python 3.9，稳定且广泛支持的Python版本
- **Java**：OpenJDK 11，长期支持版本
- **Node.js**：Node.js 16 LTS，长期支持版本
- **数据库**：PostgreSQL 13，Redis 6.2，Elasticsearch 7.15

### 2.2 依赖库

#### 2.2.1 核心框架

##### 2.2.1.1 深度学习框架
- **PyTorch**：1.11.0，支持动态图和分布式训练
- **TensorFlow**：2.8.0，支持生产环境部署和优化
- **Transformers**：4.17.0，Hugging Face预训练模型库
- **LangChain**：0.0.100，支持大语言模型应用开发

##### 2.2.1.2 Web框架
- **FastAPI**：0.75.2，高性能异步Web框架
- **Django**：4.0.3，全功能Web框架
- **Flask**：2.1.1，轻量级Web框架
- **Sanic**：22.3.0，异步Web框架

##### 2.2.1.3 微服务框架
- **gRPC**：1.45.0，高性能RPC框架
- **Nameko**：2.8.0，Python微服务框架
- **Istio**：1.12.0，服务网格框架
- **Consul**：1.11.0，服务发现和配置管理

#### 2.2.2 数据处理库

##### 2.2.2.1 数据处理
- **NumPy**：1.22.3，科学计算基础库
- **Pandas**：1.4.2，数据分析和处理库
- **SciPy**：1.8.0，科学计算库
- **Scikit-learn**：1.0.2，机器学习库

##### 2.2.2.2 图像处理
- **OpenCV**：4.5.5，计算机视觉库
- **Pillow**：9.1.0，图像处理库
- **Albumentations**：1.1.0，图像增强库
- **timm**：0.6.7，图像模型库

##### 2.2.2.3 音频处理
- **Librosa**：0.9.1，音频分析库
- **SoundFile**：0.10.3，音频文件读写
- **pydub**：0.25.1，音频处理库
- **torchaudio**：0.11.0，PyTorch音频处理

##### 2.2.2.4 文本处理
- **NLTK**：3.7，自然语言处理库
- **spaCy**：3.2.4，工业级NLP库
- **jieba**：0.42.1，中文分词库
- **textblob**：0.17.1，文本处理库

#### 2.2.3 系统工具库

##### 2.2.3.1 异步处理
- **asyncio**：Python内置异步库
- **aiohttp**：3.8.1，异步HTTP客户端/服务器
- **celery**：5.2.2，分布式任务队列
- **RQ**：1.10.0，简单任务队列

##### 2.2.3.2 数据库连接
- **SQLAlchemy**：1.4.35，SQL工具包和ORM
- **psycopg2**：2.9.3，PostgreSQL适配器
- **redis-py**：4.1.4，Redis客户端
- **elasticsearch-py**：8.1.0，Elasticsearch客户端

##### 2.2.3.3 监控和日志
- **loguru**：0.6.0，日志库
- **prometheus-client**：0.13.1，Prometheus客户端
- **jaeger-client**：4.8.0，分布式追踪
- **opencensus**：0.11.2，遥测库

## 3. 多模态处理模块实现

### 3.1 模块结构

多模态处理模块负责处理来自不同模态的输入数据，包括文本、图像、音频和视频等，并进行模态内处理、跨模态对齐和融合，为后续的情感处理、个性化和上下文管理提供统一的多模态表示。

```
multimodal_processing/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py          # 模块配置
│   └── model_configs.py     # 模型配置
├── core/
│   ├── __init__.py
│   ├── base_processor.py    # 基础处理器
│   ├── modality_processor.py # 模态处理器
│   └── fusion_processor.py  # 融合处理器
├── processors/
│   ├── __init__.py
│   ├── text_processor.py    # 文本处理器
│   ├── image_processor.py   # 图像处理器
│   ├── audio_processor.py   # 音频处理器
│   └── video_processor.py   # 视频处理器
├── fusion/
│   ├── __init__.py
│   ├── alignment.py         # 特征对齐
│   ├── attention.py         # 跨模态注意力
│   └── fusion.py            # 特征融合
├── models/
│   ├── __init__.py
│   ├── text_encoder.py      # 文本编码器
│   ├── image_encoder.py     # 图像编码器
│   ├── audio_encoder.py     # 音频编码器
│   └── multimodal_model.py   # 多模态模型
├── utils/
│   ├── __init__.py
│   ├── data_loader.py       # 数据加载器
│   ├── transforms.py        # 数据变换
│   └── metrics.py           # 评估指标
└── api/
    ├── __init__.py
    ├── routes.py            # API路由
    └── schemas.py           # 数据模式
```

### 3.2 基础处理器实现

#### 3.2.1 基础处理器类

```python
# core/base_processor.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from loguru import logger


class BaseProcessor(ABC):
    """基础处理器抽象类，定义处理器的基本接口和通用功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化基础处理器
        
        Args:
            config: 处理器配置字典
        """
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.preprocessor = None
        self.postprocessor = None
        
        logger.info(f"Initialized {self.__class__.__name__} with config: {config}")
    
    @abstractmethod
    def load_model(self) -> None:
        """加载模型"""
        pass
    
    @abstractmethod
    def preprocess(self, data: Any) -> Any:
        """预处理数据"""
        pass
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    def postprocess(self, data: Any) -> Any:
        """后处理数据"""
        pass
    
    def forward(self, data: Any) -> Any:
        """
        前向传播，整合预处理、处理和后处理
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        try:
            # 预处理
            preprocessed_data = self.preprocess(data)
            
            # 处理
            processed_data = self.process(preprocessed_data)
            
            # 后处理
            result = self.postprocess(processed_data)
            
            return result
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.forward: {str(e)}")
            raise
    
    def to(self, device: torch.device) -> "BaseProcessor":
        """
        将处理器移动到指定设备
        
        Args:
            device: 目标设备
            
        Returns:
            处理器实例
        """
        self.device = device
        if self.model is not None:
            self.model = self.model.to(device)
        return self
    
    def eval(self) -> "BaseProcessor":
        """
        设置为评估模式
        
        Returns:
            处理器实例
        """
        if self.model is not None:
            self.model = self.model.eval()
        return self
    
    def train(self) -> "BaseProcessor":
        """
        设置为训练模式
        
        Returns:
            处理器实例
        """
        if self.model is not None:
            self.model = self.model.train()
        return self
    
    def save_checkpoint(self, path: str) -> None:
        """
        保存检查点
        
        Args:
            path: 保存路径
        """
        if self.model is not None:
            checkpoint = {
                "model_state_dict": self.model.state_dict(),
                "config": self.config
            }
            torch.save(checkpoint, path)
            logger.info(f"Saved checkpoint to {path}")
    
    def load_checkpoint(self, path: str) -> None:
        """
        加载检查点
        
        Args:
            path: 检查点路径
        """
        checkpoint = torch.load(path, map_location=self.device)
        if self.model is not None:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        logger.info(f"Loaded checkpoint from {path}")
```

#### 3.2.2 模态处理器类

```python
# core/modality_processor.py

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from .base_processor import BaseProcessor
from loguru import logger


class ModalityProcessor(BaseProcessor):
    """模态处理器基类，处理单一模态的数据"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模态处理器
        
        Args:
            config: 处理器配置字典
        """
        super().__init__(config)
        self.modality_type = config.get("modality_type", "unknown")
        self.feature_dim = config.get("feature_dim", 512)
        
        logger.info(f"Initialized {self.__class__.__name__} for modality: {self.modality_type}")
    
    @abstractmethod
    def extract_features(self, data: Any) -> torch.Tensor:
        """
        提取特征
        
        Args:
            data: 输入数据
            
        Returns:
            特征张量
        """
        pass
    
    @abstractmethod
    def encode(self, data: Any) -> torch.Tensor:
        """
        编码数据为特征表示
        
        Args:
            data: 输入数据
            
        Returns:
            编码后的特征张量
        """
        pass
    
    def process(self, data: Any) -> torch.Tensor:
        """
        处理数据，返回特征表示
        
        Args:
            data: 输入数据
            
        Returns:
            特征张量
        """
        return self.encode(data)
    
    def get_feature_dim(self) -> int:
        """
        获取特征维度
        
        Returns:
            特征维度
        """
        return self.feature_dim
    
    def get_modality_type(self) -> str:
        """
        获取模态类型
        
        Returns:
            模态类型
        """
        return self.modality_type


class TextProcessor(ModalityProcessor):
    """文本处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文本处理器
        
        Args:
            config: 处理器配置字典
        """
        config["modality_type"] = "text"
        super().__init__(config)
        self.max_length = config.get("max_length", 512)
        self.vocab_size = config.get("vocab_size", 30522)
        
    def load_model(self) -> None:
        """加载文本模型"""
        from transformers import AutoTokenizer, AutoModel
        
        model_name = self.config.get("model_name", "bert-base-uncased")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
        # 调整特征维度
        if self.feature_dim != self.model.config.hidden_size:
            self.projection = nn.Linear(self.model.config.hidden_size, self.feature_dim)
        else:
            self.projection = nn.Identity()
            
        self.model.to(self.device)
        logger.info(f"Loaded text model: {model_name}")
    
    def preprocess(self, data: Union[str, List[str]]) -> Dict[str, torch.Tensor]:
        """
        预处理文本数据
        
        Args:
            data: 输入文本或文本列表
            
        Returns:
            预处理后的数据
        """
        if isinstance(data, str):
            data = [data]
            
        inputs = self.tokenizer(
            data,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        return {k: v.to(self.device) for k, v in inputs.items()}
    
    def extract_features(self, data: Union[str, List[str]]) -> torch.Tensor:
        """
        提取文本特征
        
        Args:
            data: 输入文本或文本列表
            
        Returns:
            文本特征张量
        """
        inputs = self.preprocess(data)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # 使用[CLS]标记的表示作为句子表示
            features = outputs.last_hidden_state[:, 0, :]
            features = self.projection(features)
            
        return features
    
    def encode(self, data: Union[str, List[str]]) -> torch.Tensor:
        """
        编码文本为特征表示
        
        Args:
            data: 输入文本或文本列表
            
        Returns:
            编码后的特征张量
        """
        return self.extract_features(data)
    
    def postprocess(self, data: torch.Tensor) -> torch.Tensor:
        """
        后处理特征
        
        Args:
            data: 特征张量
            
        Returns:
            后处理后的特征张量
        """
        # 归一化特征
        features = torch.nn.functional.normalize(data, p=2, dim=1)
        return features


class ImageProcessor(ModalityProcessor):
    """图像处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化图像处理器
        
        Args:
            config: 处理器配置字典
        """
        config["modality_type"] = "image"
        super().__init__(config)
        self.image_size = config.get("image_size", 224)
        
    def load_model(self) -> None:
        """加载图像模型"""
        import torchvision.models as models
        import torchvision.transforms as transforms
        
        model_name = self.config.get("model_name", "resnet50")
        
        if model_name == "resnet50":
            self.model = models.resnet50(pretrained=True)
            self.model.fc = nn.Identity()  # 移除最后的全连接层
            input_dim = 2048
        elif model_name == "efficientnet_b0":
            self.model = models.efficientnet_b0(pretrained=True)
            self.model.classifier = nn.Identity()  # 移除最后的分类层
            input_dim = 1280
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        
        # 调整特征维度
        if self.feature_dim != input_dim:
            self.projection = nn.Linear(input_dim, self.feature_dim)
        else:
            self.projection = nn.Identity()
            
        # 定义图像变换
        self.transform = transforms.Compose([
            transforms.Resize((self.image_size, self.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
            
        self.model.to(self.device)
        logger.info(f"Loaded image model: {model_name}")
    
    def preprocess(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        预处理图像数据
        
        Args:
            data: 输入图像或图像列表
            
        Returns:
            预处理后的图像张量
        """
        from PIL import Image
        import io
        
        if isinstance(data, (bytes, bytearray)):
            # 字节数据转PIL图像
            image = Image.open(io.BytesIO(data))
            image = image.convert("RGB")
            return self.transform(image).unsqueeze(0).to(self.device)
        elif isinstance(data, Image.Image):
            # PIL图像
            image = data.convert("RGB")
            return self.transform(image).unsqueeze(0).to(self.device)
        elif isinstance(data, list):
            # 图像列表
            images = []
            for img in data:
                if isinstance(img, (bytes, bytearray)):
                    image = Image.open(io.BytesIO(img))
                    image = image.convert("RGB")
                elif isinstance(img, Image.Image):
                    image = img.convert("RGB")
                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")
                    
                images.append(self.transform(image))
                
            return torch.stack(images).to(self.device)
        else:
            raise ValueError(f"Unsupported image type: {type(data)}")
    
    def extract_features(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        提取图像特征
        
        Args:
            data: 输入图像或图像列表
            
        Returns:
            图像特征张量
        """
        inputs = self.preprocess(data)
        
        with torch.no_grad():
            features = self.model(inputs)
            features = self.projection(features)
            
        return features
    
    def encode(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        编码图像为特征表示
        
        Args:
            data: 输入图像或图像列表
            
        Returns:
            编码后的特征张量
        """
        return self.extract_features(data)
    
    def postprocess(self, data: torch.Tensor) -> torch.Tensor:
        """
        后处理特征
        
        Args:
            data: 特征张量
            
        Returns:
            后处理后的特征张量
        """
        # 归一化特征
        features = torch.nn.functional.normalize(data, p=2, dim=1)
        return features


class AudioProcessor(ModalityProcessor):
    """音频处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化音频处理器
        
        Args:
            config: 处理器配置字典
        """
        config["modality_type"] = "audio"
        super().__init__(config)
        self.sample_rate = config.get("sample_rate", 16000)
        self.max_length = config.get("max_length", 16000)  # 1秒音频
        
    def load_model(self) -> None:
        """加载音频模型"""
        import torchaudio
        from transformers import Wav2Vec2Model, Wav2Vec2Processor
        
        model_name = self.config.get("model_name", "facebook/wav2vec2-base-960h")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2Model.from_pretrained(model_name)
        
        # 调整特征维度
        if self.feature_dim != self.model.config.hidden_size:
            self.projection = nn.Linear(self.model.config.hidden_size, self.feature_dim)
        else:
            self.projection = nn.Identity()
            
        self.model.to(self.device)
        logger.info(f"Loaded audio model: {model_name}")
    
    def preprocess(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        预处理音频数据
        
        Args:
            data: 输入音频或音频列表
            
        Returns:
            预处理后的音频张量
        """
        import torchaudio
        import io
        
        if isinstance(data, (bytes, bytearray)):
            # 字节数据转音频张量
            waveform, sample_rate = torchaudio.load(io.BytesIO(data))
            waveform = torchaudio.functional.resample(waveform, sample_rate, self.sample_rate)
            
            # 调整长度
            if waveform.shape[1] > self.max_length:
                waveform = waveform[:, :self.max_length]
            else:
                waveform = torch.nn.functional.pad(waveform, (0, self.max_length - waveform.shape[1]))
                
            return waveform.to(self.device)
        elif isinstance(data, torch.Tensor):
            # 音频张量
            if data.shape[0] > 1:
                # 多声道转单声道
                data = torch.mean(data, dim=0, keepdim=True)
                
            # 调整长度
            if data.shape[1] > self.max_length:
                data = data[:, :self.max_length]
            else:
                data = torch.nn.functional.pad(data, (0, self.max_length - data.shape[1]))
                
            return data.to(self.device)
        elif isinstance(data, list):
            # 音频列表
            waveforms = []
            for audio in data:
                if isinstance(audio, (bytes, bytearray)):
                    waveform, sample_rate = torchaudio.load(io.BytesIO(audio))
                    waveform = torchaudio.functional.resample(waveform, sample_rate, self.sample_rate)
                elif isinstance(audio, torch.Tensor):
                    waveform = audio
                    if waveform.shape[0] > 1:
                        waveform = torch.mean(waveform, dim=0, keepdim=True)
                else:
                    raise ValueError(f"Unsupported audio type: {type(audio)}")
                
                # 调整长度
                if waveform.shape[1] > self.max_length:
                    waveform = waveform[:, :self.max_length]
                else:
                    waveform = torch.nn.functional.pad(waveform, (0, self.max_length - waveform.shape[1]))
                    
                waveforms.append(waveform)
                
            return torch.stack(waveforms).to(self.device)
        else:
            raise ValueError(f"Unsupported audio type: {type(data)}")
    
    def extract_features(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        提取音频特征
        
        Args:
            data: 输入音频或音频列表
            
        Returns:
            音频特征张量
        """
        inputs = self.preprocess(data)
        
        # 处理输入
        if inputs.dim() == 2:
            inputs = inputs.unsqueeze(0)  # 添加batch维度
            
        inputs = inputs.squeeze(1)  # 移除声道维度
        
        with torch.no_grad():
            inputs = self.processor(inputs, sampling_rate=self.sample_rate, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            outputs = self.model(**inputs)
            
            # 使用平均池化作为音频表示
            features = torch.mean(outputs.last_hidden_state, dim=1)
            features = self.projection(features)
            
        return features
    
    def encode(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        编码音频为特征表示
        
        Args:
            data: 输入音频或音频列表
            
        Returns:
            编码后的特征张量
        """
        return self.extract_features(data)
    
    def postprocess(self, data: torch.Tensor) -> torch.Tensor:
        """
        后处理特征
        
        Args:
            data: 特征张量
            
        Returns:
            后处理后的特征张量
        """
        # 归一化特征
        features = torch.nn.functional.normalize(data, p=2, dim=1)
        return features


class VideoProcessor(ModalityProcessor):
    """视频处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化视频处理器
        
        Args:
            config: 处理器配置字典
        """
        config["modality_type"] = "video"
        super().__init__(config)
        self.image_size = config.get("image_size", 224)
        self.max_frames = config.get("max_frames", 16)
        self.sample_rate = config.get("sample_rate", 16000)
        self.max_audio_length = config.get("max_audio_length", 16000)
        
    def load_model(self) -> None:
        """加载视频模型"""
        import torchvision.models as models
        import torchvision.transforms as transforms
        from transformers import Wav2Vec2Model, Wav2Vec2Processor
        
        # 视觉模型
        vision_model_name = self.config.get("vision_model_name", "resnet50")
        if vision_model_name == "resnet50":
            self.vision_model = models.resnet50(pretrained=True)
            self.vision_model.fc = nn.Identity()  # 移除最后的全连接层
            vision_input_dim = 2048
        else:
            raise ValueError(f"Unsupported vision model: {vision_model_name}")
        
        # 音频模型
        audio_model_name = self.config.get("audio_model_name", "facebook/wav2vec2-base-960h")
        self.audio_processor = Wav2Vec2Processor.from_pretrained(audio_model_name)
        self.audio_model = Wav2Vec2Model.from_pretrained(audio_model_name)
        audio_input_dim = self.audio_model.config.hidden_size
        
        # 调整特征维度
        total_input_dim = vision_input_dim + audio_input_dim
        if self.feature_dim != total_input_dim:
            self.projection = nn.Linear(total_input_dim, self.feature_dim)
        else:
            self.projection = nn.Identity()
            
        # 定义图像变换
        self.transform = transforms.Compose([
            transforms.Resize((self.image_size, self.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
            
        self.vision_model.to(self.device)
        self.audio_model.to(self.device)
        logger.info(f"Loaded video model: vision={vision_model_name}, audio={audio_model_name}")
    
    def preprocess(self, data: Union[Any, List[Any]]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预处理视频数据
        
        Args:
            data: 输入视频或视频列表
            
        Returns:
            预处理后的视频帧和音频张量
        """
        import cv2
        import torchaudio
        import io
        from PIL import Image
        
        if isinstance(data, (bytes, bytearray)):
            # 字节数据转视频
            video_bytes = io.BytesIO(data)
            
            # 读取视频帧
            cap = cv2.VideoCapture(video_bytes)
            frames = []
            frame_count = 0
            
            while cap.isOpened() and frame_count < self.max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 转换BGR到RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 转换为PIL图像
                frame_pil = Image.fromarray(frame_rgb)
                # 应用变换
                frame_tensor = self.transform(frame_pil)
                frames.append(frame_tensor)
                frame_count += 1
                
            cap.release()
            
            # 填充或截取帧
            if len(frames) < self.max_frames:
                # 重复最后一帧
                last_frame = frames[-1]
                frames.extend([last_frame] * (self.max_frames - len(frames)))
            else:
                frames = frames[:self.max_frames]
                
            video_frames = torch.stack(frames).to(self.device)
            
            # 读取音频
            video_bytes.seek(0)
            waveform, sample_rate = torchaudio.load(video_bytes)
            waveform = torchaudio.functional.resample(waveform, sample_rate, self.sample_rate)
            
            # 调整长度
            if waveform.shape[1] > self.max_audio_length:
                waveform = waveform[:, :self.max_audio_length]
            else:
                waveform = torch.nn.functional.pad(waveform, (0, self.max_audio_length - waveform.shape[1]))
                
            audio_waveform = waveform.to(self.device)
            
            return video_frames, audio_waveform
        elif isinstance(data, list):
            # 视频列表
            video_frames_list = []
            audio_waveforms_list = []
            
            for video in data:
                frames, waveform = self.preprocess(video)
                video_frames_list.append(frames)
                audio_waveforms_list.append(waveform)
                
            return torch.stack(video_frames_list), torch.stack(audio_waveforms_list)
        else:
            raise ValueError(f"Unsupported video type: {type(data)}")
    
    def extract_features(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        提取视频特征
        
        Args:
            data: 输入视频或视频列表
            
        Returns:
            视频特征张量
        """
        video_frames, audio_waveform = self.preprocess(data)
        
        with torch.no_grad():
            # 提取视觉特征
            batch_size, num_frames, c, h, w = video_frames.shape
            video_frames = video_frames.view(batch_size * num_frames, c, h, w)
            vision_features = self.vision_model(video_frames)
            vision_features = vision_features.view(batch_size, num_frames, -1)
            vision_features = torch.mean(vision_features, dim=1)  # 平均池化
            
            # 提取音频特征
            batch_size, channels, length = audio_waveform.shape
            audio_waveform = audio_waveform.squeeze(1)  # 移除声道维度
            
            audio_inputs = self.audio_processor(audio_waveform, sampling_rate=self.sample_rate, return_tensors="pt")
            audio_inputs = {k: v.to(self.device) for k, v in audio_inputs.items()}
            audio_outputs = self.audio_model(**audio_inputs)
            
            # 使用平均池化作为音频表示
            audio_features = torch.mean(audio_outputs.last_hidden_state, dim=1)
            
            # 融合视觉和音频特征
            combined_features = torch.cat([vision_features, audio_features], dim=1)
            features = self.projection(combined_features)
            
        return features
    
    def encode(self, data: Union[Any, List[Any]]) -> torch.Tensor:
        """
        编码视频为特征表示
        
        Args:
            data: 输入视频或视频列表
            
        Returns:
            编码后的特征张量
        """
        return self.extract_features(data)
    
    def postprocess(self, data: torch.Tensor) -> torch.Tensor:
        """
        后处理特征
        
        Args:
            data: 特征张量
            
        Returns:
            后处理后的特征张量
        """
        # 归一化特征
        features = torch.nn.functional.normalize(data, p=2, dim=1)
        return features
```

### 3.3 融合处理器实现

#### 3.3.1 融合处理器基类

```python
# core/fusion_processor.py

from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from .base_processor import BaseProcessor
from .modality_processor import ModalityProcessor
from loguru import logger


class FusionProcessor(BaseProcessor):
    """融合处理器基类，融合多模态特征"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化融合处理器
        
        Args:
            config: 处理器配置字典
        """
        super().__init__(config)
        self.modality_processors = {}
        self.fusion_method = config.get("fusion_method", "concat")
        self.output_dim = config.get("output_dim", 512)
        
        logger.info(f"Initialized {self.__class__.__name__} with fusion method: {self.fusion_method}")
    
    def add_modality_processor(self, modality: str, processor: ModalityProcessor) -> None:
        """
        添加模态处理器
        
        Args:
            modality: 模态名称
            processor: 模态处理器实例
        """
        self.modality_processors[modality] = processor
        logger.info(f"Added processor for modality: {modality}")
    
    def load_model(self) -> None:
        """加载融合模型"""
        # 计算输入维度
        input_dim = sum(
            processor.get_feature_dim() 
            for processor in self.modality_processors.values()
        )
        
        # 根据融合方法创建融合层
        if self.fusion_method == "concat":
            self.fusion_layer = nn.Sequential(
                nn.Linear(input_dim, input_dim * 2),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(input_dim * 2, self.output_dim)
            )
        elif self.fusion_method == "attention":
            self.fusion_layer = MultiModalAttention(input_dim, self.output_dim)
        elif self.fusion_method == "gated":
            self.fusion_layer = GatedFusion(input_dim, self.output_dim)
        else:
            raise ValueError(f"Unsupported fusion method: {self.fusion_method}")
            
        self.fusion_layer.to(self.device)
        logger.info(f"Loaded fusion model with method: {self.fusion_method}")
    
    def preprocess(self, data: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """
        预处理多模态数据
        
        Args:
            data: 多模态数据字典
            
        Returns:
            预处理后的特征字典
        """
        features = {}
        
        for modality, processor in self.modality_processors.items():
            if modality in data:
                modality_data = data[modality]
                modality_features = processor.encode(modality_data)
                features[modality] = modality_features
                
        return features
    
    def process(self, data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        融合多模态特征
        
        Args:
            data: 多模态特征字典
            
        Returns:
            融合后的特征
        """
        if self.fusion_method == "concat":
            return self._concat_fusion(data)
        elif self.fusion_method == "attention":
            return self._attention_fusion(data)
        elif self.fusion_method == "gated":
            return self._gated_fusion(data)
        else:
            raise ValueError(f"Unsupported fusion method: {self.fusion_method}")
    
    def _concat_fusion(self, data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        拼接融合
        
        Args:
            data: 多模态特征字典
            
        Returns:
            融合后的特征
        """
        # 按模态名称排序，确保顺序一致
        sorted_modalities = sorted(data.keys())
        features = [data[modality] for modality in sorted_modalities]
        
        # 拼接特征
        concatenated = torch.cat(features, dim=1)
        
        # 通过融合层
        fused_features = self.fusion_layer(concatenated)
        
        return fused_features
    
    def _attention_fusion(self, data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        注意力融合
        
        Args:
            data: 多模态特征字典
            
        Returns:
            融合后的特征
        """
        # 按模态名称排序，确保顺序一致
        sorted_modalities = sorted(data.keys())
        features = [data[modality] for modality in sorted_modalities]
        
        # 堆叠特征
        stacked = torch.stack(features, dim=1)  # [batch, modalities, feature_dim]
        
        # 通过注意力融合层
        fused_features = self.fusion_layer(stacked)
        
        return fused_features
    
    def _gated_fusion(self, data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        门控融合
        
        Args:
            data: 多模态特征字典
            
        Returns:
            融合后的特征
        """
        # 按模态名称排序，确保顺序一致
        sorted_modalities = sorted(data.keys())
        features = [data[modality] for modality in sorted_modalities]
        
        # 拼接特征
        concatenated = torch.cat(features, dim=1)
        
        # 通过门控融合层
        fused_features = self.fusion_layer(concatenated)
        
        return fused_features
    
    def postprocess(self, data: torch.Tensor) -> torch.Tensor:
        """
        后处理融合特征
        
        Args:
            data: 融合特征张量
            
        Returns:
            后处理后的特征张量
        """
        # 归一化特征
        features = torch.nn.functional.normalize(data, p=2, dim=1)
        return features


class MultiModalAttention(nn.Module):
    """多模态注意力机制"""
    
    def __init__(self, input_dim: int, output_dim: int, num_heads: int = 8):
        """
        初始化多模态注意力机制
        
        Args:
            input_dim: 输入特征维度
            output_dim: 输出特征维度
            num_heads: 注意力头数
        """
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.head_dim = input_dim // num_heads
        
        assert self.head_dim * num_heads == input_dim, "input_dim must be divisible by num_heads"
        
        # 查询、键、值投影
        self.query = nn.Linear(input_dim, input_dim)
        self.key = nn.Linear(input_dim, input_dim)
        self.value = nn.Linear(input_dim, input_dim)
        
        # 输出投影
        self.output_projection = nn.Linear(input_dim, output_dim)
        
        # 层归一化
        self.layer_norm = nn.LayerNorm(input_dim)
        
        # Dropout
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入张量，形状为 [batch_size, num_modalities, input_dim]
            
        Returns:
            输出张量，形状为 [batch_size, output_dim]
        """
        batch_size, num_modalities, _ = x.shape
        
        # 残差连接和层归一化
        residual = x
        x = self.layer_norm(x)
        
        # 计算查询、键、值
        q = self.query(x)  # [batch_size, num_modalities, input_dim]
        k = self.key(x)    # [batch_size, num_modalities, input_dim]
        v = self.value(x)  # [batch_size, num_modalities, input_dim]
        
        # 重塑为多头注意力格式
        q = q.view(batch_size, num_modalities, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, num_modalities, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, num_modalities, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算注意力分数
        scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        # 应用softmax
        attention_weights = torch.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # 应用注意力权重
        attended = torch.matmul(attention_weights, v)
        
        # 重塑回原始形状
        attended = attended.transpose(1, 2).contiguous().view(
            batch_size, num_modalities, self.input_dim
        )
        
        # 平均池化跨模态维度
        pooled = torch.mean(attended, dim=1)
        
        # 输出投影
        output = self.output_projection(pooled)
        
        # 残差连接
        output = output + torch.mean(residual, dim=1)
        
        return output


class GatedFusion(nn.Module):
    """门控融合机制"""
    
    def __init__(self, input_dim: int, output_dim: int):
        """
        初始化门控融合机制
        
        Args:
            input_dim: 输入特征维度
            output_dim: 输出特征维度
        """
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # 门控网络
        self.gate_network = nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.ReLU(),
            nn.Linear(input_dim // 2, input_dim),
            nn.Sigmoid()
        )
        
        # 特征变换网络
        self.feature_network = nn.Sequential(
            nn.Linear(input_dim, input_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(input_dim, output_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入张量，形状为 [batch_size, input_dim]
            
        Returns:
            输出张量，形状为 [batch_size, output_dim]
        """
        # 计算门控权重
        gate = self.gate_network(x)
        
        # 应用门控
        gated_features = x * gate
        
        # 特征变换
        output = self.feature_network(gated_features)
        
        return output
```

## 4. 情感处理模块实现

### 4.1 模块结构

情感处理模块负责识别、生成、记忆和适应情感信息，为交互表达子系统提供情感理解和表达能力。该模块基于多模态处理模块的输出，进行情感特征提取、情感状态识别、情感表达生成和情感记忆管理。

```
emotion_processing/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py          # 模块配置
│   └── model_configs.py     # 模型配置
├── core/
│   ├── __init__.py
│   ├── base_emotion.py       # 基础情感处理类
│   ├── emotion_recognizer.py # 情感识别器
│   ├── emotion_generator.py  # 情感生成器
│   └── emotion_memory.py     # 情感记忆管理
├── recognizers/
│   ├── __init__.py
│   ├── text_emotion_recognizer.py  # 文本情感识别
│   ├── image_emotion_recognizer.py # 图像情感识别
│   ├── audio_emotion_recognizer.py # 音频情感识别
│   └── multimodal_emotion_recognizer.py # 多模态情感识别
├── generators/
│   ├── __init__.py
│   ├── text_emotion_generator.py  # 文本情感生成
│   ├── image_emotion_generator.py # 图像情感生成
│   ├── audio_emotion_generator.py # 音频情感生成
│   └── multimodal_emotion_generator.py # 多模态情感生成
├── memory/
│   ├── __init__.py
│   ├── emotion_store.py      # 情感存储
│   ├── emotion_retrieval.py  # 情感检索
│   └── emotion_adaptation.py # 情感适应
├── models/
│   ├── __init__.py
│   ├── emotion_encoder.py    # 情感编码器
│   ├── emotion_decoder.py    # 情感解码器
│   └── emotion_model.py      # 情感模型
├── utils/
│   ├── __init__.py
│   ├── emotion_utils.py      # 情感工具函数
│   └── emotion_metrics.py    # 情感评估指标
└── api/
    ├── __init__.py
    ├── routes.py              # API路由
    └── schemas.py             # 数据模式
```

### 4.2 基础情感处理类实现

#### 4.2.1 基础情感处理类

```python
# core/base_emotion.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from loguru import logger


class BaseEmotionProcessor(ABC):
    """基础情感处理器抽象类，定义情感处理的基本接口和通用功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化基础情感处理器
        
        Args:
            config: 处理器配置字典
        """
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.emotion_categories = config.get("emotion_categories", [
            "happy", "sad", "angry", "fear", "surprise", "disgust", "neutral"
        ])
        self.emotion_dim = len(self.emotion_categories)
        
        logger.info(f"Initialized {self.__class__.__name__} with {self.emotion_dim} emotion categories")
    
    @abstractmethod
    def load_model(self) -> None:
        """加载模型"""
        pass
    
    @abstractmethod
    def preprocess(self, data: Any) -> Any:
        """预处理数据"""
        pass
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    def postprocess(self, data: Any) -> Any:
        """后处理数据"""
        pass
    
    def forward(self, data: Any) -> Any:
        """
        前向传播，整合预处理、处理和后处理
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        try:
            # 预处理
            preprocessed_data = self.preprocess(data)
            
            # 处理
            processed_data = self.process(preprocessed_data)
            
            # 后处理
            result = self.postprocess(processed_data)
            
            return result
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.forward: {str(e)}")
            raise
    
    def to(self, device: torch.device) -> "BaseEmotionProcessor":
        """
        将处理器移动到指定设备
        
        Args:
            device: 目标设备
            
        Returns:
            处理器实例
        """
        self.device = device
        if self.model is not None:
            self.model = self.model.to(device)
        return self
    
    def eval(self) -> "BaseEmotionProcessor":
        """
        设置为评估模式
        
        Returns:
            处理器实例
        """
        if self.model is not None:
            self.model = self.model.eval()
        return self
    
    def train(self) -> "BaseEmotionProcessor":
        """
        设置为训练模式
        
        Returns:
            处理器实例
        """
        if self.model is not None:
            self.model = self.model.train()
        return self
    
    def save_checkpoint(self, path: str) -> None:
        """
        保存检查点
        
        Args:
            path: 保存路径
        """
        if self.model is not None:
            checkpoint = {
                "model_state_dict": self.model.state_dict(),
                "config": self.config,
                "emotion_categories": self.emotion_categories
            }
            torch.save(checkpoint, path)
            logger.info(f"Saved checkpoint to {path}")
    
    def load_checkpoint(self, path: str) -> None:
        """
        加载检查点
        
        Args:
            path: 检查点路径
        """
        checkpoint = torch.load(path, map_location=self.device)
        if self.model is not None:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        if "emotion_categories" in checkpoint:
            self.emotion_categories = checkpoint["emotion_categories"]
            self.emotion_dim = len(self.emotion_categories)
        logger.info(f"Loaded checkpoint from {path}")
    
    def get_emotion_categories(self) -> List[str]:
        """
        获取情感类别列表
        
        Returns:
            情感类别列表
        """
        return self.emotion_categories
    
    def get_emotion_dim(self) -> int:
        """
        获取情感维度
        
        Returns:
            情感维度
        """
        return self.emotion_dim
    
    def emotion_to_index(self, emotion: str) -> int:
        """
        将情感类别转换为索引
        
        Args:
            emotion: 情感类别
            
        Returns:
            情感索引
        """
        return self.emotion_categories.index(emotion)
    
    def index_to_emotion(self, index: int) -> str:
        """
        将索引转换为情感类别
        
        Args:
            index: 情感索引
            
        Returns:
            情感类别
        """
        return self.emotion_categories[index]
    
    def one_hot_emotion(self, emotion: Union[str, int]) -> torch.Tensor:
        """
        将情感转换为独热编码
        
        Args:
            emotion: 情感类别或索引
            
        Returns:
            独热编码张量
        """
        if isinstance(emotion, str):
            index = self.emotion_to_index(emotion)
        else:
            index = emotion
            
        one_hot = torch.zeros(self.emotion_dim, device=self.device)
        one_hot[index] = 1.0
        
        return one_hot
    
    def softmax_to_emotion(self, probs: torch.Tensor) -> Tuple[str, float]:
        """
        将概率分布转换为情感类别和置信度
        
        Args:
            probs: 情感概率分布
            
        Returns:
            情感类别和置信度
        """
        if probs.dim() == 2:
            probs = probs.squeeze(0)
            
        max_index = torch.argmax(probs).item()
        confidence = probs[max_index].item()
        emotion = self.index_to_emotion(max_index)
        
        return emotion, confidence
```

#### 4.2.2 情感识别器类

```python
# core/emotion_recognizer.py

from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from .base_emotion import BaseEmotionProcessor
from loguru import logger


class EmotionRecognizer(BaseEmotionProcessor):
    """情感识别器，识别输入数据中的情感信息"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化情感识别器
        
        Args:
            config: 处理器配置字典
        """
        super().__init__(config)
        self.input_dim = config.get("input_dim", 512)
        self.hidden_dim = config.get("hidden_dim", 256)
        self.dropout_rate = config.get("dropout_rate", 0.2)
        
        logger.info(f"Initialized {self.__class__.__name__} with input_dim: {self.input_dim}")
    
    def load_model(self) -> None:
        """加载情感识别模型"""
        self.model = EmotionRecognitionModel(
            input_dim=self.input_dim,
            emotion_dim=self.emotion_dim,
            hidden_dim=self.hidden_dim,
            dropout_rate=self.dropout_rate
        )
        
        self.model.to(self.device)
        logger.info(f"Loaded emotion recognition model")
    
    def preprocess(self, data: torch.Tensor) -> torch.Tensor:
        """
        预处理输入特征
        
        Args:
            data: 输入特征张量
            
        Returns:
            预处理后的特征张量
        """
        # 确保输入在正确的设备上
        if not isinstance(data, torch.Tensor):
            data = torch.tensor(data, dtype=torch.float32)
            
        data = data.to(self.device)
        
        # 确保输入是二维的 [batch_size, feature_dim]
        if data.dim() == 1:
            data = data.unsqueeze(0)
            
        return data
    
    def process(self, data: torch.Tensor) -> torch.Tensor:
        """
        处理特征，识别情感
        
        Args:
            data: 输入特征张量
            
        Returns:
            情感概率分布
        """
        with torch.no_grad():
            emotion_probs = self.model(data)
            
        return emotion_probs
    
    def postprocess(self, data: torch.Tensor) -> Dict[str, Any]:
        """
        后处理情感概率分布
        
        Args:
            data: 情感概率分布
            
        Returns:
            情感识别结果字典
        """
        # 获取主要情感和置信度
        emotion, confidence = self.softmax_to_emotion(data)
        
        # 获取所有情感的概率
        emotion_probs = {}
        for i, prob in enumerate(data.squeeze(0)):
            emotion_name = self.index_to_emotion(i)
            emotion_probs[emotion_name] = prob.item()
            
        # 构建结果
        result = {
            "emotion": emotion,
            "confidence": confidence,
            "emotion_probs": emotion_probs,
            "emotion_vector": data.squeeze(0).tolist()
        }
        
        return result
    
    def recognize_emotion(self, features: torch.Tensor) -> Dict[str, Any]:
        """
        识别情感
        
        Args:
            features: 输入特征
            
        Returns:
            情感识别结果
        """
        return self.forward(features)


class EmotionRecognitionModel(nn.Module):
    """情感识别模型"""
    
    def __init__(self, input_dim: int, emotion_dim: int, hidden_dim: int = 256, dropout_rate: float = 0.2):
        """
        初始化情感识别模型
        
        Args:
            input_dim: 输入特征维度
            emotion_dim: 情感维度
            hidden_dim: 隐藏层维度
            dropout_rate: Dropout率
        """
        super().__init__()
        
        # 特征变换层
        self.feature_transform = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        
        # 情感分类层
        self.emotion_classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 2, emotion_dim),
            nn.Softmax(dim=-1)
        )
        
        # 批归一化
        self.batch_norm = nn.BatchNorm1d(hidden_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入特征，形状为 [batch_size, input_dim]
            
        Returns:
            情感概率分布，形状为 [batch_size, emotion_dim]
        """
        # 特征变换
        features = self.feature_transform(x)
        
        # 批归一化
        features = self.batch_norm(features)
        
        # 情感分类
        emotion_probs = self.emotion_classifier(features)
        
        return emotion_probs
```

#### 4.2.3 情感生成器类

```python
# core/emotion_generator.py

from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from .base_emotion import BaseEmotionProcessor
from loguru import logger


class EmotionGenerator(BaseEmotionProcessor):
    """情感生成器，根据情感状态生成相应的表达"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化情感生成器
        
        Args:
            config: 处理器配置字典
        """
        super().__init__(config)
        self.output_dim = config.get("output_dim", 512)
        self.hidden_dim = config.get("hidden_dim", 256)
        self.dropout_rate = config.get("dropout_rate", 0.2)
        self.condition_dim = config.get("condition_dim", 256)
        
        logger.info(f"Initialized {self.__class__.__name__} with output_dim: {self.output_dim}")
    
    def load_model(self) -> None:
        """加载情感生成模型"""
        self.model = EmotionGenerationModel(
            emotion_dim=self.emotion_dim,
            output_dim=self.output_dim,
            hidden_dim=self.hidden_dim,
            condition_dim=self.condition_dim,
            dropout_rate=self.dropout_rate
        )
        
        self.model.to(self.device)
        logger.info(f"Loaded emotion generation model")
    
    def preprocess(self, data: Dict[str, Any]) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        预处理输入数据
        
        Args:
            data: 输入数据字典，包含emotion和可选的condition
            
        Returns:
            情感向量和条件向量
        """
        # 处理情感输入
        emotion = data.get("emotion")
        if isinstance(emotion, str):
            emotion_vector = self.one_hot_emotion(emotion).unsqueeze(0)
        elif isinstance(emotion, int):
            emotion_vector = self.one_hot_emotion(emotion).unsqueeze(0)
        elif isinstance(emotion, list):
            emotion_vector = torch.tensor(emotion, dtype=torch.float32).unsqueeze(0)
        elif isinstance(emotion, torch.Tensor):
            emotion_vector = emotion.unsqueeze(0) if emotion.dim() == 1 else emotion
        else:
            raise ValueError(f"Unsupported emotion type: {type(emotion)}")
            
        emotion_vector = emotion_vector.to(self.device)
        
        # 处理条件输入
        condition = data.get("condition")
        if condition is not None:
            if isinstance(condition, list):
                condition_vector = torch.tensor(condition, dtype=torch.float32).unsqueeze(0)
            elif isinstance(condition, torch.Tensor):
                condition_vector = condition.unsqueeze(0) if condition.dim() == 1 else condition
            else:
                raise ValueError(f"Unsupported condition type: {type(condition)}")
                
            condition_vector = condition_vector.to(self.device)
        else:
            condition_vector = None
            
        return emotion_vector, condition_vector
    
    def process(self, emotion_vector: torch.Tensor, condition_vector: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        生成情感表达
        
        Args:
            emotion_vector: 情感向量
            condition_vector: 条件向量
            
        Returns:
            生成的表达特征
        """
        with torch.no_grad():
            output_features = self.model(emotion_vector, condition_vector)
            
        return output_features
    
    def postprocess(self, data: torch.Tensor) -> Dict[str, Any]:
        """
        后处理生成的特征
        
        Args:
            data: 生成的特征张量
            
        Returns:
            后处理后的结果字典
        """
        # 归一化特征
        features = torch.nn.functional.normalize(data, p=2, dim=1)
        
        # 构建结果
        result = {
            "features": features.squeeze(0).tolist(),
            "feature_dim": features.shape[1]
        }
        
        return result
    
    def generate_emotion(self, emotion: Union[str, int, List[float]], condition: Optional[Union[List[float], torch.Tensor]] = None) -> Dict[str, Any]:
        """
        生成情感表达
        
        Args:
            emotion: 情感输入，可以是类别名称、索引或情感向量
            condition: 条件输入，可选
            
        Returns:
            生成的情感表达
        """
        data = {"emotion": emotion}
        if condition is not None:
            data["condition"] = condition
            
        return self.forward(data)


class EmotionGenerationModel(nn.Module):
    """情感生成模型"""
    
    def __init__(self, emotion_dim: int, output_dim: int, hidden_dim: int = 256, 
                 condition_dim: int = 256, dropout_rate: float = 0.2):
        """
        初始化情感生成模型
        
        Args:
            emotion_dim: 情感维度
            output_dim: 输出特征维度
            hidden_dim: 隐藏层维度
            condition_dim: 条件向量维度
            dropout_rate: Dropout率
        """
        super().__init__()
        
        # 情感嵌入层
        self.emotion_embedding = nn.Sequential(
            nn.Linear(emotion_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        
        # 条件嵌入层
        if condition_dim > 0:
            self.condition_embedding = nn.Sequential(
                nn.Linear(condition_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            )
        else:
            self.condition_embedding = None
            
        # 融合层
        fusion_input_dim = hidden_dim * 2 if condition_dim > 0 else hidden_dim
        self.fusion = nn.Sequential(
            nn.Linear(fusion_input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        
        # 输出层
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, output_dim)
        )
        
        # 批归一化
        self.batch_norm = nn.BatchNorm1d(hidden_dim)
        
    def forward(self, emotion_vector: torch.Tensor, condition_vector: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        前向传播
        
        Args:
            emotion_vector: 情感向量，形状为 [batch_size, emotion_dim]
            condition_vector: 条件向量，形状为 [batch_size, condition_dim]，可选
            
        Returns:
            生成的特征，形状为 [batch_size, output_dim]
        """
        # 情感嵌入
        emotion_features = self.emotion_embedding(emotion_vector)
        
        # 条件嵌入
        if condition_vector is not None and self.condition_embedding is not None:
            condition_features = self.condition_embedding(condition_vector)
            # 融合情感和条件特征
            fused_features = torch.cat([emotion_features, condition_features], dim=1)
        else:
            fused_features = emotion_vector
            
        # 特征融合
        features = self.fusion(fused_features)
        
        # 批归一化
        features = self.batch_norm(features)
        
        # 输出生成
        output_features = self.output_layer(features)
        
        return output_features
```

#### 4.2.4 情感记忆管理类

```python
# core/emotion_memory.py

from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
import numpy as np
from datetime import datetime
from .base_emotion import BaseEmotionProcessor
from loguru import logger


class EmotionMemory(BaseEmotionProcessor):
    """情感记忆管理，存储、检索和适应情感信息"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化情感记忆管理
        
        Args:
            config: 处理器配置字典
        """
        super().__init__(config)
        self.memory_size = config.get("memory_size", 1000)
        self.feature_dim = config.get("feature_dim", 512)
        self.decay_rate = config.get("decay_rate", 0.01)
        self.retrieval_top_k = config.get("retrieval_top_k", 10)
        
        # 情感记忆存储
        self.emotion_memory = []
        self.memory_embeddings = None
        self.memory_timestamps = []
        self.memory_weights = []
        
        logger.info(f"Initialized {self.__class__.__name__} with memory_size: {self.memory_size}")
    
    def load_model(self) -> None:
        """加载记忆模型"""
        # 不需要加载预训练模型，使用简单的相似度计算
        logger.info(f"Loaded emotion memory model")
    
    def preprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理输入数据
        
        Args:
            data: 输入数据字典
            
        Returns:
            预处理后的数据
        """
        # 确保情感向量在正确的设备上
        emotion_vector = data.get("emotion_vector")
        if isinstance(emotion_vector, list):
            emotion_vector = torch.tensor(emotion_vector, dtype=torch.float32)
            
        if isinstance(emotion_vector, torch.Tensor):
            emotion_vector = emotion_vector.to(self.device)
            
        data["emotion_vector"] = emotion_vector
        
        return data
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理情感记忆操作
        
        Args:
            data: 输入数据字典，包含operation和相关参数
            
        Returns:
            处理结果
        """
        operation = data.get("operation")
        
        if operation == "store":
            return self._store_emotion(data)
        elif operation == "retrieve":
            return self._retrieve_emotion(data)
        elif operation == "adapt":
            return self._adapt_emotion(data)
        elif operation == "update":
            return self._update_emotion(data)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    def postprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        后处理结果
        
        Args:
            data: 处理结果
            
        Returns:
            后处理后的结果
        """
        # 将张量转换为列表，便于序列化
        if "emotion_vector" in data and isinstance(data["emotion_vector"], torch.Tensor):
            data["emotion_vector"] = data["emotion_vector"].tolist()
            
        if "similar_emotions" in data:
            for item in data["similar_emotions"]:
                if "emotion_vector" in item and isinstance(item["emotion_vector"], torch.Tensor):
                    item["emotion_vector"] = item["emotion_vector"].tolist()
                    
        return data
    
    def _store_emotion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        存储情感记忆
        
        Args:
            data: 包含情感向量和相关信息的字典
            
        Returns:
            存储结果
        """
        emotion_vector = data.get("emotion_vector")
        context = data.get("context", {})
        emotion_label = data.get("emotion_label", "unknown")
        
        # 创建记忆条目
        memory_entry = {
            "emotion_vector": emotion_vector,
            "context": context,
            "emotion_label": emotion_label,
            "timestamp": datetime.now().isoformat(),
            "weight": 1.0
        }
        
        # 添加到记忆
        self.emotion_memory.append(memory_entry)
        self.memory_timestamps.append(datetime.now())
        self.memory_weights.append(1.0)
        
        # 更新记忆嵌入矩阵
        self._update_memory_embeddings()
        
        # 检查记忆大小，如果超过限制则移除最旧的条目
        if len(self.emotion_memory) > self.memory_size:
            self._remove_oldest_memory()
            
        return {
            "success": True,
            "message": "Emotion stored successfully",
            "memory_size": len(self.emotion_memory)
        }
    
    def _retrieve_emotion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检索相似情感
        
        Args:
            data: 包含查询向量和检索参数的字典
            
        Returns:
            检索结果
        """
        query_vector = data.get("query_vector")
        top_k = data.get("top_k", self.retrieval_top_k)
        
        if self.memory_embeddings is None or len(self.emotion_memory) == 0:
            return {
                "success": False,
                "message": "No emotion memory available",
                "similar_emotions": []
            }
            
        # 计算相似度
        similarities = torch.nn.functional.cosine_similarity(
            query_vector.unsqueeze(0), 
            self.memory_embeddings, 
            dim=1
        )
        
        # 获取top-k最相似的情感
        top_k_values, top_k_indices = torch.topk(similarities, min(top_k, len(self.emotion_memory)))
        
        # 构建结果
        similar_emotions = []
        for i, (idx, similarity) in enumerate(zip(top_k_indices, top_k_values)):
            memory_entry = self.emotion_memory[idx.item()]
            similar_emotions.append({
                "emotion_vector": memory_entry["emotion_vector"],
                "context": memory_entry["context"],
                "emotion_label": memory_entry["emotion_label"],
                "timestamp": memory_entry["timestamp"],
                "similarity": similarity.item(),
                "weight": memory_entry["weight"]
            })
            
        return {
            "success": True,
            "query_vector": query_vector,
            "similar_emotions": similar_emotions
        }
    
    def _adapt_emotion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        适应情感表达
        
        Args:
            data: 包含情感向量和适应参数的字典
            
        Returns:
            适应结果
        """
        emotion_vector = data.get("emotion_vector")
        adaptation_rate = data.get("adaptation_rate", 0.1)
        
        # 检索相似情感
        retrieval_result = self._retrieve_emotion({
            "query_vector": emotion_vector,
            "top_k": 5
        })
        
        if not retrieval_result["success"] or not retrieval_result["similar_emotions"]:
            return {
                "success": False,
                "message": "No similar emotions found for adaptation",
                "adapted_emotion_vector": emotion_vector
            }
            
        # 计算加权平均
        total_weight = 0
        weighted_sum = torch.zeros_like(emotion_vector)
        
        for similar_emotion in retrieval_result["similar_emotions"]:
            weight = similar_emotion["weight"] * similar_emotion["similarity"]
            weighted_sum += weight * similar_emotion["emotion_vector"]
            total_weight += weight
            
        if total_weight > 0:
            weighted_sum /= total_weight
            
            # 适应情感向量
            adapted_emotion_vector = (1 - adaptation_rate) * emotion_vector + adaptation_rate * weighted_sum
        else:
            adapted_emotion_vector = emotion_vector
            
        return {
            "success": True,
            "original_emotion_vector": emotion_vector,
            "adapted_emotion_vector": adapted_emotion_vector,
            "similar_emotions_used": len(retrieval_result["similar_emotions"])
        }
    
    def _update_emotion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新情感记忆
        
        Args:
            data: 包含更新信息的字典
            
        Returns:
            更新结果
        """
        emotion_id = data.get("emotion_id")
        new_weight = data.get("new_weight")
        
        if emotion_id is None or emotion_id < 0 or emotion_id >= len(self.emotion_memory):
            return {
                "success":