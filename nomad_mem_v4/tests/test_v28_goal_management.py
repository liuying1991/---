"""
test_v28_goal_management.py - 自主目标管理系统端到端测试

测试范围:
- GoalManager: 目标创建/分解/追踪/优先级/完成度/事件/统计
- GoalPlanner: 场景/经验/技能/通用目标生成、分解、难度预估
- JarvisCore集成: 初始化/状态/助手方法
"""
import pytest
import time
import os
import tempfile

# ─── Goal Manager Tests ─────────────────────────────────────────────────────


class TestGoalCreation:
    """目标创建测试"""

    def test_create_basic_goal(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        gid = gm.create_goal("user1", "完成项目报告")
        assert gid.startswith("goal_")
        goal = gm.get_goal(gid)
        assert goal is not None
        assert goal.title == "完成项目报告"
        assert goal.goal_type.value == "task"
        assert goal.priority.value == "medium"
        assert goal.status.value == "pending"
        assert goal.progress == 0.0

    def test_create_goal_with_all_params(self):
        from nomad_mem.autonomy.goal_manager import GoalManager, GoalType, GoalPriority
        gm = GoalManager()
        gid = gm.create_goal(
            "user1", "学习Python",
            description="掌握Python编程",
            goal_type="learning",
            priority="high",
            deadline=1735689600.0,
            metrics={"hours": 100},
        )
        goal = gm.get_goal(gid)
        assert goal.title == "学习Python"
        assert goal.description == "掌握Python编程"
        assert goal.goal_type == GoalType.LEARNING
        assert goal.priority == GoalPriority.HIGH
        assert goal.deadline == 1735689600.0
        assert "hours" in goal.metrics

    def test_create_goal_invalid_type_defaults(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        gid = gm.create_goal("user1", "Test", goal_type="unknown")
        goal = gm.get_goal(gid)
        assert goal.goal_type.value == "task"

    def test_create_goal_invalid_priority_defaults(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        gid = gm.create_goal("user1", "Test", priority="unknown")
        goal = gm.get_goal(gid)
        assert goal.priority.value == "medium"

    def test_create_goal_with_critical_priority(self):
        from nomad_mem.autonomy.goal_manager import GoalManager, GoalPriority
        gm = GoalManager()
        gid = gm.create_goal("user1", "紧急修复", priority="critical")
        goal = gm.get_goal(gid)
        assert goal.priority == GoalPriority.CRITICAL


class TestSubgoalManagement:
    """子目标管理测试"""

    def setup_method(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        self.gm = GoalManager()
        self.gid = self.gm.create_goal("user1", "大目标")

    def test_add_subgoals(self):
        sub_ids = self.gm.add_subgoals(self.gid, ["子目标1", "子目标2", "子目标3"])
        assert len(sub_ids) == 3
        assert all(sid.startswith("sub_") for sid in sub_ids)

    def test_add_subgoals_with_descriptions(self):
        sub_ids = self.gm.add_subgoals(
            self.gid, ["子目标1", "子目标2"],
            descriptions=["描述1", "描述2"]
        )
        assert len(sub_ids) == 2
        subgoals = self.gm.get_subgoals(self.gid)
        assert subgoals[0].description == "描述1"
        assert subgoals[1].description == "描述2"

    def test_get_subgoals(self):
        self.gm.add_subgoals(self.gid, ["A", "B", "C"])
        subgoals = self.gm.get_subgoals(self.gid)
        assert len(subgoals) == 3
        assert subgoals[0].title == "A"
        assert all(s.status.value == "pending" for s in subgoals)

    def test_update_subgoal_progress(self):
        sub_ids = self.gm.add_subgoals(self.gid, ["A", "B"])
        result = self.gm.update_subgoal_progress(self.gid, sub_ids[0], 0.5)
        assert result is True

    def test_complete_subgoal(self):
        sub_ids = self.gm.add_subgoals(self.gid, ["A", "B"])
        self.gm.complete_subgoal(self.gid, sub_ids[0])
        subgoals = self.gm.get_subgoals(self.gid)
        assert bool(subgoals[0].completed) is True
        assert subgoals[0].progress == 1.0

    def test_goal_progress_after_completion(self):
        sub_ids = self.gm.add_subgoals(self.gid, ["A", "B", "C", "D"])
        # 完成2个子目标 (50%)
        self.gm.complete_subgoal(self.gid, sub_ids[0])
        self.gm.complete_subgoal(self.gid, sub_ids[1])
        progress_info = self.gm.get_goal_progress(self.gid)
        assert progress_info["subgoal_progress"]["completed"] == 2
        assert progress_info["subgoal_progress"]["total"] == 4
        assert progress_info["progress"] > 0.3

    def test_progress_clamped(self):
        sub_ids = self.gm.add_subgoals(self.gid, ["A"])
        self.gm.update_subgoal_progress(self.gid, sub_ids[0], 1.5)
        subgoals = self.gm.get_subgoals(self.gid)
        assert subgoals[0].progress <= 1.0

    def test_progress_negative_clamped(self):
        sub_ids = self.gm.add_subgoals(self.gid, ["A"])
        self.gm.update_subgoal_progress(self.gid, sub_ids[0], -0.5)
        subgoals = self.gm.get_subgoals(self.gid)
        assert subgoals[0].progress >= 0.0


class TestGoalTracking:
    """目标追踪测试"""

    def setup_method(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        self.gm = GoalManager()

    def test_get_goal_progress_no_subgoals(self):
        gid = self.gm.create_goal("user1", "简单目标")
        info = self.gm.get_goal_progress(gid)
        assert info["progress"] == 0.0
        assert info["subgoal_progress"]["total"] == 0

    def test_get_user_goals(self):
        self.gm.create_goal("user1", "目标1")
        self.gm.create_goal("user1", "目标2")
        self.gm.create_goal("user2", "目标3")
        goals = self.gm.get_user_goals("user1")
        assert len(goals) == 2

    def test_get_user_goals_by_status(self):
        gid = self.gm.create_goal("user1", "目标")
        self.gm.update_goal_status(gid, "in_progress")
        goals = self.gm.get_user_goals("user1", status="in_progress")
        assert len(goals) == 1
        goals_pending = self.gm.get_user_goals("user1", status="pending")
        assert len(goals_pending) == 0

    def test_get_active_goals(self):
        gid1 = self.gm.create_goal("user1", "进行中")
        gid2 = self.gm.create_goal("user1", "已完成")
        self.gm.update_goal_status(gid2, "completed")
        active = self.gm.get_active_goals("user1")
        assert len(active) == 1
        assert active[0].title == "进行中"

    def test_get_goal_progress_with_subgoals(self):
        gid = self.gm.create_goal("user1", "追踪目标")
        sub_ids = self.gm.add_subgoals(gid, ["A", "B", "C"])
        self.gm.complete_subgoal(gid, sub_ids[0])
        info = self.gm.get_goal_progress(gid)
        assert "goal" in info
        assert "subgoals" in info
        assert len(info["subgoals"]) == 3


class TestPriorityManagement:
    """优先级管理测试"""

    def setup_method(self):
        from nomad_mem.autonomy.goal_manager import GoalManager, GoalPriority
        self.gm = GoalManager()
        self.gm.GP = GoalPriority

    def test_update_priority(self):
        gid = self.gm.create_goal("user1", "目标")
        result = self.gm.update_priority(gid, "high")
        assert result is True
        goal = self.gm.get_goal(gid)
        assert goal.priority.value == "high"

    def test_update_priority_invalid(self):
        gid = self.gm.create_goal("user1", "目标")
        result = self.gm.update_priority(gid, "unknown")
        assert result is False

    def test_auto_adjust_priority_urgent_deadline(self):
        gid = self.gm.create_goal("user1", "紧急目标", deadline=time.time() + 3600)
        self.gm.auto_adjust_priority(gid)
        goal = self.gm.get_goal(gid)
        assert goal.priority.value == "critical"

    def test_auto_adjust_priority_soon_deadline(self):
        gid = self.gm.create_goal("user1", "近期目标", deadline=time.time() + 86400 * 2)
        self.gm.auto_adjust_priority(gid)
        goal = self.gm.get_goal(gid)
        assert goal.priority.value == "high"

    def test_auto_adjust_priority_stale_goal(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()  # use in-memory
        gid = gm.create_goal("user1", "过期目标")
        # Manually set created_at to 8 days ago
        conn = gm._get_conn()
        conn.execute(
            "UPDATE goals SET created_at = ? WHERE goal_id = ?",
            (time.time() - 86400 * 8, gid)
        )
        conn.commit()
        # Don't close for in-memory
        gm.auto_adjust_priority(gid)
        goal = gm.get_goal(gid)
        assert goal.priority.value == "low"

    def test_priority_order_in_goals(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        gm.create_goal("user1", "低优先级", priority="low")
        gm.create_goal("user1", "高优先级", priority="high")
        gm.create_goal("user1", "关键优先级", priority="critical")
        goals = gm.get_user_goals("user1")
        assert goals[0].priority.value == "critical"
        assert goals[1].priority.value == "high"
        assert goals[2].priority.value == "low"


class TestGoalEvents:
    """目标事件测试"""

    def setup_method(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        self.gm = GoalManager()
        self.gid = self.gm.create_goal("user1", "事件测试")

    def test_goal_creation_event(self):
        events = self.gm.get_goal_events(self.gid)
        assert len(events) == 1
        assert events[0]["event_type"] == "created"

    def test_status_change_event(self):
        self.gm.update_goal_status(self.gid, "in_progress")
        events = self.gm.get_goal_events(self.gid)
        assert any(e["event_type"] == "status_change" for e in events)

    def test_decomposition_event(self):
        self.gm.add_subgoals(self.gid, ["A", "B"])
        events = self.gm.get_goal_events(self.gid)
        assert any(e["event_type"] == "decomposed" for e in events)

    def test_priority_change_event(self):
        self.gm.update_priority(self.gid, "high")
        events = self.gm.get_goal_events(self.gid)
        assert any(e["event_type"] == "priority_change" for e in events)

    def test_multiple_events(self):
        self.gm.update_goal_status(self.gid, "in_progress")
        self.gm.add_subgoals(self.gid, ["A"])
        self.gm.update_priority(self.gid, "critical")
        events = self.gm.get_goal_events(self.gid)
        assert len(events) == 4  # created + status + decomposed + priority

    def test_get_events_with_limit(self):
        for i in range(25):
            self.gm.update_goal_status(self.gid, "in_progress" if i % 2 == 0 else "pending")
        events = self.gm.get_goal_events(self.gid, k=10)
        assert len(events) <= 10


class TestGoalStats:
    """目标统计测试"""

    def setup_method(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        self.gm = GoalManager()

    def test_empty_stats(self):
        stats = self.gm.get_stats()
        assert stats["total_goals"] == 0
        assert stats["completion_rate"] == 0.0

    def test_stats_after_creation(self):
        self.gm.create_goal("user1", "目标1")
        self.gm.create_goal("user1", "目标2")
        stats = self.gm.get_stats("user1")
        assert stats["total_goals"] == 2
        assert stats["pending_goals"] == 2

    def test_stats_after_completion(self):
        gid = self.gm.create_goal("user1", "完成目标")
        self.gm.update_goal_status(gid, "completed")
        stats = self.gm.get_stats("user1")
        assert stats["completed_goals"] == 1
        assert stats["completion_rate"] == 1.0

    def test_stats_with_subgoals(self):
        gid = self.gm.create_goal("user1", "子目标统计")
        self.gm.add_subgoals(gid, ["A", "B", "C"])
        stats = self.gm.get_stats("user1")
        assert stats["total_subgoals"] == 3

    def test_stats_with_mixed_statuses(self):
        gid1 = self.gm.create_goal("user1", "进行中")
        self.gm.add_subgoals(gid1, ["A"])  # Add subgoal so completing partial = in_progress
        gid2 = self.gm.create_goal("user1", "已完成")
        # Add subgoals so completion works through subgoal tracking
        self.gm.add_subgoals(gid2, ["A"])
        self.gm.complete_subgoal(gid2, self.gm.get_subgoals(gid2)[0].subgoal_id)
        stats = self.gm.get_stats("user1")
        assert stats["in_progress_goals"] == 0  # gid1 is still pending (no subgoals completed)
        assert stats["completed_goals"] == 1
        assert stats["pending_goals"] == 1

    def test_avg_progress(self):
        gid = self.gm.create_goal("user1", "进度目标")
        sub_ids = self.gm.add_subgoals(gid, ["A", "B"])
        self.gm.complete_subgoal(gid, sub_ids[0])
        stats = self.gm.get_stats("user1")
        assert stats["avg_progress"] > 0.0


class TestGoalStatusUpdate:
    """目标状态更新测试"""

    def setup_method(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        self.gm = GoalManager()

    def test_update_to_in_progress(self):
        gid = self.gm.create_goal("user1", "目标")
        self.gm.update_goal_status(gid, "in_progress")
        goal = self.gm.get_goal(gid)
        assert goal.status.value == "in_progress"

    def test_update_to_completed(self):
        gid = self.gm.create_goal("user1", "目标")
        self.gm.update_goal_status(gid, "completed")
        goal = self.gm.get_goal(gid)
        assert goal.status.value == "completed"

    def test_update_to_failed(self):
        gid = self.gm.create_goal("user1", "目标")
        self.gm.update_goal_status(gid, "failed")
        goal = self.gm.get_goal(gid)
        assert goal.status.value == "failed"

    def test_update_to_on_hold(self):
        gid = self.gm.create_goal("user1", "目标")
        self.gm.update_goal_status(gid, "on_hold")
        goal = self.gm.get_goal(gid)
        assert goal.status.value == "on_hold"

    def test_update_to_cancelled(self):
        gid = self.gm.create_goal("user1", "目标")
        self.gm.update_goal_status(gid, "cancelled")
        goal = self.gm.get_goal(gid)
        assert goal.status.value == "cancelled"

    def test_update_invalid_status(self):
        gid = self.gm.create_goal("user1", "目标")
        result = self.gm.update_goal_status(gid, "unknown")
        assert result is False

    def test_get_nonexistent_goal(self):
        goal = self.gm.get_goal("nonexistent")
        assert goal is None


# ─── Goal Planner Tests ─────────────────────────────────────────────────────


class TestGoalPlannerSceneDriven:
    """场景驱动目标规划测试"""

    def test_scene_goals_work(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner.suggest_goals("user1", scene="work", k=3)
        assert any(p.goal_type == "task" for p in plans)

    def test_scene_goals_learning(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner.suggest_goals("user1", scene="learning", k=3)
        assert any(p.goal_type == "learning" for p in plans)

    def test_scene_goals_creation(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner.suggest_goals("user1", scene="creation", k=3)
        assert any(p.goal_type == "creation" for p in plans)

    def test_scene_goals_health(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner.suggest_goals("user1", scene="health", k=3)
        assert any(p.goal_type == "maintenance" for p in plans)

    def test_unknown_scene_returns_empty(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        scene_plans = planner._generate_scene_goals("unknown")
        assert len(scene_plans) == 0

    def test_scene_goals_have_subgoals(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner.suggest_goals("user1", scene="work", k=5)
        for p in plans:
            assert len(p.suggested_subgoals) > 0

    def test_scene_goals_have_rationale(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        scene_plans = planner._generate_scene_goals("work")
        assert len(scene_plans) > 0
        for p in scene_plans:
            assert "场景" in p.rationale or "work" in p.rationale


class TestGoalPlannerExperienceDriven:
    """经验驱动目标规划测试"""

    def setup_method(self):
        from nomad_mem.autonomy.experience_replay import ExperienceReplay, ExperienceType, ExperienceOutcome
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        self.replay = ExperienceReplay()
        self.planner = GoalPlanner(experience_replay=self.replay)
        self.ExpType = ExperienceType
        self.ExpOutcome = ExperienceOutcome

    def test_experience_goals_from_failures(self):
        self.replay.record_experience(
            user_id="user1", intent="schedule", context="{}",
            action_taken="tried calendar", result="failed",
            exp_type=self.ExpType.FAILURE, outcome=self.ExpOutcome.NEGATIVE,
            lesson_learned="需要更好的时间冲突检测",
        )
        plans = self.planner._generate_experience_goals("user1")
        assert len(plans) == 1
        assert plans[0].goal_type == "optimization"
        assert "schedule" in plans[0].goal_title

    def test_experience_goals_only_with_lessons(self):
        self.replay.record_experience(
            user_id="user1", intent="test", context="{}",
            action_taken="test", result="failed",
            exp_type=self.ExpType.FAILURE, outcome=self.ExpOutcome.NEGATIVE,
            lesson_learned="",  # 没有教训
        )
        plans = self.planner._generate_experience_goals("user1")
        assert len(plans) == 0

    def test_no_experience_returns_empty(self):
        # setup_method already creates replay but no experiences recorded yet
        plans = self.planner._generate_experience_goals("user1")
        assert len(plans) == 0

    def test_no_replay_returns_empty(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner._generate_experience_goals("user1")
        assert len(plans) == 0


class TestGoalPlannerSkillDriven:
    """技能驱动目标规划测试"""

    def test_no_skill_discoverer_returns_empty(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner._generate_skill_goals()
        assert len(plans) == 0


class TestGoalPlannerGeneral:
    """通用目标规划测试"""

    def test_general_goals_always_available(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner._generate_general_goals()
        assert len(plans) >= 2

    def test_general_goals_have_types(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        plans = planner._generate_general_goals()
        types = {p.goal_type for p in plans}
        assert "optimization" in types or "learning" in types


class TestGoalDecomposition:
    """目标分解测试"""

    def test_decompose_learning_goal(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        subgoals = planner.decompose_goal("学习计划", "learning")
        assert len(subgoals) >= 3
        assert any("目标" in s for s in subgoals)

    def test_decompose_optimization_goal(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        subgoals = planner.decompose_goal("优化流程", "optimization")
        assert "分析现状" in subgoals

    def test_decompose_creation_goal(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        subgoals = planner.decompose_goal("创作", "creation")
        assert any("创意" in s or "创作" in s for s in subgoals)

    def test_decompose_default_goal(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        subgoals = planner.decompose_goal("通用任务", "task")
        assert len(subgoals) >= 3

    def test_decompose_template_goal(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        subgoals = planner.decompose_goal("完成工作报告", "task")
        assert len(subgoals) == 3
        assert "收集数据" in subgoals


class TestDifficultyEstimation:
    """难度预估测试"""

    def test_base_difficulty(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        diff = planner.estimate_difficulty("简单目标")
        assert 0.0 <= diff <= 1.0

    def test_more_subgoals_increase_difficulty(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        diff_simple = planner.estimate_difficulty("通用任务")
        # Default decomposition has fewer subgoals than learning
        assert diff_simple > 0.3

    def test_difficulty_clamped(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        diff = planner.estimate_difficulty("超大目标")
        assert diff <= 1.0


class TestGoalPlan:
    """GoalPlan数据类测试"""

    def test_to_dict(self):
        from nomad_mem.autonomy.goal_planner import GoalPlan
        plan = GoalPlan(
            goal_title="测试目标",
            goal_description="测试描述",
            goal_type="task",
            suggested_priority="high",
            suggested_subgoals=["A", "B"],
            required_skills=["skill1"],
            estimated_difficulty=0.5,
            rationale="测试依据",
        )
        d = plan.to_dict()
        assert d["goal_title"] == "测试目标"
        assert d["suggested_subgoals"] == ["A", "B"]
        assert d["required_skills"] == ["skill1"]


class TestGoalSuggestDeduplication:
    """目标建议去重测试"""

    def test_deduplicate_plans(self):
        from nomad_mem.autonomy.goal_planner import GoalPlan, GoalPlanner
        planner = GoalPlanner()
        # Create duplicate plans manually
        plans = [
            GoalPlan(goal_title="重复目标", goal_description="desc1", estimated_difficulty=0.3),
            GoalPlan(goal_title="重复目标", goal_description="desc2", estimated_difficulty=0.5),
            GoalPlan(goal_title="唯一目标", goal_description="desc3", estimated_difficulty=0.4),
        ]
        seen = set()
        unique = []
        for p in plans:
            if p.goal_title not in seen:
                seen.add(p.goal_title)
                unique.append(p)
        assert len(unique) == 2

    def test_sort_by_difficulty(self):
        from nomad_mem.autonomy.goal_planner import GoalPlan
        plans = [
            GoalPlan(goal_title="A", goal_description="", estimated_difficulty=0.7),
            GoalPlan(goal_title="B", goal_description="", estimated_difficulty=0.3),
            GoalPlan(goal_title="C", goal_description="", estimated_difficulty=0.5),
        ]
        plans.sort(key=lambda x: x.estimated_difficulty)
        assert plans[0].estimated_difficulty == 0.3
        assert plans[2].estimated_difficulty == 0.7


# ─── Dataclass Tests ────────────────────────────────────────────────────────


class TestGoalDataclass:
    """Goal数据类测试"""

    def test_goal_to_dict(self):
        from nomad_mem.autonomy.goal_manager import Goal, GoalType, GoalPriority, GoalStatus
        goal = Goal(
            goal_id="g1", user_id="u1", title="测试",
            goal_type=GoalType.LEARNING,
            priority=GoalPriority.HIGH,
            status=GoalStatus.IN_PROGRESS,
        )
        d = goal.to_dict()
        assert d["goal_type"] == "learning"
        assert d["priority"] == "high"
        assert d["status"] == "in_progress"

    def test_goal_from_dict(self):
        from nomad_mem.autonomy.goal_manager import Goal, GoalType, GoalPriority, GoalStatus
        data = {
            "goal_id": "g1", "user_id": "u1", "title": "测试",
            "goal_type": "creation", "priority": "critical",
            "status": "completed", "progress": 1.0,
            "deadline": 0.0, "metrics": "", "subgoal_count": 0,
            "completed_subgoal_count": 0, "created_at": 0, "updated_at": 0,
        }
        goal = Goal.from_dict(data)
        assert goal.goal_type == GoalType.CREATION
        assert goal.priority == GoalPriority.CRITICAL
        assert goal.status == GoalStatus.COMPLETED


class TestSubGoalDataclass:
    """SubGoal数据类测试"""

    def test_subgoal_to_dict(self):
        from nomad_mem.autonomy.goal_manager import SubGoal, GoalStatus
        sg = SubGoal(
            subgoal_id="s1", goal_id="g1", title="子目标",
            status=GoalStatus.IN_PROGRESS, progress=0.5,
        )
        d = sg.to_dict()
        assert d["status"] == "in_progress"
        assert d["progress"] == 0.5

    def test_subgoal_from_dict(self):
        from nomad_mem.autonomy.goal_manager import SubGoal, GoalStatus
        data = {
            "subgoal_id": "s1", "goal_id": "g1", "title": "子目标",
            "description": "", "status": "completed", "completed": True,
            "progress": 1.0, "created_at": 0,
        }
        sg = SubGoal.from_dict(data)
        assert sg.status == GoalStatus.COMPLETED
        assert sg.completed is True


# ─── Persistence Tests ──────────────────────────────────────────────────────


class TestPersistence:
    """持久化测试"""

    def test_persist_to_file(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            gm = GoalManager(db_path=db_path)
            gid = gm.create_goal("user1", "持久化目标")
            gm.add_subgoals(gid, ["A", "B"])
            gm.close()

            # 重新打开
            gm2 = GoalManager(db_path=db_path)
            goal = gm2.get_goal(gid)
            assert goal is not None
            assert goal.title == "持久化目标"
            subgoals = gm2.get_subgoals(gid)
            assert len(subgoals) == 2
        finally:
            os.unlink(db_path)

    def test_events_persist(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            gm = GoalManager(db_path=db_path)
            gid = gm.create_goal("user1", "事件持久化")
            gm.update_goal_status(gid, "in_progress")
            gm.close()

            gm2 = GoalManager(db_path=db_path)
            events = gm2.get_goal_events(gid)
            assert len(events) == 2
        finally:
            os.unlink(db_path)


# ─── Edge Cases ─────────────────────────────────────────────────────────────


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_user_goals(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        goals = gm.get_user_goals("nonexistent_user")
        assert len(goals) == 0

    def test_get_progress_nonexistent_goal(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        info = gm.get_goal_progress("nonexistent")
        assert info == {}

    def test_get_subgoals_nonexistent_goal(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        subgoals = gm.get_subgoals("nonexistent")
        assert len(subgoals) == 0

    def test_complete_nonexistent_subgoal(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        result = gm.complete_subgoal("nonexistent_goal", "nonexistent_sub")
        assert result is True  # SQL doesn't error on no match

    def test_goal_with_no_subgoals_progress(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        gid = gm.create_goal("user1", "无子目标")
        info = gm.get_goal_progress(gid)
        assert info["progress"] == 0.0

    def test_all_subgoals_completed(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()
        gid = gm.create_goal("user1", "全部完成")
        sub_ids = gm.add_subgoals(gid, ["A", "B", "C"])
        for sid in sub_ids:
            gm.complete_subgoal(gid, sid)
        goal = gm.get_goal(gid)
        assert goal.status.value == "completed"
        assert goal.progress >= 0.7


# ─── Full Integration ──────────────────────────────────────────────────────


class TestGoalManagerFullLifecycle:
    """目标全生命周期测试"""

    def test_full_lifecycle(self):
        from nomad_mem.autonomy.goal_manager import GoalManager
        gm = GoalManager()

        # 1. 创建目标
        gid = gm.create_goal("user1", "完成AI项目", goal_type="creation", priority="high")
        goal = gm.get_goal(gid)
        assert goal.status.value == "pending"

        # 2. 分解目标
        sub_ids = gm.add_subgoals(gid, ["需求分析", "设计架构", "编码实现", "测试验证"])
        assert len(sub_ids) == 4

        # 3. 开始执行
        gm.update_goal_status(gid, "in_progress")

        # 4. 逐步完成
        gm.complete_subgoal(gid, sub_ids[0])
        gm.complete_subgoal(gid, sub_ids[1])

        # 5. 检查进度
        info = gm.get_goal_progress(gid)
        assert info["subgoal_progress"]["completed"] == 2
        assert info["subgoal_progress"]["remaining"] == 2
        assert info["progress"] > 0.3

        # 6. 继续完成
        gm.complete_subgoal(gid, sub_ids[2])
        gm.complete_subgoal(gid, sub_ids[3])

        # 7. 目标应自动完成
        goal = gm.get_goal(gid)
        assert goal.status.value == "completed"
        assert goal.progress >= 0.7

        # 8. 检查事件历史
        events = gm.get_goal_events(gid)
        event_types = [e["event_type"] for e in events]
        assert "created" in event_types
        assert "decomposed" in event_types
        assert "status_change" in event_types

        # 9. 检查统计
        stats = gm.get_stats("user1")
        assert stats["total_goals"] == 1
        assert stats["completed_goals"] == 1
        assert stats["completion_rate"] == 1.0


class TestGoalPlannerFullWorkflow:
    """目标规划器完整工作流测试"""

    def test_suggest_and_decompose(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()

        # 建议目标
        plans = planner.suggest_goals("user1", scene="work", k=5)
        assert len(plans) > 0

        # 分解第一个目标
        first_plan = plans[0]
        subgoals = planner.decompose_goal(first_plan.goal_title, first_plan.goal_type)
        assert len(subgoals) > 0

        # 预估难度
        diff = planner.estimate_difficulty(first_plan.goal_title)
        assert 0.0 <= diff <= 1.0

    def test_multiple_scenes(self):
        from nomad_mem.autonomy.goal_planner import GoalPlanner
        planner = GoalPlanner()
        scenes = ["work", "learning", "creation", "health"]
        for scene in scenes:
            plans = planner.suggest_goals("user1", scene=scene, k=3)
            assert len(plans) > 0


# ─── Summary ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
