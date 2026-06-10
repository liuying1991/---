"""
SSE Handler 测试
"""
import os
import sys
import json
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestSSEHandler:
    """SSE处理器测试"""

    def test_format_event(self):
        """测试事件格式化"""
        from nomad_mem.web.sse_handler import SSEHandler

        mock_dm = MagicMock()
        handler = SSEHandler(mock_dm)

        result = handler._format_event("token", {"content": "Hello"})
        assert "event: token" in result
        assert "content" in result
        assert "Hello" in result

    def test_format_event_done(self):
        """测试完成事件格式化"""
        from nomad_mem.web.sse_handler import SSEHandler

        mock_dm = MagicMock()
        handler = SSEHandler(mock_dm)

        result = handler._format_event("done", {"content": "Full response"})
        assert "event: done" in result
        assert "Full response" in result

    def test_format_event_error(self):
        """测试错误事件格式化"""
        from nomad_mem.web.sse_handler import SSEHandler

        mock_dm = MagicMock()
        handler = SSEHandler(mock_dm)

        result = handler._format_event("error", {"detail": "Test error"})
        assert "event: error" in result
        assert "Test error" in result

    def test_empty_message(self):
        """测试空消息处理"""
        from nomad_mem.web.sse_handler import SSEHandler

        mock_dm = MagicMock()
        handler = SSEHandler(mock_dm)

        async def run_test():
            events = []
            mock_request = MagicMock()
            mock_request.is_disconnected = AsyncMock(return_value=False)

            async for event in handler.chat_stream(mock_request, "", "default"):
                events.append(event)

            assert len(events) == 1
            assert "event: error" in events[0]

        asyncio.run(run_test())

    def test_chat_stream_with_mock_llm(self):
        """测试带mock LLM的流式聊天"""
        from nomad_mem.web.sse_handler import SSEHandler

        mock_dm = MagicMock()
        mock_dm.history = []
        mock_dm.memory_bridge = None
        mock_dm.memory_injection_k = 5
        mock_dm._build_messages = MagicMock(return_value=[{"role": "user", "content": "test"}])
        mock_dm._trim_history = MagicMock()

        # mock async generator
        async def mock_stream(messages):
            yield "Hello"
            yield " "
            yield "World"

        mock_dm.llm.stream_generate = mock_stream

        handler = SSEHandler(mock_dm)

        async def run_test():
            events = []
            mock_request = MagicMock()
            mock_request.is_disconnected = AsyncMock(return_value=False)

            async for event in handler.chat_stream(mock_request, "test message", "user1"):
                events.append(event)

            # 应该有 token 事件和 done 事件
            token_events = [e for e in events if "event: token" in e]
            done_events = [e for e in events if "event: done" in e]

            assert len(token_events) == 3  # "Hello", " ", "World"
            assert len(done_events) == 1

            # 验证历史已添加
            assert len(mock_dm.history) == 2  # user + assistant

        asyncio.run(run_test())

    def test_add_sse_routes(self):
        """测试添加SSE路由"""
        from nomad_mem.web.sse_handler import add_sse_routes
        from fastapi import FastAPI

        app = FastAPI()
        mock_dm = MagicMock()
        handler = add_sse_routes(app, mock_dm)

        # 验证路由已添加
        routes = [r.path for r in app.routes]
        assert "/api/chat/stream" in routes
        assert "/api/heartbeat" in routes

    def test_sse_handler_heartbeat(self):
        """测试心跳流"""
        from nomad_mem.web.sse_handler import SSEHandler

        mock_dm = MagicMock()
        handler = SSEHandler(mock_dm)
        handler.heartbeat_interval = 0.1  # 快速测试

        async def run_test():
            events = []
            mock_request = MagicMock()
            mock_request.is_disconnected = AsyncMock(side_effect=[False, False, True])

            async for event in handler.heartbeat_stream(mock_request):
                events.append(event)
                if len(events) >= 2:
                    break

            assert len(events) >= 1
            assert all("event: heartbeat" in e for e in events)

        asyncio.run(run_test())
