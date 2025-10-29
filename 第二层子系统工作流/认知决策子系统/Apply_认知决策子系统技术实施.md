# Apply_认知决策子系统技术实施

## 阶段概述

本阶段基于Analyze阶段的架构设计，进行认知决策子系统的技术实施与开发，包括环境搭建、模块开发、接口实现、数据实现、系统集成和测试验证。认知决策子系统作为真实婴儿AI管家系统的核心组件，需要实现高效的认知处理、决策制定和思维链构建能力，同时保证系统的性能、可靠性和可扩展性。

## 环境搭建

### 1. 开发环境

#### 1.1 硬件环境

1. **开发服务器**
   - CPU: Intel i7-12700K 或同等性能
   - 内存: 32GB DDR4
   - 存储: 1TB NVMe SSD
   - GPU: NVIDIA RTX 3080 或更高
   - 网络: 千兆以太网

2. **测试服务器**
   - CPU: Intel Xeon E5-2690 v4 或同等性能
   - 内存: 64GB DDR4
   - 存储: 2TB NVMe SSD
   - GPU: NVIDIA A100 或更高
   - 网络: 万兆以太网

#### 1.2 软件环境

1. **操作系统**
   - 开发环境: Windows 11 / Ubuntu 22.04 LTS
   - 测试环境: Ubuntu 22.04 LTS
   - 生产环境: Ubuntu 22.04 LTS

2. **开发工具**
   - IDE: PyCharm Professional 2023.2 / VS Code 1.82
   - 版本控制: Git 2.40+
   - 容器化: Docker 24.0+, Docker Compose 2.20+
   - 编排工具: Kubernetes 1.28+

3. **编程环境**
   - Python: 3.9.17
   - CUDA: 12.2
   - cuDNN: 8.9
   - Node.js: 18.17+ (用于前端工具)

#### 1.3 Python环境配置

```bash
# 创建虚拟环境
python -m venv cognitive_decision_env

# 激活虚拟环境
# Windows
cognitive_decision_env\Scripts\activate
# Linux/Mac
source cognitive_decision_env/bin/activate

# 升级pip
pip install --upgrade pip

# 安装基础依赖
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
pip install langchain==0.1.0 langchain-experimental==0.0.40
pip install scikit-learn==1.3.0 pandas==2.0.3 numpy==1.24.3
pip install fastapi==0.104.1 uvicorn==0.24.0
pip install sqlalchemy==2.0.21 psycopg2-binary==2.9.7 pymongo==4.5.0 redis==5.0.0
pip install pika==1.3.2 grpcio==1.58.0 grpcio-tools==1.58.0
pip install prometheus-client==0.17.1
pip install pytest==7.4.2 pytest-asyncio==0.21.1
pip install black==23.9.1 flake8==6.1.0 isort==5.12.0
pip install sphinx==7.2.6 sphinx-rtd-theme==1.3.0
```

### 2. 项目结构

```
cognitive_decision_subsystem/
├── README.md
├── requirements.txt
├── setup.py
├── Dockerfile
├── docker-compose.yml
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── logging.py
│   ├── cognitive_processing/
│   │   ├── __init__.py
│   │   ├── pattern_recognition.py
│   │   ├── knowledge_representation.py
│   │   ├── reasoning.py
│   │   └── learning.py
│   ├── decision_making/
│   │   ├── __init__.py
│   │   ├── decision_model.py
│   │   ├── decision_optimization.py
│   │   ├── decision_execution.py
│   │   └── decision_evaluation.py
│   ├── thought_chain/
│   │   ├── __init__.py
│   │   ├── chain_representation.py
│   │   ├── chain_reasoning.py
│   │   └── chain_optimization.py
│   ├── system_integration/
│   │   ├── __init__.py
│   │   ├── data_integration.py
│   │   ├── service_integration.py
│   │   ├── process_integration.py
│   │   └── interface_adaptation.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── cognitive_api.py
│   │   │   ├── decision_api.py
│   │   │   └── thought_chain_api.py
│   │   ├── grpc/
│   │   │   ├── __init__.py
│   │   │   ├── cognitive_service.py
│   │   │   ├── decision_service.py
│   │   │   └── thought_chain_service.py
│   │   └── events/
│   │       ├── __init__.py
│       ├── cognitive_events.py
│       ├── decision_events.py
│       └── thought_chain_events.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── cognitive_models.py
│   │   │   ├── decision_models.py
│   │   │   └── thought_chain_models.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── cognitive_repository.py
│   │   │   ├── decision_repository.py
│   │   │   └── thought_chain_repository.py
│   │   └── migrations/
│   │       └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── metrics.py
│       ├── exceptions.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_cognitive_processing.py
│   │   ├── test_decision_making.py
│   │   ├── test_thought_chain.py
│   │   └── test_system_integration.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_integration.py
│   │   ├── test_service_integration.py
│   │   └── test_data_integration.py
│   └── performance/
│       ├── __init__.py
│       ├── test_cognitive_performance.py
│       ├── test_decision_performance.py
│       └── test_thought_chain_performance.py
├── docs/
│   ├── source/
│   │   ├── conf.py
│   │   ├── index.rst
│   │   ├── api/
│   │   ├── tutorials/
│   │   └── developer/
│   └── build/
├── scripts/
│   ├── setup_env.sh
│   ├── run_tests.sh
│   ├── build_docs.sh
│   └── deploy.sh
└── data/
    ├── models/
    ├── knowledge/
    └── samples/
```

### 3. 配置管理

#### 3.1 环境配置

```python
# src/config/settings.py

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Cognitive Decision Subsystem"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cognitive_decision"
    db_user: str = "postgres"
    db_password: str = "password"
    
    # MongoDB配置
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_db_name: str = "cognitive_decision_docs"
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # RabbitMQ配置
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    
    # Neo4j配置
    neo4j_host: str = "localhost"
    neo4j_port: int = 7687
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # GPU配置
    use_gpu: bool = True
    gpu_device: int = 0
    
    # 模型配置
    model_dir: str = "./data/models"
    knowledge_dir: str = "./data/knowledge"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/cognitive_decision.log"
    
    # 监控配置
    metrics_enabled: bool = True
    metrics_port: int = 9090
    
    # 安全配置
    secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局设置实例
settings = Settings()
```

#### 3.2 日志配置

```python
# src/config/logging.py

import logging
import logging.handlers
import os
from pathlib import Path

from .settings import settings


def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 创建文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        settings.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    return root_logger


# 初始化日志
logger = setup_logging()
```

## 认知处理模块实现

### 1. 模式识别子模块

#### 1.1 环境模式识别

```python
# src/cognitive_processing/pattern_recognition.py

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from ..config.settings import settings
from ..utils.logger import logger
from ..utils.metrics import track_performance


class EnvironmentPatternRecognition:
    """环境模式识别类"""
    
    def __init__(self):
        self.device = torch.device(f"cuda:{settings.gpu_device}" if settings.use_gpu and torch.cuda.is_available() else "cpu")
        self.model = self._load_model()
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': self.device}
        )
        self.vector_store = None
        self.patterns = []
        
    def _load_model(self) -> nn.Module:
        """加载环境模式识别模型"""
        model = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 10)  # 假设有10种环境模式
        )
        model_path = os.path.join(settings.model_dir, "environment_pattern_recognition.pth")
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info(f"Loaded environment pattern recognition model from {model_path}")
        else:
            logger.warning(f"Environment pattern recognition model not found at {model_path}, using initialized model")
        model.to(self.device)
        model.eval()
        return model
    
    @track_performance("environment_pattern_recognition")
    def recognize_pattern(self, environment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        识别环境模式
        
        Args:
            environment_data: 环境数据，包含各种环境特征
            
        Returns:
            识别结果，包含模式类型、置信度等
        """
        try:
            # 数据预处理
            features = self._preprocess_environment_data(environment_data)
            
            # 模式识别
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
                outputs = self.model(features_tensor)
                probabilities = torch.softmax(outputs, dim=1).cpu().numpy()[0]
                
            # 获取最可能的模式
            pattern_id = np.argmax(probabilities)
            confidence = float(probabilities[pattern_id])
            
            # 获取模式描述
            pattern_description = self._get_pattern_description(pattern_id)
            
            # 更新模式库
            self._update_pattern_library(environment_data, pattern_id, confidence)
            
            result = {
                "pattern_id": int(pattern_id),
                "pattern_name": pattern_description["name"],
                "pattern_description": pattern_description["description"],
                "confidence": confidence,
                "all_probabilities": probabilities.tolist(),
                "timestamp": environment_data.get("timestamp", None)
            }
            
            logger.info(f"Recognized environment pattern: {result['pattern_name']} with confidence {result['confidence']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in environment pattern recognition: {str(e)}")
            raise
    
    def _preprocess_environment_data(self, environment_data: Dict[str, Any]) -> np.ndarray:
        """预处理环境数据"""
        # 这里实现环境数据的预处理逻辑
        # 提取关键特征，标准化等
        features = []
        
        # 时间特征
        if "timestamp" in environment_data:
            timestamp = environment_data["timestamp"]
            if isinstance(timestamp, str):
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp)
            
            # 提取时间特征
            features.append(timestamp.hour / 24.0)  # 小时归一化
            features.append(timestamp.weekday() / 6.0)  # 星期归一化
            features.append((timestamp.month - 1) / 11.0)  # 月份归一化
        else:
            features.extend([0.0, 0.0, 0.0])
        
        # 环境特征
        if "temperature" in environment_data:
            features.append((environment_data["temperature"] - 20) / 30.0)  # 温度归一化
        else:
            features.append(0.0)
            
        if "humidity" in environment_data:
            features.append(environment_data["humidity"] / 100.0)  # 湿度归一化
        else:
            features.append(0.0)
            
        if "light_level" in environment_data:
            features.append(environment_data["light_level"] / 1000.0)  # 光照归一化
        else:
            features.append(0.0)
            
        if "noise_level" in environment_data:
            features.append(environment_data["noise_level"] / 100.0)  # 噪音归一化
        else:
            features.append(0.0)
        
        # 位置特征
        if "location" in environment_data:
            location = environment_data["location"]
            if "x" in location and "y" in location and "z" in location:
                features.append(location["x"] / 100.0)  # 位置x归一化
                features.append(location["y"] / 100.0)  # 位置y归一化
                features.append(location["z"] / 10.0)  # 位置z归一化
            else:
                features.extend([0.0, 0.0, 0.0])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        # 人员特征
        if "people_count" in environment_data:
            features.append(min(environment_data["people_count"], 10) / 10.0)  # 人数归一化
        else:
            features.append(0.0)
        
        # 活动特征
        if "activity_level" in environment_data:
            features.append(environment_data["activity_level"] / 100.0)  # 活动水平归一化
        else:
            features.append(0.0)
        
        # 填充特征到512维
        while len(features) < 512:
            features.append(0.0)
            
        return np.array(features[:512])
    
    def _get_pattern_description(self, pattern_id: int) -> Dict[str, str]:
        """获取模式描述"""
        patterns = {
            0: {"name": "安静环境", "description": "环境安静，人员少，活动水平低"},
            1: {"name": "活跃环境", "description": "环境活跃，人员多，活动水平高"},
            2: {"name": "学习环境", "description": "适合学习的环境，安静但有适当活动"},
            3: {"name": "休息环境", "description": "适合休息的环境，光线柔和，噪音低"},
            4: {"name": "娱乐环境", "description": "适合娱乐的环境，光线明亮，活动水平高"},
            5: {"name": "工作环境", "description": "适合工作的环境，安静但有适当活动"},
            6: {"name": "社交环境", "description": "适合社交的环境，人员多，活动水平中等"},
            7: {"name": "运动环境", "description": "适合运动的环境，空间大，活动水平高"},
            8: {"name": "用餐环境", "description": "适合用餐的环境，光线适中，噪音中等"},
            9: {"name": "睡眠环境", "description": "适合睡眠的环境，光线暗，噪音低"}
        }
        return patterns.get(pattern_id, {"name": "未知环境", "description": "无法识别的环境模式"})
    
    def _update_pattern_library(self, environment_data: Dict[str, Any], pattern_id: int, confidence: float):
        """更新模式库"""
        # 将环境数据转换为文本表示
        text_representation = self._environment_to_text(environment_data)
        
        # 创建模式记录
        pattern_record = {
            "pattern_id": pattern_id,
            "environment_data": environment_data,
            "text_representation": text_representation,
            "confidence": confidence,
            "timestamp": environment_data.get("timestamp", None)
        }
        
        # 添加到模式库
        self.patterns.append(pattern_record)
        
        # 更新向量存储
        if self.vector_store is None:
            # 初始化向量存储
            texts = [text_representation]
            metadatas = [{"pattern_id": pattern_id, "confidence": confidence}]
            self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        else:
            # 添加到现有向量存储
            self.vector_store.add_texts([text_representation], [{"pattern_id": pattern_id, "confidence": confidence}])
    
    def _environment_to_text(self, environment_data: Dict[str, Any]) -> str:
        """将环境数据转换为文本表示"""
        text_parts = []
        
        if "timestamp" in environment_data:
            timestamp = environment_data["timestamp"]
            if isinstance(timestamp, str):
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp)
            text_parts.append(f"时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if "temperature" in environment_data:
            text_parts.append(f"温度: {environment_data['temperature']}°C")
        
        if "humidity" in environment_data:
            text_parts.append(f"湿度: {environment_data['humidity']}%")
        
        if "light_level" in environment_data:
            text_parts.append(f"光照: {environment_data['light_level']} lux")
        
        if "noise_level" in environment_data:
            text_parts.append(f"噪音: {environment_data['noise_level']} dB")
        
        if "location" in environment_data:
            location = environment_data["location"]
            if "x" in location and "y" in location and "z" in location:
                text_parts.append(f"位置: ({location['x']}, {location['y']}, {location['z']})")
        
        if "people_count" in environment_data:
            text_parts.append(f"人数: {environment_data['people_count']}")
        
        if "activity_level" in environment_data:
            text_parts.append(f"活动水平: {environment_data['activity_level']}")
        
        return ", ".join(text_parts)
    
    def find_similar_patterns(self, environment_data: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        """查找相似的环境模式"""
        if self.vector_store is None:
            return []
        
        # 将环境数据转换为文本表示
        text_representation = self._environment_to_text(environment_data)
        
        # 搜索相似模式
        results = self.vector_store.similarity_search_with_score(text_representation, k=k)
        
        # 格式化结果
        similar_patterns = []
        for doc, score in results:
            pattern_data = doc.metadata
            pattern_data["similarity_score"] = float(score)
            pattern_data["text_representation"] = doc.page_content
            similar_patterns.append(pattern_data)
        
        return similar_patterns
```

## 决策制定模块实现

### 1. 决策模型子模块

#### 1.1 多准则决策模型

```python
# src/decision_making/decision_model.py

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass

from ..config.settings import settings
from ..utils.logger import logger
from ..utils.metrics import track_performance


class DecisionType(Enum):
    """决策类型枚举"""
    SINGLE_CRITERION = "single_criterion"  # 单准则决策
    MULTI_CRITERION = "multi_criterion"    # 多准则决策
    UNCERTAINTY = "uncertainty"            # 不确定性决策
    TIME_CONSTRAINED = "time_constrained"  # 时间约束决策
    RESOURCE_CONSTRAINED = "resource_constrained"  # 资源约束决策


@dataclass
class Criterion:
    """决策准则"""
    name: str
    weight: float  # 权重
    direction: str  # "maximize" 或 "minimize"
    utility_function: Optional[str] = None  # 效用函数类型
    parameters: Optional[Dict[str, Any]] = None  # 效用函数参数


@dataclass
class Alternative:
    """决策备选方案"""
    id: str
    name: str
    description: str
    criteria_values: Dict[str, float]  # 各准则下的值
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DecisionResult:
    """决策结果"""
    selected_alternative_id: str
    selected_alternative_name: str
    scores: Dict[str, float]  # 各备选方案的得分
    ranking: List[Tuple[str, float]]  # 排名 (备选方案ID, 得分)
    explanation: str  # 决策解释
    confidence: float  # 决策置信度
    metadata: Optional[Dict[str, Any]] = None


class MultiCriteriaDecisionModel:
    """多准则决策模型"""
    
    def __init__(self):
        self.device = torch.device(f"cuda:{settings.gpu_device}" if settings.use_gpu and torch.cuda.is_available() else "cpu")
        self.model = self._load_model()
        
    def _load_model(self) -> nn.Module:
        """加载决策模型"""
        model = nn.Sequential(
            nn.Linear(10, 64),  # 假设最多10个准则
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1)  # 输出决策得分
        )
        model_path = os.path.join(settings.model_dir, "multi_criteria_decision_model.pth")
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info(f"Loaded multi-criteria decision model from {model_path}")
        else:
            logger.warning(f"Multi-criteria decision model not found at {model_path}, using initialized model")
        model.to(self.device)
        model.eval()
        return model
    
    @track_performance("multi_criteria_decision")
    def make_decision(
        self, 
        criteria: List[Criterion], 
        alternatives: List[Alternative],
        decision_type: DecisionType = DecisionType.MULTI_CRITERION
    ) -> DecisionResult:
        """
        做出多准则决策
        
        Args:
            criteria: 决策准则列表
            alternatives: 备选方案列表
            decision_type: 决策类型
            
        Returns:
            决策结果
        """
        try:
            # 验证输入
            self._validate_input(criteria, alternatives)
            
            # 标准化准则值
            normalized_alternatives = self._normalize_criteria_values(criteria, alternatives)
            
            # 计算各备选方案的得分
            scores = {}
            for alternative in normalized_alternatives:
                score = self._calculate_alternative_score(criteria, alternative, decision_type)
                scores[alternative.id] = score
            
            # 排序备选方案
            ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # 选择最佳备选方案
            selected_alternative_id = ranking[0][0]
            selected_alternative = next(
                (alt for alt in alternatives if alt.id == selected_alternative_id), 
                None
            )
            
            # 生成决策解释
            explanation = self._generate_explanation(criteria, alternatives, scores, ranking)
            
            # 计算决策置信度
            confidence = self._calculate_confidence(scores, ranking)
            
            result = DecisionResult(
                selected_alternative_id=selected_alternative_id,
                selected_alternative_name=selected_alternative.name if selected_alternative else "",
                scores=scores,
                ranking=ranking,
                explanation=explanation,
                confidence=confidence
            )
            
            logger.info(f"Multi-criteria decision made: {result.selected_alternative_name} with confidence {result.confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-criteria decision: {str(e)}")
            raise
    
    def _validate_input(self, criteria: List[Criterion], alternatives: List[Alternative]):
        """验证输入数据"""
        if not criteria:
            raise ValueError("At least one criterion must be provided")
        
        if not alternatives:
            raise ValueError("At least one alternative must be provided")
        
        # 验证准则权重
        total_weight = sum(c.weight for c in criteria)
        if abs(total_weight - 1.0) > 0.01:  # 允许小的浮点误差
            logger.warning(f"Criterion weights sum to {total_weight}, normalizing to 1.0")
            for c in criteria:
                c.weight /= total_weight
        
        # 验证备选方案的准则值
        for alternative in alternatives:
            for criterion in criteria:
                if criterion.name not in alternative.criteria_values:
                    raise ValueError(f"Alternative {alternative.id} missing value for criterion {criterion.name}")
    
    def _normalize_criteria_values(
        self, 
        criteria: List[Criterion], 
        alternatives: List[Alternative]
    ) -> List[Alternative]:
        """标准化准则值"""
        normalized_alternatives = []
        
        for alternative in alternatives:
            normalized_criteria_values = {}
            
            for criterion in criteria:
                value = alternative.criteria_values[criterion.name]
                
                # 应用效用函数（如果有）
                if criterion.utility_function:
                    value = self._apply_utility_function(
                        value, 
                        criterion.utility_function, 
                        criterion.parameters or {}
                    )
                
                # 标准化到[0, 1]范围
                if criterion.direction == "maximize":
                    # 对于最大化准则，值越大越好
                    values = [alt.criteria_values[criterion.name] for alt in alternatives]
                    min_val, max_val = min(values), max(values)
                    if max_val > min_val:
                        normalized_value = (value - min_val) / (max_val - min_val)
                    else:
                        normalized_value = 0.5  # 所有值相同，设为中间值
                else:  # minimize
                    # 对于最小化准则，值越小越好
                    values = [alt.criteria_values[criterion.name] for alt in alternatives]
                    min_val, max_val = min(values), max(values)
                    if max_val > min_val:
                        normalized_value = 1 - (value - min_val) / (max_val - min_val)
                    else:
                        normalized_value = 0.5  # 所有值相同，设为中间值
                
                normalized_criteria_values[criterion.name] = normalized_value
            
            # 创建标准化后的备选方案
            normalized_alternative = Alternative(
                id=alternative.id,
                name=alternative.name,
                description=alternative.description,
                criteria_values=normalized_criteria_values,
                metadata=alternative.metadata
            )
            normalized_alternatives.append(normalized_alternative)
        
        return normalized_alternatives
    
    def _apply_utility_function(
        self, 
        value: float, 
        utility_function: str, 
        parameters: Dict[str, Any]
    ) -> float:
        """应用效用函数"""
        if utility_function == "linear":
            # 线性效用函数: u(x) = a * x + b
            a = parameters.get("a", 1.0)
            b = parameters.get("b", 0.0)
            return a * value + b
        elif utility_function == "exponential":
            # 指数效用函数: u(x) = 1 - exp(-x / r)
            r = parameters.get("r", 1.0)
            return 1 - np.exp(-value / r)
        elif utility_function == "logarithmic":
            # 对数效用函数: u(x) = log(x + 1)
            return np.log(value + 1)
        elif utility_function == "sigmoid":
            # S型效用函数: u(x) = 1 / (1 + exp(-a * (x - b)))
            a = parameters.get("a", 1.0)
            b = parameters.get("b", 0.0)
            return 1 / (1 + np.exp(-a * (value - b)))
        else:
            # 默认不应用效用函数
            return value
    
    def _calculate_alternative_score(
        self, 
        criteria: List[Criterion], 
        alternative: Alternative, 
        decision_type: DecisionType
    ) -> float:
        """计算备选方案得分"""
        if decision_type == DecisionType.MULTI_CRITERION:
            # 多准则决策：加权求和
            score = sum(
                alternative.criteria_values[criterion.name] * criterion.weight 
                for criterion in criteria
            )
            return score
        
        elif decision_type == DecisionType.SINGLE_CRITERION:
            # 单准则决策：选择权重最高的准则
            main_criterion = max(criteria, key=lambda c: c.weight)
            return alternative.criteria_values[main_criterion.name]
        
        elif decision_type == DecisionType.UNCERTAINTY:
            # 不确定性决策：使用神经网络模型
            features = []
            for criterion in criteria:
                features.append(alternative.criteria_values[criterion.name])
            
            # 填充特征到10维
            while len(features) < 10:
                features.append(0.0)
            
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
                score = self.model(features_tensor).item()
            
            return score
        
        elif decision_type == DecisionType.TIME_CONSTRAINED:
            # 时间约束决策：优先考虑时间相关准则
            time_criteria = [c for c in criteria if "time" in c.name.lower()]
            if time_criteria:
                time_weight = sum(c.weight for c in time_criteria)
                time_score = sum(
                    alternative.criteria_values[criterion.name] * criterion.weight 
                    for criterion in time_criteria
                ) / time_weight if time_weight > 0 else 0.0
                
                other_criteria = [c for c in criteria if c not in time_criteria]
                if other_criteria:
                    other_weight = sum(c.weight for c in other_criteria)
                    other_score = sum(
                        alternative.criteria_values[criterion.name] * criterion.weight 
                        for criterion in other_criteria
                    ) / other_weight if other_weight > 0 else 0.0
                    
                    # 时间准则权重更高
                    return 0.7 * time_score + 0.3 * other_score
                else:
                    return time_score
            else:
                # 没有时间相关准则，使用普通多准则决策
                return sum(
                    alternative.criteria_values[criterion.name] * criterion.weight 
                    for criterion in criteria
                )
        
        elif decision_type == DecisionType.RESOURCE_CONSTRAINED:
            # 资源约束决策：优先考虑资源相关准则
            resource_criteria = [c for c in criteria if "resource" in c.name.lower() or "cost" in c.name.lower()]
            if resource_criteria:
                resource_weight = sum(c.weight for c in resource_criteria)
                resource_score = sum(
                    alternative.criteria_values[criterion.name] * criterion.weight 
                    for criterion in resource_criteria
                ) / resource_weight if resource_weight > 0 else 0.0
                
                other_criteria = [c for c in criteria if c not in resource_criteria]
                if other_criteria:
                    other_weight = sum(c.weight for c in other_criteria)
                    other_score = sum(
                        alternative.criteria_values[criterion.name] * criterion.weight 
                        for criterion in other_criteria
                    ) / other_weight if other_weight > 0 else 0.0
                    
                    # 资源准则权重更高
                    return 0.7 * resource_score + 0.3 * other_score
                else:
                    return resource_score
            else:
                # 没有资源相关准则，使用普通多准则决策
                return sum(
                    alternative.criteria_values[criterion.name] * criterion.weight 
                    for criterion in criteria
                )
        
        else:
            # 默认使用多准则决策
            return sum(
                alternative.criteria_values[criterion.name] * criterion.weight 
                for criterion in criteria
            )
    
    def _generate_explanation(
        self, 
        criteria: List[Criterion], 
        alternatives: List[Alternative],
        scores: Dict[str, float], 
        ranking: List[Tuple[str, float]]
    ) -> str:
        """生成决策解释"""
        selected_alternative_id = ranking[0][0]
        selected_alternative = next(
            (alt for alt in alternatives if alt.id == selected_alternative_id), 
            None
        )
        
        if not selected_alternative:
            return "无法生成决策解释：找不到选中的备选方案"
        
        explanation_parts = [
            f"选择了备选方案 '{selected_alternative.name}'，因为它在多个准则上表现最佳。"
        ]
        
        # 分析各准则的贡献
        contributions = []
        for criterion in criteria:
            value = selected_alternative.criteria_values[criterion.name]
            contribution = value * criterion.weight
            contributions.append((criterion.name, contribution, value))
        
        # 按贡献度排序
        contributions.sort(key=lambda x: x[1], reverse=True)
        
        explanation_parts.append("主要贡献因素：")
        for name, contribution, value in contributions[:3]:  # 只显示前3个
            explanation_parts.append(f"- {name}: 值为 {value:.2f}，贡献度为 {contribution:.2f}")
        
        # 比较与其他备选方案的差异
        if len(ranking) > 1:
            second_alternative_id = ranking[1][0]
            second_alternative = next(
                (alt for alt in alternatives if alt.id == second_alternative_id), 
                None
            )
            
            if second_alternative:
                score_diff = ranking[0][1] - ranking[1][1]
                explanation_parts.append(
                    f"相比第二选择的方案 '{second_alternative.name}'，得分高出 {score_diff:.2f}。"
                )
        
        return "\n".join(explanation_parts)
    
    def _calculate_confidence(
        self, 
        scores: Dict[str, float], 
        ranking: List[Tuple[str, float]]
    ) -> float:
        """计算决策置信度"""
        if len(ranking) < 2:
            return 1.0  # 只有一个备选方案，置信度为1
        
        # 计算最高分和第二高分的差距
        top_score = ranking[0][1]
        second_score = ranking[1][1]
        score_diff = top_score - second_score
        
        # 计算所有得分的标准差
        all_scores = list(scores.values())
        std_dev = np.std(all_scores)
        
        # 结合得分差距和标准差计算置信度
        # 得分差距越大，标准差越大，置信度越高
        confidence = min(1.0, (score_diff + std_dev) / 2.0)
        
        return confidence
```

## 思维链构建模块实现

### 1. 思维链表示子模块

#### 1.1 思维链图结构

```python
# src/thought_chain/chain_representation.py

import os
import json
import uuid
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from ..config.settings import settings
from ..utils.logger import logger
from ..utils.metrics import track_performance


class NodeType(Enum):
    """思维链节点类型"""
    CONCEPT = "concept"           # 概念节点
    INFERENCE = "inference"       # 推理节点
    DECISION = "decision"         # 决策节点
    ACTION = "action"            # 行动节点
    GOAL = "goal"                # 目标节点
    HYPOTHESIS = "hypothesis"    # 假设节点
    EVIDENCE = "evidence"        # 证据节点
    QUESTION = "question"        # 问题节点
    ANSWER = "answer"            # 答案节点


class EdgeType(Enum):
    """思维链边类型"""
    LEADS_TO = "leads_to"        # 导致
    DEPENDS_ON = "depends_on"    # 依赖于
    SUPPORTS = "supports"        # 支持
    CONTRADICTS = "contradicts"  # 矛盾
    CAUSES = "causes"           # 引起
    ENHANCES = "enhances"       # 增强
    REDUCES = "reduces"         # 减弱
    SIMILAR_TO = "similar_to"    # 相似于


@dataclass
class ThoughtNode:
    """思维链节点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType = NodeType.CONCEPT
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThoughtNode':
        """从字典创建节点"""
        node = cls(
            id=data.get("id", str(uuid.uuid4())),
            type=NodeType(data.get("type", NodeType.CONCEPT.value)),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 1.0)
        )
        
        if "created_at" in data:
            node.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            node.updated_at = datetime.fromisoformat(data["updated_at"])
            
        return node


@dataclass
class ThoughtEdge:
    """思维链边"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    type: EdgeType = EdgeType.LEADS_TO
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value,
            "weight": self.weight,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThoughtEdge':
        """从字典创建边"""
        edge = cls(
            id=data.get("id", str(uuid.uuid4())),
            source_id=data.get("source_id", ""),
            target_id=data.get("target_id", ""),
            type=EdgeType(data.get("type", EdgeType.LEADS_TO.value)),
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {})
        )
        
        if "created_at" in data:
            edge.created_at = datetime.fromisoformat(data["created_at"])
            
        return edge


@dataclass
class ThoughtChain:
    """思维链"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    nodes: Dict[str, ThoughtNode] = field(default_factory=dict)
    edges: Dict[str, ThoughtEdge] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self.edges.items()},
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThoughtChain':
        """从字典创建思维链"""
        chain = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            metadata=data.get("metadata", {})
        )
        
        # 加载节点
        for nid, node_data in data.get("nodes", {}).items():
            node = ThoughtNode.from_dict(node_data)
            chain.nodes[nid] = node
        
        # 加载边
        for eid, edge_data in data.get("edges", {}).items():
            edge = ThoughtEdge.from_dict(edge_data)
            chain.edges[eid] = edge
        
        if "created_at" in data:
            chain.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            chain.updated_at = datetime.fromisoformat(data["updated_at"])
            
        return chain


class ThoughtChainManager:
    """思维链管理器"""
    
    def __init__(self):
        self.chains: Dict[str, ThoughtChain] = {}
        self.current_chain_id: Optional[str] = None
        
    @track_performance("create_thought_chain")
    def create_chain(self, name: str, description: str = "") -> str:
        """
        创建新的思维链
        
        Args:
            name: 思维链名称
            description: 思维链描述
            
        Returns:
            思维链ID
        """
        chain = ThoughtChain(name=name, description=description)
        self.chains[chain.id] = chain
        self.current_chain_id = chain.id
        
        logger.info(f"Created thought chain: {name} (ID: {chain.id})")
        return chain.id
    
    @track_performance("add_node")
    def add_node(
        self, 
        chain_id: str, 
        node_type: NodeType, 
        content: str, 
        metadata: Dict[str, Any] = None,
        confidence: float = 1.0
    ) -> str:
        """
        添加节点到思维链
        
        Args:
            chain_id: 思维链ID
            node_type: 节点类型
            content: 节点内容
            metadata: 节点元数据
            confidence: 节点置信度
            
        Returns:
            节点ID
        """
        if chain_id not in self.chains:
            raise ValueError(f"Thought chain {chain_id} not found")
        
        chain = self.chains[chain_id]
        node = ThoughtNode(
            type=node_type,
            content=content,
            metadata=metadata or {},
            confidence=confidence
        )
        
        chain.nodes[node.id] = node
        chain.updated_at = datetime.now()
        
        logger.info(f"Added node to thought chain {chain_id}: {node_type.value} - {content[:50]}...")
        return node.id
    
    @track_performance("add_edge")
    def add_edge(
        self, 
        chain_id: str, 
        source_id: str, 
        target_id: str, 
        edge_type: EdgeType,
        weight: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加边到思维链
        
        Args:
            chain_id: 思维链ID
            source_id: 源节点ID
            target_id: 目标节点ID
            edge_type: 边类型
            weight: 边权重
            metadata: 边元数据
            
        Returns:
            边ID
        """
        if chain_id not in self.chains:
            raise ValueError(f"Thought chain {chain_id} not found")
        
        chain = self.chains[chain_id]
        
        if source_id not in chain.nodes:
            raise ValueError(f"Source node {source_id} not found in chain {chain_id}")
        
        if target_id not in chain.nodes:
            raise ValueError(f"Target node {target_id} not found in chain {chain_id}")
        
        edge = ThoughtEdge(
            source_id=source_id,
            target_id=target_id,
            type=edge_type,
            weight=weight,
            metadata=metadata or {}
        )
        
        chain.edges[edge.id] = edge
        chain.updated_at = datetime.now()
        
        logger.info(f"Added edge to thought chain {chain_id}: {source_id} -[{edge_type.value}]-> {target_id}")
        return edge.id
    
    def get_chain(self, chain_id: str) -> Optional[ThoughtChain]:
        """获取思维链"""
        return self.chains.get(chain_id)
    
    def get_current_chain(self) -> Optional[ThoughtChain]:
        """获取当前思维链"""
        if self.current_chain_id:
            return self.chains.get(self.current_chain_id)
        return None
    
    def set_current_chain(self, chain_id: str):
        """设置当前思维链"""
        if chain_id in self.chains:
            self.current_chain_id = chain_id
            logger.info(f"Set current thought chain to {chain_id}")
        else:
            raise ValueError(f"Thought chain {chain_id} not found")
    
    def delete_chain(self, chain_id: str) -> bool:
        """删除思维链"""
        if chain_id in self.chains:
            del self.chains[chain_id]
            if self.current_chain_id == chain_id:
                self.current_chain_id = None
            logger.info(f"Deleted thought chain {chain_id}")
            return True
        return False
    
    def delete_node(self, chain_id: str, node_id: str) -> bool:
        """删除节点"""
        if chain_id not in self.chains:
            return False
        
        chain = self.chains[chain_id]
        if node_id in chain.nodes:
            # 删除节点
            del chain.nodes[node_id]
            
            # 删除相关边
            edges_to_delete = []
            for edge_id, edge in chain.edges.items():
                if edge.source_id == node_id or edge.target_id == node_id:
                    edges_to_delete.append(edge_id)
            
            for edge_id in edges_to_delete:
                del chain.edges[edge_id]
            
            chain.updated_at = datetime.now()
            logger.info(f"Deleted node {node_id} and related edges from thought chain {chain_id}")
            return True
        
        return False
    
    def delete_edge(self, chain_id: str, edge_id: str) -> bool:
        """删除边"""
        if chain_id not in self.chains:
            return False
        
        chain = self.chains[chain_id]
        if edge_id in chain.edges:
            del chain.edges[edge_id]
            chain.updated_at = datetime.now()
            logger.info(f"Deleted edge {edge_id} from thought chain {chain_id}")
            return True
        
        return False
    
    def get_node_neighbors(self, chain_id: str, node_id: str, direction: str = "both") -> Dict[str, List[ThoughtEdge]]:
        """
        获取节点的邻居
        
        Args:
            chain_id: 思维链ID
            node_id: 节点ID
            direction: 方向，可选值: "in", "out", "both"
            
        Returns:
            邻居节点和边的字典
        """
        if chain_id not in self.chains:
            return {}
        
        chain = self.chains[chain_id]
        neighbors = {"in": [], "out": []}
        
        for edge in chain.edges.values():
            if edge.target_id == node_id and direction in ["in", "both"]:
                neighbors["in"].append(edge)
            if edge.source_id == node_id and direction in ["out", "both"]:
                neighbors["out"].append(edge)
        
        return neighbors
    
    def find_path(self, chain_id: str, source_id: str, target_id: str) -> Optional[List[str]]:
        """
        查找两个节点之间的路径
        
        Args:
            chain_id: 思维链ID
            source_id: 源节点ID
            target_id: 目标节点ID
            
        Returns:
            路径节点ID列表
        """
        if chain_id not in self.chains:
            return None
        
        chain = self.chains[chain_id]
        
        if source_id not in chain.nodes or target_id not in chain.nodes:
            return None
        
        # 使用BFS查找最短路径
        visited = set()
        queue = [(source_id, [source_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id == target_id:
                return path
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # 获取当前节点的所有出边邻居
            for edge in chain.edges.values():
                if edge.source_id == current_id:
                    neighbor_id = edge.target_id
                    if neighbor_id not in visited:
                        queue.append((neighbor_id, path + [neighbor_id]))
        
        return None  # 没有找到路径
    
    def save_to_file(self, chain_id: str, file_path: str):
        """保存思维链到文件"""
        if chain_id not in self.chains:
            raise ValueError(f"Thought chain {chain_id} not found")
        
        chain = self.chains[chain_id]
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chain.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved thought chain {chain_id} to {file_path}")
    
    def load_from_file(self, file_path: str) -> str:
        """从文件加载思维链"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chain = ThoughtChain.from_dict(data)
        self.chains[chain.id] = chain
        
        logger.info(f"Loaded thought chain {chain.id} from {file_path}")
        return chain.id
```

## 系统集成模块实现

### 1. 数据集成子模块

```python
# src/system_integration/data_integration.py

import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymongo
import redis
from kafka import KafkaConsumer, KafkaProducer
import pika

from ..config.settings import settings
from ..utils.logger import logger
from ..utils.metrics import track_performance

Base = declarative_base()


class CognitiveData(Base):
    """认知数据模型"""
    __tablename__ = "cognitive_data"
    
    id = Column(String, primary_key=True)
    type = Column(String)
    content = Column(Text)
    metadata = Column(Text)  # JSON字符串
    confidence = Column(Float)
    timestamp = Column(DateTime)
    processed = Column(Boolean, default=False)


class DecisionData(Base):
    """决策数据模型"""
    __tablename__ = "decision_data"
    
    id = Column(String, primary_key=True)
    type = Column(String)
    criteria = Column(Text)  # JSON字符串
    alternatives = Column(Text)  # JSON字符串
    result = Column(Text)  # JSON字符串
    confidence = Column(Float)
    timestamp = Column(DateTime)
    executed = Column(Boolean, default=False)


class ThoughtChainData(Base):
    """思维链数据模型"""
    __tablename__ = "thought_chain_data"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    chain_data = Column(Text)  # JSON字符串
    metadata = Column(Text)  # JSON字符串
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class DataIntegrationManager:
    """数据集成管理器"""
    
    def __init__(self):
        # 初始化数据库连接
        self.db_engine = create_engine(
            f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
        )
        Base.metadata.create_all(self.db_engine)
        self.db_session = sessionmaker(bind=self.db_engine)()
        
        # 初始化MongoDB连接
        self.mongo_client = pymongo.MongoClient(
            f"mongodb://{settings.mongo_host}:{settings.mongo_port}/"
        )
        self.mongo_db = self.mongo_client[settings.mongo_db_name]
        
        # 初始化Redis连接
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        
        # 初始化RabbitMQ连接
        self.rabbitmq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                virtual_host=settings.rabbitmq_vhost,
                credentials=pika.PlainCredentials(
                    settings.rabbitmq_user,
                    settings.rabbitmq_password
                )
            )
        )
        self.rabbitmq_channel = self.rabbitmq_connection.channel()
        
        # 初始化Kafka生产者和消费者
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=[f"{settings.kafka_host}:{settings.kafka_port}"],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        logger.info("Data integration manager initialized")
    
    @track_performance("save_cognitive_data")
    def save_cognitive_data(self, data_type: str, content: str, metadata: Dict[str, Any] = None, confidence: float = 1.0) -> str:
        """
        保存认知数据
        
        Args:
            data_type: 数据类型
            content: 数据内容
            metadata: 元数据
            confidence: 置信度
            
        Returns:
            数据ID
        """
        import uuid
        data_id = str(uuid.uuid4())
        
        # 保存到PostgreSQL
        cognitive_data = CognitiveData(
            id=data_id,
            type=data_type,
            content=content,
            metadata=json.dumps(metadata or {}),
            confidence=confidence,
            timestamp=datetime.now()
        )
        self.db_session.add(cognitive_data)
        self.db_session.commit()
        
        # 保存到MongoDB
        mongo_data = {
            "id": data_id,
            "type": data_type,
            "content": content,
            "metadata": metadata or {},
            "confidence": confidence,
            "timestamp": datetime.now()
        }
        self.mongo_db.cognitive_data.insert_one(mongo_data)
        
        # 缓存到Redis
        redis_key = f"cognitive_data:{data_id}"
        redis_data = {
            "type": data_type,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.setex(redis_key, 3600, json.dumps(redis_data))  # 缓存1小时
        
        # 发送到Kafka
        kafka_message = {
            "id": data_id,
            "type": data_type,
            "content": content,
            "metadata": metadata or {},
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self.kafka_producer.send("cognitive_data", kafka_message)
        
        logger.info(f"Saved cognitive data: {data_id}")
        return data_id
    
    @track_performance("get_cognitive_data")
    def get_cognitive_data(self, data_id: str) -> Optional[Dict[str, Any]]:
        """
        获取认知数据
        
        Args:
            data_id: 数据ID
            
        Returns:
            认知数据
        """
        # 先从Redis缓存获取
        redis_key = f"cognitive_data:{data_id}"
        cached_data = self.redis_client.get(redis_key)
        if cached_data:
            data = json.loads(cached_data)
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            data["metadata"] = json.loads(data["metadata"])
            return data
        
        # 从PostgreSQL获取
        cognitive_data = self.db_session.query(CognitiveData).filter_by(id=data_id).first()
        if cognitive_data:
            data = {
                "id": cognitive_data.id,
                "type": cognitive_data.type,
                "content": cognitive_data.content,
                "metadata": json.loads(cognitive_data.metadata),
                "confidence": cognitive_data.confidence,
                "timestamp": cognitive_data.timestamp
            }
            
            # 更新Redis缓存
            redis_data = {
                "type": data["type"],
                "content": data["content"],
                "metadata": json.dumps(data["metadata"]),
                "confidence": data["confidence"],
                "timestamp": data["timestamp"].isoformat()
            }
            self.redis_client.setex(redis_key, 3600, json.dumps(redis_data))  # 缓存1小时
            
            return data
        
        return None
    
    @track_performance("save_decision_data")
    def save_decision_data(
        self, 
        decision_type: str, 
        criteria: List[Dict[str, Any]], 
        alternatives: List[Dict[str, Any]], 
        result: Dict[str, Any], 
        confidence: float = 1.0
    ) -> str:
        """
        保存决策数据
        
        Args:
            decision_type: 决策类型
            criteria: 决策准则
            alternatives: 备选方案
            result: 决策结果
            confidence: 置信度
            
        Returns:
            数据ID
        """
        import uuid
        data_id = str(uuid.uuid4())
        
        # 保存到PostgreSQL
        decision_data = DecisionData(
            id=data_id,
            type=decision_type,
            criteria=json.dumps(criteria),
            alternatives=json.dumps(alternatives),
            result=json.dumps(result),
            confidence=confidence,
            timestamp=datetime.now()
        )
        self.db_session.add(decision_data)
        self.db_session.commit()
        
        # 保存到MongoDB
        mongo_data = {
            "id": data_id,
            "type": decision_type,
            "criteria": criteria,
            "alternatives": alternatives,
            "result": result,
            "confidence": confidence,
            "timestamp": datetime.now()
        }
        self.mongo_db.decision_data.insert_one(mongo_data)
        
        # 缓存到Redis
        redis_key = f"decision_data:{data_id}"
        redis_data = {
            "type": decision_type,
            "criteria": json.dumps(criteria),
            "alternatives": json.dumps(alternatives),
            "result": json.dumps(result),
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.setex(redis_key, 3600, json.dumps(redis_data))  # 缓存1小时
        
        # 发送到Kafka
        kafka_message = {
            "id": data_id,
            "type": decision_type,
            "criteria": criteria,
            "alternatives": alternatives,
            "result": result,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self.kafka_producer.send("decision_data", kafka_message)
        
        logger.info(f"Saved decision data: {data_id}")
        return data_id
    
    @track_performance("get_decision_data")
    def get_decision_data(self, data_id: str) -> Optional[Dict[str, Any]]:
        """
        获取决策数据
        
        Args:
            data_id: 数据ID
            
        Returns:
            决策数据
        """
        # 先从Redis缓存获取
        redis_key = f"decision_data:{data_id}"
        cached_data = self.redis_client.get(redis_key)
        if cached_data:
            data = json.loads(cached_data)
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            data["criteria"] = json.loads(data["criteria"])
            data["alternatives"] = json.loads(data["alternatives"])
            data["result"] = json.loads(data["result"])
            return data
        
        # 从PostgreSQL获取
        decision_data = self.db_session.query(DecisionData).filter_by(id=data_id).first()
        if decision_data:
            data = {
                "id": decision_data.id,
                "type": decision_data.type,
                "criteria": json.loads(decision_data.criteria),
                "alternatives": json.loads(decision_data.alternatives),
                "result": json.loads(decision_data.result),
                "confidence": decision_data.confidence,
                "timestamp": decision_data.timestamp
            }
            
            # 更新Redis缓存
            redis_data = {
                "type": data["type"],
                "criteria": json.dumps(data["criteria"]),
                "alternatives": json.dumps(data["alternatives"]),
                "result": json.dumps(data["result"]),
                "confidence": data["confidence"],
                "timestamp": data["timestamp"].isoformat()
            }
            self.redis_client.setex(redis_key, 3600, json.dumps(redis_data))  # 缓存1小时
            
            return data
        
        return None
    
    @track_performance("save_thought_chain")
    def save_thought_chain(self, thought_chain: Dict[str, Any]) -> str:
        """
        保存思维链
        
        Args:
            thought_chain: 思维链数据
            
        Returns:
            数据ID
        """
        chain_id = thought_chain.get("id")
        if not chain_id:
            import uuid
            chain_id = str(uuid.uuid4())
            thought_chain["id"] = chain_id
        
        # 保存到PostgreSQL
        thought_chain_data = ThoughtChainData(
            id=chain_id,
            name=thought_chain.get("name", ""),
            description=thought_chain.get("description", ""),
            chain_data=json.dumps(thought_chain),
            metadata=json.dumps(thought_chain.get("metadata", {})),
            created_at=datetime.fromisoformat(thought_chain.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(thought_chain.get("updated_at", datetime.now().isoformat()))
        )
        self.db_session.add(thought_chain_data)
        self.db_session.commit()
        
        # 保存到MongoDB
        mongo_data = {
            "id": chain_id,
            "name": thought_chain.get("name", ""),
            "description": thought_chain.get("description", ""),
            "chain_data": thought_chain,
            "metadata": thought_chain.get("metadata", {}),
            "created_at": datetime.fromisoformat(thought_chain.get("created_at", datetime.now().isoformat())),
            "updated_at": datetime.fromisoformat(thought_chain.get("updated_at", datetime.now().isoformat()))
        }
        self.mongo_db.thought_chain_data.insert_one(mongo_data)
        
        # 缓存到Redis
        redis_key = f"thought_chain:{chain_id}"
        redis_data = {
            "name": thought_chain.get("name", ""),
            "description": thought_chain.get("description", ""),
            "chain_data": json.dumps(thought_chain),
            "metadata": json.dumps(thought_chain.get("metadata", {})),
            "created_at": thought_chain.get("created_at", datetime.now().isoformat()),
            "updated_at": thought_chain.get("updated_at", datetime.now().isoformat())
        }
        self.redis_client.setex(redis_key, 3600, json.dumps(redis_data))  # 缓存1小时
        
        # 发送到Kafka
        kafka_message = {
            "id": chain_id,
            "name": thought_chain.get("name", ""),
            "description": thought_chain.get("description", ""),
            "chain_data": thought_chain,
            "metadata": thought_chain.get("metadata", {}),
            "created_at": thought_chain.get("created_at", datetime.now().isoformat()),
            "updated_at": thought_chain.get("updated_at", datetime.now().isoformat())
        }
        self.kafka_producer.send("thought_chain", kafka_message)
        
        logger.info(f"Saved thought chain: {chain_id}")
        return chain_id
    
    @track_performance("get_thought_chain")
    def get_thought_chain(self, chain_id: str) -> Optional[Dict[str, Any]]:
        """
        获取思维链
        
        Args:
            chain_id: 思维链ID
            
        Returns:
            思维链数据
        """
        # 先从Redis缓存获取
        redis_key = f"thought_chain:{chain_id}"
        cached_data = self.redis_client.get(redis_key)
        if cached_data:
            data = json.loads(cached_data)
            data["chain_data"] = json.loads(data["chain_data"])
            data["metadata"] = json.loads(data["metadata"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            return data["chain_data"]
        
        # 从PostgreSQL获取
        thought_chain_data = self.db_session.query(ThoughtChainData).filter_by(id=chain_id).first()
        if thought_chain_data:
            chain_data = json.loads(thought_chain_data.chain_data)
            
            # 更新Redis缓存
            redis_data = {
                "name": thought_chain_data.name,
                "description": thought_chain_data.description,
                "chain_data": json.dumps(chain_data),
                "metadata": thought_chain_data.metadata,
                "created_at": thought_chain_data.created_at.isoformat(),
                "updated_at": thought_chain_data.updated_at.isoformat()
            }
            self.redis_client.setex(redis_key, 3600, json.dumps(redis_data))  # 缓存1小时
            
            return chain_data
        
        return None
    
    def setup_rabbitmq_consumer(self, queue_name: str, callback):
        """设置RabbitMQ消费者"""
        self.rabbitmq_channel.queue_declare(queue=queue_name)
        self.rabbitmq_channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=True
        )
        
        logger.info(f"Set up RabbitMQ consumer for queue: {queue_name}")
    
    def start_rabbitmq_consumer(self):
        """启动RabbitMQ消费者"""
        self.rabbitmq_channel.start_consuming()
        logger.info("Started RabbitMQ consumer")
    
    def stop_rabbitmq_consumer(self):
        """停止RabbitMQ消费者"""
        self.rabbitmq_channel.stop_consuming()
        logger.info("Stopped RabbitMQ consumer")
    
    def setup_kafka_consumer(self, topic_name: str):
        """设置Kafka消费者"""
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=[f"{settings.kafka_host}:{settings.kafka_port}"],
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        
        logger.info(f"Set up Kafka consumer for topic: {topic_name}")
        return consumer
    
    def close(self):
        """关闭所有连接"""
        self.db_session.close()
        self.mongo_client.close()
        self.redis_client.close()
        self.rabbitmq_connection.close()
        self.kafka_producer.close()
        
        logger.info("Closed all data integration connections")
```

## 接口实现

### 1. REST API接口

#### 1.1 认知处理API

```python
# src/interfaces/api/cognitive_api.py

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from ...cognitive_processing.pattern_recognition import EnvironmentPatternRecognition, BehaviorPatternRecognition
from ...cognitive_processing.knowledge_representation import KnowledgeGraph
from ...system_integration.data_integration import DataIntegrationManager
from ...utils.logger import logger

router = APIRouter(prefix="/cognitive", tags=["cognitive"])
security = HTTPBearer()

# 依赖注入
def get_data_integration_manager():
    return DataIntegrationManager()

def get_environment_pattern_recognition():
    return EnvironmentPatternRecognition()

def get_behavior_pattern_recognition():
    return BehaviorPatternRecognition()

def get_knowledge_graph():
    return KnowledgeGraph()


# 请求模型
class EnvironmentPatternRequest(BaseModel):
    environment_data: Dict[str, Any] = Field(..., description="环境数据")
    save_result: bool = Field(True, description="是否保存结果")


class BehaviorPatternRequest(BaseModel):
    behavior_data: Dict[str, Any] = Field(..., description="行为数据")
    save_result: bool = Field(True, description="是否保存结果")


class ConceptRequest(BaseModel):
    concept_name: str = Field(..., description="概念名称")
    concept_type: str = Field(..., description="概念类型")
    properties: Optional[Dict[str, Any]] = Field(None, description="概念属性")


class RelationshipRequest(BaseModel):
    source_id: str = Field(..., description="源概念ID")
    target_id: str = Field(..., description="目标概念ID")
    relationship_type: str = Field(..., description="关系类型")
    properties: Optional[Dict[str, Any]] = Field(None, description="关系属性")


class ConceptSearchRequest(BaseModel):
    query: str = Field(..., description="查询内容")
    search_type: str = Field("name", description="搜索类型: name, type, property")


# 响应模型
class PatternRecognitionResponse(BaseModel):
    pattern_id: int = Field(..., description="模式ID")
    pattern_name: str = Field(..., description="模式名称")
    pattern_description: str = Field(..., description="模式描述")
    confidence: float = Field(..., description="置信度")
    all_probabilities: List[float] = Field(..., description="所有概率")
    timestamp: Optional[str] = Field(None, description="时间戳")
    data_id: Optional[str] = Field(None, description="数据ID")


class ConceptResponse(BaseModel):
    concept_id: str = Field(..., description="概念ID")
    concept_name: str = Field(..., description="概念名称")
    concept_type: str = Field(..., description="概念类型")
    properties: Dict[str, Any] = Field(..., description="概念属性")


class RelationshipResponse(BaseModel):
    relationship_id: str = Field(..., description="关系ID")
    source_id: str = Field(..., description="源概念ID")
    target_id: str = Field(..., description="目标概念ID")
    relationship_type: str = Field(..., description="关系类型")
    properties: Dict[str, Any] = Field(..., description="关系属性")


# API端点
@router.post("/environment_pattern", response_model=PatternRecognitionResponse)
async def recognize_environment_pattern(
    request: EnvironmentPatternRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    data_manager: DataIntegrationManager = Depends(get_data_integration_manager),
    pattern_recognition: EnvironmentPatternRecognition = Depends(get_environment_pattern_recognition)
):
    """
    识别环境模式
    """
    try:
        # 识别环境模式
        result = pattern_recognition.recognize_pattern(request.environment_data)
        
        # 保存结果
        data_id = None
        if request.save_result:
            data_id = data_manager.save_cognitive_data(
                data_type="environment_pattern",
                content=result["pattern_description"],
                metadata={
                    "pattern_id": result["pattern_id"],
                    "pattern_name": result["pattern_name"],
                    "confidence": result["confidence"],
                    "environment_data": request.environment_data
                },
                confidence=result["confidence"]
            )
        
        # 返回结果
        response = PatternRecognitionResponse(
            pattern_id=result["pattern_id"],
            pattern_name=result["pattern_name"],
            pattern_description=result["pattern_description"],
            confidence=result["confidence"],
            all_probabilities=result["all_probabilities"],
            timestamp=result.get("timestamp"),
            data_id=data_id
        )
        
        logger.info(f"Environment pattern recognized: {result['pattern_name']} with confidence {result['confidence']:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"Error recognizing environment pattern: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/behavior_pattern", response_model=PatternRecognitionResponse)
async def recognize_behavior_pattern(
    request: BehaviorPatternRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    data_manager: DataIntegrationManager = Depends(get_data_integration_manager),
    pattern_recognition: BehaviorPatternRecognition = Depends(get_behavior_pattern_recognition)
):
    """
    识别行为模式
    """
    try:
        # 识别行为模式
        result = pattern_recognition.recognize_pattern(request.behavior_data)
        
        # 保存结果
        data_id = None
        if request.save_result:
            data_id = data_manager.save_cognitive_data(
                data_type="behavior_pattern",
                content=result["pattern_description"],
                metadata={
                    "pattern_id": result["pattern_id"],
                    "pattern_name": result["pattern_name"],
                    "confidence": result["confidence"],
                    "behavior_data": request.behavior_data
                },
                confidence=result["confidence"]
            )
        
        # 返回结果
        response = PatternRecognitionResponse(
            pattern_id=result["pattern_id"],
            pattern_name=result["pattern_name"],
            pattern_description=result["pattern_description"],
            confidence=result["confidence"],
            all_probabilities=result["all_probabilities"],
            timestamp=result.get("timestamp"),
            data_id=data_id
        )
        
        logger.info(f"Behavior pattern recognized: {result['pattern_name']} with confidence {result['confidence']:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"Error recognizing behavior pattern: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/concepts", response_model=ConceptResponse)
async def create_concept(
    request: ConceptRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    knowledge_graph: KnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    创建概念
    """
    try:
        # 创建概念
        concept_id = knowledge_graph.add_concept(
            concept_name=request.concept_name,
            concept_type=request.concept_type,
            properties=request.properties or {}
        )
        
        # 获取概念
        concept = knowledge_graph.get_concept(concept_id)
        
        logger.info(f"Created concept: {request.concept_name} (ID: {concept_id})")
        return ConceptResponse(
            concept_id=concept.id,
            concept_name=concept.name,
            concept_type=concept.type,
            properties=concept.properties
        )
        
    except Exception as e:
        logger.error(f"Error creating concept: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concepts/{concept_id}", response_model=ConceptResponse)
async def get_concept(
    concept_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    knowledge_graph: KnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    获取概念
    """
    try:
        # 获取概念
        concept = knowledge_graph.get_concept(concept_id)
        
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        logger.info(f"Retrieved concept: {concept.name} (ID: {concept_id})")
        return ConceptResponse(
            concept_id=concept.id,
            concept_name=concept.name,
            concept_type=concept.type,
            properties=concept.properties
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving concept: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship(
    request: RelationshipRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    knowledge_graph: KnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    创建关系
    """
    try:
        # 创建关系
        relationship_id = knowledge_graph.add_relationship(
            source_id=request.source_id,
            target_id=request.target_id,
            relationship_type=request.relationship_type,
            properties=request.properties or {}
        )
        
        # 获取关系
        relationship = knowledge_graph.get_relationship(relationship_id)
        
        logger.info(f"Created relationship: {request.source_id} -[{request.relationship_type}]-> {request.target_id} (ID: {relationship_id})")
        return RelationshipResponse(
            relationship_id=relationship.id,
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            relationship_type=relationship.type,
            properties=relationship.properties
        )
        
    except Exception as e:
        logger.error(f"Error creating relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/concepts/search", response_model=List[ConceptResponse])
async def search_concepts(
    request: ConceptSearchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    knowledge_graph: KnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    搜索概念
    """
    try:
        # 搜索概念
        concepts = knowledge_graph.search_concepts(
            query=request.query,
            search_type=request.search_type
        )
        
        # 转换为响应模型
        responses = [
            ConceptResponse(
                concept_id=concept.id,
                concept_name=concept.name,
                concept_type=concept.type,
                properties=concept.properties
            )
            for concept in concepts
        ]
        
        logger.info(f"Found {len(concepts)} concepts matching query: {request.query}")
        return responses
        
    except Exception as e:
        logger.error(f"Error searching concepts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

## 测试与验证

### 1. 单元测试

#### 1.1 认知处理模块测试

```python
# tests/unit/test_cognitive_processing.py

import pytest
import numpy as np
from unittest.mock import Mock, patch

from src.cognitive_processing.pattern_recognition import EnvironmentPatternRecognition
from src.cognitive_processing.knowledge_representation import KnowledgeGraph, Concept, Relationship


class TestEnvironmentPatternRecognition:
    """环境模式识别测试"""
    
    @pytest.fixture
    def pattern_recognition(self):
        """创建环境模式识别实例"""
        with patch('src.cognitive_processing.pattern_recognition.settings'):
            return EnvironmentPatternRecognition()
    
    def test_recognize_pattern(self, pattern_recognition):
        """测试模式识别"""
        # 准备测试数据
        environment_data = {
            "timestamp": "2023-11-15T14:30:00",
            "temperature": 25.5,
            "humidity": 60.0,
            "light_level": 500.0,
            "noise_level": 40.0,
            "location": {"x": 10.0, "y": 20.0, "z": 1.5},
            "people_count": 2,
            "activity_level": 30.0
        }
        
        # 执行模式识别
        result = pattern_recognition.recognize_pattern(environment_data)
        
        # 验证结果
        assert "pattern_id" in result
        assert "pattern_name" in result
        assert "pattern_description" in result
        assert "confidence" in result
        assert "all_probabilities" in result
        assert 0 <= result["confidence"] <= 1
        assert len(result["all_probabilities"]) == 10  # 假设有10种模式
    
    def test_preprocess_environment_data(self, pattern_recognition):
        """测试环境数据预处理"""
        # 准备测试数据
        environment_data = {
            "timestamp": "2023-11-15T14:30:00",
            "temperature": 25.5,
            "humidity": 60.0,
            "light_level": 500.0,
            "noise_level": 40.0,
            "location": {"x": 10.0, "y": 20.0, "z": 1.5},
            "people_count": 2,
            "activity_level": 30.0
        }
        
        # 执行预处理
        features = pattern_recognition._preprocess_environment_data(environment_data)
        
        # 验证结果
        assert isinstance(features, np.ndarray)
        assert features.shape == (512,)
        assert all(0 <= f <= 1 for f in features[:10])  # 前10个特征应该在[0,1]范围内
    
    def test_get_pattern_description(self, pattern_recognition):
        """测试获取模式描述"""
        # 测试已知模式
        description = pattern_recognition._get_pattern_description(0)
        assert "name" in description
        assert "description" in description
        
        # 测试未知模式
        description = pattern_recognition._get_pattern_description(999)
        assert description["name"] == "未知环境"
        assert description["description"] == "无法识别的环境模式"
    
    def test_environment_to_text(self, pattern_recognition):
        """测试环境数据转文本"""
        # 准备测试数据
        environment_data = {
            "timestamp": "2023-11-15T14:30:00",
            "temperature": 25.5,
            "humidity": 60.0,
            "light_level": 500.0,
            "noise_level": 40.0,
            "location": {"x": 10.0, "y": 20.0, "z": 1.5},
            "people_count": 2,
            "activity_level": 30.0
        }
        
        # 执行转换
        text = pattern_recognition._environment_to_text(environment_data)
        
        # 验证结果
        assert isinstance(text, str)
        assert "时间: 2023-11-15 14:30:00" in text
        assert "温度: 25.5°C" in text
        assert "湿度: 60.0%" in text


class TestKnowledgeGraph:
    """知识图谱测试"""
    
    @pytest.fixture
    def knowledge_graph(self):
        """创建知识图谱实例"""
        with patch('src.cognitive_processing.knowledge_representation.settings'):
            return KnowledgeGraph()
    
    def test_add_concept(self, knowledge_graph):
        """测试添加概念"""
        # 添加概念
        concept_id = knowledge_graph.add_concept(
            concept_name="婴儿",
            concept_type="人物",
            properties={"age": 6, "gender": "male"}
        )
        
        # 验证结果
        assert concept_id is not None
        
        # 获取概念
        concept = knowledge_graph.get_concept(concept_id)
        assert concept.name == "婴儿"
        assert concept.type == "人物"
        assert concept.properties["age"] == 6
        assert concept.properties["gender"] == "male"
    
    def test_add_relationship(self, knowledge_graph):
        """测试添加关系"""
        # 添加概念
        concept_id1 = knowledge_graph.add_concept(
            concept_name="婴儿",
            concept_type="人物",
            properties={"age": 6}
        )
        
        concept_id2 = knowledge_graph.add_concept(
            concept_name="母亲",
            concept_type="人物",
            properties={"age": 30}
        )
        
        # 添加关系
        relationship_id = knowledge_graph.add_relationship(
            source_id=concept_id1,
            target_id=concept_id2,
            relationship_type="亲子关系",
            properties={"relation_type": "母子"}
        )
        
        # 验证结果
        assert relationship_id is not None
        
        # 获取关系
        relationship = knowledge_graph.get_relationship(relationship_id)
        assert relationship.source_id == concept_id1
        assert relationship.target_id == concept_id2
        assert relationship.type == "亲子关系"
        assert relationship.properties["relation_type"] == "母子"
    
    def test_search_concepts(self, knowledge_graph):
        """测试搜索概念"""
        # 添加概念
        concept_id1 = knowledge_graph.add_concept(
            concept_name="婴儿",
            concept_type="人物",
            properties={"age": 6}
        )
        
        concept_id2 = knowledge_graph.add_concept(
            concept_name="幼儿",
            concept_type="人物",
            properties={"age": 3}
        )
        
        concept_id3 = knowledge_graph.add_concept(
            concept_name="玩具",
            concept_type="物品",
            properties={"type": "积木"}
        )
        
        # 按名称搜索
        concepts = knowledge_graph.search_concepts(query="婴", search_type="name")
        assert len(concepts) == 1
        assert concepts[0].id == concept_id1
        
        # 按类型搜索
        concepts = knowledge_graph.search_concepts(query="人物", search_type="type")
        assert len(concepts) == 2
        
        # 按属性搜索
        concepts = knowledge_graph.search_concepts(query="age", search_type="property")
        assert len(concepts) == 2
```

### 2. 集成测试

#### 2.1 API集成测试

```python
# tests/integration/test_api_integration.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.main import app


class TestCognitiveAPI:
    """认知API集成测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_recognize_environment_pattern(self, client):
        """测试环境模式识别API"""
        # 准备请求数据
        request_data = {
            "environment_data": {
                "timestamp": "2023-11-15T14:30:00",
                "temperature": 25.5,
                "humidity": 60.0,
                "light_level": 500.0,
                "noise_level": 40.0,
                "location": {"x": 10.0, "y": 20.0, "z": 1.5},
                "people_count": 2,
                "activity_level": 30.0
            },
            "save_result": True
        }
        
        # 发送请求
        response = client.post(
            "/cognitive/environment_pattern",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "pattern_id" in data
        assert "pattern_name" in data
        assert "pattern_description" in data
        assert "confidence" in data
        assert "all_probabilities" in data
    
    def test_create_concept(self, client):
        """测试创建概念API"""
        # 准备请求数据
        request_data = {
            "concept_name": "婴儿",
            "concept_type": "人物",
            "properties": {"age": 6, "gender": "male"}
        }
        
        # 发送请求
        response = client.post(
            "/cognitive/concepts",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "concept_id" in data
        assert data["concept_name"] == "婴儿"
        assert data["concept_type"] == "人物"
        assert data["properties"]["age"] == 6
        assert data["properties"]["gender"] == "male"
    
    def test_get_concept(self, client):
        """测试获取概念API"""
        # 先创建概念
        request_data = {
            "concept_name": "婴儿",
            "concept_type": "人物",
            "properties": {"age": 6, "gender": "male"}
        }
        
        create_response = client.post(
            "/cognitive/concepts",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        concept_id = create_response.json()["concept_id"]
        
        # 获取概念
        response = client.get(
            f"/cognitive/concepts/{concept_id}",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["concept_id"] == concept_id
        assert data["concept_name"] == "婴儿"
        assert data["concept_type"] == "人物"
        assert data["properties"]["age"] == 6
        assert data["properties"]["gender"] == "male"
```

### 3. 性能测试

#### 3.1 认知处理性能测试

```python
# tests/performance/test_cognitive_performance.py

import pytest
import time
import numpy as np
from unittest.mock import patch

from src.cognitive_processing.pattern_recognition import EnvironmentPatternRecognition


class TestCognitivePerformance:
    """认知处理性能测试"""
    
    @pytest.fixture
    def pattern_recognition(self):
        """创建环境模式识别实例"""
        with patch('src.cognitive_processing.pattern_recognition.settings'):
            return EnvironmentPatternRecognition()
    
    def test_pattern_recognition_performance(self, pattern_recognition):
        """测试模式识别性能"""
        # 准备测试数据
        environment_data = {
            "timestamp": "2023-11-15T14:30:00",
            "temperature": 25.5,
            "humidity": 60.0,
            "light_level": 500.0,
            "noise_level": 40.0,
            "location": {"x": 10.0, "y": 20.0, "z": 1.5},
            "people_count": 2,
            "activity_level": 30.0
        }
        
        # 测试单次识别性能
        start_time = time.time()
        result = pattern_recognition.recognize_pattern(environment_data)
        single_time = time.time() - start_time
        
        # 验证单次识别时间
        assert single_time < 0.1  # 单次识别应在100ms内完成
        
        # 测试批量识别性能
        batch_size = 100
        start_time = time.time()
        for _ in range(batch_size):
            result = pattern_recognition.recognize_pattern(environment_data)
        batch_time = time.time() - start_time
        
        # 验证批量识别性能
        avg_time = batch_time / batch_size
        assert avg_time < 0.05  # 平均识别时间应在50ms内
        
        print(f"Single recognition time: {single_time:.4f}s")
        print(f"Average recognition time (batch of {batch_size}): {avg_time:.4f}s")
```

## 部署与运维

### 1. Docker部署

#### 1.1 Dockerfile

```dockerfile
# Dockerfile

FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  cognitive-decision-subsystem:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=cognitive_decision
      - DB_USER=postgres
      - DB_PASSWORD=password
      - MONGO_HOST=mongodb
      - MONGO_PORT=27017
      - MONGO_DB_NAME=cognitive_decision_docs
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_PORT=5672
      - RABBITMQ_USER=guest
      - RABBITMQ_PASSWORD=guest
      - KAFKA_HOST=kafka
      - KAFKA_PORT=9092
      - USE_GPU=true
      - GPU_DEVICE=0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - mongodb
      - redis
      - rabbitmq
      - kafka
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=cognitive_decision
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  mongodb:
    image: mongo:7
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
      - MONGO_INITDB_DATABASE=cognitive_decision_docs
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper
    restart: unless-stopped

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    restart: unless-stopped

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  rabbitmq_data:
```

### 2. Kubernetes部署

#### 2.1 部署配置

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: cognitive-decision-subsystem
  namespace: ai-system
  labels:
    app: cognitive-decision-subsystem
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cognitive-decision-subsystem
  template:
    metadata:
      labels:
        app: cognitive-decision-subsystem
    spec:
      containers:
      - name: cognitive-decision-subsystem
        image: cognitive-decision-subsystem:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "false"
        - name: DB_HOST
          value: "postgres-service"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "cognitive_decision"
        - name: DB_USER
          value: "postgres"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        - name: MONGO_HOST
          value: "mongodb-service"
        - name: MONGO_PORT
          value: "27017"
        - name: MONGO_DB_NAME
          value: "cognitive_decision_docs"
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PORT
          value: "6379"
        - name: REDIS_DB
          value: "0"
        - name: RABBITMQ_HOST
          value: "rabbitmq-service"
        - name: RABBITMQ_PORT
          value: "5672"
        - name: RABBITMQ_USER
          value: "guest"
        - name: RABBITMQ_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rabbitmq-secret
              key: password
        - name: KAFKA_HOST
          value: "kafka-service"
        - name: KAFKA_PORT
          value: "9092"
        - name: USE_GPU
          value: "true"
        - name: GPU_DEVICE
          value: "0"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
            nvidia.com/gpu: 1
          limits:
            memory: "4Gi"
            cpu: "2000m"
            nvidia.com/gpu: 1
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: cognitive-decision-data-pvc
      - name: logs-volume
        persistentVolumeClaim:
          claimName: cognitive-decision-logs-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: cognitive-decision-service
  namespace: ai-system
spec:
  selector:
    app: cognitive-decision-subsystem
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cognitive-decision-ingress
  namespace: ai-system
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - cognitive-decision.ai-system.example.com
    secretName: cognitive-decision-tls
  rules:
  - host: cognitive-decision.ai-system.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cognitive-decision-service
            port:
              number: 8000
```

## 监控与日志

### 1. 监控配置

#### 1.1 Prometheus监控

```python
# src/utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from functools import wraps
import time

# 定义指标
REQUEST_COUNT = Counter(
    'cognitive_decision_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'cognitive_decision_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'cognitive_decision_active_connections',
    'Number of active connections'
)

PATTERN_RECOGNITION_COUNT = Counter(
    'cognitive_decision_pattern_recognition_total',
    'Total number of pattern recognitions',
    ['pattern_type']
)

PATTERN_RECOGNITION_DURATION = Histogram(
    'cognitive_decision_pattern_recognition_duration_seconds',
    'Pattern recognition duration in seconds',
    ['pattern_type']
)

DECISION_MAKING_COUNT = Counter(
    'cognitive_decision_decision_making_total',
    'Total number of decision makings',
    ['decision_type']
)

DECISION_MAKING_DURATION = Histogram(
    'cognitive_decision_decision_making_duration_seconds',
    'Decision making duration in seconds',
    ['decision_type']
)

THOUGHT_CHAIN_OPERATIONS = Counter(
    'cognitive_decision_thought_chain_operations_total',
    'Total number of thought chain operations',
    ['operation_type']
)

THOUGHT_CHAIN_DURATION = Histogram(
    'cognitive_decision_thought_chain_duration_seconds',
    'Thought chain operation duration in seconds',
    ['operation_type']
)


def track_performance(operation_name: str, metric_type: str = "counter"):
    """
    性能跟踪装饰器
    
    Args:
        operation_name: 操作名称
        metric_type: 指标类型，可选值: counter, histogram
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 记录开始时间
            start_time = time.time()
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录结束时间和持续时间
            duration = time.time() - start_time
            
            # 更新指标
            if metric_type == "counter":
                # 根据操作名称选择相应的计数器
                if "pattern_recognition" in operation_name:
                    PATTERN_RECOGNITION_COUNT.labels(pattern_type=operation_name).inc()
                elif "decision_making" in operation_name:
                    DECISION_MAKING_COUNT.labels(decision_type=operation_name).inc()
                elif "thought_chain" in operation_name:
                    THOUGHT_CHAIN_OPERATIONS.labels(operation_type=operation_name).inc()
            elif metric_type == "histogram":
                # 根据操作名称选择相应的直方图
                if "pattern_recognition" in operation_name:
                    PATTERN_RECOGNITION_DURATION.labels(pattern_type=operation_name).observe(duration)
                elif "decision_making" in operation_name:
                    DECISION_MAKING_DURATION.labels(decision_type=operation_name).observe(duration)
                elif "thought_chain" in operation_name:
                    THOUGHT_CHAIN_DURATION.labels(operation_type=operation_name).observe(duration)
            
            return result
        
        return wrapper
    return decorator


def get_metrics():
    """获取Prometheus格式的指标"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

## 总结

本技术实施文档详细描述了认知决策子系统的技术实现方案，包括环境搭建、模块开发、接口实现、数据实现、系统集成和测试验证等方面。通过本实施文档，开发团队可以按照标准化的流程完成认知决策子系统的开发、测试和部署工作，确保系统的质量、性能和可靠性。

主要技术特点：

1. **模块化设计**：采用模块化设计，将认知处理、决策制定、思维链构建和系统集成等功能分离，提高代码的可维护性和可扩展性。

2. **多数据源支持**：支持多种数据源，包括PostgreSQL、MongoDB、Redis、RabbitMQ和Kafka，满足不同场景下的数据存储和处理需求。

3. **高性能处理**：利用GPU加速和优化算法，实现高性能的认知处理和决策制定，满足实时性要求。

4. **标准化接口**：提供标准化的REST API和gRPC接口，方便与其他子系统进行集成。

5. **全面测试**：包括单元测试、集成测试和性能测试，确保系统的质量和稳定性。

6. **容器化部署**：支持Docker和Kubernetes部署，实现系统的快速部署和弹性扩展。

7. **监控与日志**：集成Prometheus监控和结构化日志，方便系统运维和问题排查。

通过本技术实施，认知决策子系统将成为真实婴儿AI管家系统的核心组件，为系统提供强大的认知处理、决策制定和思维链构建能力，支持系统的智能化和自主化运行。