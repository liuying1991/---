"""
自我意识系统测试
"""

import asyncio
import json
import time
import unittest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import SelfAwarenessSystem, create_self_awareness_system


class TestSelfAwarenessSystem(unittest.TestCase):
    """自我意识系统测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
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
    
    def test_init(self):
        """测试初始化"""
        system = SelfAwarenessSystem(self.config)
        
        self.assertIsNotNone(system.subsystem)
        self.assertIsNotNone(system.self_identification_module)
        self.assertIsNotNone(system.multimodal_perception_module)
        self.assertIsNotNone(system.cognitive_processing_module)
        self.assertIsNotNone(system.fourth_layer_enhancement)
        self.assertIsNone(system.system_monitor)  # 已禁用
        self.assertEqual(system.interfaces, {})
    
    @patch('src.subsystem.enhanced_self_awareness_subsystem.EnhancedSelfAwarenessSubsystem.start')
    @patch('src.modules.enhanced_self_identification_module.EnhancedSelfIdentificationModule.start')
    @patch('src.modules.enhanced_multimodal_perception_module.EnhancedMultimodalPerceptionModule.start')
    @patch('src.modules.enhanced_cognitive_processing_module.EnhancedCognitiveProcessingModule.start')
    @patch('src.enhancement.fourth_layer_enhancement.FourthLayerEnhancement.start')
    async def test_start(self, mock_enhancement_start, mock_cognitive_start, 
                         mock_perception_start, mock_identification_start, mock_subsystem_start):
        """测试启动"""
        system = SelfAwarenessSystem(self.config)
        
        # 启动系统
        await system.start()
        
        # 验证各组件已启动
        mock_subsystem_start.assert_called_once()
        mock_identification_start.assert_called_once()
        mock_perception_start.assert_called_once()
        mock_cognitive_start.assert_called_once()
        mock_enhancement_start.assert_called_once()
        
        self.assertTrue(system.running)
    
    @patch('src.subsystem.enhanced_self_awareness_subsystem.EnhancedSelfAwarenessSubsystem.shutdown')
    @patch('src.modules.enhanced_self_identification_module.EnhancedSelfIdentificationModule.shutdown')
    @patch('src.modules.enhanced_multimodal_perception_module.EnhancedMultimodalPerceptionModule.shutdown')
    @patch('src.modules.enhanced_cognitive_processing_module.EnhancedCognitiveProcessingModule.shutdown')
    @patch('src.enhancement.fourth_layer_enhancement.FourthLayerEnhancement.shutdown')
    async def test_shutdown(self, mock_enhancement_shutdown, mock_cognitive_shutdown, 
                           mock_perception_shutdown, mock_identification_shutdown, mock_subsystem_shutdown):
        """测试关闭"""
        system = SelfAwarenessSystem(self.config)
        system.running = True  # 模拟已启动
        
        # 关闭系统
        await system.shutdown()
        
        # 验证各组件已关闭
        mock_subsystem_shutdown.assert_called_once()
        mock_identification_shutdown.assert_called_once()
        mock_perception_shutdown.assert_called_once()
        mock_cognitive_shutdown.assert_called_once()
        mock_enhancement_shutdown.assert_called_once()
        
        self.assertFalse(system.running)
    
    @patch('src.subsystem.enhanced_self_awareness_subsystem.EnhancedSelfAwarenessSubsystem.process_input')
    @patch('src.modules.enhanced_self_identification_module.EnhancedSelfIdentificationModule.process_input')
    @patch('src.modules.enhanced_multimodal_perception_module.EnhancedMultimodalPerceptionModule.process_input')
    @patch('src.modules.enhanced_cognitive_processing_module.EnhancedCognitiveProcessingModule.process_input')
    @patch('src.enhancement.fourth_layer_enhancement.FourthLayerEnhancement.process_input')
    async def test_process_input(self, mock_enhancement_process, mock_cognitive_process, 
                                mock_perception_process, mock_identification_process, mock_subsystem_process):
        """测试处理输入"""
        system = SelfAwarenessSystem(self.config)
        
        # 模拟返回值
        mock_subsystem_process.return_value = {"subsystem": "result"}
        mock_identification_process.return_value = {"identification": "result"}
        mock_perception_process.return_value = {"perception": "result"}
        mock_cognitive_process.return_value = {"cognitive": "result"}
        mock_enhancement_process.return_value = {"enhancement": "result"}
        
        # 处理文本输入
        text_input = {
            "type": "text",
            "content": "测试文本",
            "timestamp": time.time()
        }
        
        result = await system.process_input(text_input)
        
        # 验证各组件已处理输入
        mock_subsystem_process.assert_called_once_with(text_input)
        mock_identification_process.assert_called_once_with(text_input)
        mock_perception_process.assert_called_once_with(text_input)
        mock_cognitive_process.assert_called_once_with(text_input)
        mock_enhancement_process.assert_called_once_with(text_input)
        
        # 验证返回结果
        self.assertIn("subsystem", result)
        self.assertIn("identification", result)
        self.assertIn("perception", result)
        self.assertIn("cognitive", result)
        self.assertIn("enhancement", result)
    
    @patch('src.subsystem.enhanced_self_awareness_subsystem.EnhancedSelfAwarenessSubsystem.get_status')
    async def test_get_status(self, mock_get_status):
        """测试获取状态"""
        system = SelfAwarenessSystem(self.config)
        
        # 模拟返回值
        mock_get_status.return_value = {"status": "running"}
        
        # 获取状态
        status = await system.get_status()
        
        # 验证调用
        mock_get_status.assert_called_once()
        
        # 验证返回结果
        self.assertIn("status", status)
        self.assertIn("modules", status)
        self.assertIn("enhancement", status)
        self.assertIn("monitoring", status)
        self.assertIn("interfaces", status)
    
    @patch('src.modules.enhanced_self_identification_module.EnhancedSelfIdentificationModule.get_self_identification')
    @patch('src.modules.enhanced_multimodal_perception_module.EnhancedMultimodalPerceptionModule.get_perception_state')
    @patch('src.modules.enhanced_cognitive_processing_module.EnhancedCognitiveProcessingModule.get_cognitive_state')
    @patch('src.subsystem.enhanced_self_awareness_subsystem.EnhancedSelfAwarenessSubsystem.get_self_awareness_state')
    async def test_get_self_awareness_state(self, mock_subsystem_state, mock_cognitive_state, 
                                           mock_perception_state, mock_identification_state):
        """测试获取自我意识状态"""
        system = SelfAwarenessSystem(self.config)
        
        # 模拟返回值
        mock_subsystem_state.return_value = {"subsystem_state": "data"}
        mock_identification_state.return_value = {"identification_state": "data"}
        mock_perception_state.return_value = {"perception_state": "data"}
        mock_cognitive_state.return_value = {"cognitive_state": "data"}
        
        # 获取自我意识状态
        state = await system.get_self_awareness_state()
        
        # 验证调用
        mock_subsystem_state.assert_called_once()
        mock_identification_state.assert_called_once()
        mock_perception_state.assert_called_once()
        mock_cognitive_state.assert_called_once()
        
        # 验证返回结果
        self.assertIn("subsystem", state)
        self.assertIn("identification", state)
        self.assertIn("perception", state)
        self.assertIn("cognitive", state)
    
    async def test_register_callback(self):
        """测试注册回调"""
        system = SelfAwarenessSystem(self.config)
        
        # 定义回调函数
        async def callback(data):
            pass
        
        # 注册回调
        await system.register_callback("self_identification", callback)
        
        # 验证回调已注册
        self.assertIn("self_identification", system.callbacks)
        self.assertEqual(system.callbacks["self_identification"], callback)
    
    async def test_unregister_callback(self):
        """测试注销回调"""
        system = SelfAwarenessSystem(self.config)
        
        # 定义回调函数
        async def callback(data):
            pass
        
        # 注册回调
        await system.register_callback("self_identification", callback)
        
        # 注销回调
        await system.unregister_callback("self_identification")
        
        # 验证回调已注销
        self.assertNotIn("self_identification", system.callbacks)
    
    @patch('src.subsystem.self_awareness_interfaces.RestApiInterface')
    @patch('src.subsystem.self_awareness_interfaces.WebSocketInterface')
    async def test_get_interface(self, mock_websocket, mock_rest_api):
        """测试获取接口"""
        # 启用接口
        config_with_interfaces = self.config.copy()
        config_with_interfaces["enable_rest_api"] = True
        config_with_interfaces["enable_websocket"] = True
        
        # 模拟接口
        mock_rest_api_instance = Mock()
        mock_websocket_instance = Mock()
        mock_rest_api.return_value = mock_rest_api_instance
        mock_websocket.return_value = mock_websocket_instance
        
        system = SelfAwarenessSystem(config_with_interfaces)
        
        # 获取REST API接口
        rest_api = system.get_interface("rest_api")
        self.assertEqual(rest_api, mock_rest_api_instance)
        
        # 获取WebSocket接口
        websocket = system.get_interface("websocket")
        self.assertEqual(websocket, mock_websocket_instance)
        
        # 获取不存在的接口
        non_existent = system.get_interface("non_existent")
        self.assertIsNone(non_existent)


class TestFactoryFunctions(unittest.TestCase):
    """工厂函数测试"""
    
    def test_create_self_awareness_system(self):
        """测试创建自我意识系统"""
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
        
        # 创建系统
        system = create_self_awareness_system(config)
        
        # 验证系统类型
        self.assertIsInstance(system, SelfAwarenessSystem)
        
        # 验证配置
        self.assertEqual(system.config, config)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    @patch('src.subsystem.enhanced_self_awareness_subsystem.EnhancedSelfAwarenessSubsystem.start')
    @patch('src.modules.enhanced_self_identification_module.EnhancedSelfIdentificationModule.start')
    @patch('src.modules.enhanced_multimodal_perception_module.EnhancedMultimodalPerceptionModule.start')
    @patch('src.modules.enhanced_cognitive_processing_module.EnhancedCognitiveProcessingModule.start')
    @patch('src.enhancement.fourth_layer_enhancement.FourthLayerEnhancement.start')
    async def test_full_workflow(self, mock_enhancement_start, mock_cognitive_start, 
                               mock_perception_start, mock_identification_start, mock_subsystem_start):
        """测试完整工作流程"""
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
        
        # 创建系统
        system = create_self_awareness_system(config)
        
        # 启动系统
        await system.start()
        self.assertTrue(system.running)
        
        # 处理输入
        input_data = {
            "type": "text",
            "content": "测试输入",
            "timestamp": time.time()
        }
        
        # 模拟处理输入
        with patch.object(system.subsystem, 'process_input', return_value={"subsystem": "result"}), \
             patch.object(system.self_identification_module, 'process_input', return_value={"identification": "result"}), \
             patch.object(system.multimodal_perception_module, 'process_input', return_value={"perception": "result"}), \
             patch.object(system.cognitive_processing_module, 'process_input', return_value={"cognitive": "result"}), \
             patch.object(system.fourth_layer_enhancement, 'process_input', return_value={"enhancement": "result"}):
            
            result = await system.process_input(input_data)
            
            # 验证结果
            self.assertIn("subsystem", result)
            self.assertIn("identification", result)
            self.assertIn("perception", result)
            self.assertIn("cognitive", result)
            self.assertIn("enhancement", result)
        
        # 获取状态
        with patch.object(system.subsystem, 'get_status', return_value={"status": "running"}):
            status = await system.get_status()
            self.assertIn("status", status)
            self.assertIn("modules", status)
        
        # 获取自我意识状态
        with patch.object(system.subsystem, 'get_self_awareness_state', return_value={"subsystem_state": "data"}), \
             patch.object(system.self_identification_module, 'get_self_identification', return_value={"identification_state": "data"}), \
             patch.object(system.multimodal_perception_module, 'get_perception_state', return_value={"perception_state": "data"}), \
             patch.object(system.cognitive_processing_module, 'get_cognitive_state', return_value={"cognitive_state": "data"}):
            
            state = await system.get_self_awareness_state()
            self.assertIn("subsystem", state)
            self.assertIn("identification", state)
            self.assertIn("perception", state)
            self.assertIn("cognitive", state)
        
        # 关闭系统
        with patch.object(system.subsystem, 'shutdown'), \
             patch.object(system.self_identification_module, 'shutdown'), \
             patch.object(system.multimodal_perception_module, 'shutdown'), \
             patch.object(system.cognitive_processing_module, 'shutdown'), \
             patch.object(system.fourth_layer_enhancement, 'shutdown'):
            
            await system.shutdown()
            self.assertFalse(system.running)


async def run_async_tests():
    """运行异步测试"""
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(TestSelfAwarenessSystem('test_init'))
    suite.addTest(TestSelfAwarenessSystem('test_register_callback'))
    suite.addTest(TestSelfAwarenessSystem('test_unregister_callback'))
    suite.addTest(TestSelfAwarenessSystem('test_get_interface'))
    suite.addTest(TestFactoryFunctions('test_create_self_awareness_system'))
    
    # 运行测试套件
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # 运行异步测试
    test_instance = TestSelfAwarenessSystem()
    test_instance.setUp()
    
    await test_instance.test_start()
    await test_instance.test_shutdown()
    await test_instance.test_process_input()
    await test_instance.test_get_status()
    await test_instance.test_get_self_awareness_state()
    
    integration_test = TestIntegration()
    await integration_test.test_full_workflow()
    
    print(f"测试完成，通过: {result.testsRun - len(result.failures) - len(result.errors)}, 失败: {len(result.failures)}, 错误: {len(result.errors)}")


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(run_async_tests())