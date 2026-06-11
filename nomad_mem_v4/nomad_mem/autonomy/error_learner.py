"""
ErrorLearner - 错误学习模块

从错误中学习，避免重复犯错——自我进化的核心机制。

设计原则：
- 跟踪错误频率，识别重复模式
- 存储成功的纠正作为可复用策略
- 使用纠正成功率排序建议
- 简单模式匹配（无ML）- 匹配错误类型和上下文关键词
- 第一性原理：从错误中学习是最基本的智能形式
"""
import sqlite3
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import os
import json


class ErrorType(Enum):
    """错误类型"""
    UNDERSTANDING = "understanding"    # 理解错误：误解用户意图
    EXECUTION = "execution"            # 执行错误：任务执行失败
    SAFETY = "safety"                  # 安全错误：违反安全规则
    CONTEXT = "context"                # 上下文错误：上下文理解偏差
    KNOWLEDGE = "knowledge"            # 知识错误：知识缺失或过时
    RESPONSE = "response"              # 响应错误：响应质量不佳


class SeverityLevel(Enum):
    """严重程度"""
    LOW = "low"            # 低：轻微问题，不影响核心功能
    MEDIUM = "medium"      # 中：明显问题，影响体验
    HIGH = "high"          # 高：严重问题，功能受损
    CRITICAL = "critical"  # 危急：安全问题或数据损坏


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    error_type: str
    severity: str
    description: str
    context: str
    correction: str
    timestamp: str
    user_id: str
    frequency: int = 1
    last_corrected: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "severity": self.severity,
            "description": self.description,
            "context": self.context,
            "correction": self.correction,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "frequency": self.frequency,
            "last_corrected": self.last_corrected,
        }


@dataclass
class CorrectionStrategy:
    """纠正策略"""
    strategy_id: str
    error_type: str
    trigger_pattern: str
    action: str
    success_count: int = 0
    failure_count: int = 0
    created_at: str = ""

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def to_dict(self) -> Dict:
        return {
            "strategy_id": self.strategy_id,
            "error_type": self.error_type,
            "trigger_pattern": self.trigger_pattern,
            "action": self.action,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at,
        }


class ErrorLearner:
    """
    错误学习器

    核心职责：
    1. 记录错误并建立模式库
    2. 根据历史纠正经验推荐修复策略
    3. 分析用户的错误模式
    4. 提供实时自我纠正建议
    """

    def __init__(self, db_path: str = "data/error_learning.db"):
        """
        初始化错误学习器

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()

        # 错误记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                error_id TEXT PRIMARY KEY,
                error_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                context TEXT DEFAULT '',
                correction TEXT DEFAULT '',
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_corrected TEXT
            )
        """)

        # 纠正策略表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correction_strategies (
                strategy_id TEXT PRIMARY KEY,
                error_type TEXT NOT NULL,
                trigger_pattern TEXT NOT NULL,
                action TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        # 错误关键词索引表（用于快速检索）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                FOREIGN KEY (error_id) REFERENCES errors(error_id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_errors_type ON errors(error_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_errors_user ON errors(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_errors_type_severity ON errors(error_type, severity)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON error_keywords(keyword)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategies_type ON correction_strategies(error_type)
        """)

        self.conn.commit()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词（简单分词）

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        if not text:
            return []
        # 简单分词：按空格、标点分割，过滤短词
        import re
        words = re.findall(r'[\w\u4e00-\u9fff]{2,}', text.lower())
        # 过滤常见停用词
        stop_words = {'the', 'is', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                      'for', 'of', 'with', 'by', 'this', 'that', 'it', 'not', 'are', 'was'}
        return [w for w in words if w not in stop_words]

    def _record_keywords(self, error_id: str, text: str):
        """
        记录错误关键词

        Args:
            error_id: 错误ID
            text: 用于提取关键词的文本
        """
        cursor = self.conn.cursor()
        keywords = self._extract_keywords(text)
        for keyword in keywords:
            cursor.execute("""
                INSERT INTO error_keywords (error_id, keyword) VALUES (?, ?)
            """, (error_id, keyword))
        self.conn.commit()

    def record_error(self, user_id: str, error_type: str, description: str,
                     context: str = "", correction: str = "") -> str:
        """
        记录错误

        Args:
            user_id: 用户ID
            error_type: 错误类型（ErrorType枚举值或字符串）
            description: 错误描述
            context: 错误发生的上下文
            correction: 纠正措施

        Returns:
            错误记录ID
        """
        error_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # 确保error_type是有效的枚举值
        if isinstance(error_type, ErrorType):
            error_type = error_type.value

        # 确保severity是有效的枚举值（默认MEDIUM）
        severity = SeverityLevel.MEDIUM.value

        cursor = self.conn.cursor()

        # 检查是否有相似的已有错误（根据类型和描述匹配）
        cursor.execute("""
            SELECT error_id, description, frequency
            FROM errors
            WHERE user_id = ? AND error_type = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id, error_type))

        existing = cursor.fetchone()
        now_ts = now

        if existing:
            existing_desc = existing["description"]
            # 简单相似度检查：共享关键词
            existing_keywords = set(self._extract_keywords(existing_desc))
            new_keywords = set(self._extract_keywords(description))
            shared = existing_keywords & new_keywords

            if len(shared) >= 1:
                # 认为是相同错误，增加频率
                new_freq = existing["frequency"] + 1
                last_corrected_val = now if correction else existing.get("last_corrected")
                update_correction = correction if correction else existing.get("correction", "")

                cursor.execute("""
                    UPDATE errors
                    SET frequency = ?, correction = ?, last_corrected = ?, description = ?
                    WHERE error_id = ?
                """, (new_freq, update_correction, last_corrected_val, description, existing["error_id"]))

                self.conn.commit()
                return existing["error_id"]

        # 新错误记录
        cursor.execute("""
            INSERT INTO errors (error_id, error_type, severity, description,
                              context, correction, timestamp, user_id, frequency, last_corrected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (error_id, error_type, severity, description, context, correction, now_ts, user_id,
              now if correction else None))

        # 记录关键词
        self._record_keywords(error_id, description)
        if context:
            self._record_keywords(error_id, context)

        # 如果有纠正措施，创建纠正策略
        if correction:
            self._create_correction_strategy(error_type, description, correction)

        self.conn.commit()
        return error_id

    def _create_correction_strategy(self, error_type: str, trigger: str, action: str) -> str:
        """
        创建纠正策略

        Args:
            error_type: 错误类型
            trigger: 触发模式（描述）
            action: 纠正动作

        Returns:
            策略ID
        """
        strategy_id = f"strat_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO correction_strategies (strategy_id, error_type, trigger_pattern,
                                              action, success_count, failure_count, created_at)
            VALUES (?, ?, ?, ?, 0, 0, ?)
        """, (strategy_id, error_type, trigger[:200], action, now))
        self.conn.commit()
        return strategy_id

    def get_similar_errors(self, error_type: str, context: str = "") -> List[ErrorRecord]:
        """
        查找相似的历史错误

        Args:
            error_type: 错误类型
            context: 上下文（用于关键词匹配）

        Returns:
            相似错误记录列表
        """
        if isinstance(error_type, ErrorType):
            error_type = error_type.value

        cursor = self.conn.cursor()

        # 首先按类型查找
        cursor.execute("""
            SELECT * FROM errors
            WHERE error_type = ?
            ORDER BY frequency DESC, timestamp DESC
            LIMIT 50
        """, (error_type,))

        all_errors = [self._row_to_error(row) for row in cursor.fetchall()]

        # 如果有上下文，按关键词匹配度排序
        if context:
            context_keywords = set(self._extract_keywords(context))
            scored = []
            for err in all_errors:
                err_keywords = set(self._extract_keywords(err.description + " " + err.context))
                overlap = len(context_keywords & err_keywords)
                # 评分：关键词重叠 + 频率加权
                score = overlap + err.frequency * 0.5
                scored.append((score, err))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [err for _, err in scored[:20]]

        return all_errors[:20]

    def _row_to_error(self, row: sqlite3.Row) -> ErrorRecord:
        """将数据库行转换为ErrorRecord"""
        return ErrorRecord(
            error_id=row["error_id"],
            error_type=row["error_type"],
            severity=row["severity"],
            description=row["description"],
            context=row["context"],
            correction=row["correction"],
            timestamp=row["timestamp"],
            user_id=row["user_id"],
            frequency=row["frequency"],
            last_corrected=row["last_corrected"],
        )

    def _row_to_strategy(self, row: sqlite3.Row) -> CorrectionStrategy:
        """将数据库行转换为CorrectionStrategy"""
        return CorrectionStrategy(
            strategy_id=row["strategy_id"],
            error_type=row["error_type"],
            trigger_pattern=row["trigger_pattern"],
            action=row["action"],
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            created_at=row["created_at"],
        )

    def suggest_correction(self, error_type: str, context: str = "") -> str:
        """
        根据过去的成功纠正经验，建议纠正措施

        Args:
            error_type: 错误类型
            context: 当前上下文

        Returns:
            建议的纠正措施（空字符串表示无建议）
        """
        if isinstance(error_type, ErrorType):
            error_type = error_type.value

        cursor = self.conn.cursor()

        # 查找匹配的纠正策略，按成功率排序
        cursor.execute("""
            SELECT *,
                   CAST(success_count AS FLOAT) / NULLIF(success_count + failure_count, 0) as rate
            FROM correction_strategies
            WHERE error_type = ?
            ORDER BY rate DESC, success_count DESC
            LIMIT 5
        """, (error_type,))

        strategies = [self._row_to_strategy(row) for row in cursor.fetchall()]

        if not strategies:
            return ""

        # 如果有上下文，检查触发模式匹配
        if context:
            context_keywords = set(self._extract_keywords(context))
            best_match = None
            best_score = -1

            for strat in strategies:
                trigger_keywords = set(self._extract_keywords(strat.trigger_pattern))
                overlap = len(context_keywords & trigger_keywords)
                # 评分：关键词匹配 + 成功率加权
                score = overlap + strat.success_rate * 10
                if score > best_score:
                    best_score = score
                    best_match = strat

            if best_match:
                return best_match.action

        # 返回成功率最高的策略
        return strategies[0].action if strategies else ""

    def update_correction_success(self, strategy_id: str, success: bool):
        """
        更新纠正策略的成功率

        Args:
            strategy_id: 策略ID
            success: 是否成功
        """
        cursor = self.conn.cursor()

        if success:
            cursor.execute("""
                UPDATE correction_strategies
                SET success_count = success_count + 1
                WHERE strategy_id = ?
            """, (strategy_id,))
        else:
            cursor.execute("""
                UPDATE correction_strategies
                SET failure_count = failure_count + 1
                WHERE strategy_id = ?
            """, (strategy_id,))

        self.conn.commit()

    def get_error_patterns(self, user_id: str) -> List[Dict]:
        """
        分析用户的错误模式

        Args:
            user_id: 用户ID

        Returns:
            错误模式列表，每个模式包含类型、频率、严重程度等信息
        """
        cursor = self.conn.cursor()

        # 按错误类型聚合
        cursor.execute("""
            SELECT error_type,
                   COUNT(*) as error_count,
                   SUM(frequency) as total_occurrences,
                   AVG(CASE WHEN last_corrected IS NOT NULL THEN 1.0 ELSE 0.0 END) as correction_rate,
                   GROUP_CONCAT(DISTINCT severity) as severities
            FROM errors
            WHERE user_id = ?
            GROUP BY error_type
            ORDER BY total_occurrences DESC
        """, (user_id,))

        patterns = []
        for row in cursor.fetchall():
            # 获取该类型的高频错误描述
            cursor.execute("""
                SELECT description, frequency
                FROM errors
                WHERE user_id = ? AND error_type = ?
                ORDER BY frequency DESC
                LIMIT 3
            """, (user_id, row["error_type"]))

            top_errors = [{"description": r["description"], "frequency": r["frequency"]}
                         for r in cursor.fetchall()]

            patterns.append({
                "error_type": row["error_type"],
                "error_count": row["error_count"],
                "total_occurrences": row["total_occurrences"],
                "correction_rate": round(row["correction_rate"], 2) if row["correction_rate"] else 0,
                "severities": row["severities"].split(",") if row["severities"] else [],
                "top_errors": top_errors,
            })

        return patterns

    def get_error_stats(self) -> Dict:
        """
        获取错误统计信息

        Returns:
            包含总错误数、按类型分布、按严重程度分布、纠正率等统计信息
        """
        cursor = self.conn.cursor()

        # 总数
        cursor.execute("SELECT COUNT(*) as total FROM errors")
        total = cursor.fetchone()["total"]

        # 按类型分布
        cursor.execute("""
            SELECT error_type, COUNT(*) as count, SUM(frequency) as occurrences
            FROM errors
            GROUP BY error_type
            ORDER BY occurrences DESC
        """)
        by_type = {row["error_type"]: {"count": row["count"], "occurrences": row["occurrences"]}
                  for row in cursor.fetchall()}

        # 按严重程度分布
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM errors
            GROUP BY severity
            ORDER BY count DESC
        """)
        by_severity = {row["severity"]: row["count"] for row in cursor.fetchall()}

        # 纠正率
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN last_corrected IS NOT NULL THEN 1 END) as corrected
            FROM errors
        """)
        row = cursor.fetchone()
        total_errors = row["total"]
        corrected = row["corrected"]
        correction_rate = round(corrected / total_errors, 2) if total_errors > 0 else 0

        # 高频错误（Top 5）
        cursor.execute("""
            SELECT description, error_type, frequency
            FROM errors
            ORDER BY frequency DESC
            LIMIT 5
        """)
        frequent_errors = [{"description": r["description"],
                          "error_type": r["error_type"],
                          "frequency": r["frequency"]}
                         for r in cursor.fetchall()]

        # 策略统计
        cursor.execute("""
            SELECT COUNT(*) as total_strategies,
                   AVG(CAST(success_count AS FLOAT) / NULLIF(success_count + failure_count, 0)) as avg_success_rate
            FROM correction_strategies
        """)
        strat_row = cursor.fetchone()

        return {
            "total_errors": total,
            "by_type": by_type,
            "by_severity": by_severity,
            "correction_rate": correction_rate,
            "frequent_errors": frequent_errors,
            "total_strategies": strat_row["total_strategies"],
            "avg_strategy_success_rate": round(strat_row["avg_success_rate"], 2)
                if strat_row["avg_success_rate"] else 0,
        }

    def apply_self_correction(self, error_type: str, current_context: str) -> Dict:
        """
        应用自我纠正

        基于历史纠正经验，返回可应用的纠正动作。

        Args:
            error_type: 当前错误类型
            current_context: 当前上下文

        Returns:
            纠正动作字典，包含 action, strategy_id, confidence, past_frequency
        """
        if isinstance(error_type, ErrorType):
            error_type = error_type.value

        cursor = self.conn.cursor()

        # 查找最佳纠正策略
        cursor.execute("""
            SELECT *,
                   CAST(success_count AS FLOAT) / NULLIF(success_count + failure_count, 0) as rate
            FROM correction_strategies
            WHERE error_type = ?
            ORDER BY rate DESC, success_count DESC
            LIMIT 3
        """, (error_type,))

        strategies = cursor.fetchall()

        if not strategies:
            return {
                "action": "",
                "strategy_id": None,
                "confidence": 0.0,
                "past_frequency": 0,
                "suggestion": "No historical correction data for this error type.",
            }

        # 选择最佳匹配
        best = strategies[0]
        context_keywords = set(self._extract_keywords(current_context)) if current_context else set()

        confidence = best["rate"] if best["rate"] else 0.0

        # 如果上下文匹配，提高置信度
        if context_keywords:
            trigger_keywords = set(self._extract_keywords(best["trigger_pattern"]))
            if trigger_keywords & context_keywords:
                confidence = min(1.0, confidence + 0.2)

        return {
            "action": best["action"],
            "strategy_id": best["strategy_id"],
            "confidence": round(confidence, 2),
            "past_frequency": best["success_count"] + best["failure_count"],
            "suggestion": f"Based on {best['success_count']} successful corrections out of "
                         f"{best['success_count'] + best['failure_count']} attempts.",
        }

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """析构函数，确保关闭连接"""
        try:
            self.close()
        except Exception:
            pass
