"""自主决策引擎 - 独立决策、目标分解和策略选择。"""
from __future__ import annotations

import time
import uuid
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DecisionType(Enum):
    """决策类型"""
    ACTION = "action"
    PLAN = "plan"
    RESPONSE = "response"
    PRIORITY = "priority"
    STRATEGY = "strategy"


@dataclass
class DecisionRecord:
    """决策记录"""
    decision_id: str
    decision_type: DecisionType
    context: Dict[str, Any]
    decision_made: Any
    reasoning: str
    confidence: float  # 0-1
    timestamp: float
    outcome: Optional[Dict[str, Any]] = None  # Set when outcome is recorded


@dataclass
class Goal:
    """目标"""
    goal_id: str
    description: str
    priority: int  # 1-10, higher = more important
    sub_goals: List[str]
    status: str  # "active", "completed", "abandoned"
    created_at: float
    completed_at: Optional[float] = None


@dataclass
class StrategyOption:
    """策略选项"""
    strategy_id: str
    name: str
    description: str
    pros: List[str]
    cons: List[str]
    estimated_success: float  # 0-1


class AutonomousDecider:
    """
    自主决策引擎。

    基于目标导向的决策机制：分解复杂目标为可执行步骤，评估策略选项，
    追踪决策结果以优化未来决策。
    """

    def __init__(self):
        self._goals: Dict[str, Goal] = {}
        self._decisions: List[DecisionRecord] = []
        self._outcome_history: Dict[str, Dict] = {}  # decision_id -> outcome
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  目标管理
    # ------------------------------------------------------------------ #

    def set_goal(
        self,
        description: str,
        priority: int = 5,
        sub_goals: Optional[List[str]] = None,
    ) -> str:
        """设置一个目标，返回 goal_id。"""
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        now = time.time()
        goal = Goal(
            goal_id=goal_id,
            description=description,
            priority=max(1, min(10, priority)),
            sub_goals=sub_goals or [],
            status="active",
            created_at=now,
        )
        with self._lock:
            self._goals[goal_id] = goal
        return goal_id

    def decompose_goal(self, goal_id: str) -> List[str]:
        """将目标分解为子目标，返回子目标的 ID 列表。

        如果目标已有子目标则直接返回，否则自动生成合理的分解。
        """
        with self._lock:
            goal = self._goals.get(goal_id)
            if goal is None:
                return []

            if goal.sub_goals:
                return list(goal.sub_goals)

            # 自动分解：将目标描述拆分为标准步骤
            raw = goal.description.strip()
            sub_ids: List[str] = []
            default_steps = [
                f"[{goal_id}] 分析需求: {raw}",
                f"[{goal_id}] 制定方案",
                f"[{goal_id}] 执行方案",
                f"[{goal_id}] 验证结果",
            ]
            for step in default_steps:
                sid = f"sub_{uuid.uuid4().hex[:8]}"
                goal.sub_goals.append(sid)
                sub_ids.append(sid)
                # 将子目标也记录为独立 Goal
                self._goals[sid] = Goal(
                    goal_id=sid,
                    description=step,
                    priority=goal.priority,
                    sub_goals=[],
                    status="active",
                    created_at=time.time(),
                )

            return sub_ids

    def get_active_goals(self) -> List[Goal]:
        """获取所有活跃目标。"""
        with self._lock:
            return [
                g for g in self._goals.values() if g.status == "active"
            ]

    def complete_goal(self, goal_id: str) -> bool:
        """标记目标为已完成。"""
        with self._lock:
            goal = self._goals.get(goal_id)
            if goal is None:
                return False
            goal.status = "completed"
            goal.completed_at = time.time()
            return True

    # ------------------------------------------------------------------ #
    #  决策制定
    # ------------------------------------------------------------------ #

    def make_decision(
        self,
        context: Dict[str, Any],
        decision_type: DecisionType,
        options: Optional[List[Any]] = None,
    ) -> DecisionRecord:
        """基于上下文做出决策。"""
        decision_id = f"dec_{uuid.uuid4().hex[:8]}"
        now = time.time()

        # 根据决策类型和可用选项生成决策
        decision_made = self._resolve_decision(decision_type, options, context)
        reasoning = self._generate_reasoning(decision_type, options, context)
        confidence = self._calculate_confidence(options, context)

        record = DecisionRecord(
            decision_id=decision_id,
            decision_type=decision_type,
            context=dict(context),
            decision_made=decision_made,
            reasoning=reasoning,
            confidence=confidence,
            timestamp=now,
        )
        with self._lock:
            self._decisions.append(record)
        return record

    def _resolve_decision(
        self,
        decision_type: DecisionType,
        options: Optional[List[Any]],
        context: Dict[str, Any],
    ) -> Any:
        """解析并生成最终决策。"""
        if options is None or len(options) == 0:
            if decision_type == DecisionType.ACTION:
                return {"action": "noop", "reason": "no options available"}
            return None

        # 简单策略：如果有评分的 StrategyOption，选择评分最高的
        if isinstance(options[0], StrategyOption):
            best = max(options, key=lambda o: o.estimated_success)
            return {"strategy": best.name, "strategy_id": best.strategy_id}

        # 默认选择第一个选项
        return options[0]

    def _generate_reasoning(
        self,
        decision_type: DecisionType,
        options: Optional[List[Any]],
        context: Dict[str, Any],
    ) -> str:
        """生成决策推理说明。"""
        if options is None or len(options) == 0:
            return "无可选项，采用默认决策"

        opt_count = len(options)
        if isinstance(options[0], StrategyOption):
            best = max(options, key=lambda o: o.estimated_success)
            return (
                f"在 {opt_count} 个策略选项中，选择 '{best.name}' "
                f"(成功率 {best.estimated_success:.0%})，"
                f"优势: {'; '.join(best.pros[:2])}"
            )
        return f"在 {opt_count} 个选项中做出{decision_type.value}类型决策"

    def _calculate_confidence(
        self,
        options: Optional[List[Any]],
        context: Dict[str, Any],
    ) -> float:
        """计算决策置信度 (0-1)。"""
        if options is None or len(options) == 0:
            return 0.1

        if isinstance(options[0], StrategyOption):
            best = max(options, key=lambda o: o.estimated_success)
            # 基于最优策略的成功率，加上选项数量的信息增益
            base = best.estimated_success
            bonus = min(0.15, len(options) * 0.02)
            return min(1.0, base + bonus)

        # 选项越多置信度越高（有更多选择意味着更多确定性）
        return min(0.8, 0.3 + len(options) * 0.05)

    # ------------------------------------------------------------------ #
    #  策略评估
    # ------------------------------------------------------------------ #

    def evaluate_options(
        self, options: List[Dict[str, Any]]
    ) -> List[StrategyOption]:
        """评估并给策略选项打分。

        每个选项 dict 应包含: name, description, pros (list), cons (list)
        可选项: estimated_success (覆盖自动计算)
        """
        result: List[StrategyOption] = []
        for i, opt in enumerate(options):
            name = opt.get("name", f"option_{i}")
            description = opt.get("description", "")
            pros = opt.get("pros", [])
            cons = opt.get("cons", [])

            if "estimated_success" in opt:
                score = max(0.0, min(1.0, opt["estimated_success"]))
            else:
                # 基于 pros/cons 数量简单估算
                p_count = len(pros)
                c_count = len(cons)
                total = p_count + c_count
                if total == 0:
                    score = 0.5
                else:
                    score = max(0.1, min(0.95, p_count / total))

            strategy = StrategyOption(
                strategy_id=f"strat_{uuid.uuid4().hex[:8]}",
                name=name,
                description=description,
                pros=pros,
                cons=cons,
                estimated_success=score,
            )
            result.append(strategy)
        return result

    # ------------------------------------------------------------------ #
    #  结果追踪
    # ------------------------------------------------------------------ #

    def record_outcome(
        self, decision_id: str, success: bool, result: Any
    ) -> bool:
        """记录决策的结果。"""
        with self._lock:
            # 找到对应的决策记录并更新
            found = False
            for record in self._decisions:
                if record.decision_id == decision_id:
                    record.outcome = {
                        "success": success,
                        "result": result,
                        "recorded_at": time.time(),
                    }
                    found = True
                    break

            if found:
                self._outcome_history[decision_id] = {
                    "success": success,
                    "result": result,
                }
            return found

    # ------------------------------------------------------------------ #
    #  查询
    # ------------------------------------------------------------------ #

    def get_decision_history(self, limit: int = 20) -> List[DecisionRecord]:
        """获取决策历史记录。"""
        with self._lock:
            return list(self._decisions[-limit:])

    def get_stats(self) -> Dict:
        """获取统计信息。"""
        with self._lock:
            total_goals = len(self._goals)
            completed_goals = sum(
                1 for g in self._goals.values() if g.status == "completed"
            )
            total_decisions = len(self._decisions)
            successful = sum(
                1 for o in self._outcome_history.values() if o.get("success")
            )
            total_outcomes = len(self._outcome_history)
            success_rate = (
                successful / total_outcomes if total_outcomes > 0 else 0.0
            )
            avg_confidence = (
                sum(d.confidence for d in self._decisions) / total_decisions
                if total_decisions > 0
                else 0.0
            )
            return {
                "total_goals": total_goals,
                "completed_goals": completed_goals,
                "total_decisions": total_decisions,
                "total_outcomes": total_outcomes,
                "success_rate": success_rate,
                "avg_confidence": avg_confidence,
            }

    def close(self) -> None:
        """清理资源。"""
        with self._lock:
            self._goals.clear()
            self._decisions.clear()
            self._outcome_history.clear()
