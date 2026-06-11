"""
Scene Automation Engine - 场景自动化引擎

将场景管理器与自主引擎连接起来，根据场景自动触发动作。

核心特性:
- 自动化规则管理: 创建、启用、禁用、删除规则
- 多触发器类型: 场景变化、时间、条件、情绪、组合触发
- 动作执行: 执行预设的自动化动作
- 执行历史追踪: 记录每次规则执行的结果
- 统计分析: 规则执行统计

设计原则:
- 监听场景变化和其他触发器，自动执行动作
- 动作可以是改变问候语、调整干扰频率、启用/禁用工具等
- 纯 Python 实现，无外部依赖
"""
import uuid
import time
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# ─── Enums ───────────────────────────────────────────────────────────────────


class TriggerType(Enum):
    """触发器类型"""
    SCENE_CHANGE = "scene_change"       # 场景变化触发
    TIME = "time"                       # 时间触发
    CONDITION = "condition"             # 条件触发
    EMOTION = "emotion"                 # 情绪触发
    COMBINATION = "combination"         # 组合触发


class ActionType(Enum):
    """动作类型"""
    SET_GREETING_STYLE = "set_greeting_style"
    REDUCE_INTERRUPTIONS = "reduce_interruptions"
    INCREASE_INTERRUPTIONS = "increase_interruptions"
    ENABLE_TOOL = "enable_tool"
    DISABLE_TOOL = "disable_tool"
    SET_PERSONALITY_MODE = "set_personality_mode"
    EXECUTE_TASK = "execute_task"


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class AutomationRule:
    """自动化规则

    Attributes:
        rule_id: 规则唯一标识
        name: 规则名称
        scene_type: 关联的场景类型（可选）
        trigger_type: 触发器类型
        trigger_config: 触发器配置字典
        actions: 动作列表
        enabled: 是否启用
        execution_count: 执行次数
        last_executed: 最后执行时间戳
    """
    rule_id: str
    name: str
    scene_type: Optional[str] = None
    trigger_type: TriggerType = TriggerType.SCENE_CHANGE
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    enabled: bool = True
    execution_count: int = 0
    last_executed: Optional[float] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["trigger_type"] = self.trigger_type.value
        d["actions"] = list(self.actions)
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "AutomationRule":
        data = dict(data)
        if isinstance(data.get("trigger_type"), str):
            data["trigger_type"] = TriggerType(data["trigger_type"])
        # Filter to only dataclass fields
        allowed = {
            "rule_id", "name", "scene_type", "trigger_type",
            "trigger_config", "actions", "enabled",
            "execution_count", "last_executed",
        }
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


@dataclass
class AutomationEvent:
    """自动化执行事件

    Attributes:
        event_id: 事件唯一标识
        rule_id: 关联的规则ID
        timestamp: 事件时间戳
        event_type: 事件类型
        context: 执行上下文
        result: 执行结果
        success: 是否执行成功
    """
    event_id: str
    rule_id: str
    timestamp: float = field(default_factory=time.time)
    event_type: str = "execution"
    context: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "AutomationEvent":
        data = dict(data)
        allowed = {
            "event_id", "rule_id", "timestamp", "event_type",
            "context", "result", "success",
        }
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


# ─── SceneAutomation ─────────────────────────────────────────────────────────


class SceneAutomation:
    """
    场景自动化引擎

    监听场景变化和其他触发器，自动执行预定义的动作。
    动作包括：改变问候语、调整主动提醒频率、启用/禁用工具、
    切换人格模式、执行特定任务等。

    Args:
        scene_manager: 场景管理器实例（可选）
        tool_registry: 工具注册表实例（可选）

    使用示例:
        >>> auto = SceneAutomation()
        >>> rule_id = auto.create_automation_rule(
        ...     "工作模式问候", "work", "scene_change",
        ...     {}, ["set_greeting_style:professional"]
        ... )
        >>> events = auto.check_and_execute({"scene_type": "work"})
        >>> auto.get_stats()
    """

    # 内置动作处理器
    _builtin_handlers: Dict[str, Callable] = {}

    def __init__(self, scene_manager=None, tool_registry=None):
        self.scene_manager = scene_manager
        self.tool_registry = tool_registry

        # 规则存储: rule_id -> AutomationRule
        self._rules: Dict[str, AutomationRule] = {}

        # 事件历史: list of AutomationEvent
        self._event_history: List[AutomationEvent] = []

        # 自定义动作处理器: action_name -> callable
        self._action_handlers: Dict[str, Callable] = {}

        # 初始化内置动作处理器
        self._init_builtin_handlers()

    def _init_builtin_handlers(self):
        """初始化内置动作处理器"""
        self._builtin_handlers = {
            "set_greeting_style": self._handle_set_greeting_style,
            "reduce_interruptions": self._handle_reduce_interruptions,
            "increase_interruptions": self._handle_increase_interruptions,
            "enable_tool": self._handle_enable_tool,
            "disable_tool": self._handle_disable_tool,
            "set_personality_mode": self._handle_set_personality_mode,
            "execute_task": self._handle_execute_task,
        }

    # ── Rule Management ─────────────────────────────────────────────────

    def create_automation_rule(
        self,
        name: str,
        scene_type: Optional[str],
        trigger_type: str,
        trigger_config: Dict[str, Any],
        actions: List[str],
    ) -> str:
        """
        创建自动化规则

        Args:
            name: 规则名称
            scene_type: 关联的场景类型（可选）
            trigger_type: 触发器类型 (scene_change/time/condition/emotion/combination)
            trigger_config: 触发器配置字典
            actions: 动作列表

        Returns:
            rule_id: 新规则的ID

        Raises:
            ValueError: trigger_type 或 actions 无效
        """
        valid_triggers = {t.value for t in TriggerType}
        if trigger_type not in valid_triggers:
            raise ValueError(
                f"Invalid trigger_type '{trigger_type}'. Must be one of: {valid_triggers}"
            )

        if not actions:
            raise ValueError("actions must be a non-empty list")

        rule_id = f"auto_rule_{uuid.uuid4().hex[:12]}"
        rule = AutomationRule(
            rule_id=rule_id,
            name=name,
            scene_type=scene_type,
            trigger_type=TriggerType(trigger_type),
            trigger_config=trigger_config,
            actions=list(actions),
            enabled=True,
            execution_count=0,
            last_executed=None,
        )

        self._rules[rule_id] = rule
        logger.info("Created automation rule: %s (%s)", name, rule_id)
        return rule_id

    def enable_rule(self, rule_id: str) -> bool:
        """
        启用规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功启用
        """
        rule = self._rules.get(rule_id)
        if rule is None:
            return False
        rule.enabled = True
        logger.info("Enabled rule: %s", rule_id)
        return True

    def disable_rule(self, rule_id: str) -> bool:
        """
        禁用规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功禁用
        """
        rule = self._rules.get(rule_id)
        if rule is None:
            return False
        rule.enabled = False
        logger.info("Disabled rule: %s", rule_id)
        return True

    def delete_rule(self, rule_id: str) -> bool:
        """
        删除规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功删除
        """
        if rule_id not in self._rules:
            return False
        del self._rules[rule_id]
        logger.info("Deleted rule: %s", rule_id)
        return True

    # ── Rule Execution ──────────────────────────────────────────────────

    def check_and_execute(self, context: Dict[str, Any]) -> List[AutomationEvent]:
        """
        检查所有启用规则是否匹配当前上下文，执行匹配的规则

        匹配逻辑:
        1. 遍历所有启用的规则
        2. 根据 trigger_type 检查规则是否匹配当前上下文
        3. 对匹配的规则执行其动作
        4. 记录执行事件到历史

        Args:
            context: 当前上下文字典，可能包含:
                - scene_type: 当前场景类型
                - emotion: 当前情绪
                - time_of_day: 当前时间段
                - 其他自定义条件

        Returns:
            List[AutomationEvent]: 执行的事件列表
        """
        events = []

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            if self._is_rule_matched(rule, context):
                event = self._execute_rule(rule, context)
                events.append(event)

        return events

    def _is_rule_matched(
        self, rule: AutomationRule, context: Dict[str, Any]
    ) -> bool:
        """
        检查规则是否匹配当前上下文

        Args:
            rule: 自动化规则
            context: 当前上下文

        Returns:
            是否匹配
        """
        trigger = rule.trigger_type
        config = rule.trigger_config

        if trigger == TriggerType.SCENE_CHANGE:
            # 检查场景类型是否匹配
            if rule.scene_type:
                ctx_scene = context.get("scene_type")
                if ctx_scene and ctx_scene != rule.scene_type:
                    return False
            return True

        elif trigger == TriggerType.TIME:
            # 检查时间段
            time_of_day = context.get("time_of_day")
            if config.get("time_of_day"):
                allowed = config["time_of_day"]
                if isinstance(allowed, str):
                    allowed = [allowed]
                if time_of_day is None:
                    return False  # 需要时间段信息但上下文未提供
                return time_of_day in allowed
            return True

        elif trigger == TriggerType.CONDITION:
            # 检查自定义条件
            for key, expected in config.items():
                actual = context.get(key)
                if actual is None:
                    return False
                if isinstance(expected, list):
                    if actual not in expected:
                        return False
                else:
                    if actual != expected:
                        return False
            return True

        elif trigger == TriggerType.EMOTION:
            # 检查情绪匹配
            emotion = context.get("emotion")
            if config.get("emotion"):
                allowed = config["emotion"]
                if isinstance(allowed, str):
                    allowed = [allowed]
                if emotion is None:
                    return False  # 需要情绪信息但上下文未提供
                return emotion in allowed
            return True

        elif trigger == TriggerType.COMBINATION:
            # 组合触发：需要所有子条件都满足
            sub_conditions = config.get("conditions", [])
            if not sub_conditions:
                return True
            for sub in sub_conditions:
                sub_type = sub.get("type")
                sub_config = sub.get("config", {})
                if not self._check_single_condition(sub_type, sub_config, context):
                    return False
            return True

        return True

    def _check_single_condition(
        self, cond_type: str, config: Dict, context: Dict
    ) -> bool:
        """检查单个条件是否满足"""
        if cond_type == "scene_type":
            ctx_scene = context.get("scene_type")
            expected = config.get("value")
            if expected:
                if ctx_scene is None:
                    return False  # 缺少必需的上下文
                if ctx_scene != expected:
                    return False
        elif cond_type == "emotion":
            emotion = context.get("emotion")
            expected = config.get("value")
            if expected:
                if emotion is None:
                    return False  # 缺少必需的上下文
                if emotion != expected:
                    return False
        elif cond_type == "time_of_day":
            tod = context.get("time_of_day")
            expected = config.get("value")
            if expected:
                if tod is None:
                    return False  # 缺少必需的上下文
                if tod != expected:
                    return False
        return True

    def _execute_rule(
        self, rule: AutomationRule, context: Dict[str, Any]
    ) -> AutomationEvent:
        """
        执行规则的所有动作

        Args:
            rule: 自动化规则
            context: 执行上下文

        Returns:
            AutomationEvent: 执行事件记录
        """
        event_id = f"event_{uuid.uuid4().hex[:12]}"
        action_results = []
        all_success = True

        for action in rule.actions:
            try:
                result = self._execute_action(action, context)
                action_results.append({"action": action, "result": result, "success": True})
            except Exception as e:
                logger.warning(
                    "Action '%s' failed in rule '%s': %s", action, rule.rule_id, e
                )
                action_results.append({"action": action, "result": str(e), "success": False})
                all_success = False

        # 更新规则执行统计
        rule.execution_count += 1
        rule.last_executed = time.time()

        # 创建事件记录
        event = AutomationEvent(
            event_id=event_id,
            rule_id=rule.rule_id,
            timestamp=time.time(),
            event_type="execution",
            context=context,
            result=action_results,
            success=all_success,
        )

        # 记录到历史
        self._event_history.append(event)

        logger.info(
            "Executed rule '%s' (%s): %d actions, success=%s",
            rule.name, rule.rule_id, len(rule.actions), all_success,
        )
        return event

    def _execute_action(self, action: str, context: Dict[str, Any]) -> Any:
        """
        执行单个动作

        动作格式: "action_type" 或 "action_type:argument"

        Args:
            action: 动作字符串
            context: 执行上下文

        Returns:
            动作执行结果
        """
        # 解析动作
        if ":" in action:
            action_type, argument = action.split(":", 1)
        else:
            action_type = action
            argument = None

        # 优先使用自定义处理器
        handler = self._action_handlers.get(action_type)
        if handler is None:
            handler = self._builtin_handlers.get(action_type)

        if handler is None:
            raise ValueError(f"No handler for action type: {action_type}")

        return handler(argument, context)

    # ── Built-in Action Handlers ────────────────────────────────────────

    def _handle_set_greeting_style(self, argument, context):
        """设置问候语风格"""
        return {"greeting_style": argument or "default"}

    def _handle_reduce_interruptions(self, argument, context):
        """减少主动提醒频率"""
        return {"interruption_level": "reduced"}

    def _handle_increase_interruptions(self, argument, context):
        """增加主动提醒频率"""
        return {"interruption_level": "increased"}

    def _handle_enable_tool(self, argument, context):
        """启用工具"""
        if argument and self.tool_registry:
            self.tool_registry.update_tool_status(argument, "available")
        return {"tool_enabled": argument}

    def _handle_disable_tool(self, argument, context):
        """禁用工具"""
        if argument and self.tool_registry:
            self.tool_registry.update_tool_status(argument, "disabled")
        return {"tool_disabled": argument}

    def _handle_set_personality_mode(self, argument, context):
        """设置人格模式"""
        valid_modes = {"professional", "casual", "empathetic", "humorous", "concise"}
        if argument and argument not in valid_modes:
            logger.warning(
                "Unknown personality mode '%s', using 'default'. Valid: %s",
                argument, valid_modes,
            )
        return {"personality_mode": argument or "default"}

    def _handle_execute_task(self, argument, context):
        """执行特定任务"""
        return {"task_executed": argument}

    # ── Custom Handler Registration ─────────────────────────────────────

    def register_action_handler(self, action_type: str, handler: Callable):
        """
        注册自定义动作处理器

        Args:
            action_type: 动作类型名称
            handler: 处理函数，签名为 (argument, context) -> result
        """
        self._action_handlers[action_type] = handler

    def unregister_action_handler(self, action_type: str) -> bool:
        """
        注销自定义动作处理器

        Args:
            action_type: 动作类型名称

        Returns:
            是否成功注销
        """
        if action_type in self._action_handlers:
            del self._action_handlers[action_type]
            return True
        return False

    # ── Query Methods ───────────────────────────────────────────────────

    def get_rules(self, scene_type: Optional[str] = None) -> List[AutomationRule]:
        """
        获取规则列表

        Args:
            scene_type: 可选，按场景类型过滤

        Returns:
            规则列表
        """
        rules = list(self._rules.values())
        if scene_type:
            rules = [r for r in rules if r.scene_type == scene_type]
        return rules

    def get_rule_history(
        self, rule_id: Optional[str] = None, limit: int = 20
    ) -> List[AutomationEvent]:
        """
        获取规则执行历史

        Args:
            rule_id: 可选，按规则ID过滤
            limit: 返回数量限制

        Returns:
            事件列表，按时间降序
        """
        events = self._event_history
        if rule_id:
            events = [e for e in events if e.rule_id == rule_id]

        # 按时间降序
        sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return sorted_events[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典:
            - total_rules: 规则总数
            - enabled_rules: 启用规则数
            - disabled_rules: 禁用规则数
            - by_trigger_type: 按触发器类型分类
            - by_scene_type: 按场景类型分类
            - total_executions: 总执行次数
            - success_rate: 成功率
        """
        total = len(self._rules)
        enabled = sum(1 for r in self._rules.values() if r.enabled)
        disabled = total - enabled

        by_trigger: Dict[str, int] = {}
        by_scene: Dict[str, int] = {}
        total_executions = 0

        for rule in self._rules.values():
            tt = rule.trigger_type.value
            by_trigger[tt] = by_trigger.get(tt, 0) + 1

            st = rule.scene_type or "none"
            by_scene[st] = by_scene.get(st, 0) + 1

            total_executions += rule.execution_count

        # 计算成功率
        events = self._event_history
        total_events = len(events)
        success_count = sum(1 for e in events if e.success)
        success_rate = round(success_count / total_events, 4) if total_events > 0 else 0.0

        return {
            "total_rules": total,
            "enabled_rules": enabled,
            "disabled_rules": disabled,
            "by_trigger_type": by_trigger,
            "by_scene_type": by_scene,
            "total_executions": total_executions,
            "success_rate": success_rate,
        }

    # ── Lifecycle ───────────────────────────────────────────────────────

    def close(self):
        """清理资源"""
        self._rules.clear()
        self._event_history.clear()
        self._action_handlers.clear()
        logger.info("SceneAutomation closed")
