"""
系统监控与性能优化模块
整合系统状态监控、性能分析和优化建议
"""

import asyncio
import json
import logging
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict

# 系统监控
import psutil
import GPUtil
import threading
import schedule

# 性能分析
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 大模型增强
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# 数据存储
import redis
from neo4j import GraphDatabase

# 其他工具
import os
import sys
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    GPU = "gpu"
    NETWORK = "network"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """指标数据"""
    metric_type: MetricType
    value: float
    unit: str
    timestamp: float
    source: str


@dataclass
class Alert:
    """告警"""
    alert_level: AlertLevel
    metric_type: MetricType
    message: str
    timestamp: float
    resolved: bool = False


@dataclass
class PerformanceReport:
    """性能报告"""
    report_id: str
    metrics: Dict[str, List[MetricData]]
    alerts: List[Alert]
    analysis: Dict[str, Any]
    recommendations: List[str]
    timestamp: float


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化系统监控器"""
        self.config = config
        
        # 监控配置
        self.monitor_interval = config.get("monitor_interval", 5)  # 监控间隔（秒）
        self.max_history_length = config.get("max_history_length", 1000)  # 最大历史记录数
        
        # 监控状态
        self.monitoring = False
        self.monitor_thread = None
        
        # 指标数据
        self.metrics = {
            MetricType.CPU: [],
            MetricType.MEMORY: [],
            MetricType.DISK: [],
            MetricType.GPU: [],
            MetricType.NETWORK: [],
            MetricType.RESPONSE_TIME: [],
            MetricType.THROUGHPUT: []
        }
        
        # 告警
        self.alerts = []
        self.alert_rules = self._init_alert_rules()
        
        # 回调函数
        self.alert_callbacks = []
        
        # 初始化大模型
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        
        # 初始化数据存储
        self.redis_client = redis.Redis(
            host=config.get("redis_host", "localhost"),
            port=config.get("redis_port", 6379),
            db=config.get("redis_db", 0)
        )
        
        self.neo4j_driver = GraphDatabase.driver(
            config.get("neo4j_uri", "bolt://localhost:7687"),
            auth=(
                config.get("neo4j_user", "neo4j"),
                config.get("neo4j_password", "password")
            )
        )
        
        logger.info("系统监控器初始化完成")
    
    def _init_alert_rules(self) -> Dict[MetricType, Dict[str, Any]]:
        """初始化告警规则"""
        return {
            MetricType.CPU: {
                "warning_threshold": 70.0,
                "error_threshold": 85.0,
                "critical_threshold": 95.0
            },
            MetricType.MEMORY: {
                "warning_threshold": 70.0,
                "error_threshold": 85.0,
                "critical_threshold": 95.0
            },
            MetricType.DISK: {
                "warning_threshold": 70.0,
                "error_threshold": 85.0,
                "critical_threshold": 95.0
            },
            MetricType.GPU: {
                "warning_threshold": 70.0,
                "error_threshold": 85.0,
                "critical_threshold": 95.0
            },
            MetricType.RESPONSE_TIME: {
                "warning_threshold": 1000.0,  # 1秒
                "error_threshold": 3000.0,   # 3秒
                "critical_threshold": 5000.0  # 5秒
            },
            MetricType.THROUGHPUT: {
                "warning_threshold": 100.0,   # 100请求/秒
                "error_threshold": 50.0,      # 50请求/秒
                "critical_threshold": 10.0    # 10请求/秒
            }
        }
    
    def start(self) -> None:
        """启动系统监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("系统监控已启动")
    
    def stop(self) -> None:
        """停止系统监控"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
            logger.info("系统监控已停止")
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.monitoring:
            try:
                # 收集指标数据
                self._collect_metrics()
                
                # 检查告警
                self._check_alerts()
                
                # 等待下一次监控
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"系统监控出错: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_metrics(self) -> None:
        """收集指标数据"""
        timestamp = time.time()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self._add_metric(MetricType.CPU, cpu_percent, "%", timestamp, "psutil")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        self._add_metric(MetricType.MEMORY, memory.percent, "%", timestamp, "psutil")
        
        # 磁盘使用率
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_percent = (usage.used / usage.total) * 100
                self._add_metric(MetricType.DISK, disk_percent, "%", timestamp, f"psutil:{partition.device}")
            except Exception as e:
                logger.error(f"获取磁盘使用情况失败: {e}")
        
        # GPU使用率（如果有）
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_load = gpu.load * 100
                self._add_metric(MetricType.GPU, gpu_load, "%", timestamp, f"GPUtil:{gpu.id}")
        except:
            pass
        
        # 网络IO
        net_io = psutil.net_io_counters()
        if net_io:
            # 计算网络吞吐量（简化实现）
            network_throughput = (net_io.bytes_sent + net_io.bytes_recv) / 1024  # KB/s
            self._add_metric(MetricType.NETWORK, network_throughput, "KB/s", timestamp, "psutil")
    
    def _add_metric(self, metric_type: MetricType, value: float, unit: str, timestamp: float, source: str) -> None:
        """添加指标数据"""
        metric = MetricData(
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=timestamp,
            source=source
        )
        
        self.metrics[metric_type].append(metric)
        
        # 限制历史长度
        if len(self.metrics[metric_type]) > self.max_history_length:
            self.metrics[metric_type] = self.metrics[metric_type][-self.max_history_length:]
    
    def _check_alerts(self) -> None:
        """检查告警"""
        for metric_type, metric_list in self.metrics.items():
            if not metric_list:
                continue
            
            # 获取最新指标
            latest_metric = metric_list[-1]
            
            # 获取告警规则
            rules = self.alert_rules.get(metric_type)
            if not rules:
                continue
            
            # 检查告警阈值
            alert_level = None
            if latest_metric.value >= rules["critical_threshold"]:
                alert_level = AlertLevel.CRITICAL
            elif latest_metric.value >= rules["error_threshold"]:
                alert_level = AlertLevel.ERROR
            elif latest_metric.value >= rules["warning_threshold"]:
                alert_level = AlertLevel.WARNING
            
            # 如果需要告警
            if alert_level:
                # 检查是否已有相同类型的未解决告警
                existing_alert = next(
                    (a for a in self.alerts 
                     if a.metric_type == metric_type and not a.resolved),
                    None
                )
                
                if not existing_alert:
                    # 创建新告警
                    alert = Alert(
                        alert_level=alert_level,
                        metric_type=metric_type,
                        message=f"{metric_type.value}值{latest_metric.value}{latest_metric.unit}超过{alert_level.value}阈值{rules[f'{alert_level.value}_threshold']}{latest_metric.unit}",
                        timestamp=latest_metric.timestamp
                    )
                    
                    self.alerts.append(alert)
                    
                    # 触发告警回调
                    self._trigger_alert_callbacks(alert)
                    
                    logger.warning(f"触发告警: {alert.message}")
    
    def _trigger_alert_callbacks(self, alert: Alert) -> None:
        """触发告警回调"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
    
    def register_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """注册告警回调"""
        self.alert_callbacks.append(callback)
    
    def get_metrics(self, metric_type: Optional[MetricType] = None, limit: int = 100) -> Dict[MetricType, List[MetricData]]:
        """获取指标数据"""
        if metric_type:
            return {metric_type: self.metrics[metric_type][-limit:]}
        else:
            return {k: v[-limit:] for k, v in self.metrics.items()}
    
    def get_alerts(self, resolved: Optional[bool] = None) -> List[Alert]:
        """获取告警"""
        if resolved is None:
            return self.alerts
        else:
            return [a for a in self.alerts if a.resolved == resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self.alerts:
            if str(id(alert)) == alert_id and not alert.resolved:
                alert.resolved = True
                logger.info(f"告警已解决: {alert.message}")
                return True
        return False
    
    async def generate_performance_report(self) -> PerformanceReport:
        """生成性能报告"""
        report_id = f"perf_report_{int(time.time())}"
        timestamp = time.time()
        
        # 获取指标数据
        metrics = self.get_metrics()
        
        # 分析性能
        analysis = await self._analyze_performance(metrics)
        
        # 生成优化建议
        recommendations = await self._generate_recommendations(metrics, analysis)
        
        # 创建报告
        report = PerformanceReport(
            report_id=report_id,
            metrics=metrics,
            alerts=self.get_alerts(resolved=False),
            analysis=analysis,
            recommendations=recommendations,
            timestamp=timestamp
        )
        
        # 保存报告到Redis
        await self._save_report(report)
        
        return report
    
    async def _analyze_performance(self, metrics: Dict[MetricType, List[MetricData]]) -> Dict[str, Any]:
        """分析性能"""
        analysis = {}
        
        for metric_type, metric_list in metrics.items():
            if not metric_list:
                continue
            
            # 提取值
            values = [m.value for m in metric_list]
            
            # 计算统计信息
            metric_analysis = {
                "count": len(values),
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values),
                "p95": np.percentile(values, 95),
                "p99": np.percentile(values, 99),
                "trend": self._analyze_trend(values)
            }
            
            analysis[metric_type.value] = metric_analysis
        
        return analysis
    
    def _analyze_trend(self, values: List[float]) -> str:
        """分析趋势"""
        if len(values) < 2:
            return "insufficient_data"
        
        # 计算前后半段的平均值
        mid = len(values) // 2
        first_half_avg = np.mean(values[:mid])
        second_half_avg = np.mean(values[mid:])
        
        # 判断趋势
        if second_half_avg > first_half_avg * 1.1:
            return "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    async def _generate_recommendations(
        self, 
        metrics: Dict[MetricType, List[MetricData]], 
        analysis: Dict[str, Any]
    ) -> List[str]:
        """生成优化建议"""
        try:
            # 使用大模型生成优化建议
            prompt = ChatPromptTemplate.from_template(
                "基于以下性能指标和分析，生成优化建议：\n"
                "性能指标: {metrics}\n"
                "性能分析: {analysis}\n\n"
                "请提供以下内容：\n"
                "1. 性能瓶颈识别\n"
                "2. 优化策略\n"
                "3. 具体措施\n"
                "4. 预期效果\n"
                "5. 实施步骤\n"
            )
            
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "metrics": str({k.value: v for k, v in metrics.items()}),
                "analysis": str(analysis)
            })
            
            # 解析响应
            recommendations_text = response.content
            
            # 简化实现：将整个响应作为一条建议
            # 实际实现中可以解析为多条建议
            recommendations = [recommendations_text]
            
            return recommendations
        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
            return [f"生成优化建议失败: {str(e)}"]
    
    async def _save_report(self, report: PerformanceReport) -> None:
        """保存报告"""
        try:
            # 转换为可序列化格式
            report_dict = asdict(report)
            
            # 存储到Redis
            self.redis_client.setex(
                f"performance_report:{report.report_id}",
                3600 * 24,  # 24小时过期
                json.dumps(report_dict)
            )
        except Exception as e:
            logger.error(f"保存性能报告失败: {e}")
    
    async def get_performance_report(self, report_id: str) -> Optional[PerformanceReport]:
        """获取性能报告"""
        try:
            # 从Redis获取报告
            report_data = self.redis_client.get(f"performance_report:{report_id}")
            
            if report_data:
                report_dict = json.loads(report_data)
                return PerformanceReport(**report_dict)
            
            return None
        except Exception as e:
            logger.error(f"获取性能报告失败: {e}")
            return None
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        status = {}
        
        for metric_type, metric_list in self.metrics.items():
            if metric_list:
                latest_metric = metric_list[-1]
                status[metric_type.value] = {
                    "value": latest_metric.value,
                    "unit": latest_metric.unit,
                    "timestamp": latest_metric.timestamp,
                    "source": latest_metric.source
                }
        
        # 添加告警信息
        status["alerts"] = {
            "total": len(self.alerts),
            "unresolved": len(self.get_alerts(resolved=False)),
            "critical": len([a for a in self.get_alerts(resolved=False) if a.alert_level == AlertLevel.CRITICAL]),
            "error": len([a for a in self.get_alerts(resolved=False) if a.alert_level == AlertLevel.ERROR]),
            "warning": len([a for a in self.get_alerts(resolved=False) if a.alert_level == AlertLevel.WARNING])
        }
        
        return status
    
    async def shutdown(self) -> None:
        """关闭监控器"""
        # 停止监控
        self.stop()
        
        # 关闭Neo4j连接
        self.neo4j_driver.close()
        
        # 关闭Redis连接
        self.redis_client.close()
        
        logger.info("系统监控器已关闭")


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化性能优化器"""
        self.config = config
        
        # 初始化大模型
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        
        # 初始化数据存储
        self.redis_client = redis.Redis(
            host=config.get("redis_host", "localhost"),
            port=config.get("redis_port", 6379),
            db=config.get("redis_db", 0)
        )
        
        # 优化历史
        self.optimization_history = []
        
        logger.info("性能优化器初始化完成")
    
    async def optimize(self, metrics: Dict[MetricType, List[MetricData]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行性能优化"""
        try:
            # 识别性能瓶颈
            bottlenecks = await self._identify_bottlenecks(metrics, analysis)
            
            # 生成优化策略
            strategies = await self._generate_optimization_strategies(bottlenecks)
            
            # 实施优化措施
            results = await self._implement_optimizations(strategies)
            
            # 创建优化记录
            optimization_record = {
                "timestamp": time.time(),
                "bottlenecks": bottlenecks,
                "strategies": strategies,
                "results": results
            }
            
            # 添加到历史
            self.optimization_history.append(optimization_record)
            
            # 限制历史长度
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]
            
            # 保存到Redis
            await self._save_optimization_record(optimization_record)
            
            return optimization_record
        except Exception as e:
            logger.error(f"性能优化失败: {e}")
            return {"error": str(e)}
    
    async def _identify_bottlenecks(
        self, 
        metrics: Dict[MetricType, List[MetricData]], 
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        # 分析CPU瓶颈
        if MetricType.CPU in metrics and MetricType.CPU.value in analysis:
            cpu_analysis = analysis[MetricType.CPU.value]
            if cpu_analysis["mean"] > 70 or cpu_analysis["p95"] > 90:
                bottlenecks.append({
                    "type": "cpu",
                    "severity": "high" if cpu_analysis["mean"] > 85 else "medium",
                    "description": f"CPU使用率过高，平均值{cpu_analysis['mean']:.2f}%，95分位数{cpu_analysis['p95']:.2f}%"
                })
        
        # 分析内存瓶颈
        if MetricType.MEMORY in metrics and MetricType.MEMORY.value in analysis:
            memory_analysis = analysis[MetricType.MEMORY.value]
            if memory_analysis["mean"] > 70 or memory_analysis["p95"] > 90:
                bottlenecks.append({
                    "type": "memory",
                    "severity": "high" if memory_analysis["mean"] > 85 else "medium",
                    "description": f"内存使用率过高，平均值{memory_analysis['mean']:.2f}%，95分位数{memory_analysis['p95']:.2f}%"
                })
        
        # 分析磁盘瓶颈
        if MetricType.DISK in metrics and MetricType.DISK.value in analysis:
            disk_analysis = analysis[MetricType.DISK.value]
            if disk_analysis["mean"] > 70 or disk_analysis["p95"] > 90:
                bottlenecks.append({
                    "type": "disk",
                    "severity": "high" if disk_analysis["mean"] > 85 else "medium",
                    "description": f"磁盘使用率过高，平均值{disk_analysis['mean']:.2f}%，95分位数{disk_analysis['p95']:.2f}%"
                })
        
        # 分析GPU瓶颈
        if MetricType.GPU in metrics and MetricType.GPU.value in analysis:
            gpu_analysis = analysis[MetricType.GPU.value]
            if gpu_analysis["mean"] > 70 or gpu_analysis["p95"] > 90:
                bottlenecks.append({
                    "type": "gpu",
                    "severity": "high" if gpu_analysis["mean"] > 85 else "medium",
                    "description": f"GPU使用率过高，平均值{gpu_analysis['mean']:.2f}%，95分位数{gpu_analysis['p95']:.2f}%"
                })
        
        # 分析响应时间瓶颈
        if MetricType.RESPONSE_TIME in metrics and MetricType.RESPONSE_TIME.value in analysis:
            response_analysis = analysis[MetricType.RESPONSE_TIME.value]
            if response_analysis["mean"] > 1000 or response_analysis["p95"] > 3000:
                bottlenecks.append({
                    "type": "response_time",
                    "severity": "high" if response_analysis["mean"] > 3000 else "medium",
                    "description": f"响应时间过长，平均值{response_analysis['mean']:.2f}ms，95分位数{response_analysis['p95']:.2f}ms"
                })
        
        # 分析吞吐量瓶颈
        if MetricType.THROUGHPUT in metrics and MetricType.THROUGHPUT.value in analysis:
            throughput_analysis = analysis[MetricType.THROUGHPUT.value]
            if throughput_analysis["mean"] < 100:
                bottlenecks.append({
                    "type": "throughput",
                    "severity": "high" if throughput_analysis["mean"] < 50 else "medium",
                    "description": f"吞吐量过低，平均值{throughput_analysis['mean']:.2f}请求/秒"
                })
        
        return bottlenecks
    
    async def _generate_optimization_strategies(self, bottlenecks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成优化策略"""
        try:
            # 使用大模型生成优化策略
            prompt = ChatPromptTemplate.from_template(
                "基于以下性能瓶颈，生成优化策略：\n"
                "性能瓶颈: {bottlenecks}\n\n"
                "请为每个瓶颈提供以下内容：\n"
                "1. 瓶颈类型\n"
                "2. 优化策略\n"
                "3. 具体措施\n"
                "4. 预期效果\n"
                "5. 实施难度\n"
                "6. 风险评估\n"
            )
            
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "bottlenecks": str(bottlenecks)
            })
            
            # 解析响应
            strategies_text = response.content
            
            # 简化实现：将整个响应作为一条策略
            # 实际实现中可以解析为多条策略
            strategies = [{
                "bottlenecks": bottlenecks,
                "strategy": strategies_text,
                "timestamp": time.time()
            }]
            
            return strategies
        except Exception as e:
            logger.error(f"生成优化策略失败: {e}")
            return [{"error": str(e)}]
    
    async def _implement_optimizations(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """实施优化措施"""
        results = []
        
        for strategy in strategies:
            if "error" in strategy:
                results.append({
                    "strategy": strategy,
                    "result": "failed",
                    "error": strategy["error"]
                })
                continue
            
            try:
                # 简化实现：模拟优化措施实施
                # 实际实现中需要根据策略执行具体的优化措施
                
                # 模拟优化执行时间
                await asyncio.sleep(1)
                
                # 模拟优化结果
                result = {
                    "strategy": strategy,
                    "result": "success",
                    "timestamp": time.time(),
                    "metrics_improvement": {
                        "cpu_usage": -5.0,  # CPU使用率降低5%
                        "memory_usage": -3.0,  # 内存使用率降低3%
                        "response_time": -10.0  # 响应时间降低10ms
                    }
                }
                
                results.append(result)
            except Exception as e:
                logger.error(f"实施优化措施失败: {e}")
                results.append({
                    "strategy": strategy,
                    "result": "failed",
                    "error": str(e)
                })
        
        return results
    
    async def _save_optimization_record(self, record: Dict[str, Any]) -> None:
        """保存优化记录"""
        try:
            # 存储到Redis
            self.redis_client.setex(
                f"optimization_record:{record['timestamp']}",
                3600 * 24 * 7,  # 7天过期
                json.dumps(record)
            )
        except Exception as e:
            logger.error(f"保存优化记录失败: {e}")
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self.optimization_history[-limit:]
    
    async def shutdown(self) -> None:
        """关闭优化器"""
        # 关闭Redis连接
        self.redis_client.close()
        
        logger.info("性能优化器已关闭")


# 工厂函数
def create_system_monitor(config: Dict[str, Any]) -> SystemMonitor:
    """创建系统监控器实例"""
    return SystemMonitor(config)


def create_performance_optimizer(config: Dict[str, Any]) -> PerformanceOptimizer:
    """创建性能优化器实例"""
    return PerformanceOptimizer(config)


# 示例用法
if __name__ == "__main__":
    # 配置
    config = {
        "monitor_interval": 5,
        "max_history_length": 1000,
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 0,
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password"
    }
    
    # 创建实例
    monitor = create_system_monitor(config)
    optimizer = create_performance_optimizer(config)
    
    # 启动监控
    monitor.start()
    
    # 模拟运行一段时间
    import asyncio
    async def main():
        # 运行30秒
        await asyncio.sleep(30)
        
        # 生成性能报告
        report = await monitor.generate_performance_report()
        print(f"性能报告ID: {report.report_id}")
        
        # 执行性能优化
        optimization_result = await optimizer.optimize(report.metrics, report.analysis)
        print(f"优化结果: {optimization_result}")
        
        # 停止监控
        monitor.stop()
    
    asyncio.run(main())