"""
LLM记忆压缩器

用LLM将冗长对话压缩为结构化摘要，替代原有的关键词规则压缩。
"""
import json
from typing import Optional


class LLMCompressor:
    """使用LLM进行智能记忆压缩"""

    def __init__(self, llm_engine):
        """
        初始化

        Args:
            llm_engine: LLMEngine实例
        """
        self.llm = llm_engine

    def compress_conversation(self, messages: list[dict]) -> Optional[dict]:
        """
        将对话压缩为结构化摘要

        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}, ...]

        Returns:
            压缩结果字典，包含:
                - summary: 对话摘要
                - key_decisions: 关键决策列表
                - user_preferences: 用户偏好列表
                - important_facts: 重要事实列表
                - entities: 实体列表
        """
        # 构建对话文本
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"AI: {content}")

        conversation_text = "\n".join(lines)

        prompt = f"""请分析以下对话，提取关键信息并以JSON格式返回。

对话内容：
{conversation_text}

请提取以下信息，返回JSON格式（确保是有效的JSON）：
- summary: 一句话对话摘要
- key_decisions: 关键决策（数组）
- user_preferences: 用户偏好（数组）
- important_facts: 重要事实（数组）
- entities: 提到的实体（数组）

如果没有提取到某类信息，返回空数组。"""

        try:
            result = self.llm.generate([{"role": "user", "content": prompt}], max_tokens=512)
            content = result.get("content", "").strip()

            # 提取JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())
        except (json.JSONDecodeError, Exception) as e:
            # 回退到简单摘要
            return {
                "summary": conversation_text[:200] + "..." if len(conversation_text) > 200 else conversation_text,
                "key_decisions": [],
                "user_preferences": [],
                "important_facts": [],
                "entities": [],
                "error": str(e),
            }

    def compress_to_memory_entry(self, messages: list[dict]) -> Optional[dict]:
        """
        将对话压缩为记忆条目

        Args:
            messages: 对话消息列表

        Returns:
            记忆条目字典
        """
        compressed = self.compress_conversation(messages)
        if not compressed:
            return None

        return {
            "content": compressed.get("summary", ""),
            "key_decisions": compressed.get("key_decisions", []),
            "user_preferences": compressed.get("user_preferences", []),
            "important_facts": compressed.get("important_facts", []),
            "entities": compressed.get("entities", []),
        }
