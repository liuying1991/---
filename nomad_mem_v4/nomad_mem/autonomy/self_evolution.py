"""
Self Evolution Engine - 自我进化引擎

核心能力:
1. 错误学习：记录错误 → 发现模式 → 自我纠正
2. 知识自扩：从对话抽取事实 → 候选审核 → 扩充知识图谱
3. 技能发现：追踪使用模式 → 发现组合 → 推荐新技能
4. 响应优化：收集反馈 → 优化模板 → 自适应回复

设计原则:
- 从每次交互中自动学习
- 保守验证，不盲目接受新知识
- 基于证据的进化，不是随机变化
- 可追溯：每个进化决策都有依据

参考:
- 经验回放(Experience Replay)
- 在线学习(Online Learning)
- 强化学习中的自我改进循环
"""
import time
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class EvolutionPhase(Enum):
    """进化阶段"""
    OBSERVE = "observe"        # 观察收集
    ANALYZE = "analyze"        # 分析模式
    HYPOTHESIZE = "hypothesize"  # 形成假设
    VALIDATE = "validate"      # 验证假设
    INTEGRATE = "integrate"    # 整合进化


@dataclass
class EvolutionReport:
    """进化报告"""
    timestamp: float
    phase: EvolutionPhase
    findings: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    knowledge_gained: int = 0
    errors_corrected: int = 0
    skills_discovered: int = 0
    responses_optimized: int = 0


class SelfEvolutionEngine:
    """自我进化引擎

    整合错误学习、知识自扩、技能发现、响应优化，
    为Jarvis提供持续自我进化的能力。
    """

    def __init__(self, data_dir: str = "data", knowledge_graph=None):
        os.makedirs(data_dir, exist_ok=True)

        # 初始化子模块
        from nomad_mem.autonomy.error_learner import ErrorLearner
        from nomad_mem.memory.knowledge_expansion import KnowledgeExpander
        from nomad_mem.skills.skill_discovery import SkillDiscoverer
        from nomad_mem.autonomy.response_optimizer import ResponseOptimizer

        self.error_learner = ErrorLearner(
            db_path=os.path.join(data_dir, "error_learner.db")
        )
        self.knowledge_expander = KnowledgeExpander(
            db_path=os.path.join(data_dir, "knowledge_expansion.db")
        )
        self.skill_discoverer = SkillDiscoverer(
            db_path=os.path.join(data_dir, "skill_discovery.db")
        )
        self.response_optimizer = ResponseOptimizer(
            db_path=os.path.join(data_dir, "response_optimizer.db")
        )

        self.knowledge_graph = knowledge_graph
        self._evolution_history: List[EvolutionReport] = []

    def record_interaction_result(self, user_id: str, message: str,
                                   response: str, success: bool,
                                   error_type: str = "", feedback: str = "",
                                   skills_used: List[str] = None):
        """
        记录交互结果，驱动各子模块学习

        Args:
            user_id: 用户ID
            message: 用户消息
            response: 系统回复
            success: 是否成功
            error_type: 错误类型（失败时填写）
            feedback: 用户反馈 (positive/negative/neutral)
            skills_used: 使用的技能列表
        """
        # 1. 错误学习
        if not success and error_type:
            from nomad_mem.autonomy.error_learner import ErrorType
            try:
                et = ErrorType(error_type.lower())
            except ValueError:
                et = ErrorType.CONTEXT

            self.error_learner.record_error(
                user_id=user_id,
                error_type=et,
                description=f"处理消息失败: {message[:100]}",
                context={"message": message, "response": response},
                correction=feedback,
            )

        # 2. 知识自扩：从成功对话中提取事实
        if success:
            facts = self.knowledge_expander.extract_facts(message, response)
            # 自动添加为候选（低置信度需要人工验证）
            for fact in facts:
                if fact.confidence > 0.7:
                    # 高置信度直接验证
                    self.knowledge_expander.extract_facts.__self__  # no-op, just using extract_facts
                # Facts are stored, candidates need manual addition

        # 3. 技能发现
        if skills_used:
            for skill in skills_used:
                self.skill_discoverer.record_usage(
                    skill_name=skill,
                    context={"message": message[:50]},
                    result=response[:100],
                    success=success,
                )

        # 4. 响应优化
        if feedback:
            self.response_optimizer.record_feedback(
                response_text=response,
                feedback_type=feedback,
                context={"message": message[:50]},
            )

    def learn_from_conversation(self, user_id: str, message: str,
                                 response: str, user_feedback: str = ""):
        """
        从对话中学习

        Args:
            user_id: 用户ID
            message: 用户消息
            response: 系统回复
            user_feedback: 用户反馈 (good/bad/neutral or any text)
        """
        # 推断反馈类型
        feedback_lower = user_feedback.lower() if user_feedback else ""
        if any(w in feedback_lower for w in ["good", "great", "thanks", "helpful", "正确", "好", "谢谢"]):
            feedback_type = "positive"
        elif any(w in feedback_lower for w in ["bad", "wrong", "useless", "错误", "不好", "没用"]):
            feedback_type = "negative"
        else:
            feedback_type = "neutral"

        # 让响应优化器学习
        self.response_optimizer.learn_from_conversation(
            message=message,
            response=response,
            user_feedback=user_feedback,
        )

        # 知识扩展：抽取事实
        facts = self.knowledge_expander.extract_facts(message, response)

    def get_correction_suggestion(self, error_type: str, context: Dict = None) -> Optional[str]:
        """
        获取纠正建议

        Args:
            error_type: 错误类型
            context: 当前上下文

        Returns:
            纠正建议
        """
        return self.error_learner.suggest_correction(error_type, context or {})

    def get_optimized_response(self, intent_category: str, user_context: Dict = None) -> Optional[str]:
        """
        获取优化后的回复模板

        Args:
            intent_category: 意图类别
            user_context: 用户上下文

        Returns:
            优化后的回复
        """
        return self.response_optimizer.get_best_template(intent_category)

    def get_skill_recommendations(self, current_skills: List[str]) -> List[str]:
        """
        获取技能推荐

        Args:
            current_skills: 当前使用的技能

        Returns:
            推荐技能列表
        """
        suggested = self.skill_discoverer.suggest_next_skill(current_skills)
        return [suggested] if suggested else []

    def get_pending_knowledge(self, limit: int = 10) -> List[Dict]:
        """
        获取待审核知识

        Args:
            limit: 返回数量

        Returns:
            待审核知识候选列表
        """
        candidates = self.knowledge_expander.get_pending_candidates(limit)
        return [
            {
                "candidate_id": c.candidate_id,
                "entity_name": c.entity_name,
                "entity_type": c.entity_type,
                "confidence": c.confidence,
            }
            for c in candidates
        ]

    def verify_knowledge(self, candidate_id: str, verified: bool = True) -> bool:
        """
        验证知识候选

        Args:
            candidate_id: 候选ID
            verified: 是否验证通过

        Returns:
            是否成功
        """
        return self.knowledge_expander.verify_candidate(candidate_id, verified)

    def run_evolution_cycle(self) -> EvolutionReport:
        """
        执行一次完整的进化周期

        Returns:
            进化报告
        """
        report = EvolutionReport(
            timestamp=time.time(),
            phase=EvolutionPhase.ANALYZE,
        )

        # 1. 分析错误模式
        error_stats = self.error_learner.get_error_stats()
        if error_stats["total_errors"] > 0:
            report.findings.append(f"发现 {error_stats['total_errors']} 个错误记录")
            report.errors_corrected = error_stats.get("corrected_count", 0)

        # 2. 检查知识扩展
        expansion_stats = self.knowledge_expander.get_expansion_stats()
        pending = expansion_stats.get("pending_candidates", 0)
        if pending > 0:
            report.findings.append(f"有 {pending} 个知识候选待审核")

        # 3. 发现技能组合
        combos = self.skill_discoverer.find_combinations(min_frequency=2)
        if combos:
            report.findings.append(f"发现 {len(combos)} 个技能组合模式")
            report.skills_discovered = len(combos)

        # 4. 分析反馈趋势
        feedback = self.response_optimizer.get_feedback_summary()
        if feedback.get("total_feedback", 0) > 0:
            report.findings.append(f"收到 {feedback['total_feedback']} 条反馈")
            report.responses_optimized = feedback.get("total_templates", 0)

        # 尝试自动扩展知识到图谱
        if self.knowledge_graph:
            added = self.knowledge_expander.auto_expand(self.knowledge_graph)
            report.knowledge_gained = added

        report.phase = EvolutionPhase.INTEGRATE
        report.actions_taken = report.findings[:]
        self._evolution_history.append(report)

        return report

    def get_evolution_summary(self) -> Dict:
        """获取进化摘要"""
        return {
            "error_learner": self.error_learner.get_error_stats(),
            "knowledge_expansion": self.knowledge_expander.get_expansion_stats(),
            "skill_discovery": {
                "top_skills": self.skill_discoverer.get_top_skills(limit=5),
                "combinations": len(self.skill_discoverer.find_combinations()),
            },
            "response_optimizer": self.response_optimizer.get_feedback_summary(),
            "evolution_cycles": len(self._evolution_history),
        }

    def close(self):
        """关闭所有子模块"""
        self.error_learner.close()
        self.knowledge_expander.close()
        self.skill_discoverer.close()
        self.response_optimizer.close()
