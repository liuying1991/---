"""
MemoryOS - AI代理记忆操作系统

参考论文：MemoryOS (EMNLP 2025) - https://github.com/BAI-LAB/MemoryOS

核心架构：
- 三级存储单元：短期记忆、中期记忆、长期个人记忆
- 四级功能模块：存储、更新、检索、生成
- 动态更新：短期→中期（FIFO对话链）、中期→长期（分段页组织策略）
"""
import time
import json
import sqlite3
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum


class MemoryLevel(Enum):
    """记忆级别"""
    SHORT_TERM = "short_term"      # 短期记忆（当前会话）
    MID_TERM = "mid_term"          # 中期记忆（会话链）
    LONG_TERM = "long_term"        # 长期记忆（个人画像）


@dataclass
class MemoryUnit:
    """记忆单元"""
    id: str
    level: MemoryLevel
    content: str
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)  # 关联记忆ID


@dataclass
class DialogChain:
    """对话链 - 用于短期→中期转换"""
    session_id: str
    messages: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    summary: str = ""
    key_points: List[str] = field(default_factory=list)


class MemoryStorage:
    """记忆存储模块 - 三级存储管理"""

    def __init__(self, db_path: str = "data/memory_os.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self.short_term_cache: Dict[str, MemoryUnit] = {}

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                level TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at REAL,
                updated_at REAL,
                access_count INTEGER DEFAULT 0,
                importance REAL DEFAULT 0.5,
                tags TEXT DEFAULT '[]',
                links TEXT DEFAULT '[]'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialog_chains (
                session_id TEXT PRIMARY KEY,
                messages TEXT DEFAULT '[]',
                created_at REAL,
                summary TEXT DEFAULT '',
                key_points TEXT DEFAULT '[]'
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_level ON memories(level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_importance ON memories(importance)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_created ON memories(created_at)")
        self.conn.commit()

    def store(self, unit: MemoryUnit) -> str:
        """存储记忆单元"""
        # 短期记忆使用内存缓存
        if unit.level == MemoryLevel.SHORT_TERM:
            self.short_term_cache[unit.id] = unit
            return unit.id

        # 中长期记忆持久化
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memories
            (id, level, content, metadata, created_at, updated_at, access_count, importance, tags, links)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unit.id, unit.level.value, unit.content,
            json.dumps(unit.metadata), unit.created_at, unit.updated_at,
            unit.access_count, unit.importance,
            json.dumps(unit.tags), json.dumps(unit.links)
        ))
        self.conn.commit()
        return unit.id

    def retrieve(self, memory_id: str) -> Optional[MemoryUnit]:
        """检索记忆单元"""
        # 先查短期缓存
        if memory_id in self.short_term_cache:
            unit = self.short_term_cache[memory_id]
            unit.access_count += 1
            return unit

        # 查询数据库
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        if not row:
            return None

        unit = MemoryUnit(
            id=row["id"],
            level=MemoryLevel(row["level"]),
            content=row["content"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            access_count=row["access_count"] + 1,
            importance=row["importance"],
            tags=json.loads(row["tags"]),
            links=json.loads(row["links"])
        )
        # 更新访问计数
        cursor.execute("UPDATE memories SET access_count = ? WHERE id = ?",
                      (unit.access_count, memory_id))
        self.conn.commit()
        return unit

    def search_by_level(self, level: MemoryLevel, limit: int = 10) -> List[MemoryUnit]:
        """按级别搜索记忆"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM memories WHERE level = ? ORDER BY importance DESC LIMIT ?
        """, (level.value, limit))

        units = []
        for row in cursor.fetchall():
            units.append(MemoryUnit(
                id=row["id"],
                level=MemoryLevel(row["level"]),
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                access_count=row["access_count"],
                importance=row["importance"],
                tags=json.loads(row["tags"]),
                links=json.loads(row["links"])
            ))
        return units

    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryUnit]:
        """按标签搜索记忆"""
        cursor = self.conn.cursor()
        # 搜索包含任一标签的记忆
        results = []
        for tag in tags:
            cursor.execute("""
                SELECT * FROM memories WHERE tags LIKE ? ORDER BY importance DESC LIMIT ?
            """, (f'%"%{tag}%"%', limit))
            for row in cursor.fetchall():
                unit = MemoryUnit(
                    id=row["id"],
                    level=MemoryLevel(row["level"]),
                    content=row["content"],
                    metadata=json.loads(row["metadata"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    access_count=row["access_count"],
                    importance=row["importance"],
                    tags=json.loads(row["tags"]),
                    links=json.loads(row["links"])
                )
                results.append(unit)
        return results[:limit]

    def search_by_content(self, query: str, limit: int = 10) -> List[MemoryUnit]:
        """按内容搜索记忆（LIKE搜索，短期记忆也从缓存搜索）"""
        results = []

        # 短期记忆从缓存搜索
        for unit in self.short_term_cache.values():
            if query.lower() in unit.content.lower():
                results.append(unit)

        # 中长期记忆从数据库搜索
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM memories
            WHERE content LIKE ?
            ORDER BY importance DESC
            LIMIT ?
        """, (f"%{query}%", limit))

        for row in cursor.fetchall():
            unit = MemoryUnit(
                id=row["id"],
                level=MemoryLevel(row["level"]),
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                access_count=row["access_count"],
                importance=row["importance"],
                tags=json.loads(row["tags"]),
                links=json.loads(row["links"])
            )
            results.append(unit)

        # 按重要性排序
        results.sort(key=lambda u: u.importance, reverse=True)
        return results[:limit]

    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self.short_term_cache:
            del self.short_term_cache[memory_id]
            return True

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_stats(self) -> Dict:
        """获取存储统计"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT level, COUNT(*) as cnt FROM memories GROUP BY level")
        level_counts = {row["level"]: row["cnt"] for row in cursor.fetchall()}

        return {
            "short_term": len(self.short_term_cache),
            **level_counts,
            "total": sum(level_counts.values()) + len(self.short_term_cache)
        }

    def close(self):
        self.conn.close()


class MemoryUpdater:
    """记忆更新模块 - 动态更新管理"""

    def __init__(self, storage: MemoryStorage, config: Dict = None):
        self.storage = storage
        self.config = config or {}
        self.short_to_mid_threshold = self.config.get("short_to_mid_threshold", 5)  # 对话链阈值
        self.mid_to_long_threshold = self.config.get("mid_to_long_threshold", 3)  # 巩固次数阈值
        self.decay_rate = self.config.get("decay_rate", 0.01)  # 衰减率

    def update_short_to_mid(self, dialog_chain: DialogChain) -> List[MemoryUnit]:
        """短期→中期更新：基于对话链的FIFO原则"""
        mid_units = []

        # 提取对话关键点
        summary = dialog_chain.summary or self._extract_summary(dialog_chain.messages)
        key_points = dialog_chain.key_points or self._extract_key_points(dialog_chain.messages)

        # 创建中期记忆单元
        for i, point in enumerate(key_points):
            unit = MemoryUnit(
                id=f"mid_{dialog_chain.session_id}_{i}",
                level=MemoryLevel.MID_TERM,
                content=point,
                metadata={
                    "session_id": dialog_chain.session_id,
                    "summary": summary,
                    "source": "dialog_chain"
                },
                tags=["conversation", "key_point"],
                importance=0.6
            )
            self.storage.store(unit)
            mid_units.append(unit)

        # 创建对话摘要记忆
        if summary:
            summary_unit = MemoryUnit(
                id=f"mid_{dialog_chain.session_id}_summary",
                level=MemoryLevel.MID_TERM,
                content=summary,
                metadata={
                    "session_id": dialog_chain.session_id,
                    "source": "dialog_summary"
                },
                tags=["conversation", "summary"],
                importance=0.7
            )
            self.storage.store(summary_unit)
            mid_units.append(summary_unit)

        return mid_units

    def update_mid_to_long(self, mid_units: List[MemoryUnit]) -> List[MemoryUnit]:
        """中期→长期更新：分段页组织策略"""
        long_units = []

        for unit in mid_units:
            # 重要性超过阈值的升级为长期记忆
            if unit.importance >= 0.6:
                long_unit = MemoryUnit(
                    id=f"long_{unit.id}",
                    level=MemoryLevel.LONG_TERM,
                    content=unit.content,
                    metadata={
                        **unit.metadata,
                        "promoted_from": unit.id.value,
                        "promotion_time": time.time()
                    },
                    tags=unit.tags + ["long_term"],
                    importance=unit.importance + 0.1  # 提升重要性
                )
                long_unit.importance = min(1.0, long_unit.importance)
                self.storage.store(long_unit)
                long_units.append(long_unit)

        return long_units

    def apply_decay(self, hours: float = 1.0):
        """应用记忆衰减"""
        cursor = self.storage.conn.cursor()
        cursor.execute("""
            UPDATE memories
            SET importance = MAX(0.1, importance - ? * ?),
                updated_at = ?
            WHERE level IN (?, ?)
        """, (self.decay_rate, hours, time.time(),
              MemoryLevel.SHORT_TERM.value, MemoryLevel.MID_TERM.value))
        self.storage.conn.commit()

    def merge_similar(self, threshold: float = 0.8):
        """合并相似记忆"""
        # 简单实现：基于内容重叠合并
        cursor = self.storage.conn.cursor()
        cursor.execute("SELECT id, content, level FROM memories ORDER BY importance DESC")
        memories = cursor.fetchall()

        merged = set()
        for i, m1 in enumerate(memories):
            if m1["id"] in merged:
                continue
            for m2 in memories[i+1:]:
                if m2["id"] in merged:
                    continue
                # 计算内容重叠
                words1 = set(m1["content"].lower().split())
                words2 = set(m2["content"].lower().split())
                if not words1 or not words2:
                    continue
                overlap = len(words1 & words2) / max(len(words1), len(words2))
                if overlap >= threshold:
                    # 合并到重要性更高的
                    cursor.execute("""
                        UPDATE memories
                        SET content = content || '\n---\n' || ?,
                            importance = MAX(importance, ?),
                            updated_at = ?
                        WHERE id = ?
                    """, (m2["content"], m1["importance"] if m1["importance"] > m2["importance"] else m2["importance"],
                          time.time(), m1["id"]))
                    cursor.execute("DELETE FROM memories WHERE id = ?", (m2["id"],))
                    merged.add(m2["id"])

        if merged:
            self.storage.conn.commit()

    def _extract_summary(self, messages: List[Dict]) -> str:
        """提取对话摘要"""
        if not messages:
            return ""
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if user_msgs:
            return f"对话包含 {len(user_msgs)} 轮交互"
        return ""

    def _extract_key_points(self, messages: List[Dict]) -> List[str]:
        """提取对话关键点"""
        points = []
        for msg in messages:
            if msg.get("role") == "user" and len(msg.get("content", "")) > 20:
                points.append(msg["content"][:100])
        return points


class MemoryRetriever:
    """记忆检索模块 - 自适应检索"""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def retrieve_relevant(self, query: str, levels: List[MemoryLevel] = None,
                         limit: int = 5) -> List[MemoryUnit]:
        """
        检索相关记忆

        策略：
        1. 短期记忆优先
        2. 按重要性排序
        3. 标签匹配增强
        """
        levels = levels or [MemoryLevel.SHORT_TERM, MemoryLevel.MID_TERM, MemoryLevel.LONG_TERM]

        results = []
        for level in levels:
            if level == MemoryLevel.SHORT_TERM:
                # 短期记忆从缓存检索
                for unit in self.storage.short_term_cache.values():
                    if query.lower() in unit.content.lower():
                        results.append(unit)
            else:
                # 中长期从数据库检索
                units = self.storage.search_by_level(level, limit)
                for unit in units:
                    if query.lower() in unit.content.lower():
                        results.append(unit)

            if len(results) >= limit:
                break

        # 按重要性排序
        results.sort(key=lambda u: u.importance, reverse=True)
        return results[:limit]

    def retrieve_by_context(self, context: Dict, limit: int = 5) -> List[MemoryUnit]:
        """按上下文检索"""
        tags = context.get("tags", [])
        if tags:
            return self.storage.search_by_tags(tags, limit)
        return []

    def retrieve_recent(self, limit: int = 10) -> List[MemoryUnit]:
        """检索最近记忆"""
        cursor = self.storage.conn.cursor()
        cursor.execute("""
            SELECT * FROM memories ORDER BY created_at DESC LIMIT ?
        """, (limit,))

        units = []
        for row in cursor.fetchall():
            units.append(MemoryUnit(
                id=row["id"],
                level=MemoryLevel(row["level"]),
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                access_count=row["access_count"],
                importance=row["importance"],
                tags=json.loads(row["tags"]),
                links=json.loads(row["links"])
            ))
        return units


class MemoryGenerator:
    """记忆生成模块 - 上下文生成"""

    def __init__(self, retriever: MemoryRetriever):
        self.retriever = retriever

    def generate_context(self, query: str, max_tokens: int = 1000) -> str:
        """生成记忆上下文"""
        relevant = self.retriever.retrieve_relevant(query, limit=5)
        if not relevant:
            return ""

        context_parts = []
        for unit in relevant:
            level_name = {
                MemoryLevel.SHORT_TERM: "短期",
                MemoryLevel.MID_TERM: "中期",
                MemoryLevel.LONG_TERM: "长期"
            }.get(unit.level, "未知")

            context_parts.append(
                f"[{level_name}记忆] (重要性: {unit.importance:.2f})\n{unit.content}"
            )

        return "\n---\n".join(context_parts)

    def generate_memory_summary(self, units: List[MemoryUnit]) -> str:
        """生成记忆摘要"""
        if not units:
            return "无记忆"

        summary_parts = []
        by_level = {}
        for unit in units:
            if unit.level not in by_level:
                by_level[unit.level] = []
            by_level[unit.level].append(unit)

        for level, level_units in by_level.items():
            level_name = {
                MemoryLevel.SHORT_TERM: "短期",
                MemoryLevel.MID_TERM: "中期",
                MemoryLevel.LONG_TERM: "长期"
            }.get(level, "未知")
            summary_parts.append(f"{level_name}记忆: {len(level_units)}条")

        return " | ".join(summary_parts)


class MemoryOS:
    """记忆操作系统 - 统一记忆管理框架"""

    def __init__(self, db_path: str = "data/memory_os.db", config: Dict = None):
        self.config = config or {}
        self.storage = MemoryStorage(db_path)
        self.updater = MemoryUpdater(self.storage, self.config)
        self.retriever = MemoryRetriever(self.storage)
        self.generator = MemoryGenerator(self.retriever)

    def add_short_term(self, content: str, metadata: Dict = None, tags: List[str] = None) -> MemoryUnit:
        """添加短期记忆"""
        import uuid
        unit = MemoryUnit(
            id=f"st_{uuid.uuid4().hex[:8]}",
            level=MemoryLevel.SHORT_TERM,
            content=content,
            metadata=metadata or {},
            tags=tags or []
        )
        self.storage.store(unit)
        return unit

    def add_mid_term(self, content: str, importance: float = 0.6, metadata: Dict = None, tags: List[str] = None) -> MemoryUnit:
        """添加中期记忆"""
        import uuid
        unit = MemoryUnit(
            id=f"mt_{uuid.uuid4().hex[:8]}",
            level=MemoryLevel.MID_TERM,
            content=content,
            metadata=metadata or {},
            tags=tags or [],
            importance=importance
        )
        self.storage.store(unit)
        return unit

    def promote_to_mid(self, dialog_chain: DialogChain) -> List[MemoryUnit]:
        """提升短期到中期"""
        return self.updater.update_short_to_mid(dialog_chain)

    def promote_to_long(self, mid_units: List[MemoryUnit]) -> List[MemoryUnit]:
        """提升中期到长期"""
        return self.updater.update_mid_to_long(mid_units)

    def query(self, query_text: str, limit: int = 5) -> List[MemoryUnit]:
        """查询相关记忆"""
        return self.retriever.retrieve_relevant(query_text, limit=limit)

    def get_context(self, query: str) -> str:
        """获取记忆上下文"""
        return self.generator.generate_context(query)

    def get_stats(self) -> Dict:
        """获取系统统计"""
        return self.storage.get_stats()

    def run_maintenance(self):
        """运行维护任务"""
        self.updater.apply_decay(hours=1.0)
        self.updater.merge_similar(threshold=0.8)

    def close(self):
        self.storage.close()
