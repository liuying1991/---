"""Connection establishment — vector similarity-weighted connection creation."""

from __future__ import annotations

import random
import numpy as np

from notion.notion_cell import NotionType


def establish_connections(network, stage_config):
    """
    Establish connections for unconnected node pairs within spatial range.

    Algorithm:
      1. For all node pairs (i, j) within connection_radius
      2. Compute cosine similarity s = cosine(node_i.vector, node_j.vector)
      3. Connection prob P = s × base_prob (if s < 0, P = min_prob)
      4. Randomly decide whether to connect based on P
      5. Initial connection strength = 0.1 (weak connection for Hebbian strengthening)

    Performance: Cap attempts per cycle and only process under-connected nodes.
    """
    conn_rules = network.config.connection
    radius = network.config.initial.connection_radius * stage_config.connection_radius_mult

    new_connections = 0
    max_attempts = 500  # Cap total attempts per cycle
    attempts = 0

    # Only process nodes with few connections (most in need)
    nodes_list = [n for n in network.nodes.values() if len(n.connections) < 20]
    random.shuffle(nodes_list)

    for node_a in nodes_list:
        if attempts >= max_attempts:
            break

        nearby_ids = network.spatial_hash.get_nearby_entities(
            node_a.position, radius
        )
        random.shuffle(nearby_ids)

        for neighbor_id in nearby_ids:
            if attempts >= max_attempts:
                break

            if neighbor_id <= node_a.id:
                continue
            if neighbor_id in node_a.connections:
                continue

            attempts += 1
            node_b = network.nodes.get(neighbor_id)
            if node_b is None:
                continue

            # Skip if too many connections already
            if len(node_b.connections) > 50:
                continue

            # Compute cosine similarity
            sim = _cosine_similarity(node_a.vector, node_b.vector)

            # Connection probability
            if sim > 0:
                prob = sim * conn_rules.base_prob
            else:
                prob = conn_rules.min_prob

            # Clamp probability
            prob = min(prob, 0.5)

            if random.random() < prob:
                # Increased initial connection strength for better signal propagation
                strength = 0.25  # Was 0.1, increased to improve network activity
                # Inhibitor connections start negative
                if node_b.type == NotionType.INHIBITOR:
                    strength = -0.25
                elif node_a.type == NotionType.INHIBITOR:
                    strength = -0.25

                node_a.connections[neighbor_id] = strength
                node_b.connections[node_a.id] = strength
                new_connections += 1

    return new_connections


def _cosine_similarity(a, b):
    """Cosine similarity between two numpy arrays."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
