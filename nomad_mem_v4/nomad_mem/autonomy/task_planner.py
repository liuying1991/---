"""
Task Planner - 任务规划器

核心能力:
1. 任务分解：将复杂任务分解为可执行的子任务
2. 依赖图：构建任务依赖关系，确定执行顺序
3. 执行计划：生成有序的执行计划
4. 动态调整：根据执行结果调整计划
5. 并行优化：识别可并行执行的任务

参考:
- DAG任务调度理论
- 项目关键路径方法(CPM)
- 工作流引擎设计模式
"""
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    READY = "ready"       # 依赖已满足，可执行
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"   # 被跳过（依赖失败）


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SubTask:
    """子任务"""
    task_id: str
    title: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    estimated_steps: int = 1
    actual_steps: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskPlanner:
    """任务规划器"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_parallel = self.config.get("max_parallel", 3)
        self.plans: Dict[str, List[SubTask]] = {}  # plan_id -> tasks
        self.execution_history: List[Dict] = []

    def decompose_task(
        self,
        task_description: str,
        complexity: int = 3,
        context: Dict = None
    ) -> str:
        """
        分解复杂任务为子任务

        Args:
            task_description: 任务描述
            complexity: 复杂度(1-5)，决定分解深度
            context: 任务上下文

        Returns:
            plan_id
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        subtasks = self._generate_subtasks(task_description, complexity, context)
        self.plans[plan_id] = subtasks
        return plan_id

    def get_execution_order(self, plan_id: str) -> List[str]:
        """
        获取任务执行顺序（拓扑排序）

        Args:
            plan_id: 计划ID

        Returns:
            按依赖排序的任务ID列表
        """
        if plan_id not in self.plans:
            return []

        tasks = self.plans[plan_id]
        task_map = {t.task_id: t for t in tasks}

        # Kahn算法拓扑排序
        in_degree = {t.task_id: 0 for t in tasks}
        for task in tasks:
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.task_id] += 1

        # 入度为0的任务先执行
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        # 按优先级排序
        queue.sort(key=lambda tid: task_map[tid].priority.value, reverse=True)

        order = []
        while queue:
            tid = queue.pop(0)
            order.append(tid)

            # 更新依赖此任务的下游任务
            for task in tasks:
                if tid in task.dependencies:
                    in_degree[task.task_id] -= 1
                    if in_degree[task.task_id] == 0:
                        queue.append(task.task_id)
                        queue.sort(key=lambda t: task_map[t].priority.value, reverse=True)

        return order

    def get_ready_tasks(self, plan_id: str) -> List[SubTask]:
        """
        获取可执行的任务（依赖已满足）

        Args:
            plan_id: 计划ID

        Returns:
            可执行的任务列表
        """
        if plan_id not in self.plans:
            return []

        tasks = self.plans[plan_id]
        task_map = {t.task_id: t for t in tasks}
        ready = []

        for task in tasks:
            if task.status != TaskStatus.PENDING:
                continue

            # 检查依赖
            deps_met = all(
                task_map[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
                if dep in task_map
            )
            if deps_met:
                ready.append(task)

        # 按优先级排序
        ready.sort(key=lambda t: t.priority.value, reverse=True)
        return ready[:self.max_parallel]

    def mark_task_completed(self, plan_id: str, task_id: str, result: Any = None):
        """
        标记任务完成

        Args:
            plan_id: 计划ID
            task_id: 任务ID
            result: 任务结果
        """
        if plan_id not in self.plans:
            return

        for task in self.plans[plan_id]:
            if task.task_id == task_id:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = time.time()
                task.actual_steps += 1

                self.execution_history.append({
                    "plan_id": plan_id,
                    "task_id": task_id,
                    "status": "completed",
                    "timestamp": time.time(),
                })
                break

    def mark_task_failed(self, plan_id: str, task_id: str, error: str = ""):
        """
        标记任务失败

        Args:
            plan_id: 计划ID
            task_id: 任务ID
            error: 错误信息
        """
        if plan_id not in self.plans:
            return

        for task in self.plans[plan_id]:
            if task.task_id == task_id:
                task.status = TaskStatus.FAILED
                task.error = error
                task.completed_at = time.time()
                task.actual_steps += 1

                # 标记依赖此任务的下游任务为SKIPPED
                for downstream in self.plans[plan_id]:
                    if task_id in downstream.dependencies:
                        downstream.status = TaskStatus.SKIPPED
                        downstream.error = f"依赖任务 {task_id} 失败"

                self.execution_history.append({
                    "plan_id": plan_id,
                    "task_id": task_id,
                    "status": "failed",
                    "error": error,
                    "timestamp": time.time(),
                })
                break

    def mark_task_running(self, plan_id: str, task_id: str):
        """标记任务开始执行"""
        if plan_id not in self.plans:
            return

        for task in self.plans[plan_id]:
            if task.task_id == task_id:
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                task.actual_steps += 1
                break

    def get_plan_progress(self, plan_id: str) -> Dict[str, Any]:
        """
        获取计划进度

        Args:
            plan_id: 计划ID

        Returns:
            进度信息
        """
        if plan_id not in self.plans:
            return {"progress": 0.0, "total": 0}

        tasks = self.plans[plan_id]
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        running = sum(1 for t in tasks if t.status == TaskStatus.RUNNING)

        return {
            "progress": completed / total if total > 0 else 0.0,
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total - completed - failed - running,
        }

    def is_plan_complete(self, plan_id: str) -> bool:
        """检查计划是否完成（所有任务完成或跳过）"""
        if plan_id not in self.plans:
            return False

        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for t in self.plans[plan_id]
        )

    def has_failed_tasks(self, plan_id: str) -> bool:
        """检查计划是否有失败任务"""
        if plan_id not in self.plans:
            return False

        return any(t.status == TaskStatus.FAILED for t in self.plans[plan_id])

    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        """获取计划摘要"""
        if plan_id not in self.plans:
            return {}

        tasks = self.plans[plan_id]
        return {
            "plan_id": plan_id,
            "total_tasks": len(tasks),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.name,
                    "dependencies": t.dependencies,
                }
                for t in tasks
            ],
            "progress": self.get_plan_progress(plan_id),
        }

    def get_parallel_groups(self, plan_id: str) -> List[List[str]]:
        """
        获取可并行执行的任务组

        Args:
            plan_id: 计划ID

        Returns:
            任务组列表，每组内的任务可并行执行
        """
        if plan_id not in self.plans:
            return []

        tasks = self.plans[plan_id]
        task_map = {t.task_id: t for t in tasks}

        # 计算每个任务的最早开始时间（层级）
        levels: Dict[str, int] = {}

        def get_level(task_id: str) -> int:
            if task_id in levels:
                return levels[task_id]
            task = task_map.get(task_id)
            if not task or not task.dependencies:
                levels[task_id] = 0
                return 0
            level = max(get_level(dep) for dep in task.dependencies if dep in task_map) + 1
            levels[task_id] = level
            return level

        for task in tasks:
            get_level(task.task_id)

        # 按层级分组
        max_level = max(levels.values()) if levels else 0
        groups = [[] for _ in range(max_level + 1)]
        for task_id, level in levels.items():
            groups[level].append(task_id)

        return [g for g in groups if g]

    def _generate_subtasks(
        self, task_description: str, complexity: int, context: Dict = None
    ) -> List[SubTask]:
        """
        生成子任务（基于规则分解）

        Args:
            task_description: 任务描述
            complexity: 复杂度
            context: 上下文

        Returns:
            子任务列表
        """
        tasks = []

        # 根据复杂度决定分解策略
        if complexity <= 2:
            # 简单任务：单步执行
            tasks.append(SubTask(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                title="执行任务",
                description=task_description,
            ))
        elif complexity <= 3:
            # 中等任务：分析→执行→验证
            task_ids = []
            for title, desc in [
                ("分析需求", f"分析任务: {task_description}"),
                ("执行操作", f"执行: {task_description}"),
                ("验证结果", f"验证执行结果"),
            ]:
                tid = f"task_{uuid.uuid4().hex[:8]}"
                deps = [task_ids[-1]] if task_ids else []
                task_ids.append(tid)
                tasks.append(SubTask(
                    task_id=tid,
                    title=title,
                    description=desc,
                    dependencies=deps,
                ))
        else:
            # 复杂任务：理解→规划→分解→执行→测试→总结
            task_ids = []
            steps = [
                ("理解需求", f"深入理解: {task_description}"),
                ("制定计划", "制定执行计划和方案"),
                ("分解任务", "将计划分解为可执行步骤"),
                ("执行核心", "执行核心任务"),
                ("测试验证", "测试和验证结果"),
                ("总结报告", "生成总结报告"),
            ]
            for title, desc in steps:
                tid = f"task_{uuid.uuid4().hex[:8]}"
                deps = [task_ids[-1]] if task_ids else []
                task_ids.append(tid)
                tasks.append(SubTask(
                    task_id=tid,
                    title=title,
                    description=desc,
                    priority=TaskPriority.HIGH if title in ["执行核心", "测试验证"] else TaskPriority.MEDIUM,
                ))

        return tasks
