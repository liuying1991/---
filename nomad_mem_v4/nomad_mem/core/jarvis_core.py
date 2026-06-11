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
                self.session_manager.add_turn(
                    session_id=session_id,
                    user_utterance=message,
                    dialog_act=intent_category,
                )
                response["session_id"] = session_id

            # 13. 行为预测（预测下一步需求）
            if self.behavior_predictor:
                intent_str = intent.category.value if intent and hasattr(intent, 'category') else "chat"
                self.behavior_predictor.record_behavior(
                    user_id=user_id,
                    action=intent_str,
                    context={"message_length": len(message)},
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
                "patterns_count": len(self.behavior_predictor.pattern_memory.get_all_patterns()),
            }

        if self.session_manager:
            status["modules"]["session_manager"] = self.session_manager.get_stats()

        # 第十一轮新增模块状态
        if self.self_evolution:
            status["modules"]["self_evolution"] = self.self_evolution.get_evolution_summary()

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
