"""
Proactive Responder - 主动响应引擎

基于意图预测结果生成主动响应，让 Jarvis 能在用户开口前提供有价值的内容。

核心特性:
- 响应模板: 不同预测意图对应不同的响应模板
- 上下文感知: 根据场景/情绪/经验调整响应内容
- 渐进主动: 只在置信度足够高时才主动响应
- 用户控制: 用户可以调节主动程度

设计原则:
- 主动但不打扰: 高置信度才主动
- 响应简洁: 主动响应不超过2句话
- 可撤回: 用户随时可以关闭主动响应
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ProactiveResponse:
    """主动响应

    Attributes:
        should_respond: 是否应该主动响应
        response_text: 响应文本
        predicted_intent: 预测的意图
        confidence: 置信度
        action_suggestion: 建议的动作
    """
    should_respond: bool
    response_text: str = ""
    predicted_intent: str = ""
    confidence: float = 0.0
    action_suggestion: str = ""

    def to_dict(self) -> Dict:
        return {
            "should_respond": self.should_respond,
            "response_text": self.response_text,
            "predicted_intent": self.predicted_intent,
            "confidence": self.confidence,
            "action_suggestion": self.action_suggestion,
        }


class ProactiveResponder:
    """
    主动响应引擎

    基于意图预测生成主动响应。

    使用示例:
        >>> responder = ProactiveResponder()
        >>> prediction = IntentPrediction("schedule", 0.8, "reason")
        >>> response = responder.generate_response(prediction)
        >>> if response.should_respond:
        ...     print(response.response_text)
    """

    # 主动响应阈值
    DEFAULT_THRESHOLD = 0.4

    # 意图到响应模板的映射
    INTENT_RESPONSE_TEMPLATES = {
        "schedule": "看起来您可能需要安排日程，需要我帮您查看今天的空档吗？",
        "query": "有什么我可以帮您查询的吗？",
        "reminder": "需要我为您设置提醒吗？",
        "email": "需要我帮您处理邮件吗？",
        "chat": "想聊点什么？",
        "task": "有什么任务需要我协助吗？",
        "meeting": "需要帮您预定会议室或安排会议吗？",
        "weather": "需要查看天气情况吗？",
        "health": "需要关注健康相关的信息吗？",
        "learning": "需要学习资源推荐吗？",
    }

    # 意图到建议动作的映射
    INTENT_ACTION_SUGGESTIONS = {
        "schedule": "查看日历空档",
        "query": "准备搜索",
        "reminder": "打开提醒设置",
        "email": "检查收件箱",
        "task": "加载任务列表",
        "meeting": "查看可用会议室",
        "weather": "获取天气预报",
    }

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        proactive_level: str = "balanced",
    ):
        self.threshold = threshold
        self.proactive_level = proactive_level  # "minimal", "balanced", "aggressive"
        self._level_multipliers = {
            "minimal": 1.5,     # 需要更高置信度才主动
            "balanced": 1.0,
            "aggressive": 0.7,  # 更低置信度就主动
        }

    def generate_response(
        self,
        prediction,
        context: Optional[Dict] = None,
    ) -> ProactiveResponse:
        """
        基于预测生成主动响应

        Args:
            prediction: IntentPrediction 对象
            context: 可选上下文

        Returns:
            ProactiveResponse
        """
        if prediction is None:
            return ProactiveResponse(should_respond=False)

        # 调整阈值
        multiplier = self._level_multipliers.get(self.proactive_level, 1.0)
        adjusted_threshold = self.threshold * multiplier

        # 检查置信度
        if prediction.confidence < adjusted_threshold:
            return ProactiveResponse(
                should_respond=False,
                predicted_intent=prediction.predicted_intent,
                confidence=prediction.confidence,
            )

        # 生成响应
        intent = prediction.predicted_intent
        response_text = self._get_response_text(intent, context)
        action = self._get_action_suggestion(intent)

        return ProactiveResponse(
            should_respond=True,
            response_text=response_text,
            predicted_intent=intent,
            confidence=prediction.confidence,
            action_suggestion=action,
        )

    def generate_top_response(
        self,
        predictions: List,
        context: Optional[Dict] = None,
    ) -> ProactiveResponse:
        """
        基于预测列表生成最高置信度的主动响应

        Args:
            predictions: IntentPrediction 列表
            context: 可选上下文

        Returns:
            ProactiveResponse
        """
        if not predictions:
            return ProactiveResponse(should_respond=False)

        top = predictions[0]
        return self.generate_response(top, context)

    def set_threshold(self, threshold: float):
        """设置主动响应阈值"""
        self.threshold = max(0.1, min(threshold, 0.9))

    def set_proactive_level(self, level: str):
        """设置主动程度: minimal/balanced/aggressive"""
        if level in self._level_multipliers:
            self.proactive_level = level

    def _get_response_text(self, intent: str, context: Optional[Dict]) -> str:
        """获取响应文本"""
        template = self.INTENT_RESPONSE_TEMPLATES.get(intent)
        if template:
            return template

        # 通用响应
        return f"我注意到您可能需要处理 {intent} 相关的事务，需要协助吗？"

    def _get_action_suggestion(self, intent: str) -> str:
        """获取建议动作"""
        return self.INTENT_ACTION_SUGGESTIONS.get(intent, "")

    def get_config(self) -> Dict:
        """获取当前配置"""
        return {
            "threshold": self.threshold,
            "proactive_level": self.proactive_level,
            "adjusted_threshold": self.threshold * self._level_multipliers.get(self.proactive_level, 1.0),
        }
