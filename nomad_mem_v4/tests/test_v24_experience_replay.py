"""
第十六轮端到端测试: 经验回放系统 + 经验摘要 + Jarvis集成

测试覆盖:
- ExperienceReplay: 经验记录/检索/模式提取/统计分析
- ExperienceSummarizer: 用户摘要/系统摘要/失败分析/建议生成
- JarvisCore集成: 经验记录/检索/摘要/模式提取
"""
import pytest
import os
import tempfile
import time


# ─── Experience Replay Tests ────────────────────────────────────────────────


class TestExperienceType:
    def test_experience_types(self):
        from nomad_mem.autonomy.experience_replay import ExperienceType
        assert ExperienceType.SUCCESS.value == "success"
        assert ExperienceType.FAILURE.value == "failure"
        assert ExperienceType.INSIGHT.value == "insight"
        assert ExperienceType.PREFERENCE.value == "preference"
        assert ExperienceType.PATTERN.value == "pattern"

    def test_experience_outcomes(self):
        from nomad_mem.autonomy.experience_replay import ExperienceOutcome
        assert ExperienceOutcome.POSITIVE.value == "positive"
        assert ExperienceOutcome.NEGATIVE.value == "negative"
        assert ExperienceOutcome.NEUTRAL.value == "neutral"


class TestExperienceDataclass:
    def test_create_experience(self):
        from nomad_mem.autonomy.experience_replay import Experience, ExperienceType, ExperienceOutcome
        exp = Experience(
            exp_id="test_1",
            exp_type=ExperienceType.SUCCESS,
            outcome=ExperienceOutcome.POSITIVE,
            user_id="user1",
            intent="schedule",
            context='{"time": "morning"}',
            action_taken="used calendar",
            result="scheduled successfully",
        )
        assert exp.importance == 0.5
        assert exp.usage_count == 0

    def test_experience_to_dict(self):
        from nomad_mem.autonomy.experience_replay import Experience, ExperienceType, ExperienceOutcome
        exp = Experience(
            exp_id="test_2",
            exp_type=ExperienceType.FAILURE,
            outcome=ExperienceOutcome.NEGATIVE,
            user_id="user1",
            intent="query",
            context="{}",
            action_taken="search",
            result="failed",
            lesson_learned="need better search",
            importance=0.8,
        )
        d = exp.to_dict()
        assert d["exp_type"] == "failure"
        assert d["outcome"] == "negative"
        restored = Experience.from_dict(d)
        assert restored.exp_type == ExperienceType.FAILURE


class TestExperienceReplayCore:
    @pytest.fixture
    def replay(self):
        from nomad_mem.autonomy.experience_replay import ExperienceReplay
        db = tempfile.mktemp(suffix=".db")
        r = ExperienceReplay(db_path=db)
        yield r
        r.close()
        if os.path.exists(db):
            os.remove(db)

    def test_init(self, replay):
        assert replay.db_path is not None

    def test_record_success_experience(self, replay):
        exp_id = replay.record_experience(
            user_id="user1",
            intent="schedule",
            context='{"time": "morning"}',
            action_taken="calendar_tool",
            result="scheduled",
        )
        assert exp_id is not None
        exp = replay.get_experience(exp_id)
        assert exp is not None
        assert exp.intent == "schedule"

    def test_record_failure_experience(self, replay):
        from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
        exp_id = replay.record_experience(
            user_id="user1",
            intent="query",
            context="{}",
            action_taken="search",
            result="not found",
            exp_type=ExperienceType.FAILURE,
            outcome=ExperienceOutcome.NEGATIVE,
            lesson_learned="search term too specific",
            importance=0.7,
        )
        exp = replay.get_experience(exp_id)
        assert exp.outcome == ExperienceOutcome.NEGATIVE
        assert "search term" in exp.lesson_learned

    def test_increment_usage(self, replay):
        exp_id = replay.record_experience(
            user_id="user1", intent="test", context="{}",
            action_taken="test", result="ok",
        )
        replay.increment_usage(exp_id)
        replay.increment_usage(exp_id)
        exp = replay.get_experience(exp_id)
        assert exp.usage_count == 2

    def test_get_nonexistent_experience(self, replay):
        exp = replay.get_experience("nonexistent")
        assert exp is None


class TestExperienceReplayRetrieval:
    @pytest.fixture
    def replay(self):
        from nomad_mem.autonomy.experience_replay import ExperienceReplay
        db = tempfile.mktemp(suffix=".db")
        r = ExperienceReplay(db_path=db)
        yield r
        r.close()
        if os.path.exists(db):
            os.remove(db)

    def test_retrieve_similar(self, replay):
        replay.record_experience(
            user_id="user1", intent="schedule_meeting",
            context="{}", action_taken="calendar", result="ok",
            importance=0.9,
        )
        results = replay.retrieve_similar("schedule", k=5)
        assert len(results) >= 1

    def test_retrieve_by_intent(self, replay):
        for i in range(3):
            replay.record_experience(
                user_id="user1", intent="chat",
                context="{}", action_taken="reply", result="ok",
            )
        results = replay.retrieve_by_intent("chat", k=5)
        assert len(results) == 3

    def test_retrieve_by_user(self, replay):
        replay.record_experience(
            user_id="alice", intent="query", context="{}",
            action_taken="search", result="ok",
        )
        replay.record_experience(
            user_id="bob", intent="query", context="{}",
            action_taken="search", result="ok",
        )
        alice_exps = replay.retrieve_by_user("alice")
        assert len(alice_exps) == 1

    def test_retrieve_recent_failures(self, replay):
        from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
        for i in range(3):
            replay.record_experience(
                user_id="user1", intent=f"test_{i}", context="{}",
                action_taken="fail", result="error",
                exp_type=ExperienceType.FAILURE,
                outcome=ExperienceOutcome.NEGATIVE,
            )
        failures = replay.retrieve_recent_failures(k=5)
        assert len(failures) == 3

    def test_retrieve_lessons(self, replay):
        replay.record_experience(
            user_id="user1", intent="test", context="{}",
            action_taken="test", result="ok",
            lesson_learned="always validate input first",
            importance=0.9,
        )
        lessons = replay.retrieve_lessons("test", k=5)
        assert len(lessons) >= 1
        assert "validate" in lessons[0]


class TestExperienceReplayPatterns:
    @pytest.fixture
    def replay(self):
        from nomad_mem.autonomy.experience_replay import ExperienceReplay
        db = tempfile.mktemp(suffix=".db")
        r = ExperienceReplay(db_path=db)
        yield r
        r.close()
        if os.path.exists(db):
            os.remove(db)

    def test_extract_patterns_no_data(self, replay):
        patterns = replay.extract_patterns()
        assert isinstance(patterns, list)

    def test_extract_patterns_with_data(self, replay):
        for i in range(3):
            replay.record_experience(
                user_id="user1", intent="schedule",
                context="{}", action_taken="calendar", result="ok",
            )
        patterns = replay.extract_patterns()
        assert len(patterns) >= 1
        assert patterns[0].frequency >= 3

    def test_save_and_get_patterns(self, replay):
        from nomad_mem.autonomy.experience_replay import ExperiencePattern
        pattern = ExperiencePattern(
            pattern_id="test_pat",
            pattern_type="test",
            description="test pattern",
            frequency=5,
            success_rate=0.8,
        )
        replay.save_patterns([pattern])
        patterns = replay.get_patterns()
        assert len(patterns) >= 1

    def test_failure_pattern_extraction(self, replay):
        from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
        for i in range(3):
            replay.record_experience(
                user_id="user1", intent=f"fail_{i}", context="{}",
                action_taken="bad", result="timeout_error",
                exp_type=ExperienceType.FAILURE,
                outcome=ExperienceOutcome.NEGATIVE,
            )
        patterns = replay.extract_patterns()
        failure_pats = [p for p in patterns if p.pattern_type == "failure_pattern"]
        assert len(failure_pats) >= 1


class TestExperienceReplayAnalytics:
    @pytest.fixture
    def replay(self):
        from nomad_mem.autonomy.experience_replay import ExperienceReplay
        db = tempfile.mktemp(suffix=".db")
        r = ExperienceReplay(db_path=db)
        yield r
        r.close()
        if os.path.exists(db):
            os.remove(db)

    def test_user_stats_empty(self, replay):
        stats = replay.get_user_stats("nobody")
        assert stats["total_experiences"] == 0

    def test_user_stats_with_data(self, replay):
        replay.record_experience(
            user_id="user1", intent="test1", context="{}",
            action_taken="a", result="ok",
        )
        from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
        replay.record_experience(
            user_id="user1", intent="test2", context="{}",
            action_taken="b", result="fail",
            exp_type=ExperienceType.FAILURE,
            outcome=ExperienceOutcome.NEGATIVE,
        )
        stats = replay.get_user_stats("user1")
        assert stats["total_experiences"] == 2
        assert stats["positive_count"] == 1
        assert stats["negative_count"] == 1

    def test_top_intents(self, replay):
        for i in range(5):
            replay.record_experience(
                user_id="user1", intent="chat", context="{}",
                action_taken="reply", result="ok",
            )
        replay.record_experience(
            user_id="user1", intent="schedule", context="{}",
            action_taken="calendar", result="ok",
        )
        top = replay.get_top_intents(k=5)
        assert top[0][0] == "chat"
        assert top[0][1] == 5

    def test_get_stats(self, replay):
        replay.record_experience(
            user_id="alice", intent="test", context="{}",
            action_taken="a", result="ok",
        )
        replay.record_experience(
            user_id="bob", intent="test", context="{}",
            action_taken="a", result="ok",
        )
        stats = replay.get_stats()
        assert stats["total_experiences"] == 2
        assert stats["total_users"] == 2


# ─── Experience Summarizer Tests ─────────────────────────────────────────────


class TestExperienceSummarizer:
    @pytest.fixture
    def setup(self):
        from nomad_mem.autonomy.experience_replay import ExperienceReplay
        from nomad_mem.core.experience_summarizer import ExperienceSummarizer
        db = tempfile.mktemp(suffix=".db")
        replay = ExperienceReplay(db_path=db)
        summarizer = ExperienceSummarizer(experience_replay=replay)
        yield replay, summarizer
        replay.close()
        summarizer = None
        if os.path.exists(db):
            os.remove(db)

    def test_user_summary_empty(self, setup):
        _, summarizer = setup
        summary = summarizer.generate_user_summary("nobody")
        assert summary.total_experiences == 0

    def test_user_summary_with_data(self, setup):
        replay, summarizer = setup
        replay.record_experience(
            user_id="user1", intent="chat", context="{}",
            action_taken="reply", result="ok",
            lesson_learned="be more concise",
        )
        replay.record_experience(
            user_id="user1", intent="schedule", context="{}",
            action_taken="calendar", result="ok",
        )
        summary = summarizer.generate_user_summary("user1")
        assert summary.total_experiences == 2
        assert summary.positive_rate == 1.0
        assert len(summary.top_intents) >= 1
        assert len(summary.suggestions) >= 1

    def test_system_summary(self, setup):
        replay, summarizer = setup
        replay.record_experience(
            user_id="user1", intent="test", context="{}",
            action_taken="a", result="ok",
        )
        replay.record_experience(
            user_id="user2", intent="test", context="{}",
            action_taken="a", result="ok",
        )
        summary = summarizer.generate_system_summary()
        assert summary.total_experiences == 2

    def test_failure_analysis_no_failures(self, setup):
        replay, summarizer = setup
        replay.record_experience(
            user_id="user1", intent="test", context="{}",
            action_taken="a", result="ok",
        )
        analysis = summarizer.generate_failure_analysis()
        assert analysis["total_failures"] == 0

    def test_failure_analysis_with_failures(self, setup):
        replay, summarizer = setup
        from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
        for i in range(3):
            replay.record_experience(
                user_id="user1", intent=f"fail_{i}", context="{}",
                action_taken="bad", result="error",
                exp_type=ExperienceType.FAILURE,
                outcome=ExperienceOutcome.NEGATIVE,
                lesson_learned=f"lesson {i}",
            )
        analysis = summarizer.generate_failure_analysis()
        assert analysis["total_failures"] == 3
        assert len(analysis["top_failure_intents"]) >= 1

    def test_suggestions_low_positive_rate(self, setup):
        replay, summarizer = setup
        from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
        for i in range(10):
            replay.record_experience(
                user_id="user1", intent=f"test_{i}", context="{}",
                action_taken="a", result="fail",
                exp_type=ExperienceType.FAILURE,
                outcome=ExperienceOutcome.NEGATIVE,
            )
        summary = summarizer.generate_user_summary("user1")
        assert any("较低" in s for s in summary.suggestions)

    def test_summarizer_without_replay(self):
        from nomad_mem.core.experience_summarizer import ExperienceSummarizer
        summarizer = ExperienceSummarizer()
        summary = summarizer.generate_user_summary("user1")
        assert summary.total_experiences == 0


# ─── Jarvis Integration Tests ────────────────────────────────────────────────


class TestJarvisExperienceIntegration:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_experience_replay_initialized(self, jarvis):
        assert jarvis.experience_replay is not None

    def test_experience_summarizer_initialized(self, jarvis):
        assert jarvis.experience_summarizer is not None

    def test_status_includes_experience(self, jarvis):
        status = jarvis.get_status()
        assert "experience_replay" in status["modules"]

    def test_record_experience_via_jarvis(self, jarvis):
        exp_id = jarvis.record_experience(
            user_id="user1",
            intent="schedule",
            action="calendar_tool",
            result="scheduled",
            outcome="positive",
            lesson="always confirm time",
            importance=0.8,
        )
        assert exp_id != ""

    def test_retrieve_experiences_via_jarvis(self, jarvis):
        jarvis.record_experience(
            user_id="user1", intent="schedule_meeting",
            action="calendar", result="ok",
        )
        results = jarvis.retrieve_experiences("schedule", k=5)
        assert len(results) >= 1

    def test_get_experience_summary_via_jarvis(self, jarvis):
        jarvis.record_experience(
            user_id="user1", intent="test",
            action="a", result="ok",
            lesson="test lesson",
        )
        summary = jarvis.get_experience_summary("user1")
        assert summary["total_experiences"] >= 1

    def test_get_failure_analysis_via_jarvis(self, jarvis):
        analysis = jarvis.get_failure_analysis()
        assert "total_failures" in analysis or "error" in analysis

    def test_get_experience_stats_via_jarvis(self, jarvis):
        jarvis.record_experience(
            user_id="user1", intent="test",
            action="a", result="ok",
        )
        stats = jarvis.get_experience_stats("user1")
        assert stats.get("total_experiences", 0) >= 1

    def test_extract_patterns_via_jarvis(self, jarvis):
        for i in range(3):
            jarvis.record_experience(
                user_id="user1", intent="chat",
                action="reply", result="ok",
            )
        patterns = jarvis.extract_experience_patterns()
        assert isinstance(patterns, list)

    def test_close_does_not_crash(self, jarvis):
        jarvis.close()
        assert jarvis.initialized is False


class TestJarvisFullWorkflowWithExperience:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_chat_record_retrieve_experience(self, jarvis):
        # Chat
        result = jarvis.chat("帮我安排一个会议", user_id="user1")
        assert "response" in result

        # Record experience
        exp_id = jarvis.record_experience(
            user_id="user1",
            intent="schedule_meeting",
            action="used calendar tool",
            result="meeting scheduled",
            lesson="always check availability first",
        )
        assert exp_id != ""

        # Retrieve experience
        exps = jarvis.retrieve_experiences("meeting", k=5)
        assert len(exps) >= 1
        assert "calendar" in exps[0]["action"]

    def test_experience_summary_after_interactions(self, jarvis):
        # Multiple interactions
        for i in range(5):
            jarvis.record_experience(
                user_id="user1",
                intent="chat",
                action="conversation",
                result="positive interaction",
                importance=0.5 + i * 0.1,
            )

        summary = jarvis.get_experience_summary("user1")
        assert summary["total_experiences"] >= 5
        assert summary["positive_rate"] == 1.0

    def test_failure_learning_workflow(self, jarvis):
        # Record failures
        for i in range(3):
            jarvis.record_experience(
                user_id="user1",
                intent=f"complex_task_{i}",
                action="attempted",
                result="failed - timeout",
                outcome="negative",
                lesson=f"need to handle timeout for task {i}",
                importance=0.9,
            )

        analysis = jarvis.get_failure_analysis()
        assert analysis["total_failures"] >= 3

        # Verify lessons are retrievable
        lessons = jarvis.experience_replay.retrieve_lessons(k=5)
        assert len(lessons) >= 3
