"""
系统监控与性能优化模块的示例应用
"""

import asyncio
import json
import time
import logging
from datetime import datetime

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.monitoring.system_monitor import (
    SystemMonitor, PerformanceOptimizer, MetricType, AlertLevel,
    create_system_monitor, create_performance_optimizer
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    # 配置
    config = {
        "monitor_interval": 2,  # 2秒间隔
        "max_history_length": 100,
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 0,
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password"
    }
    
    # 创建系统监控器
    monitor = create_system_monitor(config)
    
    # 创建性能优化器
    optimizer = create_performance_optimizer(config)
    
    # 注册告警回调
    def alert_callback(alert):
        """告警回调函数"""
        timestamp = datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {alert.alert_level.value.upper()} 告警: {alert.message}")
        
        # 如果是严重告警，自动触发优化
        if alert.alert_level == AlertLevel.CRITICAL:
            logger.info("检测到严重告警，触发自动优化")
            asyncio.create_task(auto_optimize(monitor, optimizer))
    
    monitor.register_alert_callback(alert_callback)
    
    # 启动监控
    monitor.start()
    logger.info("系统监控已启动")
    
    # 运行一段时间
    try:
        # 运行60秒
        await asyncio.sleep(60)
        
        # 生成性能报告
        logger.info("生成性能报告...")
        report = await monitor.generate_performance_report()
        
        # 打印报告摘要
        print("\n性能报告摘要:")
        print(f"报告ID: {report.report_id}")
        print(f"生成时间: {datetime.fromtimestamp(report.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 打印指标摘要
        print("\n指标摘要:")
        for metric_type, metrics in report.metrics.items():
            if metrics:
                values = [m.value for m in metrics]
                print(f"{metric_type.value}: 平均值={sum(values)/len(values):.2f}, 最大值={max(values):.2f}, 最小值={min(values):.2f}")
        
        # 打印告警摘要
        print("\n告警摘要:")
        print(f"总告警数: {len(report.alerts)}")
        for alert_level in [AlertLevel.CRITICAL, AlertLevel.ERROR, AlertLevel.WARNING]:
            count = len([a for a in report.alerts if a.alert_level == alert_level])
            if count > 0:
                print(f"{alert_level.value}: {count}")
        
        # 打印优化建议
        print("\n优化建议:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"{i}. {recommendation}")
        
        # 手动执行优化
        logger.info("执行手动优化...")
        optimization_result = await optimizer.optimize(report.metrics, report.analysis)
        
        # 打印优化结果
        print("\n优化结果:")
        print(f"优化时间: {datetime.fromtimestamp(optimization_result['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 打印瓶颈
        if "bottlenecks" in optimization_result:
            print("\n识别的瓶颈:")
            for i, bottleneck in enumerate(optimization_result["bottlenecks"], 1):
                print(f"{i}. {bottleneck['type']}: {bottleneck['description']}")
        
        # 打印优化策略
        if "strategies" in optimization_result:
            print("\n优化策略:")
            for i, strategy in enumerate(optimization_result["strategies"], 1):
                if isinstance(strategy, dict) and "strategy" in strategy:
                    print(f"{i}. {strategy['strategy']}")
                else:
                    print(f"{i}. {strategy}")
        
        # 打印优化结果
        if "results" in optimization_result:
            print("\n优化实施结果:")
            for i, result in enumerate(optimization_result["results"], 1):
                if isinstance(result, dict) and "result" in result:
                    print(f"{i}. 结果: {result['result']}")
                    if "metrics_improvement" in result:
                        print("   性能改进:")
                        for metric, improvement in result["metrics_improvement"].items():
                            print(f"     {metric}: {improvement}")
        
    except KeyboardInterrupt:
        logger.info("用户中断，停止监控")
    finally:
        # 停止监控
        monitor.stop()
        
        # 关闭连接
        await monitor.shutdown()
        await optimizer.shutdown()
        
        logger.info("系统监控与优化已停止")


async def auto_optimize(monitor, optimizer):
    """自动优化函数"""
    try:
        # 获取当前指标
        metrics = monitor.get_metrics()
        
        # 分析性能
        analysis = await monitor._analyze_performance(metrics)
        
        # 执行优化
        optimization_result = await optimizer.optimize(metrics, analysis)
        
        logger.info(f"自动优化完成: {optimization_result}")
    except Exception as e:
        logger.error(f"自动优化失败: {e}")


async def simulate_load():
    """模拟系统负载"""
    logger.info("开始模拟系统负载...")
    
    # 模拟CPU密集型任务
    def cpu_intensive_task():
        """CPU密集型任务"""
        end_time = time.time() + 5  # 运行5秒
        while time.time() < end_time:
            # 执行一些计算密集型操作
            sum(i * i for i in range(10000))
    
    # 模拟内存密集型任务
    def memory_intensive_task():
        """内存密集型任务"""
        # 创建一个大列表
        big_list = [i for i in range(1000000)]
        time.sleep(5)
        del big_list
    
    # 启动任务
    import threading
    cpu_thread = threading.Thread(target=cpu_intensive_task)
    memory_thread = threading.Thread(target=memory_intensive_task)
    
    cpu_thread.start()
    memory_thread.start()
    
    # 等待任务完成
    cpu_thread.join()
    memory_thread.join()
    
    logger.info("系统负载模拟完成")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())