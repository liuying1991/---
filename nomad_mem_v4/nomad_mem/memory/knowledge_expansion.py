"""
Knowledge Expander - 知识扩展模块

从对话中自动提取事实并扩展知识图谱 —— 像Jarvis从与Tony Stark的对话中学习新事实。

核心能力:
1. 事实提取：从对话中抽取结构化事实（X是Y、X有Y、X能Y等模式）
2. 候选管理：提取的事实作为候选待审核，审核后成为真正知识
3. 知识审核：保守策略，候选必须经过验证才能进入知识图谱
4. 自动扩展：将已验证的候选自动加入知识图谱
5. 来源追溯：每个事实都记录来源消息，可追溯

设计原则:
- 保守：候选必须验证后才能成为真正知识
- 简单模式匹配提取事实
- 来源可追溯
- 基于提取模式可靠性的置信度评分
- 第一性原理：真正的学习意味着从非结构化对话中提取结构化知识
"""
import re
import uuid
import time
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

from nomad_mem.memory.knowledge_graph import (
    KnowledgeGraph, EntityType, RelationType, Entity,
)


@dataclass
class ExtractedFact:
    """提取的事实"""
    fact_id: str
    subject: str          # 主体（如 "Python"）
    predicate: str        # 谓词（如 "is"）
    object_: str          # 客体（如 "a programming language"）
    confidence: float     # 置信度 [0, 1]
    source_message: str   # 来源消息
    timestamp: float      # 时间戳
    verified: bool = False  # 是否已验证


@dataclass
class KnowledgeCandidate:
    """知识候选"""
    candidate_id: str
    entity_name: str          # 实体名称
    entity_type: str          # 实体类型字符串
    description: str          # 描述
    relations: List[Dict]     # 关系列表 [{"target": "...", "type": "...", "weight": 1.0}]
    source: str               # 来源
    confidence: float         # 置信度


# 事实提取模式：(正则, 谓词映射, 基础置信度)
EXTRACTION_PATTERNS: List[Tuple[str, str, float]] = [
    # "X is a Y" / "X is an Y" / "X is the Y"
    (r'\b(\w[\w\s]*?)\s+is\s+(?:a|an|the)\s+([\w\s]+?)\s*$', 'is_a', 0.85),
    # "X is Y" (直接描述)
    (r'\b(\w[\w\s]*?)\s+is\s+([\w\s]+?)\s*$', 'is', 0.70),
    # "X has Y"
    (r'\b(\w[\w\s]*?)\s+has\s+(?:a|an|the\s+)?([\w\s]+?)\s*$', 'has', 0.75),
    # "X can Y"
    (r'\b(\w[\w\s]*?)\s+can\s+([\w\s]+?)\s*$', 'can', 0.70),
    # "X was created by Y"
    (r'\b(\w[\w\s]*?)\s+was\s+created\s+by\s+([\w\s]+?)\s*$', 'created_by', 0.90),
    # "X is used for Y" / "X is used to Y"
    (r'\b(\w[\w\s]*?)\s+is\s+used\s+(?:for|to)\s+([\w\s]+?)\s*$', 'used_for', 0.80),
    # "X is part of Y" / "X is a part of Y"
    (r'\b(\w[\w\s]*?)\s+is\s+(?:a\s+)?part\s+of\s+([\w\s]+?)\s*$', 'part_of', 0.85),
    # "X is located in Y" / "X is in Y" (地点)
    (r'\b(\w[\w\s]*?)\s+is\s+(?:located\s+)?in\s+([\w\s]+?)\s*$', 'located_in', 0.65),
    # "X is related to Y" / "X is associated with Y"
    (r'\b(\w[\w\s]*?)\s+is\s+(?:related|associated)\s+(?:to|with)\s+([\w\s]+?)\s*$', 'related_to', 0.65),
    # "X knows Y" / "X learned Y"
    (r'\b(\w[\w\s]*?)\s+(?:knows|learned)\s+([\w\s]+?)\s*$', 'knows', 0.70),
    # "X is a type of Y"
    (r'\b(\w[\w\s]*?)\s+is\s+a\s+type\s+of\s+([\w\s]+?)\s*$', 'is_a', 0.90),
    # "X is a kind of Y"
    (r'\b(\w[\w\s]*?)\s+is\s+a\s+kind\s+of\s+([\w\s]+?)\s*$', 'is_a', 0.85),
    # "X was born in Y"
    (r'\b(\w[\w\s]*?)\s+was\s+born\s+in\s+([\w\s]+?)\s*$', 'located_in', 0.85),
    # "X works at Y" / "X works for Y"
    (r'\b(\w[\w\s]*?)\s+works\s+(?:at|for)\s+([\w\s]+?)\s*$', 'related_to', 0.75),
    # "X belongs to Y"
    (r'\b(\w[\w\s]*?)\s+belongs\s+to\s+([\w\s]+?)\s*$', 'part_of', 0.80),
    # "X has the ability to Y"
    (r'\b(\w[\w\s]*?)\s+has\s+the\s+ability\s+to\s+([\w\s]+?)\s*$', 'can', 0.80),
    # "X is capable of Y"
    (r'\b(\w[\w\s]*?)\s+is\s+capable\s+of\s+([\w\s]+?)\s*$', 'can', 0.75),
    # "X is known for Y"
    (r'\b(\w[\w\s]*?)\s+is\s+known\s+for\s+([\w\s]+?)\s*$', 'has_property', 0.70),
    # "X is responsible for Y"
    (r'\b(\w[\w\s]*?)\s+is\s+responsible\s+for\s+([\w\s]+?)\s*$', 'has_property', 0.75),
    # "X is based in Y"
    (r'\b(\w[\w\s]*?)\s+is\s+based\s+in\s+([\w\s]+?)\s*$', 'located_in', 0.80),
]

# 否定模式（检测到否定时降低置信度或标记为未验证）
NEGATION_PATTERNS: List[str] = [
    r'\b(is\s+)?not\b',
    r"\b(is\s+)?n't\b",
    r'\bnever\b',
    r'\bno\s+\w+\b',
    r'\bwithout\b',
    r'\bcannot\b',
    r"\bcan't\b",
    r'\bdon\'t\b',
    r'\bdoesn\'t\b',
    r'\bdidn\'t\b',
    r'\bwon\'t\b',
    r'\bwouldn\'t\b',
]


class KnowledgeExpander:
    """知识扩展器"""

    def __init__(self, db_path: str = "data/knowledge_expansion.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """初始化数据库表结构"""
        cursor = self.conn.cursor()

        # 提取的事实表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_facts (
                fact_id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                source_message TEXT DEFAULT '',
                timestamp REAL,
                verified INTEGER DEFAULT 0
            )
        """)

        # 知识候选表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_candidates (
                candidate_id TEXT PRIMARY KEY,
                entity_name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                description TEXT DEFAULT '',
                relations TEXT DEFAULT '[]',
                source TEXT DEFAULT '',
                confidence REAL DEFAULT 0.5,
                status TEXT DEFAULT 'pending',  -- pending, verified, rejected
                reject_reason TEXT DEFAULT '',
                created_at REAL,
                verified_at REAL
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_subject ON extracted_facts(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_predicate ON extracted_facts(predicate)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_verified ON extracted_facts(verified)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_status ON knowledge_candidates(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_entity ON knowledge_candidates(entity_name)")

        self.conn.commit()

    def extract_facts(self, message: str, response: str = "") -> List[ExtractedFact]:
        """
        从对话中提取事实

        使用简单模式匹配从消息和回复中抽取结构化事实。
        检测否定模式，否定事实会降低置信度。

        Args:
            message: 用户消息
            response: 系统回复（可选，也用于提取）

        Returns:
            提取的事实列表
        """
        facts = []
        texts = [message]
        if response:
            texts.append(response)

        for text in texts:
            # 按句号分割成句子
            sentences = re.split(r'[.!?;]\s*', text)

            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 5:
                    continue

                is_negated = self._is_negated(sentence)

                for pattern, predicate, base_confidence in EXTRACTION_PATTERNS:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        subject = match.group(1).strip()
                        object_val = match.group(2).strip()

                        # 过滤太短的提取
                        if len(subject) < 2 or len(object_val) < 2:
                            continue

                        # 置信度调整
                        confidence = base_confidence
                        if is_negated:
                            confidence *= 0.3  # 否定大幅降低置信度

                        # 模式可靠性加权：越具体的模式置信度越高
                        specificity_bonus = len(pattern.split()) * 0.02
                        confidence = min(1.0, confidence + specificity_bonus)

                        fact_id = f"fact_{uuid.uuid4().hex[:8]}"
                        fact = ExtractedFact(
                            fact_id=fact_id,
                            subject=subject,
                            predicate=predicate,
                            object_=object_val,
                            confidence=round(confidence, 3),
                            source_message=sentence,
                            timestamp=time.time(),
                            verified=False,
                        )
                        facts.append(fact)
                        self._save_fact(fact)
                        break  # 每个句子只匹配一个模式

        return facts

    def _is_negated(self, text: str) -> bool:
        """检测文本是否包含否定"""
        for neg_pattern in NEGATION_PATTERNS:
            if re.search(neg_pattern, text, re.IGNORECASE):
                return True
        return False

    def _save_fact(self, fact: ExtractedFact):
        """保存事实到数据库"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO extracted_facts
            (fact_id, subject, predicate, object, confidence, source_message, timestamp, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fact.fact_id, fact.subject, fact.predicate, fact.object_,
            fact.confidence, fact.source_message, fact.timestamp,
            1 if fact.verified else 0,
        ))
        self.conn.commit()

    def add_candidate(self, candidate: KnowledgeCandidate) -> str:
        """
        添加知识候选待审核

        Args:
            candidate: 知识候选对象

        Returns:
            候选ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_candidates
            (candidate_id, entity_name, entity_type, description, relations, source, confidence, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            candidate.candidate_id,
            candidate.entity_name,
            candidate.entity_type,
            candidate.description,
            json.dumps(candidate.relations),
            candidate.source,
            candidate.confidence,
            time.time(),
        ))
        self.conn.commit()
        return candidate.candidate_id

    def verify_candidate(self, candidate_id: str, verified: bool = True) -> bool:
        """
        标记候选为已验证（成为真正知识）

        Args:
            candidate_id: 候选ID
            verified: 是否验证通过

        Returns:
            是否操作成功
        """
        cursor = self.conn.cursor()

        if verified:
            cursor.execute("""
                UPDATE knowledge_candidates
                SET status = 'verified', verified_at = ?
                WHERE candidate_id = ? AND status = 'pending'
            """, (time.time(), candidate_id))
        else:
            cursor.execute("""
                UPDATE knowledge_candidates
                SET status = 'rejected', verified_at = ?
                WHERE candidate_id = ? AND status = 'pending'
            """, (time.time(), candidate_id))

        self.conn.commit()
        return cursor.rowcount > 0

    def reject_candidate(self, candidate_id: str, reason: str = ""):
        """
        拒绝候选

        Args:
            candidate_id: 候选ID
            reason: 拒绝原因
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE knowledge_candidates
            SET status = 'rejected', reject_reason = ?, verified_at = ?
            WHERE candidate_id = ? AND status = 'pending'
        """, (reason, time.time(), candidate_id))
        self.conn.commit()

    def get_pending_candidates(self, limit: int = 20) -> List[KnowledgeCandidate]:
        """
        获取待审核的候选

        Args:
            limit: 返回数量上限

        Returns:
            候选列表（按置信度降序）
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM knowledge_candidates
            WHERE status = 'pending'
            ORDER BY confidence DESC
            LIMIT ?
        """, (limit,))

        candidates = []
        for row in cursor.fetchall():
            candidates.append(KnowledgeCandidate(
                candidate_id=row["candidate_id"],
                entity_name=row["entity_name"],
                entity_type=row["entity_type"],
                description=row["description"],
                relations=json.loads(row["relations"]),
                source=row["source"],
                confidence=row["confidence"],
            ))
        return candidates

    def get_verified_facts(self, subject: str, limit: int = 10) -> List[ExtractedFact]:
        """
        获取关于某主体的已验证事实

        Args:
            subject: 主体名称
            limit: 返回数量上限

        Returns:
            已验证事实列表（按置信度降序）
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM extracted_facts
            WHERE subject LIKE ? AND verified = 1
            ORDER BY confidence DESC
            LIMIT ?
        """, (f"%{subject}%", limit))

        facts = []
        for row in cursor.fetchall():
            facts.append(ExtractedFact(
                fact_id=row["fact_id"],
                subject=row["subject"],
                predicate=row["predicate"],
                object_=row["object"],
                confidence=row["confidence"],
                source_message=row["source_message"],
                timestamp=row["timestamp"],
                verified=True,
            ))
        return facts

    def auto_expand(self, knowledge_graph: KnowledgeGraph) -> int:
        """
        自动将已验证候选扩展到知识图谱

        将状态为 verified 的候选转换为知识图谱中的实体和关系。
        只处理尚未扩展的 verified 候选。

        Args:
            knowledge_graph: 知识图谱实例

        Returns:
            添加的实体数量
        """
        cursor = self.conn.cursor()

        # 获取所有已验证但未扩展的候选
        cursor.execute("""
            SELECT * FROM knowledge_candidates
            WHERE status = 'verified'
        """)

        added_count = 0
        for row in cursor.fetchall():
            candidate = KnowledgeCandidate(
                candidate_id=row["candidate_id"],
                entity_name=row["entity_name"],
                entity_type=row["entity_type"],
                description=row["description"],
                relations=json.loads(row["relations"]),
                source=row["source"],
                confidence=row["confidence"],
            )

            # 将候选加入知识图谱
            entity_id = self._add_to_graph(knowledge_graph, candidate)
            if entity_id:
                added_count += 1

        return added_count

    def _add_to_graph(self, knowledge_graph: KnowledgeGraph, candidate: KnowledgeCandidate) -> Optional[str]:
        """
        将候选添加到知识图谱

        Args:
            knowledge_graph: 知识图谱实例
            candidate: 知识候选

        Returns:
            实体ID，如果添加失败返回 None
        """
        try:
            # 将字符串类型映射到 EntityType
            entity_type = self._map_entity_type(candidate.entity_type)
            entity_id = f"ent_{uuid.uuid4().hex[:8]}"

            # 添加实体
            knowledge_graph.add_entity(
                entity_id=entity_id,
                name=candidate.entity_name,
                entity_type=entity_type,
                description=candidate.description,
                properties={"source": candidate.source, "confidence": candidate.confidence},
            )

            # 添加关系
            for rel in candidate.relations:
                target_name = rel.get("target", "")
                rel_type_str = rel.get("type", "related_to")

                # 查找或创建目标实体
                target_entities = knowledge_graph.search_entities(target_name)
                if target_entities:
                    target_id = target_entities[0].entity_id
                else:
                    target_id = f"ent_{uuid.uuid4().hex[:8]}"
                    knowledge_graph.add_entity(
                        entity_id=target_id,
                        name=target_name,
                        entity_type=EntityType.CONCEPT,
                        description=f"Auto-created from relation: {target_name}",
                    )

                rel_type = self._map_relation_type(rel_type_str)
                knowledge_graph.add_relation(
                    source_id=entity_id,
                    target_id=target_id,
                    relation_type=rel_type,
                    weight=rel.get("weight", 1.0),
                    description=f"From candidate: {candidate.candidate_id}",
                )

            return entity_id

        except Exception:
            return None

    def _map_entity_type(self, type_str: str) -> EntityType:
        """将字符串映射到 EntityType"""
        type_map = {
            "concept": EntityType.CONCEPT,
            "person": EntityType.PERSON,
            "object": EntityType.OBJECT,
            "event": EntityType.EVENT,
            "place": EntityType.PLACE,
            "organization": EntityType.ORGANIZATION,
            "skill": EntityType.SKILL,
            "topic": EntityType.TOPIC,
        }
        return type_map.get(type_str.lower(), EntityType.CONCEPT)

    def _map_relation_type(self, type_str: str) -> RelationType:
        """将字符串映射到 RelationType"""
        type_map = {
            "is_a": RelationType.IS_A,
            "has_property": RelationType.HAS_PROPERTY,
            "related_to": RelationType.RELATED_TO,
            "part_of": RelationType.PART_OF,
            "used_for": RelationType.USED_FOR,
            "created_by": RelationType.CREATED_BY,
            "located_in": RelationType.LOCATED_IN,
            "knows": RelationType.KNOWS,
        }
        return type_map.get(type_str.lower(), RelationType.RELATED_TO)

    def get_expansion_stats(self) -> Dict[str, Any]:
        """
        获取扩展统计信息

        Returns:
            包含各项统计的字典
        """
        cursor = self.conn.cursor()

        # 总事实数
        cursor.execute("SELECT COUNT(*) as count FROM extracted_facts")
        total_facts = cursor.fetchone()["count"]

        # 已验证事实数
        cursor.execute("SELECT COUNT(*) as count FROM extracted_facts WHERE verified = 1")
        verified_facts = cursor.fetchone()["count"]

        # 候选状态统计
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM knowledge_candidates GROUP BY status
        """)
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        pending = status_counts.get("verified", 0)  # verified candidates not yet expanded
        rejected = status_counts.get("rejected", 0)

        return {
            "total_facts": total_facts,
            "verified_facts": verified_facts,
            "pending_candidates": pending,
            "rejected_candidates": rejected,
            "total_candidates": sum(status_counts.values()),
        }

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
