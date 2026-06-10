"""
自主意识驱动引擎

核心理念: Jarvis 不是被动应答工具，而是拥有主动感知、主动决策、主动执行能力的AI管家。

自主意识三要素:
1. 感知(Perceive) — 监控系统状态、记忆状态、用户行为模式
2. 评估(Evaluate) — 判断是否需要主动行动、行动优先级
3. 驱动(Act) — 选择合适的技能执行、生成主动建议

触发类型:
- 时间触发: 定时检查、早晚问候
- 状态触发: 系统异常、记忆满溢、磁盘不足
- 行为触发: 用户习惯模式、长时间无交互
- 记忆触发: 重要记忆提醒、遗忘预警
"""
import time
import logging
from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """触发类型"""
    TIMER = "timer"              # 定时触发
    STATE = "state"              # 状态触发
    BEHAVIOR = "behavior"        # 行为触发
    MEMORY = "memory"            # 记忆触发
    MANUAL = "manual"            # 手动触发


class Priority(Enum):
    """优先级"""
    CRITICAL = 10                # 紧急（系统故障）
    HIGH = 7                     # 高（重要提醒）
    MEDIUM = 4                   # 中（建议）
    LOW = 1                      # 低（闲聊）


@dataclass
class TriggerEvent:
    """触发事件"""
    trigger_type: TriggerType
    priority: Priority
    source: str                  # 触发来源
    message: str                 # 触发描述
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ActionProposal:
    """行动提议"""
    action: str                  # 行动名称
    description: str             # 行动描述
    skill_name: Optional[str]    # 关联技能
    skill_args: dict = field(default_factory=dict)
    message: str = ""            # 对用户的消息
    priority: Priority = Priority.MEDIUM
    trigger: Optional[TriggerEvent] = None


class Sensor:
    """感知器基类"""

    def __init__(self, name: str):
        self.name = name

    def sense(self, context: dict) -> list[TriggerEvent]:
        """
        感知环境，返回触发事件列表

        Args:
            context: 感知上下文，包含系统状态、记忆状态等

        Returns:
            触发事件列表
        """
        raise NotImplementedError


class SystemSensor(Sensor):
    """系统状态感知器"""

    def __init__(self):
        super().__init__("system")
        self.last_disk_warning = 0
        self.last_memory_warning = 0
        self.warning_cooldown = 3600  # 1小时冷却

    def sense(self, context: dict) -> list[TriggerEvent]:
        events = []
        now = time.time()

        # 检查磁盘空间
        disk_usage = context.get("disk_usage", {})
        disk_percent = disk_usage.get("percent", 0)
        if disk_percent > 90 and now - self.last_disk_warning > self.warning_cooldown:
            events.append(TriggerEvent(
                trigger_type=TriggerType.STATE,
                priority=Priority.HIGH,
                source=self.name,
                message=f"磁盘空间不足，已使用 {disk_percent:.1f}%",
                data={"disk_percent": disk_percent},
            ))
            self.last_disk_warning = now

        # 检查内存使用
        memory_usage = context.get("memory_usage", {})
        mem_percent = memory_usage.get("percent", 0)
        if mem_percent > 90 and now - self.last_memory_warning > self.warning_cooldown:
            events.append(TriggerEvent(
                trigger_type=TriggerType.STATE,
                priority=Priority.CRITICAL,
                source=self.name,
                message=f"内存使用率过高，已达 {mem_percent:.1f}%",
                data={"memory_percent": mem_percent},
            ))
            self.last_memory_warning = now

        return events


class MemorySensor(Sensor):
    """记忆状态感知器"""

    def __init__(self):
        super().__init__("memory")
        self.last_consolidation_reminder = 0
        self.reminder_cooldown = 7200  # 2小时冷却

    def sense(self, context: dict) -> list[TriggerEvent]:
        events = []
        now = time.time()

        # 工作记忆满溢预警
        working_memory = context.get("working_memory", {})
        wm_size = working_memory.get("size", 0)
        wm_max = working_memory.get("max", 4)
        if wm_size >= wm_max:
            events.append(TriggerEvent(
                trigger_type=TriggerType.MEMORY,
                priority=Priority.MEDIUM,
                source=self.name,
                message="工作记忆已满，建议整理记忆或触发睡眠巩固",
                data={"wm_size": wm_size, "wm_max": wm_max},
            ))

        # 长时间未巩固提醒
        last_consolidation = context.get("last_consolidation_time", 0)
        consolidation_interval = context.get("consolidation_interval", 21600)
        if now - last_consolidation > consolidation_interval * 1.5 and \
           now - self.last_consolidation_reminder > self.reminder_cooldown:
            events.append(TriggerEvent(
                trigger_type=TriggerType.MEMORY,
                priority=Priority.MEDIUM,
                source=self.name,
                message="记忆已长时间未巩固，建议执行睡眠巩固",
            ))
            self.last_consolidation_reminder = now

        return events


class BehaviorSensor(Sensor):
    """用户行为感知器"""

    def __init__(self):
        super().__init__("behavior")
        self.last_interaction_time = 0
        self.greeting_cooldown = 86400  # 24小时
        self.last_greeting_time = 0
        self.idle_reminder_interval = 1800  # 30分钟无交互提醒
        self.last_idle_reminder = 0

    def sense(self, context: dict) -> list[TriggerEvent]:
        events = []
        now = time.time()

        # 长时间无交互 - 空闲提醒
        time_since_interaction = now - self.last_interaction_time
        if time_since_interaction > self.idle_reminder_interval and \
           time_since_interaction < 86400 and \
           now - self.last_idle_reminder > self.idle_reminder_interval:
            events.append(TriggerEvent(
                trigger_type=TriggerType.BEHAVIOR,
                priority=Priority.LOW,
                source=self.name,
                message="你似乎很久没有和我说话了，需要帮忙吗？",
                data={"idle_seconds": time_since_interaction},
            ))
            self.last_idle_reminder = now

        # 早安/晚安问候（每天一次）
        hour = context.get("current_hour", 12)
        if 6 <= hour <= 8 and now - self.last_greeting_time > self.greeting_cooldown:
            events.append(TriggerEvent(
                trigger_type=TriggerType.TIMER,
                priority=Priority.LOW,
                source=self.name,
                message="早上好！今天有什么计划吗？",
            ))
            self.last_greeting_time = now
        elif 22 <= hour <= 23 and now - self.last_greeting_time > self.greeting_cooldown:
            events.append(TriggerEvent(
                trigger_type=TriggerType.TIMER,
                priority=Priority.LOW,
                source=self.name,
                message="夜深了，注意休息。",
            ))
            self.last_greeting_time = now

        return events

    def record_interaction(self):
        """记录用户交互时间"""
        self.last_interaction_time = time.time()


class IntentEngine:
    """意图引擎 - 将触发事件转化为行动提议"""

    def __init__(self):
        self._handlers: dict[TriggerType, list[Callable]] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """注册默认处理器"""
        self._handlers[TriggerType.STATE] = [
            self._handle_system_alert,
        ]
        self._handlers[TriggerType.MEMORY] = [
            self._handle_memory_consolidation,
            self._handle_memory_overflow,
        ]
        self._handlers[TriggerType.BEHAVIOR] = [
            self._handle_idle_reminder,
        ]
        self._handlers[TriggerType.TIMER] = [
            self._handle_greeting,
        ]

    def evaluate(self, event: TriggerEvent, context: dict) -> list[ActionProposal]:
        """
        评估触发事件，生成行动提议

        Args:
            event: 触发事件
            context: 当前上下文

        Returns:
            行动提议列表
        """
        proposals = []
        handlers = self._handlers.get(event.trigger_type, [])
        for handler in handlers:
            result = handler(event, context)
            if result:
                proposals.append(result)
        return proposals

    def _handle_system_alert(self, event: TriggerEvent, context: dict) -> Optional[ActionProposal]:
        """处理系统告警"""
        if event.priority == Priority.CRITICAL:
            return ActionProposal(
                action="system_alert",
                description="系统资源严重不足，需要立即关注",
                skill_name="system_info",
                skill_args={},
                message=f"⚠️ {event.message}，让我查看一下系统状况。",
                priority=Priority.CRITICAL,
                trigger=event,
            )
        elif event.priority == Priority.HIGH:
            return ActionProposal(
                action="disk_warning",
                description="磁盘空间不足预警",
                skill_name="disk_usage",
                skill_args={},
                message=f"注意：{event.message}，建议清理不需要的文件。",
                priority=Priority.HIGH,
                trigger=event,
            )
        return None

    def _handle_memory_consolidation(self, event: TriggerEvent, context: dict) -> Optional[ActionProposal]:
        """处理记忆巩固建议"""
        return ActionProposal(
            action="memory_consolidation",
            description="建议执行记忆巩固",
            skill_name="memory_status",
            skill_args={},
            message=f"💭 {event.message}",
            priority=Priority.MEDIUM,
            trigger=event,
        )

    def _handle_memory_overflow(self, event: TriggerEvent, context: dict) -> Optional[ActionProposal]:
        """处理工作记忆满溢"""
        return ActionProposal(
            action="memory_review",
            description="工作记忆满溢，建议整理",
            skill_name="memory_status",
            skill_args={},
            message=f"🧠 {event.message}，我来帮你整理一下。",
            priority=Priority.MEDIUM,
            trigger=event,
        )

    def _handle_idle_reminder(self, event: TriggerEvent, context: dict) -> Optional[ActionProposal]:
        """处理空闲提醒"""
        return ActionProposal(
            action="idle_check",
            description="用户空闲，主动询问",
            skill_name=None,
            skill_args={},
            message=event.message,
            priority=Priority.LOW,
            trigger=event,
        )

    def _handle_greeting(self, event: TriggerEvent, context: dict) -> Optional[ActionProposal]:
        """处理问候"""
        return ActionProposal(
            action="greeting",
            description="定时问候",
            skill_name=None,
            skill_args={},
            message=event.message,
            priority=Priority.LOW,
            trigger=event,
        )


class AutonomyDriver:
    """
    自主意识驱动引擎

    这是 Jarvis 区别于普通聊天机器人的核心模块。
    它让 AI 拥有"主动性"——不是等人来问，而是主动感知、主动判断、主动行动。
    """

    def __init__(self, dialog_manager=None, config: dict = None):
        """
        初始化自主意识驱动引擎

        Args:
            dialog_manager: 对话管理器实例
            config: 自主意识配置
        """
        self.dialog_manager = dialog_manager
        self.config = config or {}

        # 传感器
        self.sensors = [
            SystemSensor(),
            MemorySensor(),
            BehaviorSensor(),
        ]

        # 意图引擎
        self.intent_engine = IntentEngine()

        # 状态
        self.running = False
        self.last_sense_time = 0
        self.sense_interval = self.config.get("sense_interval", 60)  # 感知间隔（秒）
        self.max_actions_per_cycle = self.config.get("max_actions_per_cycle", 3)

        # 行动历史（防止重复行动）
        self.action_history = []
        self.action_cooldown = self.config.get("action_cooldown", 3600)  # 1小时

    def sense(self, context: dict) -> list[TriggerEvent]:
        """
        感知阶段 — 收集所有传感器的触发事件

        Args:
            context: 感知上下文

        Returns:
            触发事件列表
        """
        all_events = []
        for sensor in self.sensors:
            try:
                events = sensor.sense(context)
                all_events.extend(events)
            except Exception as e:
                logger.error(f"传感器 {sensor.name} 异常: {e}")

        # 按优先级排序
        all_events.sort(key=lambda e: e.priority.value, reverse=True)
        return all_events

    def evaluate(self, events: list[TriggerEvent], context: dict) -> list[ActionProposal]:
        """
        评估阶段 — 将触发事件转化为行动提议

        Args:
            events: 触发事件列表
            context: 当前上下文

        Returns:
            行动提议列表，按优先级排序
        """
        all_proposals = []
        for event in events:
            proposals = self.intent_engine.evaluate(event, context)
            all_proposals.extend(proposals)

        # 去重（相同action在冷却期内）
        now = time.time()
        filtered = []
        for proposal in all_proposals:
            is_cooldown = any(
                h["action"] == proposal.action and
                now - h["timestamp"] < self.action_cooldown
                for h in self.action_history
            )
            if not is_cooldown:
                filtered.append(proposal)

        # 按优先级排序，限制数量
        filtered.sort(key=lambda p: p.priority.value, reverse=True)
        return filtered[:self.max_actions_per_cycle]

    def act(self, proposals: list[ActionProposal]) -> list[str]:
        """
        行动阶段 — 执行行动提议

        Args:
            proposals: 行动提议列表

        Returns:
            执行结果列表
        """
        results = []
        now = time.time()

        for proposal in proposals:
            logger.info(f"执行自主行动: {proposal.action} - {proposal.description}")

            # 记录行动历史
            self.action_history.append({
                "action": proposal.action,
                "timestamp": now,
            })

            # 如果有技能，执行技能
            if proposal.skill_name and self.dialog_manager and self.dialog_manager.skill_registry:
                skill = self.dialog_manager.skill_registry.get_skill(proposal.skill_name)
                if skill:
                    try:
                        skill_result = skill.execute(proposal.skill_args)
                        results.append(f"[{proposal.action}] {proposal.message} -> {skill_result}")
                    except Exception as e:
                        results.append(f"[{proposal.action}] 执行失败: {e}")
                else:
                    results.append(f"[{proposal.action}] 技能不存在: {proposal.skill_name}")
            else:
                # 无技能，直接返回消息
                results.append(f"[{proposal.action}] {proposal.message}")

        # 清理过期行动历史
        self.action_history = [
            h for h in self.action_history
            if now - h["timestamp"] < self.action_cooldown * 2
        ]

        return results

    def cycle(self, context: dict) -> list[str]:
        """
        完整感知→评估→行动循环

        Args:
            context: 感知上下文

        Returns:
            执行结果列表
        """
        now = time.time()
        if now - self.last_sense_time < self.sense_interval:
            return []

        self.last_sense_time = now

        # 1. 感知
        events = self.sense(context)
        if not events:
            return []

        logger.info(f"[Autonomy] 感知到 {len(events)} 个触发事件")

        # 2. 评估
        proposals = self.evaluate(events, context)
        if not proposals:
            logger.info("[Autonomy] 无行动提议（可能在冷却期）")
            return []

        logger.info(f"[Autonomy] 生成 {len(proposals)} 个行动提议")

        # 3. 行动
        results = self.act(proposals)

        # 更新交互时间（如果是用户触发的循环）
        behavior_sensor = next((s for s in self.sensors if isinstance(s, BehaviorSensor)), None)
        if behavior_sensor:
            # 每次自主循环后不更新交互时间，只有用户主动交互时才更新
            pass

        return results

    def on_user_interaction(self):
        """用户交互时调用，更新行为传感器"""
        behavior_sensor = next((s for s in self.sensors if isinstance(s, BehaviorSensor)), None)
        if behavior_sensor:
            behavior_sensor.record_interaction()

    def autonomous_chat(self, context: dict) -> Optional[str]:
        """
        自主发起对话 — Jarvis 主动对用户说话

        这是 Jarvis 区别于普通聊天机器人的核心能力。
        当自主意识判断需要主动联系用户时，直接通过 LLM 生成主动消息。

        Args:
            context: 感知上下文

        Returns:
            主动生成的消息，如果不需要说话返回 None
        """
        # 1. 感知
        events = self.sense(context)
        if not events:
            return None

        # 2. 评估
        proposals = self.evaluate(events, context)
        if not proposals:
            return None

        # 3. 如果有高优先级提案，直接生成主动消息
        high_priority = [p for p in proposals if p.priority.value >= Priority.MEDIUM.value]
        if not high_priority:
            return None

        # 取最高优先级提案
        top = high_priority[0]

        # 记录行动历史
        self.action_history.append({
            "action": f"autonomous_{top.action}",
            "timestamp": time.time(),
        })

        # 如果有技能，先执行技能获取上下文
        skill_context = ""
        if top.skill_name and self.dialog_manager and self.dialog_manager.skill_registry:
            skill = self.dialog_manager.skill_registry.get_skill(top.skill_name)
            if skill:
                try:
                    skill_result = skill.execute(top.skill_args)
                    skill_context = f"\n系统状态: {skill_result[:200]}"
                except Exception:
                    pass

        # 4. 构建自主对话 prompt
        prompt = f"""你是一个智能AI管家 Jarvis。你刚刚感知到以下情况，需要主动联系用户。

感知到的情况: {top.message}
{skill_context}

请生成一条简短、自然、不打扰用户的主动消息。如果是系统告警，要简洁明了；如果是问候，要友好但不过分热情。
消息控制在50字以内。只输出消息内容，不要输出其他内容。"""

        # 5. 通过 LLM 生成主动消息
        if self.dialog_manager and self.dialog_manager.llm:
            try:
                result = self.dialog_manager.llm.generate(
                    [{"role": "user", "content": prompt}],
                    max_tokens=128,
                )
                message = result.get("content", "").strip()
                if message:
                    # 将自主消息添加到对话历史
                    self.dialog_manager.history.append({"role": "assistant", "content": message})
                    return message
            except Exception as e:
                logger.error(f"自主对话生成失败: {e}")

        # 回退：使用预设消息
        return top.message

    def get_status(self) -> dict:
        """获取自主意识状态"""
        return {
            "running": self.running,
            "last_sense_time": self.last_sense_time,
            "sense_interval": self.sense_interval,
            "action_history_count": len(self.action_history),
            "sensors": [s.name for s in self.sensors],
        }
