"""
3D渲染器 - 使用ASCII渲染3D意识空间的2D投影
"""

import math
import sys
import os
from typing import Dict, List, Optional, Tuple

# 使用physics层的Vector3
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from engine.physics.space import Vector3


class Camera:
    """虚拟摄像机"""

    def __init__(self, position: Vector3, fov: float = 60.0):
        self.position = position
        self.rotation = Vector3(0, 0, 0)  # pitch, yaw, roll
        self.fov = fov

    def project(self, point: Vector3, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """将3D点投影到2D屏幕"""
        # 简单透视投影
        relative = Vector3(
            point.x - self.position.x,
            point.y - self.position.y,
            point.z - self.position.z,
        )

        # 避免除以零
        if relative.z <= 0.1:
            relative.z = 0.1

        # 投影系数
        focal_length = screen_height / (2 * math.tan(math.radians(self.fov / 2)))
        scale = focal_length / relative.z

        screen_x = int(screen_width / 2 + relative.x * scale)
        screen_y = int(screen_height / 2 - relative.y * scale)

        return (screen_x, screen_y)


class WorldObject:
    """世界中的对象"""

    def __init__(
        self,
        obj_id: str,
        position: Vector3,
        obj_type: str = "default",
        properties: Optional[Dict] = None,
    ):
        self.id = obj_id
        self.position = position
        self.type = obj_type
        self.properties = properties or {}
        self.attention_score = 0.0
        self.emotion_relevance = 0.0

    def update(self, dt: float):
        """更新对象状态"""
        pass


class Scene:
    """3D场景"""

    def __init__(self):
        self.objects: Dict[str, WorldObject] = {}
        self.camera = Camera(Vector3(0, 0, 10))
        self.time = 0.0

    def add_object(self, obj: WorldObject):
        """添加对象到场景"""
        self.objects[obj.id] = obj

    def remove_object(self, obj_id: str):
        """从场景移除对象"""
        if obj_id in self.objects:
            del self.objects[obj_id]

    def get_objects_in_range(
        self,
        center: Vector3,
        radius: float,
    ) -> List[WorldObject]:
        """获取范围内所有对象"""
        return [
            obj
            for obj in self.objects.values()
            if (obj.position - center).magnitude() <= radius
        ]

    def update(self, dt: float):
        """更新场景"""
        self.time += dt
        for obj in self.objects.values():
            obj.update(dt)


class Renderer3D:
    """
    3D渲染器（使用ASCII/控制台渲染）
    将3D意识空间投影到2D显示
    """

    def __init__(self, config: Dict):
        self.config = config
        self.screen_width = config.get("vr", {}).get("screen_width", 80)
        self.screen_height = config.get("vr", {}).get("screen_height", 24)
        self.scene = Scene()
        self.is_running = False

    def set_camera_position(self, x: float, y: float, z: float):
        """设置摄像机位置"""
        self.scene.camera.position = Vector3(x, y, z)

    def add_object(self, obj_id: str, x: float, y: float, z: float, obj_type: str = "default", properties: Dict = None):
        """添加场景对象"""
        obj = WorldObject(obj_id, Vector3(x, y, z), obj_type, properties)
        self.scene.add_object(obj)

    def update_object_attention(self, obj_id: str, attention: float, emotion: float = 0.0):
        """更新对象注意力"""
        if obj_id in self.scene.objects:
            self.scene.objects[obj_id].attention_score = attention
            self.scene.objects[obj_id].emotion_relevance = emotion

    def render_frame(self) -> str:
        """渲染一帧到ASCII字符串"""
        # 创建空白画布
        canvas = [[" " for _ in range(self.screen_width)] for _ in range(self.screen_height)]

        # 投影所有对象
        projected = []
        for obj in self.scene.objects.values():
            screen_pos = self.scene.camera.project(
                obj.position, self.screen_width, self.screen_height
            )
            depth = (obj.position - self.scene.camera.position).magnitude()
            projected.append((obj, screen_pos, depth))

        # 按深度排序（远的先画）
        projected.sort(key=lambda x: x[2], reverse=True)

        # 渲染对象
        for obj, (sx, sy), depth in projected:
            if 0 <= sx < self.screen_width and 0 <= sy < self.screen_height:
                # 根据注意力选择字符
                attention = obj.attention_score
                if attention > 0.7:
                    char = "@"
                elif attention > 0.4:
                    char = "#"
                elif attention > 0.2:
                    char = "+"
                else:
                    char = "."

                # 根据对象类型调整
                if obj.type == "perception_visual":
                    char = "V"
                elif obj.type == "perception_audio":
                    char = "A"
                elif obj.type == "memory_focus":
                    char = "*"
                elif obj.type == "emotion_trigger":
                    char = "~"

                canvas[sy][sx] = char

        # 转换为字符串
        frame = "\n".join("".join(row) for row in canvas)
        return frame

    def render_state_summary(self) -> str:
        """渲染状态摘要"""
        obj_count = len(self.scene.objects)
        camera = self.scene.camera.position
        lines = [
            f"=== Consciousness Space ===",
            f"Objects: {obj_count}",
            f"Camera: ({camera.x:.1f}, {camera.y:.1f}, {camera.z:.1f})",
            f"Time: {self.scene.time:.1f}s",
            f"===========================",
        ]
        return "\n".join(lines)

    def update(self, dt: float):
        """更新渲染器"""
        self.scene.update(dt)
