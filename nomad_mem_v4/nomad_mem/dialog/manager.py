"""
对话管理器 - 协调LLM、技能、记忆的核心枢纽

核心职责:
1. 管理对话历史和上下文
2. 执行tool calling循环（LLM → 工具调用 → 结果回传 → 再次LLM）
3. 注入记忆上下文
4. 上下文压缩防止溢出
"""
import time
import json
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class DialogManager:
    """对话管理器"""

    def __init__(self, llm_engine, memory_bridge=None, skill_registry=None, config: dict = None):
        """
        初始化对话管理器

        Args:
            llm_engine: LLM引擎实例
            memory_bridge: 记忆桥接器实例（可选）
            skill_registry: 技能注册表实例（可选）
            config: 对话配置字典
        """
        self.llm = llm_engine
        self.memory_bridge = memory_bridge
        self.skill_registry = skill_registry
        self.config = config or {}

        # 对话配置
        self.system_prompt = self.config.get("system_prompt", "你是Jarvis，一个智能AI管家。")
        self.max_history = self.config.get("max_history_messages", 50)
        self.max_context_tokens = self.config.get("max_context_tokens", 4000)
        self.memory_injection_k = self.config.get("memory_injection_k", 5)

        # 对话历史
        self.history = []

    def chat(self, user_message: str, user_id: str = "default") -> str:
        """
        执行一轮对话

        Args:
            user_message: 用户消息
            user_id: 用户ID（用于记忆隔离）

        Returns:
            AI回复文本
        """
        # 1. 注入用户消息
        self.history.append({"role": "user", "content": user_message})

        # 2. 查询相关记忆并注入
        memory_context = ""
        if self.memory_bridge:
            memories = self.memory_bridge.relevant_memories(user_message, k=self.memory_injection_k)
            if memories:
                memory_context = self._format_memories_for_context(memories)
                # 记录记忆查询到工作记忆
                self.memory_bridge.record_query(user_message, memories, user_id)

        # 3. 构建完整消息列表
        messages = self._build_messages(memory_context)

        # 4. 执行tool calling循环
        response = self._tool_calling_loop(messages)

        # 5. 添加助手回复到历史
        if response:
            self.history.append({"role": "assistant", "content": response})

        # 6. 存储对话到记忆系统
        if self.memory_bridge:
            self.memory_bridge.store_conversation(user_message, response, user_id)

        # 7. 裁剪历史
        self._trim_history()

        return response

    async def chat_stream(self, user_message: str, user_id: str = "default"):
        """
        流式对话（异步生成器）

        Args:
            user_message: 用户消息
            user_id: 用户ID

        Yields:
            流式文本片段
        """
        # 注入用户消息
        self.history.append({"role": "user", "content": user_message})

        # 查询记忆
        memory_context = ""
        if self.memory_bridge:
            memories = self.memory_bridge.relevant_memories(user_message, k=self.memory_injection_k)
            if memories:
                memory_context = self._format_memories_for_context(memories)
                self.memory_bridge.record_query(user_message, memories, user_id)

        # 构建消息
        messages = self._build_messages(memory_context)

        # 流式生成（不支持流式过程中的tool calling）
        full_response = ""
        async for chunk in self.llm.stream_generate(messages):
            full_response += chunk
            yield chunk

        # 添加回复到历史
        if full_response:
            self.history.append({"role": "assistant", "content": full_response})

        # 存储到记忆
        if self.memory_bridge:
            self.memory_bridge.store_conversation(user_message, full_response, user_id)

        # 裁剪历史
        self._trim_history()

    def _build_messages(self, memory_context: str = "") -> list[dict]:
        """
        构建完整的消息列表（包含system prompt + 记忆上下文 + 历史）

        Args:
            memory_context: 记忆上下文字符串

        Returns:
            消息列表
        """
        # System prompt
        system_content = self.system_prompt
        if memory_context:
            system_content += f"\n\n--- 相关记忆 ---\n{memory_context}"

        messages = [{"role": "system", "content": system_content}]

        # 添加历史（排除最后一条用户消息，因为它稍后单独添加）
        messages.extend(self.history)

        return messages

    def _tool_calling_loop(self, messages: list[dict], max_iterations: int = 5) -> str:
        """
        执行tool calling循环

        流程:
        1. 调用LLM获取响应
        2. 如果有tool_calls，执行技能并回传结果
        3. 如果没有tool_calls，返回最终回复
        4. 重复最多max_iterations次

        Args:
            messages: 消息列表
            max_iterations: 最大迭代次数（防止无限循环）

        Returns:
            最终回复文本
        """
        if not self.skill_registry:
            # 没有技能注册表，直接返回LLM回复
            result = self.llm.generate(messages)
            return result.get("content", "")

        # 获取工具定义
        tools = self.llm.get_tools_definition(self.skill_registry.get_all_skills())

        for iteration in range(max_iterations):
            # 调用LLM
            result = self.llm.generate(messages, tools=tools)
            content = result.get("content", "")
            tool_calls = result.get("tool_calls", [])

            # 如果没有工具调用，返回最终回复
            if not tool_calls:
                return content

            # 执行工具调用
            for tool_call in tool_calls:
                tool_id = tool_call["id"]
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                logger.info(f"执行工具: {tool_name}, 参数: {tool_args}")

                # 执行技能
                try:
                    skill = self.skill_registry.get_skill(tool_name)
                    if skill:
                        output = skill.execute(tool_args)
                        tool_result = str(output)
                    else:
                        tool_result = f"Error: 技能 '{tool_name}' 不存在"
                except Exception as e:
                    tool_result = f"Error: {str(e)}"

                logger.info(f"工具结果: {tool_result[:200]}...")

                # 将工具调用和结果添加到消息历史
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_id,
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args),
                        },
                    }],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": tool_result,
                })

        # 达到最大迭代次数，返回最后一次内容
        return content

    def _format_memories_for_context(self, memories: list[dict]) -> str:
        """
        将记忆格式化为对话上下文字符串

        Args:
            memories: 记忆列表

        Returns:
            格式化的记忆字符串
        """
        lines = []
        for i, mem in enumerate(memories, 1):
            content = mem.get("content", "")
            summary = mem.get("summary", "")
            importance = mem.get("importance", 0)
            created_at = mem.get("created_at", "")

            if summary:
                lines.append(f"[{i}] [{summary}] (重要性:{importance:.2f}) {content}")
            else:
                lines.append(f"[{i}] (重要性:{importance:.2f}) {content}")

        return "\n".join(lines)

    def _trim_history(self):
        """裁剪对话历史，防止超出最大限制"""
        while len(self.history) > self.max_history:
            # 移除最早的一对消息（user + assistant）
            if len(self.history) >= 2:
                self.history = self.history[2:]
            else:
                self.history = self.history[1:]

    def clear_history(self):
        """清空对话历史"""
        self.history = []

    def get_history(self) -> list[dict]:
        """获取对话历史"""
        return self.history.copy()
