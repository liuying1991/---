"""
工具选择器模块

根据用户意图自动选择合适的工具 —— 像 Jarvis 一样智能判断该用哪个工具完成任务。

设计原则:
- 多策略匹配: 关键词、语义(简单)、上下文、历史
- 综合打分排序: 多维度评分,得分越高越匹配
- 从选择结果中学习: 记录成功/失败反馈,持续优化
- 第一性原理: 工具选择的本质是匹配用户意图与工具能力,匹配度越高效果越好
"""
from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SelectionStrategy(str, Enum):
    """选择策略"""
    KEYWORD_MATCH = "keyword_match"      # 关键词匹配
    SEMANTIC_MATCH = "semantic_match"    # 语义匹配(简单)
    CONTEXT_MATCH = "context_match"      # 上下文匹配
    HISTORY_MATCH = "history_match"      # 历史匹配


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ToolMatch:
    """工具匹配结果"""
    tool_id: str
    score: float                          # 0.0 - 1.0, 越高越匹配
    reason: str                           # 匹配原因说明
    parameters: Dict[str, Any] = field(default_factory=dict)
    strategy: SelectionStrategy = SelectionStrategy.KEYWORD_MATCH

    def __lt__(self, other: ToolMatch) -> bool:
        return self.score < other.score


# ---------------------------------------------------------------------------
# Keyword patterns database
# ---------------------------------------------------------------------------

# 意图类别到关键词的映射
INTENT_KEYWORDS: Dict[str, List[str]] = {
    "file": ["文件", "文件夹", "创建", "删除", "复制", "移动", "读取", "写入", "下载", "上传",
             "file", "folder", "create", "delete", "copy", "move", "read", "write", "download", "upload"],
    "system": ["系统", "进程", "内存", "CPU", "磁盘", "网络", "重启", "关机",
               "system", "process", "memory", "cpu", "disk", "network", "restart", "shutdown"],
    "time": ["时间", "日期", "日程", "提醒", "闹钟", "计时", "天气",
             "time", "date", "schedule", "reminder", "alarm", "timer", "weather"],
    "search": ["搜索", "查找", "查询", "检索", "找",
               "search", "find", "query", "look up"],
    "calculation": ["计算", "算", "数学", "公式", "转换",
                    "calculate", "math", "formula", "convert"],
    "communication": ["发送", "邮件", "消息", "通知", "打电话", "聊天",
                      "send", "email", "message", "notify", "call", "chat"],
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class ToolSelector:
    """
    工具选择器 —— 根据用户意图自动选择最合适的工具。

    核心思路:
    1. 多策略并行匹配(关键词、语义、上下文、历史)
    2. 综合各策略得分,按总分排序
    3. 记录选择结果,用于后续学习和优化
    """

    def __init__(
        self,
        tool_registry,
        db_path: Optional[str] = None,
    ) -> None:
        """
        初始化选择器。

        Args:
            tool_registry: ToolRegistry 实例
            db_path: SQLite 数据库路径,默认使用 nomad_mem 下的 tool_selector.db
        """
        self._registry = tool_registry

        # 确定数据库路径
        if db_path is None:
            base = Path(__file__).resolve().parents[2] / "data"
            base.mkdir(parents=True, exist_ok=True)
            db_path = str(base / "tool_selector.db")

        self._db_path = db_path
        self._init_db()

    # -- database -----------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """初始化 SQLite 表结构。"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS selection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    tool_id TEXT NOT NULL,
                    intent_category TEXT,
                    strategy TEXT,
                    score REAL,
                    success INTEGER,          -- 1=成功, 0=失败
                    timestamp REAL NOT NULL,
                    message TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sh_user
                ON selection_history(user_id, timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sh_tool
                ON selection_history(tool_id)
            """)

    # -- public API ---------------------------------------------------------

    def select_tools(
        self,
        intent_category: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ToolMatch]:
        """
        选择匹配意图的工具列表,按得分降序排列。

        Args:
            intent_category: 意图类别(如 file, system, time 等)
            message: 用户原始消息
            context: 上下文信息(可选)

        Returns:
            按得分排序的 ToolMatch 列表
        """
        tools = self._registry.list_tools()
        if not tools:
            return []

        # 并行执行各策略
        keyword_matches = self.match_by_keyword(message, tools)
        context_matches = self.match_by_context(context or {}, tools) if context else []
        history_matches = self._match_by_history(intent_category, tools)

        # 合并并去重(保留最高分)
        combined: Dict[str, ToolMatch] = {}
        for match_list in [keyword_matches, context_matches, history_matches]:
            for m in match_list:
                existing = combined.get(m.tool_id)
                if existing is None or m.score > existing.score:
                    combined[m.tool_id] = m

        # 按得分降序
        results = sorted(combined.values(), key=lambda x: x.score, reverse=True)
        logger.debug(
            "ToolSelector selected %d tools for intent='%s'",
            len(results), intent_category,
        )
        return results

    def get_top_tool(
        self,
        intent_category: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[ToolMatch]:
        """
        获取得分最高的工具。

        Args:
            intent_category: 意图类别
            message: 用户原始消息
            context: 上下文信息(可选)

        Returns:
            最佳匹配的 ToolMatch,无匹配时返回 None
        """
        matches = self.select_tools(intent_category, message, context)
        return matches[0] if matches else None

    def match_by_keyword(
        self,
        query: str,
        tools: list,
    ) -> List[ToolMatch]:
        """
        基于关键词匹配工具。

        将用户查询与预定义的意图关键词对照,找到相关工具。

        Args:
            query: 用户查询文本
            tools: 候选工具列表

        Returns:
            关键词匹配的 ToolMatch 列表
        """
        matches: List[ToolMatch] = []
        query_lower = query.lower()

        for tool in tools:
            score = 0.0
            matched_keywords: List[str] = []

            # 1. 工具名称匹配 (权重最高)
            if tool.name.lower() in query_lower:
                score += 0.5
                matched_keywords.append(tool.name)

            # 2. 工具描述匹配
            if tool.description.lower() in query_lower:
                score += 0.3
                matched_keywords.append(tool.description[:30])

            # 3. 意图关键词匹配
            intent_kw = INTENT_KEYWORDS.get(tool.category.value, [])
            for kw in intent_kw:
                if kw.lower() in query_lower:
                    score += 0.2
                    matched_keywords.append(kw)
                    break  # 每个类别只计一次

            # 4. 工具参数名称匹配
            for param in tool.parameters:
                if param.name.lower() in query_lower:
                    score += 0.1
                    matched_keywords.append(param.name)

            if score > 0:
                # 分数封顶 1.0
                score = min(score, 1.0)
                matches.append(ToolMatch(
                    tool_id=tool.tool_id,
                    score=score,
                    reason=f"关键词匹配: {', '.join(matched_keywords)}",
                    strategy=SelectionStrategy.KEYWORD_MATCH,
                ))

        return matches

    def match_by_context(
        self,
        context: Dict[str, Any],
        tools: list,
    ) -> List[ToolMatch]:
        """
        基于上下文匹配工具。

        利用当前上下文(如当前位置、当前操作等)提升相关工具的得分。

        Args:
            context: 上下文信息字典,支持以下键:
                - last_tool: 上次使用的工具 ID
                - current_location: 当前位置/路径
                - current_action: 当前正在进行的操作
                - related_tools: 相关工具 ID 列表
            tools: 候选工具列表

        Returns:
            上下文匹配的 ToolMatch 列表
        """
        matches: List[ToolMatch] = []

        last_tool = context.get("last_tool")
        current_action = context.get("current_action", "").lower()
        related_tools: List[str] = context.get("related_tools", [])
        current_location = context.get("current_location", "").lower()

        for tool in tools:
            score = 0.0
            reasons: List[str] = []

            # 1. 上次使用的工具(连续性)
            if last_tool and tool.tool_id == last_tool:
                score += 0.3
                reasons.append("上次使用的工具")

            # 2. 相关工具推荐
            if tool.tool_id in related_tools:
                score += 0.4
                reasons.append("关联工具推荐")

            # 3. 当前操作相关性
            if current_action:
                tool_desc_lower = tool.description.lower()
                tool_name_lower = tool.name.lower()
                if current_action in tool_desc_lower or current_action in tool_name_lower:
                    score += 0.2
                    reasons.append(f"与当前操作 '{current_action}' 相关")

            # 4. 位置相关性(路径匹配)
            if current_location and tool.category.value in ("file", "system"):
                if current_location in tool.description.lower():
                    score += 0.15
                    reasons.append("与当前位置相关")

            if score > 0:
                score = min(score, 1.0)
                matches.append(ToolMatch(
                    tool_id=tool.tool_id,
                    score=score,
                    reason="上下文匹配: " + ", ".join(reasons),
                    strategy=SelectionStrategy.CONTEXT_MATCH,
                ))

        return matches

    def record_selection(self, tool_id: str, success: bool) -> None:
        """
        记录选择结果,用于学习优化。

        Args:
            tool_id: 被选中的工具 ID
            success: 是否执行成功
        """
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO selection_history
                    (tool_id, success, timestamp)
                VALUES (?, ?, ?)
            """, (tool_id, 1 if success else 0, time.time()))
            logger.info(
                "Recorded selection: tool=%s success=%s",
                tool_id, success,
            )

    def record_full_selection(
        self,
        tool_id: str,
        intent_category: str,
        strategy: SelectionStrategy,
        score: float,
        success: bool,
        user_id: str = "default",
        message: Optional[str] = None,
    ) -> None:
        """
        记录完整的选中信息。

        Args:
            tool_id: 工具 ID
            intent_category: 意图类别
            strategy: 使用的选择策略
            score: 匹配得分
            success: 是否成功
            user_id: 用户 ID
            message: 用户消息
        """
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO selection_history
                    (user_id, tool_id, intent_category, strategy, score, success, timestamp, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, tool_id, intent_category, strategy.value,
                score, 1 if success else 0, time.time(), message,
            ))

    def get_selection_history(
        self,
        user_id: str = "default",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取选择历史记录。

        Args:
            user_id: 用户 ID
            limit: 返回条数上限

        Returns:
            历史记录列表(按时间倒序)
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, user_id, tool_id, intent_category, strategy,
                       score, success, timestamp, message
                FROM selection_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()

        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "tool_id": row["tool_id"],
                "intent_category": row["intent_category"],
                "strategy": row["strategy"],
                "score": row["score"],
                "success": bool(row["success"]),
                "timestamp": row["timestamp"],
                "message": row["message"],
            }
            for row in rows
        ]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取选择统计信息。

        Returns:
            统计字典,包含:
                - total_selections: 总选择次数
                - accuracy: 成功率
                - most_selected: 最常被选中的工具列表
                - by_strategy: 各策略使用次数
                - by_intent: 各意图类别使用次数
        """
        with self._get_conn() as conn:
            # 总选择次数
            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM selection_history"
            ).fetchone()["cnt"]

            if total == 0:
                return {
                    "total_selections": 0,
                    "accuracy": 0.0,
                    "most_selected": [],
                    "by_strategy": {},
                    "by_intent": {},
                }

            # 成功率
            success_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM selection_history WHERE success = 1"
            ).fetchone()["cnt"]
            accuracy = success_count / total if total > 0 else 0.0

            # 最常被选中的工具
            most_selected_rows = conn.execute("""
                SELECT tool_id, COUNT(*) as cnt,
                       SUM(success) as succ
                FROM selection_history
                GROUP BY tool_id
                ORDER BY cnt DESC
                LIMIT 10
            """).fetchall()
            most_selected = [
                {
                    "tool_id": r["tool_id"],
                    "count": r["cnt"],
                    "success_rate": r["succ"] / r["cnt"] if r["cnt"] > 0 else 0.0,
                }
                for r in most_selected_rows
            ]

            # 各策略使用次数
            by_strategy_rows = conn.execute("""
                SELECT strategy, COUNT(*) as cnt
                FROM selection_history
                WHERE strategy IS NOT NULL
                GROUP BY strategy
            """).fetchall()
            by_strategy = {r["strategy"]: r["cnt"] for r in by_strategy_rows}

            # 各意图类别使用次数
            by_intent_rows = conn.execute("""
                SELECT intent_category, COUNT(*) as cnt
                FROM selection_history
                WHERE intent_category IS NOT NULL
                GROUP BY intent_category
            """).fetchall()
            by_intent = {r["intent_category"]: r["cnt"] for r in by_intent_rows}

        return {
            "total_selections": total,
            "accuracy": round(accuracy, 4),
            "most_selected": most_selected,
            "by_strategy": by_strategy,
            "by_intent": by_intent,
        }

    def close(self) -> None:
        """关闭数据库连接。"""
        # SQLite 连接在上下文管理器中自动关闭,无需额外操作
        logger.info("ToolSelector closed")

    # -- internal helpers ---------------------------------------------------

    def _match_by_history(
        self,
        intent_category: str,
        tools: list,
    ) -> List[ToolMatch]:
        """
        基于历史选择记录匹配工具。

        查找历史上在同一意图类别下成功使用的工具。

        Args:
            intent_category: 意图类别
            tools: 候选工具列表

        Returns:
            历史匹配的 ToolMatch 列表
        """
        tool_ids = {t.tool_id for t in tools}

        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT tool_id,
                       COUNT(*) as total,
                       SUM(success) as successes
                FROM selection_history
                WHERE intent_category = ?
                  AND tool_id IN ({})
                GROUP BY tool_id
                ORDER BY successes DESC, total DESC
            """.format(",".join("?" * len(tool_ids))),
                [intent_category] + list(tool_ids),
            ).fetchall()

        matches: List[ToolMatch] = []
        for row in rows:
            total = row["total"]
            successes = row["successes"]
            success_rate = successes / total if total > 0 else 0.0

            # 历史成功率直接作为得分,使用次数作为修正因子
            usage_bonus = min(total / 10, 0.1)  # 最多 +0.1
            score = min(success_rate + usage_bonus, 1.0)

            matches.append(ToolMatch(
                tool_id=row["tool_id"],
                score=score,
                reason=f"历史匹配: 成功率 {success_rate:.0%} ({successes}/{total} 次)",
                strategy=SelectionStrategy.HISTORY_MATCH,
            ))

        return matches
