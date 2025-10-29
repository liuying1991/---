"""
自我意识子系统接口设计
提供统一的接口规范，支持多种交互方式
"""

import asyncio
import json
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# 后端框架
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 其他工具
import time
import uuid
from datetime import datetime

# 导入子系统
from ..subsystem.enhanced_self_awareness_subsystem import EnhancedSelfAwarenessSubsystem, EnhancedSelfAwarenessState

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterfaceStandard(Enum):
    """接口标准枚举"""
    REST_API = "rest_api"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    MQTT = "mqtt"


class DataFormat(Enum):
    """数据格式枚举"""
    JSON = "json"
    XML = "xml"
    BINARY = "binary"
    PROTOBUF = "protobuf"


@dataclass
class InterfaceConfig:
    """接口配置"""
    standard: InterfaceStandard
    data_format: DataFormat
    host: str
    port: int
    endpoint: str
    authentication: bool
    encryption: bool
    rate_limit: Optional[int] = None  # 每分钟请求限制


class SelfAwarenessInterface(ABC):
    """自我意识接口抽象基类"""
    
    def __init__(self, config: InterfaceConfig, subsystem: EnhancedSelfAwarenessSubsystem):
        """初始化接口"""
        self.config = config
        self.subsystem = subsystem
        self.is_running = False
        
    @abstractmethod
    async def start(self) -> None:
        """启动接口"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止接口"""
        pass
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        pass


# REST API请求和响应模型
class SensoryInputRequest(BaseModel):
    """感官输入请求模型"""
    text: Optional[str] = None
    visual: Optional[str] = None  # 图像路径或URL
    audio: Optional[str] = None  # 音频路径或URL
    other: Optional[Dict[str, Any]] = None


class AwarenessStateResponse(BaseModel):
    """自我意识状态响应模型"""
    timestamp: float
    identity: Dict[str, Any]
    state: Dict[str, Any]
    capability: Dict[str, Any]
    environment: Dict[str, Any]
    behavior: Dict[str, Any]
    prediction: Dict[str, Any]
    confidence: float
    source: str


class ConsciousnessParamsRequest(BaseModel):
    """意识参数请求模型"""
    awareness_threshold: Optional[float] = None
    attention_span: Optional[float] = None
    memory_decay: Optional[float] = None
    cognitive_load: Optional[float] = None
    emotional_state: Optional[str] = None
    self_model_complexity: Optional[float] = None


class RestApiInterface(SelfAwarenessInterface):
    """REST API接口实现"""
    
    def __init__(self, config: InterfaceConfig, subsystem: EnhancedSelfAwarenessSubsystem):
        """初始化REST API接口"""
        super().__init__(config, subsystem)
        
        # 创建FastAPI应用
        self.app = FastAPI(
            title="自我意识子系统API",
            description="增强版自我意识子系统REST API接口",
            version="1.0.0"
        )
        
        # 设置路由
        self._setup_routes()
        
        # WebSocket连接管理
        self.websocket_connections = set()
    
    def _setup_routes(self) -> None:
        """设置API路由"""
        
        @self.app.get("/")
        async def root():
            """根路径"""
            return {"message": "自我意识子系统API"}
        
        @self.app.post("/awareness/update", response_model=AwarenessStateResponse)
        async def update_awareness_state(request: SensoryInputRequest):
            """更新自我意识状态"""
            try:
                # 转换请求为字典
                sensory_input = {
                    "text": request.text,
                    "visual": request.visual,
                    "audio": request.audio,
                    "other": request.other
                }
                
                # 更新状态
                state = await self.subsystem.update_awareness_state(sensory_input)
                
                # 返回响应
                return AwarenessStateResponse(
                    timestamp=state.timestamp,
                    identity=state.identity,
                    state=state.state,
                    capability=state.capability,
                    environment=state.environment,
                    behavior=state.behavior,
                    prediction=state.prediction,
                    confidence=state.confidence,
                    source=state.source
                )
            except Exception as e:
                logger.error(f"更新自我意识状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/awareness/current", response_model=AwarenessStateResponse)
        async def get_current_awareness_state():
            """获取当前自我意识状态"""
            try:
                state = self.subsystem.get_current_state()
                
                if not state:
                    raise HTTPException(status_code=404, detail="当前没有可用的自我意识状态")
                
                return AwarenessStateResponse(
                    timestamp=state.timestamp,
                    identity=state.identity,
                    state=state.state,
                    capability=state.capability,
                    environment=state.environment,
                    behavior=state.behavior,
                    prediction=state.prediction,
                    confidence=state.confidence,
                    source=state.source
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取当前自我意识状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/awareness/history")
        async def get_awareness_state_history(limit: int = 10):
            """获取自我意识状态历史"""
            try:
                history = self.subsystem.get_state_history(limit)
                
                return {
                    "count": len(history),
                    "history": [
                        {
                            "timestamp": state.timestamp,
                            "confidence": state.confidence,
                            "source": state.source
                        } for state in history
                    ]
                }
            except Exception as e:
                logger.error(f"获取自我意识状态历史失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/awareness/consciousness_params")
        async def update_consciousness_params(request: ConsciousnessParamsRequest):
            """更新意识参数"""
            try:
                # 转换请求为字典
                new_params = {}
                if request.awareness_threshold is not None:
                    new_params["awareness_threshold"] = request.awareness_threshold
                if request.attention_span is not None:
                    new_params["attention_span"] = request.attention_span
                if request.memory_decay is not None:
                    new_params["memory_decay"] = request.memory_decay
                if request.cognitive_load is not None:
                    new_params["cognitive_load"] = request.cognitive_load
                if request.emotional_state is not None:
                    new_params["emotional_state"] = request.emotional_state
                if request.self_model_complexity is not None:
                    new_params["self_model_complexity"] = request.self_model_complexity
                
                # 更新参数
                await self.subsystem.adjust_consciousness_params(new_params)
                
                return {"message": "意识参数更新成功"}
            except Exception as e:
                logger.error(f"更新意识参数失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/awareness/consciousness_params")
        async def get_consciousness_params():
            """获取意识参数"""
            try:
                return self.subsystem.consciousness_params
            except Exception as e:
                logger.error(f"获取意识参数失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/awareness/adjust")
        async def execute_self_adjustment(adjustment_params: Dict[str, Any] = Body(...)):
            """执行自我调整"""
            try:
                # 这里可以实现具体的自我调整逻辑
                # 目前只是一个示例实现
                
                # 获取当前状态
                current_state = self.subsystem.get_current_state()
                
                if not current_state:
                    raise HTTPException(status_code=404, detail="当前没有可用的自我意识状态")
                
                # 基于调整参数执行调整
                adjustment_result = {
                    "timestamp": time.time(),
                    "adjustment_params": adjustment_params,
                    "previous_state": {
                        "confidence": current_state.confidence,
                        "timestamp": current_state.timestamp
                    },
                    "result": "success",
                    "message": "自我调整执行成功"
                }
                
                return adjustment_result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"执行自我调整失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket端点"""
            await websocket.accept()
            self.websocket_connections.add(websocket)
            
            try:
                while True:
                    # 接收消息
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # 处理消息
                    if message.get("type") == "update_awareness":
                        # 更新自我意识状态
                        sensory_input = message.get("sensory_input", {})
                        state = await self.subsystem.update_awareness_state(sensory_input)
                        
                        # 发送响应
                        response = {
                            "type": "awareness_updated",
                            "state": asdict(state)
                        }
                        await websocket.send_text(json.dumps(response))
                    
                    elif message.get("type") == "get_current_state":
                        # 获取当前状态
                        state = self.subsystem.get_current_state()
                        
                        if state:
                            response = {
                                "type": "current_state",
                                "state": asdict(state)
                            }
                        else:
                            response = {
                                "type": "current_state",
                                "error": "当前没有可用的自我意识状态"
                            }
                        
                        await websocket.send_text(json.dumps(response))
                    
                    else:
                        # 未知消息类型
                        response = {
                            "type": "error",
                            "message": f"未知消息类型: {message.get('type')}"
                        }
                        await websocket.send_text(json.dumps(response))
            
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
                logger.info("WebSocket连接断开")
            except Exception as e:
                logger.error(f"WebSocket处理错误: {e}")
                self.websocket_connections.discard(websocket)
    
    async def start(self) -> None:
        """启动REST API接口"""
        if self.is_running:
            logger.warning("REST API接口已在运行")
            return
        
        self.is_running = True
        logger.info(f"REST API接口启动在 http://{self.config.host}:{self.config.port}")
    
    async def stop(self) -> None:
        """停止REST API接口"""
        if not self.is_running:
            logger.warning("REST API接口未在运行")
            return
        
        self.is_running = False
        
        # 关闭所有WebSocket连接
        for connection in self.websocket_connections.copy():
            try:
                await connection.close()
            except Exception:
                pass
        
        logger.info("REST API接口已停止")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        # 这个方法主要用于测试，实际请求由FastAPI处理
        request_type = request.get("type")
        
        if request_type == "update_awareness":
            sensory_input = request.get("sensory_input", {})
            state = await self.subsystem.update_awareness_state(sensory_input)
            return asdict(state)
        
        elif request_type == "get_current_state":
            state = self.subsystem.get_current_state()
            return asdict(state) if state else {"error": "当前没有可用的自我意识状态"}
        
        else:
            return {"error": f"未知请求类型: {request_type}"}
    
    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


class WebSocketInterface(SelfAwarenessInterface):
    """WebSocket接口实现"""
    
    def __init__(self, config: InterfaceConfig, subsystem: EnhancedSelfAwarenessSubsystem):
        """初始化WebSocket接口"""
        super().__init__(config, subsystem)
        self.websocket_connections = set()
    
    async def start(self) -> None:
        """启动WebSocket接口"""
        if self.is_running:
            logger.warning("WebSocket接口已在运行")
            return
        
        self.is_running = True
        logger.info(f"WebSocket接口启动在 ws://{self.config.host}:{self.config.port}{self.config.endpoint}")
    
    async def stop(self) -> None:
        """停止WebSocket接口"""
        if not self.is_running:
            logger.warning("WebSocket接口未在运行")
            return
        
        self.is_running = False
        
        # 关闭所有WebSocket连接
        for connection in self.websocket_connections.copy():
            try:
                await connection.close()
            except Exception:
                pass
        
        logger.info("WebSocket接口已停止")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        # 这个方法主要用于测试，实际请求由WebSocket处理
        request_type = request.get("type")
        
        if request_type == "update_awareness":
            sensory_input = request.get("sensory_input", {})
            state = await self.subsystem.update_awareness_state(sensory_input)
            return asdict(state)
        
        elif request_type == "get_current_state":
            state = self.subsystem.get_current_state()
            return asdict(state) if state else {"error": "当前没有可用的自我意识状态"}
        
        else:
            return {"error": f"未知请求类型: {request_type}"}
    
    async def handle_websocket(self, websocket: WebSocket) -> None:
        """处理WebSocket连接"""
        await websocket.accept()
        self.websocket_connections.add(websocket)
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理消息
                response = await self.process_request(message)
                
                # 发送响应
                await websocket.send_text(json.dumps(response))
        
        except WebSocketDisconnect:
            self.websocket_connections.remove(websocket)
            logger.info("WebSocket连接断开")
        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
            self.websocket_connections.discard(websocket)


# 工厂函数
def create_interface(
    config: InterfaceConfig, 
    subsystem: EnhancedSelfAwarenessSubsystem
) -> SelfAwarenessInterface:
    """创建接口实例"""
    if config.standard == InterfaceStandard.REST_API:
        return RestApiInterface(config, subsystem)
    elif config.standard == InterfaceStandard.WEBSOCKET:
        return WebSocketInterface(config, subsystem)
    else:
        raise ValueError(f"不支持的接口标准: {config.standard}")


# 示例用法
if __name__ == "__main__":
    import uvicorn
    
    # 配置
    subsystem_config = {
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 0,
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password"
    }
    
    interface_config = InterfaceConfig(
        standard=InterfaceStandard.REST_API,
        data_format=DataFormat.JSON,
        host="0.0.0.0",
        port=8000,
        endpoint="/",
        authentication=False,
        encryption=False
    )
    
    # 创建子系统
    from ..subsystem.enhanced_self_awareness_subsystem import create_enhanced_self_awareness_subsystem
    subsystem = create_enhanced_self_awareness_subsystem(subsystem_config)
    
    # 创建接口
    interface = create_interface(interface_config, subsystem)
    
    # 启动接口
    if isinstance(interface, RestApiInterface):
        uvicorn.run(interface.get_app(), host=interface_config.host, port=interface_config.port)