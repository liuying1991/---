"""
Reflection Engine - 自主反思引擎

让Jarvis具备自我反思能力：
1. 评估自身表现（响应质量、行动效果、目标进度）
2. 识别改进点（失败模式、效率瓶颈、策略偏差）
3. 生成改进建议（具体可执行的建议）
4. 追踪改进效果（建议采纳后是否有效）

核心特性:
- 多维评估: 响应质量/行动效果/目标进度/经验积累
- 深度分析: 模式识别/根因分析/趋势预测
- 可操作建议: 具体、优先级排序、可执行
- 闭环反馈: 追踪建议采纳效果

设计原则:
- 反思不是自责，而是学习
- 基于数据而非感觉
- 建议必须可执行可验证
"""
import time
import sqlite3
import json
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ─── Enums ───────────────────────────────────────────────────────────────────


class EvaluationLevel(Enum):
    """评估等级"""
    EXCELLENT = "excellent"    # 优秀
    GOOD = "good"             # 良好
    ACCEPTABLE = "acceptable" # 可接受
    NEEDS_IMPROVEMENT = "needs_improvement"  # 需改进
    POOR = "poor"             # 差


class ReflectionType(Enum):
    """反思类型"""
    PERFORMANCE = "performance"      # 表现反思
    STRATEGY = "strategy"            # 策略反思
    BEHAVIOR = "behavior"            # 行为反思
    KNOWLEDGE = "knowledge"          # 知识反思
    RELATIONSHIP = "relationship"    # 关系反思


class RecommendationPriority(Enum):
    """建议优先级"""
    CRITICAL = "critical"    # 关键
    HIGH = "high"           # 高
    MEDIUM = "medium"       # 中
    LOW = "low"             # 低


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class Evaluation:
    """评估结果
    Attributes:
        evaluation_id: 评估ID
        dimension: 评估维度
        score: 得分(0.0-1.0)
        level: 评估等级
        evidence: 证据
        timestamp: 评估时间
    """
    evaluation_id: str
    dimension: str
    score: float
    level: str
    evidence: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "evaluation_id": self.evaluation_id,
            "dimension": self.dimension,
            "score": self.score,
            "level": self.level,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }


@dataclass
class Reflection:
    """反思记录
    Attributes:
        reflection_id: 反思ID
        reflection_type: 反思类型
        summary: 反思摘要
        findings: 发现
        root_cause: 根因分析
        triggered_by: 触发原因
        timestamp: 反思时间
    """
    reflection_id: str
    reflection_type: str
    summary: str
    findings: List[str] = field(default_factory=list)
    root_cause: str = ""
    triggered_by: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "reflection_id": self.reflection_id,
            "reflection_type": self.reflection_type,
            "summary": self.summary,
            "findings": self.findings,
            "root_cause": self.root_cause,
            "triggered_by": self.triggered_by,
            "timestamp": self.timestamp,
        }


@dataclass
class Recommendation:
    """改进建议
    Attributes:
        recommendation_id: 建议ID
        title: 建议标题
        description: 详细描述
        priority: 优先级
        reflection_id: 关联反思ID
        category: 建议类别
        expected_impact: 预期影响
        status: 状态
        created_at: 创建时间
        applied_at: 应用时间
    """
    recommendation_id: str
    title: str
    description: str
    priority: str
    reflection_id: str = ""
    category: str = ""
    expected_impact: str = ""
    status: str = "pending"  # pending/applied/rejected/expired
    created_at: float = field(default_factory=time.time)
    applied_at: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "reflection_id": self.reflection_id,
            "category": self.category,
            "expected_impact": self.expected_impact,
            "status": self.status,
            "created_at": self.created_at,
            "applied_at": self.applied_at,
        }


# ─── Reflection Engine ──────────────────────────────────────────────────────


class ReflectionEngine:
    """
    自主反思引擎

    让Jarvis具备自我评估和改进能力：
    1. 评估最近表现
    2. 分析失败模式
    3. 生成改进建议
    4. 追踪改进效果

    使用示例:
        >>> engine = ReflectionEngine()
        >>> evaluations = engine.evaluate_performance(experience_replay, goal_manager)
        >>> reflection = engine.reflect_on_failures(experience_replay, "user1")
        >>> recommendations = engine.generate_recommendations(reflection)
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._persistent_conn = None
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._persistent_conn:
            return self._persistent_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _maybe_close(self, conn):
        if not self._persistent_conn:
            conn.close()

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS evaluations (
                evaluation_id TEXT PRIMARY KEY,
                dimension     TEXT NOT NULL,
                score         REAL NOT NULL,
                level         TEXT NOT NULL,
                evidence      TEXT NOT NULL DEFAULT '',
                timestamp     REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reflections (
                reflection_id   TEXT PRIMARY KEY,
                reflection_type TEXT NOT NULL,
                summary         TEXT NOT NULL,
                findings        TEXT NOT NULL DEFAULT '[]',
                root_cause      TEXT NOT NULL DEFAULT '',
                triggered_by    TEXT NOT NULL DEFAULT '',
                timestamp       REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id TEXT PRIMARY KEY,
                title             TEXT NOT NULL,
                description       TEXT NOT NULL,
                priority          TEXT NOT NULL,
                reflection_id     TEXT NOT NULL DEFAULT '',
                category          TEXT NOT NULL DEFAULT '',
                expected_impact   TEXT NOT NULL DEFAULT '',
                status            TEXT NOT NULL DEFAULT 'pending',
                created_at        REAL NOT NULL,
                applied_at        REAL NOT NULL DEFAULT 0.0
            );

            CREATE INDEX IF NOT EXISTS idx_evaluations_ts ON evaluations(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_reflections_ts ON reflections(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);
        """)
        conn.commit()
        self._maybe_close(conn)

    # ── Evaluate Performance ──────────────────────────────────────────────

    def evaluate_performance(
        self,
        experience_replay=None,
        goal_manager=None,
        autonomous_executor=None,
    ) -> List[Evaluation]:
        """
        评估整体表现

        评估维度:
        - response_quality: 响应质量（基于经验成功率）
        - goal_progress: 目标进度（基于目标完成率）
        - action_effectiveness: 行动效果（基于自主行动成功率）
        - learning_rate: 学习速度（基于经验积累速度）

        Returns:
            评估结果列表
        """
        evaluations = []

        # 1. 响应质量评估
        if experience_replay:
            evaluations.append(
                self._evaluate_response_quality(experience_replay)
            )

        # 2. 目标进度评估
        if goal_manager:
            evaluations.append(
                self._evaluate_goal_progress(goal_manager)
            )

        # 3. 行动效果评估
        if autonomous_executor:
            evaluations.append(
                self._evaluate_action_effectiveness(autonomous_executor)
            )

        # 4. 学习速度评估（如果有经验回放）
        if experience_replay:
            evaluations.append(
                self._evaluate_learning_rate(experience_replay)
            )

        # 持久化
        for e in evaluations:
            self._save_evaluation(e)

        return evaluations

    def _evaluate_response_quality(self, experience_replay) -> Evaluation:
        """评估响应质量"""
        stats = experience_replay.get_stats()
        total = stats.get("total_experiences", 0)
        positive = stats.get("positive_count", 0)
        negative = stats.get("negative_count", 0)

        if total == 0:
            return Evaluation(
                evaluation_id=f"eval_{int(time.time()*1000)}_response",
                dimension="response_quality",
                score=0.0,
                level=EvaluationLevel.POOR.value,
                evidence="无任何经验记录",
            )

        success_rate = positive / total
        failure_rate = negative / total

        # 评分：高成功率=高分，高失败率=低分
        score = success_rate * 0.7 + (1 - failure_rate) * 0.3

        if score >= 0.9:
            level = EvaluationLevel.EXCELLENT.value
        elif score >= 0.7:
            level = EvaluationLevel.GOOD.value
        elif score >= 0.5:
            level = EvaluationLevel.ACCEPTABLE.value
        elif score >= 0.3:
            level = EvaluationLevel.NEEDS_IMPROVEMENT.value
        else:
            level = EvaluationLevel.POOR.value

        return Evaluation(
            evaluation_id=f"eval_{int(time.time()*1000)}_response",
            dimension="response_quality",
            score=round(score, 4),
            level=level,
            evidence=f"成功率{success_rate:.0%}, 失败率{failure_rate:.0%}, 总经验{total}条",
        )

    def _evaluate_goal_progress(self, goal_manager) -> Evaluation:
        """评估目标进度"""
        stats = goal_manager.get_stats()
        completion_rate = stats.get("completion_rate", 0)
        avg_progress = stats.get("avg_progress", 0)

        # 综合评分
        score = completion_rate * 0.6 + avg_progress * 0.4

        if score >= 0.9:
            level = EvaluationLevel.EXCELLENT.value
        elif score >= 0.7:
            level = EvaluationLevel.GOOD.value
        elif score >= 0.5:
            level = EvaluationLevel.ACCEPTABLE.value
        elif score >= 0.3:
            level = EvaluationLevel.NEEDS_IMPROVEMENT.value
        else:
            level = EvaluationLevel.POOR.value

        return Evaluation(
            evaluation_id=f"eval_{int(time.time()*1000)}_goals",
            dimension="goal_progress",
            score=round(score, 4),
            level=level,
            evidence=f"完成率{completion_rate:.0%}, 平均进度{avg_progress:.0%}",
        )

    def _evaluate_action_effectiveness(self, autonomous_executor) -> Evaluation:
        """评估行动效果"""
        stats = autonomous_executor.get_action_stats()
        success_rate = stats.get("success_rate", 0)
        total = stats.get("total_actions", 0)

        if total == 0:
            return Evaluation(
                evaluation_id=f"eval_{int(time.time()*1000)}_actions",
                dimension="action_effectiveness",
                score=0.0,
                level=EvaluationLevel.ACCEPTABLE.value,
                evidence="尚无自主行动记录",
            )

        if success_rate >= 0.9:
            level = EvaluationLevel.EXCELLENT.value
        elif success_rate >= 0.7:
            level = EvaluationLevel.GOOD.value
        elif success_rate >= 0.5:
            level = EvaluationLevel.ACCEPTABLE.value
        elif success_rate >= 0.3:
            level = EvaluationLevel.NEEDS_IMPROVEMENT.value
        else:
            level = EvaluationLevel.POOR.value

        return Evaluation(
            evaluation_id=f"eval_{int(time.time()*1000)}_actions",
            dimension="action_effectiveness",
            score=round(success_rate, 4),
            level=level,
            evidence=f"成功率{success_rate:.0%}, 总行动{total}次",
        )

    def _evaluate_learning_rate(self, experience_replay) -> Evaluation:
        """评估学习速度"""
        stats = experience_replay.get_stats()
        total = stats.get("total_experiences", 0)
        with_lessons = stats.get("with_lessons", 0)

        if total == 0:
            return Evaluation(
                evaluation_id=f"eval_{int(time.time()*1000)}_learning",
                dimension="learning_rate",
                score=0.0,
                level=EvaluationLevel.POOR.value,
                evidence="无经验记录",
            )

        lesson_ratio = with_lessons / total

        if lesson_ratio >= 0.7:
            level = EvaluationLevel.EXCELLENT.value
        elif lesson_ratio >= 0.5:
            level = EvaluationLevel.GOOD.value
        elif lesson_ratio >= 0.3:
            level = EvaluationLevel.ACCEPTABLE.value
        elif lesson_ratio >= 0.1:
            level = EvaluationLevel.NEEDS_IMPROVEMENT.value
        else:
            level = EvaluationLevel.POOR.value

        return Evaluation(
            evaluation_id=f"eval_{int(time.time()*1000)}_learning",
            dimension="learning_rate",
            score=round(lesson_ratio, 4),
            level=level,
            evidence=f"教训记录率{lesson_ratio:.0%}, 总经验{total}条",
        )

    # ── Reflect ───────────────────────────────────────────────────────────

    def reflect_on_failures(
        self,
        experience_replay,
        user_id: str,
    ) -> Optional[Reflection]:
        """
        反思失败经验

        Returns:
            反思记录
        """
        if not experience_replay:
            return None

        # 获取失败经验
        failures = experience_replay.retrieve_by_intent("failed", k=20)
        # 按用户过滤
        failures = [f for f in failures if f.user_id == user_id]

        if not failures:
            return None

        findings = []
        root_causes = []

        # 分析失败模式
        for exp in failures[:10]:
            intent = exp.intent
            action = exp.action_taken
            lesson = exp.lesson_learned

            findings.append(f"意图'{intent}'执行'{action}'失败")
            if lesson:
                root_causes.append(f"{intent}: {lesson}")

        if not findings:
            return None

        reflection = Reflection(
            reflection_id=f"reflection_{int(time.time()*1000)}",
            reflection_type=ReflectionType.PERFORMANCE.value,
            summary=f"分析 {len(failures)} 条失败经验，发现 {len(findings)} 个模式",
            findings=findings,
            root_cause=" | ".join(root_causes[:5]) if root_causes else "未知",
            triggered_by="failure_analysis",
        )

        self._save_reflection(reflection)
        return reflection

    def reflect_on_strategy(
        self,
        evaluations: List[Evaluation],
    ) -> Optional[Reflection]:
        """
        基于评估结果反思策略

        Returns:
            反思记录
        """
        if not evaluations:
            return None

        poor_dims = [e for e in evaluations if e.level in (
            EvaluationLevel.POOR.value,
            EvaluationLevel.NEEDS_IMPROVEMENT.value,
        )]

        if not poor_dims:
            return None

        findings = [f"维度'{e.dimension}'评分{e.score:.2f}({e.level})" for e in poor_dims]
        root_causes = [e.evidence for e in poor_dims]

        reflection = Reflection(
            reflection_id=f"reflection_{int(time.time()*1000)}",
            reflection_type=ReflectionType.STRATEGY.value,
            summary=f"发现 {len(poor_dims)} 个需改进的维度",
            findings=findings,
            root_cause=" | ".join(root_causes[:5]),
            triggered_by="poor_evaluation",
        )

        self._save_reflection(reflection)
        return reflection

    def reflect_on_autonomous_actions(
        self,
        cycle_reports: List[Dict],
    ) -> Optional[Reflection]:
        """
        基于自主循环报告反思

        Returns:
            反思记录
        """
        if not cycle_reports:
            return None

        recent = cycle_reports[:5]
        failed_cycles = [r for r in recent if r.get("actions_failed", 0) > 0]

        if not failed_cycles:
            return None

        findings = []
        for r in failed_cycles:
            findings.append(
                f"循环 {r['cycle_id']}: "
                f"执行{r['actions_executed']}次, "
                f"成功{r['actions_succeeded']}次, "
                f"失败{r['actions_failed']}次"
            )

        reflection = Reflection(
            reflection_id=f"reflection_{int(time.time()*1000)}",
            reflection_type=ReflectionType.BEHAVIOR.value,
            summary=f"最近 {len(recent)} 次循环中有 {len(failed_cycles)} 次出现失败",
            findings=findings,
            root_cause="自主行动成功率不足",
            triggered_by="cycle_failures",
        )

        self._save_reflection(reflection)
        return reflection

    # ── Generate Recommendations ──────────────────────────────────────────

    def generate_recommendations(
        self,
        reflection: Reflection = None,
        evaluations: List[Evaluation] = None,
    ) -> List[Recommendation]:
        """
        基于反思和评估生成改进建议

        Returns:
            建议列表
        """
        recommendations = []

        if reflection:
            recommendations.extend(
                self._generate_from_reflection(reflection)
            )

        if evaluations:
            recommendations.extend(
                self._generate_from_evaluations(evaluations)
            )

        # 去重
        seen = set()
        unique = []
        for r in recommendations:
            if r.title not in seen:
                seen.add(r.title)
                unique.append(r)
                self._save_recommendation(r)

        return unique

    def _generate_from_reflection(self, reflection: Reflection) -> List[Recommendation]:
        """基于反思生成建议"""
        recs = []

        if reflection.reflection_type == ReflectionType.PERFORMANCE.value:
            # 性能反思
            for finding in reflection.findings[:3]:
                recs.append(Recommendation(
                    recommendation_id=f"rec_{int(time.time()*1000)}_{len(recs)}",
                    title=f"改进: {finding[:50]}",
                    description=f"根据反思: {reflection.summary}",
                    priority=RecommendationPriority.HIGH.value,
                    reflection_id=reflection.reflection_id,
                    category="performance",
                    expected_impact="提升响应质量",
                ))

        elif reflection.reflection_type == ReflectionType.STRATEGY.value:
            # 策略反思
            for finding in reflection.findings[:3]:
                recs.append(Recommendation(
                    recommendation_id=f"rec_{int(time.time()*1000)}_{len(recs)}",
                    title=f"策略调整: {finding[:50]}",
                    description=f"根据评估: {reflection.summary}",
                    priority=RecommendationPriority.CRITICAL.value,
                    reflection_id=reflection.reflection_id,
                    category="strategy",
                    expected_impact="改善策略效果",
                ))

        elif reflection.reflection_type == ReflectionType.BEHAVIOR.value:
            # 行为反思
            recs.append(Recommendation(
                recommendation_id=f"rec_{int(time.time()*1000)}_behavior",
                title="降低自主执行级别",
                description=f"原因: {reflection.summary}",
                priority=RecommendationPriority.CRITICAL.value,
                reflection_id=reflection.reflection_id,
                category="behavior",
                expected_impact="减少自主行动失败",
            ))

        return recs

    def _generate_from_evaluations(self, evaluations: List[Evaluation]) -> List[Recommendation]:
        """基于评估生成建议"""
        recs = []

        for e in evaluations:
            if e.score < 0.5:
                recs.append(Recommendation(
                    recommendation_id=f"rec_{int(time.time()*1000)}_eval_{e.dimension}",
                    title=f"提升{e.dimension}维度表现",
                    description=f"当前评分{e.score:.2f}({e.level}), {e.evidence}",
                    priority=RecommendationPriority.CRITICAL.value,
                    category=f"eval_{e.dimension}",
                    expected_impact=f"提升{e.dimension}评分",
                ))
            elif e.score < 0.7:
                recs.append(Recommendation(
                    recommendation_id=f"rec_{int(time.time()*1000)}_eval_{e.dimension}",
                    title=f"优化{e.dimension}维度",
                    description=f"当前评分{e.score:.2f}({e.level}), {e.evidence}",
                    priority=RecommendationPriority.MEDIUM.value,
                    category=f"eval_{e.dimension}",
                    expected_impact=f"优化{e.dimension}评分",
                ))

        return recs

    # ── Track Recommendations ─────────────────────────────────────────────

    def apply_recommendation(self, recommendation_id: str) -> bool:
        """标记建议为已应用"""
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE recommendations SET status = 'applied', applied_at = ? WHERE recommendation_id = ?",
            (time.time(), recommendation_id),
        )
        conn.commit()
        self._maybe_close(conn)
        return cursor.rowcount > 0

    def reject_recommendation(self, recommendation_id: str) -> bool:
        """标记建议为已拒绝"""
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE recommendations SET status = 'rejected' WHERE recommendation_id = ?",
            (recommendation_id,),
        )
        conn.commit()
        self._maybe_close(conn)
        return cursor.rowcount > 0

    def get_pending_recommendations(self) -> List[Dict]:
        """获取待处理建议"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM recommendations
            WHERE status = 'pending'
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END"""
        ).fetchall()
        self._maybe_close(conn)
        return [dict(r) for r in rows]

    # ── Persistence ───────────────────────────────────────────────────────

    def _save_evaluation(self, evaluation: Evaluation):
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO evaluations
            (evaluation_id, dimension, score, level, evidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                evaluation.evaluation_id, evaluation.dimension,
                evaluation.score, evaluation.level,
                evaluation.evidence, evaluation.timestamp,
            ),
        )
        conn.commit()
        self._maybe_close(conn)

    def _save_reflection(self, reflection: Reflection):
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO reflections
            (reflection_id, reflection_type, summary, findings, root_cause, triggered_by, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                reflection.reflection_id, reflection.reflection_type,
                reflection.summary, json.dumps(reflection.findings, ensure_ascii=False),
                reflection.root_cause, reflection.triggered_by,
                reflection.timestamp,
            ),
        )
        conn.commit()
        self._maybe_close(conn)

    def _save_recommendation(self, recommendation: Recommendation):
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO recommendations
            (recommendation_id, title, description, priority, reflection_id,
             category, expected_impact, status, created_at, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                recommendation.recommendation_id, recommendation.title,
                recommendation.description, recommendation.priority,
                recommendation.reflection_id, recommendation.category,
                recommendation.expected_impact, recommendation.status,
                recommendation.created_at, recommendation.applied_at,
            ),
        )
        conn.commit()
        self._maybe_close(conn)

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_evaluation_history(self, k: int = 10) -> List[Dict]:
        """获取评估历史"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM evaluations
            ORDER BY timestamp DESC LIMIT ?""",
            (k,),
        ).fetchall()
        self._maybe_close(conn)
        return [dict(r) for r in rows]

    def get_reflection_history(self, k: int = 10) -> List[Dict]:
        """获取反思历史"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM reflections
            ORDER BY timestamp DESC LIMIT ?""",
            (k,),
        ).fetchall()
        self._maybe_close(conn)
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        """获取系统统计"""
        conn = self._get_conn()

        eval_stats = conn.execute(
            "SELECT COUNT(*) as total, AVG(score) as avg_score FROM evaluations"
        ).fetchone()

        reflection_stats = conn.execute(
            "SELECT COUNT(*) as total FROM reflections"
        ).fetchone()

        rec_stats = conn.execute(
            """SELECT COUNT(*) as total,
               SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status='applied' THEN 1 ELSE 0 END) as applied,
               SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) as rejected
               FROM recommendations"""
        ).fetchone()

        self._maybe_close(conn)

        return {
            "total_evaluations": eval_stats["total"] or 0,
            "avg_evaluation_score": round(eval_stats["avg_score"] or 0.0, 4),
            "total_reflections": reflection_stats["total"] or 0,
            "total_recommendations": rec_stats["total"] or 0,
            "pending_recommendations": rec_stats["pending"] or 0,
            "applied_recommendations": rec_stats["applied"] or 0,
            "rejected_recommendations": rec_stats["rejected"] or 0,
        }

    def close(self):
        if self._persistent_conn:
            self._persistent_conn.close()
            self._persistent_conn = None
