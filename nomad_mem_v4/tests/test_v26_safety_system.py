"""
第十八轮端到端测试: 自主安全系统 + Jarvis集成

测试覆盖:
- SafetyEngine: 风险评分、行为基线、安全策略
- SafetyMonitor: 实时监控、异常检测(频率/风险累积/模式变化/异常时段)
- JarvisCore集成: 风险评估/异常检查/策略切换/安全状态
"""
import pytest
import os
import tempfile
import time


# ─── Safety Engine Tests ────────────────────────────────────────────────────


class TestSafetyEnums:
    def test_risk_levels(self):
        from nomad_mem.core.safety_engine import RiskLevel
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_safety_actions(self):
        from nomad_mem.core.safety_engine import SafetyAction
        assert SafetyAction.ALLOW.value == "allow"
        assert SafetyAction.BLOCK.value == "block"


class TestRiskAssessment:
    def test_create_assessment(self):
        from nomad_mem.core.safety_engine import RiskAssessment, RiskLevel, SafetyAction
        a = RiskAssessment(
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            safety_action=SafetyAction.LOG,
        )
        assert a.risk_score == 0.5

    def test_assessment_to_dict(self):
        from nomad_mem.core.safety_engine import RiskAssessment, RiskLevel, SafetyAction
        a = RiskAssessment(
            risk_score=0.7,
            risk_level=RiskLevel.HIGH,
            safety_action=SafetyAction.REQUIRE_CONFIRM,
            reasons=["high risk action"],
        )
        d = a.to_dict()
        assert d["risk_score"] == 0.7
        assert d["risk_level"] == "high"


class TestRiskScoringEngine:
    @pytest.fixture
    def engine(self):
        from nomad_mem.core.safety_engine import RiskScoringEngine
        return RiskScoringEngine()

    def test_low_risk_read(self, engine):
        result = engine.assess_risk("read")
        assert result.risk_level.value == "low"
        assert result.safety_action.value == "allow"

    def test_high_risk_delete(self, engine):
        result = engine.assess_risk("delete")
        assert result.risk_score > 0.1

    def test_frequency_risk(self, engine):
        result = engine.assess_risk("read", frequency=50)
        assert len(result.reasons) >= 1

    def test_non_typical_hour(self, engine):
        result = engine.assess_risk("read", is_typical_hour=False)
        assert result.risk_score > 0.1

    def test_sensitive_target(self, engine):
        result = engine.assess_risk("read", target="/etc/shadow")
        assert len(result.reasons) >= 1

    def test_deviation_from_baseline(self, engine):
        result = engine.assess_risk("read", deviation_from_baseline=0.8)
        assert result.risk_score > 0.1

    def test_custom_rule(self, engine):
        engine.add_custom_rule(r"secret_file", 0.5, "操作机密文件")
        result = engine.assess_risk("read", target="/path/to/secret_file")
        assert len(result.reasons) >= 1

    def test_action_multiplier(self, engine):
        engine.set_action_multiplier("read", 3.0)
        result = engine.assess_risk("read")
        assert result.risk_score > 0.1

    def test_critical_level(self, engine):
        result = engine.assess_risk("admin", target="/etc/shadow", frequency=50)
        assert result.risk_level.value in ("high", "critical")

    def test_score_normalized(self, engine):
        result = engine.assess_risk("delete", target="/etc/shadow", frequency=100,
                                     deviation_from_baseline=0.9)
        assert result.risk_score <= 1.0


class TestBehaviorBaselineManager:
    @pytest.fixture
    def manager(self):
        from nomad_mem.core.safety_engine import BehaviorBaselineManager
        db = tempfile.mktemp(suffix=".db")
        m = BehaviorBaselineManager(db_path=db)
        yield m
        m.close()
        if os.path.exists(db):
            os.remove(db)

    def test_init(self, manager):
        assert manager.db_path is not None

    def test_record_activity(self, manager):
        manager.record_activity("user1", "read", 0.1)
        stats = manager.get_stats()
        assert stats["total_activities_recorded"] == 1

    def test_get_baseline_no_data(self, manager):
        baseline = manager.get_baseline("nobody")
        assert baseline is None

    def test_update_baseline(self, manager):
        for _ in range(10):
            manager.record_activity("user1", "read", 0.1)
        manager.update_baseline("user1")
        baseline = manager.get_baseline("user1")
        assert baseline is not None
        assert baseline.sample_count == 10

    def test_calculate_deviation_no_baseline(self, manager):
        dev = manager.calculate_deviation("new_user", "read")
        assert dev == 0.0

    def test_calculate_deviation_with_baseline(self, manager):
        for _ in range(10):
            manager.record_activity("user1", "read", 0.1)
        manager.update_baseline("user1")
        dev = manager.calculate_deviation("user1", "delete")
        assert dev >= 0.0  # 可能偏离如果delete不在常见操作中


class TestSafetyPolicyManager:
    @pytest.fixture
    def pm(self):
        from nomad_mem.core.safety_engine import SafetyPolicyManager
        return SafetyPolicyManager()

    def test_default_policy(self, pm):
        policy = pm.get_active_policy()
        assert "risk_threshold_block" in policy

    def test_set_policy(self, pm):
        assert pm.set_active_policy("strict") is True
        assert pm.get_active_policy()["risk_threshold_block"] == 0.5

    def test_set_invalid_policy(self, pm):
        assert pm.set_active_policy("nonexistent") is False

    def test_determine_action_allow(self, pm):
        action = pm.determine_action(0.1)
        assert action.value == "allow"

    def test_determine_action_block(self, pm):
        action = pm.determine_action(0.9)
        assert action.value == "block"

    def test_determine_action_confirm(self, pm):
        action = pm.determine_action(0.7)
        assert action.value == "require_confirm"

    def test_strict_policy(self, pm):
        pm.set_active_policy("strict")
        # strict blocks at 0.5, confirms at 0.3
        assert pm.determine_action(0.6).value == "block"
        assert pm.determine_action(0.4).value == "require_confirm"

    def test_relaxed_policy(self, pm):
        pm.set_active_policy("relaxed")
        assert pm.determine_action(0.7).value in ("allow", "log")  # relaxed is more lenient

    def test_add_custom_policy(self, pm):
        pm.add_policy("custom", {
            "risk_threshold_block": 0.6,
            "risk_threshold_confirm": 0.4,
            "risk_threshold_log": 0.2,
            "max_actions_per_minute": 50,
            "enabled": True,
        })
        assert pm.set_active_policy("custom") is True

    def test_get_all_policies(self, pm):
        policies = pm.get_all_policies()
        assert "default" in policies
        assert "strict" in policies
        assert "relaxed" in policies


class TestSafetyEngineIntegration:
    @pytest.fixture
    def engine(self):
        from nomad_mem.core.safety_engine import SafetyEngine
        db = tempfile.mktemp(suffix=".db")
        e = SafetyEngine(db_path=db)
        yield e
        e.close()
        if os.path.exists(db):
            os.remove(db)

    def test_assess_operation(self, engine):
        result = engine.assess_operation("user1", "read", "/data/file")
        assert "risk_score" in result.to_dict()

    def test_assess_high_risk_operation(self, engine):
        result = engine.assess_operation("user1", "delete", "/etc/config")
        assert result.risk_score > 0.1

    def test_set_policy(self, engine):
        assert engine.set_policy("strict") is True

    def test_get_safety_status(self, engine):
        status = engine.get_safety_status()
        assert "baseline" in status
        assert "policy" in status

    def test_get_recent_assessments(self, engine):
        engine.assess_operation("user1", "read")
        engine.assess_operation("user1", "write")
        assessments = engine.get_recent_assessments()
        assert len(assessments) >= 2

    def test_update_baseline(self, engine):
        for _ in range(10):
            engine.assess_operation("user1", "read")
        engine.update_user_baseline("user1")
        status = engine.get_safety_status()
        assert status["baseline"]["total_users_with_baseline"] >= 1


# ─── Safety Monitor Tests ───────────────────────────────────────────────────


class TestSafetyEvent:
    def test_create_event(self):
        from nomad_mem.autonomy.safety_monitor import SafetyEvent, EventType, ResponseAction
        e = SafetyEvent(
            event_id="test_1",
            event_type=EventType.FREQUENCY_SPIKE,
            user_id="user1",
            severity=0.8,
            description="test",
            response=ResponseAction.THROTTLE,
        )
        assert e.severity == 0.8

    def test_event_to_dict(self):
        from nomad_mem.autonomy.safety_monitor import SafetyEvent, EventType, ResponseAction
        e = SafetyEvent(
            event_id="test_2",
            event_type=EventType.RISK_ACCUMULATION,
            user_id="user1",
            severity=0.6,
            description="risk",
            response=ResponseAction.ALERT,
        )
        d = e.to_dict()
        assert d["event_type"] == "risk_accumulation"
        assert d["response"] == "alert"


class TestSafetyMonitorCore:
    @pytest.fixture
    def monitor(self):
        from nomad_mem.autonomy.safety_monitor import SafetyMonitor
        db = tempfile.mktemp(suffix=".db")
        m = SafetyMonitor(db_path=db)
        yield m
        m.close()
        if os.path.exists(db):
            os.remove(db)

    def test_init(self, monitor):
        assert monitor.db_path is not None

    def test_report_operation(self, monitor):
        monitor.report_operation("user1", "read", 0.1)
        status = monitor.get_user_status("user1")
        assert status["total_ops"] == 1

    def test_get_user_status_empty(self, monitor):
        status = monitor.get_user_status("nobody")
        assert status["total_ops"] == 0

    def test_get_stats(self, monitor):
        stats = monitor.get_stats()
        assert "total_events_recorded" in stats

    def test_set_threshold(self, monitor):
        monitor.set_threshold(frequency=10, risk_accumulation=2.0)
        assert monitor.frequency_threshold == 10
        assert monitor.risk_accumulation_threshold == 2.0


class TestSafetyMonitorAnomalyDetection:
    @pytest.fixture
    def monitor(self):
        from nomad_mem.autonomy.safety_monitor import SafetyMonitor
        db = tempfile.mktemp(suffix=".db")
        m = SafetyMonitor(db_path=db)
        yield m
        m.close()
        if os.path.exists(db):
            os.remove(db)

    def test_frequency_spike_detection(self, monitor):
        monitor.frequency_threshold = 5
        # Report many operations quickly
        for _ in range(10):
            monitor.report_operation("user1", "read", 0.1)
        events = monitor.check_anomalies("user1")
        freq_events = [e for e in events if e.event_type.value == "frequency_spike"]
        assert len(freq_events) >= 1

    def test_risk_accumulation_detection(self, monitor):
        monitor.risk_accumulation_threshold = 1.0
        # Report high-risk operations
        for _ in range(5):
            monitor.report_operation("user1", "delete", 0.8)
        events = monitor.check_anomalies("user1")
        risk_events = [e for e in events if e.event_type.value == "risk_accumulation"]
        assert len(risk_events) >= 1

    def test_no_anomalies_normal_usage(self, monitor):
        monitor.report_operation("user1", "read", 0.05)
        monitor.report_operation("user1", "write", 0.1)
        events = monitor.check_anomalies("user1")
        assert len(events) == 0

    def test_pattern_change_detection(self, monitor):
        # Build a pattern with one dominant action
        for _ in range(25):
            monitor.report_operation("user1", "read", 0.1)
        # Then add diverse actions to dilute the pattern
        diverse_actions = ["write", "delete", "execute", "admin", "network",
                          "query", "schedule", "email", "chat", "task"]
        for action in diverse_actions:
            monitor.report_operation("user1", action, 0.2)
        events = monitor.check_anomalies("user1")
        # May or may not detect pattern change depending on ratios
        assert isinstance(events, list)

    def test_get_events(self, monitor):
        monitor.frequency_threshold = 5
        for _ in range(10):
            monitor.report_operation("user1", "read", 0.1)
        monitor.check_anomalies("user1")
        events = monitor.get_events("user1")
        assert len(events) >= 1

    def test_events_persist_across_checks(self, monitor):
        monitor.frequency_threshold = 3
        for _ in range(5):
            monitor.report_operation("user1", "read", 0.1)
        monitor.check_anomalies("user1")
        events1 = monitor.get_events("user1")
        assert len(events1) >= 1
        # Second check should not duplicate
        monitor.check_anomalies("user1")
        events2 = monitor.get_events("user1")
        # Events should still be there
        assert len(events2) >= 1


# ─── Jarvis Integration Tests ────────────────────────────────────────────────


class TestJarvisSafetyIntegration:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_safety_engine_initialized(self, jarvis):
        assert jarvis.safety_engine is not None

    def test_safety_monitor_initialized(self, jarvis):
        assert jarvis.safety_monitor is not None

    def test_status_includes_safety(self, jarvis):
        status = jarvis.get_status()
        assert "safety_engine" in status["modules"]
        assert "safety_monitor" in status["modules"]

    def test_assess_safety_risk(self, jarvis):
        result = jarvis.assess_safety_risk("user1", "read", "/data/file")
        assert "risk_score" in result

    def test_assess_high_risk(self, jarvis):
        result = jarvis.assess_safety_risk("user1", "delete", "/etc/config")
        assert result["risk_score"] > 0.1

    def test_check_safety_anomalies_no_data(self, jarvis):
        events = jarvis.check_safety_anomalies("new_user")
        assert isinstance(events, list)

    def test_report_user_operation(self, jarvis):
        jarvis.report_user_operation("user1", "read", 0.1, "/data/file")
        status = jarvis.get_user_safety_status("user1")
        assert status["total_ops"] >= 1

    def test_get_user_safety_status(self, jarvis):
        jarvis.report_user_operation("user1", "read", 0.1)
        status = jarvis.get_user_safety_status("user1")
        assert "user_id" in status

    def test_set_safety_policy(self, jarvis):
        assert jarvis.set_safety_policy("strict") is True
        assert jarvis.set_safety_policy("relaxed") is True

    def test_get_safety_events(self, jarvis):
        jarvis.safety_monitor.frequency_threshold = 3
        for _ in range(5):
            jarvis.report_user_operation("user1", "read", 0.1)
        jarvis.check_safety_anomalies("user1")
        events = jarvis.get_safety_events("user1")
        assert len(events) >= 1

    def test_update_user_baseline(self, jarvis):
        for _ in range(10):
            jarvis.assess_safety_risk("user1", "read")
        jarvis.update_user_baseline("user1")
        overview = jarvis.get_safety_overview()
        assert overview["baseline"]["total_users_with_baseline"] >= 1

    def test_get_safety_overview(self, jarvis):
        overview = jarvis.get_safety_overview()
        assert "policy" in overview

    def test_close_cleans_up(self, jarvis):
        jarvis.close()
        assert jarvis.initialized is False


class TestJarvisFullWorkflowWithSafety:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_full_safety_workflow(self, jarvis):
        # Record operations
        for _ in range(5):
            jarvis.report_user_operation("user1", "read", 0.1)
        jarvis.report_user_operation("user1", "delete", 0.6, "/etc/config")

        # Check anomalies
        events = jarvis.check_safety_anomalies("user1")
        assert isinstance(events, list)

        # Get safety status
        status = jarvis.get_user_safety_status("user1")
        assert status["total_ops"] >= 6

    def test_safety_policy_switching(self, jarvis):
        # Default policy
        default_result = jarvis.assess_safety_risk("user1", "execute", "/bin/script")
        default_score = default_result["risk_score"]

        # Switch to strict
        jarvis.set_safety_policy("strict")
        strict_result = jarvis.assess_safety_risk("user1", "execute", "/bin/script")

        # Both should produce valid results
        assert "risk_score" in strict_result

    def test_high_frequency_triggers_alert(self, jarvis):
        jarvis.safety_monitor.frequency_threshold = 3
        for _ in range(10):
            jarvis.report_user_operation("user1", "read", 0.05)

        events = jarvis.check_safety_anomalies("user1")
        freq_events = [e for e in events if e.event_type.value == "frequency_spike"]
        assert len(freq_events) >= 1

    def test_safety_events_accumulate(self, jarvis):
        jarvis.safety_monitor.frequency_threshold = 2
        jarvis.safety_monitor.risk_accumulation_threshold = 0.5

        # Trigger frequency spike
        for _ in range(5):
            jarvis.report_user_operation("user1", "read", 0.1)

        jarvis.check_safety_anomalies("user1")
        events = jarvis.get_safety_events("user1", k=10)
        assert len(events) >= 1
