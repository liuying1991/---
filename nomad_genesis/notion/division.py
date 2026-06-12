"""Division rules — cell division with mutation."""

from __future__ import annotations

import random
import numpy as np
from typing import List

from notion.notion_cell import Notion, NotionType


def process_divisions(network, cycle: int):
    """
    Traverse all nodes, execute division for those meeting conditions:
      1. energy > division_threshold
      2. local connection density < max_local_density (fraction of possible connections used)
      3. division_count < max_divisions

    Division process:
      - Parent keeps type, child starts as STEM
      - Child vector = parent vector + N(0, mutation_sigma)
      - Child placed near parent with random offset
      - Parent energy halved, child gets other half
    """
    division_rules = network.config.division
    new_nodes: List[Notion] = []

    # Collect candidates
    candidates = []
    for node_id, node in list(network.nodes.items()):
        if not node.can_divide(division_rules):
            continue

        # Check local density: fraction of nearby nodes that are connected
        nearby = network.spatial_hash.get_nearby_entities(
            node.position, network.config.initial.connection_radius
        )
        nearby_count = len(nearby)
        if nearby_count > 0:
            local_density = len(node.connections) / nearby_count
        else:
            local_density = 0.0

        if local_density < division_rules.max_local_density:
            candidates.append(node)

    # Cap divisions per cycle to prevent explosion
    if len(candidates) > 5:
        candidates = random.sample(candidates, 5)

    for parent in candidates:
        # Create child
        mutation_sigma = division_rules.mutation_sigma
        child_vector = parent.vector + np.random.randn(len(parent.vector)) * mutation_sigma

        # Random position offset near parent
        offset = np.random.randn(3) * 2.0
        child_position = parent.position + offset

        child = Notion.create_stem(
            vector_dim=len(parent.vector),
            position=child_position,
            base_metabolism=network.config.initial.base_metabolism,
            born_at_stage=network.stage_tracker.get_current_stage().name if network.stage_tracker else "embryonic",
        )

        # Split energy
        parent.energy /= 2.0
        child.energy = parent.energy

        # Inherit some connections from parent
        shared_neighbors = list(parent.connections.keys())
        if shared_neighbors:
            to_inherit = random.sample(shared_neighbors,
                                       min(len(shared_neighbors), max(1, len(shared_neighbors) // 3)))
            for nid in to_inherit:
                child.connections[nid] = parent.connections[nid] * 0.5

        parent.division_count += 1
        new_nodes.append(child)

    # Add all new nodes
    for child in new_nodes:
        network.add_node(child)

    return len(new_nodes)
