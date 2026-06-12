"""Collision Detection — AABB + spatial hash based collision."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


class CollisionDetector:
    """
    Collision detection using spatial hash grid.
    Detects when entities are within threshold distance.
    """

    def __init__(self, space):
        """
        Args:
            space: Space3D instance for position queries.
        """
        self.space = space

    def check_collision(self, entity_a: str, entity_b: str,
                        threshold: float) -> bool:
        """Check if two entities are colliding (distance < threshold)."""
        dist = self.space.distance(entity_a, entity_b)
        return dist < threshold

    def get_collisions(self, threshold: float) -> List[Tuple[str, str]]:
        """
        Get all collision pairs in the world.
        Returns list of (entity_a, entity_b) tuples.
        """
        collisions = []
        checked = set()

        for entity_id in self.space.positions:
            nearby = self.space.get_nearby(entity_id, threshold)
            for other_id in nearby:
                pair = tuple(sorted([entity_id, other_id]))
                if pair not in checked:
                    actual_dist = self.space.distance(entity_id, other_id)
                    if actual_dist < threshold:
                        collisions.append(pair)
                        checked.add(pair)

        return collisions

    def is_within_region(self, position: np.ndarray,
                         region_center: np.ndarray,
                         region_radius: float) -> bool:
        """Check if a position is within a spherical region."""
        dist = np.linalg.norm(position - region_center)
        return dist <= region_radius

    def get_entities_in_region(self, region_center: np.ndarray,
                                region_radius: float) -> List[str]:
        """Get all entities within a spherical region."""
        in_region = []
        radius_sq = region_radius * region_radius
        for eid, pos in self.space.positions.items():
            dist_sq = np.sum((pos - region_center) ** 2)
            if dist_sq <= radius_sq:
                in_region.append(eid)
        return in_region
