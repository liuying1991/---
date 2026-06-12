"""Differentiation logic — 9 types of cell specialization."""

from __future__ import annotations

import random
import numpy as np
from typing import Optional

from notion.notion_cell import Notion, NotionType


def check_differentiation(node: Notion, network) -> Optional[NotionType]:
    """
    Determine differentiation direction based on node state and global network state.
    Check order (first match wins):

    1. STEM → MEMORY:  single activation intensity > global mean × intensity_ratio
    2. STEM → OSCILLATOR: idle_cycles > 200 AND energy > survival_threshold × 3
    3. STEM → GATE:     consecutive inhibitory signals > 100 cycles
    4. STEM → SENSOR:   input signal density > input_density_threshold
    5. STEM → INTERNEURON: connections > 3 AND activation freq > global mean
    6. STEM → HUB:      degree > neighbor mean × degree_ratio
    7. STEM → PROJECTOR: vector cosine similarity to another region > 0.8
    8. INTERNEURON → INHIBITOR: random prob conversion_prob (20%)

    Returns new type or None if no differentiation.
    """
    diff_rules = network.config.differentiation
    global_stats = network.global_stats
    
    if node.type == NotionType.STEM:
        # Only differentiate after some maturation (idle cycles > threshold)
        # This ensures STEM cells have time to divide before specializing
        if node.idle_cycles < 100:
            return None
        
        # 1. → MEMORY: high activation intensity
        if global_stats.mean_activation > 0:
            intensity_ratio = diff_rules.memory.intensity_ratio
            if node.activation > global_stats.mean_activation * intensity_ratio:
                return NotionType.MEMORY
        
        # 2. → OSCILLATOR: idle with high energy AND can no longer divide
        osc_rules = diff_rules.oscillator
        if (node.idle_cycles > osc_rules.idle_cycles and
                node.energy > network.config.initial.base_metabolism * osc_rules.energy_multiplier and
                node.division_count >= network.config.division.max_divisions):
            return NotionType.OSCILLATOR
        
        # 3. → GATE: consecutive inhibitory signals
        if node.inhibitory_cycles > diff_rules.gate.inhibitory_cycles:
            return NotionType.GATE
        
        # 4. → SENSOR: high input signal density
        if node.input_count > 0:
            input_density = node.total_input_signal / node.input_count
            if input_density > diff_rules.sensor.input_density_threshold:
                return NotionType.SENSOR
        
        # 5. → INTERNEURON: enough connections and high activation freq
        if (node.degree >= diff_rules.interneuron.min_connections and
                _activation_freq_ratio(node, global_stats) >= diff_rules.interneuron.activation_freq_ratio):
            return NotionType.INTERNEURON
        
        # 6. → HUB: degree much higher than neighbors
        neighbor_avg_degree = _neighbor_avg_degree(node, network)
        if neighbor_avg_degree > 0 and node.degree > neighbor_avg_degree * diff_rules.hub.degree_ratio:
            return NotionType.HUB
        
        # 7. → PROJECTOR: cosine similarity with distant nodes
        if _has_high_similarity_remote(node, network, diff_rules.projector.cosine_similarity_threshold):
            return NotionType.PROJECTOR
    
    elif node.type == NotionType.INTERNEURON:
        # 8. → INHIBITOR: random conversion (only if not enough inhibitors exist)
        inhibitor_count = len(network.get_nodes_by_type(NotionType.INHIBITOR))
        total = len(network.nodes)
        inhibitor_ratio = inhibitor_count / max(total, 1)
        # Cap inhibitor ratio at ~20%
        if inhibitor_ratio < 0.20 and random.random() < diff_rules.inhibitor.conversion_prob * 0.01:
            return NotionType.INHIBITOR
    
    return None


def apply_differentiation(node: Notion, new_type: NotionType, network):
    """Apply differentiation to a node."""
    old_type = node.type
    node.type = new_type
    
    # Adjust plasticity based on type
    type_plasticity = {
        NotionType.SENSOR: 0.3,
        NotionType.INTERNEURON: 0.5,
        NotionType.INHIBITOR: 0.4,
        NotionType.OSCILLATOR: 0.2,
        NotionType.PROJECTOR: 0.3,
        NotionType.HUB: 0.1,
        NotionType.MEMORY: 0.15,
        NotionType.GATE: 0.2,
    }
    node.plasticity = type_plasticity.get(new_type, node.plasticity)
    
    # Type-specific initialization
    if new_type == NotionType.OSCILLATOR:
        osc_rules = network.config.differentiation.oscillator
        node.oscillator_period = random.randint(
            osc_rules.period_range[0], osc_rules.period_range[1]
        )
        node.oscillator_phase = random.randint(0, node.oscillator_period - 1)
    
    elif new_type == NotionType.INHIBITOR:
        # Invert connection weights to negative
        for nid in node.connections:
            node.connections[nid] = -abs(node.connections[nid])
    
    elif new_type == NotionType.GATE:
        node.threshold *= 1.5  # Higher threshold for gate cells


def _activation_freq_ratio(node: Notion, global_stats) -> float:
    """Ratio of node's activation frequency to global mean."""
    if not node.activation_history:
        return 0.0
    node_freq = sum(node.activation_history[-100:]) / max(len(node.activation_history[-100:]), 1)
    if global_stats.mean_activation <= 0:
        return 0.0
    return node_freq / global_stats.mean_activation


def _neighbor_avg_degree(node: Notion, network) -> float:
    """Average degree of this node's neighbors."""
    if not node.connections:
        return 0.0
    total = 0
    count = 0
    for nid in node.connections:
        neighbor = network.nodes.get(nid)
        if neighbor:
            total += neighbor.degree
            count += 1
    return total / max(count, 1)


def _has_high_similarity_remote(node: Notion, network, threshold: float) -> bool:
    """Check if node has high cosine similarity with nodes in a different region."""
    if not node.connections:
        return False
    
    # Sample some neighbors to check similarity
    sample_ids = list(node.connections.keys())[:10]
    for nid in sample_ids:
        neighbor = network.nodes.get(nid)
        if neighbor is None:
            continue
        # Check distance — should be in different region (far away)
        dist = np.linalg.norm(node.position - neighbor.position)
        if dist > 15.0:  # Far enough to be "different region"
            sim = _cosine_similarity(node.vector, neighbor.vector)
            if sim > threshold:
                return True
    return False


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
