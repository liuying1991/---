"""
Knowledge Graph - 知识图谱系统

核心能力:
1. 实体管理：创建/查询/更新实体
2. 关系网络：实体间关系的存储和查询
3. 概念图谱：概念层次结构和继承关系
4. 语义推理：基于规则的简单推理
5. 路径发现：发现实体间的关联路径

参考:
- RDF/OWL语义网标准
- 图数据库设计(Neo4j)
- 知识图谱推理技术
"""
import time
import json
import sqlite3
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class EntityType(Enum):
    """实体类型"""
    CONCEPT = "concept"           # 概念
    PERSON = "person"            # 人物
    OBJECT = "object"            # 物体
    EVENT = "event"              # 事件
    PLACE = "place"              # 地点
    ORGANIZATION = "organization" # 组织
    SKILL = "skill"              # 技能
    TOPIC = "topic"              # 话题


class RelationType(Enum):
    """关系类型"""
    IS_A = "is_a"                # 是一个（继承）
    HAS_PROPERTY = "has_property"  # 有属性
    RELATED_TO = "related_to"    # 相关
    PART_OF = "part_of"          # 部分属于
    USED_FOR = "used_for"        # 用于
    CREATED_BY = "created_by"    # 由...创建
    LOCATED_IN = "located_in"    # 位于
    KNOWS = "knows"              # 知道


@dataclass
class Entity:
    """知识实体"""
    entity_id: str
    name: str
    entity_type: EntityType
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0


@dataclass
class Relation:
    """关系"""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    description: str = ""
    created_at: float = field(default_factory=time.time)


class KnowledgeGraph:
    """知识图谱"""

    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self.entity_cache: Dict[str, Entity] = {}
        self.relation_cache: List[Relation] = []

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                description TEXT DEFAULT '',
                properties TEXT DEFAULT '{}',
                created_at REAL,
                updated_at REAL,
                access_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                relation_id TEXT PRIMARY KEY,
                source_id TEXT,
                target_id TEXT,
                relation_type TEXT,
                weight REAL DEFAULT 1.0,
                description TEXT DEFAULT '',
                created_at REAL,
                FOREIGN KEY (source_id) REFERENCES entities(entity_id),
                FOREIGN KEY (target_id) REFERENCES entities(entity_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relation_source ON relations(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relation_target ON relations(target_id)")
        self.conn.commit()

    def add_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: EntityType,
        description: str = "",
        properties: Dict = None,
    ) -> Entity:
        """
        添加实体

        Args:
            entity_id: 实体ID
            name: 名称
            entity_type: 类型
            description: 描述
            properties: 属性

        Returns:
            实体对象
        """
        entity = Entity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            description=description,
            properties=properties or {},
        )

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entities
            (entity_id, name, entity_type, description, properties, created_at, updated_at, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            entity.entity_id, entity.name, entity.entity_type.value,
            entity.description, json.dumps(entity.properties),
            entity.created_at, entity.updated_at
        ))
        self.conn.commit()

        self.entity_cache[entity_id] = entity
        return entity

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        description: str = "",
    ) -> str:
        """
        添加关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            weight: 权重
            description: 描述

        Returns:
            关系ID
        """
        import uuid
        relation_id = f"rel_{uuid.uuid4().hex[:8]}"

        relation = Relation(
            relation_id=relation_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            description=description,
        )

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO relations
            (relation_id, source_id, target_id, relation_type, weight, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            relation.relation_id, relation.source_id, relation.target_id,
            relation.relation_type.value, relation.weight, relation.description,
            relation.created_at
        ))
        self.conn.commit()

        self.relation_cache.append(relation)
        return relation_id

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        if entity_id in self.entity_cache:
            entity = self.entity_cache[entity_id]
            entity.access_count += 1
            return entity

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE entity_id = ?", (entity_id,))
        row = cursor.fetchone()

        if row:
            entity = Entity(
                entity_id=row["entity_id"],
                name=row["name"],
                entity_type=EntityType(row["entity_type"]),
                description=row["description"],
                properties=json.loads(row["properties"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                access_count=row["access_count"] + 1,
            )
            self.entity_cache[entity_id] = entity
            return entity

        return None

    def search_entities(self, query: str, entity_type: EntityType = None) -> List[Entity]:
        """
        搜索实体

        Args:
            query: 搜索关键词
            entity_type: 类型过滤

        Returns:
            实体列表
        """
        cursor = self.conn.cursor()

        sql = "SELECT * FROM entities WHERE name LIKE ?"
        params = [f"%{query}%"]

        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type.value)

        cursor.execute(sql, params)

        entities = []
        for row in cursor.fetchall():
            entities.append(Entity(
                entity_id=row["entity_id"],
                name=row["name"],
                entity_type=EntityType(row["entity_type"]),
                description=row["description"],
                properties=json.loads(row["properties"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                access_count=row["access_count"],
            ))
        return entities

    def get_relations(self, entity_id: str, direction: str = "outgoing") -> List[Relation]:
        """
        获取实体的关系

        Args:
            entity_id: 实体ID
            direction: outgoing(出)/incoming(入)/both(双向)

        Returns:
            关系列表
        """
        cursor = self.conn.cursor()

        if direction == "outgoing":
            cursor.execute("SELECT * FROM relations WHERE source_id = ?", (entity_id,))
        elif direction == "incoming":
            cursor.execute("SELECT * FROM relations WHERE target_id = ?", (entity_id,))
        else:
            cursor.execute("""
                SELECT * FROM relations
                WHERE source_id = ? OR target_id = ?
            """, (entity_id, entity_id))

        relations = []
        for row in cursor.fetchall():
            relations.append(Relation(
                relation_id=row["relation_id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relation_type=RelationType(row["relation_type"]),
                weight=row["weight"],
                description=row["description"],
                created_at=row["created_at"],
            ))
        return relations

    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> List[List[str]]:
        """
        查找两个实体间的路径

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            max_depth: 最大搜索深度

        Returns:
            路径列表（每条路径是实体ID序列）
        """
        # BFS搜索
        queue = [(source_id, [source_id])]
        visited = {source_id}
        paths = []

        while queue and len(paths) < 5:
            current, path = queue.pop(0)

            if current == target_id and len(path) > 1:
                paths.append(path)
                continue

            if len(path) >= max_depth:
                continue

            # 获取邻居
            relations = self.get_relations(current, "outgoing")
            for rel in relations:
                neighbor = rel.target_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return paths

    def infer_relations(self, entity_id: str) -> List[Dict]:
        """
        推理潜在关系

        Args:
            entity_id: 实体ID

        Returns:
            推理结果列表
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return []

        inferences = []

        # 1. 传递性推理 (is_a)
        is_a_relations = [r for r in self.get_relations(entity_id, "outgoing")
                         if r.relation_type == RelationType.IS_A]
        for rel in is_a_relations:
            parent_relations = self.get_relations(rel.target_id, "outgoing")
            for parent_rel in parent_relations:
                if parent_rel.relation_type == RelationType.HAS_PROPERTY:
                    inferences.append({
                        "type": "inherited_property",
                        "source": entity_id,
                        "target": parent_rel.target_id,
                        "via": rel.target_id,
                        "description": f"通过 {rel.target_id} 继承属性",
                    })

        # 2. 共同邻居推理
        outgoing = self.get_relations(entity_id, "outgoing")
        targets = {r.target_id for r in outgoing}

        for target in targets:
            target_relations = self.get_relations(target, "outgoing")
            for tr in target_relations:
                if tr.target_id not in targets and tr.target_id != entity_id:
                    inferences.append({
                        "type": "common_neighbor",
                        "source": entity_id,
                        "target": tr.target_id,
                        "via": target,
                        "description": f"通过 {target} 关联到 {tr.target_id}",
                    })

        return inferences

    def get_entity_neighborhood(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        获取实体邻域

        Args:
            entity_id: 实体ID
            depth: 搜索深度

        Returns:
            邻域信息
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return {}

        neighborhood = {
            "entity": entity,
            "outgoing_relations": [],
            "incoming_relations": [],
            "related_entities": [],
        }

        # 直接关系
        neighborhood["outgoing_relations"] = self.get_relations(entity_id, "outgoing")
        neighborhood["incoming_relations"] = self.get_relations(entity_id, "incoming")

        # 相关实体
        for rel in neighborhood["outgoing_relations"]:
            related = self.get_entity(rel.target_id)
            if related:
                neighborhood["related_entities"].append(related)

        if depth > 1:
            # 递归获取
            for related in neighborhood["related_entities"][:5]:
                sub_neighborhood = self.get_entity_neighborhood(related.entity_id, depth - 1)
                neighborhood[f"sub_{related.entity_id}"] = sub_neighborhood

        return neighborhood

    def update_entity_properties(self, entity_id: str, properties: Dict):
        """更新实体属性"""
        entity = self.get_entity(entity_id)
        if not entity:
            return

        entity.properties.update(properties)
        entity.updated_at = time.time()

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE entities SET properties = ?, updated_at = ?
            WHERE entity_id = ?
        """, (json.dumps(entity.properties), entity.updated_at, entity_id))
        self.conn.commit()

    def delete_entity(self, entity_id: str):
        """删除实体及其关系"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM relations WHERE source_id = ? OR target_id = ?", (entity_id, entity_id))
        cursor.execute("DELETE FROM entities WHERE entity_id = ?", (entity_id,))
        self.conn.commit()

        self.entity_cache.pop(entity_id, None)
        self.relation_cache = [r for r in self.relation_cache
                               if r.source_id != entity_id and r.target_id != entity_id]

    def get_stats(self) -> Dict[str, Any]:
        """获取图谱统计"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM entities")
        entity_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM relations")
        relation_count = cursor.fetchone()["count"]

        # 类型分布
        cursor.execute("""
            SELECT entity_type, COUNT(*) as count
            FROM entities GROUP BY entity_type
        """)
        type_distribution = {row["entity_type"]: row["count"] for row in cursor.fetchall()}

        # 关系类型分布
        cursor.execute("""
            SELECT relation_type, COUNT(*) as count
            FROM relations GROUP BY relation_type
        """)
        relation_distribution = {row["relation_type"]: row["count"] for row in cursor.fetchall()}

        return {
            "total_entities": entity_count,
            "total_relations": relation_count,
            "entity_types": type_distribution,
            "relation_types": relation_distribution,
            "cache_size": len(self.entity_cache),
        }

    def close(self):
        self.conn.close()
