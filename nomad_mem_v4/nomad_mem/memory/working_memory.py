"""
WorkingMemory - 工作记忆管理器
硬性4项限制，前额叶模拟
"""
import time
from typing import List, Tuple, Any


class WorkingMemory:
    """工作记忆：硬性4项限制"""

    def __init__(self, max_items: int = 4):
        self.max_items = max_items
        # 每项: (vector_id, attention_weight, timestamp)
        self.items: List[Tuple[int, float, float]] = []

    def add(self, vector_id: int, attention: float) -> Optional[Tuple[int, float]]:
        """
        添加项目到工作记忆
        如果超过限制，遗忘注意力最低的项目
        返回: 被遗忘的(vector_id, attention)，如果没有则为None
        """
        forgotten = None

        # 检查是否已存在
        for i, (vid, _, _) in enumerate(self.items):
            if vid == vector_id:
                # 更新注意力权重
                self.items[i] = (vector_id, attention, time.time())
                return None

        # 如果满了，遗忘最低注意力的项目
        if len(self.items) >= self.max_items:
            # 按注意力排序
            self.items.sort(key=lambda x: x[1])
            forgotten = (self.items[0][0], self.items[0][1])
            self.items.pop(0)

        # 添加新项目
        self.items.append((vector_id, attention, time.time()))
        return forgotten

    def get_current_focus(self) -> List[int]:
        """获取当前聚焦的向量ID列表"""
        return [item[0] for item in self.items]

    def get_items(self) -> List[Tuple[int, float, float]]:
        """获取所有工作记忆项目"""
        return list(self.items)

    def clear(self):
        """清空工作记忆"""
        self.items = []

    def is_full(self) -> bool:
        """检查是否已满"""
        return len(self.items) >= self.max_items

    def size(self) -> int:
        """获取当前项目数"""
        return len(self.items)
