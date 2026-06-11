"""
Safety Engine - 自主安全引擎

在现有SafetyLayer基础上，增加：
1. 风险评分引擎：量化操作风险，动态评分
2. 操作拦截策略：基于风险分数的自动拦截
3. 安全策略管理：动态调整安全级别和规则
4. 行为基线：建立用户行为基线，检测偏离

设计原则:
- 风险可量化：每个操作都有风险分数
- 策略可编程：安全规则可动态配置
- 基线自适应：随交互增多越来越准
"""
import time
import json
import sqlite3
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# ─── Enums ───────────────────────────────────────────────────────────────────


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"               # 0-0.3
    MEDIUM = "medium"         # 0.3-0.6
    HIGH = "high"             # 0.6-0.8
    CRITICAL = "critical"     # 0.8-1.0


class SafetyAction(Enum):
    """安全处置动作"""
    ALLOW = "allow"                   # 放行
    LOG = "log"                       # 仅记录
    REQUIRE_CONFIRM = "require_confirm"  # 需要确认
    THROTTLE = "throttle"             # 限速
    BLOCK = "block"                   # 拦截


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class RiskAssessment:
    """风险评估结果

    Attributes:
        risk_score: 风险分数 (0.0-1.0)
        risk_level: 风险等级
        safety_action: 安全处置动作
        reasons: 风险原因列表
        recommendations: 建议列表
    """
    risk_score: float
    risk_level: RiskLevel
    safety_action: SafetyAction
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "safety_action": self.safety_action.value,
            "reasons": self.reasons,
            "recommendations": self.recommendations,
        }


@dataclass
class BehaviorBaseline:
    """用户行为基线

    Attributes:
        user_id: 用户ID
        avg_actions_per_hour: 每小时平均操作数
        typical_hours: 典型活跃时段
        common_actions: 常见操作类型
        risk_tolerance: 风险承受度
        sample_count: 样本数
    """
    user_id: str
    avg_actions_per_hour: float = 0.0
    typical_hours: str = ""
    common_actions: str = ""
    risk_tolerance: float = 0.5
    sample_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "avg_actions_per_hour": self.avg_actions_per_hour,
            "typical_hours": list(self.typical_hours) if isinstance(self.typical_hours, str) else self.typical_hours,
            "common_actions": list(self.common_actions) if isinstance(self.common_actions, str) else self.common_actions,
            "risk_tolerance": self.risk_tolerance,
            "sample_count": self.sample_count,
        }


# ─── Risk Scoring Engine ─────────────────────────────────────────────────────


class RiskScoringEngine:
    """
    风险评分引擎

    基于多维度因素对操作进行风险评分。

    评分维度:
    - 操作类型: delete/execute 风险高于 read
    - 操作频率: 短时间内大量操作风险更高
    - 用户行为偏离: 偏离基线行为风险更高
    - 操作目标: 操作敏感资源风险更高
    - 时间因素: 非典型时段操作风险更高
    """

    # 操作类型基础风险分
    ACTION_RISK_SCORES = {
        "read": 0.05,
        "write": 0.15,
        "execute": 0.3,
        "delete": 0.4,
        "admin": 0.5,
        "network": 0.25,
    }

    # 敏感目标模式
    SENSITIVE_TARGETS = [
        "/etc/", "/root/", "/var/log/",
        "password", "secret", "key", "token",
        "database", "backup", "config",
    ]

    def __init__(self):
        self._custom_rules: List[Dict] = []
        self._action_multipliers: Dict[str, float] = {}

    def add_custom_rule(self, pattern: str, risk_score: float, reason: str):
        """添加自定义风险规则"""
        self._custom_rules.append({
            "pattern": pattern,
            "risk_score": max(0.0, min(risk_score, 1.0)),
            "reason": reason,
        })

    def set_action_multiplier(self, action: str, multiplier: float):
        """设置操作风险倍数"""
        self._action_multipliers[action] = max(0.1, multiplier)

    def assess_risk(
        self,
        action: str,
        target: str = "",
        frequency: int = 1,
        is_typical_hour: bool = True,
        deviation_from_baseline: float = 0.0,
        user_risk_tolerance: float = 0.5,
    ) -> RiskAssessment:
        """
        评估操作风险

        Args:
            action: 操作类型
            target: 操作目标
            frequency: 操作频率(短时间内次数)
            is_typical_hour: 是否在典型时段
            deviation_from_baseline: 偏离基线程度(0-1)
            user_risk_tolerance: 用户风险承受度

        Returns:
            风险评估结果
        """
        score = 0.0
        reasons = []
        recommendations = []

        # 1. 操作类型基础分
        base_score = self.ACTION_RISK_SCORES.get(action, 0.2)
        multiplier = self._action_multipliers.get(action, 1.0)
        score += base_score * multiplier
        if base_score > 0.2:
            reasons.append(f"操作类型 '{action}' 基础风险较高")

        # 2. 频率风险
        if frequency > 10:
            freq_score = min(0.3, (frequency - 10) * 0.02)
            score += freq_score
            reasons.append(f"操作频率过高({frequency}次)")
            recommendations.append("建议降低操作频率")

        # 3. 时间风险
        if not is_typical_hour:
            score += 0.15
            reasons.append("非典型时段操作")

        # 4. 行为偏离风险
        if deviation_from_baseline > 0.5:
            deviation_score = (deviation_from_baseline - 0.5) * 0.4
            score += deviation_score
            reasons.append(f"行为偏离基线({deviation_from_baseline:.0%})")
            recommendations.append("操作模式与历史行为差异较大")

        # 5. 敏感目标检测
        for sensitive in self.SENSITIVE_TARGETS:
            if sensitive in target.lower():
                score += 0.2
                reasons.append(f"操作目标包含敏感模式: {sensitive}")
                break

        # 6. 自定义规则匹配
        import re
        for rule in self._custom_rules:
            if re.search(rule["pattern"], target, re.IGNORECASE):
                score += rule["risk_score"]
                reasons.append(rule["reason"])

        # 7. 用户风险承受度调整
        # 高承受度用户略微降低风险分
        score *= (1.0 - user_risk_tolerance * 0.2)

        # 归一化到 0-1
        score = max(0.0, min(score, 1.0))

        # 确定风险等级和处置动作
        risk_level = self._score_to_level(score)
        safety_action = self._level_to_action(risk_level)

        return RiskAssessment(
            risk_score=round(score, 4),
            risk_level=risk_level,
            safety_action=safety_action,
            reasons=reasons,
            recommendations=recommendations,
        )

    @staticmethod
    def _score_to_level(score: float) -> RiskLevel:
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def _level_to_action(level: RiskLevel) -> SafetyAction:
        mapping = {
            RiskLevel.LOW: SafetyAction.ALLOW,
            RiskLevel.MEDIUM: SafetyAction.LOG,
            RiskLevel.HIGH: SafetyAction.REQUIRE_CONFIRM,
            RiskLevel.CRITICAL: SafetyAction.BLOCK,
        }
        return mapping[level]


# ─── Behavior Baseline Manager ───────────────────────────────────────────────


class BehaviorBaselineManager:
    """
    用户行为基线管理器

    记录用户行为模式，建立基线，检测偏离。
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                action      TEXT NOT NULL,
                timestamp   REAL NOT NULL,
                risk_score  REAL NOT NULL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS baselines (
                user_id             TEXT PRIMARY KEY,
                avg_actions_hour    REAL NOT NULL DEFAULT 0.0,
                typical_hours       TEXT NOT NULL DEFAULT '[]',
                common_actions      TEXT NOT NULL DEFAULT '[]',
                risk_tolerance      REAL NOT NULL DEFAULT 0.5,
                sample_count        INTEGER NOT NULL DEFAULT 0,
                updated_at          REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id);
            CREATE INDEX IF NOT EXISTS idx_activity_time ON user_activity(timestamp);
        """)
        conn.commit()
        conn.close()

    def record_activity(self, user_id: str, action: str, risk_score: float = 0.0):
        """记录用户活动"""
        now = time.time()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO user_activity (user_id, action, timestamp, risk_score) VALUES (?, ?, ?, ?)",
            (user_id, action, now, risk_score),
        )
        conn.commit()
        conn.close()

    def update_baseline(self, user_id: str):
        """
        更新用户行为基线

        基于最近的活动数据重新计算基线。
        """
        conn = self._get_conn()
        now = time.time()
        window = 7 * 24 * 3600  # 7天窗口

        # 统计活跃时段
        hour_rows = conn.execute(
            """SELECT CAST(strftime('%H', datetime(timestamp, 'unixepoch')) AS INTEGER) as hour,
                      COUNT(*) as cnt
               FROM user_activity
               WHERE user_id = ? AND timestamp > ?
               GROUP BY hour
               ORDER BY cnt DESC
               LIMIT 5""",
            (user_id, now - window),
        ).fetchall()

        typical_hours = json.dumps([r["hour"] for r in hour_rows])

        # 统计常见操作
        action_rows = conn.execute(
            """SELECT action, COUNT(*) as cnt
               FROM user_activity
               WHERE user_id = ? AND timestamp > ?
               GROUP BY action
               ORDER BY cnt DESC
               LIMIT 5""",
            (user_id, now - window),
        ).fetchall()

        common_actions = json.dumps([r["action"] for r in action_rows])

        # 计算平均每小时操作数
        total = conn.execute(
            """SELECT COUNT(*) as cnt
               FROM user_activity
               WHERE user_id = ? AND timestamp > ?""",
            (user_id, now - window),
        ).fetchone()["cnt"]

        avg_per_hour = total / (window / 3600) if window > 0 else 0

        # 计算平均风险分数
        avg_risk = conn.execute(
            """SELECT AVG(risk_score) as avg_risk
               FROM user_activity
               WHERE user_id = ? AND timestamp > ?""",
            (user_id, now - window),
        ).fetchone()["avg_risk"] or 0.0

        risk_tolerance = 1.0 - avg_risk  # 风险分数越低，承受度越高

        conn.execute(
            """INSERT OR REPLACE INTO baselines
            (user_id, avg_actions_hour, typical_hours, common_actions,
             risk_tolerance, sample_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, avg_per_hour, typical_hours, common_actions,
             risk_tolerance, total, now),
        )
        conn.commit()
        conn.close()

    def get_baseline(self, user_id: str) -> Optional[BehaviorBaseline]:
        """获取用户行为基线"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM baselines WHERE user_id = ?", (user_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return BehaviorBaseline(
            user_id=row["user_id"],
            avg_actions_per_hour=row["avg_actions_hour"],
            typical_hours=row["typical_hours"],
            common_actions=row["common_actions"],
            risk_tolerance=row["risk_tolerance"],
            sample_count=row["sample_count"],
        )

    def calculate_deviation(self, user_id: str, current_action: str) -> float:
        """
        计算当前操作偏离基线的程度

        Returns:
            偏离程度 (0.0-1.0)
        """
        baseline = self.get_baseline(user_id)
        if baseline is None or baseline.sample_count < 5:
            return 0.0  # 样本不足，不判定偏离

        deviation = 0.0

        # 检查操作类型是否在常见操作中
        common = json.loads(baseline.common_actions) if baseline.common_actions else []
        if current_action not in common:
            deviation += 0.3

        # 检查是否在典型时段
        now_hour = int(time.localtime().tm_hour)
        typical = json.loads(baseline.typical_hours) if baseline.typical_hours else []
        if typical and now_hour not in typical:
            deviation += 0.2

        return min(deviation, 1.0)

    def get_stats(self) -> Dict:
        """获取基线系统统计"""
        conn = self._get_conn()
        user_count = conn.execute("SELECT COUNT(DISTINCT user_id) FROM baselines").fetchone()[0]
        total_activities = conn.execute("SELECT COUNT(*) FROM user_activity").fetchone()[0]
        conn.close()
        return {
            "total_users_with_baseline": user_count,
            "total_activities_recorded": total_activities,
        }

    def close(self):
        pass


# ─── Safety Policy Manager ──────────────────────────────────────────────────


class SafetyPolicyManager:
    """
    安全策略管理器

    管理动态安全策略，允许运行时调整安全级别。
    """

    def __init__(self):
        self._policies: Dict[str, Dict] = {
            "default": {
                "risk_threshold_block": 0.8,
                "risk_threshold_confirm": 0.6,
                "risk_threshold_log": 0.3,
                "max_actions_per_minute": 60,
                "enabled": True,
            },
            "strict": {
                "risk_threshold_block": 0.5,
                "risk_threshold_confirm": 0.3,
                "risk_threshold_log": 0.1,
                "max_actions_per_minute": 30,
                "enabled": True,
            },
            "relaxed": {
                "risk_threshold_block": 0.95,
                "risk_threshold_confirm": 0.8,
                "risk_threshold_log": 0.5,
                "max_actions_per_minute": 120,
                "enabled": True,
            },
        }
        self._active_policy = "default"

    def set_active_policy(self, policy_name: str) -> bool:
        """激活指定策略"""
        if policy_name in self._policies:
            self._active_policy = policy_name
            return True
        return False

    def get_active_policy(self) -> Dict:
        """获取当前激活的策略"""
        return dict(self._policies[self._active_policy])

    def get_all_policies(self) -> Dict[str, Dict]:
        """获取所有策略"""
        return dict(self._policies)

    def add_policy(self, name: str, policy: Dict):
        """添加自定义策略"""
        self._policies[name] = policy

    def determine_action(self, risk_score: float) -> SafetyAction:
        """
        根据风险分数和当前策略决定处置动作

        Args:
            risk_score: 风险分数

        Returns:
            处置动作
        """
        policy = self._policies[self._active_policy]
        if risk_score >= policy["risk_threshold_block"]:
            return SafetyAction.BLOCK
        elif risk_score >= policy["risk_threshold_confirm"]:
            return SafetyAction.REQUIRE_CONFIRM
        elif risk_score >= policy["risk_threshold_log"]:
            return SafetyAction.LOG
        return SafetyAction.ALLOW

    def get_stats(self) -> Dict:
        return {
            "active_policy": self._active_policy,
            "available_policies": list(self._policies.keys()),
        }

    def close(self):
        pass


# ─── Safety Engine (Main) ────────────────────────────────────────────────────


class SafetyEngine:
    """
    自主安全引擎

    整合风险评分、行为基线、安全策略，提供全面的安全保障。

    使用示例:
        >>> engine = SafetyEngine(db_path="safety.db")
        >>> assessment = engine.assess_operation(
        ...     user_id="user1",
        ...     action="delete",
        ...     target="/important/file",
        ... )
        >>> if assessment.safety_action == SafetyAction.BLOCK:
        ...     print(f"Blocked! Risk: {assessment.risk_score}")
    """

    def __init__(self, db_path: str = ":memory:"):
        self.risk_engine = RiskScoringEngine()
        self.baseline_manager = BehaviorBaselineManager(
            db_path=db_path
        )
        self.policy_manager = SafetyPolicyManager()
        self._operation_log: List[Dict] = []

    def assess_operation(
        self,
        user_id: str,
        action: str,
        target: str = "",
        frequency: int = 1,
    ) -> RiskAssessment:
        """
        评估操作风险

        Args:
            user_id: 用户ID
            action: 操作类型
            target: 操作目标
            frequency: 频率

        Returns:
            风险评估结果
        """
        # 获取基线信息
        baseline = self.baseline_manager.get_baseline(user_id)
        deviation = self.baseline_manager.calculate_deviation(user_id, action)

        is_typical = True
        risk_tolerance = 0.5
        if baseline:
            typical_hours = json.loads(baseline.typical_hours) if baseline.typical_hours else []
            now_hour = int(time.localtime().tm_hour)
            is_typical = now_hour in typical_hours if typical_hours else True
            risk_tolerance = baseline.risk_tolerance

        # 风险评估
        assessment = self.risk_engine.assess_risk(
            action=action,
            target=target,
            frequency=frequency,
            is_typical_hour=is_typical,
            deviation_from_baseline=deviation,
            user_risk_tolerance=risk_tolerance,
        )

        # 应用策略覆盖
        policy_action = self.policy_manager.determine_action(assessment.risk_score)
        # 取更严格的动作
        assessment.safety_action = self._stricter_action(
            assessment.safety_action, policy_action
        )

        # 记录操作
        self._log_operation(user_id, action, target, assessment)

        # 记录活动到基线
        self.baseline_manager.record_activity(user_id, action, assessment.risk_score)

        return assessment

    def update_user_baseline(self, user_id: str):
        """更新用户行为基线"""
        self.baseline_manager.update_baseline(user_id)

    def set_policy(self, policy_name: str) -> bool:
        """切换安全策略"""
        return self.policy_manager.set_active_policy(policy_name)

    def get_safety_status(self) -> Dict:
        """获取安全系统状态"""
        return {
            "risk_engine": {"rules_count": len(self.risk_engine._custom_rules)},
            "baseline": self.baseline_manager.get_stats(),
            "policy": self.policy_manager.get_stats(),
            "operations_logged": len(self._operation_log),
        }

    def get_recent_assessments(self, k: int = 10) -> List[Dict]:
        """获取最近的风险评估"""
        return self._operation_log[-k:]

    def _log_operation(self, user_id: str, action: str, target: str, assessment: RiskAssessment):
        """记录操作评估"""
        self._operation_log.append({
            "timestamp": time.time(),
            "user_id": user_id,
            "action": action,
            "target": target,
            "assessment": assessment.to_dict(),
        })
        # 保持日志不超过1000条
        if len(self._operation_log) > 1000:
            self._operation_log = self._operation_log[-500:]

    @staticmethod
    def _stricter_action(a: SafetyAction, b: SafetyAction) -> SafetyAction:
        """取更严格的安全处置动作"""
        strictness = {
            SafetyAction.ALLOW: 0,
            SafetyAction.LOG: 1,
            SafetyAction.THROTTLE: 2,
            SafetyAction.REQUIRE_CONFIRM: 3,
            SafetyAction.BLOCK: 4,
        }
        return a if strictness[a] >= strictness[b] else b

    def close(self):
        self.baseline_manager.close()
        self.policy_manager.close()
