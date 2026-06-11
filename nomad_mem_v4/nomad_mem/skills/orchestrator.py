"""
Skill Orchestrator - 技能编排器

核心能力:
1. 链式调用：多个技能按顺序执行，传递中间结果
2. 条件执行：根据条件决定是否执行某个技能
3. 回退策略：主技能失败时自动尝试备用技能
4. 并行执行：多个独立技能同时执行
5. 结果聚合：合并多个技能的执行结果

参考:
- 工作流引擎设计模式（Airflow/Temporal）
- 函数式编程 Pipeline 模式
- 责任链模式（Chain of Responsibility）
"""
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    CONDITIONAL = "conditional"    # 条件执行
    FALLBACK = "fallback"          # 回退执行


@dataclass
class SkillStep:
    """技能步骤"""
    step_id: str
    skill_name: str
    args: Dict[str, Any] = field(default_factory=dict)
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    condition: Optional[Callable[[Dict], bool]] = None  # 条件函数
    fallback_skill: Optional[str] = None  # 回退技能
    timeout: float = 30.0  # 超时时间（秒）
    retry_count: int = 0
    max_retries: int = 2
    depends_on: List[str] = field(default_factory=list)  # 依赖的步骤ID


@dataclass
class StepResult:
    """步骤执行结果"""
    step_id: str
    skill_name: str
    success: bool
    result: Any = None
    error: str = ""
    execution_time: float = 0.0
    retries_used: int = 0
    was_fallback: bool = False


@dataclass
class ExecutionPlan:
    """执行计划"""
    plan_id: str
    steps: List[SkillStep] = field(default_factory=list)
    results: List[StepResult] = field(default_factory=list)
    status: str = "pending"  # pending/running/completed/failed
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    total_time: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)  # 步骤间共享上下文


class SkillOrchestrator:
    """技能编排器"""

    def __init__(self, skill_registry=None, config: Dict = None):
        """
        初始化技能编排器

        Args:
            skill_registry: SkillRegistry实例
            config: 配置字典
        """
        self.registry = skill_registry
        self.config = config or {}
        self.max_concurrent = self.config.get("max_concurrent", 5)
        self.execution_plans: Dict[str, ExecutionPlan] = {}

    def create_chain(self, skill_chain: List[Dict], context: Dict = None) -> str:
        """
        创建链式执行计划

        Args:
            skill_chain: 技能链配置
                [{"skill": "name", "args": {...}}, ...]
            context: 初始上下文

        Returns:
            plan_id
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        steps = []
        prev_step_id = None

        for item in skill_chain:
            step_id = f"step_{uuid.uuid4().hex[:8]}"
            step = SkillStep(
                step_id=step_id,
                skill_name=item["skill"],
                args=item.get("args", {}),
                mode=item.get("mode", ExecutionMode.SEQUENTIAL),
                condition=item.get("condition"),
                fallback_skill=item.get("fallback"),
                timeout=item.get("timeout", 30.0),
                max_retries=item.get("max_retries", 2),
            )
            if prev_step_id:
                step.depends_on = [prev_step_id]
            steps.append(step)
            prev_step_id = step_id

        plan = ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            context=context or {},
        )
        self.execution_plans[plan_id] = plan
        return plan_id

    def create_parallel(self, skills: List[Dict], context: Dict = None) -> str:
        """
        创建并行执行计划

        Args:
            skills: 技能列表
            context: 初始上下文

        Returns:
            plan_id
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        steps = [
            SkillStep(
                step_id=f"step_{uuid.uuid4().hex[:8]}",
                skill_name=item["skill"],
                args=item.get("args", {}),
                mode=ExecutionMode.PARALLEL,
                timeout=item.get("timeout", 30.0),
            )
            for item in skills
        ]

        plan = ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            context=context or {},
        )
        self.execution_plans[plan_id] = plan
        return plan_id

    def create_conditional(self, condition: Callable, true_steps: List[Dict],
                           false_steps: List[Dict] = None, context: Dict = None) -> str:
        """
        创建条件执行计划

        Args:
            condition: 条件函数
            true_steps: 条件为真时执行的步骤
            false_steps: 条件为假时执行的步骤
            context: 初始上下文

        Returns:
            plan_id
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        steps = []

        # 添加条件步骤
        condition_step = SkillStep(
            step_id=f"cond_{uuid.uuid4().hex[:8]}",
            skill_name="__condition__",
            args={"condition_fn": condition},
            mode=ExecutionMode.CONDITIONAL,
            condition=condition,
        )
        steps.append(condition_step)

        # 添加true分支
        prev_id = condition_step.step_id
        for item in true_steps:
            step_id = f"step_t_{uuid.uuid4().hex[:8]}"
            step = SkillStep(
                step_id=step_id,
                skill_name=item["skill"],
                args=item.get("args", {}),
                depends_on=[prev_id],
            )
            steps.append(step)
            prev_id = step_id

        # 添加false分支
        if false_steps:
            for item in false_steps:
                step_id = f"step_f_{uuid.uuid4().hex[:8]}"
                step = SkillStep(
                    step_id=step_id,
                    skill_name=item["skill"],
                    args=item.get("args", {}),
                    depends_on=[condition_step.step_id],
                )
                # 标记为条件分支（需要运行时判断）
                step.condition = lambda ctx: False  # 默认不执行
                steps.append(step)

        plan = ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            context=context or {},
        )
        self.execution_plans[plan_id] = plan
        return plan_id

    def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        执行计划

        Args:
            plan_id: 计划ID

        Returns:
            执行结果摘要
        """
        if plan_id not in self.execution_plans:
            return {"error": "Plan not found"}

        plan = self.execution_plans[plan_id]
        plan.status = "running"
        plan.started_at = time.time()

        # 按依赖拓扑排序执行
        ordered_steps = self._topological_sort(plan.steps)

        executed_steps = set()
        step_results = {}

        for step in ordered_steps:
            # 检查依赖
            deps_met = all(
                dep_id in executed_steps
                for dep_id in step.depends_on
            )
            if not deps_met:
                # 依赖未满足，跳过
                plan.results.append(StepResult(
                    step_id=step.step_id,
                    skill_name=step.skill_name,
                    success=False,
                    error="Dependencies not met",
                ))
                continue

            # 检查条件
            if step.condition:
                try:
                    if not step.condition(plan.context):
                        plan.results.append(StepResult(
                            step_id=step.step_id,
                            skill_name=step.skill_name,
                            success=True,
                            result="Skipped (condition not met)",
                        ))
                        executed_steps.add(step.step_id)
                        continue
                except Exception:
                    pass

            # 执行步骤
            result = self._execute_step(step, plan.context)
            plan.results.append(result)
            step_results[step.step_id] = result

            if result.success:
                executed_steps.add(step.step_id)
                # 将结果存入上下文
                plan.context[f"result_{step.step_id}"] = result.result
            else:
                # 尝试回退
                if step.fallback_skill:
                    fallback_result = self._execute_fallback(step, plan.context)
                    if fallback_result:
                        plan.results.append(fallback_result)
                        if fallback_result.success:
                            executed_steps.add(step.step_id)
                            plan.context[f"result_{step.step_id}"] = fallback_result.result

        plan.completed_at = time.time()
        plan.total_time = plan.completed_at - plan.started_at

        # 判断整体状态
        all_success = all(r.success for r in plan.results if r.skill_name != "__condition__")
        plan.status = "completed" if all_success else "failed"

        return self._summarize_plan(plan)

    def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """获取计划状态"""
        if plan_id not in self.execution_plans:
            return {"error": "Plan not found"}

        plan = self.execution_plans[plan_id]
        return {
            "plan_id": plan.plan_id,
            "status": plan.status,
            "total_steps": len(plan.steps),
            "completed_steps": sum(1 for r in plan.results if r.success),
            "failed_steps": sum(1 for r in plan.results if not r.success and r.error != "Dependencies not met"),
            "total_time": plan.total_time,
        }

    def _execute_step(self, step: SkillStep, context: Dict) -> StepResult:
        """
        执行单个步骤（带重试）

        Args:
            step: 技能步骤
            context: 上下文

        Returns:
            步骤结果
        """
        if not self.registry:
            return StepResult(
                step_id=step.step_id,
                skill_name=step.skill_name,
                success=False,
                error="No skill registry available",
            )

        skill = self.registry.get_skill(step.skill_name)
        if not skill:
            return StepResult(
                step_id=step.step_id,
                skill_name=step.skill_name,
                success=False,
                error=f"Skill '{step.skill_name}' not found",
            )

        # 合并上下文到参数
        args = {**step.args, "_context": context}

        start_time = time.time()
        last_error = ""

        for attempt in range(step.max_retries + 1):
            try:
                result = skill.execute(args)
                execution_time = time.time() - start_time
                return StepResult(
                    step_id=step.step_id,
                    skill_name=step.skill_name,
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    retries_used=attempt,
                )
            except Exception as e:
                last_error = str(e)
                step.retry_count += 1

        execution_time = time.time() - start_time
        return StepResult(
            step_id=step.step_id,
            skill_name=step.skill_name,
            success=False,
            error=last_error,
            execution_time=execution_time,
            retries_used=step.max_retries,
        )

    def _execute_fallback(self, step: SkillStep, context: Dict) -> Optional[StepResult]:
        """执行回退技能"""
        if not step.fallback_skill or not self.registry:
            return None

        skill = self.registry.get_skill(step.fallback_skill)
        if not skill:
            return None

        args = {**step.args, "_context": context}
        start_time = time.time()

        try:
            result = skill.execute(args)
            return StepResult(
                step_id=step.step_id,
                skill_name=step.fallback_skill,
                success=True,
                result=result,
                execution_time=time.time() - start_time,
                was_fallback=True,
            )
        except Exception as e:
            return StepResult(
                step_id=step.step_id,
                skill_name=step.fallback_skill,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                was_fallback=True,
            )

    def _topological_sort(self, steps: List[SkillStep]) -> List[SkillStep]:
        """拓扑排序"""
        step_map = {s.step_id: s for s in steps}
        in_degree = {s.step_id: 0 for s in steps}

        for step in steps:
            for dep in step.depends_on:
                if dep in in_degree:
                    in_degree[step.step_id] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        ordered = []

        while queue:
            sid = queue.pop(0)
            ordered.append(step_map[sid])

            for step in steps:
                if sid in step.depends_on:
                    in_degree[step.step_id] -= 1
                    if in_degree[step.step_id] == 0:
                        queue.append(step.step_id)

        return ordered

    def _summarize_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """总结执行计划"""
        results = [r for r in plan.results if r.skill_name != "__condition__"]
        return {
            "plan_id": plan.plan_id,
            "status": plan.status,
            "total_steps": len(results),
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "total_time": plan.total_time,
            "results": [
                {
                    "step_id": r.step_id,
                    "skill": r.skill_name,
                    "success": r.success,
                    "error": r.error,
                    "time": r.execution_time,
                    "was_fallback": r.was_fallback,
                }
                for r in results
            ],
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取编排器统计"""
        total_plans = len(self.execution_plans)
        completed = sum(1 for p in self.execution_plans.values() if p.status == "completed")
        failed = sum(1 for p in self.execution_plans.values() if p.status == "failed")

        return {
            "total_plans": total_plans,
            "completed_plans": completed,
            "failed_plans": failed,
            "total_steps_executed": sum(len(p.results) for p in self.execution_plans.values()),
        }
