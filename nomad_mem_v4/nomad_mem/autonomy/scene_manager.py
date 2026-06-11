"""
Scene Manager - 场景管理器

Jarvis 自动检测和切换交互场景（上下文/模式）的核心模块。
场景代表用户当前的不同状态，如"工作中"、"休息中"、"紧急模式"等。

核心特性:
- 场景定义: 预定义 + 自定义场景类型
- 自动检测: 基于多信号上下文（时间、情绪、活动、位置）推断当前场景
- 规则引擎: 每个场景关联触发条件和动作列表
- 场景切换: 追踪场景转换历史，支持分析
- SQLite 持久化: 轻量级本地存储

设计原则:
- 场景是用户与 Jarvis 交互模式的高级抽象
- 自动检测基于多种上下文信号的综合判断
- 规则定义 Jarvis 在每个场景中的差异化行为
- 场景切换可回溯、可分析
"""
import sqlite3
import time
import json
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import Counter


# ─── Enums ───────────────────────────────────────────────────────────────────


class SceneType(Enum):
    """场景类型"""
    WORK = "work"                   # 工作模式
    REST = "rest"                   # 休息模式
    EMERGENCY = "emergency"         # 紧急模式
    SOCIAL = "social"               # 社交模式
    LEARNING = "learning"           # 学习模式
    CREATION = "creation"           # 创作模式
    HEALTH = "health"               # 健康模式
    COMMUTE = "commute"             # 通勤模式
    SLEEP = "sleep"                 # 睡眠模式
    CUSTOM = "custom"               # 自定义模式


class SceneStatus(Enum):
    """场景状态"""
    INACTIVE = "inactive"           # 未激活
    ACTIVE = "active"               # 激活中
    TRANSITIONING = "transitioning"  # 切换中


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class SceneRule:
    """场景自动化规则

    Attributes:
        rule_id: 规则唯一标识
        scene_type: 关联的场景类型
        trigger_conditions: 触发条件字典，如 {"time_of_day": "morning", "activity_state": "active"}
        actions: 触发动作列表，如 ["set_greeting_style:professional", "reduce_interruptions"]
        priority: 优先级 (1-10)，数值越高优先级越高
        enabled: 是否启用
    """
    rule_id: str
    scene_type: SceneType
    trigger_conditions: Dict[str, Any]
    actions: List[str]
    priority: int = 5
    enabled: bool = True

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["scene_type"] = self.scene_type.value
        d["trigger_conditions"] = json.dumps(self.trigger_conditions, ensure_ascii=False)
        d["actions"] = json.dumps(self.actions, ensure_ascii=False)
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "SceneRule":
        data = dict(data)
        if isinstance(data.get("scene_type"), str):
            data["scene_type"] = SceneType(data["scene_type"])
        if isinstance(data.get("trigger_conditions"), str):
            data["trigger_conditions"] = json.loads(data["trigger_conditions"])
        if isinstance(data.get("actions"), str):
            data["actions"] = json.loads(data["actions"])
        # Filter to only dataclass fields
        allowed = {"rule_id", "scene_type", "trigger_conditions", "actions", "priority", "enabled"}
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


@dataclass
class SceneState:
    """场景状态

    Attributes:
        scene_id: 场景实例唯一标识
        scene_type: 场景类型
        status: 场景状态
        activated_at: 激活时间戳
        activated_by: 触发方式 (auto/user)
        duration_seconds: 持续时长（秒）
        rules_applied: 已应用的规则ID列表
    """
    scene_id: str
    scene_type: SceneType
    status: SceneStatus
    activated_at: float = field(default_factory=time.time)
    activated_by: str = "auto"  # auto | user
    duration_seconds: float = 0.0
    rules_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["scene_type"] = self.scene_type.value
        d["status"] = self.status.value
        d["rules_applied"] = json.dumps(self.rules_applied, ensure_ascii=False)
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "SceneState":
        data = dict(data)
        if isinstance(data.get("scene_type"), str):
            data["scene_type"] = SceneType(data["scene_type"])
        if isinstance(data.get("status"), str):
            data["status"] = SceneStatus(data["status"])
        if isinstance(data.get("rules_applied"), str):
            data["rules_applied"] = json.loads(data["rules_applied"])
        return cls(**data)


@dataclass
class SceneTransition:
    """场景转换记录

    Attributes:
        from_scene: 源场景类型（首次激活为 None）
        to_scene: 目标场景类型
        timestamp: 转换时间戳
        reason: 转换原因
        trigger: 触发方式 (auto/user)
    """
    from_scene: Optional[SceneType]
    to_scene: SceneType
    timestamp: float = field(default_factory=time.time)
    reason: str = ""
    trigger: str = "auto"

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["from_scene"] = self.from_scene.value if self.from_scene else None
        d["to_scene"] = self.to_scene.value
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "SceneTransition":
        data = dict(data)
        if isinstance(data.get("from_scene"), str):
            data["from_scene"] = SceneType(data["from_scene"])
        elif data.get("from_scene") is None:
            data["from_scene"] = None
        if isinstance(data.get("to_scene"), str):
            data["to_scene"] = SceneType(data["to_scene"])
        return cls(**data)


# ─── SceneManager ────────────────────────────────────────────────────────────


class SceneManager:
    """
    场景管理器

    管理场景的定义、规则、自动检测、激活和切换。
    Jarvis 根据当前场景自动调整交互策略。

    Args:
        db_path: SQLite 数据库文件路径，默认使用内存数据库

    使用示例:
        >>> mgr = SceneManager(":memory:")
        >>> scene_id = mgr.define_scene(SceneType.CUSTOM, "阅读模式", "深度阅读时的专注场景", icon="📖")
        >>> mgr.create_rule(SceneType.WORK, {"time_of_day": "morning"}, ["set_greeting_style:professional"])
        >>> scene = mgr.detect_current_scene({"time_of_day": "morning", "activity_state": "active"})
        >>> mgr.activate_scene(scene)
        >>> mgr.get_stats()
    """

    # 场景检测权重配置
    DETECTION_WEIGHTS = {
        "time_of_day": 0.15,
        "day_type": 0.10,
        "activity_state": 0.25,
        "emotion": 0.15,
        "location": 0.15,
        "recent_actions": 0.20,
    }

    # 场景-条件映射规则（内置默认检测逻辑）
    SCENE_CONDITION_MAP = {
        SceneType.WORK: {
            "time_of_day": ["morning", "late_afternoon"],
            "activity_state": ["active", "focused", "busy"],
            "day_type": ["weekday"],
        },
        SceneType.REST: {
            "time_of_day": ["afternoon", "evening"],
            "activity_state": ["idle", "relaxed"],
            "emotion": ["neutral", "relaxed"],
        },
        SceneType.EMERGENCY: {
            "emotion": ["stressed", "anxious"],
            "recent_actions": ["error", "urgent"],
        },
        SceneType.SOCIAL: {
            "time_of_day": ["evening"],
            "activity_state": ["active"],
            "emotion": ["positive"],
            "recent_actions": ["chat", "social"],
        },
        SceneType.LEARNING: {
            "activity_state": ["focused"],
            "recent_actions": ["query", "learn", "research"],
        },
        SceneType.CREATION: {
            "activity_state": ["focused", "active"],
            "recent_actions": ["create", "write", "design"],
        },
        SceneType.HEALTH: {
            "recent_actions": ["exercise", "health_check"],
            "location": ["gym", "outdoor"],
        },
        SceneType.COMMUTE: {
            "time_of_day": ["early_morning", "late_afternoon"],
            "location": ["transit", "moving"],
            "activity_state": ["idle"],
        },
        SceneType.SLEEP: {
            "time_of_day": ["night", "late_night"],
            "activity_state": ["idle"],
        },
    }

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()
        self._init_default_scenes()

    # ── Database ──────────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scene_definitions (
                scene_id     TEXT PRIMARY KEY,
                scene_type   TEXT NOT NULL,
                name         TEXT NOT NULL,
                description  TEXT NOT NULL DEFAULT '',
                icon         TEXT NOT NULL DEFAULT '',
                is_builtin   INTEGER NOT NULL DEFAULT 0,
                created_at   REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scene_rules (
                rule_id            TEXT PRIMARY KEY,
                scene_type         TEXT NOT NULL,
                trigger_conditions TEXT NOT NULL DEFAULT '{}',
                actions            TEXT NOT NULL DEFAULT '[]',
                priority           INTEGER NOT NULL DEFAULT 5,
                enabled            INTEGER NOT NULL DEFAULT 1,
                created_at         REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scene_states (
                scene_id        TEXT PRIMARY KEY,
                scene_type      TEXT NOT NULL,
                status          TEXT NOT NULL,
                activated_at    REAL NOT NULL,
                activated_by    TEXT NOT NULL DEFAULT 'auto',
                duration_seconds REAL NOT NULL DEFAULT 0,
                rules_applied   TEXT NOT NULL DEFAULT '[]',
                FOREIGN KEY (scene_type) REFERENCES scene_definitions(scene_type)
            );

            CREATE TABLE IF NOT EXISTS scene_transitions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                from_scene  TEXT,
                to_scene    TEXT NOT NULL,
                timestamp   REAL NOT NULL,
                reason      TEXT NOT NULL DEFAULT '',
                trigger     TEXT NOT NULL DEFAULT 'auto'
            );

            CREATE INDEX IF NOT EXISTS idx_rules_scene ON scene_rules(scene_type);
            CREATE INDEX IF NOT EXISTS idx_rules_enabled ON scene_rules(enabled);
            CREATE INDEX IF NOT EXISTS idx_states_status ON scene_states(status);
            CREATE INDEX IF NOT EXISTS idx_transitions_time ON scene_transitions(timestamp);
            CREATE INDEX IF NOT EXISTS idx_transitions_to ON scene_transitions(to_scene);
        """)
        conn.commit()

    def _init_default_scenes(self):
        """初始化预定义场景"""
        conn = self._get_conn()
        defaults = [
            (SceneType.WORK, "工作模式", "工作时间的高效协作场景", "💼"),
            (SceneType.REST, "休息模式", "放松和恢复精力的场景", "☕"),
            (SceneType.EMERGENCY, "紧急模式", "处理紧急事务的高优先级场景", "🚨"),
            (SceneType.SOCIAL, "社交模式", "社交互动和闲聊场景", "👥"),
            (SceneType.LEARNING, "学习模式", "知识获取和技能学习场景", "📚"),
            (SceneType.CREATION, "创作模式", "创意输出和内容创作场景", "🎨"),
            (SceneType.HEALTH, "健康模式", "健康管理和运动场景", "💪"),
            (SceneType.COMMUTE, "通勤模式", "出行途中的轻量交互场景", "🚗"),
            (SceneType.SLEEP, "睡眠模式", "睡眠准备和低打扰场景", "🌙"),
        ]
        now = time.time()
        for st, name, desc, icon in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO scene_definitions (scene_id, scene_type, name, description, icon, is_builtin, created_at) "
                "VALUES (?, ?, ?, ?, ?, 1, ?)",
                (f"builtin_{st.value}", st.value, name, desc, icon, now),
            )
        conn.commit()

    # ── Scene Definition ──────────────────────────────────────────────────

    def define_scene(self, scene_type: SceneType, name: str, description: str = "", icon: str = "") -> str:
        """
        定义一个新的场景类型

        Args:
            scene_type: 场景类型（使用 CUSTOM 表示自定义）
            name: 场景名称
            description: 场景描述
            icon: 场景图标（可选）

        Returns:
            scene_id: 新场景的ID
        """
        scene_id = f"scene_{uuid.uuid4().hex[:12]}"
        now = time.time()

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO scene_definitions (scene_id, scene_type, name, description, icon, is_builtin, created_at) "
            "VALUES (?, ?, ?, ?, ?, 0, ?)",
            (scene_id, scene_type.value, name, description, icon, now),
        )
        conn.commit()
        return scene_id

    # ── Rule Management ───────────────────────────────────────────────────

    def create_rule(self, scene_type: SceneType, trigger_conditions: Dict[str, Any],
                    actions: List[str], priority: int = 5) -> str:
        """
        为场景创建自动化规则

        Args:
            scene_type: 场景类型
            trigger_conditions: 触发条件字典
                支持的键: time_of_day, day_type, activity_state, emotion, location, recent_actions
                值: 字符串或字符串列表
            actions: 动作列表，格式如 ["set_greeting_style:professional", "reduce_interruptions"]
            priority: 优先级 (1-10)，默认5

        Returns:
            rule_id: 新规则的ID

        Raises:
            ValueError: priority 不在 1-10 范围内
        """
        if not (1 <= priority <= 10):
            raise ValueError(f"Priority must be between 1 and 10, got {priority}")

        rule_id = f"rule_{uuid.uuid4().hex[:12]}"
        now = time.time()

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO scene_rules (rule_id, scene_type, trigger_conditions, actions, priority, enabled, created_at) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (rule_id, scene_type.value,
             json.dumps(trigger_conditions, ensure_ascii=False),
             json.dumps(actions, ensure_ascii=False),
             priority, now),
        )
        conn.commit()
        return rule_id

    def delete_rule(self, rule_id: str) -> bool:
        """
        删除规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功删除
        """
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM scene_rules WHERE rule_id = ?", (rule_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_scene_rules(self, scene_type: Optional[SceneType] = None) -> List[SceneRule]:
        """
        获取场景规则

        Args:
            scene_type: 可选，按场景类型过滤

        Returns:
            规则列表，按优先级降序排列
        """
        conn = self._get_conn()
        if scene_type:
            rows = conn.execute(
                "SELECT * FROM scene_rules WHERE scene_type = ? ORDER BY priority DESC, created_at DESC",
                (scene_type.value,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scene_rules ORDER BY priority DESC, created_at DESC"
            ).fetchall()

        return [SceneRule.from_dict(dict(r)) for r in rows]

    # ── Scene Detection ───────────────────────────────────────────────────

    def detect_current_scene(self, context: Dict[str, Any]) -> SceneType:
        """
        根据上下文自动检测当前场景

        检测策略:
        1. 遍历所有预定义场景类型
        2. 对每个场景计算与上下文的匹配得分
        3. 匹配得分 = Σ(权重 × 条件匹配度)
        4. 返回得分最高的场景

        Args:
            context: 上下文字典，支持的键:
                - time_of_day: str ("morning"/"afternoon"/"evening"/"night"/"early_morning"/"late_afternoon"/"late_night")
                - day_type: str ("weekday"/"weekend"/"holiday")
                - activity_state: str ("idle"/"active"/"busy"/"focused"/"distracted")
                - emotion: str ("positive"/"neutral"/"negative"/"stressed"/"relaxed")
                - location: str ("home"/"office"/"gym"/"transit"/"outdoor"/"moving")
                - recent_actions: List[str] (如 ["query", "chat", "create"])

        Returns:
            检测到的场景类型
        """
        if not context:
            return SceneType.REST  # 默认回退

        weights = self.DETECTION_WEIGHTS
        scores: Dict[SceneType, float] = {}

        for stype, conditions in self.SCENE_CONDITION_MAP.items():
            score = 0.0
            total_weight = 0.0

            for cond_key, cond_values in conditions.items():
                w = weights.get(cond_key, 0.1)
                total_weight += w

                ctx_val = context.get(cond_key)
                if ctx_val is None:
                    continue

                # 支持字符串和列表值
                if isinstance(ctx_val, list):
                    # 取最近的一个动作/多个动作
                    match = any(v in ctx_val for v in (cond_values if isinstance(cond_values, list) else [cond_values]))
                else:
                    match = ctx_val in (cond_values if isinstance(cond_values, list) else [cond_values])

                if match:
                    score += w

            # 归一化
            if total_weight > 0:
                scores[stype] = score / total_weight
            else:
                scores[stype] = 0.0

        if not scores:
            return SceneType.REST

        # 返回得分最高的场景
        best = max(scores, key=scores.get)
        # 如果所有得分都为0，回退到 REST
        if scores[best] == 0.0:
            return SceneType.REST

        return best

    # ── Scene Activation ──────────────────────────────────────────────────

    def activate_scene(self, scene_type: SceneType, triggered_by: str = "auto") -> SceneState:
        """
        激活一个场景

        如果已有活跃场景，先记录转换再停用旧场景。

        Args:
            scene_type: 要激活的场景类型
            triggered_by: 触发方式 ("auto" 或 "user")

        Returns:
            SceneState: 新激活的场景状态
        """
        conn = self._get_conn()
        now = time.time()

        # 获取当前活跃场景（转为字典避免 Row 失效）
        current_row = self._load_active_scene()
        current = dict(current_row) if current_row else None
        from_scene = None

        if current:
            from_scene = SceneType(current["scene_type"])
            # 记录旧场景持续时间
            duration = now - current["activated_at"]
            conn.execute(
                "UPDATE scene_states SET status = 'inactive', duration_seconds = ? WHERE scene_id = ?",
                (duration, current["scene_id"]),
            )
        else:
            from_scene = None

        # 记录转换
        conn.execute(
            "INSERT INTO scene_transitions (from_scene, to_scene, timestamp, reason, trigger) "
            "VALUES (?, ?, ?, ?, ?)",
            (from_scene.value if from_scene else None, scene_type.value, now,
             f"Activated by {triggered_by}", triggered_by),
        )

        # 获取并应用规则
        rules = self.get_scene_rules(scene_type)
        rules_applied = [r.rule_id for r in rules if r.enabled]

        # 创建新场景状态
        scene_id = f"state_{uuid.uuid4().hex[:12]}"
        conn.execute(
            "INSERT INTO scene_states (scene_id, scene_type, status, activated_at, activated_by, duration_seconds, rules_applied) "
            "VALUES (?, ?, 'active', ?, ?, 0, ?)",
            (scene_id, scene_type.value, now, triggered_by,
             json.dumps(rules_applied, ensure_ascii=False)),
        )
        conn.commit()

        return SceneState(
            scene_id=scene_id,
            scene_type=scene_type,
            status=SceneStatus.ACTIVE,
            activated_at=now,
            activated_by=triggered_by,
            duration_seconds=0.0,
            rules_applied=rules_applied,
        )

    def deactivate_scene(self) -> bool:
        """
        停用当前活跃场景

        Returns:
            是否成功停用
        """
        conn = self._get_conn()
        now = time.time()

        current = self._load_active_scene()
        if not current:
            return False

        current = dict(current)
        duration = now - current["activated_at"]
        conn.execute(
            "UPDATE scene_states SET status = 'inactive', duration_seconds = ? WHERE scene_id = ?",
            (duration, current["scene_id"]),
        )
        conn.commit()
        return True

    def get_current_scene(self) -> Optional[SceneState]:
        """
        获取当前活跃场景

        Returns:
            当前活跃的场景状态，如果没有则返回 None
        """
        row = self._load_active_scene()
        if row is None:
            return None

        return SceneState(
            scene_id=row["scene_id"],
            scene_type=SceneType(row["scene_type"]),
            status=SceneStatus(row["status"]),
            activated_at=row["activated_at"],
            activated_by=row["activated_by"],
            duration_seconds=row["duration_seconds"],
            rules_applied=json.loads(row["rules_applied"]) if row["rules_applied"] else [],
        )

    # ── History ───────────────────────────────────────────────────────────

    def get_scene_history(self, limit: int = 20) -> List[SceneState]:
        """
        获取场景历史

        Args:
            limit: 返回数量限制

        Returns:
            场景状态列表，按激活时间降序
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM scene_states ORDER BY activated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

        return [
            SceneState(
                scene_id=r["scene_id"],
                scene_type=SceneType(r["scene_type"]),
                status=SceneStatus(r["status"]),
                activated_at=r["activated_at"],
                activated_by=r["activated_by"],
                duration_seconds=r["duration_seconds"],
                rules_applied=json.loads(r["rules_applied"]) if r["rules_applied"] else [],
            )
            for r in rows
        ]

    def get_transition_history(self, limit: int = 20) -> List[SceneTransition]:
        """
        获取场景转换历史

        Args:
            limit: 返回数量限制

        Returns:
            转换记录列表，按时间降序
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM scene_transitions ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()

        return [
            SceneTransition(
                from_scene=SceneType(r["from_scene"]) if r["from_scene"] else None,
                to_scene=SceneType(r["to_scene"]),
                timestamp=r["timestamp"],
                reason=r["reason"],
                trigger=r["trigger"],
            )
            for r in rows
        ]

    # ── Actions & Rules Application ───────────────────────────────────────

    def get_scene_actions(self, scene_type: SceneType) -> List[str]:
        """
        获取场景的所有动作（合并所有启用规则的动作）

        Args:
            scene_type: 场景类型

        Returns:
            动作列表，按规则优先级排序
        """
        rules = self.get_scene_rules(scene_type)
        actions = []
        for rule in rules:
            if rule.enabled:
                actions.extend(rule.actions)
        return actions

    def apply_scene_rules(self, scene_type: SceneType) -> List[str]:
        """
        应用场景规则，返回动作列表

        Args:
            scene_type: 场景类型

        Returns:
            已应用的规则动作列表
        """
        return self.get_scene_actions(scene_type)

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """
        获取场景统计信息

        Returns:
            统计字典:
            - total_scenes: 定义的场景总数
            - total_transitions: 总转换次数
            - most_common_scene: 最常见的场景类型
            - avg_duration: 平均场景持续时间（秒）
            - active_scene: 当前活跃场景类型（无则为 None）
            - auto_activations: 自动激活次数
            - user_activations: 手动激活次数
        """
        conn = self._get_conn()

        # 场景总数
        total = conn.execute("SELECT COUNT(*) as cnt FROM scene_definitions").fetchone()["cnt"] or 0

        # 转换总数
        total_trans = conn.execute("SELECT COUNT(*) as cnt FROM scene_transitions").fetchone()["cnt"] or 0

        # 最常见场景
        row = conn.execute(
            "SELECT to_scene, COUNT(*) as cnt FROM scene_transitions GROUP BY to_scene ORDER BY cnt DESC LIMIT 1"
        ).fetchone()
        most_common = SceneType(row["to_scene"]).value if row else None

        # 平均持续时间
        row = conn.execute(
            "SELECT AVG(duration_seconds) as avg_dur FROM scene_states WHERE status = 'inactive'"
        ).fetchone()
        avg_dur = round(row["avg_dur"] or 0.0, 2)

        # 当前活跃场景
        active = self._load_active_scene()
        active_scene = SceneType(active["scene_type"]).value if active else None

        # 激活方式统计
        auto_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM scene_transitions WHERE trigger = 'auto'"
        ).fetchone()["cnt"] or 0
        user_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM scene_transitions WHERE trigger = 'user'"
        ).fetchone()["cnt"] or 0

        return {
            "total_scenes": total,
            "total_transitions": total_trans,
            "most_common_scene": most_common,
            "avg_duration": avg_dur,
            "active_scene": active_scene,
            "auto_activations": auto_count,
            "user_activations": user_count,
        }

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _load_active_scene(self) -> Optional[sqlite3.Row]:
        conn = self._get_conn()
        return conn.execute(
            "SELECT * FROM scene_states WHERE status = 'active' ORDER BY activated_at DESC LIMIT 1"
        ).fetchone()
