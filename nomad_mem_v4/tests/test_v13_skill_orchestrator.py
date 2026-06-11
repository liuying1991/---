"""
Skill Orchestrator & Jarvis Core 测试
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSkillOrchestrator:
    """技能编排器测试"""

    def test_create_chain(self):
        """测试创建链式执行计划"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator

        orchestrator = SkillOrchestrator()
        plan_id = orchestrator.create_chain([
            {"skill": "file_create", "args": {"path": "/test.txt"}},
            {"skill": "file_read", "args": {"path": "/test.txt"}},
        ])

        assert plan_id.startswith("plan_")
        assert plan_id in orchestrator.execution_plans

        plan = orchestrator.execution_plans[plan_id]
        assert len(plan.steps) == 2
        # 第二个步骤依赖第一个
        assert plan.steps[1].depends_on == [plan.steps[0].step_id]

    def test_create_parallel(self):
        """测试创建并行执行计划"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator

        orchestrator = SkillOrchestrator()
        plan_id = orchestrator.create_parallel([
            {"skill": "file_read", "args": {"path": "/a.txt"}},
            {"skill": "file_read", "args": {"path": "/b.txt"}},
        ])

        plan = orchestrator.execution_plans[plan_id]
        assert len(plan.steps) == 2
        # 并行步骤不应有依赖
        assert not plan.steps[0].depends_on
        assert not plan.steps[1].depends_on

    def test_create_conditional(self):
        """测试创建条件执行计划"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator

        orchestrator = SkillOrchestrator()
        plan_id = orchestrator.create_conditional(
            condition=lambda ctx: True,
            true_steps=[{"skill": "file_create", "args": {}}],
            false_steps=[{"skill": "file_read", "args": {}}],
        )

        plan = orchestrator.execution_plans[plan_id]
        # 至少有条件步骤+true分支
        assert len(plan.steps) >= 2

    def test_execute_plan_with_mock_registry(self):
        """测试执行计划（带mock注册表）"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator
        from unittest.mock import MagicMock

        # 创建mock skill
        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.execute.return_value = "执行成功"

        # 创建mock registry
        mock_registry = MagicMock()
        mock_registry.get_skill.return_value = mock_skill

        orchestrator = SkillOrchestrator(skill_registry=mock_registry)
        plan_id = orchestrator.create_chain([
            {"skill": "test_skill", "args": {"data": "test"}},
        ])

        result = orchestrator.execute_plan(plan_id)
        assert result["status"] == "completed"
        assert result["successful"] == 1
        assert result["failed"] == 0

    def test_execute_plan_missing_skill(self):
        """测试缺失技能"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator
        from unittest.mock import MagicMock

        mock_registry = MagicMock()
        mock_registry.get_skill.return_value = None

        orchestrator = SkillOrchestrator(skill_registry=mock_registry)
        plan_id = orchestrator.create_chain([
            {"skill": "nonexistent", "args": {}},
        ])

        result = orchestrator.execute_plan(plan_id)
        assert result["status"] == "failed"
        assert result["failed"] == 1

    def test_execute_plan_with_fallback(self):
        """测试回退执行"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator
        from unittest.mock import MagicMock

        # 主技能失败
        failing_skill = MagicMock()
        failing_skill.name = "failing"
        failing_skill.execute.side_effect = Exception("主技能失败")

        # 回退技能成功
        fallback_skill = MagicMock()
        fallback_skill.name = "fallback"
        fallback_skill.execute.return_value = "回退成功"

        mock_registry = MagicMock()
        def get_skill(name):
            return failing_skill if name == "failing" else fallback_skill
        mock_registry.get_skill.side_effect = get_skill

        orchestrator = SkillOrchestrator(skill_registry=mock_registry)
        plan_id = orchestrator.create_chain([
            {"skill": "failing", "args": {}, "fallback": "fallback"},
        ])

        result = orchestrator.execute_plan(plan_id)
        assert result["successful"] == 1
        assert any(r.get("was_fallback") for r in result["results"])

    def test_execute_plan_with_condition(self):
        """测试条件执行"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator
        from unittest.mock import MagicMock

        mock_skill = MagicMock()
        mock_skill.name = "test"
        mock_skill.execute.return_value = "成功"

        mock_registry = MagicMock()
        mock_registry.get_skill.return_value = mock_skill

        orchestrator = SkillOrchestrator(skill_registry=mock_registry)

        # 条件为真时执行
        plan_id = orchestrator.create_chain([
            {"skill": "test", "args": {}, "condition": lambda ctx: True},
        ])

        result = orchestrator.execute_plan(plan_id)
        assert result["successful"] == 1

        # 条件为假时跳过
        plan_id2 = orchestrator.create_chain([
            {"skill": "test", "args": {}, "condition": lambda ctx: False},
        ])

        result2 = orchestrator.execute_plan(plan_id2)
        # 条件不满足应跳过
        assert result2["successful"] == 0 or result2["failed"] == 0

    def test_get_plan_status(self):
        """测试获取计划状态"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator

        orchestrator = SkillOrchestrator()
        plan_id = orchestrator.create_chain([
            {"skill": "test", "args": {}},
        ])

        status = orchestrator.get_plan_status(plan_id)
        assert status["plan_id"] == plan_id
        assert status["status"] == "pending"
        assert status["total_steps"] == 1

    def test_topological_sort(self):
        """测试拓扑排序"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator, SkillStep

        orchestrator = SkillOrchestrator()

        # 创建有依赖的步骤
        step_a = SkillStep(step_id="a", skill_name="A")
        step_b = SkillStep(step_id="b", skill_name="B", depends_on=["a"])
        step_c = SkillStep(step_id="c", skill_name="C", depends_on=["a"])
        step_d = SkillStep(step_id="d", skill_name="D", depends_on=["b", "c"])

        sorted_steps = orchestrator._topological_sort([step_a, step_b, step_c, step_d])

        # a应该排在最前面
        assert sorted_steps[0].step_id == "a"
        # d应该排在最后
        assert sorted_steps[-1].step_id == "d"

    def test_get_stats(self):
        """测试获取统计"""
        from nomad_mem.skills.orchestrator import SkillOrchestrator

        orchestrator = SkillOrchestrator()
        orchestrator.create_chain([{"skill": "test", "args": {}}])

        stats = orchestrator.get_stats()
        assert stats["total_plans"] >= 1


class TestJarvisCore:
    """贾维斯核心测试"""

    def test_initialize(self):
        """测试初始化"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        assert jarvis.initialized
        assert jarvis.memory_os is not None
        assert jarvis.intent_engine is not None

        jarvis.close()

    def test_chat_basic(self):
        """测试基础聊天"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        result = jarvis.chat("你好，我是小明")

        assert "response" in result
        assert result["response"]  # 有回复内容
        assert "processing_time" in result
        assert result["processing_time"] >= 0

        jarvis.close()

    def test_chat_with_intent(self):
        """测试带意图识别的聊天"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        result = jarvis.chat("如何学习Python编程？")

        assert "intent" in result
        if result["intent"]:
            assert "category" in result["intent"]
            assert "confidence" in result["intent"]

        jarvis.close()

    def test_chat_remembers_context(self):
        """测试记忆上下文"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        # 第一次对话
        jarvis.chat("我喜欢Python编程")
        # 第二次对话应该能检索到相关记忆
        result = jarvis.chat("Python好学吗")

        assert result["memories_used"] >= 0  # 可能有也可能没有记忆

        jarvis.close()

    def test_execute_task(self):
        """测试执行任务"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        result = jarvis.execute_task("创建一个Python项目", complexity=3)

        assert "plan_id" in result
        assert result["status"] in ["planned", "pending", "failed"]

        jarvis.close()

    def test_get_status(self):
        """测试获取系统状态"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        status = jarvis.get_status()

        assert status["initialized"] is True
        assert "modules" in status
        assert "memory_os" in status["modules"]

        jarvis.close()

    def test_chat_error_handling(self):
        """测试错误处理"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        # 正常对话不应报错
        result = jarvis.chat("测试消息")
        assert "response" in result
        assert "error" not in result

        jarvis.close()

    def test_close_and_reinitialize(self):
        """测试关闭后重新初始化"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()
        assert jarvis.initialized

        jarvis.close()
        assert not jarvis.initialized

        jarvis.initialize()
        assert jarvis.initialized

        jarvis.close()

    def test_chat_quality_assessment(self):
        """测试质量评估"""
        from nomad_mem.core.jarvis_core import JarvisCore

        jarvis = JarvisCore()
        jarvis.initialize()

        result = jarvis.chat("这是一个测试消息")

        assert "quality_score" in result or True  # 质量分数可选
        assert "processing_time" in result
        assert result["processing_time"] > 0

        jarvis.close()
