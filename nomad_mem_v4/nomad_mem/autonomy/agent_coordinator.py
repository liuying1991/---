"""
Agent Coordinator - 四代理协调框架

参考项目：Mnemosyne (2025) - https://github.com/rand/mnemosyne

四个专业代理协调工作：
- Orchestrator: 工作队列管理，依赖跟踪，死锁检测
- Optimizer: 上下文预算分配，动态技能发现
- Reviewer: 质量门控，语义验证
- Executor: 工作执行，超时重试，子代理生成
"""
import time
import uuid
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AgentRole(Enum):
    """代理角色"""
    ORCHESTRATOR = "orchestrator"  # 协调器
    OPTIMIZER = "optimizer"        # 优化器
    REVIEWER = "reviewer"          # 审核器
    EXECUTOR = "executor"          # 执行器


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """代理任务"""
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5  # 0=最高，10=最低
    assigned_agent: Optional[AgentRole] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: str = ""
    error: str = ""
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


class Orchestrator:
    """协调器 - 工作队列管理，依赖跟踪，死锁检测"""

    def __init__(self):
        self.work_queue: List[AgentTask] = []
        self.completed_tasks: Dict[str, AgentTask] = {}
        self.deadlock_timeout = 60  # 60秒死锁检测

    def add_task(self, task: AgentTask) -> str:
        """添加任务到工作队列"""
        self.work_queue.append(task)
        self.work_queue.sort(key=lambda t: t.priority)
        return task.id

    def get_next_task(self) -> Optional[AgentTask]:
        """获取下一个可执行任务"""
        for task in self.work_queue:
            if task.status == TaskStatus.PENDING:
                # 检查依赖
                if self._are_dependencies_met(task):
                    return task
        return None

    def complete_task(self, task_id: str, result: str = "", error: str = ""):
        """完成任务"""
        # 从工作队列移除
        self.work_queue = [t for t in self.work_queue if t.id != task_id]

        # 添加到已完成
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
        else:
            task = next((t for t in self.work_queue if t.id == task_id), None)
            if not task:
                return

        task.status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
        task.result = result
        task.error = error
        task.completed_at = time.time()
        self.completed_tasks[task_id] = task

    def detect_deadlock(self) -> List[str]:
        """死锁检测"""
        # 简单循环检测
        pending = [t for t in self.work_queue if t.status == TaskStatus.PENDING]
        circular = []

        for task in pending:
            if self._is_circular_dependency(task, visited=set()):
                circular.append(task.id)

        return circular

    def _are_dependencies_met(self, task: AgentTask) -> bool:
        """检查依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if self.completed_tasks[dep_id].status != TaskStatus.COMPLETED:
                return False
        return True

    def _is_circular_dependency(self, task: AgentTask, visited: set) -> bool:
        """循环依赖检测"""
        if task.id in visited:
            return True
        visited.add(task.id)

        for dep_id in task.dependencies:
            dep_task = next((t for t in self.work_queue if t.id == dep_id), None)
            if dep_task and self._is_circular_dependency(dep_task, visited.copy()):
                return True
        return False


class Optimizer:
    """优化器 - 上下文预算分配，动态技能发现"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.context_budget = {
            "critical": 0.4,  # 关键记忆
            "skills": 0.3,    # 技能上下文
            "project": 0.2,   # 项目信息
            "general": 0.1    # 通用信息
        }

    def allocate_context(self, available_tokens: int) -> Dict[str, int]:
        """分配上下文预算"""
        return {
            category: int(available_tokens * ratio)
            for category, ratio in self.context_budget.items()
        }

    def optimize_task(self, task: AgentTask) -> AgentTask:
        """优化任务"""
        # 根据任务类型调整优先级
        if "critical" in task.description.lower():
            task.priority = min(task.priority, 2)
        elif "background" in task.description.lower():
            task.priority = max(task.priority, 7)

        return task


class Reviewer:
    """审核器 - 质量门控，语义验证"""

    def __init__(self):
        self.quality_gates = [
            "intent_satisfied",
            "no_errors",
            "result_valid"
        ]

    def review_task(self, task: AgentTask) -> Dict[str, bool]:
        """审核任务结果"""
        results = {}

        # 检查意图是否满足
        results["intent_satisfied"] = bool(task.result) and len(task.result) > 0

        # 检查是否有错误
        results["no_errors"] = not bool(task.error)

        # 检查结果有效性
        results["result_valid"] = self._validate_result(task.result)

        return results

    def _validate_result(self, result: str) -> bool:
        """验证结果有效性"""
        if not result:
            return False
        # 检查结果不是错误消息
        error_indicators = ["error:", "exception:", "failed:", "traceback"]
        return not any(indicator in result.lower() for indicator in error_indicators)


class Executor:
    """执行器 - 工作执行，超时重试，子代理生成"""

    def __init__(self):
        self.execution_timeout = 30  # 30秒超时
        self.max_sub_agents = 3

    def execute_task(self, task: AgentTask, executor_fn: Callable) -> str:
        """
        执行任务

        Args:
            task: 要执行的任务
            executor_fn: 执行函数

        Returns:
            执行结果
        """
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        try:
            result = executor_fn(task)
            return result
        except Exception as e:
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                # 重试
                return self.execute_task(task, executor_fn)
            else:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                return f"执行失败: {e}"


class AgentCoordinator:
    """四代理协调器"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.orchestrator = Orchestrator()
        self.optimizer = Optimizer(self.config)
        self.reviewer = Reviewer()
        self.executor = Executor()
        self.task_history: List[AgentTask] = []

    def submit_task(self, title: str, description: str, priority: int = 5,
                   dependencies: List[str] = None) -> str:
        """提交任务"""
        task = AgentTask(
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or []
        )

        # 优化任务
        task = self.optimizer.optimize_task(task)

        # 添加到队列
        return self.orchestrator.add_task(task)

    def execute_cycle(self, executor_fn: Callable) -> List[Dict]:
        """
        执行一个协调周期

        Args:
            executor_fn: 任务执行函数

        Returns:
            执行结果列表
        """
        results = []

        # 死锁检测
        deadlocks = self.orchestrator.detect_deadlock()
        if deadlocks:
            for task_id in deadlocks:
                self.orchestrator.complete_task(task_id, error="死锁检测")
                results.append({"task_id": task_id, "status": "deadlock_resolved"})

        # 执行任务
        while True:
            task = self.orchestrator.get_next_task()
            if not task:
                break

            # 分配角色
            task.assigned_agent = self._assign_role(task)

            # 执行
            result = self.executor.execute_task(task, executor_fn)

            # 审核
            task.result = result
            review_results = self.reviewer.review_task(task)

            if all(review_results.values()):
                self.orchestrator.complete_task(task.id, result=result)
                results.append({
                    "task_id": task.id,
                    "status": "completed",
                    "review": review_results
                })
            else:
                self.orchestrator.complete_task(task.id, error="审核未通过")
                results.append({
                    "task_id": task.id,
                    "status": "review_failed",
                    "review": review_results
                })

        self.task_history.extend(results)
        return results

    def _assign_role(self, task: AgentTask) -> AgentRole:
        """分配代理角色"""
        # 简单规则分配
        if "execute" in task.description.lower() or "run" in task.description.lower():
            return AgentRole.EXECUTOR
        elif "optimize" in task.description.lower():
            return AgentRole.OPTIMIZER
        elif "review" in task.description.lower() or "check" in task.description.lower():
            return AgentRole.REVIEWER
        else:
            return AgentRole.ORCHESTRATOR

    def get_stats(self) -> Dict:
        """获取协调器统计"""
        total_tasks = len(self.task_history)
        completed = sum(1 for r in self.task_history if r.get("status") == "completed")
        failed = total_tasks - completed

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / max(total_tasks, 1),
            "pending_tasks": len([t for t in self.orchestrator.work_queue
                                 if t.status == TaskStatus.PENDING])
        }
