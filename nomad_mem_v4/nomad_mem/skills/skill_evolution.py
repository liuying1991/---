"""
Skill Evolution - 技能进化系统

管理技能版本、优化技能性能、追踪技能健康度。
在SkillDiscoverer的基础上，增加：
1. 技能版本管理: 每次优化都保留版本记录
2. 技能性能追踪: 成功率、响应时间、用户满意度
3. 自动优化建议: 基于数据生成优化建议
4. 技能生命周期: 创建→验证→发布→优化→废弃
"""
import time
import json
import uuid
import sqlite3
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# ─── Enums ───────────────────────────────────────────────────────────────────


class SkillStatus(Enum):
    """技能状态"""
    DRAFT = "draft"                   # 草稿
    VALIDATING = "validating"         # 验证中
    ACTIVE = "active"                 # 已发布
    DEPRECATED = "deprecated"         # 已废弃
    ARCHIVED = "archived"             # 已归档


class EvolutionType(Enum):
    """进化类型"""
    PERFORMANCE = "performance"       # 性能优化
    BUG_FIX = "bug_fix"               # 缺陷修复
    FEATURE_ADD = "feature_add"       # 功能增加
    DEPRECATE = "deprecate"           # 废弃


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class SkillVersion:
    """技能版本

    Attributes:
        version_id: 版本ID
        skill_name: 技能名称
        version: 版本号
        status: 技能状态
        description: 版本描述
        evolution_type: 进化类型
        success_rate: 成功率
        avg_response_time: 平均响应时间
        usage_count: 使用次数
        created_at: 创建时间
        metadata: 元数据
    """
    version_id: str
    skill_name: str
    version: str
    status: SkillStatus
    description: str
    evolution_type: EvolutionType = EvolutionType.PERFORMANCE
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    usage_count: int = 0
    created_at: float = field(default_factory=time.time)
    metadata: str = ""

    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "skill_name": self.skill_name,
            "version": self.version,
            "status": self.status.value,
            "description": self.description,
            "evolution_type": self.evolution_type.value,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SkillVersion":
        d = dict(data)
        if isinstance(d.get("status"), str):
            d["status"] = SkillStatus(d["status"])
        if isinstance(d.get("evolution_type"), str):
            d["evolution_type"] = EvolutionType(d["evolution_type"])
        allowed = {
            "version_id", "skill_name", "version", "status", "description",
            "evolution_type", "success_rate", "avg_response_time",
            "usage_count", "created_at", "metadata",
        }
        d = {k: v for k, v in d.items() if k in allowed}
        return cls(**d)


@dataclass
class OptimizationSuggestion:
    """优化建议

    Attributes:
        suggestion_id: 建议ID
        skill_name: 技能名称
        suggestion: 建议内容
        priority: 优先级 (0.0-1.0)
        reason: 建议原因
        expected_improvement: 预期改进
    """
    suggestion_id: str
    skill_name: str
    suggestion: str
    priority: float
    reason: str
    expected_improvement: str = ""

    def to_dict(self) -> Dict:
        return {
            "suggestion_id": self.suggestion_id,
            "skill_name": self.skill_name,
            "suggestion": self.suggestion,
            "priority": self.priority,
            "reason": self.reason,
            "expected_improvement": self.expected_improvement,
        }


# ─── Skill Evolution Manager ────────────────────────────────────────────────


class SkillEvolutionManager:
    """
    技能进化管理器

    管理技能版本、追踪性能、生成优化建议。

    使用示例:
        >>> manager = SkillEvolutionManager(db_path="skill_evolution.db")
        >>> # 注册新技能
        >>> manager.register_skill("read_file", "读取文件内容")
        >>> # 记录使用结果
        >>> manager.record_skill_result("read_file", 0.5, True, 0.9)
        >>> # 获取优化建议
        >>> suggestions = manager.get_optimization_suggestions()
        >>> # 创建新版本
        >>> manager.create_version("read_file", "2.0", "performance优化")
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
            CREATE TABLE IF NOT EXISTS skills (
                skill_name    TEXT PRIMARY KEY,
                description   TEXT NOT NULL DEFAULT '',
                category      TEXT NOT NULL DEFAULT 'general',
                status        TEXT NOT NULL DEFAULT 'active',
                created_at    REAL NOT NULL,
                updated_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS skill_versions (
                version_id      TEXT PRIMARY KEY,
                skill_name      TEXT NOT NULL,
                version         TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'active',
                description     TEXT NOT NULL DEFAULT '',
                evolution_type  TEXT NOT NULL DEFAULT 'performance',
                success_rate    REAL NOT NULL DEFAULT 0.0,
                avg_response_time REAL NOT NULL DEFAULT 0.0,
                usage_count     INTEGER NOT NULL DEFAULT 0,
                created_at      REAL NOT NULL,
                metadata        TEXT DEFAULT '',
                FOREIGN KEY (skill_name) REFERENCES skills(skill_name)
            );

            CREATE TABLE IF NOT EXISTS skill_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name      TEXT NOT NULL,
                response_time   REAL NOT NULL,
                success         INTEGER NOT NULL,
                user_rating     REAL NOT NULL DEFAULT 0.5,
                timestamp       REAL NOT NULL,
                context         TEXT DEFAULT '',
                FOREIGN KEY (skill_name) REFERENCES skills(skill_name)
            );

            CREATE INDEX IF NOT EXISTS idx_results_skill ON skill_results(skill_name);
            CREATE INDEX IF NOT EXISTS idx_results_time ON skill_results(timestamp);
            CREATE INDEX IF NOT EXISTS idx_versions_skill ON skill_versions(skill_name);
        """)
        conn.commit()
        conn.close()

    # ── Skill Registration ───────────────────────────────────────────────

    def register_skill(self, skill_name: str, description: str = "",
                       category: str = "general") -> bool:
        """
        注册新技能

        Args:
            skill_name: 技能名称
            description: 技能描述
            category: 技能分类

        Returns:
            是否注册成功
        """
        now = time.time()
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO skills (skill_name, description, category, status, created_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, ?)""",
                (skill_name, description, category, now, now),
            )
            # 创建初始版本
            self._create_version_record(
                conn, skill_name, "1.0", SkillStatus.ACTIVE,
                "初始版本", EvolutionType.FEATURE_ADD
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """获取技能基本信息"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM skills WHERE skill_name = ?", (skill_name,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return dict(row)

    def get_all_skills(self, status: Optional[str] = None) -> List[Dict]:
        """获取所有技能"""
        conn = self._get_conn()
        if status:
            rows = conn.execute(
                "SELECT * FROM skills WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM skills ORDER BY updated_at DESC"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Version Management ────────────────────────────────────────────────

    def create_version(self, skill_name: str, version: str, description: str,
                       evolution_type: str = "performance") -> Optional[str]:
        """
        创建新版本

        Args:
            skill_name: 技能名称
            version: 版本号
            description: 版本描述
            evolution_type: 进化类型

        Returns:
            版本ID，失败则返回None
        """
        try:
            etype = EvolutionType(evolution_type)
        except ValueError:
            etype = EvolutionType.PERFORMANCE

        conn = self._get_conn()
        version_id = self._create_version_record(
            conn, skill_name, version, SkillStatus.ACTIVE,
            description, etype
        )
        conn.commit()
        conn.close()
        return version_id

    def _create_version_record(self, conn, skill_name, version, status, description, etype):
        """内部方法：创建版本记录"""
        version_id = f"ver_{uuid.uuid4().hex[:12]}"
        now = time.time()
        conn.execute(
            """INSERT INTO skill_versions
            (version_id, skill_name, version, status, description,
             evolution_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (version_id, skill_name, version, status.value,
             description, etype.value, now),
        )
        conn.execute(
            "UPDATE skills SET updated_at = ? WHERE skill_name = ?",
            (now, skill_name),
        )
        return version_id

    def get_versions(self, skill_name: str) -> List[SkillVersion]:
        """获取技能的所有版本"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM skill_versions WHERE skill_name = ?
            ORDER BY created_at DESC""",
            (skill_name,),
        ).fetchall()
        conn.close()
        return [SkillVersion.from_dict(dict(r)) for r in rows]

    def get_latest_version(self, skill_name: str) -> Optional[SkillVersion]:
        """获取最新版本"""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT * FROM skill_versions WHERE skill_name = ?
            ORDER BY created_at DESC LIMIT 1""",
            (skill_name,),
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return SkillVersion.from_dict(dict(row))

    def deprecate_skill(self, skill_name: str) -> bool:
        """废弃技能"""
        conn = self._get_conn()
        conn.execute(
            "UPDATE skills SET status = 'deprecated', updated_at = ? WHERE skill_name = ?",
            (time.time(), skill_name),
        )
        conn.execute(
            "UPDATE skill_versions SET status = 'deprecated' WHERE skill_name = ?",
            (skill_name,),
        )
        conn.commit()
        conn.close()
        return True

    # ── Performance Tracking ──────────────────────────────────────────────

    def record_skill_result(self, skill_name: str, response_time: float,
                            success: bool, user_rating: float = 0.5,
                            context: str = ""):
        """
        记录技能使用结果

        Args:
            skill_name: 技能名称
            response_time: 响应时间(秒)
            success: 是否成功
            user_rating: 用户评分 (0.0-1.0)
            context: 上下文
        """
        now = time.time()
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO skill_results
            (skill_name, response_time, success, user_rating, timestamp, context)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (skill_name, response_time, int(success), user_rating, now, context),
        )
        conn.commit()
        conn.close()

    def get_skill_performance(self, skill_name: str, window_days: int = 7) -> Dict:
        """
        获取技能性能指标

        Args:
            skill_name: 技能名称
            window_days: 统计窗口(天)

        Returns:
            性能指标字典
        """
        conn = self._get_conn()
        cutoff = time.time() - window_days * 86400

        row = conn.execute(
            """SELECT
               COUNT(*) as total,
               SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes,
               AVG(response_time) as avg_time,
               AVG(user_rating) as avg_rating,
               MIN(response_time) as min_time,
               MAX(response_time) as max_time
               FROM skill_results
               WHERE skill_name = ? AND timestamp > ?""",
            (skill_name, cutoff),
        ).fetchone()

        conn.close()

        if row is None or row["total"] == 0:
            return {
                "skill_name": skill_name,
                "total_uses": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "avg_user_rating": 0.0,
            }

        total = row["total"]
        return {
            "skill_name": skill_name,
            "total_uses": total,
            "success_count": row["successes"],
            "success_rate": round(row["successes"] / total, 4),
            "avg_response_time": round(row["avg_time"], 4),
            "min_response_time": round(row["min_time"], 4),
            "max_response_time": round(row["max_time"], 4),
            "avg_user_rating": round(row["avg_rating"], 4),
        }

    # ── Optimization Suggestions ──────────────────────────────────────────

    def get_optimization_suggestions(self, skill_name: str = "") -> List[OptimizationSuggestion]:
        """
        生成优化建议

        Args:
            skill_name: 可选，指定技能

        Returns:
            优化建议列表
        """
        suggestions = []

        # 获取需要分析的技能
        conn = self._get_conn()
        if skill_name:
            skills = conn.execute(
                "SELECT skill_name FROM skills WHERE status = 'active' AND skill_name = ?",
                (skill_name,),
            ).fetchall()
        else:
            skills = conn.execute(
                "SELECT skill_name FROM skills WHERE status = 'active'"
            ).fetchall()
        conn.close()

        for skill_row in skills:
            name = skill_row["skill_name"]
            perf = self.get_skill_performance(name)

            if perf["total_uses"] < 3:
                continue  # 样本不足

            # 1. 低成功率建议
            if perf["success_rate"] < 0.7:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"sugg_{uuid.uuid4().hex[:8]}",
                    skill_name=name,
                    suggestion="提高技能成功率",
                    priority=0.9,
                    reason=f"当前成功率仅 {perf['success_rate']:.0%}",
                    expected_improvement="成功率提升至90%以上",
                ))

            # 2. 响应时间过长建议
            if perf["avg_response_time"] > 2.0:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"sugg_{uuid.uuid4().hex[:8]}",
                    skill_name=name,
                    suggestion="优化响应时间",
                    priority=0.7,
                    reason=f"平均响应时间 {perf['avg_response_time']:.2f}秒",
                    expected_improvement="响应时间降低到1秒以内",
                ))

            # 3. 用户评分低建议
            if perf["avg_user_rating"] < 0.5:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"sugg_{uuid.uuid4().hex[:8]}",
                    skill_name=name,
                    suggestion="改善用户体验",
                    priority=0.8,
                    reason=f"用户平均评分仅 {perf['avg_user_rating']:.1f}/1.0",
                    expected_improvement="用户评分提升到0.8以上",
                ))

        # 按优先级排序
        suggestions.sort(key=lambda x: -x.priority)
        return suggestions

    # ── Lifecycle Management ──────────────────────────────────────────────

    def get_deprecation_candidates(self) -> List[Dict]:
        """
        获取可能应该废弃的技能

        Returns:
            候选列表
        """
        conn = self._get_conn()
        cutoff = time.time() - 30 * 86400  # 30天

        rows = conn.execute(
            """SELECT s.skill_name, s.description,
               COUNT(sr.id) as recent_uses
               FROM skills s
               LEFT JOIN skill_results sr ON s.skill_name = sr.skill_name AND sr.timestamp > ?
               WHERE s.status = 'active'
               GROUP BY s.skill_name
               HAVING recent_uses = 0
               ORDER BY s.updated_at ASC""",
            (cutoff,),
        ).fetchall()
        conn.close()

        return [
            {
                "skill_name": r["skill_name"],
                "description": r["description"],
                "reason": "30天内无使用记录",
                "last_updated": r["last_updated"] if "last_updated" in r else None,
            }
            for r in rows
        ]

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """获取系统整体统计"""
        conn = self._get_conn()
        total_skills = conn.execute(
            "SELECT COUNT(*) FROM skills"
        ).fetchone()[0]
        active_skills = conn.execute(
            "SELECT COUNT(*) FROM skills WHERE status = 'active'"
        ).fetchone()[0]
        total_versions = conn.execute(
            "SELECT COUNT(*) FROM skill_versions"
        ).fetchone()[0]
        total_results = conn.execute(
            "SELECT COUNT(*) FROM skill_results"
        ).fetchone()[0]
        conn.close()

        return {
            "total_skills": total_skills,
            "active_skills": active_skills,
            "total_versions": total_versions,
            "total_results_recorded": total_results,
        }

    def close(self):
        pass
