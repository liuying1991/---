"""Oscillator rhythm management."""

from __future__ import annotations

import random


def update_oscillators(network, cycle: int):
    """
    Update all oscillator nodes.
    Each oscillator has an internal phase counter.
    When phase reaches period, it fires fully and resets.
    """
    from .notion_cell import NotionType
    
    for node in network.get_nodes_by_type(NotionType.OSCILLATOR):
        if node.oscillator_period is None or node.oscillator_period <= 0:
            node.oscillator_period = random.randint(10, 200)
            node.oscillator_phase = 0
            
        node.oscillator_phase = (node.oscillator_phase + 1) % node.oscillator_period
        
        if node.oscillator_phase == 0:
            node.activation = 1.0
            node.potential = 1.0  # Ensure it will propagate
