"""
Jarvis Core - 贾维斯核心集成层

整合所有模块的统一入口:
1. 记忆系统 (MemoryOS + 进化 + 压缩)
2. 自主意识 (Driver + 元认知 + 人格)
3. 意图理解 (Intent Engine)
4. 任务规划 (Task Planner)
5. 技能编排 (Skill Orchestrator)
6. 对话管理 (Dialog Manager)
7. 用户画像 (User Profile)

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

            # 7. 格式化回复（人格化）
            if self.persona_engine:
                emotion = self.persona_engine.select_emotion(message)
                reply = self.persona_engine.format_response(reply, emotion)

            response["response"] = reply

            # 8. 存储到记忆
            if self.memory_bridge_v2:
                self.memory_bridge_v2.store_conversation(message, reply, user_id)

            # 9. 更新用户画像
            if self.user_profile:
                self.user_profile.update_from_interaction(
                    user_id=user_id,
                    message=message,
                )

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

        return status

    def close(self):
        """关闭所有模块"""
        if self.memory_os:
            self.memory_os.close()
        if self.memory_evolution:
            self.memory_evolution.close()
        if self.user_profile:
            self.user_profile.close()
        self.initialized = False

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
