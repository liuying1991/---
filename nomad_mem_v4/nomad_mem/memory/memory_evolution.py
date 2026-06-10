"""
Memory Evolution - 记忆进化系统

参考论文：A-Mem: Agentic Memory for LLM Agents (2025)

核心机制：
- 动态索引：新记忆添加时生成综合笔记（上下文、关键词、标签）
- 链接生成：分析历史记忆，建立有意义的连接
- 记忆进化：新记忆触发历史记忆的更新和精炼
"""
import time
import json
import sqlite3
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class MemoryNote:
    """记忆笔记 - A-Mem风格的综合记忆表示"""
    id: str
    content: str
    context: str  # 上下文描述
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    links: List[Dict] = field(default_factory=list)  # [{"target_id": "...", "relation": "...", "strength": 0.5}]
    evolution_count: int = 0  # 进化次数


class MemoryEvolution:
    """记忆进化系统"""

    def __init__(self, db_path: str = "data/memory_evolution.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self.notes_cache: Dict[str, MemoryNote] = {}

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_notes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                context TEXT DEFAULT '',
                keywords TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                created_at REAL,
                updated_at REAL,
                links TEXT DEFAULT '[]',
                evolution_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts4(
                content, context, keywords, tags
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_updated ON memory_notes(updated_at)")
        self.conn.commit()

    def create_note(self, content: str, context: str = "", keywords: List[str] = None,
                   tags: List[str] = None) -> MemoryNote:
        """
        创建记忆笔记

        Args:
            content: 笔记内容
            context: 上下文描述
            keywords: 关键词列表
            tags: 标签列表

        Returns:
            创建的笔记对象
        """
        import uuid
        note_id = f"note_{uuid.uuid4().hex[:8]}"

        note = MemoryNote(
            id=note_id,
            content=content,
            context=context,
            keywords=keywords or self._extract_keywords(content),
            tags=tags or [],
            links=[]
        )

        self._save_note(note)
        return note

    def generate_links(self, note_id: str, min_strength: float = 0.3) -> List[Dict]:
        """
        为新笔记生成链接

        分析历史笔记，找到有意义的连接

        Args:
            note_id: 新笔记ID
            min_strength: 最小链接强度阈值

        Returns:
            链接列表
        """
        note = self._load_note(note_id)
        if not note:
            return []

        links = []
        all_notes = self.get_all_notes()

        for other in all_notes:
            if other.id == note_id:
                continue

            # 计算链接强度
            strength = self._calculate_link_strength(note, other)
            if strength >= min_strength:
                # 确定关系类型
                relation = self._determine_relation(note, other)
                links.append({
                    "target_id": other.id,
                    "relation": relation,
                    "strength": strength,
                    "created_at": time.time()
                })

                # 反向链接
                self._add_reverse_link(other.id, note_id, relation, strength)

        # 保存链接
        if links:
            note.links = links
            self._save_note(note)

        return links

    def evolve_memory(self, new_note: MemoryNote) -> List[str]:
        """
        记忆进化：新笔记触发历史笔记的更新

        Args:
            new_note: 新添加的笔记

        Returns:
            被更新的笔记ID列表
        """
        updated_ids = []

        # 查找相关笔记
        related = self._find_related_notes(new_note)
        for related_note in related:
            # 检查是否需要更新
            if self._should_evolve(related_note, new_note):
                # 执行进化
                updated = self._perform_evolution(related_note, new_note)
                if updated:
                    self._save_note(related_note)
                    updated_ids.append(related_note.id)

        return updated_ids

    def merge_notes(self, note1_id: str, note2_id: str) -> Optional[MemoryNote]:
        """
        合并两个笔记

        Args:
            note1_id: 第一个笔记ID
            note2_id: 第二个笔记ID

        Returns:
            合并后的笔记，失败返回None
        """
        note1 = self._load_note(note1_id)
        note2 = self._load_note(note2_id)

        if not note1 or not note2:
            return None

        # 合并内容
        merged_content = f"{note1.content}\n\n与{note2.content}相关联"
        merged_keywords = list(set(note1.keywords + note2.keywords))
        merged_tags = list(set(note1.tags + note2.tags))
        merged_links = note1.links + note2.links

        # 创建合并笔记
        import uuid
        merged_note = MemoryNote(
            id=f"merged_{uuid.uuid4().hex[:8]}",
            content=merged_content,
            context=note1.context or note2.context,
            keywords=merged_keywords,
            tags=merged_tags,
            links=merged_links,
            evolution_count=max(note1.evolution_count, note2.evolution_count) + 1
        )

        self._save_note(merged_note)

        # 删除原笔记
        self.delete_note(note1_id)
        self.delete_note(note2_id)

        return merged_note

    def refine_note(self, note_id: str, new_info: str) -> bool:
        """
        精炼笔记：添加新信息并更新

        Args:
            note_id: 笔记ID
            new_info: 新信息

        Returns:
            是否成功
        """
        note = self._load_note(note_id)
        if not note:
            return False

        # 更新内容
        note.content = f"{note.content}\n更新: {new_info}"
        note.updated_at = time.time()
        note.evolution_count += 1

        # 更新关键词
        new_keywords = self._extract_keywords(new_info)
        note.keywords = list(set(note.keywords + new_keywords))

        self._save_note(note)
        return True

    def get_all_notes(self, limit: int = 100) -> List[MemoryNote]:
        """获取所有笔记"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM memory_notes ORDER BY updated_at DESC LIMIT ?
        """, (limit,))

        notes = []
        for row in cursor.fetchall():
            notes.append(MemoryNote(
                id=row["id"],
                content=row["content"],
                context=row["context"],
                keywords=json.loads(row["keywords"]),
                tags=json.loads(row["tags"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                links=json.loads(row["links"]),
                evolution_count=row["evolution_count"]
            ))
        return notes

    def search_notes(self, query: str, limit: int = 10) -> List[MemoryNote]:
        """搜索笔记 - 使用LIKE进行全文搜索"""
        cursor = self.conn.cursor()
        # 使用LIKE搜索内容、上下文和关键词
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM memory_notes
            WHERE content LIKE ? OR context LIKE ? OR keywords LIKE ?
            ORDER BY updated_at DESC
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, limit))

        notes = []
        for row in cursor.fetchall():
            notes.append(MemoryNote(
                id=row["id"],
                content=row["content"],
                context=row["context"],
                keywords=json.loads(row["keywords"]),
                tags=json.loads(row["tags"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                links=json.loads(row["links"]),
                evolution_count=row["evolution_count"]
            ))
        return notes

    def get_linked_notes(self, note_id: str, min_strength: float = 0.3) -> List[Tuple[MemoryNote, float]]:
        """获取关联笔记"""
        note = self._load_note(note_id)
        if not note:
            return []

        linked = []
        for link in note.links:
            if link["strength"] >= min_strength:
                target = self._load_note(link["target_id"])
                if target:
                    linked.append((target, link["strength"]))

        return linked

    def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memory_notes WHERE id = ?", (note_id,))
        self.conn.commit()
        if note_id in self.notes_cache:
            del self.notes_cache[note_id]
        return cursor.rowcount > 0

    def _save_note(self, note: MemoryNote):
        """保存笔记到数据库"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memory_notes
            (id, content, context, keywords, tags, created_at, updated_at, links, evolution_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            note.id, note.content, note.context,
            json.dumps(note.keywords), json.dumps(note.tags),
            note.created_at, note.updated_at,
            json.dumps(note.links), note.evolution_count
        ))
        self.conn.commit()
        self.notes_cache[note.id] = note

        # 同步到FTS表
        cursor.execute("DELETE FROM notes_fts WHERE docid = (SELECT rowid FROM memory_notes WHERE id = ?)", (note.id,))
        cursor.execute("""
            INSERT INTO notes_fts(docid, content, context, keywords, tags)
            SELECT rowid, content, context, keywords, tags FROM memory_notes WHERE id = ?
        """, (note.id,))
        self.conn.commit()

    def _load_note(self, note_id: str) -> Optional[MemoryNote]:
        """加载笔记"""
        if note_id in self.notes_cache:
            return self.notes_cache[note_id]

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memory_notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        if not row:
            return None

        note = MemoryNote(
            id=row["id"],
            content=row["content"],
            context=row["context"],
            keywords=json.loads(row["keywords"]),
            tags=json.loads(row["tags"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            links=json.loads(row["links"]),
            evolution_count=row["evolution_count"]
        )
        self.notes_cache[note_id] = note
        return note

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现）"""
        # 分词并过滤常见词
        common_words = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        words = text.lower().split()
        return [w for w in words if len(w) > 1 and w not in common_words][:10]

    def _calculate_link_strength(self, note1: MemoryNote, note2: MemoryNote) -> float:
        """计算链接强度"""
        # 基于关键词重叠和标签重叠
        keywords1 = set(note1.keywords)
        keywords2 = set(note2.keywords)
        tags1 = set(note1.tags)
        tags2 = set(note2.tags)

        if not keywords1 or not keywords2:
            return 0.0

        keyword_overlap = len(keywords1 & keywords2) / max(len(keywords1 | keywords2), 1)
        tag_overlap = len(tags1 & tags2) / max(len(tags1 | tags2), 1) if (tags1 or tags2) else 0.0

        # 内容相似度（简单词重叠）
        words1 = set(note1.content.lower().split())
        words2 = set(note2.content.lower().split())
        content_similarity = len(words1 & words2) / max(len(words1 | words2), 1)

        return 0.4 * keyword_overlap + 0.3 * tag_overlap + 0.3 * content_similarity

    def _determine_relation(self, note1: MemoryNote, note2: MemoryNote) -> str:
        """确定关系类型"""
        common_keywords = set(note1.keywords) & set(note2.keywords)
        if common_keywords:
            return f"关键词关联({', '.join(list(common_keywords)[:2])})"

        common_tags = set(note1.tags) & set(note2.tags)
        if common_tags:
            return f"标签关联({', '.join(list(common_tags)[:2])})"

        return "内容关联"

    def _add_reverse_link(self, from_id: str, to_id: str, relation: str, strength: float):
        """添加反向链接"""
        note = self._load_note(from_id)
        if note:
            note.links.append({
                "target_id": to_id,
                "relation": relation,
                "strength": strength,
                "created_at": time.time()
            })
            self._save_note(note)

    def _find_related_notes(self, new_note: MemoryNote) -> List[MemoryNote]:
        """查找相关笔记"""
        all_notes = self.get_all_notes()
        related = []
        for note in all_notes:
            if note.id == new_note.id:
                continue
            strength = self._calculate_link_strength(new_note, note)
            if strength > 0.2:
                related.append(note)
        return related

    def _should_evolve(self, existing: MemoryNote, new: MemoryNote) -> bool:
        """检查是否应该进化"""
        # 如果内容高度相似，应该合并/更新
        strength = self._calculate_link_strength(existing, new)
        return strength > 0.4 and existing.evolution_count < 5

    def _perform_evolution(self, existing: MemoryNote, new: MemoryNote) -> bool:
        """执行记忆进化"""
        # 更新上下文
        if new.context and new.context not in existing.context:
            existing.context = f"{existing.context}\n与新信息关联: {new.context[:100]}"

        # 添加新关键词
        existing.keywords = list(set(existing.keywords + new.keywords))

        # 更新时间戳和进化计数
        existing.updated_at = time.time()
        existing.evolution_count += 1

        return True

    def get_stats(self) -> Dict:
        """获取统计信息"""
        notes = self.get_all_notes()
        total_links = sum(len(n.links) for n in notes)
        avg_evolution = sum(n.evolution_count for n in notes) / max(len(notes), 1)

        return {
            "total_notes": len(notes),
            "total_links": total_links,
            "avg_evolution_count": avg_evolution,
            "notes_with_links": sum(1 for n in notes if n.links)
        }

    def close(self):
        self.conn.close()
