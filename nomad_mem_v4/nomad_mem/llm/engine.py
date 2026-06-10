"""
LLM引擎 - 支持OpenAI兼容API
支持后端: vLLM / llama.cpp / Ollama / 任何OpenAI兼容API
"""
import json
import httpx
from typing import AsyncGenerator


class LLMEngine:
    """LLM引擎，通过OpenAI兼容API调用"""

    def __init__(self, config: dict):
        """
        初始化LLM引擎

        Args:
            config: LLM配置字典，包含:
                - backend: 后端类型 (openai_compatible/ollama/vllm)
                - api_base: API基础URL
                - api_key: API密钥(可选)
                - model: 模型名称
                - max_tokens: 最大输出token数
                - temperature: 温度参数
                - top_p: top_p参数
        """
        self.backend = config.get("backend", "openai_compatible")
        self.api_base = config.get("api_base", "http://localhost:8000/v1").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "qwen2.5-7b-instruct")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
        self.top_p = config.get("top_p", 0.9)

        # 构建HTTP客户端
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.Client(
            base_url=self.api_base,
            headers=headers,
            timeout=120.0,
        )

    def generate(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """
        生成响应（支持tool calling）

        Args:
            messages: 对话消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            tools: 工具定义列表，格式为 [{"type": "function", "function": {...}}, ...]
            max_tokens: 最大输出token数（可选，覆盖默认值）

        Returns:
            响应字典，包含:
                - content: 文本内容
                - tool_calls: 工具调用列表（如有）
                - finish_reason: 结束原因
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        if tools:
            payload["tools"] = tools

        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        message = choice["message"]

        result = {
            "content": message.get("content", ""),
            "finish_reason": choice.get("finish_reason", "stop"),
        }

        # 解析tool_calls
        if "tool_calls" in message and message["tool_calls"]:
            result["tool_calls"] = []
            for tc in message["tool_calls"]:
                tool_call = {
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "arguments": json.loads(tc["function"]["arguments"]),
                }
                result["tool_calls"].append(tool_call)

        return result

    async def stream_generate(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成响应

        Args:
            messages: 对话消息列表
            tools: 工具定义列表（可选）
            max_tokens: 最大输出token数（可选）

        Yields:
            流式文本片段
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(
            base_url=self.api_base,
            timeout=120.0,
        ) as async_client:
            if self.api_key:
                async_client.headers["Authorization"] = f"Bearer {self.api_key}"

            async with async_client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    def get_tools_definition(self, skills: list) -> list[dict]:
        """
        将技能列表转换为OpenAI工具定义格式

        Args:
            skills: 技能列表，每个技能需有 name, description, parameters 属性

        Returns:
            工具定义列表，格式为 [{"type": "function", "function": {...}}, ...]
        """
        tools = []
        for skill in skills:
            tool_def = {
                "type": "function",
                "function": {
                    "name": skill.name,
                    "description": skill.description,
                    "parameters": skill.parameters,
                },
            }
            tools.append(tool_def)
        return tools

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()
