"""Resource Distribution — energy sources in the virtual world."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


@dataclass
class ResourcePoint:
    id: str
    position: np.ndarray  # (x, y, z)
    amount: float          # Remaining amount
    regen_rate: float      # Regeneration rate per tick
    max_amount: float      # Maximum capacity


class ResourceManager:
    """Manage resource points in the 3D world."""

    def __init__(self):
        self.resources: Dict[str, ResourcePoint] = {}

    def spawn_resource(self, x: float, y: float, z: float,
                       amount: float, regen_rate: float,
                       max_amount: Optional[float] = None) -> str:
        """Spawn a new resource point. Returns resource ID."""
        rid = str(uuid.uuid4())[:8]
        if max_amount is None:
            max_amount = amount * 2.0
        pos = np.array([x, y, z], dtype=np.float64)
        self.resources[rid] = ResourcePoint(
            id=rid, position=pos, amount=amount,
            regen_rate=regen_rate, max_amount=max_amount,
        )
        return rid

    def consume(self, resource_id: str, amount: float) -> float:
        """Consume from a resource point. Returns actual amount obtained."""
        res = self.resources.get(resource_id)
        if res is None:
            return 0.0
        actual = min(amount, res.amount)
        res.amount -= actual
        return actual

    def get_visible_resources(self, observer_pos: np.ndarray,
                               vision_radius: float) -> List[ResourcePoint]:
        """Get all resource points within vision radius."""
        visible = []
        radius_sq = vision_radius * vision_radius
        for res in self.resources.values():
            dist_sq = np.sum((res.position - observer_pos) ** 2)
            if dist_sq <= radius_sq:
                visible.append(res)
        return visible

    def tick(self):
        """Regenerate resources each tick."""
        for res in self.resources.values():
            if res.amount < res.max_amount:
                res.amount = min(res.max_amount, res.amount + res.regen_rate)

    def remove_depleted(self, threshold: float = 0.0):
        """Remove resource points that are fully depleted."""
        depleted = [rid for rid, res in self.resources.items()
                    if res.amount <= threshold]
        for rid in depleted:
            del self.resources[rid]

    def spawn_cluster(self, center: np.ndarray, count: int,
                      spread: float, amount_range: tuple,
                      regen_range: tuple):
        """Spawn a cluster of resources around a center point."""
        for _ in range(count):
            offset = np.random.randn(3) * spread
            pos = center + offset
            amount = np.random.uniform(*amount_range)
            regen = np.random.uniform(*regen_range)
            self.spawn_resource(pos[0], pos[1], pos[2], amount, regen)
