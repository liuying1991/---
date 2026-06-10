"""
Context Compressor - 上下文压缩器

参考研究:
1. JetBrains 复杂性研究: simple observation masking 比 complex LLM summarization 更有效
2. ACON (Microsoft 2026): 迭代优化压缩指南
3. Factory AI: 结构化持久化摘要（意图/文件/决策/下一步）

核心设计原则:
- 按区域结构化摘要，而不是简单的文本拼接
- 使用 observation masking 标记已处理的消息
- 分层压缩：消息级别 → 对话级别 → 记忆条目级别
- 保留关键信息（意图、决策、技能调用）
"""
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class CompressionZone:
    """压缩区域 - 按语义分区的上下文"""
    zone_id: str
    name: str
    content: str
    importance: float = 0.5
    masked: bool = False  # observation masking 标记
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class StructuredSummary:
    """结构化摘要"""
    intent: str = ""  # 用户意图
    key_decisions: List[str] = field(default_factory=list)  # 关键决策
    skill_calls: List[Dict] = field(default_factory=list)  # 技能调用记录
    conversation_summary: str = ""  # 对话摘要
    next_steps: List[str] = field(default_factory=list)  # 下一步行动
    created_at: float = field(default_factory=time.time)


class ContextCompressor:
    """上下文压缩器"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_summary_tokens = self.config.get("max_summary_tokens", 1000)
        self.compression_threshold = self.config.get("compression_threshold", 0.7)
        self.zones: Dict[str, CompressionZone] = {}
        self.observation_mask: Dict[str, bool] = {}  # message_id -> masked
        self.summary_history: List[StructuredSummary] = []

    def compress_messages(
        self,
        messages: List[Dict],
        max_messages: int = 10
    ) -> StructuredSummary:
        """
        压缩对话消息为结构化摘要

        基于 JetBrains 研究：简单 observation masking 比复杂 LLM 摘要更有效

        Args:
            messages: 对话消息列表
            max_messages: 保留最近消息数

        Returns:
            结构化摘要
        """
        summary = StructuredSummary()

        # 1. 提取意图（从第一条用户消息）
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            summary.intent = self._extract_intent(user_messages[0].get("content", ""))

        # 2. 提取关键决策（从助手消息）
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        for msg in assistant_messages:
            decision = self._extract_decision(msg)
            if decision:
                summary.key_decisions.append(decision)

        # 3. 提取技能调用
        for msg in messages:
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    summary.skill_calls.append({
                        "tool": tc.get("function", {}).get("name", ""),
                        "args": tc.get("function", {}).get("arguments", ""),
                    })
            elif msg.get("role") == "tool":
                # 关联到最近的技能调用
                if summary.skill_calls:
                    summary.skill_calls[-1]["result"] = msg.get("content", "")[:200]

        # 4. 生成对话摘要（保留最近消息）
        recent = messages[-max_messages:] if len(messages) > max_messages else messages
        summary.conversation_summary = self._summarize_recent(recent)

        # 5. 推断下一步行动
        summary.next_steps = self._infer_next_steps(summary)

        # 应用 observation masking - 标记已处理的消息
        for i, msg in enumerate(messages[:-max_messages]):
            msg_id = f"msg_{i}"
            self.observation_mask[msg_id] = True

        self.summary_history.append(summary)
        return summary

    def to_memory_entry(self, summary: StructuredSummary) -> Dict[str, Any]:
        """
        将结构化摘要转换为记忆条目

        参考 Factory AI 格式：意图/文件/决策/下一步

        Args:
            summary: 结构化摘要

        Returns:
            记忆条目字典
        """
        content_parts = []

        if summary.intent:
            content_parts.append(f"用户意图: {summary.intent}")

        if summary.key_decisions:
            content_parts.append(f"关键决策: {'; '.join(summary.key_decisions)}")

        if summary.skill_calls:
            skills_desc = "; ".join(
                f"{s['tool']}({s.get('args', '')})" for s in summary.skill_calls
            )
            content_parts.append(f"技能调用: {skills_desc}")

        if summary.conversation_summary:
            content_parts.append(f"对话摘要: {summary.conversation_summary}")

        if summary.next_steps:
            content_parts.append(f"下一步: {'; '.join(summary.next_steps)}")

        return {
            "content": "\n".join(content_parts),
            "importance": self._calculate_importance(summary),
            "tags": self._extract_tags(summary),
            "created_at": summary.created_at,
        }

    def compress_to_memory_entry(
        self, messages: List[Dict], max_messages: int = 10
    ) -> Dict[str, Any]:
        """
        便捷方法：压缩消息并直接返回记忆条目

        Args:
            messages: 对话消息列表
            max_messages: 保留最近消息数

        Returns:
            记忆条目
        """
        summary = self.compress_messages(messages, max_messages)
        return self.to_memory_entry(summary)

    def should_compress(self, messages: List[Dict], token_estimate: int) -> bool:
        """
        判断是否需要压缩

        Args:
            messages: 当前消息列表
            token_estimate: 估计的 token 数

        Returns:
            是否需要压缩
        """
        if token_estimate <= 0:
            return False
        ratio = token_estimate / self.max_summary_tokens
        return ratio > self.compression_threshold

    def get_masked_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        获取未被 masking 的消息

        基于 JetBrains 研究：被 masking 的消息表示已处理，不需要再次关注

        Args:
            messages: 消息列表

        Returns:
            未被 masking 的消息
        """
        unmasked = []
        for i, msg in enumerate(messages):
            msg_id = f"msg_{i}"
            if not self.observation_mask.get(msg_id, False):
                unmasked.append(msg)
        return unmasked

    def clear_mask(self):
        """清空 masking 状态"""
        self.observation_mask.clear()

    def get_zones(self) -> List[CompressionZone]:
        """获取所有压缩区域"""
        return list(self.zones.values())

    def create_zone(self, zone_id: str, name: str, content: str, importance: float = 0.5) -> CompressionZone:
        """创建压缩区域"""
        zone = CompressionZone(
            zone_id=zone_id,
            name=name,
            content=content,
            importance=importance,
        )
        self.zones[zone_id] = zone
        return zone

    def mask_zone(self, zone_id: str):
        """对区域应用 masking"""
        if zone_id in self.zones:
            self.zones[zone_id].masked = True
            self.zones[zone_id].updated_at = time.time()

    def _extract_intent(self, message: str) -> str:
        """提取用户意图（简单规则提取）"""
        if not message:
            return ""

        # 关键词匹配
        intent_keywords = {
            "帮助": ["帮助", "help", "怎么做", "如何使用"],
            "计算": ["计算", "算一下", "等于多少"],
            "查询": ["查询", "搜索", "查找", "看看"],
            "创建": ["创建", "新建", "生成", "写一个"],
            "修改": ["修改", "更改", "更新", "调整"],
            "删除": ["删除", "移除", "去掉"],
            "聊天": ["你好", "嗨", "hello", "hi", "在吗"],
        }

        for intent, keywords in intent_keywords.items():
            if any(kw in message.lower() for kw in keywords):
                return intent

        return message[:50]  # 默认截取前50字符

    def _extract_decision(self, message: Dict) -> Optional[str]:
        """从助手消息提取关键决策"""
        content = message.get("content", "")
        if not content:
            return None

        # 提取关键陈述
        decision_markers = ["建议", "推荐", "应该", "最佳", "方案", "选择"]
        for marker in decision_markers:
            if marker in content:
                # 提取包含标记的句子
                sentences = content.replace("。", "。\n").replace("！", "！\n").split("\n")
                for s in sentences:
                    if marker in s:
                        return s.strip()[:100]

        return None

    def _summarize_recent(self, messages: List[Dict]) -> str:
        """生成最近消息摘要"""
        if not messages:
            return ""

        parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content:
                parts.append(f"{role}: {content[:100]}")

        return " | ".join(parts) if parts else ""

    def _infer_next_steps(self, summary: StructuredSummary) -> List[str]:
        """推断下一步行动"""
        steps = []

        # 基于意图推断
        if summary.intent in ["帮助", "查询"]:
            steps.append("等待用户进一步指令")
        elif summary.intent in ["创建", "修改"]:
            steps.append("确认操作结果")
        elif summary.skill_calls:
            steps.append("检查技能执行结果")

        return steps

    def _calculate_importance(self, summary: StructuredSummary) -> float:
        """计算摘要重要性"""
        score = 0.3  # 基础分

        # 有明确意图加分
        if summary.intent:
            score += 0.2

        # 有关键决策加分
        if summary.key_decisions:
            score += 0.1 * min(len(summary.key_decisions), 3)

        # 有技能调用加分
        if summary.skill_calls:
            score += 0.1 * min(len(summary.skill_calls), 3)

        return min(score, 1.0)

    def _extract_tags(self, summary: StructuredSummary) -> List[str]:
        """提取标签"""
        tags = []
        if summary.intent:
            tags.append(f"intent:{summary.intent}")
        for skill in summary.skill_calls:
            tool_name = skill.get("tool", "")
            if tool_name:
                tags.append(f"skill:{tool_name}")
        return tags

    def get_stats(self) -> Dict:
        """获取压缩器统计"""
        return {
            "total_compressions": len(self.summary_history),
            "total_zones": len(self.zones),
            "masked_messages": sum(1 for v in self.observation_mask.values() if v),
            "latest_summary_time": (
                self.summary_history[-1].created_at if self.summary_history else 0
            ),
        }
