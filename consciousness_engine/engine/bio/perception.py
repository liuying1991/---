"""
PerceptionSystem - 感知系统
视觉/听觉/触觉 → 神经信号
"""
import math
import numpy as np
from typing import Dict, Any, List, Tuple
from engine.physics.space import Vector3


class PerceptionSystem:
    """感知系统"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bio_config = config.get("bio", {})
        self.perception_config = self.bio_config.get("perception", {})

        self.visual_range = self.perception_config.get("visual_range", 50)
        self.audio_range = self.perception_config.get("audio_range", 30)
        self.tactile_range = self.perception_config.get("tactile_range", 2)

    def perceive_space(self, space, position: Vector3, direction: Vector3,
                      fov: float = 90.0) -> List[Dict[str, Any]]:
        """
        感知空间中的实体（视觉）
        返回感知列表
        """
        # 获取视野内实体
        visible = space.entities_in_view(position, direction, fov)

        perceptions = []
        for entity_id, dist, angle in visible:
            if dist <= self.visual_range:
                entity_data = space.entities.get(entity_id, {})
                perception = {
                    "modality": "visual",
                    "entity_id": entity_id,
                    "distance": dist,
                    "angle": angle,
                    "properties": entity_data.get("properties", {}),
                    "clarity": 1.0 - (dist / self.visual_range),
                }
                perceptions.append(perception)

        return perceptions

    def perceive_audio(self, space, position: Vector3,
                      sound_sources: List[Tuple[Vector3, str, float]]
                      ) -> List[Dict[str, Any]]:
        """
        感知声音
        sound_sources: [(position, sound_type, volume)]
        """
        perceptions = []
        for source_pos, sound_type, volume in sound_sources:
            dist = space.distance(position, source_pos)
            if dist <= self.audio_range:
                perception = {
                    "modality": "audio",
                    "sound_type": sound_type,
                    "distance": dist,
                    "volume": volume * (1.0 - dist / self.audio_range),
                }
                perceptions.append(perception)

        return perceptions

    def perceive_tactile(self, space, position: Vector3) -> List[Dict[str, Any]]:
        """感知触觉（附近接触的实体）"""
        nearby = space.entities_in_range(position, self.tactile_range)
        perceptions = []
        for entity_id, dist in nearby:
            if dist <= self.tactile_range:
                perception = {
                    "modality": "tactile",
                    "entity_id": entity_id,
                    "distance": dist,
                    "pressure": 1.0 - (dist / self.tactile_range),
                }
                perceptions.append(perception)

        return perceptions

    def perceive_all(self, space, position: Vector3, direction: Vector3,
                    sound_sources: List[Tuple[Vector3, str, float]] = None) -> List[Dict[str, Any]]:
        """综合所有感知"""
        perceptions = []
        perceptions.extend(self.perceive_space(space, position, direction))
        perceptions.extend(self.perceive_tactile(space, position))

        if sound_sources:
            perceptions.extend(self.perceive_audio(space, position, sound_sources))

        return perceptions

    def perception_to_text(self, perceptions: List[Dict[str, Any]]) -> str:
        """将感知转换为文本描述（用于编码到记忆）"""
        if not perceptions:
            return "没有感知到任何事物"

        descriptions = []
        for p in perceptions:
            if p["modality"] == "visual":
                entity_id = p["entity_id"]
                dist = p["distance"]
                props = p.get("properties", {})
                desc = f"看到{entity_id}在{dist:.1f}米外"
                if props:
                    desc += f"，属性: {props}"
                descriptions.append(desc)

            elif p["modality"] == "audio":
                descriptions.append(f"听到{p['sound_type']}，音量{p['volume']:.2f}")

            elif p["modality"] == "tactile":
                descriptions.append(f"感受到{p['entity_id']}接触，压力{p['pressure']:.2f}")

        return "；".join(descriptions)

    def process_visual(self, object_id: str, object_type: str,
                      distance: float, position: Tuple[float, float, float]) -> Dict[str, Any]:
        """
        处理视觉感知
        返回感知数据字典
        """
        if distance > self.visual_range:
            return None

        salience = max(0, 1.0 - (distance / self.visual_range))

        return {
            "type": "visual",
            "object_id": object_id,
            "object_type": object_type,
            "distance": distance,
            "position": position,
            "salience": salience,
            "description": f"看到{object_type}物体{object_id}在{distance:.1f}米处",
        }

    def process_audio(self, object_id: str, sound_type: str,
                     distance: float) -> Dict[str, Any]:
        """
        处理听觉感知
        返回感知数据字典
        """
        if distance > self.audio_range:
            return None

        salience = max(0, 1.0 - (distance / self.audio_range))

        return {
            "type": "audio",
            "object_id": object_id,
            "sound_type": sound_type,
            "distance": distance,
            "salience": salience,
            "description": f"听到{object_id}发出{sound_type}声音",
        }

    def process_tactile(self, object_id: str, distance: float) -> Dict[str, Any]:
        """
        处理触觉感知
        返回感知数据字典
        """
        if distance > self.tactile_range:
            return None

        pressure = max(0, 1.0 - (distance / self.tactile_range))

        return {
            "type": "tactile",
            "object_id": object_id,
            "distance": distance,
            "salience": pressure,
            "description": f"感受到{object_id}接触",
        }
