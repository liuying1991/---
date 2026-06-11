"""
Goal Manager - 自主目标管理系统

让Jarvis能自主设定、分解、追踪和调整目标。

核心特性:
- 目标定义: 创建目标，设置优先级、期限、指标
- 目标分解: 将大目标分解为可执行的子目标
- 进度追踪: 实时更新目标完成度
- 优先级管理: 动态调整目标优先级
- 自动调整: 基于进展自动调整目标策略

设计原则:
- 目标可量化: 每个目标都有明确的完成度指标
- 分解可执行: 子目标足够小，可以立即执行
- 动态调整: 根据实际进展自动调整计划
"""
import time
import uuid
import sqlite3
import json
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# ─── Enums ───────────────────────────────────────────────────────────────────


class GoalStatus(Enum):
    """目标状态"""
    PENDING = "pending"           # 待开始
    IN_PROGRESS = "in_progress"   # 进行中
    ON_HOLD = "on_hold"           # 暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class GoalPriority(Enum):
    """目标优先级"""
    LOW = "low"                   # 1
    MEDIUM = "medium"             # 2
    HIGH = "high"                 # 3
    CRITICAL = "critical"         # 4


class GoalType(Enum):
    """目标类型"""
    TASK = "task"                 # 任务型
    LEARNING = "learning"         # 学习型
    OPTIMIZATION = "optimization" # 优化型
    CREATION = "creation"         # 创造型
    MAINTENANCE = "maintenance"   # 维护型


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class SubGoal:
    """子目标

    Attributes:
        subgoal_id: 子目标ID
        goal_id: 父目标ID
        title: 子目标标题
        description: 描述
        status: 状态
        completed: 是否完成
        progress: 完成度(0.0-1.0)
        created_at: 创建时间
    """
    subgoal_id: str
    goal_id: str
    title: str
    description: str = ""
    status: GoalStatus = GoalStatus.PENDING
    completed: bool = False
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "subgoal_id": self.subgoal_id,
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "completed": self.completed,
            "progress": self.progress,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SubGoal":
        d = dict(data)
        if isinstance(d.get("status"), str):
            d["status"] = GoalStatus(d["status"])
        allowed = {"subgoal_id", "goal_id", "title", "description",
                   "status", "completed", "progress", "created_at"}
        d = {k: v for k, v in d.items() if k in allowed}
        return cls(**d)


@dataclass
class Goal:
    """目标

    Attributes:
        goal_id: 目标ID
        user_id: 用户ID
        title: 目标标题
        description: 描述
        goal_type: 目标类型
        priority: 优先级
        status: 状态
        progress: 完成度(0.0-1.0)
        deadline: 截止时间戳(0表示无期限)
        metrics: 衡量指标(JSON字符串)
        subgoal_count: 子目标数量
        completed_subgoal_count: 已完成子目标数
        created_at: 创建时间
        updated_at: 更新时间
    """
    goal_id: str
    user_id: str
    title: str
    description: str = ""
    goal_type: GoalType = GoalType.TASK
    priority: GoalPriority = GoalPriority.MEDIUM
    status: GoalStatus = GoalStatus.PENDING
    progress: float = 0.0
    deadline: float = 0.0
    metrics: str = ""
    subgoal_count: int = 0
    completed_subgoal_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "goal_id": self.goal_id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "goal_type": self.goal_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "progress": self.progress,
            "deadline": self.deadline,
            "metrics": self.metrics,
            "subgoal_count": self.subgoal_count,
            "completed_subgoal_count": self.completed_subgoal_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Goal":
        d = dict(data)
        for enum_field, enum_cls in [("status", GoalStatus), ("priority", GoalPriority),
                                       ("goal_type", GoalType)]:
            if isinstance(d.get(enum_field), str):
                d[enum_field] = enum_cls(d[enum_field])
        allowed = {"goal_id", "user_id", "title", "description", "goal_type",
                   "priority", "status", "progress", "deadline", "metrics",
                   "subgoal_count", "completed_subgoal_count", "created_at", "updated_at"}
        d = {k: v for k, v in d.items() if k in allowed}
        return cls(**d)


# ─── Goal Manager ────────────────────────────────────────────────────────────


class GoalManager:
    """
    自主目标管理器

    管理目标的创建、分解、追踪、优先级调整和完成度计算。

    使用示例:
        >>> manager = GoalManager(db_path="goals.db")
        >>> goal_id = manager.create_goal("user1", "完成项目报告", priority="high")
        >>> manager.add_subgoals(goal_id, ["收集数据", "分析数据", "撰写报告"])
        >>> manager.update_subgoal_progress(goal_id, subgoal_id, 0.5)
        >>> progress = manager.get_goal_progress(goal_id)
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
        """Close connection only if not using persistent in-memory DB"""
        if not self._persistent_conn:
            conn.close()

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS goals (
                goal_id               TEXT PRIMARY KEY,
                user_id               TEXT NOT NULL DEFAULT 'default',
                title                 TEXT NOT NULL,
                description           TEXT NOT NULL DEFAULT '',
                goal_type             TEXT NOT NULL DEFAULT 'task',
                priority              TEXT NOT NULL DEFAULT 'medium',
                status                TEXT NOT NULL DEFAULT 'pending',
                progress              REAL NOT NULL DEFAULT 0.0,
                deadline              REAL NOT NULL DEFAULT 0.0,
                metrics               TEXT NOT NULL DEFAULT '',
                subgoal_count         INTEGER NOT NULL DEFAULT 0,
                completed_subgoal_count INTEGER NOT NULL DEFAULT 0,
                created_at            REAL NOT NULL,
                updated_at            REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subgoals (
                subgoal_id    TEXT PRIMARY KEY,
                goal_id       TEXT NOT NULL,
                title         TEXT NOT NULL,
                description   TEXT NOT NULL DEFAULT '',
                status        TEXT NOT NULL DEFAULT 'pending',
                completed     INTEGER NOT NULL DEFAULT 0,
                progress      REAL NOT NULL DEFAULT 0.0,
                created_at    REAL NOT NULL,
                FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS goal_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id     TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                details     TEXT NOT NULL DEFAULT '',
                timestamp   REAL NOT NULL,
                FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
            CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
            CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority);
            CREATE INDEX IF NOT EXISTS idx_subgoals_goal ON subgoals(goal_id);
            CREATE INDEX IF NOT EXISTS idx_events_goal ON goal_events(goal_id);
        """)
        conn.commit()
        self._maybe_close(conn)

    # ── Goal Creation ─────────────────────────────────────────────────────

    def create_goal(
        self,
        user_id: str,
        title: str,
        description: str = "",
        goal_type: str = "task",
        priority: str = "medium",
        deadline: float = 0.0,
        metrics: Optional[Dict] = None,
    ) -> str:
        """
        创建新目标

        Args:
            user_id: 用户ID
            title: 目标标题
            description: 描述
            goal_type: 目标类型 (task/learning/optimization/creation/maintenance)
            priority: 优先级 (low/medium/high/critical)
            deadline: 截止时间戳
            metrics: 衡量指标

        Returns:
            目标ID
        """
        goal_id = f"goal_{uuid.uuid4().hex[:12]}"
        now = time.time()
        metrics_str = json.dumps(metrics or {}, ensure_ascii=False)

        try:
            gt = GoalType(goal_type).value
        except ValueError:
            gt = GoalType.TASK.value

        try:
            gp = GoalPriority(priority).value
        except ValueError:
            gp = GoalPriority.MEDIUM.value

        conn = self._get_conn()
        conn.execute(
            """INSERT INTO goals 
            (goal_id, user_id, title, description, goal_type, priority,
             deadline, metrics, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, user_id, title, description, gt, gp,
             deadline, metrics_str, now, now),
        )
        self._log_event(conn, goal_id, "created", f"目标创建: {title}")
        conn.commit()
        self._maybe_close(conn)
        return goal_id

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """获取目标"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM goals WHERE goal_id = ?", (goal_id,)
        ).fetchone()
        self._maybe_close(conn)
        if row is None:
            return None
        return Goal.from_dict(dict(row))

    def update_goal_status(self, goal_id: str, status: str) -> bool:
        """更新目标状态"""
        try:
            gs = GoalStatus(status).value
        except ValueError:
            return False

        conn = self._get_conn()
        conn.execute(
            "UPDATE goals SET status = ?, updated_at = ? WHERE goal_id = ?",
            (gs, time.time(), goal_id),
        )
        self._log_event(conn, goal_id, "status_change", f"状态变为: {status}")
        conn.commit()
        self._maybe_close(conn)
        return True

    # ── Subgoal Management ────────────────────────────────────────────────

    def add_subgoals(self, goal_id: str, titles: List[str],
                     descriptions: Optional[List[str]] = None) -> List[str]:
        """
        添加子目标（目标分解）

        Args:
            goal_id: 父目标ID
            titles: 子目标标题列表
            descriptions: 可选，子目标描述列表

        Returns:
            子目标ID列表
        """
        descs = descriptions or [""] * len(titles)
        subgoal_ids = []
        now = time.time()

        conn = self._get_conn()
        for title, desc in zip(titles, descs):
            subgoal_id = f"sub_{uuid.uuid4().hex[:10]}"
            conn.execute(
                """INSERT INTO subgoals (subgoal_id, goal_id, title, description, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (subgoal_id, goal_id, title, desc, now),
            )
            subgoal_ids.append(subgoal_id)

        # 更新父目标的子目标计数
        conn.execute(
            """UPDATE goals SET subgoal_count = subgoal_count + ?, updated_at = ?
            WHERE goal_id = ?""",
            (len(subgoal_ids), now, goal_id),
        )
        self._log_event(conn, goal_id, "decomposed", f"分解为{len(subgoal_ids)}个子目标")
        conn.commit()
        self._maybe_close(conn)
        return subgoal_ids

    def get_subgoals(self, goal_id: str) -> List[SubGoal]:
        """获取目标的所有子目标"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM subgoals WHERE goal_id = ?
            ORDER BY created_at ASC""",
            (goal_id,),
        ).fetchall()
        self._maybe_close(conn)
        return [SubGoal.from_dict(dict(r)) for r in rows]

    def update_subgoal_progress(self, goal_id: str, subgoal_id: str,
                                progress: float) -> bool:
        """
        更新子目标进度

        Args:
            goal_id: 父目标ID
            subgoal_id: 子目标ID
            progress: 进度(0.0-1.0)

        Returns:
            是否成功
        """
        progress = max(0.0, min(progress, 1.0))
        status = GoalStatus.COMPLETED.value if progress >= 1.0 else GoalStatus.IN_PROGRESS.value
        completed = 1 if progress >= 1.0 else 0

        conn = self._get_conn()
        conn.execute(
            """UPDATE subgoals SET progress = ?, status = ?, completed = ?
            WHERE subgoal_id = ? AND goal_id = ?""",
            (progress, status, completed, subgoal_id, goal_id),
        )

        # 重新计算父目标完成度
        self._recalculate_goal_progress(conn, goal_id)
        conn.commit()
        self._maybe_close(conn)
        return True

    def complete_subgoal(self, goal_id: str, subgoal_id: str) -> bool:
        """完成子目标"""
        return self.update_subgoal_progress(goal_id, subgoal_id, 1.0)

    def _recalculate_goal_progress(self, conn, goal_id: str):
        """重新计算目标完成度"""
        # 统计子目标
        row = conn.execute(
            """SELECT COUNT(*) as total,
               SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) as completed_count,
               AVG(progress) as avg_progress
               FROM subgoals WHERE goal_id = ?""",
            (goal_id,),
        ).fetchone()

        if row["total"] == 0:
            return

        completed_count = row["completed_count"] or 0
        avg_progress = row["avg_progress"] or 0.0

        # 目标进度 = 已完成子目标比例 * 0.7 + 平均进度 * 0.3
        completion_ratio = completed_count / row["total"]
        new_progress = round(completion_ratio * 0.7 + avg_progress * 0.3, 4)

        # 更新目标状态
        if completion_ratio >= 1.0:
            new_status = GoalStatus.COMPLETED.value
        elif completion_ratio > 0:
            new_status = GoalStatus.IN_PROGRESS.value
        else:
            new_status = GoalStatus.PENDING.value

        conn.execute(
            """UPDATE goals SET progress = ?, status = ?,
               completed_subgoal_count = ?, updated_at = ?
               WHERE goal_id = ?""",
            (new_progress, new_status, completed_count, time.time(), goal_id),
        )

    # ── Goal Tracking ─────────────────────────────────────────────────────

    def get_goal_progress(self, goal_id: str) -> Dict:
        """
        获取目标进度详情

        Args:
            goal_id: 目标ID

        Returns:
            进度详情
        """
        goal = self.get_goal(goal_id)
        if goal is None:
            return {}

        subgoals = self.get_subgoals(goal_id)
        return {
            "goal": goal.to_dict(),
            "subgoals": [s.to_dict() for s in subgoals],
            "progress": goal.progress,
            "subgoal_progress": {
                "total": goal.subgoal_count,
                "completed": goal.completed_subgoal_count,
                "remaining": goal.subgoal_count - goal.completed_subgoal_count,
            },
        }

    def get_user_goals(self, user_id: str, status: Optional[str] = None) -> List[Goal]:
        """获取用户的目标"""
        conn = self._get_conn()
        if status:
            rows = conn.execute(
                """SELECT * FROM goals WHERE user_id = ? AND status = ?
                ORDER BY 
                    CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 
                         WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END,
                    created_at DESC""",
                (user_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM goals WHERE user_id = ?
                ORDER BY 
                    CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 
                         WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END,
                    created_at DESC""",
                (user_id,),
            ).fetchall()
        self._maybe_close(conn)
        return [Goal.from_dict(dict(r)) for r in rows]

    def get_active_goals(self, user_id: str) -> List[Goal]:
        """获取用户的活跃目标(进行中+待开始)"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM goals WHERE user_id = ? 
            AND status IN ('pending', 'in_progress')
            ORDER BY 
                CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 
                     WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END""",
            (user_id,),
        ).fetchall()
        self._maybe_close(conn)
        return [Goal.from_dict(dict(r)) for r in rows]

    # ── Priority Management ───────────────────────────────────────────────

    def update_priority(self, goal_id: str, priority: str) -> bool:
        """更新目标优先级"""
        try:
            gp = GoalPriority(priority).value
        except ValueError:
            return False

        conn = self._get_conn()
        conn.execute(
            "UPDATE goals SET priority = ?, updated_at = ? WHERE goal_id = ?",
            (gp, time.time(), goal_id),
        )
        self._log_event(conn, goal_id, "priority_change", f"优先级变为: {priority}")
        conn.commit()
        self._maybe_close(conn)
        return True

    def auto_adjust_priority(self, goal_id: str) -> bool:
        """
        自动调整优先级

        规则:
        - 临近截止日期的目标提升优先级
        - 长期未进展的目标降低优先级
        """
        goal = self.get_goal(goal_id)
        if goal is None:
            return False

        now = time.time()
        current = goal.priority.value

        # 检查截止日期
        if goal.deadline > 0:
            days_left = (goal.deadline - now) / 86400
            if days_left <= 1 and current != "critical":
                return self.update_priority(goal_id, "critical")
            elif days_left <= 3 and current not in ("critical", "high"):
                return self.update_priority(goal_id, "high")

        # 检查进展
        if goal.progress == 0 and (now - goal.created_at) > 86400 * 7:
            if current != "low":
                return self.update_priority(goal_id, "low")

        return False

    # ── Events ────────────────────────────────────────────────────────────

    def get_goal_events(self, goal_id: str, k: int = 20) -> List[Dict]:
        """获取目标事件历史"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM goal_events WHERE goal_id = ?
            ORDER BY timestamp DESC LIMIT ?""",
            (goal_id, k),
        ).fetchall()
        self._maybe_close(conn)
        return [dict(r) for r in rows]

    def _log_event(self, conn, goal_id: str, event_type: str, details: str = ""):
        """记录目标事件"""
        conn.execute(
            """INSERT INTO goal_events (goal_id, event_type, details, timestamp)
            VALUES (?, ?, ?, ?)""",
            (goal_id, event_type, details, time.time()),
        )

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_stats(self, user_id: str = "") -> Dict:
        """获取目标系统统计"""
        conn = self._get_conn()
        if user_id:
            row = conn.execute(
                """SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                   AVG(progress) as avg_progress
                   FROM goals WHERE user_id = ?""",
                (user_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                   AVG(progress) as avg_progress
                   FROM goals"""
            ).fetchone()

        total_subgoals = conn.execute("SELECT COUNT(*) FROM subgoals").fetchone()[0]
        self._maybe_close(conn)

        total = row["total"] or 0
        return {
            "total_goals": total,
            "completed_goals": row["completed"] or 0,
            "in_progress_goals": row["in_progress"] or 0,
            "pending_goals": row["pending"] or 0,
            "completion_rate": (row["completed"] or 0) / total if total > 0 else 0.0,
            "avg_progress": round(row["avg_progress"] or 0.0, 4),
            "total_subgoals": total_subgoals,
        }

    def close(self):
        if self._persistent_conn:
            self._persistent_self._maybe_close(conn)
            self._persistent_conn = None
