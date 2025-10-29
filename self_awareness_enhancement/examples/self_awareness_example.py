"""
自我意识系统示例应用
展示如何使用自我意识系统
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import create_self_awareness_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_usage_example():
    """基本使用示例"""
    print("\n=== 基本使用示例 ===")
    
    # 配置
    config = {
        # 子系统配置
        "subsystem": {
            "enable_actr": True,
            "enable_lida": True,
            "enable_babyagi": True,
            "enable_langchain": True
        },
        
        # 模块配置
        "modules": {
            "enable_multimodal": True,
            "clip_model": "openai/clip-vit-base-patch32",
            "whisper_model": "openai/whisper-base"
        },
        
        # 第四层增强配置
        "enhancement": {
            "enable_multimodal_fusion": True,
            "enable_performance_optimization": True,
            "enable_security_enhancement": True
        },
        
        # 系统监控配置
        "enable_monitoring": False,  # 简化示例，关闭监控
        
        # 接口配置
        "enable_rest_api": False,  # 简化示例，关闭接口
        "enable_websocket": False
    }
    
    # 创建自我意识系统
    system = create_self_awareness_system(config)
    
    try:
        # 启动系统
        await system.start()
        
        # 处理文本输入
        text_input = {
            "type": "text",
            "content": "你好，请介绍一下你自己",
            "timestamp": time.time()
        }
        
        result = await system.process_input(text_input)
        print(f"文本输入处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 获取自我意识状态
        state = await system.get_self_awareness_state()
        print(f"\n自我意识状态: {json.dumps(state, indent=2, ensure_ascii=False)}")
        
        # 获取系统状态
        status = await system.get_status()
        print(f"\n系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
    finally:
        # 关闭系统
        await system.shutdown()


async def multimodal_example():
    """多模态处理示例"""
    print("\n=== 多模态处理示例 ===")
    
    # 配置
    config = {
        # 子系统配置
        "subsystem": {
            "enable_actr": True,
            "enable_lida": True,
            "enable_babyagi": True,
            "enable_langchain": True
        },
        
        # 模块配置
        "modules": {
            "enable_multimodal": True,
            "clip_model": "openai/clip-vit-base-patch32",
            "whisper_model": "openai/whisper-base"
        },
        
        # 第四层增强配置
        "enhancement": {
            "enable_multimodal_fusion": True,
            "enable_performance_optimization": True,
            "enable_security_enhancement": True
        },
        
        # 系统监控配置
        "enable_monitoring": False,
        
        # 接口配置
        "enable_rest_api": False,
        "enable_websocket": False
    }
    
    # 创建自我意识系统
    system = create_self_awareness_system(config)
    
    try:
        # 启动系统
        await system.start()
        
        # 处理图像输入（模拟）
        image_input = {
            "type": "image",
            "content": "https://example.com/image.jpg",  # 示例URL
            "timestamp": time.time()
        }
        
        result = await system.process_input(image_input)
        print(f"图像输入处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 处理音频输入（模拟）
        audio_input = {
            "type": "audio",
            "content": "https://example.com/audio.wav",  # 示例URL
            "timestamp": time.time()
        }
        
        result = await system.process_input(audio_input)
        print(f"\n音频输入处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 处理多模态输入（模拟）
        multimodal_input = {
            "type": "multimodal",
            "content": {
                "text": "请描述这张图片",
                "image": "https://example.com/image.jpg",
                "audio": "https://example.com/audio.wav"
            },
            "timestamp": time.time()
        }
        
        result = await system.process_input(multimodal_input)
        print(f"\n多模态输入处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    finally:
        # 关闭系统
        await system.shutdown()


async def monitoring_example():
    """系统监控示例"""
    print("\n=== 系统监控示例 ===")
    
    # 配置
    config = {
        # 子系统配置
        "subsystem": {
            "enable_actr": True,
            "enable_lida": True,
            "enable_babyagi": True,
            "enable_langchain": True
        },
        
        # 模块配置
        "modules": {
            "enable_multimodal": True,
            "clip_model": "openai/clip-vit-base-patch32",
            "whisper_model": "openai/whisper-base"
        },
        
        # 第四层增强配置
        "enhancement": {
            "enable_multimodal_fusion": True,
            "enable_performance_optimization": True,
            "enable_security_enhancement": True
        },
        
        # 系统监控配置
        "enable_monitoring": True,
        "monitor_interval": 2,  # 2秒间隔，加快示例速度
        "max_history_length": 100,
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 0,
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password",
        
        # 接口配置
        "enable_rest_api": False,
        "enable_websocket": False
    }
    
    # 创建自我意识系统
    system = create_self_awareness_system(config)
    
    try:
        # 启动系统
        await system.start()
        
        # 运行一段时间，收集监控数据
        print("收集监控数据...")
        await asyncio.sleep(10)
        
        # 生成性能报告
        report = await system.generate_performance_report()
        print(f"\n性能报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
        
        # 优化性能
        optimization = await system.optimize_performance()
        print(f"\n优化结果: {json.dumps(optimization, indent=2, ensure_ascii=False)}")
        
    finally:
        # 关闭系统
        await system.shutdown()


async def callback_example():
    """回调函数示例"""
    print("\n=== 回调函数示例 ===")
    
    # 配置
    config = {
        # 子系统配置
        "subsystem": {
            "enable_actr": True,
            "enable_lida": True,
            "enable_babyagi": True,
            "enable_langchain": True
        },
        
        # 模块配置
        "modules": {
            "enable_multimodal": True,
            "clip_model": "openai/clip-vit-base-patch32",
            "whisper_model": "openai/whisper-base"
        },
        
        # 第四层增强配置
        "enhancement": {
            "enable_multimodal_fusion": True,
            "enable_performance_optimization": True,
            "enable_security_enhancement": True
        },
        
        # 系统监控配置
        "enable_monitoring": False,
        
        # 接口配置
        "enable_rest_api": False,
        "enable_websocket": False
    }
    
    # 创建自我意识系统
    system = create_self_awareness_system(config)
    
    # 定义回调函数
    async def self_identification_callback(data: Dict[str, Any]):
        print(f"自我识别回调: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    async def multimodal_perception_callback(data: Dict[str, Any]):
        print(f"多模态感知回调: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    async def cognitive_processing_callback(data: Dict[str, Any]):
        print(f"认知处理回调: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        # 启动系统
        await system.start()
        
        # 注册回调函数
        await system.register_callback("self_identification", self_identification_callback)
        await system.register_callback("multimodal_perception", multimodal_perception_callback)
        await system.register_callback("cognitive_processing", cognitive_processing_callback)
        
        # 处理输入，触发回调
        input_data = {
            "type": "text",
            "content": "请进行自我识别",
            "timestamp": time.time()
        }
        
        result = await system.process_input(input_data)
        print(f"处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 等待回调执行
        await asyncio.sleep(2)
        
    finally:
        # 关闭系统
        await system.shutdown()


async def interface_example():
    """接口示例"""
    print("\n=== 接口示例 ===")
    
    # 配置
    config = {
        # 子系统配置
        "subsystem": {
            "enable_actr": True,
            "enable_lida": True,
            "enable_babyagi": True,
            "enable_langchain": True
        },
        
        # 模块配置
        "modules": {
            "enable_multimodal": True,
            "clip_model": "openai/clip-vit-base-patch32",
            "whisper_model": "openai/whisper-base"
        },
        
        # 第四层增强配置
        "enhancement": {
            "enable_multimodal_fusion": True,
            "enable_performance_optimization": True,
            "enable_security_enhancement": True
        },
        
        # 系统监控配置
        "enable_monitoring": False,
        
        # 接口配置
        "enable_rest_api": True,
        "rest_api_host": "0.0.0.0",
        "rest_api_port": 8000,
        "enable_websocket": True,
        "websocket_host": "0.0.0.0",
        "websocket_port": 8001
    }
    
    # 创建自我意识系统
    system = create_self_awareness_system(config)
    
    try:
        # 启动系统
        await system.start()
        
        # 获取接口
        rest_api = system.get_interface("rest_api")
        websocket = system.get_interface("websocket")
        
        if rest_api:
            print(f"REST API接口已启动，地址: http://{config['rest_api_host']}:{config['rest_api_port']}")
        
        if websocket:
            print(f"WebSocket接口已启动，地址: ws://{config['websocket_host']}:{config['websocket_port']}")
        
        # 运行一段时间
        print("接口运行中，可以通过HTTP请求或WebSocket连接进行交互...")
        await asyncio.sleep(10)
        
    finally:
        # 关闭系统
        await system.shutdown()


async def main():
    """主函数"""
    print("自我意识系统示例应用")
    
    # 运行各种示例
    await basic_usage_example()
    await multimodal_example()
    await monitoring_example()
    await callback_example()
    await interface_example()
    
    print("\n所有示例运行完成")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())