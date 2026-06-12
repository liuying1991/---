"""3D Spatial Coordinate System with spatial hashing for fast neighbor lookups."""

from __future__ import annotations

import numpy as np
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class SpatialHashGrid:
    """
    Spatial hash grid for O(1) neighbor lookups.
    Cell size defaults to 10.0 units.
    """

    def __init__(self, cell_size: float = 10.0):
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int, int], List[str]] = defaultdict(list)
        self._entity_cells: Dict[str, Tuple[int, int, int]] = {}

    def _hash(self, pos: np.ndarray) -> Tuple[int, int, int]:
        return (
            int(pos[0] // self.cell_size),
            int(pos[1] // self.cell_size),
            int(pos[2] // self.cell_size),
        )

    def insert(self, entity_id: str, pos: np.ndarray):
        cell = self._hash(pos)
        # Remove from old cell if exists
        if entity_id in self._entity_cells:
            old_cell = self._entity_cells[entity_id]
            if entity_id in self.grid[old_cell]:
                self.grid[old_cell].remove(entity_id)
        # Insert into new cell
        self.grid[cell].append(entity_id)
        self._entity_cells[entity_id] = cell

    def remove(self, entity_id: str):
        if entity_id in self._entity_cells:
            cell = self._entity_cells[entity_id]
            if entity_id in self.grid[cell]:
                self.grid[cell].remove(entity_id)
            del self._entity_cells[entity_id]

    def get_nearby_cells(self, pos: np.ndarray, radius: float) -> List[Tuple[int, int, int]]:
        """Get all grid cells within radius of pos."""
        cell = self._hash(pos)
        cells_radius = int(np.ceil(radius / self.cell_size))
        nearby = []
        for dx in range(-cells_radius, cells_radius + 1):
            for dy in range(-cells_radius, cells_radius + 1):
                for dz in range(-cells_radius, cells_radius + 1):
                    nearby.append((cell[0] + dx, cell[1] + dy, cell[2] + dz))
        return nearby

    def get_nearby_entities(self, pos: np.ndarray, radius: float) -> List[str]:
        """Get all entity IDs within radius of pos."""
        radius_sq = radius * radius
        nearby = []
        for cell in self.get_nearby_cells(pos, radius):
            for eid in self.grid.get(cell, []):
                nearby.append(eid)
        return nearby


class Space3D:
    """
    3D continuous space management.
    """

    def __init__(self, cell_size: float = 10.0):
        self.positions: Dict[str, np.ndarray] = {}
        self.spatial_hash = SpatialHashGrid(cell_size)

    def set_position(self, entity_id: str, x: float, y: float, z: float):
        pos = np.array([x, y, z], dtype=np.float64)
        self.positions[entity_id] = pos
        self.spatial_hash.insert(entity_id, pos)

    def get_position(self, entity_id: str) -> Optional[np.ndarray]:
        return self.positions.get(entity_id)

    def remove_entity(self, entity_id: str):
        self.positions.pop(entity_id, None)
        self.spatial_hash.remove(entity_id)

    def distance(self, entity_a: str, entity_b: str) -> float:
        pos_a = self.positions.get(entity_a)
        pos_b = self.positions.get(entity_b)
        if pos_a is None or pos_b is None:
            return float('inf')
        return float(np.linalg.norm(pos_a - pos_b))

    def get_nearby(self, entity_id: str, radius: float) -> List[str]:
        pos = self.positions.get(entity_id)
        if pos is None:
            return []
        nearby = self.spatial_hash.get_nearby_entities(pos, radius)
        nearby = [eid for eid in nearby if eid != entity_id]
        return nearby

    def move_toward(self, entity_id: str, target_x: float, target_y: float,
                    target_z: float, speed: float):
        pos = self.positions.get(entity_id)
        if pos is None:
            return
        target = np.array([target_x, target_y, target_z], dtype=np.float64)
        direction = target - pos
        dist = np.linalg.norm(direction)
        if dist > 0:
            direction = direction / dist
            new_pos = pos + direction * min(speed, dist)
            self.set_position(entity_id, new_pos[0], new_pos[1], new_pos[2])
