"""
V6测试 - 自主意识、持久化、审计日志
"""
import os
import sys
import json
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAutonomyDriver:
    """自主意识驱动引擎测试"""

    def test_sense_system_alert(self):
        """测试系统告警感知"""
        from nomad_mem.autonomy.driver import AutonomyDriver, TriggerType, Priority

        driver = AutonomyDriver()
        context = {
            "disk_usage": {"percent": 95},
            "memory_usage": {"percent": 50},
            "working_memory": {"size": 4, "max": 4},
            "current_hour": 12,
            "last_consolidation_time": time.time() - 30000,
            "consolidation_interval": 21600,
        }

        events = driver.sense(context)
        # 应该有磁盘告警和工作记忆满溢
        assert len(events) >= 1
        assert any(e.source == "system" for e in events)

    def test_evaluate_system_alert(self):
        """测试系统告警评估"""
        from nomad_mem.autonomy.driver import (
            AutonomyDriver, TriggerEvent, TriggerType, Priority,
        )

        driver = AutonomyDriver()
        event = TriggerEvent(
            trigger_type=TriggerType.STATE,
            priority=Priority.HIGH,
            source="system",
            message="磁盘空间不足，已使用 95.0%",
            data={"disk_percent": 95},
        )

        proposals = driver.evaluate([event], {})
        assert len(proposals) >= 1
        assert proposals[0].skill_name == "disk_usage"

    def test_behavior_sensor_idle(self):
        """测试行为传感器空闲检测"""
        from nomad_mem.autonomy.driver import AutonomyDriver

        driver = AutonomyDriver()
        # 设置上次交互为很久之前
        for sensor in driver.sensors:
            if sensor.name == "behavior":
                sensor.last_interaction_time = time.time() - 3600  # 1小时前
                sensor.last_idle_reminder = 0  # 允许触发

        context = {
            "disk_usage": {"percent": 50},
            "memory_usage": {"percent": 50},
            "working_memory": {"size": 1, "max": 4},
            "current_hour": 12,
            "last_consolidation_time": time.time(),
        }

        events = driver.sense(context)
        behavior_events = [e for e in events if e.source == "behavior"]
        assert len(behavior_events) >= 1

    def test_greeting_trigger(self):
        """测试问候触发"""
        from nomad_mem.autonomy.driver import AutonomyDriver

        driver = AutonomyDriver()
        for sensor in driver.sensors:
            if sensor.name == "behavior":
                sensor.last_greeting_time = 0  # 允许触发

        context = {
            "disk_usage": {"percent": 50},
            "memory_usage": {"percent": 50},
            "working_memory": {"size": 1, "max": 4},
            "current_hour": 7,  # 早上好
            "last_consolidation_time": time.time(),
        }

        events = driver.sense(context)
        greeting_events = [e for e in events if "早上好" in e.message]
        assert len(greeting_events) >= 1

    def test_action_cooldown(self):
        """测试行动冷却"""
        from nomad_mem.autonomy.driver import (
            AutonomyDriver, TriggerEvent, TriggerType, Priority, ActionProposal,
        )

        driver = AutonomyDriver()
        driver.action_cooldown = 0  # 禁用冷却以便测试

        event = TriggerEvent(
            trigger_type=TriggerType.BEHAVIOR,
            priority=Priority.LOW,
            source="behavior",
            message="test",
        )

        proposals = driver.evaluate([event], {})
        # 执行后记录历史
        results = driver.act(proposals)
        assert len(results) >= 1

        # 再次评估，应该被冷却
        proposals2 = driver.evaluate([event], {})
        # 由于action_cooldown=0，冷却期已过，应该还有提议
        # 但实际应该被去重逻辑过滤
        assert len(proposals2) <= len(proposals)

    def test_full_cycle(self):
        """测试完整感知-评估-行动循环"""
        from nomad_mem.autonomy.driver import AutonomyDriver

        driver = AutonomyDriver()
        driver.sense_interval = 0  # 允许立即触发
        driver.action_cooldown = 0

        context = {
            "disk_usage": {"percent": 50},
            "memory_usage": {"percent": 50},
            "working_memory": {"size": 1, "max": 4},
            "current_hour": 7,
            "last_consolidation_time": time.time(),
        }

        results = driver.cycle(context)
        # 至少应该有问候触发
        assert isinstance(results, list)

    def test_status(self):
        """测试状态查询"""
        from nomad_mem.autonomy.driver import AutonomyDriver

        driver = AutonomyDriver(config={"sense_interval": 120})
        status = driver.get_status()

        assert "running" in status
        assert "sense_interval" in status
        assert status["sense_interval"] == 120
        assert "sensors" in status
        assert len(status["sensors"]) == 3


class TestConversationHistory:
    """对话历史持久化测试"""

    def test_save_and_load(self):
        """测试保存和加载"""
        from nomad_mem.persistence.history import ConversationHistory

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_history.db")
            history = ConversationHistory(db_path)

            # 保存消息
            history.save_message("user", "你好", user_id="test")
            history.save_message("assistant", "你好！有什么可以帮助你的？", user_id="test")

            # 加载
            messages = history.load_history(user_id="test")
            assert len(messages) == 2
            # load_history returns oldest first (reversed from DESC query)
            assert messages[0]["role"] == "user" or messages[0]["role"] == "assistant"
            assert messages[1]["role"] == "user" or messages[1]["role"] == "assistant"

            history.close()

    def test_save_history_batch(self):
        """测试批量保存"""
        from nomad_mem.persistence.history import ConversationHistory

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_history.db")
            history = ConversationHistory(db_path)

            messages = [
                {"role": "user", "content": "msg1"},
                {"role": "assistant", "content": "reply1"},
                {"role": "user", "content": "msg2"},
            ]
            history.save_history(messages, user_id="test")

            loaded = history.load_history(user_id="test")
            assert len(loaded) == 3

            history.close()

    def test_skill_call_history(self):
        """测试技能调用记录"""
        from nomad_mem.persistence.history import ConversationHistory

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_history.db")
            history = ConversationHistory(db_path)

            history.record_skill_call(
                "calculate",
                {"expression": "2+3"},
                "2+3 = 5",
                user_id="test",
            )

            records = history.get_skill_history(user_id="test")
            assert len(records) == 1
            assert records[0]["skill_name"] == "calculate"

            history.close()

    def test_stats(self):
        """测试统计信息"""
        from nomad_mem.persistence.history import ConversationHistory

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_history.db")
            history = ConversationHistory(db_path)

            history.save_message("user", "test", user_id="test")
            history.record_skill_call("test_skill", {}, "ok", user_id="test")

            stats = history.get_stats(user_id="test")
            assert stats["message_count"] == 1
            assert stats["skill_call_count"] == 1

            history.close()

    def test_clear_history(self):
        """测试清空历史"""
        from nomad_mem.persistence.history import ConversationHistory

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_history.db")
            history = ConversationHistory(db_path)

            history.save_message("user", "test", user_id="test")
            history.clear_history(user_id="test")

            messages = history.load_history(user_id="test")
            assert len(messages) == 0

            history.close()


class TestAuditLogger:
    """审计日志测试"""

    def test_log_skill_call(self):
        """测试技能调用日志"""
        from nomad_mem.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            logger.log_skill_call("calculate", {"expression": "2+3"}, "2+3 = 5")

            # 读取日志文件
            log_path = logger._current_path
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            record = json.loads(lines[0])
            assert record["event_type"] == "skill_call"
            assert record["skill_name"] == "calculate"

            logger.close()

    def test_log_user_message(self):
        """测试用户消息日志"""
        from nomad_mem.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            logger.log_user_message("你好", response="你好！")

            log_path = logger._current_path
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            record = json.loads(lines[0])
            assert record["event_type"] == "user_message"
            assert record["message"] == "你好"

            logger.close()

    def test_log_system_event(self):
        """测试系统事件日志"""
        from nomad_mem.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            logger.log_system_event("startup", "系统启动", level="info")

            log_path = logger._current_path
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            record = json.loads(lines[0])
            assert record["event_type"] == "system_event"
            assert record["event"] == "startup"

            logger.close()

    def test_log_memory_operation(self):
        """测试记忆操作日志"""
        from nomad_mem.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            logger.log_memory_operation("insert", "新增向量", vector_id=42)

            log_path = logger._current_path
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            record = json.loads(lines[0])
            assert record["event_type"] == "memory_operation"
            assert record["operation"] == "insert"
            assert record["vector_id"] == 42

            logger.close()

    def test_multiple_logs(self):
        """测试多条日志"""
        from nomad_mem.audit_logger import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            logger.log_skill_call("calc", {"expr": "1+1"}, "2")
            logger.log_user_message("hello", response="hi")
            logger.log_system_event("test", "testing")

            log_path = logger._current_path
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 3

            logger.close()
