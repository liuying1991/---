"""
Dialog Flow Manager — 多轮对话流程管理器

管理多轮对话流程，支持追问、确认、菜单选择、表单填写等交互模式。
Jarvis 通过引导式对话自然推进，像真人管家一样与用户沟通。

核心特性:
- 对话流程状态机: WAITING / ACTIVE / COMPLETED / CANCELLED / ERROR
- 流程类型: FOLLOW_UP / CONFIRMATION / MENU / MULTI_CHOICE / FILL_FORM / COLLECT_INFO
- 步骤级验证: 每步可配置输入验证规则，验证通过才进入下一步
- SQLite 持久化: 轻量级本地存储，支持流程恢复
- 快捷创建: 确认/菜单/表单等常见模式的便捷构造器
- 多用户隔离: 按 user_id 隔离活跃流程
"""
import sqlite3
import time
import json
import re
import uuid
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# ─── Enums ───────────────────────────────────────────────────────────────────


class FlowState(Enum):
    """对话流程状态"""
    WAITING = "waiting"           # 等待用户响应
    ACTIVE = "active"             # 流程进行中
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消
    ERROR = "error"               # 出错


class FlowType(Enum):
    """对话流程类型"""
    FOLLOW_UP = "follow_up"         # 追问
    CONFIRMATION = "confirmation"   # 确认（是/否）
    MENU = "menu"                   # 菜单选择（单选）
    MULTI_CHOICE = "multi_choice"   # 多选
    FILL_FORM = "fill_form"         # 表单填写
    COLLECT_INFO = "collect_info"   # 信息采集


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class FlowStep:
    """对话流程中的单个步骤"""
    step_id: str                                  # 步骤唯一标识
    step_type: FlowType                           # 步骤类型
    prompt: str                                   # 向用户展示的问题/提示
    expected_input_type: str = "text"             # 期望输入类型: text/number/choice/confirm/list
    validation: Optional[Dict[str, Any]] = None   # 验证规则 {type, pattern, min, max, options, custom_fn_name}
    options: List[str] = field(default_factory=list)  # 选项列表（菜单类型使用）
    required: bool = True                         # 是否必填
    help_text: str = ""                           # 帮助说明文本
    default_value: Any = None                     # 默认值
    error_message: str = "您的回答不符合要求，请重新回答。"  # 验证失败时的提示
    max_retries: int = 3                          # 最大重试次数

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["step_type"] = self.step_type.value
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "FlowStep":
        data = dict(data)
        data["step_type"] = FlowType(data["step_type"])
        if data.get("validation") and isinstance(data["validation"], str):
            data["validation"] = json.loads(data["validation"])
        if data.get("options") and isinstance(data["options"], str):
            data["options"] = json.loads(data["options"])
        return cls(**data)


@dataclass
class DialogFlow:
    """一个完整的对话流程"""
    flow_id: str                                  # 流程唯一标识
    flow_type: FlowType                           # 流程类型
    state: FlowState = FlowState.WAITING          # 当前状态
    current_step_index: int = 0                   # 当前步骤索引
    steps: List[FlowStep] = field(default_factory=list)  # 流程步骤列表
    context: Dict[str, Any] = field(default_factory=dict)  # 流程上下文
    result: Dict[str, Any] = field(default_factory=dict)   # 流程结果（各步骤收集的值）
    user_id: str = ""                             # 关联用户ID
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None          # 完成时间
    retry_count: int = 0                          # 当前步骤重试次数
    parent_flow_id: Optional[str] = None          # 父流程ID（子流程嵌套）
    error_message: str = ""                       # 错误信息

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["flow_type"] = self.flow_type.value
        d["state"] = self.state.value
        d["steps"] = [s.to_dict() for s in self.steps]
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "DialogFlow":
        data = dict(data)
        data["flow_type"] = FlowType(data["flow_type"])
        data["state"] = FlowState(data["state"])
        data["steps"] = [FlowStep.from_dict(s) for s in data.get("steps", [])]
        if data.get("context") and isinstance(data["context"], str):
            data["context"] = json.loads(data["context"])
        if data.get("result") and isinstance(data["result"], str):
            data["result"] = json.loads(data["result"])
        return cls(**data)


# ─── DialogFlowManager ───────────────────────────────────────────────────────


class DialogFlowManager:
    """
    对话流程管理器

    负责多轮对话流程的创建、推进、验证和持久化。
    支持多种交互模式：确认、菜单、表单、追问等。
    使用 SQLite 存储流程数据，支持流程中断恢复。

    Args:
        db_path: SQLite 数据库文件路径，默认使用内存数据库
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        # 注册自定义验证函数
        self._custom_validators: Dict[str, Callable] = {}
        self._init_db()

    # ── Database ──────────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS dialog_flows (
                flow_id          TEXT PRIMARY KEY,
                flow_type        TEXT NOT NULL,
                state            TEXT NOT NULL DEFAULT 'waiting',
                current_step     INTEGER NOT NULL DEFAULT 0,
                steps            TEXT NOT NULL DEFAULT '[]',
                context          TEXT NOT NULL DEFAULT '{}',
                result           TEXT NOT NULL DEFAULT '{}',
                user_id          TEXT NOT NULL DEFAULT '',
                created_at       REAL NOT NULL,
                updated_at       REAL NOT NULL,
                completed_at     REAL,
                retry_count      INTEGER NOT NULL DEFAULT 0,
                parent_flow_id   TEXT,
                error_message    TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_flows_user ON dialog_flows(user_id);
            CREATE INDEX IF NOT EXISTS idx_flows_state ON dialog_flows(state);
            CREATE INDEX IF NOT EXISTS idx_flows_type ON dialog_flows(flow_type);
            CREATE INDEX IF NOT EXISTS idx_flows_parent ON dialog_flows(parent_flow_id);
        """)
        conn.commit()

    # ── Custom Validators ─────────────────────────────────────────────────

    def register_validator(self, name: str, validator_fn: Callable[[str], bool]):
        """
        注册自定义验证函数

        Args:
            name: 验证函数名称（在 FlowStep.validation['custom_fn_name'] 中引用）
            validator_fn: 验证函数，接受用户输入字符串，返回 bool
        """
        self._custom_validators[name] = validator_fn

    # ── Core Methods ──────────────────────────────────────────────────────

    def start_flow(
        self,
        flow_type: FlowType,
        steps: List[FlowStep],
        context: Optional[Dict[str, Any]] = None,
        user_id: str = "",
        parent_flow_id: Optional[str] = None,
    ) -> str:
        """
        启动新的对话流程

        Args:
            flow_type: 流程类型
            steps: 流程步骤列表
            context: 流程上下文（可选）
            user_id: 关联用户ID
            parent_flow_id: 父流程ID（用于子流程嵌套）

        Returns:
            flow_id: 新流程的ID
        """
        flow_id = f"flow_{uuid.uuid4().hex[:12]}"
        now = time.time()

        conn = self._get_conn()
        conn.execute(
            """INSERT INTO dialog_flows (
                flow_id, flow_type, state, current_step, steps, context, result,
                user_id, created_at, updated_at, parent_flow_id
            ) VALUES (?, ?, 'waiting', 0, ?, ?, '{}', ?, ?, ?, ?)""",
            (
                flow_id,
                flow_type.value,
                json.dumps([s.to_dict() for s in steps], ensure_ascii=False),
                json.dumps(context or {}, ensure_ascii=False),
                user_id,
                now,
                now,
                parent_flow_id,
            ),
        )
        conn.commit()

        # 自动将状态推进到 ACTIVE
        self._update_flow_state(flow_id, FlowState.ACTIVE)

        return flow_id

    def create_confirmation_flow(
        self,
        question: str,
        yes_action: str = "",
        no_action: str = "",
        user_id: str = "",
    ) -> str:
        """
        快捷创建: 是/否确认流程

        Args:
            question: 确认问题
            yes_action: 确认后的动作描述
            no_action: 拒绝后的动作描述
            user_id: 关联用户ID

        Returns:
            flow_id: 新流程的ID
        """
        yes_label = yes_action or "确认执行"
        no_label = no_action or "取消"

        steps = [
            FlowStep(
                step_id="confirm_1",
                step_type=FlowType.CONFIRMATION,
                prompt=f"{question}\n请输入 'y' 确认（{yes_label}）或 'n' 拒绝（{no_label}）：",
                expected_input_type="confirm",
                options=["y", "n"],
                required=True,
            )
        ]

        return self.start_flow(
            flow_type=FlowType.CONFIRMATION,
            steps=steps,
            context={"yes_action": yes_action, "no_action": no_action},
            user_id=user_id,
        )

    def create_menu_flow(
        self,
        question: str,
        options: List[str],
        user_id: str = "",
    ) -> str:
        """
        快捷创建: 菜单选项流程（单选）

        Args:
            question: 菜单问题
            options: 选项列表
            user_id: 关联用户ID

        Returns:
            flow_id: 新流程的ID
        """
        options_display = "\n".join(f"  {i + 1}. {opt}" for i, opt in enumerate(options))
        prompt = f"{question}\n{options_display}\n请输入选项编号（1-{len(options)}）或选项名称："

        steps = [
            FlowStep(
                step_id="menu_1",
                step_type=FlowType.MENU,
                prompt=prompt,
                expected_input_type="choice",
                options=options,
                required=True,
                validation={"options": options},
            )
        ]

        return self.start_flow(
            flow_type=FlowType.MENU,
            steps=steps,
            user_id=user_id,
        )

    def create_form_flow(
        self,
        fields: List[Dict[str, Any]],
        title: str = "请填写以下信息",
        user_id: str = "",
    ) -> str:
        """
        快捷创建: 表单填写流程

        Args:
            fields: 字段列表，每项为 dict:
                - name: 字段名
                - prompt: 提示问题
                - type: 输入类型 (text/number/confirm)
                - required: 是否必填 (默认 True)
                - options: 选项列表（可选）
                - validation: 验证规则（可选）
                - help_text: 帮助文本（可选）
                - default_value: 默认值（可选）
            title: 表单标题
            user_id: 关联用户ID

        Returns:
            flow_id: 新流程的ID
        """
        steps = []
        for i, f in enumerate(fields):
            step = FlowStep(
                step_id=f"field_{f['name']}",
                step_type=FlowType.FILL_FORM,
                prompt=f"[{i + 1}/{len(fields)}] {title}\n{f['prompt']}",
                expected_input_type=f.get("type", "text"),
                required=f.get("required", True),
                options=f.get("options", []),
                validation=f.get("validation"),
                help_text=f.get("help_text", ""),
                default_value=f.get("default_value"),
            )
            steps.append(step)

        return self.start_flow(
            flow_type=FlowType.FILL_FORM,
            steps=steps,
            user_id=user_id,
        )

    def get_current_flow(self, flow_id: str) -> Optional[DialogFlow]:
        """
        获取当前流程状态

        Args:
            flow_id: 流程ID

        Returns:
            DialogFlow 或 None（流程不存在时）
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM dialog_flows WHERE flow_id = ?",
            (flow_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_flow(row)

    def get_current_prompt(self, flow_id: str) -> Optional[str]:
        """
        获取当前步骤的提示文本

        Args:
            flow_id: 流程ID

        Returns:
            当前步骤的 prompt 文本，流程不存在或无当前步骤时返回 None
        """
        flow = self.get_current_flow(flow_id)
        if flow is None:
            return None

        if flow.state not in (FlowState.WAITING, FlowState.ACTIVE):
            return None

        step = flow.steps[flow.current_step_index] if flow.current_step_index < len(flow.steps) else None
        if step is None:
            return None

        # 构建带帮助文本的提示
        prompt = step.prompt
        if step.help_text:
            prompt += f"\n💡 提示: {step.help_text}"

        # 如果重试次数 > 0，添加重试提示
        if flow.retry_count > 0:
            prompt += f"\n⚠️ 已重试 {flow.retry_count}/{step.max_retries} 次"

        # 如果是菜单类型，显示已收集的字段
        if flow.flow_type == FlowType.FILL_FORM and flow.result:
            collected = ", ".join(f"{k}: {v}" for k, v in flow.result.items())
            prompt += f"\n📋 已填写: {collected}"

        return prompt

    def process_response(self, flow_id: str, user_response: str) -> Dict[str, Any]:
        """
        处理用户响应

        Args:
            flow_id: 流程ID
            user_response: 用户响应文本

        Returns:
            Dict:
                - next_prompt: 下一步提示文本（None 表示流程结束）
                - completed: 流程是否已完成
                - result: 流程收集的结果
                - error: 错误信息（如果有）
                - step_validated: 当前步骤是否验证通过
                - retry_count: 当前步骤重试次数
        """
        result = {
            "next_prompt": None,
            "completed": False,
            "result": {},
            "error": None,
            "step_validated": False,
            "retry_count": 0,
        }

        flow = self.get_current_flow(flow_id)
        if flow is None:
            result["error"] = f"流程不存在: {flow_id}"
            return result

        if flow.state not in (FlowState.WAITING, FlowState.ACTIVE):
            result["error"] = f"流程状态不允许响应: {flow.state.value}"
            return result

        if flow.current_step_index >= len(flow.steps):
            # 所有步骤已完成
            self._complete_flow(flow_id, flow.result)
            result["completed"] = True
            result["result"] = flow.result
            return result

        step = flow.steps[flow.current_step_index]

        # ── 验证输入 ──
        validated, error_msg = self._validate_input(step, user_response)
        if not validated:
            flow.retry_count += 1
            if flow.retry_count >= step.max_retries:
                # 超过最大重试次数，跳过当前步骤（如果非必填）或终止流程
                if not step.required:
                    # 非必填字段，使用默认值并跳过
                    flow.result[step.step_id] = step.default_value
                    conn = self._get_conn()
                    conn.execute(
                        "UPDATE dialog_flows SET result = ?, updated_at = ? WHERE flow_id = ?",
                        (json.dumps(flow.result, ensure_ascii=False), time.time(), flow_id),
                    )
                    conn.commit()
                    self._advance_step(flow_id)
                    result["step_validated"] = True
                    result["retry_count"] = flow.retry_count
                    return self._build_next_result(flow_id)
                else:
                    # 必填字段，超过重试次数则标记流程为 ERROR
                    self._set_flow_error(flow_id, f"步骤 '{step.step_id}' 验证失败超过 {step.max_retries} 次: {error_msg}")
                    result["error"] = f"验证失败次数过多，流程已终止: {error_msg}"
                    return result
            else:
                # 更新重试计数
                conn = self._get_conn()
                conn.execute(
                    "UPDATE dialog_flows SET retry_count = ?, updated_at = ? WHERE flow_id = ?",
                    (flow.retry_count, time.time(), flow_id),
                )
                conn.commit()
                result["error"] = error_msg or step.error_message
                result["retry_count"] = flow.retry_count
                return result

        # ── 输入验证通过，存储结果 ──
        step_value = self._extract_value(step, user_response)
        flow.result[step.step_id] = step_value

        # 持久化结果到数据库
        conn = self._get_conn()
        conn.execute(
            "UPDATE dialog_flows SET result = ?, updated_at = ? WHERE flow_id = ?",
            (json.dumps(flow.result, ensure_ascii=False), time.time(), flow_id),
        )
        conn.commit()

        # ── 推进到下一步 ──
        self._advance_step(flow_id)

        return self._build_next_result(flow_id)

    def cancel_flow(self, flow_id: str) -> bool:
        """
        取消流程

        Args:
            flow_id: 流程ID

        Returns:
            是否成功取消
        """
        return self._update_flow_state(flow_id, FlowState.CANCELLED)

    def complete_flow(self, flow_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        标记流程为已完成

        Args:
            flow_id: 流程ID
            result: 流程最终结果（可选，如果提供则覆盖当前结果）

        Returns:
            是否成功标记为完成
        """
        if result is not None:
            conn = self._get_conn()
            conn.execute(
                "UPDATE dialog_flows SET result = ?, updated_at = ? WHERE flow_id = ?",
                (json.dumps(result, ensure_ascii=False), time.time(), flow_id),
            )
            conn.commit()
        return self._complete_flow(flow_id, result or {})

    def get_active_flows(self, user_id: str) -> List[DialogFlow]:
        """
        获取用户的活跃流程

        Args:
            user_id: 用户ID

        Returns:
            活跃流程列表（状态为 WAITING 或 ACTIVE），按 updated_at 降序
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM dialog_flows
               WHERE user_id = ? AND state IN ('waiting', 'active')
               ORDER BY updated_at DESC""",
            (user_id,),
        ).fetchall()

        return [self._row_to_flow(r) for r in rows]

    def has_active_flow(self, user_id: str) -> bool:
        """
        检查用户是否有活跃流程

        Args:
            user_id: 用户ID

        Returns:
            True 如果有活跃流程
        """
        conn = self._get_conn()
        row = conn.execute(
            """SELECT COUNT(*) as cnt FROM dialog_flows
               WHERE user_id = ? AND state IN ('waiting', 'active')""",
            (user_id,),
        ).fetchone()
        return (row["cnt"] or 0) > 0

    def resume_flow(self, flow_id: str) -> bool:
        """
        恢复已取消的流程

        Args:
            flow_id: 流程ID

        Returns:
            是否成功恢复
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE dialog_flows SET state = 'waiting', updated_at = ?, error_message = '' "
            "WHERE flow_id = ? AND state = 'cancelled'",
            (time.time(), flow_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取流程统计信息

        Returns:
            统计信息字典:
            - total_flows: 总流程数
            - by_type: 各类型流程数量
            - by_state: 各状态流程数量
            - completion_rate: 完成率
            - avg_steps_completed: 平均完成步骤数
        """
        conn = self._get_conn()

        # 总数
        total = conn.execute("SELECT COUNT(*) as cnt FROM dialog_flows").fetchone()["cnt"] or 0

        # 按类型统计
        type_rows = conn.execute(
            "SELECT flow_type, COUNT(*) as cnt FROM dialog_flows GROUP BY flow_type"
        ).fetchall()
        by_type = {r["flow_type"]: r["cnt"] for r in type_rows}

        # 按状态统计
        state_rows = conn.execute(
            "SELECT state, COUNT(*) as cnt FROM dialog_flows GROUP BY state"
        ).fetchall()
        by_state = {r["state"]: r["cnt"] for r in state_rows}

        # 完成率
        completed = by_state.get("completed", 0)
        completion_rate = (completed / total * 100) if total > 0 else 0.0

        # 平均完成步骤数
        all_flows = conn.execute("SELECT steps, current_step, state FROM dialog_flows").fetchall()
        total_steps_completed = 0
        total_flow_count = 0
        for r in all_flows:
            steps = json.loads(r["steps"]) if r["steps"] else []
            step_count = len(steps)
            if step_count > 0:
                if r["state"] == "completed":
                    total_steps_completed += step_count
                else:
                    total_steps_completed += r["current_step"]
                total_flow_count += 1

        avg_steps = total_steps_completed / total_flow_count if total_flow_count > 0 else 0.0

        return {
            "total_flows": total,
            "by_type": by_type,
            "by_state": by_state,
            "completion_rate": round(completion_rate, 2),
            "avg_steps_completed": round(avg_steps, 2),
        }

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _row_to_flow(self, row: sqlite3.Row) -> DialogFlow:
        """将数据库行转换为 DialogFlow 对象"""
        return DialogFlow(
            flow_id=row["flow_id"],
            flow_type=FlowType(row["flow_type"]),
            state=FlowState(row["state"]),
            current_step_index=row["current_step"],
            steps=[FlowStep.from_dict(s) for s in json.loads(row["steps"])],
            context=json.loads(row["context"]) if row["context"] else {},
            result=json.loads(row["result"]) if row["result"] else {},
            user_id=row["user_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            retry_count=row["retry_count"],
            parent_flow_id=row["parent_flow_id"],
            error_message=row["error_message"],
        )

    def _update_flow_state(self, flow_id: str, state: FlowState) -> bool:
        """更新流程状态"""
        now = time.time()
        completed_at = now if state == FlowState.COMPLETED else None

        conn = self._get_conn()
        cursor = conn.execute(
            """UPDATE dialog_flows
               SET state = ?, updated_at = ?, completed_at = COALESCE(?, completed_at)
               WHERE flow_id = ?""",
            (state.value, now, completed_at, flow_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def _complete_flow(self, flow_id: str, result: Dict[str, Any]) -> bool:
        """标记流程为已完成"""
        now = time.time()
        conn = self._get_conn()
        cursor = conn.execute(
            """UPDATE dialog_flows
               SET state = 'completed', updated_at = ?, completed_at = ?, result = ?
               WHERE flow_id = ?""",
            (now, now, json.dumps(result, ensure_ascii=False), flow_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def _set_flow_error(self, flow_id: str, error_message: str) -> bool:
        """标记流程为出错"""
        now = time.time()
        conn = self._get_conn()
        cursor = conn.execute(
            """UPDATE dialog_flows
               SET state = 'error', updated_at = ?, error_message = ?
               WHERE flow_id = ?""",
            (now, error_message, flow_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def _advance_step(self, flow_id: str) -> bool:
        """推进到下一步"""
        conn = self._get_conn()
        cursor = conn.execute(
            """UPDATE dialog_flows
               SET current_step = current_step + 1,
                   retry_count = 0,
                   updated_at = ?
               WHERE flow_id = ?""",
            (time.time(), flow_id),
        )
        conn.commit()

        # 检查是否所有步骤都已完成
        flow = self.get_current_flow(flow_id)
        if flow and flow.current_step_index >= len(flow.steps):
            self._complete_flow(flow_id, flow.result)

        return cursor.rowcount > 0

    def _build_next_result(self, flow_id: str) -> Dict[str, Any]:
        """构建下一步的结果响应"""
        flow = self.get_current_flow(flow_id)
        if flow is None:
            return {
                "next_prompt": None,
                "completed": False,
                "result": {},
                "error": "流程不存在",
                "step_validated": False,
                "retry_count": 0,
            }

        if flow.state == FlowState.COMPLETED:
            return {
                "next_prompt": None,
                "completed": True,
                "result": flow.result,
                "error": None,
                "step_validated": True,
                "retry_count": 0,
            }

        if flow.state == FlowState.ERROR:
            return {
                "next_prompt": None,
                "completed": False,
                "result": flow.result,
                "error": flow.error_message,
                "step_validated": True,
                "retry_count": 0,
            }

        next_prompt = self.get_current_prompt(flow_id)
        return {
            "next_prompt": next_prompt,
            "completed": False,
            "result": flow.result,
            "error": None,
            "step_validated": True,
            "retry_count": flow.retry_count,
        }

    # ── Validation ────────────────────────────────────────────────────────

    def _validate_input(self, step: FlowStep, user_response: str) -> tuple:
        """
        验证用户输入

        Returns:
            (是否通过, 错误信息)
        """
        # 空输入检查
        if not user_response.strip():
            if step.required:
                return False, "此问题必填，请输入您的回答。"
            else:
                return True, None

        text = user_response.strip()

        # ── 确认类型验证 ──
        if step.expected_input_type == "confirm":
            if text.lower() in ("y", "yes", "是", "对", "确认", "确认执行"):
                return True, None
            elif text.lower() in ("n", "no", "否", "不", "取消"):
                return True, None
            else:
                return False, "请输入 'y'（确认）或 'n'（拒绝）。"

        # ── 数字类型验证 ──
        if step.expected_input_type == "number":
            try:
                num = float(text)
                validation = step.validation or {}
                min_val = validation.get("min")
                max_val = validation.get("max")
                if min_val is not None and num < min_val:
                    return False, f"请输入大于等于 {min_val} 的数字。"
                if max_val is not None and num > max_val:
                    return False, f"请输入小于等于 {max_val} 的数字。"
                return True, None
            except ValueError:
                return False, "请输入有效的数字。"

        # ── 选项选择验证（菜单/单选） ──
        if step.expected_input_type == "choice":
            validation = step.validation or {}
            options = validation.get("options", step.options)
            # 支持编号（1-indexed）或文本匹配
            try:
                idx = int(text)
                if 1 <= idx <= len(options):
                    return True, None
            except ValueError:
                pass
            # 文本匹配（不区分大小写）
            if any(text.lower() == opt.lower() for opt in options):
                return True, None
            return False, f"请选择有效的选项（1-{len(options)} 或选项名称）。"

        # ── 列表类型验证（多选） ──
        if step.expected_input_type == "list":
            validation = step.validation or {}
            options = validation.get("options", step.options)
            items = [item.strip() for item in text.replace("，", ",").split(",")]
            invalid_items = []
            for item in items:
                # 检查是否为数字编号
                try:
                    idx = int(item)
                    if 1 <= idx <= len(options):
                        continue
                except ValueError:
                    pass
                # 文本匹配
                if any(item.lower() == opt.lower() for opt in options):
                    continue
                invalid_items.append(item)

            if invalid_items:
                return False, f"选项 '{', '.join(invalid_items)}' 无效。有效选项: {', '.join(options)}"
            return True, None

        # ── 正则表达式验证 ──
        validation = step.validation or {}
        pattern = validation.get("pattern")
        if pattern:
            if not re.match(pattern, text):
                return False, f"输入格式不正确。{validation.get('pattern_error', '请检查输入格式。')}"

        # ── 自定义验证函数 ──
        custom_fn_name = validation.get("custom_fn_name")
        if custom_fn_name and custom_fn_name in self._custom_validators:
            validator = self._custom_validators[custom_fn_name]
            try:
                if not validator(text):
                    return False, validation.get("custom_error", step.error_message)
            except Exception as e:
                return False, f"验证函数执行出错: {str(e)}"

        return True, None

    def _extract_value(self, step: FlowStep, user_response: str) -> Any:
        """从用户响应中提取结构化值"""
        text = user_response.strip()

        if step.expected_input_type == "confirm":
            return text.lower() in ("y", "yes", "是", "对", "确认", "确认执行")

        if step.expected_input_type == "number":
            num = float(text)
            return int(num) if num == int(num) else num

        if step.expected_input_type == "choice":
            try:
                idx = int(text)
                if 1 <= idx <= len(step.options):
                    return step.options[idx - 1]
            except ValueError:
                pass
            # 查找匹配的选项
            for opt in step.options:
                if text.lower() == opt.lower():
                    return opt
            return text

        if step.expected_input_type == "list":
            items = [item.strip() for item in text.replace("，", ",").split(",")]
            result = []
            for item in items:
                try:
                    idx = int(item)
                    if 1 <= idx <= len(step.options):
                        result.append(step.options[idx - 1])
                        continue
                except ValueError:
                    pass
                for opt in step.options:
                    if item.lower() == opt.lower():
                        result.append(opt)
                        break
                else:
                    result.append(item)
            return result

        return text
