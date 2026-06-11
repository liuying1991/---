"""
Proactive Alert - 主动提醒系统

核心能力:
1. 定时提醒：基于时间的提醒
2. 事件触发：基于条件的提醒
3. 情境感知：根据上下文决定是否提醒
4. 智能调度：避免打扰用户
5. 提醒优先级：根据重要性排序

参考:
- 推送通知系统设计
- 智能助手主动行为研究
- 用户注意力模型
"""
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class AlertType(Enum):
    """提醒类型"""
    SCHEDULED = "scheduled"        # 定时提醒
    EVENT_TRIGGERED = "event_triggered"  # 事件触发
    CONTEXTUAL = "contextual"      # 情境感知
    LEARNING_BASED = "learning_based"    # 学习推荐


class AlertPriority(Enum):
    """提醒优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class AlertStatus(Enum):
    """提醒状态"""
    PENDING = "pending"
    ACTIVE = "active"
    DELIVERED = "delivered"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


@dataclass
class Alert:
    """提醒"""
    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    scheduled_time: float = 0.0
    trigger_condition: Optional[Callable] = None
    context_tags: List[str] = field(default_factory=list)
    status: AlertStatus = AlertStatus.PENDING
    created_at: float = field(default_factory=time.time)
    delivered_at: float = 0.0
    dismiss_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuietHours:
    """免打扰时段"""
    start_hour: int = 22  # 22:00
    end_hour: int = 8     # 08:00
    enabled: bool = True
    exceptions: List[str] = field(default_factory=list)  # 紧急提醒例外


class ProactiveAlertSystem:
    """主动提醒系统"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.quiet_hours = QuietHours(
            start_hour=self.config.get("quiet_start", 22),
            end_hour=self.config.get("quiet_end", 8),
            enabled=self.config.get("quiet_enabled", True),
        )
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict] = []
        self.max_pending = self.config.get("max_pending", 10)
        self.cooldown_period = self.config.get("cooldown_period", 300)  # 5分钟冷却
        self.last_alert_time: float = 0.0

    def create_scheduled_alert(
        self,
        title: str,
        message: str,
        scheduled_time: float,
        priority: AlertPriority = AlertPriority.MEDIUM,
        context_tags: List[str] = None,
    ) -> str:
        """
        创建定时提醒

        Args:
            title: 标题
            message: 消息内容
            scheduled_time: 计划时间（时间戳）
            priority: 优先级
            context_tags: 上下文标签

        Returns:
            alert_id
        """
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        alert = Alert(
            alert_id=alert_id,
            alert_type=AlertType.SCHEDULED,
            priority=priority,
            title=title,
            message=message,
            scheduled_time=scheduled_time,
            context_tags=context_tags or [],
        )
        self.alerts[alert_id] = alert
        return alert_id

    def create_event_triggered_alert(
        self,
        title: str,
        message: str,
        trigger_condition: Callable,
        priority: AlertPriority = AlertPriority.HIGH,
        context_tags: List[str] = None,
    ) -> str:
        """
        创建事件触发提醒

        Args:
            title: 标题
            message: 消息内容
            trigger_condition: 触发条件函数
            priority: 优先级
            context_tags: 上下文标签

        Returns:
            alert_id
        """
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        alert = Alert(
            alert_id=alert_id,
            alert_type=AlertType.EVENT_TRIGGERED,
            priority=priority,
            title=title,
            message=message,
            trigger_condition=trigger_condition,
            context_tags=context_tags or [],
        )
        self.alerts[alert_id] = alert
        return alert_id

    def create_contextual_alert(
        self,
        title: str,
        message: str,
        context_condition: Callable,
        priority: AlertPriority = AlertPriority.LOW,
    ) -> str:
        """
        创建情境感知提醒

        Args:
            title: 标题
            message: 消息内容
            context_condition: 情境条件函数
            priority: 优先级

        Returns:
            alert_id
        """
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        alert = Alert(
            alert_id=alert_id,
            alert_type=AlertType.CONTEXTUAL,
            priority=priority,
            title=title,
            message=message,
            trigger_condition=context_condition,
        )
        self.alerts[alert_id] = alert
        return alert_id

    def check_and_deliver(self) -> List[Alert]:
        """
        检查并发送符合条件的提醒

        Returns:
            需要发送的提醒列表
        """
        current_time = time.time()
        delivered = []

        # 检查冷却
        if current_time - self.last_alert_time < self.cooldown_period:
            return []

        for alert_id, alert in list(self.alerts.items()):
            if alert.status != AlertStatus.PENDING:
                continue

            # 检查是否应该发送
            if self._should_deliver(alert, current_time):
                alert.status = AlertStatus.ACTIVE
                alert.delivered_at = current_time
                self.last_alert_time = current_time
                delivered.append(alert)

                # 记录历史
                self.alert_history.append({
                    "alert_id": alert_id,
                    "delivered_at": current_time,
                    "type": alert.alert_type.value,
                    "priority": alert.priority.name,
                })

        return delivered

    def dismiss_alert(self, alert_id: str, reason: str = ""):
        """
        关闭提醒

        Args:
            alert_id: 提醒ID
            reason: 关闭原因
        """
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.DISMISSED
            self.alerts[alert_id].dismiss_reason = reason

    def get_pending_alerts(self, limit: int = 10) -> List[Alert]:
        """获取待发送的提醒"""
        pending = [
            a for a in self.alerts.values()
            if a.status == AlertStatus.PENDING
        ]
        # 按优先级排序
        pending.sort(key=lambda a: a.priority.value, reverse=True)
        return pending[:limit]

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃的提醒"""
        return [
            a for a in self.alerts.values()
            if a.status == AlertStatus.ACTIVE
        ]

    def should_remind(self, context: Dict = None) -> bool:
        """
        判断是否应该主动提醒

        Args:
            context: 当前上下文

        Returns:
            是否应该提醒
        """
        # 检查免打扰时段
        if self._is_quiet_hours():
            return False

        # 检查是否有待发送的高优先级提醒
        pending = self.get_pending_alerts()
        return any(a.priority.value >= AlertPriority.HIGH.value for a in pending)

    def get_reminder_suggestions(self, context: Dict = None) -> List[Dict]:
        """
        获取提醒建议

        Args:
            context: 上下文

        Returns:
            提醒建议列表
        """
        suggestions = []

        # 基于时间
        current_hour = time.localtime().tm_hour
        if current_hour == 9:
            suggestions.append({
                "type": "daily_greeting",
                "message": "早上好！今天有什么计划吗？",
                "priority": AlertPriority.LOW,
            })
        elif current_hour == 12:
            suggestions.append({
                "type": "lunch_reminder",
                "message": "午餐时间到了，记得休息一下。",
                "priority": AlertPriority.LOW,
            })
        elif current_hour == 18:
            suggestions.append({
                "type": "end_of_day",
                "message": "今天工作辛苦了，需要总结一下吗？",
                "priority": AlertPriority.LOW,
            })

        # 基于上下文
        if context:
            if context.get("idle_time", 0) > 3600:  # 1小时未交互
                suggestions.append({
                    "type": "idle_check",
                    "message": "您已经很久没有交互了，需要帮助吗？",
                    "priority": AlertPriority.LOW,
                })

        return suggestions

    def set_quiet_hours(self, start_hour: int, end_hour: int):
        """
        设置免打扰时段

        Args:
            start_hour: 开始小时
            end_hour: 结束小时
        """
        self.quiet_hours.start_hour = start_hour
        self.quiet_hours.end_hour = end_hour
        self.quiet_hours.enabled = True

    def disable_quiet_hours(self):
        """关闭免打扰"""
        self.quiet_hours.enabled = False

    def cleanup_expired(self) -> int:
        """清理过期提醒"""
        current_time = time.time()
        count = 0

        for alert in self.alerts.values():
            if alert.status == AlertStatus.PENDING:
                if alert.alert_type == AlertType.SCHEDULED:
                    if alert.scheduled_time > 0 and current_time > alert.scheduled_time + 3600:
                        alert.status = AlertStatus.EXPIRED
                        count += 1

        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取提醒系统统计"""
        status_counts = {}
        for alert in self.alerts.values():
            status = alert.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_alerts": len(self.alerts),
            "status_distribution": status_counts,
            "delivered_count": len(self.alert_history),
            "quiet_hours": {
                "enabled": self.quiet_hours.enabled,
                "start": self.quiet_hours.start_hour,
                "end": self.quiet_hours.end_hour,
            },
        }

    def _should_deliver(self, alert: Alert, current_time: float) -> bool:
        """判断是否应该发送提醒"""
        # 免打扰时段检查（高优先级例外）
        if self._is_quiet_hours() and alert.priority.value < AlertPriority.URGENT.value:
            return False

        # 定时提醒
        if alert.alert_type == AlertType.SCHEDULED:
            if alert.scheduled_time > 0 and current_time >= alert.scheduled_time:
                return True
            return False

        # 事件触发和情境感知
        if alert.trigger_condition:
            try:
                return alert.trigger_condition()
            except Exception:
                return False

        return False

    def _is_quiet_hours(self) -> bool:
        """检查是否在免打扰时段"""
        if not self.quiet_hours.enabled:
            return False

        current_hour = time.localtime().tm_hour

        if self.quiet_hours.start_hour > self.quiet_hours.end_hour:
            # 跨天（如22:00-08:00）
            return current_hour >= self.quiet_hours.start_hour or current_hour < self.quiet_hours.end_hour
        else:
            return self.quiet_hours.start_hour <= current_hour < self.quiet_hours.end_hour
