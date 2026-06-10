"""
记忆桥接层 - 将v4记忆系统桥接到对话上下文

核心职责:
1. 从向量存储中检索与当前对话相关的记忆
2. 将对话内容存储到记忆系统
3. 记录记忆查询模式
4. 支持新的 MemoryOS 系统（三级存储 + 记忆进化）
"""
import json
import time
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict


class MemoryBridge:
    """记忆桥接器"""

    def __init__(self, vector_store, encoder, working_memory=None,
                 hippocampus=None, cortex=None, attention_scorer=None):
        """
        初始化记忆桥接器

        Args:
            vector_store: VectorStore实例
            encoder: MultimodalEncoder实例（用于文本编码）
            working_memory: WorkingMemory实例（可选）
            hippocampus: Hippocampus实例（可选）
            cortex: Cortex实例（可选）
            attention_scorer: AttentionScorer实例（可选）
        """
        self.vector_store = vector_store
        self.encoder = encoder
        self.working_memory = working_memory
        self.hippocampus = hippocampus
        self.cortex = cortex
        self.attention_scorer = attention_scorer

    def relevant_memories(self, query: str, k: int = 5) -> list[dict]:
        """
        检索与查询相关的记忆

        Args:
            query: 查询文本
            k: 返回的记忆数量

        Returns:
            相关记忆列表，每个记忆包含content、summary、importance等字段
        """
        # 1. 编码查询文本
        embedding, _, _ = self.encoder.encode_text(query)
        if embedding is None:
            return []

        # 2. 在向量空间中搜索相似记忆
        similar = self.vector_store.search_similar(embedding, top_k=k, min_similarity=0.3)

        # 3. 转换为记忆格式
        memories = []
        for vector_id, similarity in similar:
            vec = self.vector_store.get_vector(vector_id)
            if vec:
                # 计算重要性
                importance = self._calc_importance(vec, similarity)

                memory = {
                    "vector_id": vector_id,
                    "content": vec["raw_content"],
                    "source_type": vec["source_type"],
                    "emotion_score": vec["emotion_score"],
                    "importance": importance,
                    "created_at": vec["created_at"],
                    "similarity": similarity,
                }
                memories.append(memory)

        # 按重要性排序
        memories.sort(key=lambda m: m["importance"], reverse=True)

        return memories

    def store_conversation(self, user_message: str, ai_response: str, user_id: str = "default"):
        """
        将对话内容存储到记忆系统

        Args:
            user_message: 用户消息
            ai_response: AI回复
            user_id: 用户ID
        """
        # 构建对话记录
        conversation = f"用户: {user_message}\nAI: {ai_response}"

        # 编码
        embedding, _, emotion_score = self.encoder.encode_text(conversation)
        if embedding is None:
            return

        # 插入向量存储
        vector_id = self.vector_store.insert_vector(
            embedding, conversation, "conversation", emotion_score
        )

        # 编码新颖性
        similar = self.vector_store.search_similar(embedding, top_k=5)
        if similar:
            import numpy as np
            novelty_score = 1.0 - np.mean([sim for _, sim in similar])
        else:
            novelty_score = 1.0

        self.vector_store.update_novelty(vector_id, novelty_score)

        # 写入工作记忆
        if self.working_memory:
            # 计算注意力分数
            wm_embeddings = []
            for wm_id in self.working_memory.get_current_focus():
                wm_emb = self.vector_store.get_embedding(wm_id)
                if wm_emb is not None:
                    wm_embeddings.append(wm_emb)

            cortex_embeddings = []
            if self.cortex:
                cortex_vectors = self.cortex.get_all()
                for cv in cortex_vectors[:10]:
                    cortex_emb = self.vector_store.get_embedding(cv["vector_id"])
                    if cortex_emb is not None:
                        cortex_embeddings.append(cortex_emb)

            attention = 0.5  # 默认注意力
            if self.attention_scorer:
                attention = self.attention_scorer.score(
                    embedding, emotion_score, wm_embeddings, cortex_embeddings
                )

            self.working_memory.add(vector_id, attention)

        # 更新海马体
        if self.hippocampus:
            self.hippocampus.encode(vector_id, emotion_score)

        # 更新最后访问时间
        self.vector_store.update_last_accessed(vector_id)

    def record_query(self, query: str, memories: list[dict], user_id: str = "default"):
        """
        记录记忆查询（用于学习用户模式）

        Args:
            query: 查询文本
            memories: 返回的记忆列表
            user_id: 用户ID
        """
        # 记录查询模式到日志（未来可扩展为学习用户查询模式）
        memory_ids = [m["vector_id"] for m in memories]
        # 这里可以进一步处理，比如统计哪些记忆被频繁访问

    def get_memory_summary(self) -> dict:
        """
        获取记忆系统摘要

        Returns:
            摘要字典
        """
        all_vectors = self.vector_store.get_all_vectors()
        total_vectors = len(all_vectors)

        # 按类型统计
        type_counts = {}
        for vec in all_vectors:
            source = vec["source_type"]
            type_counts[source] = type_counts.get(source, 0) + 1

        # 平均情绪分数
        emotions = [v["emotion_score"] for v in all_vectors]
        avg_emotion = sum(emotions) / len(emotions) if emotions else 0.0

        # 工作记忆状态
        wm_size = self.working_memory.size() if self.working_memory else 0
        wm_max = self.working_memory.max_items if self.working_memory else 0

        return {
            "total_vectors": total_vectors,
            "by_type": type_counts,
            "avg_emotion_score": avg_emotion,
            "working_memory": f"{wm_size}/{wm_max}",
        }

    def _calc_importance(self, vector: dict, similarity: float) -> float:
        """
        计算记忆重要性

        Args:
            vector: 向量字典
            similarity: 与查询的相似度

        Returns:
            重要性分数 (0-1)
        """
        # 重要性 = 情绪强度 * 新颖性 * 可塑性 * 相似度
        emotion = abs(vector.get("emotion_score", 0))
        novelty = vector.get("novelty_score", 0.5)
        plasticity = vector.get("plasticity", 0.5)

        importance = emotion * novelty * plasticity * similarity
        return min(1.0, importance)


class MemoryBridgeV2:
    """记忆桥接器 V2 - 支持 MemoryOS + 记忆进化 + 上下文压缩"""

    def __init__(self, memory_os=None, memory_evolution=None, context_compressor=None, config: dict = None):
        """
        初始化 V2 记忆桥接器

        Args:
            memory_os: MemoryOS实例（可选）
            memory_evolution: MemoryEvolution实例（可选）
            context_compressor: ContextCompressor实例（可选）
            config: 配置字典
        """
        self.memory_os = memory_os
        self.memory_evolution = memory_evolution
        self.compressor = context_compressor
        self.config = config or {}
        self.memory_injection_k = self.config.get("memory_injection_k", 5)
        self.session_queries: Dict[str, List[Dict]] = {}  # user_id -> 查询历史

    def relevant_memories(self, query: str, k: int = None) -> List[Dict]:
        """
        检索与查询相关的记忆

        Args:
            query: 查询文本
            k: 返回的记忆数量（默认使用配置值）

        Returns:
            相关记忆列表
        """
        k = k or self.memory_injection_k

        if not self.memory_os:
            return []

        # 使用 MemoryOS 检索
        units = self.memory_os.storage.search_by_content(query, limit=k * 2)

        # 转换为记忆格式
        memories = []
        for unit in units:
            memory = {
                "vector_id": unit.id,
                "content": unit.content,
                "source_type": "memory_os",
                "importance": unit.importance,
                "created_at": unit.created_at,
                "similarity": self._calc_similarity(query, unit.content),
                "tags": unit.tags,
                "level": unit.level.value,
            }
            memories.append(memory)

        # 按重要性排序
        memories.sort(key=lambda m: m["importance"], reverse=True)
        return memories[:k]

    def store_conversation(self, user_message: str, ai_response: str, user_id: str = "default"):
        """
        将对话内容存储到记忆系统

        Args:
            user_message: 用户消息
            ai_response: AI回复
            user_id: 用户ID
        """
        if not self.memory_os:
            return

        # 1. 存储到短期记忆
        conversation = f"用户: {user_message}\nAI: {ai_response}"
        unit = self.memory_os.add_short_term(
            content=conversation,
            tags=["conversation", f"user:{user_id}"],
            metadata={"user_message": user_message, "ai_response": ai_response}
        )

        # 2. 如果配置了记忆进化，创建笔记
        if self.memory_evolution and ai_response:
            note = self.memory_evolution.create_note(
                content=ai_response,
                context=f"对话: {user_message}",
                tags=["response", f"user:{user_id}"]
            )

            # 生成链接
            self.memory_evolution.generate_links(note.id)

    def record_query(self, query: str, memories: List[Dict], user_id: str = "default"):
        """
        记录记忆查询

        Args:
            query: 查询文本
            memories: 返回的记忆列表
            user_id: 用户ID
        """
        if user_id not in self.session_queries:
            self.session_queries[user_id] = []

        self.session_queries[user_id].append({
            "query": query,
            "result_count": len(memories),
            "timestamp": time.time(),
        })

    def compress_and_store(self, messages: List[Dict], user_id: str = "default"):
        """
        压缩对话并存储为记忆

        Args:
            messages: 消息列表
            user_id: 用户ID
        """
        if not self.compressor or not self.memory_os:
            return

        # 压缩消息
        entry = self.compressor.compress_to_memory_entry(messages)

        # 存储为中期记忆
        self.memory_os.add_mid_term(
            content=entry["content"],
            importance=entry.get("importance", 0.5),
            tags=entry.get("tags", []) + [f"user:{user_id}"],
        )

    def get_memory_summary(self) -> Dict:
        """获取记忆系统摘要"""
        summary = {"version": "v2"}

        if self.memory_os:
            stats = self.memory_os.get_stats()
            summary["memory_os"] = stats

        if self.memory_evolution:
            evo_stats = self.memory_evolution.get_stats()
            summary["evolution"] = evo_stats

        if self.compressor:
            comp_stats = self.compressor.get_stats()
            summary["compression"] = comp_stats

        return summary

    def _calc_importance(self, vector: Dict, similarity: float) -> float:
        """计算记忆重要性"""
        emotion = abs(vector.get("emotion_score", 0))
        novelty = vector.get("novelty_score", 0.5)
        plasticity = vector.get("plasticity", 0.5)
        importance = emotion * novelty * plasticity * similarity
        return min(1.0, importance)

    def _calc_similarity(self, query: str, content: str) -> float:
        """简单计算文本相似度（词重叠）"""
        if not query or not content:
            return 0.0

        q_words = set(query.lower().split())
        c_words = set(content.lower().split())

        if not q_words or not c_words:
            return 0.0

        overlap = len(q_words & c_words)
        union = len(q_words | c_words)
        return overlap / union if union > 0 else 0.0

    def close(self):
        """关闭连接"""
        if self.memory_os:
            self.memory_os.close()
        if self.memory_evolution:
            self.memory_evolution.close()
