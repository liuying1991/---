"""
自主引擎模块

整合调度器、监控器和决策器，构成完整的自主运行系统。
该引擎作为核心协调器，定期执行“感知-决策-执行”循环，使系统能够独立运行并响应环境变化。

核心类: AutonomousEngine

工作流:
1. 检查所有监控器以发现异常
2. 运行到期的调度任务
3. 审查活跃目标并做出决策
4. 返回完整的循环报告
"""
from __future__ import annotations

import os
import time
import logging
from typing import Dict, List, Any, Optional

from nomad_mem.autonomy.autonomous_scheduler import AutonomousScheduler, TriggerType
from nomad_mem.autonomy.autonomous_monitor import AutonomousMonitor, MonitorType
from nomad_mem.autonomy.autonomous_decider import AutonomousDecider, DecisionType

logger = logging.getLogger(__name__)


class AutonomousEngine:
    """
    自主引擎主类。

    协调 AutonomousScheduler、AutonomousMonitor 和 AutonomousDecider 三个子模块，
    提供完整的自主运行能力。引擎通过 run_autonomous_cycle 方法执行定期的感知-决策-执行循环。
    """

    def __init__(self, data_dir: str = "data"):
        """
        初始化自主引擎。

        Args:
            data_dir: 数据存储目录，用于持久化调度器数据库。
        """
        self._data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "scheduler.db")

        # 初始化子模块
        self._action_registry: Dict[str, Any] = {}
        self._scheduler = AutonomousScheduler(
            db_path=db_path,
            action_registry=self._action_registry,
        )
        self._monitor = AutonomousMonitor()
        self._decider = AutonomousDecider()

        # 引擎内部状态
        self._running = False
        self._cycle_count = 0
        self._cycle_history: List[Dict[str, Any]] = []
        self._max_history = 100

        logger.info("[AutonomousEngine] 自主引擎初始化完成 (data_dir=%s)", data_dir)

    # ------------------------------------------------------------------ #
    #  生命周期管理
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """启动自主引擎，开始监控和调度循环。"""
        self._running = True
        logger.info("[AutonomousEngine] 自主引擎已启动")

    def stop(self) -> None:
        """停止自主引擎，暂停所有自主循环。"""
        self._running = False
        logger.info("[AutonomousEngine] 自主引擎已停止")

    def is_running(self) -> bool:
        """检查引擎是否正在运行。"""
        return self._running

    # ------------------------------------------------------------------ #
    #  任务/监控/目标配置
    # ------------------------------------------------------------------ #

    def add_autonomous_task(
        self,
        name: str,
        trigger_type: str | TriggerType,
        trigger_config: Dict[str, Any],
        action: str,
    ) -> str:
        """
        快捷方法：向调度器添加一个自主任务。

        Args:
            name: 任务名称
            trigger_type: 触发类型（字符串或 TriggerType 枚举）
            trigger_config: 触发配置（如 {"interval_seconds": 300}）
            action: 要执行的动作标识符

        Returns:
            task_id: 新创建的任务 ID
        """
        if isinstance(trigger_type, str):
            try:
                trigger_type = TriggerType(trigger_type.lower().replace(" ", "_"))
            except ValueError:
                logger.warning("[AutonomousEngine] 未知触发类型 '%s'，使用默认 TIME_INTERVAL", trigger_type)
                trigger_type = TriggerType.TIME_INTERVAL

        task_id = self._scheduler.schedule_task(
            name=name,
            description=f"Autonomous task: {name}",
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            action=action,
        )
        logger.info("[AutonomousEngine] 添加自主任务: %s (id=%s)", name, task_id)
        return task_id

    def add_monitor(
        self,
        monitor_id: str,
        monitor_type: str | MonitorType,
        check_interval: float,
        thresholds: Dict[str, float],
    ) -> bool:
        """
        快捷方法：向监控器注册一个监控项。

        Args:
            monitor_id: 监控项唯一标识
            monitor_type: 监控类型（字符串或 MonitorType 枚举）
            check_interval: 检查间隔（秒）
            thresholds: 阈值配置（如 {"warning": 0.7, "critical": 0.9}）

        Returns:
            bool: 注册是否成功
        """
        if isinstance(monitor_type, str):
            try:
                monitor_type = MonitorType(monitor_type.lower().replace(" ", "_"))
            except ValueError:
                logger.warning("[AutonomousEngine] 未知监控类型 '%s'，使用默认 SYSTEM_HEALTH", monitor_type)
                monitor_type = MonitorType.SYSTEM_HEALTH

        success = self._monitor.register_monitor(
            monitor_id=monitor_id,
            monitor_type=monitor_type,
            check_interval=check_interval,
            thresholds=thresholds,
        )
        if success:
            logger.info("[AutonomousEngine] 注册监控项: %s", monitor_id)
        return success

    def set_autonomous_goal(
        self,
        description: str,
        priority: int = 5,
        sub_goals: Optional[List[str]] = None,
    ) -> str:
        """
        快捷方法：为决策器设置一个自主目标。

        Args:
            description: 目标描述
            priority: 优先级 (1-10)
            sub_goals: 子目标列表

        Returns:
            goal_id: 新创建的目标 ID
        """
        goal_id = self._decider.set_goal(
            description=description,
            priority=priority,
            sub_goals=sub_goals or [],
        )
        logger.info("[AutonomousEngine] 设置自主目标: %s (id=%s)", description, goal_id)
        return goal_id

    # ------------------------------------------------------------------ #
    #  核心自主循环
    # ------------------------------------------------------------------ #

    def run_autonomous_cycle(self) -> Dict[str, Any]:
        """
        执行一次完整的自主循环。

        流程:
        1. 检查所有监控器 -> 发现异常
        2. 运行到期的调度任务 -> 执行后台动作
        3. 审查活跃目标并做出决策 -> 生成策略/动作
        4. 编译并返回综合报告

        Returns:
            Dict: 包含循环执行情况的详细报告
        """
        if not self._running:
            return {
                "cycle_number": self._cycle_count,
                "status": "stopped",
                "error": "引擎未启动，请先调用 start()",
            }

        cycle_start = time.time()
        self._cycle_count += 1

        # 步骤 1: 检查监控器
        anomalies = self._monitor.check_all_monitors()
        anomaly_count = len(anomalies)

        # 步骤 2: 运行到期任务
        executed_tasks = self._scheduler.run_due_tasks()
        task_count = len(executed_tasks)

        # 步骤 3: 审查目标并决策
        active_goals = self._decider.get_active_goals()
        decision = None

        # 当发现异常或有活跃目标时触发决策
        if anomalies or active_goals:
            context = {
                "anomaly_count": anomaly_count,
                "executed_tasks": task_count,
                "active_goals_count": len(active_goals),
                "anomaly_details": [
                    {
                        "monitor_id": a.monitor_id,
                        "severity": a.severity.value,
                        "value": a.value,
                        "threshold": a.threshold,
                    }
                    for a in anomalies
                ],
            }
            decision_type = DecisionType.STRATEGY if anomaly_count > 0 else DecisionType.ACTION
            decision_record = self._decider.make_decision(
                context=context,
                decision_type=decision_type,
            )
            decision = {
                "decision_id": decision_record.decision_id,
                "type": decision_record.decision_type.value,
                "decision": decision_record.decision_made,
                "confidence": decision_record.confidence,
                "reasoning": decision_record.reasoning,
            }

        # 步骤 4: 生成报告
        elapsed = time.time() - cycle_start
        report = {
            "cycle_number": self._cycle_count,
            "timestamp": time.time(),
            "duration_seconds": round(elapsed, 4),
            "status": "completed",
            "monitors": {
                "checked": True,
                "anomalies_detected": anomaly_count,
            },
            "scheduler": {
                "tasks_executed": task_count,
                "task_ids": executed_tasks,
            },
            "goals": {
                "active_count": len(active_goals),
            },
            "decision": decision,
        }

        # 记录历史
        self._cycle_history.append(report)
        if len(self._cycle_history) > self._max_history:
            self._cycle_history = self._cycle_history[-self._max_history:]

        logger.info(
            "[AutonomousEngine] 自主循环 #%d 完成 | 耗时: %.4fs | 异常: %d | 任务: %d | 决策: %s",
            self._cycle_count,
            elapsed,
            anomaly_count,
            task_count,
            decision is not None,
        )
        return report

    # ------------------------------------------------------------------ #
    #  状态查询
    # ------------------------------------------------------------------ #

    def get_autonomous_status(self) -> Dict[str, Any]:
        """
        获取引擎的综合状态（包含所有子模块的统计信息）。

        Returns:
            Dict: 包含引擎运行状态、循环计数、各子模块统计及最近一次循环结果
        """
        return {
            "engine_running": self._running,
            "cycle_count": self._cycle_count,
            "scheduler_stats": self._scheduler.get_stats(),
            "monitor_stats": self._monitor.get_stats(),
            "decider_stats": self._decider.get_stats(),
            "last_cycle": self._cycle_history[-1] if self._cycle_history else None,
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取当前处于 WARNING 或 CRITICAL 状态的监控告警。"""
        return self._monitor.get_active_alerts()

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取所有待执行或已调度的任务。"""
        tasks = self._scheduler.get_pending_tasks()
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "status": t.status,
                "trigger_type": t.trigger_type,
                "next_run": t.next_run,
                "priority": t.priority,
            }
            for t in tasks
        ]

    def get_active_goals(self) -> List[Dict[str, Any]]:
        """获取所有活跃目标。"""
        goals = self._decider.get_active_goals()
        return [
            {
                "goal_id": g.goal_id,
                "description": g.description,
                "priority": g.priority,
                "status": g.status,
                "sub_goals_count": len(g.sub_goals),
            }
            for g in goals
        ]

    # ------------------------------------------------------------------ #
    #  资源清理
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """停止引擎并释放所有子模块资源。"""
        logger.info("[AutonomousEngine] 正在关闭自主引擎...")
        self.stop()
        self._scheduler.close()
        self._monitor.close()
        self._decider.close()
        self._cycle_history.clear()
        logger.info("[AutonomousEngine] 自主引擎已完全关闭")
