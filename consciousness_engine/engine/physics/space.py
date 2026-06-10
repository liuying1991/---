"""
Space - 空间几何
XYZ坐标、距离、方向、空间关系
"""
import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional


class Vector3:
    """三维向量"""

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __repr__(self):
        return f"Vector3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

    def magnitude(self) -> float:
        """向量长度"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3':
        """归一化"""
        mag = self.magnitude()
        if mag == 0:
            return Vector3()
        return Vector3(self.x/mag, self.y/mag, self.z/mag)

    def dot(self, other: 'Vector3') -> float:
        """点积"""
        return self.x*other.x + self.y*other.y + self.z*other.z

    def to_numpy(self) -> np.ndarray:
        """转换为numpy数组"""
        return np.array([self.x, self.y, self.z], dtype=np.float32)

    @staticmethod
    def from_numpy(arr: np.ndarray) -> 'Vector3':
        """从numpy数组创建"""
        return Vector3(float(arr[0]), float(arr[1]), float(arr[2]))


class SpatialRelations:
    """空间关系计算辅助类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        space_config = config.get("physics", {}).get("space", {})
        self.vision_range = space_config.get("max_view_distance", 100)
        self.default_vision_range = 50.0
        self.default_hearing_range = 30.0

    def is_in_range(self, pos_a: Vector3, pos_b: Vector3, max_distance: float = None) -> bool:
        """检查两点是否在指定距离内"""
        dist = (pos_a - pos_b).magnitude()
        threshold = max_distance or self.vision_range
        return dist <= threshold

    def is_in_field_of_view(self, observer: Vector3, forward: Vector3,
                           target: Vector3, fov_degrees: float = 90.0) -> bool:
        """检查目标是否在视野范围内"""
        to_target = (target - observer).normalize()
        cos_angle = forward.normalize().dot(to_target)
        angle = math.acos(max(-1, min(1, cos_angle)))
        angle_deg = math.degrees(angle)
        return angle_deg <= fov_degrees / 2


class Space:
    """空间几何管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.space_config = config.get("physics", {}).get("space", {})
        self.dimensions = self.space_config.get("dimensions", 3)
        self.unit = self.space_config.get("unit", "meter")
        self.max_view_distance = self.space_config.get("max_view_distance", 100)

        # 实体字典 {entity_id: {position, direction, properties}}
        self.entities = {}

    def add_entity(self, entity_id: str, position: Vector3,
                  direction: Vector3 = None, properties: Dict = None):
        """添加实体到空间"""
        self.entities[entity_id] = {
            "position": position,
            "direction": direction or Vector3(0, 0, 1),
            "properties": properties or {},
        }

    def move_entity(self, entity_id: str, new_position: Vector3):
        """移动实体"""
        if entity_id in self.entities:
            self.entities[entity_id]["position"] = new_position

    def get_entity_position(self, entity_id: str) -> Optional[Vector3]:
        """获取实体位置"""
        if entity_id in self.entities:
            return self.entities[entity_id]["position"]
        return None

    def distance(self, pos_a: Vector3, pos_b: Vector3) -> float:
        """计算两点距离"""
        return (pos_a - pos_b).magnitude()

    def direction_to(self, from_pos: Vector3, to_pos: Vector3) -> Vector3:
        """计算从A到B的方向向量"""
        return (to_pos - from_pos).normalize()

    def entities_in_range(self, position: Vector3,
                         range_meters: float) -> List[Tuple[str, float]]:
        """获取指定范围内的实体，返回[(entity_id, distance)]"""
        results = []
        for entity_id, data in self.entities.items():
            dist = self.distance(position, data["position"])
            if dist <= range_meters:
                results.append((entity_id, dist))

        # 按距离排序
        results.sort(key=lambda x: x[1])
        return results

    def entities_in_view(self, position: Vector3,
                        direction: Vector3,
                        fov: float = 90.0) -> List[Tuple[str, float, float]]:
        """
        获取视野内的实体
        返回[(entity_id, distance, angle)]
        """
        results = []
        for entity_id, data in self.entities.items():
            dist = self.distance(position, data["position"])

            if dist > self.max_view_distance:
                continue

            # 计算方向
            to_entity = self.direction_to(position, data["position"])

            # 计算夹角
            cos_angle = direction.normalize().dot(to_entity)
            angle = math.acos(max(-1, min(1, cos_angle)))
            angle_deg = math.degrees(angle)

            if angle_deg <= fov / 2:
                results.append((entity_id, dist, angle_deg))

        results.sort(key=lambda x: x[1])
        return results

    def spatial_relationship(self, entity_a: str, entity_b: str) -> Dict[str, Any]:
        """计算两个实体的空间关系"""
        pos_a = self.get_entity_position(entity_a)
        pos_b = self.get_entity_position(entity_b)

        if pos_a is None or pos_b is None:
            return {}

        dist = self.distance(pos_a, pos_b)
        direction = self.direction_to(pos_a, pos_b)

        return {
            "distance": dist,
            "direction": direction,
            "nearby": dist < 5,
            "close": dist < 2,
            "far": dist > 20,
        }

    def get_scene_snapshot(self) -> Dict[str, Any]:
        """获取场景快照"""
        return {
            "entities": {
                eid: {
                    "position": {"x": d["position"].x, "y": d["position"].y, "z": d["position"].z},
                    "direction": {"x": d["direction"].x, "y": d["direction"].y, "z": d["direction"].z},
                    "properties": d["properties"],
                }
                for eid, d in self.entities.items()
            },
            "entity_count": len(self.entities),
        }
