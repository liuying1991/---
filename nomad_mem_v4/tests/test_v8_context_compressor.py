"""
Context Compressor 测试
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestContextCompressor:
    """上下文压缩器测试"""

    def test_compress_messages(self):
        """测试压缩消息"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()

        messages = [
            {"role": "user", "content": "帮我计算1+1"},
            {"role": "assistant", "content": None, "tool_calls": [{
                "id": "tc1",
                "function": {"name": "calculate", "arguments": '{"expression": "1+1"}'}
            }]},
            {"role": "tool", "tool_call_id": "tc1", "content": "2"},
            {"role": "assistant", "content": "结果是2"},
        ]

        summary = compressor.compress_messages(messages)
        assert summary.intent  # 应该提取到意图
        assert len(summary.skill_calls) == 1
        assert summary.skill_calls[0]["tool"] == "calculate"
        assert summary.conversation_summary

    def test_compress_to_memory_entry(self):
        """测试压缩为记忆条目"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()

        messages = [
            {"role": "user", "content": "Python编程教程"},
            {"role": "assistant", "content": "Python是一门优秀的编程语言，建议从基础语法开始学习。"},
        ]

        entry = compressor.compress_to_memory_entry(messages)
        assert "content" in entry
        assert "Python" in entry["content"]
        assert "importance" in entry
        assert "tags" in entry

    def test_should_compress(self):
        """测试判断是否需要压缩"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor({"max_summary_tokens": 1000, "compression_threshold": 0.7})

        # 超过阈值
        assert compressor.should_compress([], 800) is True
        # 低于阈值
        assert compressor.should_compress([], 500) is False

    def test_observation_masking(self):
        """测试 observation masking"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()

        messages = [
            {"role": "user", "content": "消息1"},
            {"role": "assistant", "content": "回复1"},
            {"role": "user", "content": "消息2"},
            {"role": "assistant", "content": "回复2"},
        ]

        # 压缩前两条
        compressor.compress_messages(messages[:2], max_messages=2)

        # 获取未masking的消息
        unmasked = compressor.get_masked_messages(messages)
        assert len(unmasked) <= len(messages)

    def test_compress_with_tool_calls(self):
        """测试带工具调用的压缩"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()

        messages = [
            {"role": "user", "content": "创建文件"},
            {"role": "assistant", "content": None, "tool_calls": [{
                "id": "tc1",
                "function": {"name": "file_create", "arguments": '{"path": "/test.txt", "content": "hello"}'}
            }]},
            {"role": "tool", "tool_call_id": "tc1", "content": "文件已创建"},
            {"role": "assistant", "content": "文件已创建成功"},
        ]

        summary = compressor.compress_messages(messages)
        assert len(summary.skill_calls) == 1
        assert summary.skill_calls[0]["tool"] == "file_create"
        assert "result" in summary.skill_calls[0]

    def test_create_zone(self):
        """测试创建压缩区域"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()
        zone = compressor.create_zone("intent", "用户意图", "用户想学习Python", importance=0.8)
        assert zone.zone_id == "intent"
        assert zone.importance == 0.8
        assert zone.masked is False

        # 应用 masking
        compressor.mask_zone("intent")
        assert compressor.zones["intent"].masked is True

    def test_compress_fallback_on_error(self):
        """测试压缩错误回退"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()

        # 空消息列表
        entry = compressor.compress_to_memory_entry([])
        assert "content" in entry

    def test_extract_intent(self):
        """测试意图提取"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()

        assert compressor._extract_intent("你好") == "聊天"
        assert compressor._extract_intent("帮助我") == "帮助"
        assert compressor._extract_intent("计算1+1") == "计算"
        assert compressor._extract_intent("查询天气") == "查询"

    def test_calculate_importance(self):
        """测试重要性计算"""
        from nomad_mem.memory.context_compressor import StructuredSummary, ContextCompressor

        compressor = ContextCompressor()

        # 空摘要
        empty = StructuredSummary()
        empty_score = compressor._calculate_importance(empty)
        assert 0.0 <= empty_score <= 1.0

        # 有意图和决策
        full = StructuredSummary(
            intent="计算",
            key_decisions=["选择方案A"],
            skill_calls=[{"tool": "calculate"}]
        )
        full_score = compressor._calculate_importance(full)
        assert full_score > empty_score

    def test_get_stats(self):
        """测试获取统计"""
        from nomad_mem.memory.context_compressor import ContextCompressor

        compressor = ContextCompressor()
        compressor.compress_messages([
            {"role": "user", "content": "测试"},
            {"role": "assistant", "content": "回复"},
        ])

        stats = compressor.get_stats()
        assert "total_compressions" in stats
        assert stats["total_compressions"] >= 1

    def test_extract_tags(self):
        """测试标签提取"""
        from nomad_mem.memory.context_compressor import StructuredSummary, ContextCompressor

        compressor = ContextCompressor()

        summary = StructuredSummary(
            intent="计算",
            skill_calls=[{"tool": "calculate"}, {"tool": "file_read"}]
        )
        tags = compressor._extract_tags(summary)
        assert "intent:计算" in tags
        assert "skill:calculate" in tags
        assert "skill:file_read" in tags


class TestStructuredSummary:
    """结构化摘要测试"""

    def test_structured_summary_defaults(self):
        """测试默认值"""
        from nomad_mem.memory.context_compressor import StructuredSummary

        summary = StructuredSummary()
        assert summary.intent == ""
        assert summary.key_decisions == []
        assert summary.skill_calls == []
        assert summary.conversation_summary == ""
        assert summary.next_steps == []

    def test_structured_summary_with_data(self):
        """测试带数据的摘要"""
        from nomad_mem.memory.context_compressor import StructuredSummary

        summary = StructuredSummary(
            intent="查询",
            key_decisions=["使用方案A"],
            skill_calls=[{"tool": "search"}],
            conversation_summary="用户查询信息",
            next_steps=["等待结果"]
        )
        assert summary.intent == "查询"
        assert len(summary.key_decisions) == 1
        assert len(summary.skill_calls) == 1
