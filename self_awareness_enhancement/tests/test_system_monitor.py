"""
系统监控与性能优化模块的测试
"""

import asyncio
import json
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.monitoring.system_monitor import (
    SystemMonitor, PerformanceOptimizer, MetricType, AlertLevel,
    MetricData, Alert, PerformanceReport, create_system_monitor,
    create_performance_optimizer
)


class TestSystemMonitor(unittest.TestCase):
    """系统监控器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            "monitor_interval": 0.1,  # 0.1秒间隔，加快测试速度
            "max_history_length": 10,
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_db": 0,
            "neo4j_uri": "bolt://localhost:7687",
            "neo4j_user": "neo4j",
            "neo4j_password": "password"
        }
        
        # Mock Redis和Neo4j连接
        self.redis_mock = Mock()
        self.neo4j_driver_mock = Mock()
        
        # Mock psutil和GPUtil
        self.psutil_mock = Mock()
        self.gputil_mock = Mock()
        
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_initialization(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试初始化"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        mock_neo4j.return_value = self.neo4j_driver_mock
        
        # 创建监控器
        monitor = SystemMonitor(self.config)
        
        # 验证初始化
        self.assertEqual(monitor.monitor_interval, 0.1)
        self.assertEqual(monitor.max_history_length, 10)
        self.assertFalse(monitor.monitoring)
        self.assertEqual(len(monitor.metrics), len(MetricType))
        self.assertEqual(len(monitor.alerts), 0)
        self.assertEqual(len(monitor.alert_rules), len(MetricType))
        
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_start_stop(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试启动和停止"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        mock_neo4j.return_value = self.neo4j_driver_mock
        
        # 创建监控器
        monitor = SystemMonitor(self.config)
        
        # 测试启动
        monitor.start()
        self.assertTrue(monitor.monitoring)
        self.assertIsNotNone(monitor.monitor_thread)
        
        # 测试停止
        monitor.stop()
        self.assertFalse(monitor.monitoring)
        
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_collect_metrics(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试指标收集"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        mock_neo4j.return_value = self.neo4j_driver_mock
        
        # Mock psutil返回值
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_partition = Mock()
        mock_partition.mountpoint = "/test"
        mock_psutil.disk_partitions.return_value = [mock_partition]
        
        mock_usage = Mock()
        mock_usage.used = 5000
        mock_usage.total = 10000
        mock_psutil.disk_usage.return_value = mock_usage
        
        mock_net_io = Mock()
        mock_net_io.bytes_sent = 1000
        mock_net_io.bytes_recv = 2000
        mock_psutil.net_io_counters.return_value = mock_net_io
        
        # Mock GPUtil返回值
        mock_gpu = Mock()
        mock_gpu.load = 0.7
        mock_gpu.id = 0
        mock_gputil.getGPUs.return_value = [mock_gpu]
        
        # 创建监控器
        monitor = SystemMonitor(self.config)
        
        # 收集指标
        monitor._collect_metrics()
        
        # 验证指标
        self.assertEqual(len(monitor.metrics[MetricType.CPU]), 1)
        self.assertEqual(monitor.metrics[MetricType.CPU][0].value, 50.0)
        
        self.assertEqual(len(monitor.metrics[MetricType.MEMORY]), 1)
        self.assertEqual(monitor.metrics[MetricType.MEMORY][0].value, 60.0)
        
        self.assertEqual(len(monitor.metrics[MetricType.DISK]), 1)
        self.assertEqual(monitor.metrics[MetricType.DISK][0].value, 50.0)  # 5000/10000*100
        
        self.assertEqual(len(monitor.metrics[MetricType.GPU]), 1)
        self.assertEqual(monitor.metrics[MetricType.GPU][0].value, 70.0)  # 0.7*100
        
        self.assertEqual(len(monitor.metrics[MetricType.NETWORK]), 1)
        self.assertEqual(monitor.metrics[MetricType.NETWORK][0].value, 3.0)  # (1000+2000)/1024
        
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_alerts(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试告警"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        mock_neo4j.return_value = self.neo4j_driver_mock
        
        # 创建监控器
        monitor = SystemMonitor(self.config)
        
        # 添加高CPU使用率指标，触发告警
        monitor._add_metric(MetricType.CPU, 90.0, "%", time.time(), "test")
        
        # 检查告警
        monitor._check_alerts()
        
        # 验证告警
        self.assertEqual(len(monitor.alerts), 1)
        self.assertEqual(monitor.alerts[0].metric_type, MetricType.CPU)
        self.assertEqual(monitor.alerts[0].alert_level, AlertLevel.ERROR)
        
        # 添加告警回调
        callback_called = False
        alert_received = None
        
        def test_callback(alert):
            nonlocal callback_called, alert_received
            callback_called = True
            alert_received = alert
        
        monitor.register_alert_callback(test_callback)
        
        # 添加更高CPU使用率指标，触发新告警
        monitor._add_metric(MetricType.CPU, 95.0, "%", time.time(), "test")
        monitor._check_alerts()
        
        # 验证回调被调用
        self.assertTrue(callback_called)
        self.assertEqual(alert_received.metric_type, MetricType.CPU)
        self.assertEqual(alert_received.alert_level, AlertLevel.CRITICAL)
        
        # 测试解决告警
        alert_id = str(id(monitor.alerts[0]))
        result = monitor.resolve_alert(alert_id)
        self.assertTrue(result)
        self.assertTrue(monitor.alerts[0].resolved)
        
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_get_metrics(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试获取指标"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        mock_neo4j.return_value = self.neo4j_driver_mock
        
        # 创建监控器
        monitor = SystemMonitor(self.config)
        
        # 添加指标
        for i in range(5):
            monitor._add_metric(MetricType.CPU, float(i * 10), "%", time.time(), "test")
        
        # 获取所有指标
        all_metrics = monitor.get_metrics()
        self.assertEqual(len(all_metrics[MetricType.CPU]), 5)
        
        # 获取特定类型指标
        cpu_metrics = monitor.get_metrics(MetricType.CPU)
        self.assertEqual(len(cpu_metrics[MetricType.CPU]), 5)
        
        # 限制数量
        limited_metrics = monitor.get_metrics(MetricType.CPU, limit=3)
        self.assertEqual(len(limited_metrics[MetricType.CPU]), 3)
        
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_get_alerts(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试获取告警"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        mock_neo4j.return_value = self.neo4j_driver_mock
        
        # 创建监控器
        monitor = SystemMonitor(self.config)
        
        # 添加告警
        alert1 = Alert(AlertLevel.WARNING, MetricType.CPU, "CPU警告", time.time())
        alert2 = Alert(AlertLevel.ERROR, MetricType.MEMORY, "内存错误", time.time())
        alert2.resolved = True
        
        monitor.alerts = [alert1, alert2]
        
        # 获取所有告警
        all_alerts = monitor.get_alerts()
        self.assertEqual(len(all_alerts), 2)
        
        # 获取未解决告警
        unresolved_alerts = monitor.get_alerts(resolved=False)
        self.assertEqual(len(unresolved_alerts), 1)
        self.assertEqual(unresolved_alerts[0].metric_type, MetricType.CPU)
        
        # 获取已解决告警
        resolved_alerts = monitor.get_alerts(resolved=True)
        self.assertEqual(len(resolved_alerts), 1)
        self.assertEqual(resolved_alerts[0].metric_type, MetricType.MEMORY)
        
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_get_current_status(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试获取当前状态"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        mock_neo4j.return_value = self.neo4j_driver_mock
        
        # 创建监控器
        monitor = SystemMonitor(self.config)
        
        # 添加指标
        monitor._add_metric(MetricType.CPU, 50.0, "%", time.time(), "test")
        monitor._add_metric(MetricType.MEMORY, 60.0, "%", time.time(), "test")
        
        # 添加告警
        alert1 = Alert(AlertLevel.WARNING, MetricType.CPU, "CPU警告", time.time())
        alert2 = Alert(AlertLevel.ERROR, MetricType.MEMORY, "内存错误", time.time())
        
        monitor.alerts = [alert1, alert2]
        
        # 获取当前状态
        status = monitor.get_current_status()
        
        # 验证状态
        self.assertIn("cpu", status)
        self.assertEqual(status["cpu"]["value"], 50.0)
        self.assertEqual(status["cpu"]["unit"], "%")
        
        self.assertIn("memory", status)
        self.assertEqual(status["memory"]["value"], 60.0)
        self.assertEqual(status["memory"]["unit"], "%")
        
        self.assertIn("alerts", status)
        self.assertEqual(status["alerts"]["total"], 2)
        self.assertEqual(status["alerts"]["unresolved"], 2)
        self.assertEqual(status["alerts"]["warning"], 1)
        self.assertEqual(status["alerts"]["error"], 1)


class TestPerformanceOptimizer(unittest.TestCase):
    """性能优化器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_db": 0
        }
        
        # Mock Redis连接
        self.redis_mock = Mock()
        
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_initialization(self, mock_llm, mock_redis):
        """测试初始化"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        
        # 创建优化器
        optimizer = PerformanceOptimizer(self.config)
        
        # 验证初始化
        self.assertEqual(len(optimizer.optimization_history), 0)
        self.assertIsNotNone(optimizer.llm)
        self.assertIsNotNone(optimizer.redis_client)
        
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    async def test_identify_bottlenecks(self, mock_llm, mock_redis):
        """测试识别瓶颈"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        
        # 创建优化器
        optimizer = PerformanceOptimizer(self.config)
        
        # 创建指标数据
        metrics = {
            MetricType.CPU: [MetricData(MetricType.CPU, 80.0, "%", time.time(), "test")],
            MetricType.MEMORY: [MetricData(MetricType.MEMORY, 60.0, "%", time.time(), "test")],
            MetricType.DISK: [MetricData(MetricType.DISK, 90.0, "%", time.time(), "test")]
        }
        
        # 创建分析数据
        analysis = {
            "cpu": {
                "mean": 80.0,
                "p95": 85.0
            },
            "memory": {
                "mean": 60.0,
                "p95": 65.0
            },
            "disk": {
                "mean": 90.0,
                "p95": 95.0
            }
        }
        
        # 识别瓶颈
        bottlenecks = await optimizer._identify_bottlenecks(metrics, analysis)
        
        # 验证瓶颈
        self.assertEqual(len(bottlenecks), 2)  # CPU和Disk
        
        # 验证CPU瓶颈
        cpu_bottleneck = next((b for b in bottlenecks if b["type"] == "cpu"), None)
        self.assertIsNotNone(cpu_bottleneck)
        self.assertEqual(cpu_bottleneck["severity"], "medium")
        
        # 验证磁盘瓶颈
        disk_bottleneck = next((b for b in bottlenecks if b["type"] == "disk"), None)
        self.assertIsNotNone(disk_bottleneck)
        self.assertEqual(disk_bottleneck["severity"], "high")
        
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    async def test_generate_optimization_strategies(self, mock_llm, mock_redis):
        """测试生成优化策略"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        
        # Mock LLM响应
        mock_llm_instance = Mock()
        mock_llm_instance.ainvoke.return_value = Mock(content="优化策略内容")
        mock_llm.return_value = mock_llm_instance
        
        # 创建优化器
        optimizer = PerformanceOptimizer(self.config)
        
        # 创建瓶颈
        bottlenecks = [
            {
                "type": "cpu",
                "severity": "high",
                "description": "CPU使用率过高"
            }
        ]
        
        # 生成优化策略
        strategies = await optimizer._generate_optimization_strategies(bottlenecks)
        
        # 验证策略
        self.assertEqual(len(strategies), 1)
        self.assertEqual(strategies[0]["bottlenecks"], bottlenecks)
        self.assertEqual(strategies[0]["strategy"], "优化策略内容")
        
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    async def test_implement_optimizations(self, mock_llm, mock_redis):
        """测试实施优化"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        
        # 创建优化器
        optimizer = PerformanceOptimizer(self.config)
        
        # 创建策略
        strategies = [
            {
                "bottlenecks": [{"type": "cpu"}],
                "strategy": "优化CPU使用率",
                "timestamp": time.time()
            }
        ]
        
        # 实施优化
        results = await optimizer._implement_optimizations(strategies)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["strategy"], strategies[0])
        self.assertEqual(results[0]["result"], "success")
        self.assertIn("metrics_improvement", results[0])
        
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    async def test_optimize(self, mock_llm, mock_redis):
        """测试优化流程"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        
        # Mock LLM响应
        mock_llm_instance = Mock()
        mock_llm_instance.ainvoke.return_value = Mock(content="优化策略内容")
        mock_llm.return_value = mock_llm_instance
        
        # 创建优化器
        optimizer = PerformanceOptimizer(self.config)
        
        # 创建指标数据
        metrics = {
            MetricType.CPU: [MetricData(MetricType.CPU, 80.0, "%", time.time(), "test")],
            MetricType.MEMORY: [MetricData(MetricType.MEMORY, 60.0, "%", time.time(), "test")]
        }
        
        # 创建分析数据
        analysis = {
            "cpu": {
                "mean": 80.0,
                "p95": 85.0
            },
            "memory": {
                "mean": 60.0,
                "p95": 65.0
            }
        }
        
        # 执行优化
        result = await optimizer.optimize(metrics, analysis)
        
        # 验证结果
        self.assertIn("timestamp", result)
        self.assertIn("bottlenecks", result)
        self.assertIn("strategies", result)
        self.assertIn("results", result)
        
        # 验证历史记录
        self.assertEqual(len(optimizer.optimization_history), 1)
        self.assertEqual(optimizer.optimization_history[0], result)
        
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    def test_get_optimization_history(self, mock_llm, mock_redis):
        """测试获取优化历史"""
        # 设置返回值
        mock_redis.return_value = self.redis_mock
        
        # 创建优化器
        optimizer = PerformanceOptimizer(self.config)
        
        # 添加历史记录
        for i in range(5):
            optimizer.optimization_history.append({
                "timestamp": time.time() + i,
                "bottlenecks": [],
                "strategies": [],
                "results": []
            })
        
        # 获取历史记录
        history = optimizer.get_optimization_history()
        self.assertEqual(len(history), 5)
        
        # 限制数量
        limited_history = optimizer.get_optimization_history(limit=3)
        self.assertEqual(len(limited_history), 3)


class TestFactoryFunctions(unittest.TestCase):
    """工厂函数测试"""
    
    def test_create_system_monitor(self):
        """测试创建系统监控器"""
        config = {
            "monitor_interval": 5,
            "max_history_length": 1000
        }
        
        with patch('src.monitoring.system_monitor.redis.Redis'), \
             patch('src.monitoring.system_monitor.GraphDatabase.driver'), \
             patch('src.monitoring.system_monitor.ChatOpenAI'):
            
            monitor = create_system_monitor(config)
            self.assertIsInstance(monitor, SystemMonitor)
            self.assertEqual(monitor.monitor_interval, 5)
            self.assertEqual(monitor.max_history_length, 1000)
    
    def test_create_performance_optimizer(self):
        """测试创建性能优化器"""
        config = {
            "redis_host": "localhost",
            "redis_port": 6379
        }
        
        with patch('src.monitoring.system_monitor.redis.Redis'), \
             patch('src.monitoring.system_monitor.ChatOpenAI'):
            
            optimizer = create_performance_optimizer(config)
            self.assertIsInstance(optimizer, PerformanceOptimizer)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    @patch('src.monitoring.system_monitor.psutil')
    @patch('src.monitoring.system_monitor.GPUtil')
    @patch('src.monitoring.system_monitor.redis.Redis')
    @patch('src.monitoring.system_monitor.GraphDatabase.driver')
    @patch('src.monitoring.system_monitor.ChatOpenAI')
    async def test_monitor_optimize_workflow(self, mock_llm, mock_neo4j, mock_redis, mock_gputil, mock_psutil):
        """测试监控优化工作流"""
        # 设置返回值
        mock_redis.return_value = Mock()
        mock_neo4j.return_value = Mock()
        
        # Mock psutil返回值
        mock_psutil.cpu_percent.return_value = 80.0
        mock_memory = Mock()
        mock_memory.percent = 85.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        # Mock LLM响应
        mock_llm_instance = Mock()
        mock_llm_instance.ainvoke.return_value = Mock(content="优化策略内容")
        mock_llm.return_value = mock_llm_instance
        
        # 创建监控器和优化器
        monitor = SystemMonitor({
            "monitor_interval": 0.1,
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_db": 0,
            "neo4j_uri": "bolt://localhost:7687",
            "neo4j_user": "neo4j",
            "neo4j_password": "password"
        })
        
        optimizer = PerformanceOptimizer({
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_db": 0
        })
        
        # 启动监控
        monitor.start()
        
        # 等待收集一些指标
        await asyncio.sleep(0.3)
        
        # 停止监控
        monitor.stop()
        
        # 生成性能报告
        report = await monitor.generate_performance_report()
        
        # 验证报告
        self.assertIsNotNone(report)
        self.assertIn("metrics", report.__dict__)
        self.assertIn("analysis", report.__dict__)
        self.assertIn("recommendations", report.__dict__)
        
        # 执行优化
        optimization_result = await optimizer.optimize(report.metrics, report.analysis)
        
        # 验证优化结果
        self.assertIn("timestamp", optimization_result)
        self.assertIn("bottlenecks", optimization_result)
        self.assertIn("strategies", optimization_result)
        self.assertIn("results", optimization_result)
        
        # 关闭
        await monitor.shutdown()
        await optimizer.shutdown()


if __name__ == "__main__":
    # 运行测试
    unittest.main()