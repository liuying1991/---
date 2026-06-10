"""
V5集成测试 - 端到端验证
测试: LLM引擎、对话管理器、技能系统、记忆桥接、Web服务
"""
import os
import sys
import json
import tempfile
import pytest

# 确保项目路径可用
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSkillRegistry:
    """技能注册表测试"""

    def test_register_and_get(self):
        from nomad_mem.skills.registry import SkillRegistry
        from nomad_mem.skills.tools import Calculate

        registry = SkillRegistry()
        calc = Calculate()
        registry.register(calc)

        assert registry.get_skill("calculate") is calc
        assert "calculate" in registry.get_skill_names()
        assert len(registry.get_all_skills()) == 1

    def test_unregister(self):
        from nomad_mem.skills.registry import SkillRegistry
        from nomad_mem.skills.tools import Calculate

        registry = SkillRegistry()
        registry.register(Calculate())
        registry.unregister("calculate")

        assert registry.get_skill("calculate") is None


class TestSkills:
    """技能执行测试"""

    def test_calculate(self):
        from nomad_mem.skills.tools import Calculate

        calc = Calculate()
        result = calc.execute({"expression": "2 + 3 * 4"})
        assert "14" in result

    def test_calculate_invalid(self):
        from nomad_mem.skills.tools import Calculate

        calc = Calculate()
        result = calc.execute({"expression": "2 + abc"})
        assert "非法" in result

    def test_datetime(self):
        from nomad_mem.skills.tools import GetDatetime

        dt = GetDatetime()
        result = dt.execute({})
        assert len(result) > 0  # 有返回内容

    def test_execute_command_blacklist(self):
        from nomad_mem.skills.command import ExecuteCommand

        config = {
            "sandbox_enabled": True,
            "work_dir": "/tmp",
            "command_blacklist": ["rm -rf /", "mkfs"],
            "command_whitelist": [],
        }
        cmd = ExecuteCommand(config)
        result = cmd.execute({"command": "rm -rf /"})
        assert "拒绝" in result or "危险" in result

    def test_execute_command_safe(self):
        from nomad_mem.skills.command import ExecuteCommand

        config = {
            "sandbox_enabled": True,
            "work_dir": "/tmp",
            "command_blacklist": [],
            "command_whitelist": [],
        }
        cmd = ExecuteCommand(config)
        result = cmd.execute({"command": "echo hello"})
        assert "hello" in result

    def test_file_operations(self):
        from nomad_mem.skills.files import Sandbox, ReadFile, WriteFile, ListFiles

        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = Sandbox(tmpdir)
            write_skill = WriteFile(sandbox)
            read_skill = ReadFile(sandbox)
            list_skill = ListFiles(sandbox)

            # 写入
            write_result = write_skill.execute({
                "path": "test.txt",
                "content": "hello world",
            })
            assert "写入" in write_result

            # 读取
            read_result = read_skill.execute({"path": "test.txt"})
            assert "hello world" in read_result

            # 列出
            list_result = list_skill.execute({"path": "."})
            assert "test.txt" in list_result

    def test_file_sandbox_escape(self):
        from nomad_mem.skills.files import Sandbox, ReadFile

        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = Sandbox(tmpdir)
            read_skill = ReadFile(sandbox)

            # 尝试逃出沙箱
            result = read_skill.execute({"path": "../../../etc/passwd"})
            assert "拒绝" in result or "逃出" in result

    def test_memory_store_and_recall(self):
        """记忆技能测试（使用mock）"""
        import numpy as np
        from nomad_mem.skills.memory import MemoryRecall, MemoryStore, MemoryStatus
        from nomad_mem.skills.registry import SkillRegistry

        registry = SkillRegistry()

        # 创建mock memory_bridge
        class MockMemoryBridge:
            def __init__(self):
                self.memories = []
                self.encoder = MockEncoder()
                self.vector_store = MockVectorStore()

            def relevant_memories(self, query, k=5):
                return self.memories[:k]

            def store_conversation(self, user_msg, ai_resp, user_id="default"):
                self.memories.append({
                    "content": f"用户: {user_msg}\nAI: {ai_resp}",
                    "source_type": "conversation",
                    "importance": 0.5,
                    "created_at": "2024-01-01",
                    "vector_id": len(self.memories),
                })

            def get_memory_summary(self):
                return {
                    "total_vectors": len(self.memories),
                    "by_type": {"conversation": len(self.memories)},
                    "avg_emotion_score": 0.0,
                    "working_memory": "0/4",
                }

        class MockEncoder:
            def encode_text(self, text):
                return np.random.rand(384).astype(np.float32), text, 0.5

        class MockVectorStore:
            def insert_vector(self, embedding, content, source_type, emotion_score):
                return 1

            def update_last_accessed(self, vector_id):
                pass

        bridge = MockMemoryBridge()
        registry.register(MemoryRecall(bridge))
        registry.register(MemoryStore(bridge))
        registry.register(MemoryStatus(bridge))

        # 存储记忆
        store = registry.get_skill("memory_store")
        result = store.execute({
            "content": "用户喜欢Python",
            "category": "preference",
        })
        assert "已存储" in result

        # 检索记忆
        recall = registry.get_skill("memory_recall")
        result = recall.execute({"query": "Python"})
        # mock没有相似记忆，但至少不报错
        assert result is not None

        # 状态
        status = registry.get_skill("memory_status")
        result = status.execute({})
        assert "状态" in result


class TestDialogManager:
    """对话管理器测试"""

    def test_build_messages(self):
        from nomad_mem.dialog.manager import DialogManager

        class MockLLM:
            def generate(self, messages, tools=None, max_tokens=None):
                return {"content": "Hello!", "finish_reason": "stop"}

            def stream_generate(self, messages, tools=None, max_tokens=None):
                async def gen():
                    yield "Hello!"
                return gen()

            def get_tools_definition(self, skills):
                return []

            def close(self):
                pass

        dm = DialogManager(
            llm_engine=MockLLM(),
            config={"system_prompt": "You are Jarvis.", "max_history_messages": 10},
        )

        messages = dm._build_messages("")
        assert messages[0]["role"] == "system"
        assert "Jarvis" in messages[0]["content"]

    def test_chat_without_llm(self):
        """无LLM时的对话管理（仅测试历史管理）"""
        from nomad_mem.dialog.manager import DialogManager

        class MockLLM:
            def generate(self, messages, tools=None, max_tokens=None):
                return {"content": "test response", "finish_reason": "stop"}

            def get_tools_definition(self, skills):
                return []

            def close(self):
                pass

        dm = DialogManager(
            llm_engine=MockLLM(),
            config={"system_prompt": "test", "max_history_messages": 5},
        )

        response = dm.chat("hello")
        assert response == "test response"
        assert len(dm.get_history()) == 2  # user + assistant

    def test_history_trim(self):
        from nomad_mem.dialog.manager import DialogManager

        class MockLLM:
            def generate(self, messages, tools=None, max_tokens=None):
                return {"content": "ok", "finish_reason": "stop"}

            def get_tools_definition(self, skills):
                return []

            def close(self):
                pass

        dm = DialogManager(
            llm_engine=MockLLM(),
            config={"system_prompt": "test", "max_history_messages": 3},
        )

        # 添加超过限制的消息
        for i in range(10):
            dm.chat(f"message {i}")

        assert len(dm.get_history()) <= 4  # 最多3条+1条新消息


class TestLLMEngine:
    """LLM引擎测试"""

    def test_tool_definition_conversion(self):
        from nomad_mem.llm.engine import LLMEngine
        from nomad_mem.skills.tools import Calculate

        config = {
            "backend": "openai_compatible",
            "api_base": "http://localhost:8000/v1",
            "model": "test-model",
        }
        engine = LLMEngine(config)

        tools = engine.get_tools_definition([Calculate()])
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "calculate"
        assert "parameters" in tools[0]["function"]

        engine.close()


class TestWebServer:
    """Web服务测试"""

    def test_create_app(self):
        from nomad_mem.web.server import create_app
        from nomad_mem.dialog.manager import DialogManager

        class MockLLM:
            def generate(self, messages, tools=None, max_tokens=None):
                return {"content": "ok", "finish_reason": "stop"}

            def get_tools_definition(self, skills):
                return []

            def close(self):
                pass

        dm = DialogManager(llm_engine=MockLLM())
        app = create_app(dm)

        assert app is not None
        assert app.title == "Jarvis v5.0"


class TestRunPyModes:
    """测试run.py的模式解析"""

    def test_config_loading(self):
        """测试配置文件加载"""
        import yaml
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config.yaml"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "llm" in config
        assert "skills" in config
        assert "web" in config
        assert "dialog" in config
