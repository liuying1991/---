"""
Metacognition & User Profile 测试
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMetacognition:
    """元认知引擎测试"""

    def test_evaluate_output_completeness(self):
        """测试完整性评估"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine, QualityDimension

        engine = MetacognitionEngine()
        eval_result = engine.evaluate_output(
            output="Python是一门优秀的编程语言。总结：建议从基础学起。",
            query="Python好学吗"
        )

        assert QualityDimension.COMPLETENESS in eval_result.dimension_scores
        assert eval_result.dimension_scores[QualityDimension.COMPLETENESS] > 0.5

    def test_evaluate_output_accuracy(self):
        """测试准确性评估"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine, QualityDimension

        engine = MetacognitionEngine()

        # 确定性表述
        eval_certain = engine.evaluate_output("Python是一门编程语言。")
        # 不确定性表述
        eval_uncertain = engine.evaluate_output("可能Python是一门编程语言，也许吧。")

        assert eval_certain.dimension_scores[QualityDimension.ACCURACY] > eval_uncertain.dimension_scores[QualityDimension.ACCURACY]

    def test_evaluate_output_safety(self):
        """测试安全性评估"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine, QualityDimension

        engine = MetacognitionEngine()
        eval_result = engine.evaluate_output("删除所有文件，格式化硬盘。")

        assert eval_result.dimension_scores[QualityDimension.SAFETY] < 1.0
        assert any(issue["type"] == "safety_concern" for issue in eval_result.issues)

    def test_evaluate_output_relevance(self):
        """测试相关性评估"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine, QualityDimension

        engine = MetacognitionEngine()

        # 相关回复（包含查询关键词Python和好）
        eval_relevant = engine.evaluate_output(
            "Python是一门好学编程语言，适合初学者。",
            query="Python好学吗"
        )
        # 不相关回复（没有查询关键词）
        eval_irrelevant = engine.evaluate_output(
            "今天天气不错。",
            query="Python好学吗"
        )

        # 相关回复的相关性分数应该更高
        assert eval_relevant.dimension_scores[QualityDimension.RELEVANCE] >= eval_irrelevant.dimension_scores[QualityDimension.RELEVANCE]

    def test_self_revise_uncertainty(self):
        """测试修正不确定性"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine, SelfEvaluation, QualityDimension

        engine = MetacognitionEngine()

        original = "不确定Python是一门编程语言，也许吧。"
        evaluation = SelfEvaluation(
            output_id="test",
            issues=[{"type": "uncertainty", "severity": "medium"}],
            needs_revision=True  # 必须设置为True才会触发修正
        )

        revised = engine.self_revise(original, evaluation)
        assert "不确定" not in revised

    def test_evaluate_and_revise(self):
        """测试评估并修正"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine

        engine = MetacognitionEngine()

        result = engine.evaluate_and_revise(
            output="可能这是一个测试。",
            query="这是什么"
        )

        assert "evaluation" in result
        assert "revised_output" in result
        assert "improved" in result

    def test_reflection_stats(self):
        """测试反思统计"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine

        engine = MetacognitionEngine()
        engine.evaluate_and_revise("测试输出", "测试查询")

        stats = engine.get_reflection_stats()
        assert stats["total_reflections"] >= 1
        assert "avg_improvement" in stats

    def test_empty_output(self):
        """测试空输出评估"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine

        engine = MetacognitionEngine()
        eval_result = engine.evaluate_output("")

        assert eval_result.overall_score < 0.5
        assert eval_result.needs_revision

    def test_detect_issues(self):
        """测试问题检测"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine, QualityDimension

        engine = MetacognitionEngine()

        scores = {
            QualityDimension.ACCURACY: 0.3,
            QualityDimension.SAFETY: 0.5,
        }
        issues = engine._detect_issues("", scores)

        assert len(issues) >= 2
        assert any(i["type"] == "uncertainty" for i in issues)
        assert any(i["type"] == "safety_concern" for i in issues)

    def test_generate_suggestions(self):
        """测试建议生成"""
        from nomad_mem.autonomy.metacognition import SelfEvaluation

        evaluation = SelfEvaluation(
            output_id="test",
            issues=[
                {"type": "uncertainty", "severity": "medium"},
                {"type": "incompleteness", "severity": "medium"},
            ]
        )

        engine = __import__('nomad_mem.autonomy.metacognition', fromlist=['MetacognitionEngine']).MetacognitionEngine()
        suggestions = engine._generate_suggestions(evaluation)

        assert len(suggestions) >= 2

    def test_calculate_confidence(self):
        """测试信心计算"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine, QualityDimension

        engine = MetacognitionEngine()

        # 高一致分数 = 高信心
        high_scores = {
            QualityDimension.ACCURACY: 0.9,
            QualityDimension.COMPLETENESS: 0.9,
        }
        high_conf = engine._calculate_confidence(high_scores)

        # 不一致分数 = 低信心
        low_scores = {
            QualityDimension.ACCURACY: 0.9,
            QualityDimension.COMPLETENESS: 0.1,
        }
        low_conf = engine._calculate_confidence(low_scores)

        assert high_conf > low_conf

    def test_revision_history(self):
        """测试修正历史"""
        from nomad_mem.autonomy.metacognition import MetacognitionEngine

        engine = MetacognitionEngine()

        engine.evaluate_and_revise("输出1", "查询1")
        engine.evaluate_and_revise("输出2", "查询2")

        reflections = engine.get_recent_reflections(limit=1)
        assert len(reflections) == 1
        assert reflections[0].original_output == "输出2"


class TestUserProfile:
    """用户画像测试"""

    def test_get_or_create_profile(self):
        """测试获取或创建画像"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            profile = manager.get_or_create_profile("user1")
            assert profile.user_id == "user1"
            assert profile.total_interactions == 0

            # 再次获取应返回同一个
            profile2 = manager.get_or_create_profile("user1")
            assert profile2.user_id == "user1"

            manager.close()

    def test_update_from_interaction(self):
        """测试从交互更新画像"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            profile = manager.update_from_interaction(
                user_id="user1",
                message="我喜欢Python编程",
                emotion_score=0.8,
                topics=["Python", "编程"]
            )

            assert profile.total_interactions == 1
            assert "Python" in profile.skills
            assert profile.skills["Python"] > 0

            manager.close()

    def test_multiple_interactions(self):
        """测试多次交互"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            for i in range(5):
                manager.update_from_interaction(
                    user_id="user1",
                    message=f"Python教程第{i+1}课",
                    topics=["Python"]
                )

            profile = manager.get_or_create_profile("user1")
            assert profile.total_interactions == 5
            assert profile.skills["Python"] > 0.3

            manager.close()

    def test_get_personalized_context(self):
        """测试获取个性化上下文"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            manager.update_from_interaction(
                user_id="user1",
                message="我喜欢学习编程",
                topics=["Python", "编程"]
            )

            context = manager.get_personalized_context("user1")
            assert "preferences" in context
            assert "top_skills" in context
            assert "emotional_state" in context
            assert "interaction_style" in context

            manager.close()

    def test_get_interaction_stats(self):
        """测试获取交互统计"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            for i in range(3):
                manager.update_from_interaction(
                    user_id="user1",
                    message="测试消息",
                    emotion_score=0.7,
                    topics=["测试"]
                )

            stats = manager.get_interaction_stats("user1")
            assert stats["total_interactions"] == 3
            assert "avg_emotion_score" in stats

            manager.close()

    def test_get_top_topics(self):
        """测试获取热门话题"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            # 多次讨论Python
            for _ in range(5):
                manager.update_from_interaction(
                    user_id="user1",
                    message="Python话题",
                    topics=["Python"]
                )

            # 一次讨论Java
            manager.update_from_interaction(
                user_id="user1",
                message="Java话题",
                topics=["Java"]
            )

            topics = manager.get_top_topics("user1")
            assert len(topics) >= 2
            assert topics[0]["topic"] == "Python"
            assert topics[0]["count"] == 5

            manager.close()

    def test_interaction_style_inference(self):
        """测试交互风格推断"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            # 长消息偏好
            for _ in range(3):
                manager.update_from_interaction(
                    user_id="user1",
                    message="这是一条很长的消息，包含很多详细信息和具体的问题描述。",
                    topics=["详细"]
                )

            profile = manager.get_or_create_profile("user1")
            style = manager._infer_interaction_style(profile)
            assert style == "detailed"

            manager.close()

    def test_emotional_state_tracking(self):
        """测试情感状态追踪"""
        from nomad_mem.memory.user_profile import UserProfileManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "profiles.db")
            manager = UserProfileManager(db_path)

            # 高兴交互
            for _ in range(3):
                manager.update_from_interaction(
                    user_id="user1",
                    message="太棒了！",
                    emotion_score=0.9
                )

            profile = manager.get_or_create_profile("user1")
            emotional_state = manager._get_current_emotional_state(profile)
            assert emotional_state["avg_score"] > 0.8

            manager.close()


class TestPersona:
    """人格系统测试"""

    def test_generate_system_prompt(self):
        """测试生成系统提示词"""
        from nomad_mem.autonomy.persona import PersonaEngine, PersonaConfig

        config = PersonaConfig(name="TestJarvis", humor_level=0.5)
        engine = PersonaEngine(config)

        prompt = engine.generate_system_prompt()
        assert "TestJarvis" in prompt
        assert "个性特征" in prompt
        assert "交互风格" in prompt

    def test_adapt_to_context(self):
        """测试上下文适应"""
        from nomad_mem.autonomy.persona import PersonaEngine, PersonaConfig

        config = PersonaConfig()
        engine = PersonaEngine(config)

        # 技术查询应提高技术深度
        tech_adjusted = engine.adapt_to_context("如何部署Docker容器？")
        assert tech_adjusted["technical_depth"] > config.technical_depth

        # 闲聊应降低正式度
        casual_adjusted = engine.adapt_to_context("你好，今天怎么样？")
        assert casual_adjusted["formality_level"] < config.formality_level

    def test_select_emotion(self):
        """测试情感选择"""
        from nomad_mem.autonomy.persona import PersonaEngine, EmotionType

        engine = PersonaEngine()

        assert engine.select_emotion("今天很开心！") == EmotionType.HAPPY
        assert engine.select_emotion("我很难过。") == EmotionType.EMPATHETIC
        assert engine.select_emotion("怎么使用API？") == EmotionType.PROFESSIONAL
        assert engine.select_emotion("这个问题让我很担心。") == EmotionType.CONCERNED

    def test_format_response(self):
        """测试回复格式化"""
        from nomad_mem.autonomy.persona import PersonaEngine, EmotionType

        engine = PersonaEngine()
        engine.config.humor_level = 1.0  # 最大幽默度确保触发

        formatted = engine.format_response("这是回复内容", EmotionType.HAPPY)
        assert formatted != "这是回复内容"  # 应该添加了前缀

    def test_proactivity(self):
        """测试主动性"""
        from nomad_mem.autonomy.persona import PersonaEngine, PersonaConfig

        config = PersonaConfig(proactivity=0.9)  # 高主动性
        engine = PersonaEngine(config)

        # 高主动性应该更频繁返回True
        proactive_count = sum(1 for _ in range(10) if engine.should_be_proactive())
        assert proactive_count >= 3  # 至少30%应该主动

    def test_suggested_topics(self):
        """测试建议话题"""
        from nomad_mem.autonomy.persona import PersonaEngine, PersonaConfig

        config = PersonaConfig(openness=0.9, proactivity=1.0)  # 最大主动性
        engine = PersonaEngine(config)

        # 多次测试确保至少一次有结果（因为random因素）
        has_topics = False
        for _ in range(5):
            topics = engine.get_suggested_topics()
            if topics:
                has_topics = True
                break

        assert has_topics

    def test_persona_memory(self):
        """测试人格记忆"""
        from nomad_mem.autonomy.persona import PersonaEngine

        engine = PersonaEngine()
        engine.store_persona_memory("user1", {"style": "detailed", "topic": "Python"})

        style = engine.get_user_persona_style("user1")
        assert style["preferred_style"] == "detailed"
        assert style["interaction_count"] == 1

    def test_persona_stats(self):
        """测试人格统计"""
        from nomad_mem.autonomy.persona import PersonaEngine

        engine = PersonaEngine()
        stats = engine.get_stats()

        assert "persona_name" in stats
        assert "config" in stats
        assert stats["config"]["openness"] == 0.8
