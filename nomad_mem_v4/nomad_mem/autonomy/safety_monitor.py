"""
Safety Monitor - 自主安全监控器

实时监控Jarvis操作，检测异常行为，自动响应安全事件。

核心特性:
- 实时监控: 持续监控操作流
- 异常检测: 检测频率异常、模式异常、风险累积
- 自动响应: 自动限速、暂停、告警
- 安全事件记录: 记录和分析安全事件
"""
import time
import sqlite3
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


class EventType(Enum):
    """安全事件类型"""
    FREQUENCY_SPIKE = "frequency_spike"
    PATTERN_CHANGE = "pattern_change"
    RISK_ACCUMULATION = "risk_accumulation"
    UNUSUAL_HOUR = "unusual_hour"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    REPEATED_FAILURE = "repeated_failure"


class ResponseAction(Enum):
    """监控响应动作"""
    NONE = "none"
    ALERT = "alert"
    THROTTLE = "throttle"
    PAUSE = "pause"
    LOCKDOWN = "lockdown"


@dataclass
class SafetyEvent:
    """安全事件"""
    event_id: str
    event_type: EventType
    user_id: str
    severity: float
    description: str
    response: ResponseAction
    timestamp: float = field(default_factory=time.time)
    details: str = ""

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "severity": self.severity,
            "description": self.description,
            "response": self.response.value,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class SafetyMonitor:
    """
    自主安全监控器

    实时监控用户操作，检测异常，自动响应。
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_db()
        self._recent_ops: Dict[str, List[Dict]] = defaultdict(list)
        self._user_states: Dict[str, Dict] = {}
        self._events: List[SafetyEvent] = []
        self.frequency_threshold = 20
        self.risk_accumulation_threshold = 3.0
        self.window_seconds = 60

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS safety_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                severity REAL NOT NULL,
                description TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp REAL NOT NULL,
                details TEXT DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON safety_events(user_id)")
        conn.commit()
        conn.close()

    def report_operation(self, user_id: str, action: str, risk_score: float = 0.0, target: str = ""):
        """报告用户操作"""
        now = time.time()
        op = {"timestamp": now, "action": action, "risk_score": risk_score, "target": target}
        self._recent_ops[user_id].append(op)
        cutoff = now - self.window_seconds * 5
        self._recent_ops[user_id] = [o for o in self._recent_ops[user_id] if o["timestamp"] > cutoff]
        self._update_user_state(user_id, op)

    def check_anomalies(self, user_id: str) -> List[SafetyEvent]:
        """检查用户异常"""
        events = []
        for check in [self._check_frequency, self._check_risk_accumulation,
                      self._check_pattern_change, self._check_unusual_hour]:
            event = check(user_id)
            if event:
                events.append(event)
        return events

    def get_user_status(self, user_id: str) -> Dict:
        """获取用户安全状态"""
        ops = self._recent_ops.get(user_id, [])
        recent = [o for o in ops if o["timestamp"] > time.time() - self.window_seconds]
        state = self._user_states.get(user_id, {})
        return {
            "user_id": user_id,
            "total_ops": len(ops),
            "recent_ops": len(recent),
            "ops_per_minute": len(recent),
            "avg_risk": state.get("avg_risk", 0.0),
            "max_risk": state.get("max_risk", 0.0),
            "risk_accumulation": state.get("risk_accumulation", 0.0),
            "current_response": state.get("response", ResponseAction.NONE.value),
        }

    def get_events(self, user_id: str = "", k: int = 20) -> List[Dict]:
        """获取安全事件"""
        filtered = [e for e in self._events if not user_id or e.user_id == user_id]
        return [e.to_dict() for e in filtered[-k:]]

    def set_threshold(self, frequency: int = None, risk_accumulation: float = None):
        """设置阈值"""
        if frequency is not None:
            self.frequency_threshold = frequency
        if risk_accumulation is not None:
            self.risk_accumulation_threshold = risk_accumulation

    def get_stats(self) -> Dict:
        """获取监控统计"""
        conn = self._get_conn()
        total_events = conn.execute("SELECT COUNT(*) FROM safety_events").fetchone()[0]
        conn.close()
        return {
            "total_events_recorded": total_events,
            "active_users": len(self._recent_ops),
            "frequency_threshold": self.frequency_threshold,
            "risk_accumulation_threshold": self.risk_accumulation_threshold,
        }

    def close(self):
        pass

    # ── Internal ──

    def _update_user_state(self, user_id: str, op: Dict):
        if user_id not in self._user_states:
            self._user_states[user_id] = {
                "avg_risk": 0.0, "max_risk": 0.0, "risk_accumulation": 0.0,
                "response": ResponseAction.NONE.value,
                "action_counts": defaultdict(int),
            }
        state = self._user_states[user_id]
        risk = op["risk_score"]
        state["avg_risk"] = (state["avg_risk"] + risk) / 2
        state["max_risk"] = max(state["max_risk"], risk)
        state["risk_accumulation"] = state["risk_accumulation"] * 0.95 + risk
        state["action_counts"][op["action"]] += 1
        if state["risk_accumulation"] > self.risk_accumulation_threshold:
            state["response"] = ResponseAction.THROTTLE.value
        elif state["max_risk"] > 0.8:
            state["response"] = ResponseAction.ALERT.value

    def _check_frequency(self, user_id: str) -> Optional[SafetyEvent]:
        now = time.time()
        ops = self._recent_ops.get(user_id, [])
        recent = [o for o in ops if o["timestamp"] > now - self.window_seconds]
        if len(recent) > self.frequency_threshold:
            event = SafetyEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                event_type=EventType.FREQUENCY_SPIKE,
                user_id=user_id,
                severity=min(1.0, len(recent) / (self.frequency_threshold * 2)),
                description=f"操作频率异常: {len(recent)}次/分钟 (阈值: {self.frequency_threshold})",
                response=ResponseAction.THROTTLE,
            )
            self._record_event(event)
            return event
        return None

    def _check_risk_accumulation(self, user_id: str) -> Optional[SafetyEvent]:
        state = self._user_states.get(user_id, {})
        acc = state.get("risk_accumulation", 0.0)
        if acc > self.risk_accumulation_threshold:
            event = SafetyEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                event_type=EventType.RISK_ACCUMULATION,
                user_id=user_id,
                severity=min(1.0, acc / (self.risk_accumulation_threshold * 2)),
                description=f"风险累积过高: {acc:.2f}",
                response=ResponseAction.ALERT,
            )
            self._record_event(event)
            return event
        return None

    def _check_pattern_change(self, user_id: str) -> Optional[SafetyEvent]:
        state = self._user_states.get(user_id, {})
        counts = state.get("action_counts", {})
        if not counts:
            return None
        total = sum(counts.values())
        if total < 10:
            return None
        most_common = max(counts, key=counts.get)
        ratio = counts[most_common] / total
        if ratio < 0.3 and total > 20:
            event = SafetyEvent(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                event_type=EventType.PATTERN_CHANGE,
                user_id=user_id,
                severity=0.5,
                description=f"操作模式变化: '{most_common}' 占比降至 {ratio:.0%}",
                response=ResponseAction.ALERT,
            )
            self._record_event(event)
            return event
        return None

    def _check_unusual_hour(self, user_id: str) -> Optional[SafetyEvent]:
        ops = self._recent_ops.get(user_id, [])
        if not ops:
            return None
        now_hour = int(time.localtime().tm_hour)
        if now_hour < 6 or now_hour > 23:
            recent = [o for o in ops if o["timestamp"] > time.time() - 300]
            if len(recent) > 3:
                event = SafetyEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:12]}",
                    event_type=EventType.UNUSUAL_HOUR,
                    user_id=user_id,
                    severity=0.4,
                    description=f"异常时段操作: {now_hour}点有{len(recent)}次操作",
                    response=ResponseAction.ALERT,
                )
                self._record_event(event)
                return event
        return None

    def _record_event(self, event: SafetyEvent):
        self._events.append(event)
        conn = self._get_conn()
        conn.execute(
            """INSERT OR IGNORE INTO safety_events
            (event_id, event_type, user_id, severity, description, response, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event.event_id, event.event_type.value, event.user_id,
             event.severity, event.description, event.response.value,
             event.timestamp, event.details),
        )
        conn.commit()
        conn.close()
        if len(self._events) > 500:
            self._events = self._events[-250:]
