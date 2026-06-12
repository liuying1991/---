"""Plasticity rules — Hebbian learning, decay, pruning, hub monopoly protection."""

from __future__ import annotations

from typing import Dict, Set


def hebbian_update(
    conn_strength: float,
    src_fired: bool,
    dst_fired: bool,
    hebb_increment: float,
    max_strength: float = 1.0,
) -> float:
    """Hebbian rule: co-activation strengthens connection (preserves sign)."""
    if src_fired and dst_fired:
        # For excitatory connections: strengthen (more positive)
        # For inhibitory connections: strengthen (more negative)
        if conn_strength > 0:
            return min(conn_strength + hebb_increment, max_strength)
        else:
            return max(conn_strength - hebb_increment, -max_strength)
    return conn_strength


def decay_update(
    conn_strength: float,
    inactive_cycles: int,
    decay_amount: float,
    decay_interval: int = 100,
) -> float:
    """Decay: connections weaken if not co-activated."""
    if inactive_cycles > 0 and inactive_cycles % decay_interval == 0:
        # For excitatory connections: weaken toward 0
        # For inhibitory connections: weaken toward 0 (become less negative)
        if conn_strength > 0:
            return max(conn_strength - decay_amount, 0.0)
        else:
            return min(conn_strength + decay_amount, 0.0)
    return conn_strength


def update_plasticity(network, cycle: int, stage_config):
    """
    Apply plasticity rules to all connections.
    
    1. Hebbian enhancement: both endpoints fired → strengthen
    2. Steady decay: N cycles without co-activation → weaken
    3. Pruning: strength < threshold AND inactive > max → remove
    4. Hub monopoly protection: hub connections > 5% global → lock plasticity
    """
    conn_rules = network.config.connection
    prune_threshold = conn_rules.prune_threshold if stage_config.pruning else 0.0
    prune_inactive = conn_rules.prune_inactive_cycles
    
    nodes_to_prune = []  # (node_id, neighbor_id)

    for node_id, node in network.nodes.items():
        if node.plasticity < 0.01:
            continue
            
        # Skip if energy too low
        base_meta = network.config.initial.base_metabolism
        if node.energy < base_meta * 0.1:
            continue

        fired_this_cycle = (node.last_activation_cycle == cycle)

        neighbors_to_remove = []
        for neighbor_id, weight in list(node.connections.items()):
            neighbor = network.nodes.get(neighbor_id)
            if neighbor is None:
                neighbors_to_remove.append(neighbor_id)
                continue

            neighbor_fired = (neighbor.last_activation_cycle == cycle)
            
            # Inactive cycles tracking
            inactive = cycle - max(node.last_activation_cycle, neighbor.last_activation_cycle)
            
            # Hebbian update
            new_weight = hebbian_update(
                weight, fired_this_cycle, neighbor_fired,
                conn_rules.hebb_increment * node.plasticity
            )
            
            # Decay update
            new_weight = decay_update(
                new_weight, inactive,
                conn_rules.decay_amount * node.plasticity,
                conn_rules.decay_interval
            )
            
            node.connections[neighbor_id] = new_weight
            
            # Check pruning
            if stage_config.pruning:
                if new_weight < prune_threshold and inactive > prune_inactive:
                    neighbors_to_remove.append(neighbor_id)

        # Remove pruned neighbors
        for nid in neighbors_to_remove:
            node.connections.pop(nid, None)
            # Also remove reciprocal connection
            neighbor = network.nodes.get(nid)
            if neighbor and node_id in neighbor.connections:
                del neighbor.connections[node_id]

    # Hub monopoly protection
    _protect_hub_monopoly(network)


def _protect_hub_monopoly(network):
    """
    Check if any hub's connections exceed 5% of global total.
    If so, permanently lock plasticity to 0.01.
    """
    threshold = network.config.connection.hub_monopoly_threshold
    total_connections = network.get_total_connections()
    if total_connections == 0:
        return
    
    from notion.notion_cell import NotionType
    hubs = network.get_nodes_by_type(NotionType.HUB)
    
    for hub in hubs:
        hub_ratio = len(hub.connections) / max(total_connections, 1)
        if hub_ratio >= threshold:
            hub.plasticity = 0.01  # Lock plasticity
