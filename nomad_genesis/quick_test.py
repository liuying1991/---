#!/usr/bin/env python3
"""Quick test to check current differentiation status."""

import sys
from dna.parser import load_dna
from notion.network import NotionNetwork
from monitor.stage_tracker import StageTracker


def quick_differentiation_test():
    """Run a short simulation to check type diversity."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()
    
    print(f"Initial: {len(net.nodes)} nodes")
    print(f"Config - base_prob: {config.connection.base_prob}")
    print(f"Config - idle_cycles for OSCILLATOR: {config.differentiation.oscillator.idle_cycles}")
    print(f"Config - inhibitory_cycles for GATE: {config.differentiation.gate.inhibitory_cycles}")
    
    # Run for 5 sim hours (5000 cycles)
    for cycle in range(1, 5001):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
        
        net.step(cycle, [], stage)
    
    # Check final state
    types = {}
    for n in net.nodes.values():
        types[n.type.value] = types.get(n.type.value, 0) + 1
    
    print(f"\n{'='*60}")
    print(f"After 5h: {len(net.nodes)} nodes, {net.get_total_connections()} connections")
    print(f"Types ({len(types)}): {types}")
    
    # Check specific conditions for missing types
    print(f"\nDiagnostic:")
    stem_nodes = [n for n in net.nodes.values() if n.type.value == 'STEM']
    if stem_nodes:
        sample = stem_nodes[0]
        print(f"  STEM sample - idle_cycles: {sample.idle_cycles}, energy: {sample.energy:.2f}")
        print(f"  OSCILLATOR needs: idle > {config.differentiation.oscillator.idle_cycles}, energy > {config.initial.base_metabolism * config.differentiation.oscillator.energy_multiplier:.2f}")
    
    return len(types)

if __name__ == "__main__":
    quick_differentiation_test()
