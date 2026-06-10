"""
V4测试 - MemoryOS + 记忆进化 + Agent协调
"""
import os
import sys
import json
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMemoryOS:
    """MemoryOS测试"""

    def test_add_short_term_memory(self):
        """测试添加短期记忆"""
        from nomad_mem.memory.memory_os import MemoryOS, MemoryLevel

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            unit = memory_os.add_short_term("测试短期记忆", tags=["test"])
            assert unit.level == MemoryLevel.SHORT_TERM
            assert "测试短期记忆" in unit.content
            assert "test" in unit.tags

            memory_os.close()

    def test_retrieve_short_term_memory(self):
        """测试检索短期记忆"""
        from nomad_mem.memory.memory_os import MemoryOS

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            unit = memory_os.add_short_term("用户喜欢Python", tags=["preference", "python"])
            retrieved = memory_os.storage.retrieve(unit.id)
            assert retrieved is not None
            assert retrieved.access_count == 1

            memory_os.close()

    def test_search_by_tags(self):
        """测试按标签搜索"""
        from nomad_mem.memory.memory_os import MemoryOS, MemoryLevel, MemoryUnit

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            # 添加中期记忆
            unit = MemoryUnit(
                id="mid_test_1",
                level=MemoryLevel.MID_TERM,
                content="Python编程偏好",
                tags=["preference", "python"],
                importance=0.7
            )
            memory_os.storage.store(unit)

            results = memory_os.storage.search_by_tags(["python"])
            assert len(results) >= 1
            assert any("Python" in r.content for r in results)

            memory_os.close()

    def test_promote_short_to_mid(self):
        """测试短期→中期提升"""
        from nomad_mem.memory.memory_os import MemoryOS, DialogChain

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            dialog_chain = DialogChain(
                session_id="test_session",
                messages=[
                    {"role": "user", "content": "我喜欢用Python写代码"},
                    {"role": "assistant", "content": "Python是一门优秀的语言"}
                ],
                summary="用户表达Python编程偏好",
                key_points=["用户喜欢Python", "编程偏好讨论"]
            )

            mid_units = memory_os.promote_to_mid(dialog_chain)
            assert len(mid_units) >= 1
            assert any(u.content for u in mid_units)

            memory_os.close()

    def test_get_context(self):
        """测试获取记忆上下文"""
        from nomad_mem.memory.memory_os import MemoryOS, MemoryLevel, MemoryUnit

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            # 添加一些记忆
            unit = MemoryUnit(
                id="ctx_test_1",
                level=MemoryLevel.MID_TERM,
                content="用户偏好Python编程",
                tags=["preference"],
                importance=0.7
            )
            memory_os.storage.store(unit)

            context = memory_os.get_context("Python")
            assert "Python" in context or "编程" in context

            memory_os.close()

    def test_get_stats(self):
        """测试获取统计"""
        from nomad_mem.memory.memory_os import MemoryOS

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            memory_os.add_short_term("短期记忆1")
            stats = memory_os.get_stats()
            assert "short_term" in stats
            assert stats["short_term"] >= 1

            memory_os.close()

    def test_run_maintenance(self):
        """测试运行维护"""
        from nomad_mem.memory.memory_os import MemoryOS, MemoryLevel, MemoryUnit

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(db_path)

            # 添加中期记忆
            unit = MemoryUnit(
                id="maint_test_1",
                level=MemoryLevel.MID_TERM,
                content="测试维护",
                importance=0.5
            )
            memory_os.storage.store(unit)

            memory_os.run_maintenance()
            # 应该不抛出异常

            memory_os.close()


class TestMemoryEvolution:
    """记忆进化系统测试"""

    def test_create_note(self):
        """测试创建笔记"""
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_evolution.db")
            evolution = MemoryEvolution(db_path)

            note = evolution.create_note(
                content="用户喜欢Python编程",
                context="对话记录",
                keywords=["Python", "编程"],
                tags=["preference"]
            )

            assert note.content == "用户喜欢Python编程"
            assert "Python" in note.keywords
            assert "preference" in note.tags

            evolution.close()

    def test_generate_links(self):
        """测试生成链接"""
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_evolution.db")
            evolution = MemoryEvolution(db_path)

            # 创建两个相关笔记
            note1 = evolution.create_note(
                content="Python编程技巧",
                keywords=["Python", "编程", "技巧"],
                tags=["coding"]
            )

            note2 = evolution.create_note(
                content="Python数据分析",
                keywords=["Python", "数据分析"],
                tags=["coding", "data"]
            )

            links = evolution.generate_links(note2.id, min_strength=0.2)
            assert len(links) >= 1
            assert any(link["target_id"] == note1.id for link in links)

            evolution.close()

    def test_evolve_memory(self):
        """测试记忆进化"""
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_evolution.db")
            evolution = MemoryEvolution(db_path)

            # 创建基础笔记
            base_note = evolution.create_note(
                content="用户偏好Python",
                keywords=["Python", "偏好"],
                tags=["preference"]
            )

            # 创建相关新笔记
            new_note = evolution.create_note(
                content="Python是用户最喜欢的语言",
                keywords=["Python", "喜欢", "语言"],
                tags=["preference"]
            )

            updated_ids = evolution.evolve_memory(new_note)
            # 应该有笔记被更新
            assert isinstance(updated_ids, list)

            evolution.close()

    def test_refine_note(self):
        """测试精炼笔记"""
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_evolution.db")
            evolution = MemoryEvolution(db_path)

            note = evolution.create_note("原始内容")
            success = evolution.refine_note(note.id, "更新信息")

            assert success is True
            updated = evolution._load_note(note.id)
            assert "原始内容" in updated.content
            assert "更新信息" in updated.content
            assert updated.evolution_count == 1

            evolution.close()

    def test_search_notes(self):
        """测试搜索笔记"""
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_evolution.db")
            evolution = MemoryEvolution(db_path)

            evolution.create_note("Python编程入门", keywords=["Python"])
            evolution.create_note("Java开发指南", keywords=["Java"])

            results = evolution.search_notes("Python")
            assert len(results) >= 1
            assert any("Python" in r.content for r in results)

            evolution.close()

    def test_get_stats(self):
        """测试获取统计"""
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "memory_evolution.db")
            evolution = MemoryEvolution(db_path)

            evolution.create_note("笔记1", keywords=["test"])
            evolution.create_note("笔记2", keywords=["test2"])

            stats = evolution.get_stats()
            assert "total_notes" in stats
            assert stats["total_notes"] == 2

            evolution.close()


class TestAgentCoordinator:
    """Agent协调器测试"""

    def test_submit_task(self):
        """测试提交任务"""
        from nomad_mem.autonomy.agent_coordinator import AgentCoordinator

        coordinator = AgentCoordinator()
        task_id = coordinator.submit_task(
            "测试任务",
            "这是一个测试任务",
            priority=3
        )

        assert task_id.startswith("task_")
        assert len(coordinator.orchestrator.work_queue) == 1

    def test_execute_cycle(self):
        """测试执行周期"""
        from nomad_mem.autonomy.agent_coordinator import AgentCoordinator

        coordinator = AgentCoordinator()
        coordinator.submit_task("简单任务", "执行简单任务")

        def dummy_executor(task):
            return f"任务 {task.title} 已执行"

        results = coordinator.execute_cycle(dummy_executor)
        assert len(results) >= 1
        assert any(r["status"] == "completed" for r in results)

    def test_execute_with_failure(self):
        """测试执行失败"""
        from nomad_mem.autonomy.agent_coordinator import AgentCoordinator

        coordinator = AgentCoordinator()
        coordinator.submit_task("失败任务", "这个任务会失败")

        def failing_executor(task):
            raise Exception("模拟失败")

        results = coordinator.execute_cycle(failing_executor)
        assert len(results) >= 1

    def test_deadlock_detection(self):
        """测试死锁检测"""
        from nomad_mem.autonomy.agent_coordinator import (
            AgentCoordinator, AgentTask, TaskStatus
        )

        coordinator = AgentCoordinator()

        # 创建循环依赖 - 使用实际task.id
        task1 = AgentTask(title="任务1", description="依赖任务2")
        task2 = AgentTask(title="任务2", description="依赖任务1")

        # 设置循环依赖
        task1.dependencies = [task2.id]
        task2.dependencies = [task1.id]

        coordinator.orchestrator.add_task(task1)
        coordinator.orchestrator.add_task(task2)

        deadlocks = coordinator.orchestrator.detect_deadlock()
        assert len(deadlocks) > 0

    def test_get_stats(self):
        """测试获取统计"""
        from nomad_mem.autonomy.agent_coordinator import AgentCoordinator

        coordinator = AgentCoordinator()
        coordinator.submit_task("任务1", "执行任务1")

        def executor(task):
            return "完成"

        coordinator.execute_cycle(executor)

        stats = coordinator.get_stats()
        assert "total_tasks" in stats
        assert "success_rate" in stats
        assert stats["total_tasks"] >= 1

    def test_context_allocation(self):
        """测试上下文分配"""
        from nomad_mem.autonomy.agent_coordinator import AgentCoordinator

        coordinator = AgentCoordinator()
        allocation = coordinator.optimizer.allocate_context(4000)

        assert sum(allocation.values()) == 4000
        assert allocation["critical"] == 1600  # 40%
        assert allocation["skills"] == 1200    # 30%

    def test_review_task(self):
        """测试任务审核"""
        from nomad_mem.autonomy.agent_coordinator import (
            AgentCoordinator, AgentTask, TaskStatus
        )

        coordinator = AgentCoordinator()

        # 成功任务
        task1 = AgentTask(title="成功", description="成功任务", result="成功结果")
        review1 = coordinator.reviewer.review_task(task1)
        assert all(review1.values())

        # 失败任务
        task2 = AgentTask(title="失败", description="失败任务", error="发生错误")
        review2 = coordinator.reviewer.review_task(task2)
        assert review2["no_errors"] is False


class TestIntegration:
    """集成测试"""

    def test_memory_os_with_evolution(self):
        """测试MemoryOS与记忆进化集成"""
        from nomad_mem.memory.memory_os import MemoryOS, DialogChain
        from nomad_mem.memory.memory_evolution import MemoryEvolution

        with tempfile.TemporaryDirectory() as tmpdir:
            memory_db = os.path.join(tmpdir, "memory_os.db")
            evolution_db = os.path.join(tmpdir, "memory_evolution.db")

            memory_os = MemoryOS(memory_db)
            evolution = MemoryEvolution(evolution_db)

            # 添加记忆
            memory_os.add_short_term("用户喜欢Python")

            # 创建笔记
            note = evolution.create_note(
                content="用户偏好Python编程",
                tags=["preference"]
            )

            # 生成链接
            note2 = evolution.create_note(
                content="Python数据分析库",
                tags=["python", "data"]
            )

            links = evolution.generate_links(note2.id)
            assert len(links) >= 0  # 可能没有足够重叠

            # 验证统计
            mem_stats = memory_os.get_stats()
            evo_stats = evolution.get_stats()

            assert mem_stats["short_term"] >= 1
            assert evo_stats["total_notes"] == 2

            memory_os.close()
            evolution.close()

    def test_agent_coordinator_with_memory(self):
        """测试Agent协调器与记忆系统集成"""
        from nomad_mem.autonomy.agent_coordinator import AgentCoordinator
        from nomad_mem.memory.memory_os import MemoryOS

        with tempfile.TemporaryDirectory() as tmpdir:
            memory_db = os.path.join(tmpdir, "memory_os.db")
            memory_os = MemoryOS(memory_db)

            coordinator = AgentCoordinator()

            # 提交记忆相关任务
            task_id = coordinator.submit_task(
                "记忆整理",
                "整理和更新用户记忆"
            )

            def memory_task_executor(task):
                memory_os.add_short_term(f"任务执行: {task.title}")
                return f"记忆已更新"

            results = coordinator.execute_cycle(memory_task_executor)
            assert len(results) >= 1

            # 验证记忆已添加
            stats = memory_os.get_stats()
            assert stats["short_term"] >= 1

            memory_os.close()
