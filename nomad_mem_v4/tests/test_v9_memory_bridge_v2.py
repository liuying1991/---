"""
MemoryBridge V2 测试
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMemoryBridgeV2:
    """记忆桥接器 V2 测试"""

    def test_store_conversation(self):
        """测试存储对话"""
        from nomad_mem.memory_bridge import MemoryBridgeV2
        from nomad_mem.memory.memory_os import MemoryOS

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)
            bridge = MemoryBridgeV2(memory_os=memory_os)

            bridge.store_conversation("你好，我是小明", "你好小明，很高兴认识你")

            stats = memory_os.get_stats()
            assert stats["short_term"] >= 1

            memory_os.close()

    def test_relevant_memories(self):
        """测试检索相关记忆"""
        from nomad_mem.memory_bridge import MemoryBridgeV2
        from nomad_mem.memory.memory_os import MemoryOS

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            # 添加一些记忆
            memory_os.add_short_term("Python编程教程", tags=["python", "tutorial"])
            memory_os.add_short_term("Java基础知识", tags=["java", "basics"])

            bridge = MemoryBridgeV2(memory_os=memory_os)
            memories = bridge.relevant_memories("Python", k=5)

            assert len(memories) >= 1
            assert any("Python" in m["content"] for m in memories)

            memory_os.close()

    def test_record_query(self):
        """测试记录查询"""
        from nomad_mem.memory_bridge import MemoryBridgeV2

        bridge = MemoryBridgeV2()
        bridge.record_query("Python教程", [{"content": "教程内容"}], user_id="user1")

        assert "user1" in bridge.session_queries
        assert len(bridge.session_queries["user1"]) == 1

    def test_compress_and_store(self):
        """测试压缩并存储"""
        from nomad_mem.memory_bridge import MemoryBridgeV2
        from nomad_mem.memory.memory_os import MemoryOS
        from nomad_mem.memory.context_compressor import ContextCompressor

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)
            compressor = ContextCompressor()
            bridge = MemoryBridgeV2(
                memory_os=memory_os,
                context_compressor=compressor
            )

            messages = [
                {"role": "user", "content": "帮我计算1+1"},
                {"role": "assistant", "content": "结果是2"},
            ]

            bridge.compress_and_store(messages, user_id="user1")

            stats = memory_os.get_stats()
            assert stats.get("mid_term", 0) >= 1

            memory_os.close()

    def test_get_memory_summary(self):
        """测试获取记忆摘要"""
        from nomad_mem.memory_bridge import MemoryBridgeV2
        from nomad_mem.memory.memory_os import MemoryOS
        from nomad_mem.memory.memory_evolution import MemoryEvolution
        from nomad_mem.memory.context_compressor import ContextCompressor

        with tempfile.TemporaryDirectory() as tmpdir:
            mem_db = os.path.join(tmpdir, "memory_os.db")
            evo_db = os.path.join(tmpdir, "memory_evolution.db")

            memory_os = MemoryOS(mem_db)
            evolution = MemoryEvolution(evo_db)
            compressor = ContextCompressor()

            bridge = MemoryBridgeV2(
                memory_os=memory_os,
                memory_evolution=evolution,
                context_compressor=compressor
            )

            # 添加一些数据
            memory_os.add_short_term("测试记忆")
            evolution.create_note("测试笔记")
            compressor.compress_messages([{"role": "user", "content": "测试"}])

            summary = bridge.get_memory_summary()
            assert "version" in summary
            assert summary["version"] == "v2"
            assert "memory_os" in summary
            assert "evolution" in summary
            assert "compression" in summary

            memory_os.close()
            evolution.close()

    def test_store_with_evolution(self):
        """测试存储对话+记忆进化"""
        from nomad_mem.memory_bridge import MemoryBridgeV2
        from nomad_mem.memory.memory_os import MemoryOS
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            mem_db = os.path.join(tmpdir, "memory_os.db")
            evo_db = os.path.join(tmpdir, "memory_evolution.db")

            memory_os = MemoryOS(mem_db)
            evolution = MemoryEvolution(evo_db)
            bridge = MemoryBridgeV2(memory_os=memory_os, memory_evolution=evolution)

            bridge.store_conversation("Python好学吗", "Python是一门友好的语言，适合初学者")

            # 验证记忆已存储
            stats = memory_os.get_stats()
            assert stats["short_term"] >= 1

            # 验证笔记已创建
            evo_stats = evolution.get_stats()
            assert evo_stats["total_notes"] >= 1

            memory_os.close()
            evolution.close()

    def test_similarity_calculation(self):
        """测试相似度计算"""
        from nomad_mem.memory_bridge import MemoryBridgeV2

        bridge = MemoryBridgeV2()

        sim = bridge._calc_similarity("Python programming", "Python is a programming language")
        assert sim > 0

        sim_none = bridge._calc_similarity("", "")
        assert sim_none == 0.0

    def test_close(self):
        """测试关闭连接"""
        from nomad_mem.memory_bridge import MemoryBridgeV2
        from nomad_mem.memory.memory_os import MemoryOS

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)
            bridge = MemoryBridgeV2(memory_os=memory_os)

            bridge.close()
            # 不应该抛出异常

    def test_empty_components(self):
        """测试空组件情况"""
        from nomad_mem.memory_bridge import MemoryBridgeV2

        bridge = MemoryBridgeV2()

        # 没有memory_os时应返回空列表
        memories = bridge.relevant_memories("test")
        assert memories == []

        # 存储对话不应抛出异常
        bridge.store_conversation("test", "response")

        # 压缩存储不应抛出异常
        bridge.compress_and_store([{"role": "user", "content": "test"}])

    def test_calc_importance(self):
        """测试重要性计算"""
        from nomad_mem.memory_bridge import MemoryBridgeV2

        bridge = MemoryBridgeV2()

        vector = {
            "emotion_score": 0.8,
            "novelty_score": 0.6,
            "plasticity": 0.5,
        }
        importance = bridge._calc_importance(vector, 0.9)
        assert 0.0 <= importance <= 1.0
