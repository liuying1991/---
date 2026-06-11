"""
自主调度器模块

为 Jarvis 提供后台任务的自主调度能力——在正确的时间做正确的事，无需被要求。

核心组件:
- TaskStatus: 任务状态枚举
- TriggerType: 触发类型枚举
- ScheduledTask: 调度任务数据类
- AutonomousScheduler: 自主调度器主类

特性:
- 基于 SQLite 的持久化存储
- 线程安全（并发锁保护）
- 后台线程执行（不阻塞调度器）
- 多种触发类型支持（定时、CRON、条件、单次、周期）
- 优先级排序执行
- 执行历史追踪
"""
import sqlite3
import threading
import logging
import json
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, List, Any
from contextlib import contextmanager
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TriggerType(Enum):
    """触发类型"""
    TIME_INTERVAL = "time_interval"      # 固定时间间隔
    CRON = "cron"                        # CRON 表达式
    CONDITION = "condition"              # 条件触发
    ONCE = "once"                        # 单次触发
    PERIODIC = "periodic"                # 周期性触发


@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    name: str
    description: str
    trigger_type: str  # TriggerType 的 value
    trigger_config: Dict[str, Any]
    action: str        # 可序列化的 action 标识符
    action_params: Dict[str, Any] = field(default_factory=dict)
    status: str = TaskStatus.PENDING.value
    created_at: str = ""
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    run_count: int = 0
    max_runs: int = 0    # 0 = 无限
    priority: int = 5    # 1-10

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class AutonomousScheduler:
    """
    自主调度器

    设计原则:
    - 任务在后台线程中执行（不阻塞调度器）
    - 跟踪执行历史以便调试
    - 支持多种触发类型（时间、类 CRON、条件）
    - 多任务到期时按优先级执行
    - 基于 SQLite 持久化，线程安全
    """

    def __init__(self, db_path: str = ":memory:", action_registry: Optional[Dict[str, Callable]] = None):
        self._db_path = db_path
        self._lock = threading.RLock()
        self._action_registry = action_registry or {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._running_tasks: Dict[str, threading.Thread] = {}
        # Use a single shared connection for persistence (critical for :memory:)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """获取共享数据库连接（线程安全由 _lock 保证）"""
        yield self._conn

    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    trigger_type TEXT NOT NULL,
                    trigger_config TEXT NOT NULL,
                    action TEXT NOT NULL,
                    action_params TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    next_run TEXT,
                    last_run TEXT,
                    run_count INTEGER NOT NULL DEFAULT 0,
                    max_runs INTEGER NOT NULL DEFAULT 0,
                    priority INTEGER NOT NULL DEFAULT 5
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(task_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON scheduled_tasks(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_next_run ON scheduled_tasks(next_run)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_task_id ON task_history(task_id)
            """)
            conn.commit()

    def _row_to_task(self, row: sqlite3.Row) -> ScheduledTask:
        """将数据库行转换为 ScheduledTask"""
        return ScheduledTask(
            task_id=row["task_id"],
            name=row["name"],
            description=row["description"],
            trigger_type=row["trigger_type"],
            trigger_config=json.loads(row["trigger_config"]),
            action=row["action"],
            action_params=json.loads(row["action_params"]),
            status=row["status"],
            created_at=row["created_at"],
            next_run=row["next_run"],
            last_run=row["last_run"],
            run_count=row["run_count"],
            max_runs=row["max_runs"],
            priority=row["priority"],
        )

    def schedule_task(
        self,
        name: str,
        description: str,
        trigger_type: TriggerType,
        trigger_config: Dict[str, Any],
        action: str,
        action_params: Optional[Dict[str, Any]] = None,
        max_runs: int = 0,
        priority: int = 5,
    ) -> str:
        """
        调度一个新任务。

        Args:
            name: 任务名称
            description: 任务描述
            trigger_type: 触发类型
            trigger_config: 触发配置
                - TIME_INTERVAL: {"interval_seconds": X}
                - CRON: {"cron_expression": "*/5 * * * *"}
                - CONDITION: {"condition": "user_inactive_2h"}
                - ONCE: {"run_at": "2026-06-11T10:00:00"}
                - PERIODIC: {"interval_seconds": X, "max_runs": Y}
            action: 要执行的动作标识符（需在 action_registry 中注册）
            action_params: 动作参数
            max_runs: 最大执行次数（0=无限）
            priority: 优先级（1-10）

        Returns:
            task_id: 任务 ID
        """
        task_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        action_params = action_params or {}
        next_run = self._calc_next_run(trigger_type, trigger_config)

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            description=description,
            trigger_type=trigger_type.value,
            trigger_config=trigger_config,
            action=action,
            action_params=action_params,
            status=TaskStatus.SCHEDULED.value,
            created_at=now,
            next_run=next_run,
            max_runs=max_runs,
            priority=max(1, min(10, priority)),
        )

        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """INSERT INTO scheduled_tasks
                       (task_id, name, description, trigger_type, trigger_config,
                        action, action_params, status, created_at, next_run,
                        run_count, max_runs, priority)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                    (
                        task.task_id, task.name, task.description,
                        task.trigger_type, json.dumps(task.trigger_config),
                        task.action, json.dumps(task.action_params),
                        task.status, task.created_at, task.next_run,
                        task.max_runs, task.priority,
                    ),
                )
                conn.commit()

        self._history[task_id] = []
        logger.info(f"[Scheduler] 任务已调度: {name} (id={task_id}, trigger={trigger_type.value})")
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """取消一个任务"""
        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT status FROM scheduled_tasks WHERE task_id = ?",
                    (task_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False

                status = row["status"]
                if status in (TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value):
                    return False

                conn.execute(
                    "UPDATE scheduled_tasks SET status = ? WHERE task_id = ?",
                    (TaskStatus.CANCELLED.value, task_id),
                )
                conn.commit()

            # 记录历史
            self._add_history(task_id, TaskStatus.CANCELLED.value, result=None, error=None)
            logger.info(f"[Scheduler] 任务已取消: {task_id}")
            return True

    def run_due_tasks(self) -> List[str]:
        """
        查找并执行所有到期的任务。

        返回实际被运行的 task_id 列表。
        """
        now = datetime.utcnow().isoformat()
        due_task_ids = []

        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """SELECT * FROM scheduled_tasks
                       WHERE status IN (?, ?)
                         AND next_run IS NOT NULL
                         AND next_run <= ?
                       ORDER BY priority DESC, next_run ASC""",
                    (TaskStatus.SCHEDULED.value, TaskStatus.PENDING.value, now),
                )
                rows = cursor.fetchall()
                due_task_ids = [row["task_id"] for row in rows]

                # 将状态更新为 RUNNING
                for tid in due_task_ids:
                    conn.execute(
                        "UPDATE scheduled_tasks SET status = ? WHERE task_id = ?",
                        (TaskStatus.RUNNING.value, tid),
                    )
                conn.commit()

        # 在后台线程中执行每个到期任务
        for task_id in due_task_ids:
            self._execute_task_async(task_id)

        return due_task_ids

    def mark_task_completed(self, task_id: str, result: Any = None) -> bool:
        """标记任务为已完成"""
        now = datetime.utcnow().isoformat()

        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM scheduled_tasks WHERE task_id = ?",
                    (task_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False

                task = self._row_to_task(row)
                new_run_count = task.run_count + 1

                # 检查是否达到最大运行次数
                if task.max_runs > 0 and new_run_count >= task.max_runs:
                    new_status = TaskStatus.COMPLETED.value
                    new_next_run = None
                else:
                    # 计算下次运行时间
                    new_next_run = self._calc_next_run(
                        TriggerType(task.trigger_type),
                        task.trigger_config,
                    )
                    new_status = TaskStatus.SCHEDULED.value if new_next_run else TaskStatus.COMPLETED.value

                conn.execute(
                    """UPDATE scheduled_tasks
                       SET status = ?, last_run = ?, next_run = ?, run_count = ?
                       WHERE task_id = ?""",
                    (new_status, now, new_next_run, new_run_count, task_id),
                )
                conn.commit()

            result_json = json.dumps(result, default=str) if result is not None else None
            self._add_history(task_id, TaskStatus.COMPLETED.value, result=result_json, error=None)
            logger.info(f"[Scheduler] 任务已完成: {task_id} (第 {new_run_count} 次)")
            return True

    def mark_task_failed(self, task_id: str, error: str) -> bool:
        """标记任务为失败"""
        now = datetime.utcnow().isoformat()

        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM scheduled_tasks WHERE task_id = ?",
                    (task_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False

                task = self._row_to_task(row)
                new_run_count = task.run_count + 1

                # 失败后仍计算下次运行时间（重试机制）
                new_next_run = self._calc_next_run(
                    TriggerType(task.trigger_type),
                    task.trigger_config,
                )
                # 如果达到最大运行次数，则不再重试
                if task.max_runs > 0 and new_run_count >= task.max_runs:
                    new_status = TaskStatus.FAILED.value
                    new_next_run = None
                else:
                    new_status = TaskStatus.SCHEDULED.value if new_next_run else TaskStatus.FAILED.value

                conn.execute(
                    """UPDATE scheduled_tasks
                       SET status = ?, last_run = ?, next_run = ?, run_count = ?
                       WHERE task_id = ?""",
                    (new_status, now, new_next_run, new_run_count, task_id),
                )
                conn.commit()

            self._add_history(task_id, TaskStatus.FAILED.value, result=None, error=error)
            logger.error(f"[Scheduler] 任务失败: {task_id} — {error}")
            return True

    def get_pending_tasks(self) -> List[ScheduledTask]:
        """获取所有待执行和已调度的任务"""
        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """SELECT * FROM scheduled_tasks
                       WHERE status IN (?, ?)
                       ORDER BY priority DESC, next_run ASC""",
                    (TaskStatus.SCHEDULED.value, TaskStatus.PENDING.value),
                )
                return [self._row_to_task(row) for row in cursor.fetchall()]

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取单个任务"""
        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM scheduled_tasks WHERE task_id = ?",
                    (task_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return self._row_to_task(row)

    def get_task_history(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务的执行历史"""
        # 先检查内存缓存
        if task_id in self._history:
            entries = self._history[task_id]
            return entries[-limit:] if len(entries) > limit else entries[:]

        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """SELECT timestamp, status, result, error FROM task_history
                       WHERE task_id = ?
                       ORDER BY id DESC
                       LIMIT ?""",
                    (task_id, limit),
                )
                rows = cursor.fetchall()
                return [
                    {
                        "timestamp": row["timestamp"],
                        "status": row["status"],
                        "result": json.loads(row["result"]) if row["result"] else None,
                        "error": row["error"],
                    }
                    for row in rows
                ]

    def get_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        with self._lock:
            with self._get_conn() as conn:
                # 总数
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM scheduled_tasks")
                total = cursor.fetchone()["cnt"]

                # 按状态分组
                cursor = conn.execute(
                    "SELECT status, COUNT(*) as cnt FROM scheduled_tasks GROUP BY status"
                )
                by_status = {row["status"]: row["cnt"] for row in cursor.fetchall()}

                # 总运行次数
                cursor = conn.execute("SELECT SUM(run_count) as total FROM scheduled_tasks")
                total_runs = cursor.fetchone()["total"] or 0

                # 成功/失败次数（从历史表）
                cursor = conn.execute(
                    "SELECT status, COUNT(*) as cnt FROM task_history GROUP BY status"
                )
                history_counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}

                completed = history_counts.get(TaskStatus.COMPLETED.value, 0)
                failed = history_counts.get(TaskStatus.FAILED.value, 0)
                total_finished = completed + failed
                success_rate = (completed / total_finished * 100) if total_finished > 0 else 0.0

                return {
                    "total_tasks": total,
                    "by_status": by_status,
                    "total_runs": total_runs,
                    "success_count": completed,
                    "failed_count": failed,
                    "success_rate": round(success_rate, 2),
                }

    def reschedule_task(self, task_id: str, new_trigger_config: Dict[str, Any]) -> bool:
        """重新调度任务（修改触发配置）"""
        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM scheduled_tasks WHERE task_id = ?",
                    (task_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False

                task = self._row_to_task(row)
                next_run = self._calc_next_run(
                    TriggerType(task.trigger_type),
                    new_trigger_config,
                )

                conn.execute(
                    """UPDATE scheduled_tasks
                       SET trigger_config = ?, next_run = ?, status = ?
                       WHERE task_id = ?""",
                    (
                        json.dumps(new_trigger_config),
                        next_run,
                        TaskStatus.SCHEDULED.value,
                        task_id,
                    ),
                )
                conn.commit()

            logger.info(f"[Scheduler] 任务已重新调度: {task_id}")
            return True

    def close(self):
        """关闭调度器，等待正在运行的任务完成"""
        logger.info("[Scheduler] 正在关闭调度器...")
        for tid, thread in list(self._running_tasks.items()):
            if thread.is_alive():
                thread.join(timeout=5)
                logger.info(f"[Scheduler] 等待任务 {tid} 完成")
        self._running_tasks.clear()
        if self._conn:
            self._conn.close()
        logger.info("[Scheduler] 调度器已关闭")

    # ---- 内部方法 ----

    def _calc_next_run(self, trigger_type: TriggerType, config: Dict[str, Any]) -> Optional[str]:
        """计算下次运行时间"""
        now = datetime.utcnow()

        if trigger_type == TriggerType.TIME_INTERVAL:
            interval = config.get("interval_seconds", 60)
            return (now + timedelta(seconds=interval)).isoformat()

        elif trigger_type == TriggerType.PERIODIC:
            interval = config.get("interval_seconds", 60)
            return (now + timedelta(seconds=interval)).isoformat()

        elif trigger_type == TriggerType.ONCE:
            run_at = config.get("run_at")
            if run_at:
                run_dt = datetime.fromisoformat(run_at)
                if run_dt > now:
                    return run_dt.isoformat()
            return None  # 时间已过或无效

        elif trigger_type == TriggerType.CRON:
            cron_expr = config.get("cron_expression", "")
            next_dt = self._next_cron_time(cron_expr, now)
            return next_dt.isoformat() if next_dt else None

        elif trigger_type == TriggerType.CONDITION:
            # 条件触发立即执行
            return now.isoformat()

        return None

    def _next_cron_time(self, cron_expr: str, after: datetime) -> Optional[datetime]:
        """
        解析简单的 CRON 表达式（5 字段格式）并计算下次运行时间。

        支持: 精确值、*、*/N、N-M、N,M

        格式: minute hour day-of-month month day-of-week
        """
        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return None

            fields = {
                "minute": (parts[0], lambda dt: dt.minute, lambda dt, v: dt.replace(minute=v)),
                "hour": (parts[1], lambda dt: dt.hour, lambda dt, v: dt.replace(hour=v)),
                "dom": (parts[2], lambda dt: dt.day, lambda dt, v: dt.replace(day=v)),
                "month": (parts[3], lambda dt: dt.month, lambda dt, v: dt.replace(month=v)),
                "dow": (parts[4], lambda dt: dt.weekday(), None),  # handled separately
            }

            # 从 after + 1 秒开始搜索，最多搜索 2 年
            candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
            max_iterations = 366 * 24 * 60  # 最多搜索约 2 年

            for _ in range(max_iterations):
                if self._cron_matches(fields, candidate):
                    return candidate
                candidate += timedelta(minutes=1)

            return None
        except (ValueError, IndexError):
            return None

    def _cron_matches(self, fields: Dict, dt: datetime) -> bool:
        """检查时间是否匹配 CRON 表达式"""
        # 检查分钟
        if not self._cron_field_matches(fields["minute"][0], dt.minute, 0, 59):
            return False
        # 检查小时
        if not self._cron_field_matches(fields["hour"][0], dt.hour, 0, 23):
            return False
        # 检查日期
        if not self._cron_field_matches(fields["dom"][0], dt.day, 1, 31):
            return False
        # 检查月份
        if not self._cron_field_matches(fields["month"][0], dt.month, 1, 12):
            return False
        # 检查星期
        if not self._cron_field_matches(fields["dow"][0], dt.weekday(), 0, 6):
            return False
        return True

    def _cron_field_matches(self, pattern: str, value: int, min_val: int, max_val: int) -> bool:
        """匹配单个 CRON 字段"""
        if pattern == "*":
            return True

        if pattern.startswith("*/"):
            step = int(pattern[2:])
            return value % step == min_val % step

        # 支持 N,M 列表
        if "," in pattern:
            parts = [int(p) for p in pattern.split(",")]
            return value in parts

        # 支持 N-M 范围
        if "-" in pattern:
            start, end = pattern.split("-", 1)
            return int(start) <= value <= int(end)

        return int(pattern) == value

    def _execute_task_async(self, task_id: str):
        """在后台线程中异步执行任务"""
        thread = threading.Thread(
            target=self._execute_task,
            args=(task_id,),
            name=f"scheduler-{task_id}",
            daemon=True,
        )
        self._running_tasks[task_id] = thread
        thread.start()

    def _execute_task(self, task_id: str):
        """执行单个任务"""
        try:
            with self._lock:
                with self._get_conn() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM scheduled_tasks WHERE task_id = ?",
                        (task_id,),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return
                    task = self._row_to_task(row)

            # 查找并执行 action
            action_fn = self._action_registry.get(task.action)
            if action_fn is None:
                self.mark_task_failed(task_id, f"Action '{task.action}' 未注册")
                return

            result = action_fn(**task.action_params)

            # 标记完成
            self.mark_task_completed(task_id, result=result)

        except Exception as e:
            logger.exception(f"[Scheduler] 任务执行异常: {task_id}")
            self.mark_task_failed(task_id, str(e))
        finally:
            self._running_tasks.pop(task_id, None)

    def _add_history(self, task_id: str, status: str, result: Any = None, error: str = None):
        """添加执行历史"""
        now = datetime.utcnow().isoformat()
        entry = {
            "timestamp": now,
            "status": status,
            "result": result,
            "error": error,
        }

        # 内存缓存
        if task_id not in self._history:
            self._history[task_id] = []
        self._history[task_id].append(entry)

        # 持久化
        with self._lock:
            with self._get_conn() as conn:
                result_json = result if isinstance(result, str) else json.dumps(result, default=str) if result else None
                conn.execute(
                    """INSERT INTO task_history (task_id, timestamp, status, result, error)
                       VALUES (?, ?, ?, ?, ?)""",
                    (task_id, now, status, result_json, error),
                )
                conn.commit()

    def register_action(self, name: str, fn: Callable):
        """注册一个可执行的动作"""
        self._action_registry[name] = fn
