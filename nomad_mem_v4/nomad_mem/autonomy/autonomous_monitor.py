"""环境监控模块 - 监控系统状态、检测异常并触发自动响应。"""
from __future__ import annotations

import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict


class MonitorType(Enum):
    """监控类型"""
    SYSTEM_HEALTH = "system_health"
    USER_ACTIVITY = "user_activity"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RATE = "error_rate"
    PERFORMANCE = "performance"


class MonitorStatus(Enum):
    """监控状态"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class MonitorConfig:
    """监控配置"""
    monitor_id: str
    monitor_type: MonitorType
    check_interval_seconds: float
    thresholds: Dict[str, float]  # e.g. {"warning": 0.7, "critical": 0.9}
    alert_action: str = ""


@dataclass
class MonitorState:
    """监控状态"""
    monitor_id: str
    status: MonitorStatus = MonitorStatus.UNKNOWN
    last_check: float = 0.0
    last_value: Optional[float] = None
    check_count: int = 0
    alert_count: int = 0
    history: List[float] = field(default_factory=list)


@dataclass
class AnomalyRecord:
    """异常记录"""
    timestamp: float
    monitor_id: str
    anomaly_type: str  # "threshold_exceeded", "threshold_breached", etc.
    severity: MonitorStatus
    value: float
    threshold: float
    details: str = ""


class AutonomousMonitor:
    """
    自主环境监控器。

    基于阈值检测异常，追踪指标历史，检测值是否跨越阈值。
    """

    def __init__(self):
        self._configs: Dict[str, MonitorConfig] = {}
        self._states: Dict[str, MonitorState] = {}
        self._anomaly_history: List[AnomalyRecord] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  注册与移除
    # ------------------------------------------------------------------ #

    def register_monitor(
        self,
        monitor_id: str,
        monitor_type: MonitorType,
        check_interval: float,
        thresholds: Dict[str, float],
        alert_action: str = "",
    ) -> bool:
        """注册一个新的监控项。"""
        if monitor_id in self._configs:
            return False
        config = MonitorConfig(
            monitor_id=monitor_id,
            monitor_type=monitor_type,
            check_interval_seconds=check_interval,
            thresholds=thresholds,
            alert_action=alert_action,
        )
        state = MonitorState(monitor_id=monitor_id)
        with self._lock:
            self._configs[monitor_id] = config
            self._states[monitor_id] = state
        return True

    def remove_monitor(self, monitor_id: str) -> bool:
        """移除一个监控项。"""
        with self._lock:
            if monitor_id not in self._configs:
                return False
            del self._configs[monitor_id]
            del self._states[monitor_id]
        return True

    # ------------------------------------------------------------------ #
    #  指标更新
    # ------------------------------------------------------------------ #

    def update_metric(self, monitor_id: str, value: float) -> bool:
        """更新监控指标的当前值。"""
        with self._lock:
            state = self._states.get(monitor_id)
            if state is None:
                return False
            state.last_value = value
            state.history.append(value)
            # 保留最近 100 条记录
            if len(state.history) > 100:
                state.history = state.history[-100:]
        return True

    # ------------------------------------------------------------------ #
    #  检查逻辑
    # ------------------------------------------------------------------ #

    def check_all_monitors(self) -> List[AnomalyRecord]:
        """检查所有监控项，返回检测到的异常列表。"""
        anomalies: List[AnomalyRecord] = []
        with self._lock:
            for mid in list(self._states.keys()):
                anomaly = self._check_single(mid)
                if anomaly is not None:
                    anomalies.append(anomaly)
        return anomalies

    def check_monitor(self, monitor_id: str) -> Optional[AnomalyRecord]:
        """检查指定的监控项。"""
        with self._lock:
            return self._check_single(monitor_id)

    def _check_single(self, monitor_id: str) -> Optional[AnomalyRecord]:
        """内部：检查单个监控项，需持有锁。"""
        config = self._configs.get(monitor_id)
        state = self._states.get(monitor_id)
        if config is None or state is None:
            return None

        value = state.last_value
        if value is None:
            return None

        now = time.time()
        state.last_check = now
        state.check_count += 1

        thresholds = config.thresholds
        new_status = MonitorStatus.NORMAL

        # 按 critical -> warning 的顺序检查（从高到低）
        if "critical" in thresholds:
            if value >= thresholds["critical"]:
                new_status = MonitorStatus.CRITICAL
            elif "warning" in thresholds and value >= thresholds["warning"]:
                new_status = MonitorStatus.WARNING
        elif "warning" in thresholds:
            if value >= thresholds["warning"]:
                new_status = MonitorStatus.WARNING

        state.status = new_status

        if new_status in (MonitorStatus.WARNING, MonitorStatus.CRITICAL):
            state.alert_count += 1
            severity_label = new_status.value
            threshold_val = thresholds.get(severity_label, 0.0)
            anomaly = AnomalyRecord(
                timestamp=now,
                monitor_id=monitor_id,
                anomaly_type="threshold_exceeded",
                severity=new_status,
                value=value,
                threshold=threshold_val,
                details=f"Monitor {monitor_id}: value {value} >= {severity_label} threshold {threshold_val}",
            )
            self._anomaly_history.append(anomaly)
            return anomaly

        return None

    # ------------------------------------------------------------------ #
    #  查询
    # ------------------------------------------------------------------ #

    def get_monitor_state(self, monitor_id: str) -> Optional[MonitorState]:
        """获取指定监控项的状态。"""
        with self._lock:
            state = self._states.get(monitor_id)
            if state is None:
                return None
            # 返回副本
            return MonitorState(
                monitor_id=state.monitor_id,
                status=state.status,
                last_check=state.last_check,
                last_value=state.last_value,
                check_count=state.check_count,
                alert_count=state.alert_count,
                history=list(state.history),
            )

    def get_anomaly_history(
        self, monitor_id: Optional[str] = None, limit: int = 50
    ) -> List[AnomalyRecord]:
        """获取异常历史记录。"""
        with self._lock:
            if monitor_id:
                records = [
                    r for r in self._anomaly_history if r.monitor_id == monitor_id
                ]
            else:
                records = list(self._anomaly_history)
            return records[-limit:]

    def get_active_alerts(self) -> List[Dict]:
        """获取当前处于 WARNING 或 CRITICAL 状态的监控项。"""
        alerts: List[Dict] = []
        with self._lock:
            for mid, state in self._states.items():
                if state.status in (MonitorStatus.WARNING, MonitorStatus.CRITICAL):
                    config = self._configs[mid]
                    alerts.append({
                        "monitor_id": mid,
                        "monitor_type": config.monitor_type.value,
                        "status": state.status.value,
                        "last_value": state.last_value,
                        "alert_count": state.alert_count,
                    })
        return alerts

    def get_stats(self) -> Dict:
        """获取监控统计信息。"""
        with self._lock:
            total = len(self._configs)
            by_type: Dict[str, int] = defaultdict(int)
            by_status: Dict[str, int] = defaultdict(int)
            for mid, config in self._configs.items():
                by_type[config.monitor_type.value] += 1
            for mid, state in self._states.items():
                by_status[state.status.value] += 1
            anomaly_count = len(self._anomaly_history)
            return {
                "total_monitors": total,
                "by_type": dict(by_type),
                "by_status": dict(by_status),
                "anomaly_count": anomaly_count,
            }

    def close(self) -> None:
        """清理资源。"""
        with self._lock:
            self._configs.clear()
            self._states.clear()
            self._anomaly_history.clear()
