"""
Metacognition - 元认知模块

核心能力：
1. 自我评估：评估输出质量（完整性、准确性、一致性）
2. 错误检测：识别潜在错误或幻觉
3. 自我修正：发现问题后自动修正
4. 信心评分：对输出给予置信度
5. 反思日志：记录自我评估历史

参考：
- 元认知理论 (Flavell, 1979): 对认知过程的认知
- 自我修正循环 (Madaan et al., 2023): Self-Refine
"""
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class QualityDimension(Enum):
    """质量维度"""
    COMPLETENESS = "completeness"      # 完整性
    ACCURACY = "accuracy"              # 准确性
    CONSISTENCY = "consistency"        # 一致性
    RELEVANCE = "relevance"            # 相关性
    CLARITY = "clarity"                # 清晰性
    SAFETY = "safety"                  # 安全性


class ConfidenceLevel(Enum):
    """信心等级"""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class SelfEvaluation:
    """自我评估结果"""
    output_id: str
    dimension_scores: Dict[QualityDimension, float] = field(default_factory=dict)
    overall_score: float = 0.5
    confidence: float = 0.5
    issues: List[Dict] = field(default_factory=list)  # [{"type": "...", "description": "...", "severity": "..."}]
    suggestions: List[str] = field(default_factory=list)
    needs_revision: bool = False
    evaluated_at: float = field(default_factory=time.time)


@dataclass
class ReflectionLog:
    """反思日志"""
    log_id: str
    original_output: str
    evaluation: SelfEvaluation
    revision: str = ""
    improvement_score: float = 0.0
    created_at: float = field(default_factory=time.time)


class MetacognitionEngine:
    """元认知引擎"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.quality_threshold = self.config.get("quality_threshold", 0.6)
        self.max_revision_attempts = self.config.get("max_revision_attempts", 2)
        self.reflection_history: List[ReflectionLog] = []

        # 检查规则
        self.safety_keywords = self.config.get("safety_keywords", [
            "不确定", "可能", "也许", "应该", "或许"
        ])
        self.error_patterns = self.config.get("error_patterns", [
            "我不知道", "我不确定", "无法回答", "没有信息"
        ])

    def evaluate_output(
        self,
        output: str,
        query: str = "",
        context: Dict = None
    ) -> SelfEvaluation:
        """
        评估输出质量

        Args:
            output: AI输出文本
            query: 原始查询
            context: 对话上下文

        Returns:
            自我评估结果
        """
        import uuid
        evaluation = SelfEvaluation(output_id=f"eval_{uuid.uuid4().hex[:8]}")

        # 1. 完整性检查
        evaluation.dimension_scores[QualityDimension.COMPLETENESS] = self._check_completeness(output, query)

        # 2. 准确性检查
        evaluation.dimension_scores[QualityDimension.ACCURACY] = self._check_accuracy(output)

        # 3. 一致性检查
        evaluation.dimension_scores[QualityDimension.CONSISTENCY] = self._check_consistency(output, context)

        # 4. 相关性检查
        evaluation.dimension_scores[QualityDimension.RELEVANCE] = self._check_relevance(output, query)

        # 5. 清晰性检查
        evaluation.dimension_scores[QualityDimension.CLARITY] = self._check_clarity(output)

        # 6. 安全性检查
        evaluation.dimension_scores[QualityDimension.SAFETY] = self._check_safety(output)

        # 计算总体分数
        scores = list(evaluation.dimension_scores.values())
        evaluation.overall_score = sum(scores) / len(scores) if scores else 0.5

        # 计算信心分数
        evaluation.confidence = self._calculate_confidence(evaluation.dimension_scores)

        # 检测问题
        evaluation.issues = self._detect_issues(output, evaluation.dimension_scores)

        # 生成建议
        evaluation.suggestions = self._generate_suggestions(evaluation)

        # 判断是否需要修正
        evaluation.needs_revision = (
            evaluation.overall_score < self.quality_threshold or
            any(issue["severity"] == "high" for issue in evaluation.issues)
        )

        return evaluation

    def self_revise(
        self,
        output: str,
        evaluation: SelfEvaluation,
        revision_fn: Optional[Any] = None
    ) -> str:
        """
        自我修正

        Args:
            output: 原始输出
            evaluation: 评估结果
            revision_fn: 修正函数（可选，默认使用规则修正）

        Returns:
            修正后的输出
        """
        if not evaluation.needs_revision:
            return output

        # 根据问题类型进行修正
        revised = output

        for issue in evaluation.issues:
            issue_type = issue.get("type", "")

            if issue_type == "uncertainty":
                revised = self._revise_uncertainty(revised)
            elif issue_type == "incompleteness":
                revised = self._revise_incompleteness(revised)
            elif issue_type == "inconsistency":
                revised = self._revise_inconsistency(revised)
            elif issue_type == "safety_concern":
                revised = self._revise_safety(revised)

        return revised

    def evaluate_and_revise(
        self,
        output: str,
        query: str = "",
        context: Dict = None,
        revision_fn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        评估并修正（一键式）

        Args:
            output: AI输出
            query: 原始查询
            context: 对话上下文
            revision_fn: 修正函数

        Returns:
            包含评估结果和修正后输出的字典
        """
        evaluation = self.evaluate_output(output, query, context)
        revised = self.self_revise(output, evaluation, revision_fn)

        import uuid
        log = ReflectionLog(
            log_id=f"log_{uuid.uuid4().hex[:8]}",
            original_output=output,
            evaluation=evaluation,
            revision=revised,
            improvement_score=self._calc_improvement(output, revised)
        )
        self.reflection_history.append(log)

        return {
            "evaluation": evaluation,
            "revised_output": revised,
            "improved": log.improvement_score > 0,
        }

    def get_reflection_stats(self) -> Dict[str, Any]:
        """获取反思统计"""
        if not self.reflection_history:
            return {
                "total_reflections": 0,
                "avg_improvement": 0.0,
                "revision_rate": 0.0,
            }

        improvements = [log.improvement_score for log in self.reflection_history]
        revisions = sum(1 for log in self.reflection_history if log.evaluation.needs_revision)

        return {
            "total_reflections": len(self.reflection_history),
            "avg_improvement": sum(improvements) / len(improvements),
            "revision_rate": revisions / len(self.reflection_history),
            "latest_reflection": self.reflection_history[-1].created_at,
        }

    def _check_completeness(self, output: str, query: str) -> float:
        """检查完整性"""
        if not output:
            return 0.0

        score = 0.5  # 基础分

        # 长度合理
        if 10 <= len(output) <= 2000:
            score += 0.1

        # 有结论或总结
        if any(word in output for word in ["总结", "结论", "所以", "因此", "综上所述"]):
            score += 0.1

        # 回答包含查询关键词
        if query:
            query_words = set(query.lower().split())
            output_words = set(output.lower().split())
            keyword_coverage = len(query_words & output_words) / max(len(query_words), 1)
            score += keyword_coverage * 0.3

        return min(1.0, score)

    def _check_accuracy(self, output: str) -> float:
        """检查准确性"""
        if not output:
            return 0.0

        score = 0.7  # 默认较高

        # 检测到不确定性词汇扣分
        uncertainty_count = sum(1 for kw in self.safety_keywords if kw in output)
        score -= uncertainty_count * 0.05

        # 检测到明确错误模式扣分
        error_count = sum(1 for pat in self.error_patterns if pat in output.lower())
        score -= error_count * 0.2

        return max(0.0, min(1.0, score))

    def _check_consistency(self, output: str, context: Dict = None) -> float:
        """检查一致性"""
        if not output or not context:
            return 0.5

        score = 0.7

        # 检查是否与历史对话矛盾
        history = context.get("history", [])
        if history:
            contradictions = self._detect_contradictions(output, history)
            score -= contradictions * 0.15

        return max(0.0, min(1.0, score))

    def _check_relevance(self, output: str, query: str) -> float:
        """检查相关性"""
        if not query:
            return 0.5

        query_words = set(query.lower().split())
        output_words = set(output.lower().split())

        if not query_words:
            return 0.5

        overlap = len(query_words & output_words) / len(query_words)
        return min(1.0, 0.4 + overlap * 0.6)

    def _check_clarity(self, output: str) -> float:
        """检查清晰性"""
        if not output:
            return 0.0

        score = 0.5

        # 段落分明
        if "\n" in output and len(output.split("\n")) > 1:
            score += 0.1

        # 使用标点符号
        if any(p in output for p in ["。", "！", "？", ".", "!", "?"]):
            score += 0.1

        # 长度适中
        if 20 <= len(output) <= 500:
            score += 0.2

        return min(1.0, score)

    def _check_safety(self, output: str) -> float:
        """检查安全性"""
        if not output:
            return 0.0

        score = 1.0

        # 检查危险关键词
        danger_keywords = ["删除所有", "格式化", "破坏", "攻击", "hack"]
        for kw in danger_keywords:
            if kw.lower() in output.lower():
                score -= 0.3

        return max(0.0, min(1.0, score))

    def _calculate_confidence(self, scores: Dict[QualityDimension, float]) -> float:
        """计算信心分数"""
        if not scores:
            return 0.5

        # 基于各维度分数的方差调整信心
        values = list(scores.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)

        # 方差越低，信心越高
        confidence = mean * (1.0 - variance * 0.5)
        return max(0.1, min(1.0, confidence))

    def _detect_issues(self, output: str, scores: Dict[QualityDimension, float]) -> List[Dict]:
        """检测问题"""
        issues = []

        # 准确性低
        if scores.get(QualityDimension.ACCURACY, 1.0) < 0.5:
            issues.append({
                "type": "uncertainty",
                "description": "输出包含较多不确定性表述",
                "severity": "medium"
            })

        # 完整性低
        if scores.get(QualityDimension.COMPLETENESS, 1.0) < 0.5:
            issues.append({
                "type": "incompleteness",
                "description": "输出可能不完整",
                "severity": "medium"
            })

        # 一致性低
        if scores.get(QualityDimension.CONSISTENCY, 1.0) < 0.5:
            issues.append({
                "type": "inconsistency",
                "description": "输出可能与历史不一致",
                "severity": "high"
            })

        # 安全问题
        if scores.get(QualityDimension.SAFETY, 1.0) < 0.7:
            issues.append({
                "type": "safety_concern",
                "description": "输出可能存在安全问题",
                "severity": "high"
            })

        return issues

    def _generate_suggestions(self, evaluation: SelfEvaluation) -> List[str]:
        """生成改进建议"""
        suggestions = []

        for issue in evaluation.issues:
            if issue["type"] == "uncertainty":
                suggestions.append("使用更肯定的表述，减少不确定性词汇")
            elif issue["type"] == "incompleteness":
                suggestions.append("补充更多细节或提供总结")
            elif issue["type"] == "inconsistency":
                suggestions.append("检查与历史对话的一致性")
            elif issue["type"] == "safety_concern":
                suggestions.append("重新评估输出的安全性")

        return suggestions

    def _detect_contradictions(self, output: str, history: List) -> int:
        """检测矛盾"""
        contradictions = 0

        for msg in history:
            if msg.get("role") == "assistant":
                prev_content = msg.get("content", "").lower()
                # 简单矛盾检测：肯定vs否定
                if ("不" in prev_content and "不" not in output.lower()) or \
                   ("是" in prev_content and "不是" in output.lower()):
                    contradictions += 1

        return contradictions

    def _revise_uncertainty(self, output: str) -> str:
        """修正不确定性表述"""
        # 将不确定性表述替换为更肯定的表述
        # 使用占位符避免链式替换
        replacements = [
            ("不确定", "__PLACEHOLDER_1__"),
            ("也许", "应该"),
            ("可能", "很可能"),
            ("或许", "预计"),
            ("应该", "将"),
            ("大概", "大约"),
        ]
        for old, new in replacements:
            output = output.replace(old, new)
        # 替换占位符
        output = output.replace("__PLACEHOLDER_1__", "根据现有信息")
        return output

    def _revise_incompleteness(self, output: str) -> str:
        """修正不完整性"""
        if not output.endswith(("。", "！", "?", ".", "!")):
            output += "。"
        return output

    def _revise_inconsistency(self, output: str) -> str:
        """修正不一致性"""
        # 添加一致性说明
        return f"基于之前的讨论，{output}"

    def _revise_safety(self, output: str) -> str:
        """修正安全问题"""
        # 移除危险表述
        danger_keywords = ["删除所有", "格式化", "破坏", "攻击", "hack"]
        for kw in danger_keywords:
            output = output.replace(kw, "[已过滤]")
        return output

    def _calc_improvement(self, original: str, revised: str) -> float:
        """计算改进分数"""
        if original == revised:
            return 0.0

        # 简单计算差异程度作为改进分数
        orig_len = len(original)
        diff_count = sum(1 for a, b in zip(original, revised) if a != b)
        return min(1.0, diff_count / max(orig_len, 1))

    def get_recent_reflections(self, limit: int = 5) -> List[ReflectionLog]:
        """获取最近的反思记录"""
        return self.reflection_history[-limit:]
