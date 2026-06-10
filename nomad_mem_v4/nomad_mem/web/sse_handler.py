"""
SSE Handler - Server-Sent Events流式聊天端点

核心功能:
1. SSE流式响应 - 逐token发送LLM输出
2. 事件格式化 - 标准SSE event/data格式
3. 心跳保持 - 防止连接超时
4. 错误处理 - 优雅的错误传播
"""
import asyncio
import json
import time
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse


class SSEHandler:
    """SSE流式处理器"""

    def __init__(self, dialog_manager):
        """
        初始化SSE处理器

        Args:
            dialog_manager: DialogManager实例
        """
        self.dialog_manager = dialog_manager
        self.heartbeat_interval = 15  # 15秒心跳间隔

    async def chat_stream(
        self,
        request: Request,
        message: str,
        user_id: str = "default",
    ) -> AsyncGenerator[str, None]:
        """
        SSE流式聊天端点

        事件格式:
        - event: token - 流式文本片段
        - event: done - 对话完成
        - event: error - 错误信息
        - event: heartbeat - 心跳保持

        Args:
            request: FastAPI请求对象
            message: 用户消息
            user_id: 用户ID

        Yields:
            SSE格式化的字符串
        """
        if not message.strip():
            yield self._format_event("error", {"detail": "消息不能为空"})
            return

        try:
            # 注入用户消息到对话历史
            self.dialog_manager.history.append({"role": "user", "content": message})

            # 查询记忆
            memory_context = ""
            if self.dialog_manager.memory_bridge:
                memories = self.dialog_manager.memory_bridge.relevant_memories(
                    message, k=self.dialog_manager.memory_injection_k
                )
                if memories:
                    memory_context = self.dialog_manager._format_memories_for_context(memories)
                    self.dialog_manager.memory_bridge.record_query(message, memories, user_id)

            # 构建消息
            messages = self.dialog_manager._build_messages(memory_context)

            # 流式生成
            full_response = ""
            async for chunk in self.dialog_manager.llm.stream_generate(messages):
                full_response += chunk
                yield self._format_event("token", {"content": chunk})

                # 检查客户端是否断开连接
                if await request.is_disconnected():
                    break

            # 添加回复到历史
            if full_response:
                self.dialog_manager.history.append(
                    {"role": "assistant", "content": full_response}
                )

            # 存储到记忆
            if self.dialog_manager.memory_bridge:
                self.dialog_manager.memory_bridge.store_conversation(
                    message, full_response, user_id
                )

            # 裁剪历史
            self.dialog_manager._trim_history()

            # 发送完成事件
            yield self._format_event("done", {
                "content": full_response,
                "timestamp": time.time(),
            })

        except Exception as e:
            yield self._format_event("error", {"detail": str(e)})

    async def heartbeat_stream(
        self, request: Request
    ) -> AsyncGenerator[str, None]:
        """
        心跳流 - 保持连接活跃

        Args:
            request: FastAPI请求对象

        Yields:
            心跳事件
        """
        while True:
            if await request.is_disconnected():
                break
            yield self._format_event("heartbeat", {"timestamp": time.time()})
            await asyncio.sleep(self.heartbeat_interval)

    def _format_event(self, event: str, data: dict) -> str:
        """
        格式化SSE事件

        Args:
            event: 事件类型
            data: 事件数据

        Returns:
            SSE格式的字符串
        """
        data_str = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {data_str}\n\n"


def add_sse_routes(app: FastAPI, dialog_manager):
    """
    为FastAPI应用添加SSE路由

    Args:
        app: FastAPI应用
        dialog_manager: DialogManager实例
    """
    handler = SSEHandler(dialog_manager)

    @app.post("/api/chat/stream")
    async def chat_stream_api(request: Request):
        """
        SSE流式聊天API

        Request body:
        {
            "message": "你好",
            "user_id": "default"
        }

        SSE Events:
        - event: token - 流式文本片段
        - event: done - 对话完成
        - event: error - 错误信息
        """
        try:
            body = await request.json()
            message = body.get("message", "")
            user_id = body.get("user_id", "default")
        except Exception:
            return StreamingResponse(
                iter([handler._format_event("error", {"detail": "无效的请求格式"})]),
                media_type="text/event-stream",
            )

        return StreamingResponse(
            handler.chat_stream(request, message, user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/api/heartbeat")
    async def heartbeat_api(request: Request):
        """心跳端点 - 保持连接活跃"""
        return StreamingResponse(
            handler.heartbeat_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    return handler
