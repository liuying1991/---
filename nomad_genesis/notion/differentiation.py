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
        # STEM CELL PRESERVATION — Check FIRST before any other logic
        # Count stem cells
        stem_count = sum(1 for n in network.nodes.values() if n.type == NotionType.STEM)
        
        # CRITICAL: If stem cells are below 30, almost never differentiate
        if stem_count < 30:
            if random.random() < 0.999:  # 99.9% skip rate
                return None
        
        # Only differentiate after network has grown sufficiently
        # Check both node age and network size
        node_age = network._cycle - node.birth_cycle
        network_size = len(network.nodes)
        
        # Don't differentiate if network is still small (need to grow first)
        # Target: 500-800 nodes, so start differentiation around 500 nodes
        if network_size < 500:
            return None
        
        # Also require minimum age
        if node_age < 100:
            return None
        
        # Calculate current type distribution
        type_counts = {}
        for n in network.nodes.values():
            type_counts[n.type] = type_counts.get(n.type, 0) + 1
        total_nodes = len(network.nodes)
        
        # Gradual differentiation: probability increases as network grows
        # At 500 nodes: ~1% chance; at 700 nodes: ~15% chance; at 800 nodes: ~35% chance
        if total_nodes < 800:
            diff_prob = 0.01 + 0.34 * ((total_nodes - 500) / 300.0) ** 1.5
            diff_prob = max(0.01, min(0.35, diff_prob))
            if random.random() > diff_prob:
                return None
        
        # Additional ratio-based preservation for low stem ratios
        stem_ratio = stem_count / total_nodes
        if stem_ratio < 0.03:  # Below 3%
            if random.random() < 0.995:  # 99.5% skip
                return None
        
        # Check differentiation in priority order (rarer types first)
        # This ensures diversity instead of all nodes becoming SENSOR
        
        # 1. → OSCILLATOR: high energy with moderate connections (rare, ~5%)
        # Relaxed: lower energy threshold and add random fallback
        osc_rules = diff_rules.oscillator
        if type_counts.get(NotionType.OSCILLATOR, 0) < total_nodes * 0.08:
            # Primary path: high energy + moderate connectivity
            if (node.energy > network.config.initial.base_metabolism * 1.5 and
                    node.degree < 25 and node.degree >= 3):
                return NotionType.OSCILLATOR
            # Fallback: random probability for older nodes with some connections
            elif node.degree >= 5 and random.random() < 0.005:  # 0.5% chance
                return NotionType.OSCILLATOR
        
        # 2. → GATE: high inhibitory connections OR random probability (rare, ~8%)
        # Boosted: increase random probability from 0.5% to 1.5%
        if type_counts.get(NotionType.GATE, 0) < total_nodes * 0.12:
            # Check if receiving many inhibitory signals
            inhibitory_count = sum(1 for w in node.connections.values() if w < 0)
            if inhibitory_count >= 2 or random.random() < 0.015:  # 1.5% chance per cycle
                return NotionType.GATE
        
        # 3. → HUB: slightly higher degree than neighbors (rare, ~10%)
        # Relaxed: lower degree_ratio from 1.3 to 1.1
        if type_counts.get(NotionType.HUB, 0) < total_nodes * 0.15:
            neighbor_avg_degree = _neighbor_avg_degree(node, network)
            if neighbor_avg_degree > 0 and node.degree > neighbor_avg_degree * 1.1:
                return NotionType.HUB
        
        # 4. → MEMORY: high activation intensity (rare, ~10%)
        # Relaxed: lower intensity_ratio from 2.5 to 1.5
        if type_counts.get(NotionType.MEMORY, 0) < total_nodes * 0.15:
            if global_stats.mean_activation > 0:
                if node.activation > global_stats.mean_activation * 1.5:
                    return NotionType.MEMORY
        
        # 5. → INTERNEURON: enough connections and high activation freq (common, ~30%)
        # Relaxed: lower activation_freq_ratio from 0.8 to 0.5
        if type_counts.get(NotionType.INTERNEURON, 0) < total_nodes * 0.40:
            if (node.degree >= diff_rules.interneuron.min_connections and
                    _activation_freq_ratio(node, global_stats) >= 0.5):
                return NotionType.INTERNEURON
        
        # 6. → PROJECTOR: any cosine similarity with neighbors (rare, ~8%)
        # Boosted: lower threshold from 0.3 to 0.2, increase cap from 15% to 12%
        if type_counts.get(NotionType.PROJECTOR, 0) < total_nodes * 0.12:
            if _has_high_similarity_remote(node, network, 0.2):
                return NotionType.PROJECTOR
            # Fallback: random probability if node has many connections
            elif node.degree >= 10 and random.random() < 0.008:  # 0.8% chance
                return NotionType.PROJECTOR
        
        # 7. → SENSOR: high input signal density (common, ~30%, fallback)
        if type_counts.get(NotionType.SENSOR, 0) < total_nodes * 0.40:
            if node.input_count > 0:
                input_density = node.total_input_signal / node.input_count
                if input_density > diff_rules.sensor.input_density_threshold:
                    return NotionType.SENSOR
    
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
        # Invert ALL connection weights to negative (both directions)
        # First, invert this node's outgoing connections
        for nid in node.connections:
            node.connections[nid] = -abs(node.connections[nid])
            # Also invert the reverse connection in the neighbor
            neighbor = network.nodes.get(nid)
            if neighbor and node.id in neighbor.connections:
                neighbor.connections[node.id] = -abs(neighbor.connections[node.id])
    
    elif new_type == NotionType.GATE:
        node.threshold *= 0.7  # Lower threshold for gate cells to make them more active


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
