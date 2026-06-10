"""
记忆技能 - memory_recall, memory_store
连接v4记忆系统
"""
import json
from nomad_mem.skills.base import BaseSkill


class MemoryRecall(BaseSkill):
    """从记忆系统中检索相关记忆"""

    def __init__(self, memory_bridge):
        self.memory_bridge = memory_bridge

    @property
    def name(self) -> str:
        return "memory_recall"

    @property
    def description(self) -> str:
        return "从我的记忆系统中检索与关键词相关的历史记忆。用于回忆过去的对话、用户偏好、重要事实等。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "检索关键词或查询语句",
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数量，默认5",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, args: dict) -> str:
        query = args.get("query", "")
        max_results = args.get("max_results", 5)

        if not self.memory_bridge:
            return "记忆系统未初始化"

        memories = self.memory_bridge.relevant_memories(query, k=max_results)

        if not memories:
            return f"没有找到与'{query}'相关的记忆"

        output = [f"与'{query}'相关的记忆:"]
        for i, mem in enumerate(memories, 1):
            source = mem.get("source_type", "unknown")
            importance = mem.get("importance", 0)
            content = mem.get("content", "")
            created = mem.get("created_at", "")

            # 截断过长内容
            if len(content) > 200:
                content = content[:200] + "..."

            output.append(
                f"{i}. [{source}] (重要性:{importance:.2f}) {created}\n{content}"
            )

        return "\n".join(output)


class MemoryStore(BaseSkill):
    """向记忆系统中存储信息"""

    def __init__(self, memory_bridge):
        self.memory_bridge = memory_bridge

    @property
    def name(self) -> str:
        return "memory_store"

    @property
    def description(self) -> str:
        return "将重要信息存储到我的记忆系统中。用于记住用户偏好、重要事实、任务记录等。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "要存储的信息内容",
                },
                "category": {
                    "type": "string",
                    "description": "信息类别: preference/fact/task/conversation",
                    "enum": ["preference", "fact", "task", "conversation", "other"],
                    "default": "other",
                },
            },
            "required": ["content"],
        }

    def execute(self, args: dict) -> str:
        content = args.get("content", "")
        category = args.get("category", "other")

        if not self.memory_bridge:
            return "记忆系统未初始化"

        if not content:
            return "存储内容不能为空"

        # 构建存储格式
        record = f"[{category}] {content}"

        # 编码并存储
        embedding, _, emotion_score = self.memory_bridge.encoder.encode_text(record)
        if embedding is None:
            return "编码失败，无法存储"

        vector_id = self.memory_bridge.vector_store.insert_vector(
            embedding, record, f"stored_{category}", emotion_score
        )
        self.memory_bridge.vector_store.update_last_accessed(vector_id)

        return f"信息已存储 (ID: {vector_id}, 类别: {category})"


class MemoryStatus(BaseSkill):
    """获取记忆系统状态摘要"""

    def __init__(self, memory_bridge):
        self.memory_bridge = memory_bridge

    @property
    def name(self) -> str:
        return "memory_status"

    @property
    def description(self) -> str:
        return "获取我的记忆系统状态摘要，包括记忆总量、各类型分布、工作记忆状态等。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, args: dict) -> str:
        if not self.memory_bridge:
            return "记忆系统未初始化"

        summary = self.memory_bridge.get_memory_summary()

        lines = ["=== 记忆系统状态 ==="]
        lines.append(f"总记忆数: {summary['total_vectors']}")

        if summary.get("by_type"):
            lines.append("按类型分布:")
            for type_name, count in summary["by_type"].items():
                lines.append(f"  {type_name}: {count}")

        lines.append(f"平均情绪分: {summary['avg_emotion_score']:.3f}")
        lines.append(f"工作记忆: {summary['working_memory']}")

        return "\n".join(lines)
