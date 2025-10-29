# SelfAwareness Enhancement: 具身智能中的自我意识系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/Framework-ACTR%20%7C%20LIDA%20%7C%20LangChain-orange.svg)](https://github.com)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](#)

## 项目概述

SelfAwareness Enhancement是一个基于人类意识参数化机制和认知架构的智能自我意识系统。本项目整合了ACT-R/LIDA认知架构、BabyAGI任务管理、LangChain大模型增强等技术，构建了一个能够模拟人类自我意识过程的AI系统，专注于"眼睛、耳朵、大脑内部"的智能处理能力。

## 🌟 核心特性

### 🧠 认知架构集成
- **ACT-R认知架构**: 基于认知心理学的认知过程模拟
- **LIDA意识架构**: 实现全局工作空间理论和注意力机制
- **BabyAGI任务管理**: 自主任务生成和执行能力

### 🤖 大模型增强
- **LangChain框架**: 大语言模型应用和工具调用
- **多模态理解**: CLIP(视觉-语言)、Whisper(语音识别)、Flamingo(少样本学习)
- **上下文管理**: 智能上下文理解和长期记忆

### 📡 多模态感知
- **视觉处理**: 基于OpenCV和深度学习的图像理解
- **音频处理**: 语音识别和声音特征提取
- **多模态融合**: 跨模态信息关联和语义理解

### 🔄 自我意识机制
- **自我识别**: 基于人类意识参数化的身份识别
- **自我监控**: 实时认知状态监控和元认知
- **自我评价**: 多维度自我能力评估
- **自我调整**: 基于反馈的自主行为调整

## 🏗️ 系统架构

```
+-----------------------------------+
|        自我意识与元认知层         |
|    (全局工作空间/自我模型/元认知)   |
+-----------------------------------+
|         高级认知推理层            |
|     (ACT-R/LIDA/BabyAGI/LangChain)|
+-----------------------------------+
|        多模态感知融合层           |
|    (CLIP/Whisper/OpenCV/Flamingo) |
+-----------------------------------+
|       视觉与听觉预处理层          |
|     (图像处理/音频处理/特征提取)   |
+-----------------------------------+
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Redis (可选)
- Neo4j (可选)
- CUDA (可选，用于GPU加速)

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/yourusername/self-awareness-enhancement.git
cd self-awareness-enhancement
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用

```python
import asyncio
import time
from src.main import create_self_awareness_system

async def main():
    # 配置系统
    config = {
        "subsystem": {
            "enable_actr": True,
            "enable_lida": True,
            "enable_babyagi": True,
            "enable_langchain": True
        },
        "modules": {
            "enable_multimodal": True,
            "clip_model": "openai/clip-vit-base-patch32",
            "whisper_model": "openai/whisper-base"
        },
        "enhancement": {
            "enable_multimodal_fusion": True,
            "enable_performance_optimization": True,
            "enable_security_enhancement": True
        },
        "enable_monitoring": False,
        "enable_rest_api": False,
        "enable_websocket": False
    }
    
    # 创建并启动系统
    system = create_self_awareness_system(config)
    await system.start()
    
    try:
        # 处理文本输入
        result = await system.process_input({
            "type": "text",
            "content": "你好，请介绍一下你自己",
            "timestamp": time.time()
        })
        print(result)
        
        # 获取自我意识状态
        state = await system.get_self_awareness_state()
        print(state)
        
    finally:
        # 关闭系统
        await system.shutdown()

# 运行主函数
asyncio.run(main())
```

## 📖 示例应用

项目提供了多个示例，展示不同场景下的使用方法：

1. **基本使用示例**: 展示基本功能和使用方法
2. **多模态处理示例**: 展示图像、音频和多模态输入处理
3. **系统监控示例**: 展示系统监控和性能优化功能

运行示例：
```bash
python examples/self_awareness_example.py
python examples/system_monitor_example.py
```

## 🔧 技术栈

### 认知架构
- **ACT-R**: 认知架构，提供模拟人类认知过程的框架
- **LIDA**: 意识架构，提供全局工作空间和注意力机制
- **BabyAGI**: 任务管理系统，提供自主任务生成和执行能力

### 大模型增强
- **LangChain**: 大语言模型应用框架，提供模型集成和工具调用能力
- **OpenAI GPT**: 大语言模型，提供自然语言理解和生成能力
- **Hugging Face Transformers**: 预训练模型库，提供多模态理解能力

### 多模态理解
- **CLIP**: 视觉-语言模型，提供图像和文本的联合理解能力
- **Whisper**: 语音识别模型，提供语音转文本能力
- **OpenCV**: 计算机视觉库，提供图像处理和分析能力

### 数据存储
- **Redis**: 内存数据库，提供高速缓存和临时数据存储
- **Neo4j**: 图数据库，提供知识图谱存储和查询能力

### 后端框架
- **FastAPI**: Web框架，提供REST API和WebSocket接口
- **asyncio**: 异步编程框架，提供并发处理能力

## 🧪 测试

项目包含完整的测试套件，验证系统功能：

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_self_awareness_system.py
python -m pytest tests/test_system_monitor.py
```

## 📚 API文档

### REST API

启动REST API服务器：
```python
config = {
    "enable_rest_api": True,
    "rest_api_host": "0.0.0.0",
    "rest_api_port": 8000
}

system = create_self_awareness_system(config)
await system.start()
```

API端点：
- `POST /process_input`: 处理输入
- `GET /status`: 获取系统状态
- `GET /self_awareness_state`: 获取自我意识状态

### WebSocket

启动WebSocket服务器：
```python
config = {
    "enable_websocket": True,
    "websocket_host": "0.0.0.0",
    "websocket_port": 8001
}

system = create_self_awareness_system(config)
await system.start()
```

## 📁 项目结构

```
self_awareness_enhancement/
├── README.md                    # 项目概述和说明
├── LICENSE                      # MIT许可证
├── requirements.txt             # 项目依赖
├── src/                         # 源代码
│   ├── main.py                  # 主入口文件
│   ├── subsystem/               # 自我意识子系统
│   │   ├── enhanced_self_awareness_subsystem.py  # 增强版自我意识子系统
│   │   └── self_awareness_interfaces.py          # 自我意识接口
│   ├── modules/                 # 核心模块
│   │   ├── enhanced_self_identification_module.py      # 增强版自我识别模块
│   │   ├── enhanced_multimodal_perception_module.py    # 增强版多模态感知模块
│   │   └── enhanced_cognitive_processing_module.py     # 增强版认知处理模块
│   ├── enhancement/             # 第四层增强
│   │   └── fourth_layer_enhancement.py   # 第四层增强实现
│   └── monitoring/              # 系统监控
│       ├── README.md            # 监控模块概述
│       └── system_monitor.py    # 系统监控实现
├── tests/                       # 测试代码
│   ├── test_self_awareness_system.py  # 自我意识系统测试
│   └── test_system_monitor.py          # 系统监控测试
└── examples/                    # 示例代码
    ├── self_awareness_example.py        # 自我意识系统示例
    └── system_monitor_example.py       # 系统监控示例
```

## 🤝 贡献指南

我们欢迎各种形式的贡献，包括但不限于：

- 提交Bug报告和功能请求
- 改进文档
- 提交代码改进
- 分享使用经验和案例

请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [ACT-R](https://act-r.psy.cmu.edu/) 认知架构框架
- [LIDA](https://github.com/indylab/lida) 意识架构框架
- [LangChain](https://github.com/langchain-ai/langchain) 大语言模型应用框架
- [BabyAGI](https://github.com/yoheinakajima/babyagi) 自主AI代理框架
- [CLIP](https://github.com/openai/CLIP) 视觉-语言模型
- [Whisper](https://github.com/openai/whisper) 语音识别模型

## 📞 联系方式

- 项目主页: https://github.com/yourusername/self-awareness-enhancement
- 问题反馈: https://github.com/yourusername/self-awareness-enhancement/issues
- 邮箱: 869372447@qq.com

---

**注意**: 本项目仅用于研究和教育目的，请勿用于非法用途。使用本项目时请遵守相关法律法规和开源协议。
