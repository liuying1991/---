"""Metabolism — energy metabolism constraints for the network.

Note: metabolism logic is now integrated into NotionNetwork._update_metabolism().
This module provides standalone utility functions for external use.
"""

from __future__ import annotations


def calculate_metabolic_cost(node, base_metabolism: float, fired: bool = False,
                              divided: bool = False) -> float:
    """
    Calculate the metabolic energy cost for a node this cycle.
    
    Returns total energy to subtract.
    """
    cost = base_metabolism * 0.01  # Base cost
    
    if fired:
        cost += base_metabolism * 0.02  # 2x extra for firing
    
    if divided:
        cost += base_metabolism * 0.1  # 10x extra for division
    
    return cost


def apply_energy_effects(node, energy_ratio: float):
    """
    Apply energy-dependent effects to a node.
    
    energy_ratio = energy / base_metabolism
    """
    if energy_ratio < 0.5:
        node.plasticity *= 0.5
    
    if energy_ratio < 0.1:
        # Cannot fire, cannot learn
        node.activation = 0.0
        node.plasticity *= 0.1
    
    return energy_ratio <= 0  # Dead


def check_apoptosis(node, isolation_threshold: float = 0.0) -> bool:
    """
    Check if a node should undergo apoptosis (cell death).
    
    Conditions: energy <= 0 AND isolated (no connections)
    """
    if node.energy <= 0 and len(node.connections) == 0:
        return True
    return False
