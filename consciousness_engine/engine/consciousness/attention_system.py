"""
注意力系统 - 工作记忆管理 + 意识焦点控制
模拟前额叶皮层的注意力分配机制
"""

from typing import Dict, List, Optional, Tuple
import time
import math


class AttentionSystem:
    """
    注意力系统
    控制意识焦点在3D空间中的分配
    """

    def __init__(self, config: Dict):
        self.config = config

        # 注意力参数
        attention_config = config.get("consciousness", {}).get("attention", {})
        self.focus_radius = attention_config.get("focus_radius", 5.0)  # 焦点半径（米）
        self.attention_decay_rate = attention_config.get("decay_rate", 0.9)  # 注意力衰减率
        self.switch_cost = attention_config.get("switch_cost", 0.3)  # 注意力切换成本

        # 当前状态
        self.current_focus_location: Optional[Tuple[float, float, float]] = None
        self.focus_intensity = 1.0  # 当前焦点强度 (0-1)
        self.attention_map: Dict[str, float] = {}  # 空间对象 → 注意力分配
        self.last_focus_switch_time = 0.0

        # 统计
        self.stats = {
            "total_focus_switches": 0,
            "total_attention_updates": 0,
            "average_focus_duration": 0.0,
        }

    def shift_focus(
        self,
        new_location: Tuple[float, float, float],
        intensity: float = 1.0,
    ) -> float:
        """
        将注意力焦点转移到新位置

        Args:
            new_location: 新的焦点位置 (x, y, z)
            intensity: 焦点强度 (0-1)

        Returns:
            注意力切换成本
        """
        cost = 0.0

        if self.current_focus_location:
            # 计算空间距离
            distance = self._euclidean_distance(self.current_focus_location, new_location)

            # 距离越远，切换成本越高
            cost = self.switch_cost * (1 + distance / 10.0)

            # 衰减旧焦点
            self._decay_all_attention()

        self.current_focus_location = new_location
        self.focus_intensity = max(0.0, min(1.0, intensity))
        self.last_focus_switch_time = time.time()
        self.stats["total_focus_switches"] += 1

        return cost

    def allocate_attention(
        self,
        object_id: str,
        priority: float,
        emotional_relevance: float = 0.0,
        spatial_relevance: float = 0.0,
    ) -> float:
        """
        为特定对象分配注意力

        Args:
            object_id: 对象标识
            priority: 基础优先级 (0-1)
            emotional_relevance: 情绪相关性 (0-1)
            spatial_relevance: 空间相关性 (0-1)

        Returns:
            分配的注意力值
        """
        # 综合注意力评分
        attention_score = (
            priority * 0.4
            + emotional_relevance * 0.3
            + spatial_relevance * 0.3
        )

        # 如果对象在焦点范围内，增强注意力
        if self._is_in_focus_range(object_id):
            attention_score *= (1 + self.focus_intensity * 0.5)

        self.attention_map[object_id] = attention_score
        self.stats["total_attention_updates"] += 1

        return attention_score

    def get_attention_distribution(self) -> Dict[str, float]:
        """获取当前注意力分布"""
        # 衰减所有注意力
        self._decay_all_attention()

        # 归一化
        total = sum(self.attention_map.values())
        if total > 0:
            return {k: v / total for k, v in self.attention_map.items()}
        return dict(self.attention_map)

    def get_top_focused_objects(self, top_k: int = 3) -> List[Tuple[str, float]]:
        """获取最受关注的对象"""
        distribution = self.get_attention_distribution()
        sorted_objects = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        return sorted_objects[:top_k]

    def compute_spatial_attention(
        self,
        observer_position: Tuple[float, float, float],
        objects: List[Dict],
    ) -> Dict[str, float]:
        """
        计算空间注意力分布

        Args:
            observer_position: 观察者位置 (x, y, z)
            objects: 对象列表 [{"id": str, "position": (x,y,z), "salience": float}]

        Returns:
            对象ID → 注意力分数
        """
        attention_scores = {}

        for obj in objects:
            obj_id = obj["id"]
            obj_position = obj.get("position", (0, 0, 0))
            obj_salience = obj.get("salience", 0.5)

            # 计算距离
            distance = self._euclidean_distance(observer_position, obj_position)

            # 距离衰减
            distance_factor = 1.0 / (1.0 + distance / self.focus_radius)

            # 视野角度（简化版）
            in_focus = self._is_in_focus_range_for_position(
                observer_position, obj_position
            )

            # 综合注意力
            attention = obj_salience * distance_factor * (1.5 if in_focus else 1.0)

            attention_scores[obj_id] = attention

        return attention_scores

    def update_focus_from_perception(
        self,
        perceived_objects: List[Dict],
        observer_position: Tuple[float, float, float],
    ):
        """根据感知更新注意力焦点"""
        # 计算空间注意力
        spatial_attention = self.compute_spatial_attention(
            observer_position, perceived_objects
        )

        # 更新注意力映射
        for obj_id, attention in spatial_attention.items():
            self.allocate_attention(
                object_id=obj_id,
                priority=attention,
                spatial_relevance=attention,
            )

        # 如果最高注意力对象不在当前焦点，转移焦点
        top_objects = self.get_top_focused_objects(1)
        if top_objects:
            top_obj_id, top_attention = top_objects[0]
            for obj in perceived_objects:
                if obj["id"] == top_obj_id:
                    self.shift_focus(obj.get("position", (0, 0, 0)), top_attention)
                    break

    def _decay_all_attention(self):
        """衰减所有注意力值"""
        for obj_id in list(self.attention_map.keys()):
            self.attention_map[obj_id] *= self.attention_decay_rate
            # 移除极低注意力
            if self.attention_map[obj_id] < 0.01:
                del self.attention_map[obj_id]

    def _is_in_focus_range(self, object_id: str) -> bool:
        """检查对象是否在焦点范围内（简化版）"""
        return object_id in self.attention_map

    def _is_in_focus_range_for_position(
        self,
        observer: Tuple[float, float, float],
        target: Tuple[float, float, float],
    ) -> bool:
        """检查目标位置是否在焦点范围内"""
        if self.current_focus_location is None:
            return True
        distance = self._euclidean_distance(self.current_focus_location, target)
        return distance <= self.focus_radius

    @staticmethod
    def _euclidean_distance(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        """计算3D欧几里得距离"""
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
