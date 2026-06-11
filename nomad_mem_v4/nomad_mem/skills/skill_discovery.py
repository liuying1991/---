"""
技能发现模块
从使用模式中发现新的技能组合和技能使用规律
"""
import sqlite3
import uuid
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import Counter
from itertools import combinations


@dataclass
class SkillUsage:
    usage_id: str
    skill_name: str
    context: str
    result: str
    timestamp: float
    success: bool


@dataclass
class SkillCombination:
    combo_id: str
    skills: List[str]
    frequency: int
    success_rate: float
    discovered_at: float


class SkillDiscoverer:
    """技能发现器 - 从使用模式中发现新的技能组合"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS skill_usage (
                    usage_id TEXT PRIMARY KEY,
                    skill_name TEXT NOT NULL,
                    context TEXT,
                    result TEXT,
                    timestamp REAL NOT NULL,
                    success INTEGER NOT NULL DEFAULT 1
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_skill ON skill_usage(skill_name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_time ON skill_usage(timestamp)")

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS skill_combinations (
                    combo_id TEXT PRIMARY KEY,
                    skills_json TEXT NOT NULL,
                    frequency INTEGER NOT NULL DEFAULT 1,
                    success_rate REAL NOT NULL DEFAULT 1.0,
                    discovered_at REAL NOT NULL
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_combo_freq ON skill_combinations(frequency DESC)")

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_sessions (
                    session_id TEXT PRIMARY KEY,
                    usage_ids_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def record_usage(self, skill_name: str, context: str = "", result: str = "", success: bool = True) -> str:
        """记录一次技能使用"""
        usage_id = str(uuid.uuid4())
        timestamp = time.time()
        with self.conn:
            self.conn.execute(
                "INSERT INTO skill_usage VALUES (?, ?, ?, ?, ?, ?)",
                (usage_id, skill_name, context, result, timestamp, int(success)),
            )
        return usage_id

    def _get_recent_session(self, window_seconds: float = 300.0) -> List[str]:
        """获取最近时间窗口内使用的技能列表"""
        cutoff = time.time() - window_seconds
        rows = self.conn.execute(
            "SELECT skill_name FROM skill_usage WHERE timestamp > ? ORDER BY timestamp",
            (cutoff,),
        ).fetchall()
        return [r["skill_name"] for r in rows]

    def find_combinations(self, min_frequency: int = 2) -> List[SkillCombination]:
        """找出经常一起使用的技能组合"""
        cutoff = time.time() - 86400 * 7  # 最近7天
        rows = self.conn.execute(
            "SELECT skill_name, usage_id, timestamp FROM skill_usage WHERE timestamp > ? ORDER BY timestamp",
            (cutoff,),
        ).fetchall()

        # 按时间窗口分组（5分钟窗口）
        sessions = []
        current_window = []
        window_start = 0
        for row in rows:
            if not current_window or row["timestamp"] - window_start > 300:
                if current_window:
                    sessions.append(current_window)
                current_window = [row["skill_name"]]
                window_start = row["timestamp"]
            else:
                current_window.append(row["skill_name"])
        if current_window:
            sessions.append(current_window)

        # 统计组合出现次数
        combo_counter: Counter = Counter()
        combo_success: Dict[str, List[bool]] = {}
        for session_skills in sessions:
            unique = sorted(set(session_skills))
            if len(unique) < 2:
                continue
            for size in range(2, min(len(unique) + 1, 4)):  # 最多3技能组合
                for combo in combinations(unique, size):
                    key = ",".join(combo)
                    combo_counter[key] += 1
                    combo_success.setdefault(key, [])
                    # 查该session中这些技能的成功率
                    for s in combo:
                        r = self.conn.execute(
                            "SELECT success FROM skill_usage WHERE skill_name=? AND timestamp > ? ORDER BY timestamp DESC LIMIT 1",
                            (s, cutoff),
                        ).fetchone()
                        if r:
                            combo_success[key].append(bool(r["success"]))

        results = []
        now = time.time()
        for combo_str, freq in combo_counter.most_common():
            if freq < min_frequency:
                continue
            skills = combo_str.split(",")
            successes = combo_success.get(combo_str, [])
            success_rate = sum(successes) / len(successes) if successes else 0.0

            combo_id = str(uuid.uuid4())
            # 持久化组合
            import json
            existing = self.conn.execute(
                "SELECT combo_id FROM skill_combinations WHERE skills_json=?",
                (combo_str,),
            ).fetchone()
            if existing:
                combo_id = existing["combo_id"]
                self.conn.execute(
                    "UPDATE skill_combinations SET frequency=?, success_rate=? WHERE combo_id=?",
                    (freq, success_rate, combo_id),
                )
            else:
                self.conn.execute(
                    "INSERT INTO skill_combinations VALUES (?, ?, ?, ?, ?)",
                    (combo_id, combo_str, freq, success_rate, now),
                )

            results.append(SkillCombination(
                combo_id=combo_id,
                skills=skills,
                frequency=freq,
                success_rate=success_rate,
                discovered_at=now,
            ))

        return results

    def suggest_next_skill(self, current_skills: List[str]) -> Optional[str]:
        """根据当前使用的技能，建议下一个可能需要的技能"""
        if not current_skills:
            return None

        cutoff = time.time() - 86400 * 7
        suggestions: Counter = Counter()

        for skill in current_skills:
            # 找出与该技能在同一时间窗口内使用的其他技能
            rows = self.conn.execute(
                """
                SELECT su2.skill_name
                FROM skill_usage su1
                JOIN skill_usage su2 ON su2.timestamp BETWEEN su1.timestamp - 300 AND su1.timestamp + 300
                WHERE su1.skill_name = ? AND su2.skill_name != ? AND su1.timestamp > ?
                """,
                (skill, skill, cutoff),
            ).fetchall()
            for r in rows:
                suggestions[r["skill_name"]] += 1

        # 排除已经在当前技能列表中的
        for s in current_skills:
            suggestions.pop(s, None)

        if suggestions:
            return suggestions.most_common(1)[0][0]
        return None

    def get_skill_stats(self, skill_name: str) -> Dict:
        """获取某个技能的统计信息"""
        row = self.conn.execute(
            """
            SELECT
                COUNT(*) as usage_count,
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                MIN(timestamp) as first_used,
                MAX(timestamp) as last_used
            FROM skill_usage
            WHERE skill_name = ?
            """,
            (skill_name,),
        ).fetchone()

        if not row or row["usage_count"] == 0:
            return {
                "skill_name": skill_name,
                "usage_count": 0,
                "success_rate": 0.0,
                "first_used": None,
                "last_used": None,
                "contexts": [],
            }

        context_rows = self.conn.execute(
            "SELECT DISTINCT context FROM skill_usage WHERE skill_name=? AND context!='' LIMIT 10",
            (skill_name,),
        ).fetchall()

        return {
            "skill_name": skill_name,
            "usage_count": row["usage_count"],
            "success_rate": round(row["success_rate"], 4),
            "first_used": row["first_used"],
            "last_used": row["last_used"],
            "contexts": [r["context"] for r in context_rows],
        }

    def get_top_skills(self, limit: int = 10) -> List[Dict]:
        """获取最常用的技能（按使用频率和成功率排序）"""
        rows = self.conn.execute(
            """
            SELECT
                skill_name,
                COUNT(*) as usage_count,
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM skill_usage
            GROUP BY skill_name
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            {
                "skill_name": r["skill_name"],
                "usage_count": r["usage_count"],
                "success_rate": round(r["success_rate"], 4),
            }
            for r in rows
        ]

    def discover_new_patterns(self) -> List[Dict]:
        """发现新的技能使用模式"""
        patterns = []

        # 1. 高频技能序列
        cutoff = time.time() - 86400 * 7
        rows = self.conn.execute(
            "SELECT skill_name, timestamp FROM skill_usage WHERE timestamp > ? ORDER BY timestamp",
            (cutoff,),
        ).fetchall()

        sequences: Counter = Counter()
        for i in range(len(rows) - 1):
            seq = f"{rows[i]['skill_name']} -> {rows[i+1]['skill_name']}"
            sequences[seq] += 1

        for seq, count in sequences.most_common(5):
            if count >= 2:
                patterns.append({
                    "pattern_type": "sequence",
                    "pattern": seq,
                    "frequency": count,
                })

        # 2. 高成功率技能
        top = self.get_top_skills(limit=5)
        for s in top:
            if s["success_rate"] >= 0.9 and s["usage_count"] >= 3:
                patterns.append({
                    "pattern_type": "high_success_skill",
                    "pattern": s["skill_name"],
                    "frequency": s["usage_count"],
                    "success_rate": s["success_rate"],
                })

        # 3. 技能组合模式
        combos = self.find_combinations(min_frequency=2)
        for combo in combos[:3]:
            patterns.append({
                "pattern_type": "combination",
                "pattern": combo.skills,
                "frequency": combo.frequency,
                "success_rate": combo.success_rate,
            })

        return patterns

    def close(self):
        self.conn.close()
