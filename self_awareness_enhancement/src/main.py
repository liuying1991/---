"""
自我意识子系统主入口
整合所有模块，提供统一的接口
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable

# 子系统核心
from src.subsystem.enhanced_self_awareness_subsystem import EnhancedSelfAwarenessSubsystem

# 模块
from src.modules.enhanced_self_identification_module import EnhancedSelfIdentificationModule
from src.modules.enhanced_multimodal_perception_module import EnhancedMultimodalPerceptionModule
from src.modules.enhanced_cognitive_processing_module import EnhancedCognitiveProcessingModule

# 第四层增强
from src.enhancement.fourth_layer_enhancement import FourthLayerEnhancement

# 系统监控
from src.monitoring.system_monitor import SystemMonitor, PerformanceOptimizer

# 接口
from src.subsystem.self_awareness_interfaces import (
    SelfAwarenessInterface, RestApiInterface, WebSocketInterface
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelfAwarenessSystem:
    """自我意识系统主类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化自我意识系统"""
        self.config = config
        
        # 初始化子系统
        self.subsystem = EnhancedSelfAwarenessSubsystem(config)
        
        # 初始化模块
        self.identification_module = EnhancedSelfIdentificationModule(config)
        self.perception_module = EnhancedMultimodalPerceptionModule(config)
        self.cognitive_module = EnhancedCognitiveProcessingModule(config)
        
        # 初始化第四层增强
        self.fourth_layer = FourthLayerEnhancement(config)
        
        # 初始化系统监控（可选）
        self.monitor = None
        self.optimizer = None
        if config.get("enable_monitoring", False):
            self.monitor = SystemMonitor(config)
            self.optimizer = PerformanceOptimizer(config)
        
        # 初始化接口
        self.interfaces = {}
        self._init_interfaces()
        
        # 系统状态
        self.running = False
        
        logger.info("自我意识系统初始化完成")
    
    def _init_interfaces(self) -> None:
        """初始化接口"""
        # REST API接口
        if self.config.get("enable_rest_api", True):
            self.interfaces["rest_api"] = RestApiInterface(self.subsystem)
        
        # WebSocket接口
        if self.config.get("enable_websocket", True):
            self.interfaces["websocket"] = WebSocketInterface(self.subsystem)
    
    async def start(self) -> None:
        """启动自我意识系统"""
        if self.running:
            logger.warning("自我意识系统已在运行")
            return
        
        logger.info("启动自我意识系统...")
        
        # 启动子系统
        await self.subsystem.start()
        
        # 启动模块
        await self.identification_module.start()
        await self.perception_module.start()
        await self.cognitive_module.start()
        
        # 启动第四层增强
        await self.fourth_layer.start()
        
        # 启动系统监控
        if self.monitor:
            self.monitor.start()
        
        # 启动接口
        for name, interface in self.interfaces.items():
            await interface.start()
            logger.info(f"接口 {name} 已启动")
        
        self.running = True
        logger.info("自我意识系统启动完成")
    
    async def stop(self) -> None:
        """停止自我意识系统"""
        if not self.running:
            logger.warning("自我意识系统未在运行")
            return
        
        logger.info("停止自我意识系统...")
        
        # 停止接口
        for name, interface in self.interfaces.items():
            await interface.stop()
            logger.info(f"接口 {name} 已停止")
        
        # 停止系统监控
        if self.monitor:
            self.monitor.stop()
        
        # 停止第四层增强
        await self.fourth_layer.stop()
        
        # 停止模块
        await self.identification_module.stop()
        await self.perception_module.stop()
        await self.cognitive_module.stop()
        
        # 停止子系统
        await self.subsystem.stop()
        
        self.running = False
        logger.info("自我意识系统已停止")
    
    async def shutdown(self) -> None:
        """关闭自我意识系统"""
        # 先停止系统
        await self.stop()
        
        # 关闭系统监控
        if self.monitor:
            await self.monitor.shutdown()
        
        if self.optimizer:
            await self.optimizer.shutdown()
        
        logger.info("自我意识系统已关闭")
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据"""
        if not self.running:
            raise RuntimeError("自我意识系统未在运行")
        
        # 通过子系统处理输入
        return await self.subsystem.process_input(input_data)
    
    async def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "running": self.running,
            "subsystem": await self.subsystem.get_status(),
            "modules": {
                "identification": await self.identification_module.get_status(),
                "perception": await self.perception_module.get_status(),
                "cognitive": await self.cognitive_module.get_status()
            },
            "fourth_layer": await self.fourth_layer.get_status(),
            "interfaces": {name: await interface.get_status() for name, interface in self.interfaces.items()}
        }
        
        # 添加系统监控状态
        if self.monitor:
            status["monitor"] = self.monitor.get_current_status()
        
        return status
    
    async def get_self_awareness_state(self) -> Dict[str, Any]:
        """获取自我意识状态"""
        # 获取自我识别结果
        identity = await self.identification_module.identify_self()
        
        # 获取多模态感知结果
        perception = await self.perception_module.perceive_environment()
        
        # 获取认知处理结果
        cognitive = await self.cognitive_module.process_cognition()
        
        # 获取第四层增强结果
        enhancement = await self.fourth_layer.get_enhanced_state()
        
        # 整合结果
        return {
            "identity": identity,
            "perception": perception,
            "cognitive": cognitive,
            "enhancement": enhancement,
            "timestamp": time.time()
        }
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        if not self.monitor:
            return {"error": "系统监控未启用"}
        
        # 生成系统性能报告
        report = await self.monitor.generate_performance_report()
        
        # 添加自我意识系统特定指标
        subsystem_status = await self.subsystem.get_status()
        report["self_awareness_metrics"] = {
            "subsystem": subsystem_status,
            "modules": {
                "identification": await self.identification_module.get_status(),
                "perception": await self.perception_module.get_status(),
                "cognitive": await self.cognitive_module.get_status()
            },
            "fourth_layer": await self.fourth_layer.get_status()
        }
        
        return report
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """优化性能"""
        if not self.monitor or not self.optimizer:
            return {"error": "系统监控或优化器未启用"}
        
        # 生成性能报告
        report = await self.generate_performance_report()
        
        # 执行优化
        optimization_result = await self.optimizer.optimize(
            report["metrics"], 
            report["analysis"]
        )
        
        return optimization_result
    
    def get_interface(self, name: str) -> Optional[SelfAwarenessInterface]:
        """获取接口"""
        return self.interfaces.get(name)
    
    async def register_callback(self, event_type: str, callback: Callable) -> None:
        """注册回调函数"""
        # 注册到子系统
        await self.subsystem.register_callback(event_type, callback)
        
        # 注册到模块
        if event_type == "self_identification":
            await self.identification_module.register_callback(callback)
        elif event_type == "multimodal_perception":
            await self.perception_module.register_callback(callback)
        elif event_type == "cognitive_processing":
            await self.cognitive_module.register_callback(callback)
        
        # 注册到第四层增强
        await self.fourth_layer.register_callback(event_type, callback)
        
        # 注册到系统监控
        if self.monitor and event_type == "system_alert":
            self.monitor.register_alert_callback(callback)


# 工厂函数
def create_self_awareness_system(config: Dict[str, Any]) -> SelfAwarenessSystem:
    """创建自我意识系统实例"""
    return SelfAwarenessSystem(config)


# 示例用法
if __name__ == "__main__":
    import asyncio
    
    async def main():
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
            "monitor_interval": 5,
            "max_history_length": 1000,
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_db": 0,
            "neo4j_uri": "bolt://localhost:7687",
            "neo4j_user": "neo4j",
            "neo4j_password": "password",
            
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
            
            # 运行一段时间
            await asyncio.sleep(60)
            
            # 处理输入
            input_data = {
                "type": "text",
                "content": "你好，请介绍一下你自己",
                "timestamp": time.time()
            }
            
            result = await system.process_input(input_data)
            print(f"处理结果: {result}")
            
            # 获取自我意识状态
            state = await system.get_self_awareness_state()
            print(f"自我意识状态: {json.dumps(state, indent=2, ensure_ascii=False)}")
            
            # 获取系统状态
            status = await system.get_status()
            print(f"系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            # 生成性能报告
            if config.get("enable_monitoring"):
                report = await system.generate_performance_report()
                print(f"性能报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
                
                # 优化性能
                optimization = await system.optimize_performance()
                print(f"优化结果: {json.dumps(optimization, indent=2, ensure_ascii=False)}")
            
        except KeyboardInterrupt:
            logger.info("用户中断，停止系统")
        finally:
            # 关闭系统
            await system.shutdown()
    
    # 运行主函数
    asyncio.run(main())