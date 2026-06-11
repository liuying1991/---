"""
Session Manager — 多轮会话管理器

基于 Dialog State Tracking (DST) 的会话管理模块，模拟真实对话式AI系统的会话生命周期。

核心特性:
- 会话状态机: ACTIVE / PAUSED / CLOSED / EXPIRED
- 对话行为追踪: GREET / QUERY / REQUEST / CONFIRM / DENY / INFORM / SUGGEST / CLOSE
- 槽位填充追踪: 类似表单填写的对话状态追踪
- SQLite 持久化: 轻量级本地存储，无外部依赖
- 会话自动过期: 可配置的空闲超时
- 上下文聚合: 从所有轮次聚合对话上下文
"""
import sqlite3
import time
import json
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


# ─── Enums ───────────────────────────────────────────────────────────────────


class SessionState(Enum):
    """会话状态"""
    ACTIVE = "active"       # 活跃中
    PAUSED = "paused"       # 暂停
    CLOSED = "closed"       # 已关闭
    EXPIRED = "expired"     # 已过期


class DialogAct(Enum):
    """对话行为 (Dialog Act)"""
    GREET = "greet"         # 问候
    QUERY = "query"         # 查询
    REQUEST = "request"     # 请求
    CONFIRM = "confirm"     # 确认
    DENY = "deny"           # 拒绝
    INFORM = "inform"       # 告知
    SUGGEST = "suggest"     # 建议
    CLOSE = "close"         # 结束


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class TurnInfo:
    """单轮对话信息"""
    turn_number: int
    user_utterance: str
    dialog_act: DialogAct
    entities: List[Dict[str, Any]] = field(default_factory=list)
    slots: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["dialog_act"] = self.dialog_act.value
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "TurnInfo":
        data = dict(data)
        data["dialog_act"] = DialogAct(data["dialog_act"])
        return cls(**data)


@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    user_id: str
    state: SessionState
    turns: List[TurnInfo] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    topic: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["state"] = self.state.value
        d["turns"] = [t.to_dict() for t in self.turns]
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "SessionInfo":
        data = dict(data)
        data["state"] = SessionState(data["state"])
        data["turns"] = [TurnInfo.from_dict(t) for t in data.get("turns", [])]
        return cls(**data)


# ─── SessionManager ──────────────────────────────────────────────────────────


class SessionManager:
    """
    会话管理器

    负责多轮会话的创建、追踪、持久化和生命周期管理。
    使用 SQLite 存储会话和轮次数据，支持对话状态追踪(DST)。

    Args:
        db_path: SQLite 数据库文件路径，默认使用内存数据库
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
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
            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL,
                state        TEXT NOT NULL DEFAULT 'active',
                topic        TEXT NOT NULL DEFAULT '',
                context      TEXT NOT NULL DEFAULT '{}',
                created_at   REAL NOT NULL,
                last_active  REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS turns (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id     TEXT NOT NULL,
                turn_number    INTEGER NOT NULL,
                user_utterance TEXT NOT NULL,
                dialog_act     TEXT NOT NULL,
                entities       TEXT NOT NULL DEFAULT '[]',
                slots          TEXT NOT NULL DEFAULT '{}',
                timestamp      REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);
            CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active);
        """)
        conn.commit()

    # ── Core Methods ──────────────────────────────────────────────────────

    def create_session(self, user_id: str, topic: str = "") -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID
            topic: 会话主题（可选）

        Returns:
            session_id: 新会话的ID
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = time.time()

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO sessions (session_id, user_id, state, topic, context, created_at, last_active) "
            "VALUES (?, ?, 'active', ?, '{}', ?, ?)",
            (session_id, user_id, topic, now, now),
        )
        conn.commit()
        return session_id

    def add_turn(
        self,
        session_id: str,
        user_utterance: str,
        dialog_act: DialogAct,
        entities: Optional[List[Dict[str, Any]]] = None,
        slots: Optional[Dict[str, Any]] = None,
    ) -> TurnInfo:
        """
        添加新对话轮次

        Args:
            session_id: 会话ID
            user_utterance: 用户话语
            dialog_act: 对话行为
            entities: 提取的实体列表
            slots: 槽位值（用于DST表单填充追踪）

        Returns:
            TurnInfo: 新轮次信息

        Raises:
            ValueError: 会话不存在或已关闭/过期
        """
        session = self._load_session_row(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        state = SessionState(session["state"])
        if state in (SessionState.CLOSED, SessionState.EXPIRED):
            raise ValueError(f"Session is {state.value}: {session_id}")

        conn = self._get_conn()

        # 获取当前轮次数
        row = conn.execute(
            "SELECT MAX(turn_number) FROM turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        turn_number = (row[0] or 0) + 1

        now = time.time()
        entities_json = json.dumps(entities or [], ensure_ascii=False)
        slots_json = json.dumps(slots or {}, ensure_ascii=False)

        conn.execute(
            "INSERT INTO turns (session_id, turn_number, user_utterance, dialog_act, entities, slots, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, turn_number, user_utterance, dialog_act.value, entities_json, slots_json, now),
        )

        # 更新会话最后活跃时间和累积上下文
        aggregated_ctx = self._compute_aggregated_context(session_id)
        conn.execute(
            "UPDATE sessions SET last_active = ?, context = ? WHERE session_id = ?",
            (now, json.dumps(aggregated_ctx, ensure_ascii=False), session_id),
        )
        conn.commit()

        return TurnInfo(
            turn_number=turn_number,
            user_utterance=user_utterance,
            dialog_act=dialog_act,
            entities=entities or [],
            slots=slots or {},
            timestamp=now,
        )

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            SessionInfo 或 None
        """
        row = self._load_session_row(session_id)
        if row is None:
            return None

        turns = self.get_session_history(session_id)
        context = json.loads(row["context"]) if row["context"] else {}

        return SessionInfo(
            session_id=row["session_id"],
            user_id=row["user_id"],
            state=SessionState(row["state"]),
            turns=turns,
            created_at=row["created_at"],
            last_active=row["last_active"],
            topic=row["topic"],
            context=context,
        )

    def get_session_history(self, session_id: str) -> List[TurnInfo]:
        """
        获取会话历史（所有轮次）

        Args:
            session_id: 会话ID

        Returns:
            轮次列表，按 turn_number 升序
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT turn_number, user_utterance, dialog_act, entities, slots, timestamp "
            "FROM turns WHERE session_id = ? ORDER BY turn_number ASC",
            (session_id,),
        ).fetchall()

        return [
            TurnInfo(
                turn_number=r["turn_number"],
                user_utterance=r["user_utterance"],
                dialog_act=DialogAct(r["dialog_act"]),
                entities=json.loads(r["entities"]) if r["entities"] else [],
                slots=json.loads(r["slots"]) if r["slots"] else {},
                timestamp=r["timestamp"],
            )
            for r in rows
        ]

    def close_session(self, session_id: str) -> bool:
        """
        关闭会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功关闭
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE sessions SET state = 'closed', last_active = ? WHERE session_id = ? AND state IN ('active', 'paused')",
            (time.time(), session_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_active_sessions(self, user_id: str) -> List[SessionInfo]:
        """
        获取用户的所有活跃会话

        Args:
            user_id: 用户ID

        Returns:
            活跃会话列表，按 last_active 降序
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? AND state = 'active' ORDER BY last_active DESC",
            (user_id,),
        ).fetchall()

        result = []
        for row in rows:
            turns = self.get_session_history(row["session_id"])
            context = json.loads(row["context"]) if row["context"] else {}
            result.append(SessionInfo(
                session_id=row["session_id"],
                user_id=row["user_id"],
                state=SessionState(row["state"]),
                turns=turns,
                created_at=row["created_at"],
                last_active=row["last_active"],
                topic=row["topic"],
                context=context,
            ))
        return result

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话聚合上下文（所有轮次的上下文聚合）

        包含:
        - filled_slots: 所有已填充的槽位（后值覆盖前值）
        - entities: 所有提取过的实体
        - dialog_acts: 出现过的对话行为
        - utterances: 所有用户话语
        - topic: 会话主题

        Args:
            session_id: 会话ID

        Returns:
            聚合上下文字典
        """
        return self._compute_aggregated_context(session_id)

    def detect_session_topic(self, session_id: str) -> str:
        """
        从会话内容检测主题

        策略:
        1. 如果已有topic且非空，直接返回
        2. 从第一轮包含实质内容的 QUERY/INFORM/REQUEST 中提取主题
        3. 取第一条有意义话语的前20个字符作为主题

        Args:
            session_id: 会话ID

        Returns:
            检测到的主题字符串
        """
        session = self._load_session_row(session_id)
        if session is None:
            return ""

        if session["topic"]:
            return session["topic"]

        turns = self.get_session_history(session_id)
        for turn in turns:
            if turn.dialog_act in (DialogAct.QUERY, DialogAct.INFORM, DialogAct.REQUEST):
                text = turn.user_utterance.strip()
                if text:
                    topic = text[:30] + ("..." if len(text) > 30 else "")
                    self._update_session_topic(session_id, topic)
                    return topic

        # 回退: 使用第一条非空话语
        for turn in turns:
            text = turn.user_utterance.strip()
            if text:
                topic = text[:30] + ("..." if len(text) > 30 else "")
                self._update_session_topic(session_id, topic)
                return topic

        return ""

    def cleanup_expired_sessions(self, max_idle_minutes: int = 30) -> int:
        """
        清理过期会话（超过指定空闲时间的活跃/暂停会话标记为过期）

        Args:
            max_idle_minutes: 最大空闲分钟数

        Returns:
            被标记为过期的会话数量
        """
        now = time.time()
        threshold = now - (max_idle_minutes * 60)

        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE sessions SET state = 'expired', last_active = ? "
            "WHERE state IN ('active', 'paused') AND last_active < ?",
            (now, threshold),
        )
        conn.commit()
        return cursor.rowcount

    def get_stats(self) -> Dict[str, Any]:
        """
        获取会话统计

        Returns:
            统计信息字典:
            - total_sessions: 总会话数
            - active: 活跃会话数
            - paused: 暂停会话数
            - closed: 已关闭会话数
            - expired: 已过期会话数
            - avg_turns_per_session: 平均每个会话的轮次数
            - total_turns: 总轮次数
        """
        conn = self._get_conn()

        # 按状态统计
        row = conn.execute(
            "SELECT "
            "COUNT(*) as total, "
            "SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active, "
            "SUM(CASE WHEN state = 'paused' THEN 1 ELSE 0 END) as paused, "
            "SUM(CASE WHEN state = 'closed' THEN 1 ELSE 0 END) as closed, "
            "SUM(CASE WHEN state = 'expired' THEN 1 ELSE 0 END) as expired "
            "FROM sessions"
        ).fetchone()

        total = row["total"] or 0
        total_turns = conn.execute("SELECT COUNT(*) as cnt FROM turns").fetchone()["cnt"] or 0
        avg_turns = total_turns / total if total > 0 else 0.0

        return {
            "total_sessions": total,
            "active": row["active"] or 0,
            "paused": row["paused"] or 0,
            "closed": row["closed"] or 0,
            "expired": row["expired"] or 0,
            "avg_turns_per_session": round(avg_turns, 2),
            "total_turns": total_turns,
        }

    def pause_session(self, session_id: str) -> bool:
        """
        暂停会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功暂停
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE sessions SET state = 'paused', last_active = ? WHERE session_id = ? AND state = 'active'",
            (time.time(), session_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def resume_session(self, session_id: str) -> bool:
        """
        恢复暂停的会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功恢复
        """
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE sessions SET state = 'active', last_active = ? WHERE session_id = ? AND state = 'paused'",
            (time.time(), session_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _load_session_row(self, session_id: str) -> Optional[sqlite3.Row]:
        conn = self._get_conn()
        return conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()

    def _compute_aggregated_context(self, session_id: str) -> Dict[str, Any]:
        """计算聚合上下文"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT dialog_act, entities, slots, user_utterance "
            "FROM turns WHERE session_id = ? ORDER BY turn_number ASC",
            (session_id,),
        ).fetchall()

        filled_slots = {}
        all_entities = []
        dialog_acts = []
        utterances = []

        for r in rows:
            dialog_acts.append(r["dialog_act"])
            utterances.append(r["user_utterance"])

            ents = json.loads(r["entities"]) if r["entities"] else []
            all_entities.extend(ents)

            slts = json.loads(r["slots"]) if r["slots"] else {}
            filled_slots.update(slts)  # 后值覆盖前值

        session_row = self._load_session_row(session_id)
        topic = session_row["topic"] if session_row else ""

        return {
            "filled_slots": filled_slots,
            "entities": all_entities,
            "dialog_acts": dialog_acts,
            "utterances": utterances,
            "topic": topic,
            "turn_count": len(rows),
        }

    def _update_session_topic(self, session_id: str, topic: str):
        conn = self._get_conn()
        conn.execute(
            "UPDATE sessions SET topic = ? WHERE session_id = ?",
            (topic, session_id),
        )
        conn.commit()
