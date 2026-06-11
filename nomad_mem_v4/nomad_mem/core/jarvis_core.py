"""
Jarvis Core V2 - 贾维斯核心集成层（升级版）

整合所有模块的统一入口:
1. 记忆系统 (MemoryOS + 进化 + 压缩 + 知识图谱)
2. 自主意识 (Driver + 元认知 + 人格)
3. 意图理解 (Intent Engine)
4. 任务规划 (Task Planner)
5. 技能编排 (Skill Orchestrator)
6. 对话管理 (Dialog Manager)
7. 用户画像 (User Profile)
8. 知识图谱 (Knowledge Graph) - 新增
9. 插件系统 (Plugin System) - 新增
10. API网关 (API Gateway) - 新增
11. 安全层 (Safety Layer) - 新增
12. 语音接口 (Voice Interface) - 已有
13. 长期学习 (Long Term Learning) - 已有
14. 主动提醒 (Proactive Alert) - 已有

核心职责:
- 统一初始化所有模块
- 提供统一的用户交互接口
- 协调模块之间的数据流
- 管理全局状态和生命周期
"""
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class JarvisCore:
    """贾维斯核心"""

    def __init__(self, config: Dict = None):
        """
        初始化贾维斯核心

        Args:
            config: 全局配置
        """
        self.config = config or {}
        self.initialized = False

        # 核心模块
        self.memory_os = None
        self.memory_evolution = None
        self.context_compressor = None
        self.intent_engine = None
        self.task_planner = None
        self.skill_orchestrator = None
        self.metacognition = None
        self.persona_engine = None
        self.user_profile = None
        self.autonomy_driver = None
        self.dialog_manager = None
        self.memory_bridge_v2 = None
        self.voice_interface = None
        self.long_term_learning = None
        self.proactive_alert = None

        # 新增模块（第九轮）
        self.knowledge_graph = None
        self.plugin_system = None
        self.api_gateway = None
        self.safety_layer = None

        # 新增模块（第十轮）
        self.context_awareness = None
        self.behavior_predictor = None
        self.session_manager = None

        # 新增模块（第十一轮）
        self.self_evolution = None

        # 新增模块（第十二轮）
        self.tool_registry = None
        self.tool_executor = None
        self.tool_selector = None

        # 新增模块（第十三轮）
        self.dialog_flow = None
        self.presentation_engine = None
        self.emotion_tracker = None

        # 新增模块（第十四轮）
        self.autonomous_engine = None

        # 新增模块（第十五轮）
        self.scene_manager = None
        self.scene_automation = None
        self.data_analyzer = None

        # 新增模块（第十六轮）
        self.experience_replay = None
        self.experience_summarizer = None

        # 新增模块（第十七轮）
        self.intent_predictor = None
        self.proactive_responder = None

        # 新增模块（第十八轮）
        self.safety_engine = None
        self.safety_monitor = None

        # 新增模块（第十九轮）
        self.skill_discoverer = None
        self.skill_evolution = None

        # 新增模块（第二十轮）
        self.goal_manager = None
        self.goal_planner = None

    def initialize(self):
        """初始化所有模块"""
        import tempfile
        import os

        tmpdir = tempfile.mkdtemp()

        # 1. 初始化记忆系统
        try:
            from nomad_mem.memory.memory_os import MemoryOS
            from nomad_mem.memory.memory_evolution import MemoryEvolution
            from nomad_mem.memory.context_compressor import ContextCompressor

            self.memory_os = MemoryOS(os.path.join(tmpdir, "memory_os.db"))
            self.memory_evolution = MemoryEvolution(os.path.join(tmpdir, "memory_evolution.db"))
            self.context_compressor = ContextCompressor(self.config.get("compressor", {}))
        except ImportError:
            pass

        # 2. 初始化意图引擎
        try:
            from nomad_mem.autonomy.intent_engine import IntentEngine
            self.intent_engine = IntentEngine(self.config.get("intent", {}))
        except ImportError:
            pass

        # 3. 初始化任务规划器
        try:
            from nomad_mem.autonomy.task_planner import TaskPlanner
            self.task_planner = TaskPlanner(self.config.get("planner", {}))
        except ImportError:
            pass

        # 4. 初始化元认知引擎
        try:
            from nomad_mem.autonomy.metacognition import MetacognitionEngine
            self.metacognition = MetacognitionEngine(self.config.get("metacognition", {}))
        except ImportError:
            pass

        # 5. 初始化人格引擎
        try:
            from nomad_mem.autonomy.persona import PersonaEngine, PersonaConfig
            persona_config_data = self.config.get("persona", {})
            persona_config = PersonaConfig(**persona_config_data) if persona_config_data else PersonaConfig()
            self.persona_engine = PersonaEngine(persona_config)
        except ImportError:
            pass

        # 6. 初始化用户画像
        try:
            from nomad_mem.memory.user_profile import UserProfileManager
            self.user_profile = UserProfileManager(os.path.join(tmpdir, "user_profiles.db"))
        except ImportError:
            pass

        # 7. 初始化记忆桥接器 V2
        try:
            from nomad_mem.memory_bridge import MemoryBridgeV2
            self.memory_bridge_v2 = MemoryBridgeV2(
                memory_os=self.memory_os,
                memory_evolution=self.memory_evolution,
                context_compressor=self.context_compressor,
                config=self.config.get("bridge", {})
            )
        except ImportError:
            pass

        # 8. 初始化知识图谱
        try:
            from nomad_mem.memory.knowledge_graph import KnowledgeGraph
            self.knowledge_graph = KnowledgeGraph(
                db_path=os.path.join(tmpdir, "knowledge_graph.db")
            )
        except ImportError:
            pass

        # 9. 初始化插件系统
        try:
            from nomad_mem.plugins.plugin_system import PluginSystem
            self.plugin_system = PluginSystem()
        except ImportError:
            pass

        # 10. 初始化API网关
        try:
            from nomad_mem.web.api_gateway import APIGateway
            gateway_config = self.config.get("api_gateway", {})
            gateway_config.setdefault("auth_db", os.path.join(tmpdir, "api_keys.db"))
            self.api_gateway = APIGateway(config=gateway_config)
        except ImportError:
            pass

        # 11. 初始化安全层
        try:
            from nomad_mem.core.safety_layer import SafetyLayer
            self.safety_layer = SafetyLayer(
                data_dir=os.path.join(tmpdir, "safety")
            )
        except ImportError:
            pass

        # 12. 初始化情境感知
        try:
            from nomad_mem.autonomy.context_awareness import ContextAwarenessEngine
            self.context_awareness = ContextAwarenessEngine(
                data_dir=os.path.join(tmpdir, "context")
            )
        except ImportError:
            pass

        # 13. 初始化行为预测
        try:
            from nomad_mem.autonomy.behavior_predictor import BehaviorPredictor
            self.behavior_predictor = BehaviorPredictor(
                db_path=os.path.join(tmpdir, "behavior_patterns.db")
            )
        except ImportError:
            pass

        # 14. 初始化会话管理
        try:
            from nomad_mem.autonomy.session_manager import SessionManager
            self.session_manager = SessionManager(
                db_path=os.path.join(tmpdir, "sessions.db")
            )
        except ImportError:
            pass

        # 15. 初始化自我进化引擎
        try:
            from nomad_mem.autonomy.self_evolution import SelfEvolutionEngine
            self.self_evolution = SelfEvolutionEngine(
                data_dir=os.path.join(tmpdir, "evolution"),
                knowledge_graph=self.knowledge_graph,
            )
        except ImportError:
            pass

        # 16. 初始化工具系统
        try:
            from nomad_mem.skills.tool_registry import ToolRegistry
            from nomad_mem.skills.tool_executor import ToolExecutor
            from nomad_mem.autonomy.tool_selector import ToolSelector
            from nomad_mem.skills.builtin_tools import register_builtin_tools

            self.tool_registry = ToolRegistry()
            register_builtin_tools(self.tool_registry)
            self.tool_executor = ToolExecutor()
            self.tool_selector = ToolSelector(self.tool_registry)
        except ImportError:
            pass

        # 17. 初始化对话流/展示/情绪模块
        try:
            from nomad_mem.autonomy.dialog_flow import DialogFlowManager
            from nomad_mem.core.presentation_engine import PresentationEngine
            from nomad_mem.autonomy.emotion_tracker import EmotionTracker

            self.dialog_flow = DialogFlowManager(
                db_path=os.path.join(tmpdir, "dialog_flow.db")
            )
            self.presentation_engine = PresentationEngine()
            self.emotion_tracker = EmotionTracker(
                db_path=os.path.join(tmpdir, "emotion_tracker.db")
            )
        except ImportError:
            pass

        # 18. 初始化自主运行系统
        try:
            from nomad_mem.autonomy.autonomous_engine import AutonomousEngine
            self.autonomous_engine = AutonomousEngine(
                data_dir=os.path.join(tmpdir, "autonomous")
            )
        except ImportError:
            pass

        # 19. 初始化场景系统+场景自动化+数据分析
        try:
            from nomad_mem.autonomy.scene_manager import SceneManager
            from nomad_mem.automation.scene_automation import SceneAutomation
            from nomad_mem.core.data_analyzer import DataAnalyzer

            self.scene_manager = SceneManager(
                db_path=os.path.join(tmpdir, "scenes.db")
            )
            self.scene_automation = SceneAutomation(
                scene_manager=self.scene_manager
            )
            self.data_analyzer = DataAnalyzer()
        except ImportError:
            pass

        # 20. 初始化经验回放+摘要
        try:
            from nomad_mem.autonomy.experience_replay import ExperienceReplay
            from nomad_mem.core.experience_summarizer import ExperienceSummarizer

            self.experience_replay = ExperienceReplay(
                db_path=os.path.join(tmpdir, "experiences.db")
            )
            self.experience_summarizer = ExperienceSummarizer(
                experience_replay=self.experience_replay
            )
        except ImportError:
            pass

        # 21. 初始化意图预测+主动响应
        try:
            from nomad_mem.autonomy.intent_predictor import IntentPredictor
            from nomad_mem.core.proactive_responder import ProactiveResponder

            self.intent_predictor = IntentPredictor(
                db_path=os.path.join(tmpdir, "intent_predictor.db")
            )
            self.proactive_responder = ProactiveResponder()
        except ImportError:
            pass

        # 22. 初始化自主安全系统
        try:
            from nomad_mem.core.safety_engine import SafetyEngine
            from nomad_mem.autonomy.safety_monitor import SafetyMonitor

            self.safety_engine = SafetyEngine(
                db_path=os.path.join(tmpdir, "safety_engine.db")
            )
            self.safety_monitor = SafetyMonitor(
                db_path=os.path.join(tmpdir, "safety_monitor.db")
            )
        except ImportError:
            pass

        # 23. 初始化技能自发现+自进化
        try:
            from nomad_mem.skills.skill_discovery import SkillDiscoverer
            from nomad_mem.skills.skill_evolution import SkillEvolutionManager

            self.skill_discoverer = SkillDiscoverer(
                db_path=os.path.join(tmpdir, "skill_discovery.db")
            )
            self.skill_evolution = SkillEvolutionManager(
                db_path=os.path.join(tmpdir, "skill_evolution.db")
            )
        except ImportError:
            pass

        # 24. 初始化自主目标管理+目标规划
        try:
            from nomad_mem.autonomy.goal_manager import GoalManager
            from nomad_mem.autonomy.goal_planner import GoalPlanner

            self.goal_manager = GoalManager(
                db_path=os.path.join(tmpdir, "goal_manager.db")
            )
            self.goal_planner = GoalPlanner(
                goal_manager=self.goal_manager,
                experience_replay=self.experience_replay,
                scene_manager=self.scene_manager,
                skill_evolution=self.skill_evolution,
            )
        except ImportError:
            pass

        self.initialized = True

    def chat(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        统一聊天接口

        Args:
            message: 用户消息
            user_id: 用户ID

        Returns:
            包含回复、意图、记忆等信息的字典
        """
        start_time = time.time()
        response = {
            "message": message,
            "user_id": user_id,
            "response": "",
            "intent": None,
            "memories_used": 0,
            "persona_applied": False,
            "processing_time": 0.0,
        }

        if not self.initialized:
            self.initialize()

        try:
            # 0. 安全检查（输入）
            if self.safety_layer:
                safety_result = self.safety_layer.check_input_safety(user_id, message)
                if not safety_result.passed:
                    return {
                        "message": message,
                        "user_id": user_id,
                        "response": "您的输入内容不符合安全规范，请重新输入。",
                        "safety_blocked": True,
                        "safety_reasons": safety_result.reasons,
                        "processing_time": time.time() - start_time,
                    }
                response["safety_level"] = safety_result.level.value

            # 0.5 情境感知
            if self.context_awareness:
                context = self.context_awareness.get_current_context(user_id)
                response["context"] = {
                    "time_of_day": context.time_of_day.value,
                    "day_type": context.day_type.value,
                    "activity_state": context.activity_state.value,
                }
                # 记录交互到习惯追踪器
                self.context_awareness.log_interaction(user_id, "chat", message[:50])

            # 1. 意图识别
            if self.intent_engine:
                context = {}
                if self.intent_engine:
                    recent = self.intent_engine.get_intent_context(user_id)
                    if recent:
                        context["recent_intents"] = recent

                intent = self.intent_engine.recognize_intent(message, context=context, user_id=user_id)
                response["intent"] = {
                    "category": intent.category.value,
                    "confidence": intent.confidence,
                    "entities": intent.entities,
                }

            # 1.5 工具选择（根据意图匹配工具）
            if self.tool_selector and self.tool_executor:
                intent_category = intent.category.value if intent and hasattr(intent, 'category') else "chat"
                tool_matches = self.tool_selector.select_tools(intent_category, message)
                if tool_matches:
                    top_tool = tool_matches[0]
                    if top_tool.score > 0.3:
                        response["suggested_tool"] = {
                            "tool_id": top_tool.tool_id,
                            "score": top_tool.score,
                            "reason": top_tool.reason,
                        }

            # 1.6 情绪检测（检测用户情绪并记录）
            if self.emotion_tracker:
                detected_emotion = self.emotion_tracker.detect_emotion(message)
                intensity = 0.5
                if detected_emotion:
                    self.emotion_tracker.record_emotion(
                        user_id=user_id,
                        emotion=detected_emotion,
                        intensity=intensity,
                        trigger=message[:100],
                    )
                    response["detected_emotion"] = detected_emotion.value

                    # 获取情感回应策略
                    strategy = self.emotion_tracker.get_emotional_response_strategy(detected_emotion)
                    response["emotion_strategy"] = strategy

                    # 获取情绪趋势
                    trend = self.emotion_tracker.get_emotional_trend(user_id, hours=24)
                    dominant = trend.dominant_emotion
                    direction = trend.trend_direction
                    response["emotional_trend"] = {
                        "dominant_emotion": dominant.value if hasattr(dominant, 'value') else (dominant or "neutral"),
                        "trend_direction": direction.value if hasattr(direction, 'value') else (direction or "stable"),
                    }

            # 2. 获取用户画像上下文
            user_context = {}
            if self.user_profile:
                user_context = self.user_profile.get_personalized_context(user_id)

                # 更新用户画像
                self.user_profile.update_from_interaction(
                    user_id=user_id,
                    message=message,
                )

            # 3. 检索相关记忆
            memories = []
            if self.memory_bridge_v2:
                memories = self.memory_bridge_v2.relevant_memories(message, k=5)
                response["memories_used"] = len(memories)

            # 4. 人格适应
            if self.persona_engine:
                user_emotion = user_context.get("emotional_state", {}).get("avg_score", 0.5)
                self.persona_engine.adapt_to_context(message, user_emotion)
                response["persona_applied"] = True

            # 5. 生成回复（模拟）
            reply = self._generate_reply(message, intent, memories, user_context)

            # 6. 元认知评估
            if self.metacognition:
                evaluation = self.metacognition.evaluate_output(reply, message)
                response["quality_score"] = evaluation.overall_score
                response["confidence"] = evaluation.confidence

                if evaluation.needs_revision:
                    revised = self.metacognition.self_revise(reply, evaluation)
                    reply = revised
                    response["revised"] = True

            # 7. 知识图谱语义增强
            kg_enrichment = []
            if self.knowledge_graph:
                # 从消息中提取关键词并在知识图谱中查找
                keywords = [w for w in message.split() if len(w) > 2]
                for keyword in keywords[:3]:
                    entities = self.knowledge_graph.search_entities(keyword)
                    if entities:
                        entities = entities[:1]
                        kg_enrichment.append({
                            "keyword": keyword,
                            "entity": entities[0].name,
                            "entity_type": entities[0].entity_type.value,
                        })
                response["kg_enrichment"] = kg_enrichment

            # 8. 格式化回复（人格化）
            if self.persona_engine:
                emotion = self.persona_engine.select_emotion(message)
                reply = self.persona_engine.format_response(reply, emotion)

            # 9. 安全检查（输出）
            if self.safety_layer:
                output_safety = self.safety_layer.check_output_safety(reply)
                if not output_safety.passed:
                    reply = "抱歉，我无法回复该问题。"
                    response["output_safety_blocked"] = True
                response["output_safety_level"] = output_safety.level.value

            response["response"] = reply

            # 10. 存储到记忆
            if self.memory_bridge_v2:
                self.memory_bridge_v2.store_conversation(message, reply, user_id)

            # 11. 更新用户画像
            if self.user_profile:
                self.user_profile.update_from_interaction(
                    user_id=user_id,
                    message=message,
                )

            # 12. 会话管理（记录对话轮次）
            if self.session_manager:
                # 尝试找到用户活跃会话，否则创建新会话
                active_sessions = self.session_manager.get_active_sessions(user_id)
                session_id = active_sessions[0].session_id if active_sessions else None
                if not session_id:
                    session_id = self.session_manager.create_session(user_id)

                intent_category = intent.category.value if intent and hasattr(intent, 'category') else "chat"
                # Convert intent string to DialogAct enum for session_manager
                try:
                    from nomad_mem.autonomy.session_manager import DialogAct
                    dialog_act = DialogAct(intent_category.upper())
                except (ValueError, ImportError):
                    dialog_act = DialogAct.INFORM
                self.session_manager.add_turn(
                    session_id=session_id,
                    user_utterance=message,
                    dialog_act=dialog_act,
                )
                response["session_id"] = session_id

            # 13. 行为预测（预测下一步需求）
            if self.behavior_predictor:
                intent_str = intent.category.value if intent and hasattr(intent, 'category') else "chat"
                import json as _json
                self.behavior_predictor.record_behavior(
                    user_id=user_id,
                    action=intent_str,
                    context=_json.dumps({"message_length": len(message)}),
                )
                predictions = self.behavior_predictor.predict_next_action(
                    user_id=user_id,
                    current_context={"action": intent_str},
                )
                if predictions:
                    response["predicted_needs"] = [
                        {"action": p.predicted_action, "confidence": p.confidence}
                        for p in predictions[:3]
                    ]

        except Exception as e:
            response["response"] = f"抱歉，处理您的请求时出现问题：{str(e)}"
            response["error"] = str(e)

        response["processing_time"] = time.time() - start_time
        return response

    def execute_task(self, task_description: str, complexity: int = 3, user_id: str = "default") -> Dict[str, Any]:
        """
        执行任务接口

        Args:
            task_description: 任务描述
            complexity: 复杂度(1-5)
            user_id: 用户ID

        Returns:
            任务执行结果
        """
        if not self.initialized:
            self.initialize()

        result = {
            "task": task_description,
            "status": "pending",
            "plan_id": None,
        }

        try:
            # 1. 任务分解
            if self.task_planner:
                plan_id = self.task_planner.decompose_task(task_description, complexity)
                result["plan_id"] = plan_id

                # 2. 执行计划
                execution_result = self.task_planner.get_plan_summary(plan_id)
                result["plan"] = execution_result
                result["status"] = "planned"
            else:
                result["status"] = "failed"
                result["error"] = "Task planner not available"

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "initialized": self.initialized,
            "modules": {},
        }

        if self.memory_os:
            status["modules"]["memory_os"] = self.memory_os.get_stats()

        if self.memory_evolution:
            status["modules"]["evolution"] = self.memory_evolution.get_stats()

        if self.intent_engine:
            status["modules"]["intent_engine"] = {"status": "ready"}

        if self.task_planner:
            status["modules"]["task_planner"] = {"status": "ready"}

        if self.metacognition:
            status["modules"]["metacognition"] = self.metacognition.get_reflection_stats()

        if self.persona_engine:
            status["modules"]["persona"] = self.persona_engine.get_stats()

        if self.memory_bridge_v2:
            status["modules"]["memory_bridge"] = self.memory_bridge_v2.get_memory_summary()

        # 新增模块状态
        if self.knowledge_graph:
            status["modules"]["knowledge_graph"] = self.knowledge_graph.get_stats()

        if self.plugin_system:
            status["modules"]["plugin_system"] = self.plugin_system.get_stats()

        if self.api_gateway:
            status["modules"]["api_gateway"] = self.api_gateway.get_request_stats()

        if self.safety_layer:
            status["modules"]["safety_layer"] = self.safety_layer.get_audit_report()

        # 第十轮新增模块状态
        if self.context_awareness:
            status["modules"]["context_awareness"] = {
                "status": "ready",
                "time_context": self.context_awareness.time_awareness.get_context_description(),
            }

        if self.behavior_predictor:
            status["modules"]["behavior_predictor"] = {
                "status": "ready",
                "patterns_count": len(self.behavior_predictor.memory.get_patterns("default")),
            }

        if self.session_manager:
            status["modules"]["session_manager"] = self.session_manager.get_stats()

        # 第十一轮新增模块状态
        if self.self_evolution:
            status["modules"]["self_evolution"] = self.self_evolution.get_evolution_summary()

        # 第十二轮新增模块状态
        if self.tool_registry:
            status["modules"]["tool_system"] = {
                "registry": self.tool_registry.get_stats(),
                "executor": self.tool_executor.get_stats() if self.tool_executor else {},
                "selector": self.tool_selector.get_stats() if self.tool_selector else {},
            }

        # 第十三轮新增模块状态
        if self.dialog_flow:
            status["modules"]["dialog_flow"] = self.dialog_flow.get_stats()

        if self.presentation_engine:
            status["modules"]["presentation_engine"] = self.presentation_engine.get_stats()

        if self.emotion_tracker:
            status["modules"]["emotion_tracker"] = self.emotion_tracker.get_stats()

        # 第十四轮新增模块状态
        if self.autonomous_engine:
            status["modules"]["autonomous_engine"] = self.autonomous_engine.get_autonomous_status()

        # 第十五轮新增模块状态
        if self.scene_manager:
            status["modules"]["scene_manager"] = self.scene_manager.get_stats()

        if self.scene_automation:
            status["modules"]["scene_automation"] = self.scene_automation.get_stats()

        if self.data_analyzer:
            status["modules"]["data_analyzer"] = {"status": "ready", "analyses_count": 0}

        # 第十六轮新增模块状态
        if self.experience_replay:
            status["modules"]["experience_replay"] = self.experience_replay.get_stats()

        # 第十七轮新增模块状态
        if self.intent_predictor:
            status["modules"]["intent_predictor"] = self.intent_predictor.get_stats()

        # 第十八轮新增模块状态
        if self.safety_engine:
            status["modules"]["safety_engine"] = self.safety_engine.get_safety_status()

        if self.safety_monitor:
            status["modules"]["safety_monitor"] = self.safety_monitor.get_stats()

        # 第十九轮新增模块状态
        if self.skill_discoverer:
            status["modules"]["skill_discoverer"] = {
                "top_skills": self.skill_discoverer.get_top_skills(3),
            }

        if self.skill_evolution:
            status["modules"]["skill_evolution"] = self.skill_evolution.get_stats()

        # 第二十轮新增模块状态
        if self.goal_manager:
            status["modules"]["goal_manager"] = self.goal_manager.get_stats()

        if self.goal_planner:
            status["modules"]["goal_planner"] = {"status": "ready"}

        return status

    def close(self):
        """关闭所有模块"""
        if self.memory_os:
            self.memory_os.close()
        if self.memory_evolution:
            self.memory_evolution.close()
        if self.user_profile:
            self.user_profile.close()
        if self.api_gateway and self.api_gateway.auth_manager:
            self.api_gateway.auth_manager.conn.close()
        if self.knowledge_graph:
            self.knowledge_graph.close()
        if self.safety_layer:
            if self.safety_layer.permission_manager.conn:
                self.safety_layer.permission_manager.conn.close()
            if self.safety_layer.audit_logger.conn:
                self.safety_layer.audit_logger.conn.close()
        if self.context_awareness:
            self.context_awareness.close()
        if self.behavior_predictor:
            self.behavior_predictor.close()
        if self.session_manager:
            self.session_manager.close()
        if self.self_evolution:
            self.self_evolution.close()
        if self.tool_executor:
            self.tool_executor.close()
        if self.tool_selector:
            self.tool_selector.close()
        if self.dialog_flow:
            self.dialog_flow.close()
        if self.presentation_engine:
            pass  # No resources to close
        if self.emotion_tracker:
            self.emotion_tracker.close()
        if self.autonomous_engine:
            self.autonomous_engine.close()
        if self.scene_manager:
            self.scene_manager.close()
        if self.scene_automation:
            self.scene_automation.close()
        if self.data_analyzer:
            pass  # DataAnalyzer has no resources to close
        if self.experience_replay:
            self.experience_replay.close()
        if self.intent_predictor:
            self.intent_predictor.close()
        if self.safety_engine:
            self.safety_engine.close()
        if self.safety_monitor:
            self.safety_monitor.close()
        if self.skill_discoverer:
            self.skill_discoverer.close()
        if self.skill_evolution:
            self.skill_evolution.close()
        if self.goal_manager:
            self.goal_manager.close()
        # GoalPlanner has no resources to close
        self.initialized = False

    def register_plugin(self, plugin_id: str, name: str, handler: Any,
                        dependencies: List[str] = None) -> bool:
        """
        注册插件到Jarvis

        Args:
            plugin_id: 插件ID
            name: 插件名称
            handler: 插件处理函数/对象
            dependencies: 依赖列表

        Returns:
            是否注册成功
        """
        if not self.plugin_system:
            return False
        self.plugin_system.register_plugin(plugin_id, name, handler, dependencies or [])
        return True

    def add_knowledge(self, name: str, entity_type: str, description: str = "",
                      properties: Dict = None) -> str:
        """
        添加知识到图谱

        Args:
            name: 实体名称
            entity_type: 实体类型 (CONCEPT/PERSON/OBJECT/EVENT/PLACE/ORGANIZATION/SKILL/TOPIC)
            description: 描述
            properties: 属性字典

        Returns:
            实体ID
        """
        if not self.knowledge_graph:
            return ""
        try:
            from nomad_mem.memory.knowledge_graph import EntityType
            et = EntityType(entity_type.lower())
        except (ValueError, ImportError):
            et = EntityType.CONCEPT
        entity_id = f"entity_{name.lower().replace(' ', '_')}_{int(time.time())}"
        self.knowledge_graph.add_entity(entity_id, name, et, description, properties or {})
        return entity_id

    def query_knowledge(self, keyword: str, depth: int = 1) -> Dict:
        """
        查询知识图谱

        Args:
            keyword: 关键词
            depth: 邻域深度

        Returns:
            查询结果
        """
        result = {"entities": [], "enrichment": []}
        if self.knowledge_graph:
            entities = self.knowledge_graph.search_entities(keyword)
            entities = entities[:5]
            result["entities"] = [
                {"name": e.name, "type": e.entity_type.value, "description": e.description}
                for e in entities
            ]
            if entities:
                neighborhood = self.knowledge_graph.get_entity_neighborhood(
                    entities[0].entity_id, depth=depth
                )
                result["enrichment"] = neighborhood
        return result

    def learn_from_feedback(self, user_id: str, message: str, response: str,
                             feedback: str) -> bool:
        """
        从用户反馈中学习

        Args:
            user_id: 用户ID
            message: 用户消息
            response: 系统回复
            feedback: 用户反馈

        Returns:
            是否学习成功
        """
        if not self.self_evolution:
            return False
        self.self_evolution.learn_from_conversation(user_id, message, response, feedback)
        return True

    def run_evolution_cycle(self) -> Dict:
        """
        执行自我进化周期

        Returns:
            进化报告
        """
        if not self.self_evolution:
            return {"error": "Self evolution engine not available"}
        report = self.self_evolution.run_evolution_cycle()
        return {
            "phase": report.phase.value,
            "findings": report.findings,
            "actions_taken": report.actions_taken,
            "knowledge_gained": report.knowledge_gained,
            "errors_corrected": report.errors_corrected,
        }

    def use_tool(self, tool_id: str, args: Dict = None, user_id: str = "default") -> Dict:
        """
        使用工具

        Args:
            tool_id: 工具ID
            args: 工具参数
            user_id: 用户ID

        Returns:
            工具执行结果
        """
        if not self.tool_registry or not self.tool_executor:
            return {"error": "Tool system not available"}

        tool = self.tool_registry.get_tool(tool_id)
        if not tool:
            return {"error": f"Tool '{tool_id}' not found"}

        if tool.status.value != "available":
            return {"error": f"Tool '{tool_id}' is not available (status: {tool.status.value})"}

        handler = self.tool_registry.get_tool_handler(tool_id)
        params = args or {}

        result = self.tool_executor.execute_sync(
            tool_id=tool_id,
            handler=handler,
            args=[],
            kwargs=params,
            timeout=30,
        )

        # Record selection for learning
        if self.tool_selector:
            self.tool_selector.record_selection(tool_id, result.success)

        return {
            "tool_id": tool_id,
            "success": result.success,
            "result": result.result_data,
            "error": result.error,
            "execution_time": result.execution_time,
            "status": result.status.value,
        }

    def list_tools(self, category: str = None) -> List[Dict]:
        """
        列出可用工具

        Args:
            category: 可选，按类别过滤

        Returns:
            工具列表
        """
        if not self.tool_registry:
            return []
        tools = self.tool_registry.list_tools(
            category=None if not category else __import__('nomad_mem.skills.tool_registry', fromlist=['ToolCategory']).ToolCategory(category)
        )
        return [
            {
                "tool_id": t.tool_id,
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "parameters": [
                    {"name": p.name, "type": p.param_type, "description": p.description, "required": p.required}
                    for p in t.parameters
                ],
            }
            for t in tools
        ]

    def start_dialog_flow(self, flow_type: str, steps: List[Dict] = None,
                          question: str = "", options: List[str] = None) -> Dict:
        """
        启动对话流程

        Args:
            flow_type: 流程类型 (confirmation/menu/form)
            steps: 流程步骤
            question: 问题（用于confirmation/menu）
            options: 选项（用于menu）

        Returns:
            流程信息
        """
        if not self.dialog_flow:
            return {"error": "Dialog flow manager not available"}

        if flow_type == "confirmation":
            flow_id = self.dialog_flow.create_confirmation_flow(question)
        elif flow_type == "menu":
            flow_id = self.dialog_flow.create_menu_flow(question, options or [])
        elif flow_type == "form":
            flow_id = self.dialog_flow.create_form_flow(steps or [])
        else:
            flow_id = self.dialog_flow.start_flow(flow_type, steps or [])

        prompt = self.dialog_flow.get_current_prompt(flow_id)
        return {"flow_id": flow_id, "prompt": prompt}

    def process_dialog_response(self, flow_id: str, user_response: str) -> Dict:
        """
        处理对话流程响应

        Args:
            flow_id: 流程ID
            user_response: 用户响应

        Returns:
            处理结果
        """
        if not self.dialog_flow:
            return {"error": "Dialog flow manager not available"}
        return self.dialog_flow.process_response(flow_id, user_response)

    def present_data(self, data, presentation_type: str = None) -> str:
        """
        展示数据

        Args:
            data: 数据
            presentation_type: 展示类型 (table/list/progress/status_panel/card/timeline)

        Returns:
            格式化后的字符串
        """
        if not self.presentation_engine:
            return str(data)
        return self.presentation_engine.format_response(data, presentation_type)

    def _generate_reply(
        self,
        message: str,
        intent=None,
        memories: List = None,
        user_context: Dict = None
    ) -> str:
        """
        生成回复（模拟，实际应由LLM生成）

        Args:
            message: 用户消息
            intent: 识别的意图
            memories: 相关记忆
            user_context: 用户上下文

        Returns:
            回复内容
        """
        if not intent:
            return f"收到您的消息：{message}"

        # 根据意图生成简单回复
        category = intent.category.value if hasattr(intent, 'category') else str(intent)

        replies = {
            "query": f"关于您的问题，我找到了一些相关信息。{memories[0]['content'] if memories else ''}",
            "command": "好的，我来执行这个操作。",
            "conversation": f"您好！很高兴和您聊天。{memories[0]['content'] if memories else ''}",
            "creation": "好的，我来帮您创建。",
            "modification": "好的，我来修改。",
            "learning": "让我为您解释一下。",
        }

        return replies.get(category, f"我明白了：{message}")

    def start_autonomous_mode(self) -> bool:
        """
        启动自主运行模式

        Returns:
            是否启动成功
        """
        if not self.autonomous_engine:
            return False
        self.autonomous_engine.start()
        return True

    def stop_autonomous_mode(self) -> bool:
        """
        停止自主运行模式

        Returns:
            是否停止成功
        """
        if not self.autonomous_engine:
            return False
        self.autonomous_engine.stop()
        return True

    def add_autonomous_task(self, name: str, trigger_type: str,
                            trigger_config: Dict, action: str) -> str:
        """
        添加自主任务

        Args:
            name: 任务名称
            trigger_type: 触发类型
            trigger_config: 触发配置
            action: 执行动作

        Returns:
            任务ID
        """
        if not self.autonomous_engine:
            return ""
        return self.autonomous_engine.add_autonomous_task(
            name, trigger_type, trigger_config, action
        )

    def run_autonomous_cycle(self) -> Dict:
        """
        执行一次自主循环

        Returns:
            循环报告
        """
        if not self.autonomous_engine:
            return {"error": "Autonomous engine not available"}
        return self.autonomous_engine.run_autonomous_cycle()

    def detect_current_scene(self, user_id: str = "default") -> Optional[str]:
        """
        检测当前场景

        Args:
            user_id: 用户ID

        Returns:
            场景类型名称
        """
        if not self.scene_manager:
            return None
        # Get current context from context_awareness if available
        context = {}
        if self.context_awareness:
            ctx = self.context_awareness.get_current_context(user_id)
            context = {
                "time_of_day": ctx.time_of_day.value,
                "day_type": ctx.day_type.value,
                "activity_state": ctx.activity_state.value,
            }
        scene_type = self.scene_manager.detect_current_scene(context)
        return scene_type.value if scene_type else None

    def activate_scene(self, scene_type: str, user_id: str = "default", reason: str = "") -> bool:
        """
        激活场景

        Args:
            scene_type: 场景类型
            user_id: 用户ID
            reason: 激活原因

        Returns:
            是否激活成功
        """
        if not self.scene_manager:
            return False
        try:
            from nomad_mem.autonomy.scene_manager import SceneType
            st = SceneType(scene_type.lower())
            self.scene_manager.activate_scene(st, triggered_by=reason or "manual")
            return True
        except (ValueError, ImportError):
            return False

    def create_scene_automation(self, scene_type: str, trigger_type: str,
                                action_type: str, action_params: Dict = None) -> bool:
        """
        创建场景自动化规则

        Args:
            scene_type: 场景类型
            trigger_type: 触发类型
            action_type: 动作类型
            action_params: 动作参数

        Returns:
            是否创建成功
        """
        if not self.scene_automation:
            return False
        try:
            action_str = action_type
            if action_params:
                action_str = f"{action_type}:{action_params.get('style', '')}"
            rule_id = self.scene_automation.create_automation_rule(
                name=f"auto_{scene_type}_{action_type}",
                scene_type=scene_type,
                trigger_type=trigger_type,
                trigger_config={},
                actions=[action_str],
            )
            return bool(rule_id)
        except (ValueError, Exception):
            return False

    def check_scene_automation(self, user_id: str = "default") -> Optional[str]:
        """
        检查并执行场景自动化

        Args:
            user_id: 用户ID

        Returns:
            执行的动作类型，无则None
        """
        if not self.scene_automation:
            return None
        # Build context from current scene
        context = {}
        current = self.scene_manager.get_current_scene() if self.scene_manager else None
        if current:
            context["scene_type"] = current.scene_type.value
        events = self.scene_automation.check_and_execute(context)
        if events:
            return events[0].event_type
        return None

    def analyze_data(self, data_points: List, analysis_types: List[str] = None,
                     target_variable: str = None) -> Dict:
        """
        数据分析

        Args:
            data_points: 数据点列表
            analysis_types: 分析类型列表
            target_variable: 目标变量

        Returns:
            分析结果
        """
        if not self.data_analyzer:
            return {"error": "Data analyzer not available"}
        types = analysis_types or ["descriptive"]
        results = {}
        for atype in types:
            try:
                result = self.data_analyzer.analyze_data(data_points, atype)
                results[atype] = result.statistics
            except ValueError:
                results[atype] = {"error": f"Unknown analysis type: {atype}"}
        return results

    def generate_report(self, data_points: List, report_type: str = "summary",
                        target_variable: str = None) -> str:
        """
        生成报告

        Args:
            data_points: 数据点列表
            report_type: 报告类型 (summary/trend/comparison)
            target_variable: 目标变量

        Returns:
            Markdown格式报告
        """
        if not self.data_analyzer:
            return "Data analyzer not available"
        try:
            if report_type == "trend":
                result = self.data_analyzer.generate_trend_report(data_points)
            elif report_type == "comparison":
                result = self.data_analyzer.generate_comparison_report(data_points, target_variable or "value")
            else:
                result = self.data_analyzer.generate_summary_report(data_points)
            # Convert AnalysisResult to markdown string if needed
            if hasattr(result, 'findings'):
                return self.data_analyzer.format_report_as_markdown(result)
            return str(result)
        except Exception:
            return f"Report generation failed for type: {report_type}"

    def record_experience(self, user_id: str, intent: str, action: str,
                          result: str, outcome: str = "positive",
                          lesson: str = "", importance: float = 0.5) -> str:
        """
        记录交互经验

        Args:
            user_id: 用户ID
            intent: 意图
            action: 采取的行动
            result: 结果
            outcome: 结果类型 (positive/negative/neutral)
            lesson: 教训
            importance: 重要程度

        Returns:
            经验ID
        """
        if not self.experience_replay:
            return ""
        try:
            from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
            exp_type = ExperienceType.SUCCESS if outcome == "positive" else ExperienceType.FAILURE
            exp_outcome = ExperienceOutcome(outcome)
            return self.experience_replay.record_experience(
                user_id=user_id,
                intent=intent,
                context="{}",
                action_taken=action,
                result=result,
                exp_type=exp_type,
                outcome=exp_outcome,
                lesson_learned=lesson,
                importance=importance,
            )
        except (ValueError, Exception):
            return ""

    def retrieve_experiences(self, keyword: str, k: int = 5) -> List[Dict]:
        """
        检索相关经验

        Args:
            keyword: 搜索关键词
            k: 返回数量

        Returns:
            经验列表
        """
        if not self.experience_replay:
            return []
        experiences = self.experience_replay.retrieve_similar(keyword, k)
        return [
            {
                "exp_id": e.exp_id,
                "intent": e.intent,
                "action": e.action_taken,
                "result": e.result,
                "outcome": e.outcome.value,
                "lesson": e.lesson_learned,
                "importance": e.importance,
            }
            for e in experiences
        ]

    def get_experience_summary(self, user_id: str = "default") -> Dict:
        """
        获取经验摘要

        Args:
            user_id: 用户ID

        Returns:
            经验摘要
        """
        if not self.experience_summarizer:
            return {"error": "Experience summarizer not available"}
        summary = self.experience_summarizer.generate_user_summary(user_id)
        return summary.to_dict()

    def get_failure_analysis(self) -> Dict:
        """
        获取失败经验分析

        Returns:
            分析报告
        """
        if not self.experience_summarizer:
            return {"error": "Experience summarizer not available"}
        return self.experience_summarizer.generate_failure_analysis()

    def get_experience_stats(self, user_id: str = "default") -> Dict:
        """
        获取经验统计

        Args:
            user_id: 用户ID

        Returns:
            统计信息
        """
        if not self.experience_replay:
            return {}
        return self.experience_replay.get_user_stats(user_id)

    def extract_experience_patterns(self) -> List[Dict]:
        """
        提取经验模式

        Returns:
            模式列表
        """
        if not self.experience_replay:
            return []
        patterns = self.experience_replay.extract_patterns()
        return [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type,
                "description": p.description,
                "frequency": p.frequency,
                "success_rate": p.success_rate,
            }
            for p in patterns
        ]

    def record_intent_transition(self, user_id: str, from_intent: str,
                                 to_intent: str, scene: str = "",
                                 success: bool = True) -> bool:
        """
        记录意图转换

        Args:
            user_id: 用户ID
            from_intent: 当前意图
            to_intent: 下一个意图
            scene: 场景上下文
            success: 是否成功

        Returns:
            是否记录成功
        """
        if not self.intent_predictor:
            return False
        try:
            self.intent_predictor.record_transition(
                user_id, from_intent, to_intent, scene, success
            )
            return True
        except Exception:
            return False

    def predict_next_intent(self, user_id: str, current_intent: str = "",
                            scene: str = "", k: int = 3) -> List[Dict]:
        """
        预测下一个意图

        Args:
            user_id: 用户ID
            current_intent: 当前意图
            scene: 场景上下文
            k: 返回预测数量

        Returns:
            预测列表
        """
        if not self.intent_predictor:
            return []
        predictions = self.intent_predictor.predict_next(
            user_id, current_intent, scene, k
        )
        return [p.to_dict() for p in predictions]

    def get_proactive_response(self, user_id: str, current_intent: str = "",
                               scene: str = "") -> Dict:
        """
        获取主动响应

        Args:
            user_id: 用户ID
            current_intent: 当前意图
            scene: 场景上下文

        Returns:
            主动响应
        """
        if not self.intent_predictor or not self.proactive_responder:
            return {"should_respond": False}
        predictions = self.intent_predictor.predict_next(
            user_id, current_intent, scene, k=1
        )
        if not predictions:
            return {"should_respond": False}
        response = self.proactive_responder.generate_response(predictions[0])
        return response.to_dict()

    def set_proactive_level(self, level: str) -> bool:
        """
        设置主动程度

        Args:
            level: minimal/balanced/aggressive

        Returns:
            是否设置成功
        """
        if not self.proactive_responder:
            return False
        try:
            self.proactive_responder.set_proactive_level(level)
            return True
        except Exception:
            return False

    def get_intent_profile(self, user_id: str = "default") -> Dict:
        """
        获取用户意图画像

        Args:
            user_id: 用户ID

        Returns:
            意图画像
        """
        if not self.intent_predictor:
            return {}
        return self.intent_predictor.get_user_intent_profile(user_id)

    def get_intent_flow(self, user_id: str = "default",
                        from_intent: str = "") -> List[Dict]:
        """
        获取意图流转统计

        Args:
            user_id: 用户ID
            from_intent: 可选，从指定意图出发

        Returns:
            流转统计
        """
        if not self.intent_predictor:
            return []
        return self.intent_predictor.get_intent_flow(user_id, from_intent)

    def assess_safety_risk(self, user_id: str, action: str,
                           target: str = "") -> Dict:
        """
        评估操作安全风险

        Args:
            user_id: 用户ID
            action: 操作类型
            target: 操作目标

        Returns:
            风险评估结果
        """
        if not self.safety_engine:
            return {}
        assessment = self.safety_engine.assess_operation(user_id, action, target)
        return assessment.to_dict()

    def check_safety_anomalies(self, user_id: str) -> List[Dict]:
        """
        检查安全异常

        Args:
            user_id: 用户ID

        Returns:
            异常事件列表
        """
        if not self.safety_monitor:
            return []
        return self.safety_monitor.check_anomalies(user_id)

    def report_user_operation(self, user_id: str, action: str,
                              risk_score: float = 0.0, target: str = ""):
        """
        报告用户操作给监控器

        Args:
            user_id: 用户ID
            action: 操作类型
            risk_score: 风险分数
            target: 操作目标
        """
        if self.safety_monitor:
            self.safety_monitor.report_operation(user_id, action, risk_score, target)

    def get_user_safety_status(self, user_id: str = "default") -> Dict:
        """
        获取用户安全状态

        Args:
            user_id: 用户ID

        Returns:
            安全状态
        """
        if not self.safety_monitor:
            return {}
        return self.safety_monitor.get_user_status(user_id)

    def get_safety_events(self, user_id: str = "", k: int = 20) -> List[Dict]:
        """
        获取安全事件

        Args:
            user_id: 可选，用户ID
            k: 返回数量

        Returns:
            安全事件列表
        """
        if not self.safety_monitor:
            return []
        return self.safety_monitor.get_events(user_id, k)

    def set_safety_policy(self, policy_name: str) -> bool:
        """
        设置安全策略

        Args:
            policy_name: 策略名称 (default/strict/relaxed)

        Returns:
            是否设置成功
        """
        if not self.safety_engine:
            return False
        return self.safety_engine.set_policy(policy_name)

    def update_user_baseline(self, user_id: str):
        """更新用户行为基线"""
        if self.safety_engine:
            self.safety_engine.update_user_baseline(user_id)

    def get_safety_overview(self) -> Dict:
        """获取安全系统总览"""
        if not self.safety_engine:
            return {}
        return self.safety_engine.get_safety_status()

    # ── Skill Discovery & Evolution ─────────────────────────────────────

    def record_skill_usage(self, skill_name: str, context: str = "",
                           result: str = "", success: bool = True) -> str:
        """
        记录技能使用

        Args:
            skill_name: 技能名称
            context: 上下文
            result: 结果
            success: 是否成功

        Returns:
            使用记录ID
        """
        if not self.skill_discoverer:
            return ""
        return self.skill_discoverer.record_usage(skill_name, context, result, success)

    def find_skill_combinations(self, min_frequency: int = 2) -> List[Dict]:
        """
        查找技能组合

        Args:
            min_frequency: 最小频率

        Returns:
            技能组合列表
        """
        if not self.skill_discoverer:
            return []
        combos = self.skill_discoverer.find_combinations(min_frequency)
        return [
            {
                "skills": c.skills,
                "frequency": c.frequency,
                "success_rate": c.success_rate,
            }
            for c in combos
        ]

    def suggest_next_skill(self, current_skills: List[str]) -> Optional[str]:
        """
        建议下一个技能

        Args:
            current_skills: 当前技能列表

        Returns:
            建议的技能名称
        """
        if not self.skill_discoverer:
            return None
        return self.skill_discoverer.suggest_next_skill(current_skills)

    def get_skill_stats(self, skill_name: str) -> Dict:
        """
        获取技能统计

        Args:
            skill_name: 技能名称

        Returns:
            统计信息
        """
        if not self.skill_discoverer:
            return {}
        return self.skill_discoverer.get_skill_stats(skill_name)

    def get_top_skills(self, limit: int = 10) -> List[Dict]:
        """
        获取最常用技能

        Args:
            limit: 返回数量

        Returns:
            技能列表
        """
        if not self.skill_discoverer:
            return []
        return self.skill_discoverer.get_top_skills(limit)

    def discover_skill_patterns(self) -> List[Dict]:
        """
        发现技能使用模式

        Returns:
            模式列表
        """
        if not self.skill_discoverer:
            return []
        return self.skill_discoverer.discover_new_patterns()

    def register_new_skill(self, skill_name: str, description: str = "",
                           category: str = "general") -> bool:
        """
        注册新技能

        Args:
            skill_name: 技能名称
            description: 描述
            category: 分类

        Returns:
            是否注册成功
        """
        if not self.skill_evolution:
            return False
        return self.skill_evolution.register_skill(skill_name, description, category)

    def get_skill_performance(self, skill_name: str) -> Dict:
        """
        获取技能性能指标

        Args:
            skill_name: 技能名称

        Returns:
            性能指标
        """
        if not self.skill_evolution:
            return {}
        return self.skill_evolution.get_skill_performance(skill_name)

    def record_skill_performance(self, skill_name: str, response_time: float,
                                 success: bool, rating: float = 0.5):
        """
        记录技能性能

        Args:
            skill_name: 技能名称
            response_time: 响应时间
            success: 是否成功
            rating: 用户评分
        """
        if self.skill_evolution:
            self.skill_evolution.record_skill_result(
                skill_name, response_time, success, rating
            )

    def get_optimization_suggestions(self, skill_name: str = "") -> List[Dict]:
        """
        获取优化建议

        Args:
            skill_name: 可选，指定技能

        Returns:
            建议列表
        """
        if not self.skill_evolution:
            return []
        suggestions = self.skill_evolution.get_optimization_suggestions(skill_name)
        return [s.to_dict() for s in suggestions]

    def get_skill_versions(self, skill_name: str) -> List[Dict]:
        """
        获取技能版本历史

        Args:
            skill_name: 技能名称

        Returns:
            版本列表
        """
        if not self.skill_evolution:
            return []
        versions = self.skill_evolution.get_versions(skill_name)
        return [v.to_dict() for v in versions]

    def create_skill_version(self, skill_name: str, version: str,
                             description: str, evolution_type: str = "performance") -> str:
        """
        创建技能新版本

        Args:
            skill_name: 技能名称
            version: 版本号
            description: 描述
            evolution_type: 进化类型

        Returns:
            版本ID
        """
        if not self.skill_evolution:
            return ""
        result = self.skill_evolution.create_version(
            skill_name, version, description, evolution_type
        )
        return result or ""

    def deprecate_skill(self, skill_name: str) -> bool:
        """
        废弃技能

        Args:
            skill_name: 技能名称

        Returns:
            是否成功
        """
        if not self.skill_evolution:
            return False
        return self.skill_evolution.deprecate_skill(skill_name)

    def get_deprecation_candidates(self) -> List[Dict]:
        """
        获取可能应该废弃的技能

        Returns:
            候选列表
        """
        if not self.skill_evolution:
            return []
        return self.skill_evolution.get_deprecation_candidates()

    def get_skill_system_stats(self) -> Dict:
        """
        获取技能系统统计

        Returns:
            统计信息
        """
        stats = {}
        if self.skill_discoverer:
            stats["discovery"] = {
                "top_skills": self.skill_discoverer.get_top_skills(5),
                "patterns": self.skill_discoverer.discover_new_patterns(),
            }
        if self.skill_evolution:
            stats["evolution"] = self.skill_evolution.get_stats()
        return stats

    # ── Goal Management & Planning ─────────────────────────────────────

    def create_goal(self, user_id: str, title: str, goal_type: str = "task",
                    priority: str = "medium", deadline: Optional[str] = None,
                    subgoals: List[str] = None) -> str:
        """
        创建目标

        Args:
            user_id: 用户ID
            title: 目标标题
            goal_type: 目标类型
            priority: 优先级
            deadline: 截止日期
            subgoals: 子目标列表

        Returns:
            目标ID
        """
        if not self.goal_manager:
            return ""
        goal_id = self.goal_manager.create_goal(
            user_id=user_id,
            title=title,
            goal_type=goal_type,
            priority=priority,
            deadline=deadline,
        )
        if subgoals and goal_id:
            self.goal_manager.add_subgoals(goal_id, subgoals)
        return goal_id

    def add_subgoals(self, goal_id: str, subgoal_titles: List[str]) -> bool:
        """
        添加子目标

        Args:
            goal_id: 目标ID
            subgoal_titles: 子目标标题列表

        Returns:
            是否添加成功
        """
        if not self.goal_manager:
            return False
        return self.goal_manager.add_subgoals(goal_id, subgoal_titles)

    def update_goal_progress(self, goal_id: str, subgoal_id: str,
                             progress: float = 100.0) -> bool:
        """
        更新子目标进度

        Args:
            goal_id: 目标ID
            subgoal_id: 子目标ID
            progress: 进度(0-100)

        Returns:
            是否更新成功
        """
        if not self.goal_manager:
            return False
        # Convert 0-100 to 0.0-1.0
        normalized = progress / 100.0 if progress > 1.0 else progress
        return self.goal_manager.update_subgoal_progress(
            goal_id, subgoal_id, normalized
        )

    def get_goal_progress(self, goal_id: str) -> Dict:
        """
        获取目标进度

        Args:
            goal_id: 目标ID

        Returns:
            进度详情字典
        """
        if not self.goal_manager:
            return {}
        return self.goal_manager.get_goal_progress(goal_id)

    def get_user_goals(self, user_id: str, status: str = "") -> List[Dict]:
        """
        获取用户目标

        Args:
            user_id: 用户ID
            status: 可选，按状态过滤

        Returns:
            目标列表
        """
        if not self.goal_manager:
            return []
        goals = self.goal_manager.get_user_goals(user_id)
        if status:
            goals = [g for g in goals if g.status.value == status]
        return [
            {
                "goal_id": g.goal_id,
                "title": g.title,
                "goal_type": g.goal_type.value,
                "priority": g.priority.value,
                "status": g.status.value,
                "progress": g.progress,
                "deadline": g.deadline,
            }
            for g in goals
        ]

    def get_active_goals(self, user_id: str = "") -> List[Dict]:
        """
        获取活跃目标

        Args:
            user_id: 可选，用户ID

        Returns:
            活跃目标列表
        """
        if not self.goal_manager:
            return []
        goals = self.goal_manager.get_active_goals(user_id)
        return [
            {
                "goal_id": g.goal_id,
                "title": g.title,
                "progress": g.progress,
                "priority": g.priority.value,
            }
            for g in goals
        ]

    def update_goal_status(self, goal_id: str, status: str) -> bool:
        """
        更新目标状态

        Args:
            goal_id: 目标ID
            status: 新状态

        Returns:
            是否更新成功
        """
        if not self.goal_manager:
            return False
        try:
            from nomad_mem.autonomy.goal_manager import GoalStatus
            gs = GoalStatus(status.upper())
            return self.goal_manager.update_goal_status(goal_id, gs)
        except (ValueError, ImportError):
            return False

    def update_goal_priority(self, goal_id: str, priority: str) -> bool:
        """
        更新目标优先级

        Args:
            goal_id: 目标ID
            priority: 新优先级

        Returns:
            是否更新成功
        """
        if not self.goal_manager:
            return False
        try:
            from nomad_mem.autonomy.goal_manager import GoalPriority
            gp = GoalPriority(priority.upper())
            return self.goal_manager.update_priority(goal_id, gp)
        except (ValueError, ImportError):
            return False

    def suggest_goals(self, user_id: str, scene: str = "", k: int = 3) -> List[Dict]:
        """
        获取目标建议

        Args:
            user_id: 用户ID
            scene: 当前场景
            k: 建议数量

        Returns:
            建议列表
        """
        if not self.goal_planner:
            return []
        plans = self.goal_planner.suggest_goals(user_id, scene, k)
        return [p.to_dict() for p in plans]

    def decompose_goal(self, goal_title: str, goal_type: str = "task") -> List[str]:
        """
        分解目标为子目标

        Args:
            goal_title: 目标标题
            goal_type: 目标类型

        Returns:
            子目标列表
        """
        if not self.goal_planner:
            return []
        return self.goal_planner.decompose_goal(goal_title, goal_type)

    def estimate_goal_difficulty(self, goal_title: str, required_skills: List[str] = None) -> float:
        """
        预估目标难度

        Args:
            goal_title: 目标标题
            required_skills: 所需技能

        Returns:
            难度(0.0-1.0)
        """
        if not self.goal_planner:
            return 0.0
        return self.goal_planner.estimate_difficulty(goal_title, required_skills)

    def get_goal_stats(self, user_id: str = "default") -> Dict:
        """
        获取目标统计

        Args:
            user_id: 用户ID

        Returns:
            统计信息
        """
        stats = {}
        if self.goal_manager:
            stats["manager"] = self.goal_manager.get_stats()
            if user_id:
                stats["user"] = self.goal_manager.get_user_stats(user_id)
        if self.goal_planner:
            stats["planner"] = {"status": "ready"}
        return stats
