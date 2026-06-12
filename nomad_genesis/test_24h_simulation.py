#!/usr/bin/env python3
"""Longer simulation to test type diversity."""

import sys
from dna.parser import load_dna
from notion.network import NotionNetwork
from monitor.stage_tracker import StageTracker


def test_longer_simulation():
    """Run a longer simulation (24h) to see if more types emerge."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()
    
    print(f"Initial: {len(net.nodes)} nodes")
    
    # Run for 24 sim hours (24000 cycles)
    target_hours = 24
    target_cycles = int(target_hours * 1000)
    
    last_print_cycle = 0
    for cycle in range(1, target_cycles + 1):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
            print(f"\n[Cycle {cycle}] Stage advanced to: {stage.name}")
        
        net.step(cycle, [], stage)
        
        # Print stats every 2 hours
        if cycle % 2000 == 0:
            types = {}
            for n in net.nodes.values():
                types[n.type.value] = types.get(n.type.value, 0) + 1
            
            total_conn = net.get_total_connections()
            avg_degree = total_conn * 2 / max(len(net.nodes), 1)
            
            print(f"\n[Cycle {cycle} / {sim_hours:.1f}h]")
            print(f"  Nodes: {len(net.nodes)}")
            print(f"  Connections: {total_conn}, Avg degree: {avg_degree:.2f}")
            print(f"  Stage: {stage.name}")
            print(f"  Types: {types}")
            
            # Check if we have 6+ types
            if len(types) >= 6:
                print(f"\n✓ SUCCESS: {len(types)} types achieved!")
                return True
            
            last_print_cycle = cycle
    
    # Final check
    types = {}
    for n in net.nodes.values():
        types[n.type.value] = types.get(n.type.value, 0) + 1
    
    print(f"\n{'='*60}")
    print(f"Final (after {target_hours}h): {len(net.nodes)} nodes")
    print(f"Types: {types}")
    print(f"Type count: {len(types)}")
    
    if len(types) >= 6:
        print(f"\n✓ SUCCESS: {len(types)} types achieved!")
        return True
    else:
        print(f"\n✗ FAILED: Only {len(types)} types (need 6+)")
        return False


if __name__ == "__main__":
    success = test_longer_simulation()
    sys.exit(0 if success else 1)
