"""
记忆桥接层 - 将NomadMem v4.0集成到意识引擎
感知数据 → 多模态编码 → 海马体快写 → 工作记忆聚焦
"""

import sys
import os
import time
from typing import Dict, List, Optional, Tuple

# 添加NomadMem v4.0到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
try:
    from nomad_mem_v4.nomad_mem.encoder.multimodal import MultimodalEncoder
    from nomad_mem_v4.nomad_mem.memory.vector_store import VectorStore
    from nomad_mem_v4.nomad_mem.memory.hippocampus import Hippocampus
    from nomad_mem_v4.nomad_mem.memory.cortex import Cortex
    from nomad_mem_v4.nomad_mem.memory.working_memory import WorkingMemory
    from nomad_mem_v4.nomad_mem.attention.scorer_v4 import AttentionScorerV4
except (ImportError, Exception) as e:
    print(f"[MemoryBridge] NomadMem v4.0 import fallback: {e}")
    MultimodalEncoder = None
    VectorStore = None
    Hippocampus = None
    Cortex = None
    WorkingMemory = None
    AttentionScorerV4 = None


class MemoryBridge:
    """
    意识引擎与NomadMem v4.0的桥梁
    负责将3D空间中的感知数据编码并存储到记忆大脑
    """

    def __init__(self, config: Dict):
        self.config = config
        self.is_active = False

        # 延迟初始化NomadMem组件
        self.encoder: Optional[MultimodalEncoder] = None
        self.vector_store: Optional[VectorStore] = None
        self.hippocampus: Optional[Hippocampus] = None
        self.cortex: Optional[Cortex] = None
        self.working_memory: Optional[WorkingMemory] = None
        self.attention_scorer: Optional[AttentionScorerV4] = None

        # 统计信息
        self.stats = {
            "total_encoded": 0,
            "total_consolidated": 0,
            "total_forgotten": 0,
            "working_memory_hits": 0,
        }

    def initialize(self):
        """初始化记忆大脑组件"""
        if MultimodalEncoder is None:
            print("[MemoryBridge] Using mock memory bridge (NomadMem v4.0 not available)")
            self.is_active = False
            return

        print("[MemoryBridge] Initializing NomadMem v4.0...")

        # 初始化编码器
        self.encoder = MultimodalEncoder(self.config)

        # 初始化向量存储
        db_path = self.config.get("consciousness", {}).get("memory", {}).get(
            "db_path", "data/consciousness_memory.db"
        )
        self.vector_store = VectorStore(db_path)

        # 初始化海马体和皮层
        self.hippocampus = Hippocampus(self.vector_store.conn, self.config)
        self.cortex = Cortex(self.vector_store.conn, self.config)

        # 初始化工作记忆（硬性4项限制）
        wm_limit = self.config.get("attention", {}).get("working_memory_limit", 4)
        self.working_memory = WorkingMemory(max_items=wm_limit)

        # 初始化注意力评分器
        self.attention_scorer = AttentionScorerV4(self.config)

        self.is_active = True
        print(f"[MemoryBridge] NomadMem v4.0 initialized (WM limit: {wm_limit})")

    def encode_perception(
        self,
        content: str,
        perception_type: str = "text",
        spatial_location: Optional[Tuple[float, float, float]] = None,
        emotion_trigger: float = 0.0,
    ) -> Optional[int]:
        """
        将感知数据编码到记忆大脑

        Args:
            content: 感知内容（文本描述/空间坐标/物体信息）
            perception_type: 感知类型（visual/auditory/tactile/spatial/text）
            spatial_location: 3D空间位置 (x, y, z)
            emotion_trigger: 情绪触发强度 (0-1)

        Returns:
            vector_id: 编码后的向量ID，失败返回None
        """
        if not self.is_active:
            return None

        # 添加空间位置信息到内容
        if spatial_location:
            content = f"[{spatial_location[0]:.1f},{spatial_location[1]:.1f},{spatial_location[2]:.1f}] {content}"

        # 编码为向量
        embedding = self.encoder.encode_text(content)

        # 计算情绪分数（结合外部触发和文本情绪）
        emotion_score = max(emotion_trigger, 0.1)

        # 插入向量存储
        vector_id = self.vector_store.insert_vector(
            embedding=embedding,
            content=content,
            source_type=perception_type,
            emotion_score=emotion_score,
        )

        # 海马体快写（情绪门控学习率）
        self.hippocampus.encode(vector_id, emotion_score)

        # 计算注意力分数
        attention_score = self.attention_scorer.score(
            embedding=embedding,
            emotion=emotion_score,
            working_memory_embeddings=self._get_working_memory_embeddings(),
            cortex_embeddings=self._get_cortex_embeddings(),
        )

        # 加入工作记忆
        evicted = self.working_memory.add(vector_id, attention_score)
        if evicted:
            evicted_id, evicted_attention = evicted
            self.stats["working_memory_hits"] += 1

        self.stats["total_encoded"] += 1

        return vector_id

    def retrieve_relevant_memories(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[Dict]:
        """
        从记忆大脑检索相关记忆

        Args:
            query: 查询内容
            top_k: 返回数量
            min_similarity: 最小相似度阈值

        Returns:
            相关记忆列表 [{vector_id, content, similarity, emotion_score}]
        """
        if not self.is_active:
            return []

        # 编码查询
        query_embedding = self.encoder.encode_text(query)

        # 搜索相似向量
        similar_vectors = self.vector_store.search_similar(
            embedding=query_embedding,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        results = []
        for vector_id, similarity in similar_vectors:
            vector_data = self.vector_store.get_vector(vector_id)
            if vector_data:
                results.append({
                    "vector_id": vector_id,
                    "content": vector_data.get("raw_content", ""),
                    "similarity": similarity,
                    "emotion_score": vector_data.get("emotion_score", 0),
                    "source_type": vector_data.get("source_type", ""),
                })

        return results

    def get_working_memory_focus(self) -> List[Dict]:
        """获取当前工作记忆焦点"""
        if not self.is_active:
            return []

        focus_ids = self.working_memory.get_current_focus()
        results = []
        for vid in focus_ids:
            vector_data = self.vector_store.get_vector(vid)
            if vector_data:
                results.append({
                    "vector_id": vid,
                    "content": vector_data.get("raw_content", ""),
                    "emotion_score": vector_data.get("emotion_score", 0),
                })
        return results

    def get_cortex_summary(self) -> Dict:
        """获取皮层记忆摘要"""
        if not self.is_active:
            return {"count": 0, "vectors": []}

        cortex_vectors = self.cortex.get_all()
        return {
            "count": len(cortex_vectors),
            "vectors": [
                {
                    "vector_id": v["vector_id"],
                    "importance": v.get("importance_score", 0),
                    "content": self.vector_store.get_vector(v["vector_id"]).get("raw_content", "")
                    if self.vector_store
                    else "",
                }
                for v in cortex_vectors[:10]
            ],
        }

    def _get_working_memory_embeddings(self) -> List:
        """获取工作记忆中所有向量的embedding"""
        if not self.is_active or not self.working_memory:
            return []
        embeddings = []
        for vid, _, _ in self.working_memory.get_items():
            emb = self.vector_store.get_embedding(vid)
            if emb is not None:
                embeddings.append(emb)
        return embeddings

    def _get_cortex_embeddings(self) -> List:
        """获取皮层中所有向量的embedding"""
        if not self.is_active or not self.cortex:
            return []
        embeddings = []
        for cortex_record in self.cortex.get_all():
            vid = cortex_record["vector_id"]
            emb = self.vector_store.get_embedding(vid)
            if emb is not None:
                embeddings.append(emb)
        return embeddings

    def close(self):
        """关闭记忆大脑"""
        if self.vector_store:
            self.vector_store.close()
        self.is_active = False
