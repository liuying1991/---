"""
Autonomous Executor - 自主行动执行引擎

让Jarvis在没有用户指令时自主运行完整循环：
检查目标 → 规划行动 → 执行技能 → 记录经验 → 反思调整

核心特性:
- 自主循环: 定时触发完整行动循环
- 目标驱动: 优先处理高优先级活跃目标
- 场景适配: 根据当前场景调整执行策略
- 安全约束: 每步操作都经过安全评估
- 经验记录: 每次执行都记录为经验供学习

设计原则:
- 自主不等于失控，安全始终优先
- 每次自主行动都应有明确目标
- 行动结果必须可追溯可反思
- 循环间隔可配置，避免过度自主
"""
import time
import uuid
import sqlite3
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field


# ─── Enums ───────────────────────────────────────────────────────────────────


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"         # 待执行
    RUNNING = "running"         # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    ABORTED = "aborted"         # 中止
    SKIPPED = "skipped"         # 跳过


class ExecutionLevel(Enum):
    """自主执行级别"""
    OBSERVE = "observe"         # 仅观察不行动
    SUGGEST = "suggest"         # 仅建议不执行
    CONFIRM = "confirm"         # 执行前需确认
    AUTONOMOUS = "autonomous"   # 完全自主执行


class LoopPhase(Enum):
    """循环阶段"""
    CHECK_GOALS = "check_goals"       # 检查目标
    PLAN_ACTIONS = "plan_actions"      # 规划行动
    EXECUTE = "execute"               # 执行行动
    REFLECT = "reflect"               # 反思结果
    ADJUST = "adjust"                 # 调整策略


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class AutonomousAction:
    """自主行动
    Attributes:
        action_id: 行动ID
        goal_id: 关联目标ID
        action_type: 行动类型
        description: 行动描述
        parameters: 行动参数
        status: 执行状态
        result: 执行结果
        execution_time: 执行耗时(秒)
        safety_score: 安全评分(0.0-1.0)
        created_at: 创建时间
        executed_at: 执行时间
    """
    action_id: str
    action_type: str
    description: str
    goal_id: str = ""
    parameters: Dict = field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: str = ""
    execution_time: float = 0.0
    safety_score: float = 1.0
    created_at: float = field(default_factory=time.time)
    executed_at: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "description": self.description,
            "goal_id": self.goal_id,
            "parameters": self.parameters,
            "status": self.status.value,
            "result": self.result,
            "execution_time": self.execution_time,
            "safety_score": self.safety_score,
            "created_at": self.created_at,
            "executed_at": self.executed_at,
        }


@dataclass
class CycleReport:
    """自主循环报告
    Attributes:
        cycle_id: 循环ID
        phase: 当前阶段
        actions_executed: 已执行行动数
        actions_succeeded: 成功行动数
        actions_failed: 失败行动数
        duration: 循环耗时(秒)
        findings: 发现/结论
        next_cycle_in: 下次循环间隔(秒)
        started_at: 开始时间
    """
    cycle_id: str
    phase: LoopPhase
    actions_executed: int = 0
    actions_succeeded: int = 0
    actions_failed: int = 0
    duration: float = 0.0
    findings: str = ""
    next_cycle_in: float = 3600.0
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase.value,
            "actions_executed": self.actions_executed,
            "actions_succeeded": self.actions_succeeded,
            "actions_failed": self.actions_failed,
            "duration": round(self.duration, 2),
            "findings": self.findings,
            "next_cycle_in": self.next_cycle_in,
            "started_at": self.started_at,
        }


# ─── Autonomous Executor ────────────────────────────────────────────────────


class AutonomousExecutor:
    """
    自主行动执行引擎

    让Jarvis在没有用户指令时自主运行：
    1. 检查活跃目标，选择最优先的目标
    2. 根据目标和场景规划行动
    3. 执行行动（受安全约束和执行级别控制）
    4. 记录执行结果为经验
    5. 反思执行结果，调整策略

    使用示例:
        >>> executor = AutonomousExecutor(db_path="autonomous.db")
        >>> executor.set_execution_level(ExecutionLevel.CONFIRM)
        >>> report = executor.run_cycle("user1", scene="work")
        >>> print(report.actions_executed)
    """

    def __init__(self, db_path: str = ":memory:", config: Dict = None):
        self.db_path = db_path
        self.config = config or {}
        self._persistent_conn = None
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row
        self._init_db()

        # 执行级别
        self.execution_level = ExecutionLevel(
            self.config.get("execution_level", "confirm")
        )

        # 循环间隔(秒)
        self.cycle_interval = self.config.get("cycle_interval", 3600)

        # 最大每循环行动数
        self.max_actions_per_cycle = self.config.get("max_actions_per_cycle", 5)

        # 行动处理器注册
        self._action_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

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
            CREATE TABLE IF NOT EXISTS autonomous_actions (
                action_id       TEXT PRIMARY KEY,
                action_type     TEXT NOT NULL,
                description     TEXT NOT NULL,
                goal_id         TEXT NOT NULL DEFAULT '',
                parameters      TEXT NOT NULL DEFAULT '{}',
                status          TEXT NOT NULL DEFAULT 'pending',
                result          TEXT NOT NULL DEFAULT '',
                execution_time  REAL NOT NULL DEFAULT 0.0,
                safety_score    REAL NOT NULL DEFAULT 1.0,
                created_at      REAL NOT NULL,
                executed_at     REAL NOT NULL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS cycle_reports (
                cycle_id            TEXT PRIMARY KEY,
                phase               TEXT NOT NULL,
                actions_executed    INTEGER NOT NULL DEFAULT 0,
                actions_succeeded   INTEGER NOT NULL DEFAULT 0,
                actions_failed      INTEGER NOT NULL DEFAULT 0,
                duration            REAL NOT NULL DEFAULT 0.0,
                findings            TEXT NOT NULL DEFAULT '',
                next_cycle_in       REAL NOT NULL DEFAULT 3600.0,
                started_at          REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_actions_status ON autonomous_actions(status);
            CREATE INDEX IF NOT EXISTS idx_actions_goal ON autonomous_actions(goal_id);
            CREATE INDEX IF NOT EXISTS idx_cycles_started ON cycle_reports(started_at DESC);
        """)
        conn.commit()
        self._maybe_close(conn)

    def _register_default_handlers(self):
        """注册默认行动处理器"""
        self._action_handlers["organize_knowledge"] = self._handle_organize_knowledge
        self._handle_organize_knowledge = self._action_handlers["organize_knowledge"]

        self._action_handlers["review_experience"] = self._handle_review_experience
        self._action_handlers["update_profile"] = self._handle_update_profile
        self._action_handlers["analyze_patterns"] = self._handle_analyze_patterns
        self._action_handlers["optimize_workflow"] = self._handle_optimize_workflow

    def set_execution_level(self, level: str) -> bool:
        """设置执行级别"""
        try:
            self.execution_level = ExecutionLevel(level)
            return True
        except ValueError:
            return False

    def set_cycle_interval(self, seconds: float):
        """设置循环间隔(秒)"""
        self.cycle_interval = max(60.0, seconds)  # 最小60秒

    def register_action_handler(self, action_type: str, handler: Callable):
        """注册自定义行动处理器"""
        self._action_handlers[action_type] = handler

    # ── Main Cycle ─────────────────────────────────────────────────────────

    def run_cycle(
        self,
        user_id: str,
        scene: str = "",
        goal_manager=None,
        goal_planner=None,
        experience_replay=None,
        safety_engine=None,
    ) -> CycleReport:
        """
        执行一次完整的自主行动循环

        Args:
            user_id: 用户ID
            scene: 当前场景
            goal_manager: 目标管理器
            goal_planner: 目标规划器
            experience_replay: 经验回放
            safety_engine: 安全引擎

        Returns:
            循环报告
        """
        cycle_id = f"cycle_{uuid.uuid4().hex[:10]}"
        report = CycleReport(cycle_id=cycle_id, phase=LoopPhase.CHECK_GOALS)
        start_time = time.time()

        findings = []

        # Phase 1: 检查目标
        report.phase = LoopPhase.CHECK_GOALS
        active_goals = self._check_goals(user_id, goal_manager)
        findings.append(f"发现 {len(active_goals)} 个活跃目标")

        if not active_goals:
            # 没有活跃目标，尝试规划新目标
            report.phase = LoopPhase.PLAN_ACTIONS
            if goal_planner:
                plans = goal_planner.suggest_goals(user_id, scene, k=3)
                if plans:
                    findings.append(f"规划了 {len(plans)} 个新目标")

        # Phase 2: 规划行动
        report.phase = LoopPhase.PLAN_ACTIONS
        actions = self._plan_actions(
            user_id, scene, active_goals,
            goal_manager, goal_planner, experience_replay
        )
        findings.append(f"规划了 {len(actions)} 个行动")

        # Phase 3: 执行行动
        report.phase = LoopPhase.EXECUTE
        for action in actions[:self.max_actions_per_cycle]:
            executed = self._execute_action(
                action, user_id, scene, safety_engine, experience_replay
            )
            if executed:
                report.actions_executed += 1
                if action.status == ExecutionStatus.COMPLETED:
                    report.actions_succeeded += 1
                elif action.status == ExecutionStatus.FAILED:
                    report.actions_failed += 1

        # Phase 4: 反思
        report.phase = LoopPhase.REFLECT
        reflection = self._reflect_on_cycle(
            report, user_id, experience_replay
        )
        if reflection:
            findings.append(reflection)

        # Phase 5: 调整
        report.phase = LoopPhase.ADJUST
        adjusted_interval = self._adjust_strategy(report, scene)
        report.next_cycle_in = adjusted_interval

        # 保存循环报告
        report.duration = time.time() - start_time
        report.findings = " | ".join(findings)
        self._save_cycle_report(report)

        return report

    # ── Phase 1: Check Goals ───────────────────────────────────────────────

    def _check_goals(self, user_id: str, goal_manager) -> List[Dict]:
        """检查活跃目标"""
        if not goal_manager:
            return []

        goals = goal_manager.get_active_goals(user_id)
        result = []
        for g in goals:
            result.append({
                "goal_id": g.goal_id,
                "title": g.title,
                "priority": g.priority.value,
                "progress": g.progress,
            })
        return result

    # ── Phase 2: Plan Actions ─────────────────────────────────────────────

    def _plan_actions(
        self,
        user_id: str,
        scene: str,
        active_goals: List[Dict],
        goal_manager=None,
        goal_planner=None,
        experience_replay=None,
    ) -> List[AutonomousAction]:
        """基于目标和场景规划行动"""
        actions = []

        # 策略1: 如果有活跃目标，为目标生成行动
        for goal in active_goals:
            if goal["progress"] < 1.0:
                action = self._create_action_for_goal(goal)
                if action:
                    actions.append(action)

        # 策略2: 基于场景生成维护行动
        scene_actions = self._get_scene_maintenance_actions(scene)
        actions.extend(scene_actions)

        # 策略3: 基于经验生成学习行动
        if experience_replay:
            learn_actions = self._get_learning_actions(user_id, experience_replay)
            actions.extend(learn_actions)

        return actions

    def _create_action_for_goal(self, goal: Dict) -> Optional[AutonomousAction]:
        """为目标创建行动"""
        progress = goal.get("progress", 0)
        priority = goal.get("priority", "medium")

        # 高优先级+低进度 = 紧急行动
        if priority in ("critical", "high") and progress < 0.3:
            return AutonomousAction(
                action_id=f"action_{uuid.uuid4().hex[:10]}",
                action_type="urgent_goal_progress",
                description=f"推进高优先级目标: {goal['title']}",
                goal_id=goal["goal_id"],
                parameters={"goal_title": goal["title"], "current_progress": progress},
            )

        # 一般进度 = 常规推进
        if progress < 0.7:
            return AutonomousAction(
                action_id=f"action_{uuid.uuid4().hex[:10]}",
                action_type="goal_progress",
                description=f"继续推进目标: {goal['title']}",
                goal_id=goal["goal_id"],
                parameters={"goal_title": goal["title"], "current_progress": progress},
            )

        # 接近完成 = 验证完成
        if progress >= 0.7:
            return AutonomousAction(
                action_id=f"action_{uuid.uuid4().hex[:10]}",
                action_type="goal_verification",
                description=f"验证目标完成度: {goal['title']}",
                goal_id=goal["goal_id"],
                parameters={"goal_title": goal["title"]},
            )

        return None

    def _get_scene_maintenance_actions(self, scene: str) -> List[AutonomousAction]:
        """获取场景维护行动"""
        actions = []

        scene_actions = {
            "work": [
                AutonomousAction(
                    action_id=f"action_{uuid.uuid4().hex[:10]}",
                    action_type="organize_knowledge",
                    description="整理工作相关知识",
                    parameters={"scope": "work"},
                ),
            ],
            "learning": [
                AutonomousAction(
                    action_id=f"action_{uuid.uuid4().hex[:10]}",
                    action_type="review_experience",
                    description="回顾学习经验",
                    parameters={"scope": "learning"},
                ),
            ],
            "health": [
                AutonomousAction(
                    action_id=f"action_{uuid.uuid4().hex[:10]}",
                    action_type="update_profile",
                    description="更新健康状况记录",
                    parameters={"scope": "health"},
                ),
            ],
        }

        return scene_actions.get(scene, [])

    def _get_learning_actions(self, user_id: str, experience_replay) -> List[AutonomousAction]:
        """基于经验生成学习行动"""
        actions = []
        stats = experience_replay.get_user_stats(user_id)

        # 如果有大量失败经验，生成改进行动
        negative_count = stats.get("negative_count", 0)
        if negative_count > 3:
            actions.append(AutonomousAction(
                action_id=f"action_{uuid.uuid4().hex[:10]}",
                action_type="analyze_patterns",
                description=f"分析 {negative_count} 条失败经验提取改进模式",
                parameters={"focus": "failure_patterns", "count": negative_count},
            ))

        return actions

    # ── Phase 3: Execute Actions ──────────────────────────────────────────

    def _execute_action(
        self,
        action: AutonomousAction,
        user_id: str,
        scene: str,
        safety_engine=None,
        experience_replay=None,
    ) -> bool:
        """
        执行单个行动

        Returns:
            是否尝试执行
        """
        # 安全检查
        if safety_engine:
            assessment = safety_engine.assess_operation(
                user_id, action.action_type, action.description
            )
            action.safety_score = assessment.risk_score
            if assessment.risk_score > 0.7:
                action.status = ExecutionStatus.ABORTED
                action.result = f"安全风险过高({assessment.risk_score})，中止执行"
                self._save_action(action)
                return True

        # 根据执行级别决定是否执行
        if self.execution_level == ExecutionLevel.OBSERVE:
            action.status = ExecutionStatus.SKIPPED
            action.result = "观察模式，不执行行动"
            self._save_action(action)
            return True

        if self.execution_level == ExecutionLevel.SUGGEST:
            action.status = ExecutionStatus.SKIPPED
            action.result = f"建议执行: {action.description}"
            self._save_action(action)
            return True

        if self.execution_level == ExecutionLevel.CONFIRM:
            action.status = ExecutionStatus.SKIPPED
            action.result = f"等待确认: {action.description}"
            self._save_action(action)
            return True

        # 自主执行
        start = time.time()
        try:
            handler = self._action_handlers.get(action.action_type)
            if handler:
                result = handler(action, user_id, scene)
                action.status = ExecutionStatus.COMPLETED
                action.result = result
            else:
                action.status = ExecutionStatus.FAILED
                action.result = f"无处理器: {action.action_type}"
        except Exception as e:
            action.status = ExecutionStatus.FAILED
            action.result = f"执行异常: {str(e)}"

        action.executed_at = time.time()
        action.execution_time = action.executed_at - start

        # 记录为经验
        if experience_replay:
            self._record_as_experience(
                action, user_id, experience_replay
            )

        self._save_action(action)
        return True

    # ── Default Action Handlers ───────────────────────────────────────────

    def _handle_organize_knowledge(self, action, user_id, scene) -> str:
        """整理知识行动"""
        return f"已整理 {scene} 相关知识"

    def _handle_review_experience(self, action, user_id, scene) -> str:
        """回顾经验行动"""
        return f"已回顾 {scene} 相关经验"

    def _handle_update_profile(self, action, user_id, scene) -> str:
        """更新画像行动"""
        return f"已更新 {scene} 相关记录"

    def _handle_analyze_patterns(self, action, user_id, scene) -> str:
        """分析模式行动"""
        count = action.parameters.get("count", 0)
        return f"已分析 {count} 条失败经验"

    def _handle_optimize_workflow(self, action, user_id, scene) -> str:
        """优化流程行动"""
        return f"已优化 {scene} 工作流程"

    # ── Phase 4: Reflect ──────────────────────────────────────────────────

    def _reflect_on_cycle(
        self,
        report: CycleReport,
        user_id: str,
        experience_replay=None,
    ) -> str:
        """反思本次循环"""
        reflections = []

        if report.actions_executed == 0:
            reflections.append("本次循环无行动可执行")
            return " | ".join(reflections)

        success_rate = report.actions_succeeded / max(1, report.actions_executed)

        if success_rate >= 0.8:
            reflections.append(f"执行成功率高({success_rate:.0%})，系统运行良好")
        elif success_rate >= 0.5:
            reflections.append(f"执行成功率中等({success_rate:.0%})，需要关注失败原因")
        else:
            reflections.append(f"执行成功率低({success_rate:.0%})，建议降低自主级别")

        if report.actions_failed > 0:
            reflections.append(f"有 {report.actions_failed} 个行动失败，需分析原因")

        return " | ".join(reflections)

    # ── Phase 5: Adjust ───────────────────────────────────────────────────

    def _adjust_strategy(self, report: CycleReport, scene: str) -> float:
        """调整下次循环间隔"""
        interval = self.cycle_interval

        # 高成功率 = 可以延长间隔
        if report.actions_executed > 0:
            success_rate = report.actions_succeeded / report.actions_executed
            if success_rate >= 0.9:
                interval *= 1.5  # 延长50%
            elif success_rate < 0.3:
                interval *= 0.5  # 缩短50%

        # 根据场景调整
        if scene == "work":
            interval *= 0.8  # 工作场景更频繁
        elif scene == "health":
            interval *= 1.2  # 健康场景减少频率

        return max(60.0, min(interval, 86400.0))  # 限制在1分钟到24小时

    # ── Persistence ───────────────────────────────────────────────────────

    def _save_action(self, action: AutonomousAction):
        """保存行动记录"""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO autonomous_actions
            (action_id, action_type, description, goal_id, parameters,
             status, result, execution_time, safety_score, created_at, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                action.action_id, action.action_type, action.description,
                action.goal_id, json.dumps(action.parameters, ensure_ascii=False),
                action.status.value, action.result, action.execution_time,
                action.safety_score, action.created_at, action.executed_at,
            ),
        )
        conn.commit()
        self._maybe_close(conn)

    def _save_cycle_report(self, report: CycleReport):
        """保存循环报告"""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO cycle_reports
            (cycle_id, phase, actions_executed, actions_succeeded,
             actions_failed, duration, findings, next_cycle_in, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                report.cycle_id, report.phase.value,
                report.actions_executed, report.actions_succeeded,
                report.actions_failed, report.duration,
                report.findings, report.next_cycle_in, report.started_at,
            ),
        )
        conn.commit()
        self._maybe_close(conn)

    # ── Record as Experience ──────────────────────────────────────────────

    def _record_as_experience(self, action, user_id, experience_replay):
        """将自主行动记录为经验"""
        try:
            from nomad_mem.autonomy.experience_replay import ExperienceType, ExperienceOutcome
            exp_type = ExperienceType.SUCCESS if action.status == ExecutionStatus.COMPLETED else ExperienceType.FAILURE
            outcome = ExperienceOutcome.POSITIVE if action.status == ExecutionStatus.COMPLETED else ExperienceOutcome.NEGATIVE

            experience_replay.record_experience(
                user_id=user_id,
                intent=f"autonomous_{action.action_type}",
                context=json.dumps({"scene": "autonomous", "goal_id": action.goal_id}),
                action_taken=action.description,
                result=action.result,
                exp_type=exp_type,
                outcome=outcome,
                lesson_learned="",
                importance=0.3,
            )
        except Exception:
            pass  # Don't fail cycle if experience recording fails

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_action_stats(self, user_id: str = "") -> Dict:
        """获取行动统计"""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT COUNT(*) as total,
               SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
               SUM(CASE WHEN status='aborted' THEN 1 ELSE 0 END) as aborted,
               AVG(execution_time) as avg_time,
               AVG(safety_score) as avg_safety
               FROM autonomous_actions"""
        ).fetchone()
        self._maybe_close(conn)

        total = row["total"] or 0
        return {
            "total_actions": total,
            "completed_actions": row["completed"] or 0,
            "failed_actions": row["failed"] or 0,
            "aborted_actions": row["aborted"] or 0,
            "success_rate": (row["completed"] or 0) / total if total > 0 else 0.0,
            "avg_execution_time": round(row["avg_time"] or 0.0, 4),
            "avg_safety_score": round(row["avg_safety"] or 0.0, 4),
        }

    def get_cycle_history(self, k: int = 10) -> List[Dict]:
        """获取循环历史"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM cycle_reports
            ORDER BY started_at DESC LIMIT ?""",
            (k,),
        ).fetchall()
        self._maybe_close(conn)
        return [dict(r) for r in rows]

    def get_recent_actions(self, k: int = 20) -> List[Dict]:
        """获取最近的行动"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM autonomous_actions
            ORDER BY created_at DESC LIMIT ?""",
            (k,),
        ).fetchall()
        self._maybe_close(conn)
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        """获取系统总统计"""
        return {
            "actions": self.get_action_stats(),
            "execution_level": self.execution_level.value,
            "cycle_interval": self.cycle_interval,
            "recent_cycles": len(self.get_cycle_history(5)),
        }

    def close(self):
        if self._persistent_conn:
            self._persistent_conn.close()
            self._persistent_conn = None
