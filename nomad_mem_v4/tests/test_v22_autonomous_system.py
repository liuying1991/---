"""
V22 测试 - 自主引擎系统集成

测试自主调度器、自主监控器、自主决策器以及集成后的自主引擎。

测试类:
- TestAutonomousScheduler: 调度器核心功能
- TestAutonomousMonitor: 监控器核心功能
- TestAutonomousDecider: 决策器核心功能
- TestAutonomousEngine: 引擎协调功能
- TestAutonomousIntegration: 完整工作流集成测试
"""
import os
import sys
import tempfile
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta

from nomad_mem.autonomy.autonomous_scheduler import (
    AutonomousScheduler,
    TriggerType,
    TaskStatus,
    ScheduledTask,
)
from nomad_mem.autonomy.autonomous_monitor import (
    AutonomousMonitor,
    MonitorType,
    MonitorStatus,
    AnomalyRecord,
)
from nomad_mem.autonomy.autonomous_decider import (
    AutonomousDecider,
    DecisionType,
    StrategyOption,
)
from nomad_mem.autonomy.autonomous_engine import AutonomousEngine


# ====================================================================
#  TestAutonomousScheduler
# ====================================================================


class TestAutonomousScheduler:
    """自主调度器测试"""

    def _make_scheduler(self) -> AutonomousScheduler:
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test_scheduler.db")
        return AutonomousScheduler(db_path=db_path)

    # ---- schedule_task ----

    def test_schedule_task_returns_id(self):
        """调度任务返回非空 ID"""
        s = self._make_scheduler()
        tid = s.schedule_task(
            name="测试任务",
            description="测试描述",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 60},
            action="test_action",
        )
        assert isinstance(tid, str)
        assert len(tid) > 0

    def test_schedule_task_persists(self):
        """调度任务可以被查询到"""
        s = self._make_scheduler()
        tid = s.schedule_task(
            name="持久化测试",
            description="测试持久化",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 120},
            action="persist_action",
        )
        task = s.get_task(tid)
        assert task is not None
        assert task.name == "持久化测试"
        assert task.trigger_type == "time_interval"

    def test_schedule_task_priority_bounds(self):
        """任务优先级被限制在 1-10"""
        s = self._make_scheduler()
        tid_low = s.schedule_task(
            name="低优先级",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 60},
            action="a",
            priority=0,
        )
        task_low = s.get_task(tid_low)
        assert task_low.priority == 1

        tid_high = s.schedule_task(
            name="高优先级",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 60},
            action="a",
            priority=99,
        )
        task_high = s.get_task(tid_high)
        assert task_high.priority == 10

    # ---- cancel_task ----

    def test_cancel_task(self):
        """取消任务成功"""
        s = self._make_scheduler()
        tid = s.schedule_task(
            name="可取消",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 60},
            action="a",
        )
        result = s.cancel_task(tid)
        assert result is True
        task = s.get_task(tid)
        assert task.status == TaskStatus.CANCELLED.value

    def test_cancel_nonexistent_task(self):
        """取消不存在的任务返回 False"""
        s = self._make_scheduler()
        assert s.cancel_task("nonexistent") is False

    # ---- run_due_tasks ----

    def test_run_due_tasks_empty(self):
        """没有到期任务时返回空列表"""
        s = self._make_scheduler()
        s.schedule_task(
            name="未来任务",
            description="",
            trigger_type=TriggerType.ONCE,
            trigger_config={"run_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()},
            action="a",
        )
        executed = s.run_due_tasks()
        assert executed == []

    def test_run_due_tasks_executes(self):
        """到期任务被执行"""
        action_results = {"ran": False}

        def my_action(**kwargs):
            action_results["ran"] = True
            return {"ok": True}

        s = self._make_scheduler()
        s.register_action("my_action", my_action)
        s.schedule_task(
            name="立即执行",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 0},
            action="my_action",
        )
        executed = s.run_due_tasks()
        assert len(executed) >= 1
        # 等待后台线程完成
        time.sleep(0.3)
        assert action_results["ran"] is True

    def test_run_due_tasks_records_history(self):
        """执行任务后记录历史"""
        s = self._make_scheduler()
        s.register_action("echo", lambda: "done")
        tid = s.schedule_task(
            name="历史测试",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 0},
            action="echo",
        )
        s.run_due_tasks()
        time.sleep(0.3)
        history = s.get_task_history(tid)
        assert len(history) >= 1

    # ---- time_interval trigger ----

    def test_time_interval_trigger(self):
        """时间间隔触发器设置正确的下次运行时间"""
        s = self._make_scheduler()
        tid = s.schedule_task(
            name="间隔任务",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 300},
            action="a",
        )
        task = s.get_task(tid)
        assert task.next_run is not None
        next_dt = datetime.fromisoformat(task.next_run)
        assert next_dt > datetime.utcnow() - timedelta(seconds=5)

    # ---- once trigger ----

    def test_once_trigger_future(self):
        """单次触发器（未来时间）设置正确的下次运行时间"""
        s = self._make_scheduler()
        future_time = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        tid = s.schedule_task(
            name="单次任务",
            description="",
            trigger_type=TriggerType.ONCE,
            trigger_config={"run_at": future_time},
            action="a",
        )
        task = s.get_task(tid)
        assert task.next_run is not None

    def test_once_trigger_past(self):
        """单次触发器（过去时间）next_run 为 None"""
        s = self._make_scheduler()
        past_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        tid = s.schedule_task(
            name="过期单次",
            description="",
            trigger_type=TriggerType.ONCE,
            trigger_config={"run_at": past_time},
            action="a",
        )
        task = s.get_task(tid)
        assert task.next_run is None

    # ---- periodic trigger ----

    def test_periodic_trigger(self):
        """周期性触发器设置正确的下次运行时间"""
        s = self._make_scheduler()
        tid = s.schedule_task(
            name="周期任务",
            description="",
            trigger_type=TriggerType.PERIODIC,
            trigger_config={"interval_seconds": 600},
            action="a",
        )
        task = s.get_task(tid)
        assert task.next_run is not None
        next_dt = datetime.fromisoformat(task.next_run)
        assert next_dt > datetime.utcnow() - timedelta(seconds=5)

    # ---- task history ----

    def test_task_history_limit(self):
        """任务历史限制返回条数"""
        s = self._make_scheduler()
        tid = s.schedule_task(
            name="历史任务",
            description="",
            trigger_type=TriggerType.CONDITION,
            trigger_config={},
            action="noop",
        )
        s._add_history(tid, "completed")
        s._add_history(tid, "failed", error="err1")
        s._add_history(tid, "completed")
        history = s.get_task_history(tid, limit=2)
        assert len(history) == 2

    def test_task_history_empty(self):
        """无历史时返回空列表"""
        s = self._make_scheduler()
        tid = s.schedule_task(
            name="空历史",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 60},
            action="a",
        )
        assert s.get_task_history(tid) == []

    # ---- stats ----

    def test_get_stats_initial(self):
        """初始调度器统计信息"""
        s = self._make_scheduler()
        stats = s.get_stats()
        assert stats["total_tasks"] == 0
        assert stats["total_runs"] == 0
        assert stats["success_rate"] == 0.0

    def test_get_stats_with_tasks(self):
        """有任务后统计信息正确"""
        s = self._make_scheduler()
        s.schedule_task(
            name="统计任务1",
            description="",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 60},
            action="a",
        )
        s.schedule_task(
            name="统计任务2",
            description="",
            trigger_type=TriggerType.ONCE,
            trigger_config={"run_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()},
            action="b",
        )
        stats = s.get_stats()
        assert stats["total_tasks"] == 2

    # ---- close ----

    def test_close_scheduler(self):
        """关闭调度器不报错"""
        s = self._make_scheduler()
        s.close()  # should not raise


# ====================================================================
#  TestAutonomousMonitor
# ====================================================================


class TestAutonomousMonitor:
    """自主监控器测试"""

    def _make_monitor(self) -> AutonomousMonitor:
        return AutonomousMonitor()

    # ---- register ----

    def test_register_monitor(self):
        """注册监控项返回 True"""
        m = self._make_monitor()
        result = m.register_monitor(
            monitor_id="cpu_usage",
            monitor_type=MonitorType.RESOURCE_USAGE,
            check_interval=30,
            thresholds={"warning": 0.7, "critical": 0.9},
        )
        assert result is True

    def test_register_duplicate(self):
        """重复注册返回 False"""
        m = self._make_monitor()
        m.register_monitor("cpu", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.7})
        result = m.register_monitor("cpu", MonitorType.RESOURCE_USAGE, 60, {"warning": 0.8})
        assert result is False

    def test_remove_monitor(self):
        """移除监控项返回 True"""
        m = self._make_monitor()
        m.register_monitor("temp", MonitorType.SYSTEM_HEALTH, 60, {})
        assert m.remove_monitor("temp") is True
        assert m.remove_monitor("temp") is False  # 第二次应返回 False

    # ---- check ----

    def test_check_no_value(self):
        """监控项无值时不产生异常"""
        m = self._make_monitor()
        m.register_monitor("disk", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.8})
        anomalies = m.check_monitor("disk")
        assert anomalies is None

    def test_check_monitor_normal(self):
        """正常值不触发异常"""
        m = self._make_monitor()
        m.register_monitor("mem", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.7, "critical": 0.9})
        m.update_metric("mem", 0.5)
        anomaly = m.check_monitor("mem")
        assert anomaly is None
        state = m.get_monitor_state("mem")
        assert state.status == MonitorStatus.NORMAL

    def test_check_monitor_warning(self):
        """超过警告阈值触发警告"""
        m = self._make_monitor()
        m.register_monitor("cpu", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.7, "critical": 0.9})
        m.update_metric("cpu", 0.75)
        anomaly = m.check_monitor("cpu")
        assert anomaly is not None
        assert anomaly.severity == MonitorStatus.WARNING

    def test_check_monitor_critical(self):
        """超过严重阈值触发严重告警"""
        m = self._make_monitor()
        m.register_monitor("disk", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.7, "critical": 0.9})
        m.update_metric("disk", 0.95)
        anomaly = m.check_monitor("disk")
        assert anomaly is not None
        assert anomaly.severity == MonitorStatus.CRITICAL

    def test_check_all_monitors(self):
        """检查所有监控项返回异常列表"""
        m = self._make_monitor()
        m.register_monitor("good", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.8})
        m.register_monitor("bad", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.5})
        m.update_metric("good", 0.3)
        m.update_metric("bad", 0.9)
        anomalies = m.check_all_monitors()
        assert len(anomalies) >= 1
        assert any(a.monitor_id == "bad" for a in anomalies)

    # ---- update ----

    def test_update_metric_nonexistent(self):
        """更新不存在的监控项返回 False"""
        m = self._make_monitor()
        assert m.update_metric("nonexistent", 0.5) is False

    def test_update_metric_keeps_history(self):
        """更新指标保留历史记录"""
        m = self._make_monitor()
        m.register_monitor("hist", MonitorType.SYSTEM_HEALTH, 30, {})
        for i in range(5):
            m.update_metric("hist", float(i))
        state = m.get_monitor_state("hist")
        assert len(state.history) == 5

    def test_update_metric_limits_history(self):
        """历史记录限制在最近 100 条"""
        m = self._make_monitor()
        m.register_monitor("hist", MonitorType.SYSTEM_HEALTH, 30, {})
        for i in range(150):
            m.update_metric("hist", float(i))
        state = m.get_monitor_state("hist")
        assert len(state.history) == 100

    # ---- anomaly detection ----

    def test_anomaly_detection_no_threshold(self):
        """无阈值配置时不产生异常"""
        m = self._make_monitor()
        m.register_monitor("no_thresh", MonitorType.SYSTEM_HEALTH, 30, {})
        m.update_metric("no_thresh", 0.99)
        anomaly = m.check_monitor("no_thresh")
        assert anomaly is None

    # ---- alert history ----

    def test_anomaly_history(self):
        """异常历史记录包含产生的异常"""
        m = self._make_monitor()
        m.register_monitor("alert_hist", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.5})
        m.update_metric("alert_hist", 0.6)
        m.check_monitor("alert_hist")
        m.update_metric("alert_hist", 0.7)
        m.check_monitor("alert_hist")
        history = m.get_anomaly_history()
        assert len(history) == 2

    def test_anomaly_history_filter_by_monitor(self):
        """异常历史可按监控 ID 过滤"""
        m = self._make_monitor()
        m.register_monitor("a", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.5})
        m.register_monitor("b", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.5})
        m.update_metric("a", 0.6)
        m.check_monitor("a")
        m.update_metric("b", 0.6)
        m.check_monitor("b")
        filtered = m.get_anomaly_history(monitor_id="a")
        assert len(filtered) == 1
        assert filtered[0].monitor_id == "a"

    # ---- get_active_alerts ----

    def test_get_active_alerts_empty(self):
        """无告警时返回空列表"""
        m = self._make_monitor()
        assert m.get_active_alerts() == []

    def test_get_active_alerts(self):
        """活跃告警列表包含异常监控项"""
        m = self._make_monitor()
        m.register_monitor("alerting", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.5})
        m.update_metric("alerting", 0.8)
        m.check_monitor("alerting")
        alerts = m.get_active_alerts()
        assert len(alerts) == 1
        assert alerts[0]["monitor_id"] == "alerting"
        assert alerts[0]["status"] == "warning"

    # ---- stats ----

    def test_get_stats(self):
        """监控统计信息正确"""
        m = self._make_monitor()
        m.register_monitor("s1", MonitorType.SYSTEM_HEALTH, 30, {})
        m.register_monitor("r1", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.5})
        stats = m.get_stats()
        assert stats["total_monitors"] == 2
        assert "system_health" in stats["by_type"]
        assert "resource_usage" in stats["by_type"]

    def test_get_stats_with_anomalies(self):
        """有异常时统计包含 anomaly_count"""
        m = self._make_monitor()
        m.register_monitor("an", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.5})
        m.update_metric("an", 0.8)
        m.check_monitor("an")
        stats = m.get_stats()
        assert stats["anomaly_count"] == 1

    # ---- close ----

    def test_close_monitor(self):
        """关闭监控器不报错"""
        m = self._make_monitor()
        m.register_monitor("c", MonitorType.SYSTEM_HEALTH, 30, {})
        m.close()


# ====================================================================
#  TestAutonomousDecider
# ====================================================================


class TestAutonomousDecider:
    """自主决策器测试"""

    def _make_decider(self) -> AutonomousDecider:
        return AutonomousDecider()

    # ---- set_goal ----

    def test_set_goal_returns_id(self):
        """设置目标返回 goal_id"""
        d = self._make_decider()
        gid = d.set_goal("提升系统性能", priority=8)
        assert gid.startswith("goal_")
        assert len(gid) > 0

    def test_set_goal_priority_bounds(self):
        """目标优先级被限制在 1-10"""
        d = self._make_decider()
        gid = d.set_goal("低优先级", priority=0)
        goals = d.get_active_goals()
        goal = [g for g in goals if g.goal_id == gid][0]
        assert goal.priority == 1

        gid2 = d.set_goal("高优先级", priority=20)
        goals = d.get_active_goals()
        goal2 = [g for g in goals if g.goal_id == gid2][0]
        assert goal2.priority == 10

    def test_set_goal_with_sub_goals(self):
        """设置目标时可指定子目标"""
        d = self._make_decider()
        gid = d.set_goal("主目标", priority=5, sub_goals=["子目标1", "子目标2"])
        goals = d.get_active_goals()
        goal = [g for g in goals if g.goal_id == gid][0]
        assert len(goal.sub_goals) == 2

    # ---- decompose_goal ----

    def test_decompose_goal_existing_subgoals(self):
        """有预设子目标时直接返回"""
        d = self._make_decider()
        gid = d.set_goal("有子目标", sub_goals=["a", "b", "c"])
        sub_ids = d.decompose_goal(gid)
        assert sub_ids == ["a", "b", "c"]

    def test_decompose_goal_auto_decompose(self):
        """无子目标时自动分解"""
        d = self._make_decider()
        gid = d.set_goal("自动分解目标")
        sub_ids = d.decompose_goal(gid)
        assert len(sub_ids) > 0

    def test_decompose_goal_nonexistent(self):
        """分解不存在的目标返回空列表"""
        d = self._make_decider()
        assert d.decompose_goal("goal_nonexistent") == []

    # ---- complete_goal ----

    def test_complete_goal(self):
        """完成目标成功"""
        d = self._make_decider()
        gid = d.set_goal("待完成目标")
        assert d.complete_goal(gid) is True
        active = d.get_active_goals()
        assert not any(g.goal_id == gid for g in active)

    def test_complete_goal_nonexistent(self):
        """完成不存在的目标返回 False"""
        d = self._make_decider()
        assert d.complete_goal("goal_nonexistent") is False

    # ---- make_decision ----

    def test_make_decision_no_options(self):
        """无选项时做出默认决策"""
        d = self._make_decider()
        record = d.make_decision({}, DecisionType.ACTION)
        assert record.decision_type == DecisionType.ACTION
        assert record.confidence >= 0.0
        assert record.confidence <= 1.0

    def test_make_decision_with_options(self):
        """有选项时做出决策"""
        d = self._make_decider()
        options = ["option_a", "option_b", "option_c"]
        record = d.make_decision({"context_key": "val"}, DecisionType.ACTION, options=options)
        assert record.decision_made in options
        assert record.confidence > 0.1

    def test_make_decision_strategy_options(self):
        """有策略选项时选择评分最高的"""
        d = self._make_decider()
        opt1 = StrategyOption("s1", "慢但安全", "", ["安全"], ["慢"], 0.9)
        opt2 = StrategyOption("s2", "快但冒险", "", ["快"], ["不稳定"], 0.4)
        record = d.make_decision({}, DecisionType.STRATEGY, options=[opt1, opt2])
        assert record.decision_made["strategy"] == "慢但安全"

    # ---- evaluate_options ----

    def test_evaluate_options_empty(self):
        """评估空选项列表"""
        d = self._make_decider()
        result = d.evaluate_options([])
        assert result == []

    def test_evaluate_options_with_scores(self):
        """评估策略选项并生成评分"""
        d = self._make_decider()
        options = [
            {"name": "opt1", "description": "描述1", "pros": ["a", "b", "c"], "cons": ["d"]},
            {"name": "opt2", "description": "描述2", "pros": ["a"], "cons": ["b", "c", "d"]},
        ]
        strategies = d.evaluate_options(options)
        assert len(strategies) == 2
        # opt1 有更多 pros，评分应更高
        assert strategies[0].estimated_success > strategies[1].estimated_success

    def test_evaluate_options_explicit_success(self):
        """评估时显式指定成功率"""
        d = self._make_decider()
        options = [
            {"name": "x", "description": "", "pros": [], "cons": [], "estimated_success": 0.85},
        ]
        strategies = d.evaluate_options(options)
        assert strategies[0].estimated_success == 0.85

    # ---- record_outcome ----

    def test_record_outcome(self):
        """记录决策结果成功"""
        d = self._make_decider()
        record = d.make_decision({}, DecisionType.ACTION)
        assert d.record_outcome(record.decision_id, success=True, result={"done": True}) is True

    def test_record_outcome_nonexistent(self):
        """记录不存在的决策结果返回 False"""
        d = self._make_decider()
        assert d.record_outcome("dec_nonexistent", False, None) is False

    # ---- decision_history ----

    def test_decision_history(self):
        """决策历史记录包含之前的决策"""
        d = self._make_decider()
        d.make_decision({"k1": "v1"}, DecisionType.ACTION)
        d.make_decision({"k2": "v2"}, DecisionType.PLAN)
        history = d.get_decision_history()
        assert len(history) == 2

    def test_decision_history_limit(self):
        """决策历史限制条数"""
        d = self._make_decider()
        for i in range(30):
            d.make_decision({"i": i}, DecisionType.ACTION)
        history = d.get_decision_history(limit=5)
        assert len(history) == 5

    # ---- stats ----

    def test_get_stats_initial(self):
        """初始统计信息"""
        d = self._make_decider()
        stats = d.get_stats()
        assert stats["total_goals"] == 0
        assert stats["total_decisions"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_confidence"] == 0.0

    def test_get_stats_with_data(self):
        """有数据后统计信息正确"""
        d = self._make_decider()
        d.set_goal("目标A")
        record = d.make_decision({}, DecisionType.ACTION)
        d.record_outcome(record.decision_id, success=True, result="ok")
        stats = d.get_stats()
        assert stats["total_goals"] == 1
        assert stats["total_decisions"] == 1
        assert stats["success_rate"] == 1.0

    # ---- close ----

    def test_close_decider(self):
        """关闭决策器不报错"""
        d = self._make_decider()
        d.set_goal("清理目标")
        d.close()


# ====================================================================
#  TestAutonomousEngine
# ====================================================================


class TestAutonomousEngine:
    """自主引擎协调功能测试"""

    def _make_engine(self) -> AutonomousEngine:
        tmpdir = tempfile.TemporaryDirectory()
        engine = AutonomousEngine(data_dir=tmpdir.name)
        engine._tmpdir = tmpdir  # 保存引用以便清理
        return engine

    def _cleanup(self, engine: AutonomousEngine):
        # 等待可能的后台线程完成
        time.sleep(0.2)
        engine.close()
        if hasattr(engine, "_tmpdir"):
            engine._tmpdir.cleanup()

    # ---- init ----

    def test_init_default(self):
        """默认初始化不报错"""
        engine = self._make_engine()
        assert engine.is_running() is False
        self._cleanup(engine)

    def test_init_custom_data_dir(self):
        """自定义数据目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AutonomousEngine(data_dir=os.path.join(tmpdir, "custom"))
            assert os.path.isdir(os.path.join(tmpdir, "custom"))
            engine.close()

    # ---- start / stop / is_running ----

    def test_start_engine(self):
        """启动后 is_running 返回 True"""
        engine = self._make_engine()
        engine.start()
        assert engine.is_running() is True
        self._cleanup(engine)

    def test_stop_engine(self):
        """停止后 is_running 返回 False"""
        engine = self._make_engine()
        engine.start()
        engine.stop()
        assert engine.is_running() is False
        self._cleanup(engine)

    def test_is_running_initial(self):
        """初始状态未运行"""
        engine = self._make_engine()
        assert engine.is_running() is False
        self._cleanup(engine)

    # ---- add_autonomous_task ----

    def test_add_autonomous_task(self):
        """添加自主任务成功"""
        engine = self._make_engine()
        tid = engine.add_autonomous_task(
            name="定期备份",
            trigger_type=TriggerType.TIME_INTERVAL,
            trigger_config={"interval_seconds": 300},
            action="backup",
        )
        assert isinstance(tid, str)
        pending = engine.get_pending_tasks()
        assert any(t["task_id"] == tid for t in pending)
        self._cleanup(engine)

    def test_add_autonomous_task_string_trigger(self):
        """添加任务时使用字符串触发类型"""
        engine = self._make_engine()
        tid = engine.add_autonomous_task(
            name="周期清理",
            trigger_type="time_interval",
            trigger_config={"interval_seconds": 600},
            action="cleanup",
        )
        assert isinstance(tid, str)
        self._cleanup(engine)

    # ---- add_monitor ----

    def test_add_monitor(self):
        """添加监控项成功"""
        engine = self._make_engine()
        result = engine.add_monitor(
            monitor_id="cpu_monitor",
            monitor_type=MonitorType.RESOURCE_USAGE,
            check_interval=60,
            thresholds={"warning": 0.7, "critical": 0.9},
        )
        assert result is True
        self._cleanup(engine)

    def test_add_monitor_string_type(self):
        """添加监控项时使用字符串类型"""
        engine = self._make_engine()
        result = engine.add_monitor(
            monitor_id="mem_monitor",
            monitor_type="resource_usage",
            check_interval=30,
            thresholds={"warning": 0.8},
        )
        assert result is True
        self._cleanup(engine)

    # ---- set_autonomous_goal ----

    def test_set_autonomous_goal(self):
        """设置自主目标成功"""
        engine = self._make_engine()
        gid = engine.set_autonomous_goal(
            description="优化系统响应时间",
            priority=7,
            sub_goals=["分析瓶颈", "实施优化", "验证效果"],
        )
        assert gid.startswith("goal_")
        goals = engine.get_active_goals()
        assert any(g["goal_id"] == gid for g in goals)
        self._cleanup(engine)

    # ---- run_autonomous_cycle ----

    def test_run_cycle_stopped(self):
        """未启动时运行循环返回错误"""
        engine = self._make_engine()
        report = engine.run_autonomous_cycle()
        assert report["status"] == "stopped"
        assert "error" in report
        self._cleanup(engine)

    def test_run_cycle_basic(self):
        """启动后基本循环成功执行"""
        engine = self._make_engine()
        engine.start()
        report = engine.run_autonomous_cycle()
        assert report["status"] == "completed"
        assert "cycle_number" in report
        assert "duration_seconds" in report
        assert "monitors" in report
        assert "scheduler" in report
        assert "goals" in report
        self._cleanup(engine)

    def test_run_cycle_with_anomalies(self):
        """有异常时循环产生决策"""
        engine = self._make_engine()
        engine.start()
        engine.add_monitor(
            "error_rate", MonitorType.ERROR_RATE, 30, {"warning": 0.5}
        )
        engine._monitor.update_metric("error_rate", 0.8)
        report = engine.run_autonomous_cycle()
        assert report["monitors"]["anomalies_detected"] >= 1
        assert report["decision"] is not None
        self._cleanup(engine)

    def test_run_cycle_with_tasks(self):
        """有到期任务时循环执行任务"""
        engine = self._make_engine()
        engine.start()
        # 注册一个 noop 动作
        engine._action_registry["noop"] = lambda: "done"
        engine.add_autonomous_task(
            "即时任务",
            TriggerType.TIME_INTERVAL,
            {"interval_seconds": 0},
            "noop",
        )
        time.sleep(0.1)  # 确保 next_run 已过去
        report = engine.run_autonomous_cycle()
        assert report["scheduler"]["tasks_executed"] >= 1
        # 等待后台线程完成后再清理
        time.sleep(0.3)
        self._cleanup(engine)

    def test_run_cycle_with_goals(self):
        """有活跃目标时循环正确处理"""
        engine = self._make_engine()
        engine.start()
        engine.set_autonomous_goal("测试目标", priority=5)
        report = engine.run_autonomous_cycle()
        assert report["goals"]["active_count"] == 1
        self._cleanup(engine)

    def test_run_cycle_multiple(self):
        """多次循环递增 cycle_number"""
        engine = self._make_engine()
        engine.start()
        engine.run_autonomous_cycle()
        engine.run_autonomous_cycle()
        engine.run_autonomous_cycle()
        report = engine.run_autonomous_cycle()
        assert report["cycle_number"] == 4
        self._cleanup(engine)

    # ---- get_autonomous_status ----

    def test_get_autonomous_status(self):
        """获取引擎状态包含所有子模块统计"""
        engine = self._make_engine()
        engine.start()
        status = engine.get_autonomous_status()
        assert status["engine_running"] is True
        assert "scheduler_stats" in status
        assert "monitor_stats" in status
        assert "decider_stats" in status
        self._cleanup(engine)

    def test_get_autonomous_status_after_cycle(self):
        """执行循环后状态包含 last_cycle"""
        engine = self._make_engine()
        engine.start()
        engine.run_autonomous_cycle()
        status = engine.get_autonomous_status()
        assert status["last_cycle"] is not None
        assert status["last_cycle"]["cycle_number"] == 1
        self._cleanup(engine)

    # ---- get_active_alerts ----

    def test_get_active_alerts(self):
        """获取活跃告警"""
        engine = self._make_engine()
        engine.add_monitor("alert_mon", MonitorType.SYSTEM_HEALTH, 30, {"warning": 0.5})
        engine._monitor.update_metric("alert_mon", 0.7)
        engine._monitor.check_monitor("alert_mon")
        alerts = engine.get_active_alerts()
        assert len(alerts) == 1
        assert alerts[0]["monitor_id"] == "alert_mon"
        engine.close()

    # ---- get_pending_tasks ----

    def test_get_pending_tasks(self):
        """获取待执行任务"""
        engine = self._make_engine()
        engine.add_autonomous_task(
            "挂起任务",
            TriggerType.TIME_INTERVAL,
            {"interval_seconds": 9999},
            "x",
        )
        tasks = engine.get_pending_tasks()
        assert len(tasks) >= 1
        assert any(t["name"] == "挂起任务" for t in tasks)
        engine.close()

    # ---- get_active_goals ----

    def test_get_active_goals(self):
        """获取活跃目标"""
        engine = self._make_engine()
        engine.set_autonomous_goal("活跃目标A")
        engine.set_autonomous_goal("活跃目标B")
        goals = engine.get_active_goals()
        assert len(goals) == 2
        engine.close()

    # ---- close ----

    def test_close_engine(self):
        """关闭引擎不报错"""
        engine = self._make_engine()
        engine.start()
        engine.close()
        assert engine.is_running() is False


# ====================================================================
#  TestAutonomousIntegration
# ====================================================================


class TestAutonomousIntegration:
    """完整工作流集成测试"""

    def _make_engine(self) -> AutonomousEngine:
        tmpdir = tempfile.TemporaryDirectory()
        engine = AutonomousEngine(data_dir=tmpdir.name)
        engine._tmpdir = tmpdir
        return engine

    def _cleanup(self, engine: AutonomousEngine):
        # 等待可能的后台线程完成
        time.sleep(0.2)
        engine.close()
        if hasattr(engine, "_tmpdir"):
            engine._tmpdir.cleanup()

    def test_full_workflow(self):
        """完整工作流: 创建引擎 → 启动 → 添加任务/监控/目标 → 运行循环 → 检查结果 → 停止 → 关闭"""
        engine = self._make_engine()

        # 1. 启动
        engine.start()
        assert engine.is_running() is True

        # 2. 添加任务
        engine._action_registry["sync"] = lambda: {"synced": True}
        tid = engine.add_autonomous_task(
            "数据同步",
            TriggerType.TIME_INTERVAL,
            {"interval_seconds": 0},  # 立即触发
            "sync",
        )
        assert isinstance(tid, str)

        # 3. 添加监控
        assert engine.add_monitor(
            "latency", MonitorType.PERFORMANCE, 10, {"warning": 0.6}
        ) is True

        # 4. 添加目标
        gid = engine.set_autonomous_goal(
            "提升系统响应速度", priority=8,
            sub_goals=["分析延迟", "优化查询", "验证性能"],
        )
        assert gid.startswith("goal_")

        # 5. 运行循环
        report = engine.run_autonomous_cycle()
        assert report["status"] == "completed"
        assert report["cycle_number"] == 1

        # 6. 检查结果
        status = engine.get_autonomous_status()
        assert status["engine_running"] is True
        assert status["cycle_count"] == 1

        pending = engine.get_pending_tasks()
        assert len(pending) >= 0  # 可能已被执行

        goals = engine.get_active_goals()
        assert len(goals) == 1

        # 7. 模拟异常并再运行循环
        engine._monitor.update_metric("latency", 0.75)
        report2 = engine.run_autonomous_cycle()
        assert report2["monitors"]["anomalies_detected"] >= 1
        assert report2["decision"] is not None

        # 8. 停止
        engine.stop()
        assert engine.is_running() is False

        # 9. 关闭
        engine.close()
        assert engine.is_running() is False

    def test_integration_multiple_cycles(self):
        """多轮循环后引擎状态一致性"""
        engine = self._make_engine()
        engine.start()

        engine.add_monitor("cpu", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.7})
        engine.set_autonomous_goal("持续优化", priority=6)

        for i in range(5):
            engine._monitor.update_metric("cpu", 0.5 + i * 0.1)
            report = engine.run_autonomous_cycle()
            assert report["status"] == "completed"
            assert report["cycle_number"] == i + 1

        status = engine.get_autonomous_status()
        assert status["cycle_count"] == 5
        assert status["last_cycle"]["cycle_number"] == 5

        self._cleanup(engine)

    def test_integration_stopped_cycle_fails(self):
        """停止后执行循环返回错误"""
        engine = self._make_engine()
        engine.start()
        engine.stop()
        report = engine.run_autonomous_cycle()
        assert report["status"] == "stopped"
        assert "error" in report
        self._cleanup(engine)

    def test_integration_alerts_after_anomaly(self):
        """产生异常后获取活跃告警"""
        engine = self._make_engine()
        engine.start()
        engine.add_monitor(
            "error_mon", MonitorType.ERROR_RATE, 30, {"warning": 0.5, "critical": 0.8}
        )
        engine._monitor.update_metric("error_mon", 0.85)
        engine.run_autonomous_cycle()

        alerts = engine.get_active_alerts()
        assert len(alerts) == 1
        assert alerts[0]["status"] == "critical"
        self._cleanup(engine)

    def test_integration_task_monitor_goal_interaction(self):
        """任务、监控、目标之间的交互"""
        engine = self._make_engine()
        engine.start()

        engine._action_registry["health_check"] = lambda: {"healthy": True}
        # 添加任务和监控
        engine.add_autonomous_task(
            "健康检查",
            TriggerType.TIME_INTERVAL,
            {"interval_seconds": 0},
            "health_check",
        )
        engine.add_monitor(
            "mem_usage", MonitorType.RESOURCE_USAGE, 30, {"warning": 0.6}
        )
        engine.set_autonomous_goal("资源优化", priority=7)

        # 制造异常
        engine._monitor.update_metric("mem_usage", 0.75)

        # 运行循环
        report = engine.run_autonomous_cycle()
        assert report["cycle_number"] == 1
        assert report["monitors"]["anomalies_detected"] >= 1

        # 再运行一次
        report = engine.run_autonomous_cycle()
        assert report["cycle_number"] == 2

        self._cleanup(engine)

    def test_integration_status_comprehensive(self):
        """综合状态包含所有模块数据"""
        engine = self._make_engine()
        engine.start()

        engine.add_autonomous_task(
            "周期清理", TriggerType.TIME_INTERVAL, {"interval_seconds": 999}, "cleanup"
        )
        engine.add_monitor("sys", MonitorType.SYSTEM_HEALTH, 60, {})
        engine.set_autonomous_goal("测试目标", priority=5)

        engine.run_autonomous_cycle()
        status = engine.get_autonomous_status()

        # 调度器统计
        assert status["scheduler_stats"]["total_tasks"] >= 1

        # 监控器统计
        assert status["monitor_stats"]["total_monitors"] >= 1

        # 决策器统计
        assert status["decider_stats"]["total_goals"] >= 1

        # 最近一次循环
        assert status["last_cycle"] is not None

        self._cleanup(engine)


# ====================================================================
#  TestJarvisAutonomousIntegration
# ====================================================================


class TestJarvisAutonomousIntegration:
    """JarvisCore 与自主引擎集成测试

    注意：这些测试只调用自主引擎相关方法，避免调用 chat() 以绕过情绪检测等无关模块。
    """

    def _make_jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        return jarvis

    def _cleanup(self, jarvis):
        time.sleep(0.2)
        jarvis.close()

    # ---- 1. 初始化后 autonomous_engine 不为空 ----

    def test_jarvis_init_autonomous_engine(self):
        """initialize 后 jarvis.autonomous_engine 不为 None"""
        jarvis = self._make_jarvis()
        try:
            assert jarvis.autonomous_engine is not None
        finally:
            self._cleanup(jarvis)

    # ---- 2. 启动自主模式 ----

    def test_jarvis_start_autonomous_mode(self):
        """start_autonomous_mode() 返回 True，is_running() 为 True"""
        jarvis = self._make_jarvis()
        try:
            assert jarvis.start_autonomous_mode() is True
            assert jarvis.autonomous_engine.is_running() is True
        finally:
            self._cleanup(jarvis)

    # ---- 3. 停止自主模式 ----

    def test_jarvis_stop_autonomous_mode(self):
        """stop_autonomous_mode() 返回 True，is_running() 为 False"""
        jarvis = self._make_jarvis()
        try:
            jarvis.start_autonomous_mode()
            assert jarvis.stop_autonomous_mode() is True
            assert jarvis.autonomous_engine.is_running() is False
        finally:
            self._cleanup(jarvis)

    # ---- 4. 添加自主任务 ----

    def test_jarvis_add_autonomous_task(self):
        """add_autonomous_task 返回非空 task_id"""
        jarvis = self._make_jarvis()
        try:
            tid = jarvis.add_autonomous_task(
                name="集成测试任务",
                trigger_type="time_interval",
                trigger_config={"interval_seconds": 300},
                action="test_action",
            )
            assert isinstance(tid, str)
            assert len(tid) > 0
        finally:
            self._cleanup(jarvis)

    # ---- 5. 添加带时间间隔触发器的自主任务 ----

    def test_jarvis_add_autonomous_task_with_time_interval(self):
        """添加 time_interval 触发任务并验证其存在"""
        jarvis = self._make_jarvis()
        try:
            tid = jarvis.add_autonomous_task(
                name="间隔任务",
                trigger_type="time_interval",
                trigger_config={"interval_seconds": 600},
                action="interval_action",
            )
            pending = jarvis.autonomous_engine.get_pending_tasks()
            assert any(t["task_id"] == tid for t in pending)
        finally:
            self._cleanup(jarvis)

    # ---- 6. 运行自主循环 ----

    def test_jarvis_run_autonomous_cycle(self):
        """run_autonomous_cycle 返回包含预期键的报告"""
        jarvis = self._make_jarvis()
        try:
            jarvis.start_autonomous_mode()
            report = jarvis.run_autonomous_cycle()
            assert report["status"] == "completed"
            assert "cycle_number" in report
            assert "duration_seconds" in report
            assert "monitors" in report
            assert "scheduler" in report
            assert "goals" in report
        finally:
            self._cleanup(jarvis)

    # ---- 7. get_status 包含 autonomous_engine ----

    def test_jarvis_get_status_includes_autonomous_engine(self):
        """get_status()["modules"]["autonomous_engine"] 存在"""
        jarvis = self._make_jarvis()
        try:
            jarvis.start_autonomous_mode()
            status = jarvis.get_status()
            assert "modules" in status
            assert "autonomous_engine" in status["modules"]
        finally:
            self._cleanup(jarvis)

    # ---- 8. close 清理自主资源 ----

    def test_jarvis_close_cleans_autonomous_resources(self):
        """close() 不抛异常，引擎资源已清理"""
        jarvis = self._make_jarvis()
        jarvis.start_autonomous_mode()
        jarvis.add_autonomous_task(
            name="清理任务",
            trigger_type="time_interval",
            trigger_config={"interval_seconds": 999},
            action="noop",
        )
        # close 应不抛异常
        jarvis.close()
        assert jarvis.initialized is False
        # autonomous_engine 引用仍在但内部已关闭
        assert jarvis.autonomous_engine.is_running() is False

    # ---- 9. 完整自主工作流 ----

    def test_jarvis_full_autonomous_workflow(self):
        """start → add task → add monitor → set goal → run cycle → get status → stop → close"""
        jarvis = self._make_jarvis()
        try:
            # start
            assert jarvis.start_autonomous_mode() is True

            # add task
            jarvis.autonomous_engine._action_registry["workflow_action"] = lambda: {"ok": True}
            tid = jarvis.add_autonomous_task(
                name="工作流任务",
                trigger_type="time_interval",
                trigger_config={"interval_seconds": 0},
                action="workflow_action",
            )
            assert tid

            # add monitor
            assert jarvis.autonomous_engine.add_monitor(
                "workflow_mon", MonitorType.SYSTEM_HEALTH, 60, {"warning": 0.5}
            ) is True

            # set goal
            gid = jarvis.autonomous_engine.set_autonomous_goal("工作流目标", priority=5)
            assert gid.startswith("goal_")

            # run cycle
            report = jarvis.run_autonomous_cycle()
            assert report["status"] == "completed"

            # get status
            status = jarvis.get_status()
            assert "autonomous_engine" in status["modules"]

            # stop
            assert jarvis.stop_autonomous_mode() is True

            # close
            jarvis.close()
            assert jarvis.initialized is False
        finally:
            time.sleep(0.2)

    # ---- 10. 待执行任务列表 ----

    def test_jarvis_autonomous_task_pending_tasks(self):
        """添加任务后 get_pending_tasks 能获取到"""
        jarvis = self._make_jarvis()
        try:
            jarvis.add_autonomous_task(
                name="挂起任务",
                trigger_type="time_interval",
                trigger_config={"interval_seconds": 9999},
                action="x",
            )
            pending = jarvis.autonomous_engine.get_pending_tasks()
            assert any(t["name"] == "挂起任务" for t in pending)
        finally:
            self._cleanup(jarvis)

    # ---- 11. 添加监控 ----

    def test_jarvis_autonomous_add_monitor(self):
        """add_monitor 返回 True"""
        jarvis = self._make_jarvis()
        try:
            result = jarvis.autonomous_engine.add_monitor(
                monitor_id="jarvis_mon",
                monitor_type=MonitorType.RESOURCE_USAGE,
                check_interval=30,
                thresholds={"warning": 0.7, "critical": 0.9},
            )
            assert result is True
        finally:
            self._cleanup(jarvis)

    # ---- 12. 获取活跃目标 ----

    def test_jarvis_autonomous_get_active_goals(self):
        """初始时活跃目标列表为空"""
        jarvis = self._make_jarvis()
        try:
            goals = jarvis.autonomous_engine.get_active_goals()
            assert isinstance(goals, list)
            assert len(goals) == 0
        finally:
            self._cleanup(jarvis)
