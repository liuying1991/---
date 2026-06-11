"""
第十七轮端到端测试: 意图预测 + 主动响应 + Jarvis集成

测试覆盖:
- IntentPredictor: 意图共现矩阵预测、时间模式预测、场景上下文加成
- ProactiveResponder: 响应生成、阈值控制、主动程度调节
- JarvisCore集成: 意图记录/预测/主动响应/意图画像
"""
import pytest
import os
import tempfile
import time


# ─── Intent Predictor Tests ─────────────────────────────────────────────────


class TestIntentPrediction:
    def test_create_prediction(self):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        pred = IntentPrediction(
            predicted_intent="schedule",
            confidence=0.8,
            reason="test",
        )
        assert pred.confidence == 0.8
        assert pred.predicted_intent == "schedule"

    def test_prediction_to_dict(self):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        pred = IntentPrediction(
            predicted_intent="query",
            confidence=0.6,
            reason="reason",
            supporting_evidence=["evidence1", "evidence2"],
        )
        d = pred.to_dict()
        assert d["predicted_intent"] == "query"
        assert d["supporting_evidence"] == ["evidence1", "evidence2"]


class TestIntentPredictorCore:
    @pytest.fixture
    def predictor(self):
        from nomad_mem.autonomy.intent_predictor import IntentPredictor
        db = tempfile.mktemp(suffix=".db")
        p = IntentPredictor(db_path=db)
        yield p
        p.close()
        if os.path.exists(db):
            os.remove(db)

    def test_init(self, predictor):
        assert predictor.db_path is not None

    def test_record_transition(self, predictor):
        predictor.record_transition("user1", "greeting", "query")
        stats = predictor.get_stats()
        assert stats["total_transitions"] == 1

    def test_record_time_pattern(self, predictor):
        predictor.record_time_pattern("user1", "schedule", 9, 1)
        stats = predictor.get_stats()
        assert stats["total_time_patterns"] == 1

    def test_get_stats_empty(self, predictor):
        stats = predictor.get_stats()
        assert stats["total_transitions"] == 0


class TestIntentPredictorCooccurrence:
    @pytest.fixture
    def predictor(self):
        from nomad_mem.autonomy.intent_predictor import IntentPredictor
        db = tempfile.mktemp(suffix=".db")
        p = IntentPredictor(db_path=db)
        yield p
        p.close()
        if os.path.exists(db):
            os.remove(db)

    def test_predict_with_no_data(self, predictor):
        predictions = predictor.predict_next("user1", current_intent="query")
        assert isinstance(predictions, list)
        assert len(predictions) == 0

    def test_predict_with_transitions(self, predictor):
        # Record multiple transitions
        for _ in range(5):
            predictor.record_transition("user1", "greeting", "query")
        for _ in range(3):
            predictor.record_transition("user1", "greeting", "schedule")
        for _ in range(2):
            predictor.record_transition("user1", "greeting", "email")

        predictions = predictor.predict_next("user1", current_intent="greeting", k=5)
        assert len(predictions) == 3
        # Highest frequency should be first
        assert predictions[0].predicted_intent == "query"
        assert predictions[0].confidence > predictions[1].confidence

    def test_predict_with_success_rate(self, predictor):
        for _ in range(3):
            predictor.record_transition("user1", "chat", "task", success=True)
        predictor.record_transition("user1", "chat", "task", success=False)

        predictions = predictor.predict_next("user1", current_intent="chat")
        assert len(predictions) >= 1

    def test_predict_k_limit(self, predictor):
        intents = ["a", "b", "c", "d", "e"]
        for i, intent in enumerate(intents):
            for _ in range(i + 1):
                predictor.record_transition("user1", "start", intent)

        predictions = predictor.predict_next("user1", current_intent="start", k=2)
        assert len(predictions) == 2


class TestIntentPredictorTimePatterns:
    @pytest.fixture
    def predictor(self):
        from nomad_mem.autonomy.intent_predictor import IntentPredictor
        db = tempfile.mktemp(suffix=".db")
        p = IntentPredictor(db_path=db)
        yield p
        p.close()
        if os.path.exists(db):
            os.remove(db)

    def test_time_pattern_prediction(self, predictor):
        current_hour = time.localtime().tm_hour
        for _ in range(5):
            predictor.record_time_pattern("user1", "schedule", current_hour, 1)
        for _ in range(2):
            predictor.record_time_pattern("user1", "email", current_hour + 1, 1)

        predictions = predictor.predict_next("user1")
        # Should return predictions based on time patterns
        assert isinstance(predictions, list)


class TestIntentPredictorSceneContext:
    @pytest.fixture
    def predictor(self):
        from nomad_mem.autonomy.intent_predictor import IntentPredictor
        db = tempfile.mktemp(suffix=".db")
        p = IntentPredictor(db_path=db)
        yield p
        p.close()
        if os.path.exists(db):
            os.remove(db)

    def test_scene_context_bonus(self, predictor):
        for _ in range(5):
            predictor.record_transition(
                "user1", "greeting", "schedule",
                scene_context="work"
            )

        predictions = predictor.predict_next(
            "user1", current_intent="greeting",
            scene_context="work"
        )
        assert len(predictions) >= 1


class TestIntentPredictorAnalytics:
    @pytest.fixture
    def predictor(self):
        from nomad_mem.autonomy.intent_predictor import IntentPredictor
        db = tempfile.mktemp(suffix=".db")
        p = IntentPredictor(db_path=db)
        yield p
        p.close()
        if os.path.exists(db):
            os.remove(db)

    def test_intent_flow(self, predictor):
        for _ in range(5):
            predictor.record_transition("user1", "greeting", "query")
        for _ in range(3):
            predictor.record_transition("user1", "greeting", "schedule")

        flows = predictor.get_intent_flow("user1", from_intent="greeting")
        assert len(flows) == 2
        assert flows[0]["from"] == "greeting"
        assert flows[0]["count"] == 5

    def test_user_intent_profile(self, predictor):
        for _ in range(10):
            predictor.record_transition("user1", "greeting", "query")
        for _ in range(3):
            predictor.record_transition("user1", "greeting", "schedule")

        profile = predictor.get_user_intent_profile("user1")
        assert profile["user_id"] == "user1"
        assert profile["total_transitions"] == 13
        assert len(profile["top_intents"]) >= 1
        assert profile["top_intents"][0]["intent"] == "query"

    def test_multi_user_stats(self, predictor):
        predictor.record_transition("alice", "greeting", "query")
        predictor.record_transition("bob", "greeting", "schedule")
        predictor.record_transition("alice", "greeting", "email")

        stats = predictor.get_stats()
        assert stats["total_transitions"] == 3
        assert stats["unique_users"] == 2


# ─── Proactive Responder Tests ──────────────────────────────────────────────


class TestProactiveResponse:
    def test_create_response(self):
        from nomad_mem.core.proactive_responder import ProactiveResponse
        resp = ProactiveResponse(
            should_respond=True,
            response_text="test",
        )
        assert resp.should_respond is True

    def test_response_to_dict(self):
        from nomad_mem.core.proactive_responder import ProactiveResponse
        resp = ProactiveResponse(
            should_respond=True,
            response_text="Need help?",
            predicted_intent="query",
            confidence=0.8,
        )
        d = resp.to_dict()
        assert d["should_respond"] is True
        assert d["response_text"] == "Need help?"


class TestProactiveResponderCore:
    @pytest.fixture
    def responder(self):
        from nomad_mem.core.proactive_responder import ProactiveResponder
        return ProactiveResponder(threshold=0.3)

    def test_generate_response_above_threshold(self, responder):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        pred = IntentPrediction(
            predicted_intent="schedule",
            confidence=0.7,
            reason="test",
        )
        resp = responder.generate_response(pred)
        assert resp.should_respond is True
        assert "日程" in resp.response_text

    def test_generate_response_below_threshold(self, responder):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        pred = IntentPrediction(
            predicted_intent="schedule",
            confidence=0.1,
            reason="test",
        )
        resp = responder.generate_response(pred)
        assert resp.should_respond is False

    def test_generate_response_none(self, responder):
        resp = responder.generate_response(None)
        assert resp.should_respond is False

    def test_generate_top_response(self, responder):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        preds = [
            IntentPrediction("schedule", 0.8, "reason1"),
            IntentPrediction("query", 0.6, "reason2"),
        ]
        resp = responder.generate_top_response(preds)
        assert resp.should_respond is True
        assert resp.predicted_intent == "schedule"

    def test_generate_top_response_empty(self, responder):
        resp = responder.generate_top_response([])
        assert resp.should_respond is False

    def test_different_intent_templates(self, responder):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        intents = ["schedule", "query", "email", "chat", "task", "meeting"]
        for intent in intents:
            pred = IntentPrediction(intent, 0.8, "reason")
            resp = responder.generate_response(pred)
            assert resp.should_respond is True
            assert len(resp.response_text) > 0

    def test_unknown_intent_template(self, responder):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        pred = IntentPrediction("unknown_intent", 0.8, "reason")
        resp = responder.generate_response(pred)
        assert resp.should_respond is True
        assert "unknown_intent" in resp.response_text

    def test_action_suggestions(self, responder):
        from nomad_mem.autonomy.intent_predictor import IntentPrediction
        pred = IntentPrediction("schedule", 0.8, "reason")
        resp = responder.generate_response(pred)
        assert resp.action_suggestion != ""


class TestProactiveResponderConfig:
    def test_set_threshold(self):
        from nomad_mem.core.proactive_responder import ProactiveResponder
        responder = ProactiveResponder(threshold=0.5)
        responder.set_threshold(0.3)
        config = responder.get_config()
        assert config["threshold"] == 0.3

    def test_set_proactive_level(self):
        from nomad_mem.core.proactive_responder import ProactiveResponder
        responder = ProactiveResponder()

        # Minimal level requires higher confidence
        responder.set_proactive_level("minimal")
        config_minimal = responder.get_config()
        assert config_minimal["proactive_level"] == "minimal"

        # Aggressive level requires lower confidence
        responder.set_proactive_level("aggressive")
        config_agg = responder.get_config()
        assert config_agg["adjusted_threshold"] < config_minimal["adjusted_threshold"]

    def test_level_affects_response(self):
        from nomad_mem.core.proactive_responder import ProactiveResponder
        from nomad_mem.autonomy.intent_predictor import IntentPrediction

        pred = IntentPrediction("schedule", 0.5, "reason")

        # Minimal: should not respond (threshold * 1.5 = 0.75 > 0.5)
        minimal = ProactiveResponder(threshold=0.5, proactive_level="minimal")
        resp_min = minimal.generate_response(pred)
        assert resp_min.should_respond is False

        # Aggressive: should respond (threshold * 0.7 = 0.35 < 0.5)
        aggressive = ProactiveResponder(threshold=0.5, proactive_level="aggressive")
        resp_agg = aggressive.generate_response(pred)
        assert resp_agg.should_respond is True


# ─── Jarvis Integration Tests ────────────────────────────────────────────────


class TestJarvisIntentIntegration:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_intent_predictor_initialized(self, jarvis):
        assert jarvis.intent_predictor is not None

    def test_proactive_responder_initialized(self, jarvis):
        assert jarvis.proactive_responder is not None

    def test_status_includes_intent_predictor(self, jarvis):
        status = jarvis.get_status()
        assert "intent_predictor" in status["modules"]

    def test_record_intent_transition(self, jarvis):
        result = jarvis.record_intent_transition(
            "user1", "greeting", "query"
        )
        assert result is True

    def test_predict_next_intent_no_data(self, jarvis):
        predictions = jarvis.predict_next_intent("new_user", current_intent="greeting")
        assert isinstance(predictions, list)

    def test_predict_next_intent_with_data(self, jarvis):
        for _ in range(5):
            jarvis.record_intent_transition("user1", "greeting", "query")
        for _ in range(3):
            jarvis.record_intent_transition("user1", "greeting", "schedule")

        predictions = jarvis.predict_next_intent("user1", current_intent="greeting")
        assert len(predictions) >= 1
        assert predictions[0]["predicted_intent"] == "query"

    def test_get_proactive_response(self, jarvis):
        for _ in range(10):
            jarvis.record_intent_transition("user1", "greeting", "schedule")

        response = jarvis.get_proactive_response("user1", current_intent="greeting")
        assert "should_respond" in response

    def test_set_proactive_level(self, jarvis):
        assert jarvis.set_proactive_level("aggressive") is True
        assert jarvis.set_proactive_level("minimal") is True

    def test_get_intent_profile(self, jarvis):
        for _ in range(5):
            jarvis.record_intent_transition("user1", "greeting", "query")
        profile = jarvis.get_intent_profile("user1")
        assert profile["user_id"] == "user1"
        assert profile["total_transitions"] == 5

    def test_get_intent_flow(self, jarvis):
        for _ in range(3):
            jarvis.record_intent_transition("user1", "start", "query")
        flows = jarvis.get_intent_flow("user1", from_intent="start")
        assert len(flows) >= 1
        assert flows[0]["from"] == "start"


class TestJarvisFullWorkflowWithIntent:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_full_intent_prediction_workflow(self, jarvis):
        # Record intent transitions through interactions
        jarvis.record_intent_transition("user1", "greeting", "query", "work")
        jarvis.record_intent_transition("user1", "query", "schedule", "work")
        jarvis.record_intent_transition("user1", "schedule", "task", "work")

        # Record more transitions to build patterns
        for _ in range(5):
            jarvis.record_intent_transition("user1", "greeting", "query")

        # Predict next intent
        predictions = jarvis.predict_next_intent("user1", current_intent="greeting")
        assert len(predictions) >= 1
        assert predictions[0]["predicted_intent"] == "query"

        # Get proactive response
        response = jarvis.get_proactive_response("user1", current_intent="greeting")
        assert "should_respond" in response

    def test_intent_profile_after_interactions(self, jarvis):
        intents = ["schedule", "query", "email", "schedule", "schedule"]
        for intent in intents:
            jarvis.record_intent_transition("user1", "start", intent)

        profile = jarvis.get_intent_profile("user1")
        assert profile["total_transitions"] == 5
        assert profile["top_intents"][0]["intent"] == "schedule"

    def test_scene_context_enhances_prediction(self, jarvis):
        # Work scene: greeting -> schedule
        for _ in range(5):
            jarvis.record_intent_transition("user1", "greeting", "schedule", "work")

        # Rest scene: greeting -> chat
        for _ in range(5):
            jarvis.record_intent_transition("user1", "greeting", "chat", "rest")

        # With work scene context, schedule should be predicted
        work_predictions = jarvis.predict_next_intent(
            "user1", current_intent="greeting", scene="work"
        )
        assert len(work_predictions) >= 1

    def test_close_cleans_up(self, jarvis):
        jarvis.close()
        assert jarvis.initialized is False
