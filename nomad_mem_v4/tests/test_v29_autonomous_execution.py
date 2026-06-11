"""
test_v29_autonomous_execution.py - 自主行动执行+反思系统端到端测试

测试范围:
- AutonomousExecutor: 自主循环/执行级别/场景行动/安全约束/统计
- ReflectionEngine: 评估/反思/建议/追踪/统计
- JarvisCore集成
"""
import pytest
import time
import os
import tempfile

# ─── AutonomousExecutor Tests ──────────────────────────────────────────────


class TestExecutionLevel:
    """执行级别测试"""

    def test_set_execution_level_valid(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor, ExecutionLevel
        executor = AutonomousExecutor()
        result = executor.set_execution_level("autonomous")
        assert result is True
        assert executor.execution_level == ExecutionLevel.AUTONOMOUS

    def test_set_execution_level_invalid(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        result = executor.set_execution_level("invalid")
        assert result is False

    def test_set_cycle_interval(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.set_cycle_interval(1800)
        assert executor.cycle_interval == 1800

    def test_set_cycle_interval_minimum(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.set_cycle_interval(10)  # Below minimum
        assert executor.cycle_interval == 60.0  # Clamped to 60

    def test_default_config(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor, ExecutionLevel
        executor = AutonomousExecutor()
        assert executor.execution_level == ExecutionLevel.CONFIRM
        assert executor.cycle_interval == 3600
        assert executor.max_actions_per_cycle == 5


class TestActionHandlers:
    """行动处理器测试"""

    def test_register_custom_handler(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.register_action_handler("custom_action", lambda a, u, s: "done")
        assert "custom_action" in executor._action_handlers

    def test_default_handlers_registered(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        assert "organize_knowledge" in executor._action_handlers
        assert "review_experience" in executor._action_handlers
        assert "update_profile" in executor._action_handlers
        assert "analyze_patterns" in executor._action_handlers
        assert "optimize_workflow" in executor._action_handlers


class TestCycleExecution:
    """循环执行测试"""

    def test_run_cycle_no_deps(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        report = executor.run_cycle("user1", scene="work")
        assert report.cycle_id.startswith("cycle_")
        assert report.actions_executed >= 0
        assert "发现 0 个活跃目标" in report.findings

    def test_run_cycle_with_goal_manager(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        from nomad_mem.autonomy.goal_manager import GoalManager
        executor = AutonomousExecutor()
        gm = GoalManager()
        gid = gm.create_goal("user1", "测试目标", priority="high")
        gm.add_subgoals(gid, ["子目标A"])
        report = executor.run_cycle("user1", scene="work", goal_manager=gm)
        assert "发现 1 个活跃目标" in report.findings

    def test_run_cycle_with_goal_planner(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        executor = AutonomousExecutor()
        planner = GoalPlanner()
        report = executor.run_cycle("user1", scene="work", goal_planner=planner)
        assert report.cycle_id.startswith("cycle_")

    def test_run_cycle_autonomous_level(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.set_execution_level("autonomous")
        report = executor.run_cycle("user1", scene="work")
        assert report.cycle_id.startswith("cycle_")
        # Work scene should generate organize_knowledge action
        assert report.actions_executed >= 0

    def test_run_cycle_with_experience_replay(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        from nomad_mem.autonomy.experience_replay import ExperienceReplay, ExperienceType, ExperienceOutcome
        executor = AutonomousExecutor()
        executor.set_execution_level("autonomous")
        replay = ExperienceReplay()
        # Record some failures to trigger pattern analysis action
        for i in range(5):
            replay.record_experience(
                user_id="user1", intent="test", context="{}",
                action_taken="test_action", result="failed",
                exp_type=ExperienceType.FAILURE, outcome=ExperienceOutcome.NEGATIVE,
                lesson_learned=f"教训{i}",
            )
        report = executor.run_cycle("user1", scene="work", experience_replay=replay)
        assert report.cycle_id.startswith("cycle_")

    def test_run_cycle_saves_report(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.run_cycle("user1", scene="work")
        history = executor.get_cycle_history(5)
        assert len(history) == 1
        assert history[0]["phase"] == "adjust"

    def test_run_cycle_reflect_and_adjust(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.set_cycle_interval(7200)
        report = executor.run_cycle("user1", scene="health")
        # Health scene should increase interval
        assert report.next_cycle_in > 7200

    def test_run_cycle_work_scene(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.set_cycle_interval(7200)
        report = executor.run_cycle("user1", scene="work")
        # Work scene should decrease interval
        assert report.next_cycle_in < 7200

    def test_multiple_cycles(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        for i in range(3):
            executor.run_cycle("user1", scene="work")
        history = executor.get_cycle_history(5)
        assert len(history) == 3

    def test_cycle_report_to_dict(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor, CycleReport, LoopPhase
        executor = AutonomousExecutor()
        report = executor.run_cycle("user1", scene="work")
        d = report.to_dict()
        assert "cycle_id" in d
        assert "phase" in d
        assert "actions_executed" in d


class TestActionPersistence:
    """行动持久化测试"""

    def test_actions_persist_after_close(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            executor = AutonomousExecutor(db_path=db_path)
            executor.set_execution_level("autonomous")
            executor.run_cycle("user1", scene="work")
            executor.close()

            executor2 = AutonomousExecutor(db_path=db_path)
            actions = executor2.get_recent_actions(10)
            assert len(actions) > 0
        finally:
            os.unlink(db_path)

    def test_get_recent_actions(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.set_execution_level("autonomous")
        executor.run_cycle("user1", scene="work")
        executor.run_cycle("user1", scene="learning")
        actions = executor.get_recent_actions(5)
        assert len(actions) > 0


class TestActionStats:
    """行动统计测试"""

    def test_empty_stats(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        stats = executor.get_action_stats()
        assert stats["total_actions"] == 0
        assert stats["success_rate"] == 0.0

    def test_stats_after_cycle(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.run_cycle("user1", scene="work")
        stats = executor.get_action_stats()
        assert isinstance(stats["total_actions"], int)

    def test_stats_after_autonomous_cycle(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        executor.set_execution_level("autonomous")
        executor.run_cycle("user1", scene="work")
        stats = executor.get_action_stats()
        assert stats["total_actions"] > 0
        assert "success_rate" in stats

    def test_get_stats(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        executor = AutonomousExecutor()
        stats = executor.get_stats()
        assert "actions" in stats
        assert "execution_level" in stats
        assert "cycle_interval" in stats
        assert "recent_cycles" in stats


class TestAutonomousActionDataclass:
    """AutonomousAction数据类测试"""

    def test_to_dict(self):
        from nomad_mem.autonomy.autonomous_executor import AutonomousAction, ExecutionStatus
        action = AutonomousAction(
            action_id="a1", action_type="test", description="测试行动",
            goal_id="g1", status=ExecutionStatus.COMPLETED,
        )
        d = action.to_dict()
        assert d["action_id"] == "a1"
        assert d["status"] == "completed"


class TestReflectionEngine:
    """反思引擎测试"""

    def test_evaluate_performance_with_experience(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        from nomad_mem.autonomy.experience_replay import ExperienceReplay, ExperienceType, ExperienceOutcome
        engine = ReflectionEngine()
        replay = ExperienceReplay()
        # Record experiences
        for i in range(5):
            replay.record_experience(
                user_id="user1", intent="test", context="{}",
                action_taken="action", result="success" if i < 4 else "failed",
                exp_type=ExperienceType.SUCCESS if i < 4 else ExperienceType.FAILURE,
                outcome=ExperienceOutcome.POSITIVE if i < 4 else ExperienceOutcome.NEGATIVE,
                lesson_learned="lesson" if i < 4 else "",
            )
        evaluations = engine.evaluate_performance(experience_replay=replay)
        assert len(evaluations) >= 2  # response_quality + learning_rate
        dims = {e.dimension for e in evaluations}
        assert "response_quality" in dims
        assert "learning_rate" in dims

    def test_evaluate_performance_with_goal_manager(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        from nomad_mem.autonomy.goal_manager import GoalManager
        engine = ReflectionEngine()
        gm = GoalManager()
        gid = gm.create_goal("user1", "目标")
        evaluations = engine.evaluate_performance(goal_manager=gm)
        assert len(evaluations) >= 1
        assert any(e.dimension == "goal_progress" for e in evaluations)

    def test_evaluate_performance_with_autonomous_executor(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        engine = ReflectionEngine()
        executor = AutonomousExecutor()
        evaluations = engine.evaluate_performance(autonomous_executor=executor)
        assert len(evaluations) >= 1
        assert any(e.dimension == "action_effectiveness" for e in evaluations)

    def test_evaluate_performance_all_modules(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        from nomad_mem.autonomy.experience_replay import ExperienceReplay
        from nomad_mem.autonomy.goal_manager import GoalManager
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor
        engine = ReflectionEngine()
        replay = ExperienceReplay()
        gm = GoalManager()
        executor = AutonomousExecutor()
        evaluations = engine.evaluate_performance(
            experience_replay=replay,
            goal_manager=gm,
            autonomous_executor=executor,
        )
        assert len(evaluations) >= 4

    def test_reflect_on_failures(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        from nomad_mem.autonomy.experience_replay import ExperienceReplay, ExperienceType, ExperienceOutcome
        engine = ReflectionEngine()
        replay = ExperienceReplay()
        # Record failures
        for i in range(3):
            replay.record_experience(
                user_id="user1", intent=f"intent_{i}", context="{}",
                action_taken=f"action_{i}", result="failed",
                exp_type=ExperienceType.FAILURE, outcome=ExperienceOutcome.NEGATIVE,
                lesson_learned=f"教训{i}",
            )
        reflection = engine.reflect_on_failures(replay, "user1")
        assert reflection is not None
        assert len(reflection.findings) > 0
        assert len(reflection.root_cause) > 0

    def test_reflect_on_failures_no_failures(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        from nomad_mem.autonomy.experience_replay import ExperienceReplay
        engine = ReflectionEngine()
        replay = ExperienceReplay()
        reflection = engine.reflect_on_failures(replay, "user1")
        assert reflection is None

    def test_reflect_on_strategy(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Evaluation, EvaluationLevel
        engine = ReflectionEngine()
        evaluations = [
            Evaluation(
                evaluation_id="e1", dimension="test",
                score=0.2, level=EvaluationLevel.POOR.value,
                evidence="低分证据",
            ),
            Evaluation(
                evaluation_id="e2", dimension="test2",
                score=0.9, level=EvaluationLevel.EXCELLENT.value,
                evidence="高分证据",
            ),
        ]
        reflection = engine.reflect_on_strategy(evaluations)
        assert reflection is not None
        assert len(reflection.findings) == 1  # Only poor dimension

    def test_reflect_on_strategy_all_good(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Evaluation, EvaluationLevel
        engine = ReflectionEngine()
        evaluations = [
            Evaluation(
                evaluation_id="e1", dimension="test",
                score=0.9, level=EvaluationLevel.EXCELLENT.value,
            ),
        ]
        reflection = engine.reflect_on_strategy(evaluations)
        assert reflection is None

    def test_reflect_on_autonomous_actions(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        engine = ReflectionEngine()
        cycle_reports = [
            {"cycle_id": "c1", "actions_executed": 3, "actions_succeeded": 1, "actions_failed": 2},
            {"cycle_id": "c2", "actions_executed": 2, "actions_succeeded": 2, "actions_failed": 0},
        ]
        reflection = engine.reflect_on_autonomous_actions(cycle_reports)
        assert reflection is not None
        assert "失败" in reflection.summary

    def test_reflect_on_autonomous_actions_no_failures(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        engine = ReflectionEngine()
        cycle_reports = [
            {"cycle_id": "c1", "actions_executed": 3, "actions_succeeded": 3, "actions_failed": 0},
        ]
        reflection = engine.reflect_on_autonomous_actions(cycle_reports)
        assert reflection is None


class TestRecommendations:
    """建议测试"""

    def test_generate_from_reflection(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Reflection, ReflectionType
        engine = ReflectionEngine()
        reflection = Reflection(
            reflection_id="r1",
            reflection_type=ReflectionType.PERFORMANCE.value,
            summary="性能反思",
            findings=["问题1", "问题2"],
        )
        recs = engine.generate_recommendations(reflection=reflection)
        assert len(recs) >= 1
        assert any("改进" in r.title for r in recs)

    def test_generate_from_evaluations(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Evaluation, EvaluationLevel
        engine = ReflectionEngine()
        evaluations = [
            Evaluation(
                evaluation_id="e1", dimension="response_quality",
                score=0.3, level=EvaluationLevel.POOR.value,
                evidence="低分",
            ),
        ]
        recs = engine.generate_recommendations(evaluations=evaluations)
        assert len(recs) >= 1
        assert any("提升" in r.title for r in recs)

    def test_apply_recommendation(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Recommendation
        engine = ReflectionEngine()
        rec = Recommendation(
            recommendation_id="rec_1",
            title="测试建议",
            description="描述",
            priority="high",
        )
        engine.generate_recommendations(reflection=None, evaluations=None)
        # Direct save
        engine._save_recommendation(rec)
        result = engine.apply_recommendation("rec_1")
        assert result is True

    def test_reject_recommend(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Recommendation
        engine = ReflectionEngine()
        rec = Recommendation(
            recommendation_id="rec_2",
            title="拒绝建议",
            description="描述",
            priority="medium",
        )
        engine._save_recommendation(rec)
        result = engine.reject_recommendation("rec_2")
        assert result is True

    def test_get_pending_recommendations(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Recommendation
        engine = ReflectionEngine()
        rec = Recommendation(
            recommendation_id="rec_3",
            title="待处理建议",
            description="描述",
            priority="high",
        )
        engine._save_recommendation(rec)
        pending = engine.get_pending_recommendations()
        assert len(pending) >= 1

    def test_deduplicate_recommendations(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Reflection, ReflectionType, Recommendation
        engine = ReflectionEngine()
        reflection = Reflection(
            reflection_id="r2",
            reflection_type=ReflectionType.PERFORMANCE.value,
            summary="重复测试",
            findings=["相同问题", "相同问题"],
        )
        recs = engine.generate_recommendations(reflection=reflection)
        titles = [r.title for r in recs]
        assert len(titles) == len(set(titles))


class TestEvaluationHistory:
    """评估历史测试"""

    def test_get_evaluation_history(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Evaluation
        engine = ReflectionEngine()
        e = Evaluation(
            evaluation_id="eval_hist_1",
            dimension="test",
            score=0.7,
            level="good",
        )
        engine._save_evaluation(e)
        history = engine.get_evaluation_history(5)
        assert len(history) == 1

    def test_get_reflection_history(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Reflection, ReflectionType
        engine = ReflectionEngine()
        r = Reflection(
            reflection_id="ref_hist_1",
            reflection_type=ReflectionType.PERFORMANCE.value,
            summary="测试反思",
        )
        engine._save_reflection(r)
        history = engine.get_reflection_history(5)
        assert len(history) == 1

    def test_get_stats(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        engine = ReflectionEngine()
        stats = engine.get_stats()
        assert "total_evaluations" in stats
        assert "avg_evaluation_score" in stats
        assert "total_reflections" in stats
        assert "total_recommendations" in stats
        assert "pending_recommendations" in stats


class TestPersistence:
    """持久化测试"""

    def test_reflection_persist(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Reflection, ReflectionType
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            engine = ReflectionEngine(db_path=db_path)
            r = Reflection(
                reflection_id="r_persist",
                reflection_type=ReflectionType.STRATEGY.value,
                summary="持久化反思",
                findings=["发现1"],
            )
            engine._save_reflection(r)
            engine.close()

            engine2 = ReflectionEngine(db_path=db_path)
            history = engine2.get_reflection_history(5)
            assert len(history) == 1
            assert history[0]["summary"] == "持久化反思"
        finally:
            os.unlink(db_path)

    def test_recommendation_persist(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine, Recommendation
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            engine = ReflectionEngine(db_path=db_path)
            rec = Recommendation(
                recommendation_id="rec_persist",
                title="持久化建议",
                description="描述",
                priority="high",
            )
            engine._save_recommendation(rec)
            engine.close()

            engine2 = ReflectionEngine(db_path=db_path)
            pending = engine2.get_pending_recommendations()
            assert len(pending) >= 1
        finally:
            os.unlink(db_path)


class TestDataclassTests:
    """数据类测试"""

    def test_evaluation_to_dict(self):
        from nomad_mem.core.reflection_engine import Evaluation
        e = Evaluation(
            evaluation_id="e1", dimension="test",
            score=0.8, level="good", evidence="证据",
        )
        d = e.to_dict()
        assert d["dimension"] == "test"
        assert d["score"] == 0.8

    def test_reflection_to_dict(self):
        from nomad_mem.core.reflection_engine import Reflection, ReflectionType
        r = Reflection(
            reflection_id="r1",
            reflection_type=ReflectionType.PERFORMANCE.value,
            summary="测试",
            findings=["f1", "f2"],
        )
        d = r.to_dict()
        assert d["reflection_type"] == "performance"
        assert d["findings"] == ["f1", "f2"]

    def test_recommendation_to_dict(self):
        from nomad_mem.core.reflection_engine import Recommendation
        r = Recommendation(
            recommendation_id="rec1",
            title="标题",
            description="描述",
            priority="high",
            category="test",
        )
        d = r.to_dict()
        assert d["title"] == "标题"
        assert d["priority"] == "high"


class TestFullIntegration:
    """完整集成测试"""

    def test_full_reflection_cycle(self):
        from nomad_mem.core.reflection_engine import ReflectionEngine
        from nomad_mem.autonomy.experience_replay import ExperienceReplay, ExperienceType, ExperienceOutcome
        from nomad_mem.autonomy.goal_manager import GoalManager
        from nomad_mem.autonomy.autonomous_executor import AutonomousExecutor

        engine = ReflectionEngine()
        replay = ExperienceReplay()
        gm = GoalManager()
        executor = AutonomousExecutor()

        # Record mixed experiences
        for i in range(10):
            success = i < 7
            replay.record_experience(
                user_id="user1", intent=f"intent_{i}", context="{}",
                action_taken=f"action_{i}", result="success" if success else "failed",
                exp_type=ExperienceType.SUCCESS if success else ExperienceType.FAILURE,
                outcome=ExperienceOutcome.POSITIVE if success else ExperienceOutcome.NEGATIVE,
                lesson_learned=f"教训{i}" if success else "",
            )

        # Create goal
        gid = gm.create_goal("user1", "集成测试目标", priority="high")
        gm.add_subgoals(gid, ["A", "B", "C"])
        gm.complete_subgoal(gid, gm.get_subgoals(gid)[0].subgoal_id)

        # Run autonomous cycle
        executor.set_execution_level("autonomous")
        executor.run_cycle("user1", scene="work", goal_manager=gm, experience_replay=replay)

        # Evaluate
        evaluations = engine.evaluate_performance(
            experience_replay=replay,
            goal_manager=gm,
            autonomous_executor=executor,
        )
        assert len(evaluations) >= 4

        # Reflect
        reflection_failures = engine.reflect_on_failures(replay, "user1")
        assert reflection_failures is not None

        reflection_strategy = engine.reflect_on_strategy(evaluations)
        # May or may not exist depending on scores

        # Generate recommendations
        recs = engine.generate_recommendations(
            reflection=reflection_failures,
            evaluations=evaluations,
        )
        assert len(recs) >= 1

        # Check stats
        stats = engine.get_stats()
        assert stats["total_evaluations"] >= 4
        assert stats["total_reflections"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
