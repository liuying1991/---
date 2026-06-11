"""
Experience Summarizer - 经验摘要引擎

从经验回放系统中提取洞察，生成可读的经验摘要报告。

核心特性:
- 经验摘要: 按时间段/用户/意图聚合经验
- 教训提取: 从失败经验中提炼可操作建议
- 趋势分析: 跟踪经验质量随时间的变化
- 建议生成: 基于历史模式生成改进建议

设计原则:
- 摘要应简洁、可操作、面向用户
- 教训应从具体经验中泛化，但不过度泛化
- 建议应基于数据，而非猜测
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ExperienceSummary:
    """经验摘要

    Attributes:
        title: 摘要标题
        period: 时间段描述
        total_experiences: 经验总数
        positive_rate: 正面经验比例
        top_intents: 高频意图列表
        key_lessons: 关键教训列表
        suggestions: 改进建议列表
        generated_at: 生成时间戳
    """
    title: str
    period: str
    total_experiences: int
    positive_rate: float
    top_intents: List[Dict[str, Any]] = field(default_factory=list)
    key_lessons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        from dataclasses import asdict
        return asdict(self)


class ExperienceSummarizer:
    """
    经验摘要引擎

    从经验回放系统中生成可读的摘要报告。

    使用示例:
        >>> summarizer = ExperienceSummarizer(experience_replay)
        >>> summary = summarizer.generate_user_summary("user1")
        >>> print(summary.title)
        >>> print(summary.key_lessons)
    """

    def __init__(self, experience_replay=None):
        self.replay = experience_replay

    def generate_user_summary(self, user_id: str, period: str = "全部") -> ExperienceSummary:
        """
        生成用户的经验摘要

        Args:
            user_id: 用户ID
            period: 时间段描述

        Returns:
            ExperienceSummary: 用户经验摘要
        """
        if not self.replay:
            return ExperienceSummary(
                title="经验摘要",
                period=period,
                total_experiences=0,
                positive_rate=0.0,
            )

        stats = self.replay.get_user_stats(user_id)
        top_intents = self.replay.get_top_intents()
        lessons = self.replay.retrieve_lessons(k=5)

        # 生成建议
        suggestions = self._generate_suggestions(stats, top_intents, lessons)

        return ExperienceSummary(
            title=f"{user_id} 的经验摘要",
            period=period,
            total_experiences=stats["total_experiences"],
            positive_rate=stats["positive_rate"],
            top_intents=[{"intent": intent, "count": count} for intent, count in top_intents[:5]],
            key_lessons=lessons,
            suggestions=suggestions,
        )

    def generate_system_summary(self) -> ExperienceSummary:
        """
        生成系统整体经验摘要

        Returns:
            ExperienceSummary: 系统经验摘要
        """
        if not self.replay:
            return ExperienceSummary(
                title="系统经验摘要",
                period="全部",
                total_experiences=0,
                positive_rate=0.0,
            )

        stats = self.replay.get_stats()
        top_intents = self.replay.get_top_intents()
        lessons = self.replay.retrieve_lessons(k=5)
        suggestions = self._generate_suggestions(stats, top_intents, lessons)

        return ExperienceSummary(
            title="系统经验摘要",
            period="全部",
            total_experiences=stats["total_experiences"],
            positive_rate=stats["positive_rate"],
            top_intents=[{"intent": intent, "count": count} for intent, count in top_intents[:5]],
            key_lessons=lessons,
            suggestions=suggestions,
        )

    def generate_failure_analysis(self) -> Dict[str, Any]:
        """
        生成失败经验分析报告

        Returns:
            分析报告字典
        """
        if not self.replay:
            return {"error": "Experience replay not available"}

        failures = self.replay.retrieve_recent_failures(k=20)
        if not failures:
            return {
                "total_failures": 0,
                "analysis": "暂无失败经验记录",
                "recommendations": [],
            }

        # 按意图分组统计
        intent_failures = {}
        for f in failures:
            intent_failures.setdefault(f.intent, []).append(f)

        analysis = {
            "total_failures": len(failures),
            "top_failure_intents": [
                {"intent": intent, "count": len(exps)}
                for intent, exps in sorted(intent_failures.items(), key=lambda x: -len(x[1]))[:5]
            ],
            "recent_lessons": [f.lesson_learned for f in failures[:5] if f.lesson_learned],
        }

        return analysis

    def _generate_suggestions(
        self, stats: Dict, top_intents: List, lessons: List[str]
    ) -> List[str]:
        """基于统计数据生成改进建议"""
        suggestions = []

        total = stats.get("total_experiences", 0)
        if total == 0:
            return ["开始记录交互经验，以便系统能够从历史中学习"]

        positive_rate = stats.get("positive_rate", 0)
        if positive_rate < 0.5:
            suggestions.append("正面经验比例较低，建议重点改进常见失败场景的处理")
        elif positive_rate > 0.9:
            suggestions.append("经验质量很高，继续保持当前服务水平")

        if total > 10:
            suggestions.append(f"已积累 {total} 条经验，建议定期回顾教训以持续改进")

        if top_intents:
            top_intent = top_intents[0]
            suggestions.append(f"最常见的交互意图是 '{top_intent[0]}'（{top_intent[1]}次），确保此场景的处理最优")

        if lessons:
            suggestions.append(f"已提取 {len(lessons)} 条教训，建议在类似场景中参考这些经验")

        return suggestions
