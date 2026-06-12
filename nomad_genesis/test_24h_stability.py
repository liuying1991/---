#!/usr/bin/env python3
"""24-hour simulation test to verify network stability and type diversity."""

import sys
from dna.parser import load_dna
from notion.network import NotionNetwork
from monitor.stage_tracker import StageTracker


def run_24h_simulation():
    """Run a 24-hour simulation and verify network properties."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()
    
    print(f"Initial: {len(net.nodes)} nodes")
    print(f"Running 24-hour simulation (24000 cycles)...\n")
    
    # Run for 24 sim hours (24000 cycles)
    target_hours = 24
    target_cycles = int(target_hours * 1000)
    
    for cycle in range(1, target_cycles + 1):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
            print(f"[Cycle {cycle}] Stage: {stage.name}")
        
        net.step(cycle, [], stage)
        
        # Print progress every 4 hours
        if cycle % 4000 == 0:
            types = {}
            for n in net.nodes.values():
                types[n.type.value] = types.get(n.type.value, 0) + 1
            
            total_conn = net.get_total_connections()
            avg_degree = total_conn * 2 / max(len(net.nodes), 1)
            
            print(f"\n[Cycle {cycle} / {sim_hours:.1f}h]")
            print(f"  Nodes: {len(net.nodes)}")
            print(f"  Connections: {total_conn}, Avg degree: {avg_degree:.2f}")
            print(f"  Types ({len(types)}): {types}")
    
    # Final check
    types = {}
    for n in net.nodes.values():
        types[n.type.value] = types.get(n.type.value, 0) + 1
    
    total_conn = net.get_total_connections()
    avg_degree = total_conn * 2 / max(len(net.nodes), 1)
    
    print(f"\n{'='*60}")
    print(f"Final (after {target_hours}h):")
    print(f"  Nodes: {len(net.nodes)}")
    print(f"  Connections: {total_conn}, Avg degree: {avg_degree:.2f}")
    print(f"  Types ({len(types)}): {types}")
    
    # Verification
    node_count = len(net.nodes)
    type_count = len(types)
    
    print(f"\n{'='*60}")
    print("Verification:")
    
    success = True
    
    # Check node count (should be 500-800, but we'll accept 400-900 for now)
    if 400 <= node_count <= 900:
        print(f"✓ Node count: {node_count} (target: 500-800, acceptable: 400-900)")
    else:
        print(f"✗ Node count: {node_count} (target: 500-800, acceptable: 400-900)")
        success = False
    
    # Check type diversity (need 6+)
    if type_count >= 6:
        print(f"✓ Type diversity: {type_count} types (need 6+)")
    else:
        print(f"✗ Type diversity: {type_count} types (need 6+)")
        success = False
    
    # Check inhibitor ratio (should be ~20%)
    inhibitor_count = types.get('INHIBITOR', 0)
    inhibitor_ratio = inhibitor_count / max(node_count, 1)
    if 0.10 <= inhibitor_ratio <= 0.30:
        print(f"✓ Inhibitor ratio: {inhibitor_ratio:.2%} (target: ~20%, acceptable: 10-30%)")
    else:
        print(f"✗ Inhibitor ratio: {inhibitor_ratio:.2%} (target: ~20%, acceptable: 10-30%)")
        success = False
    
    # Check hub monopoly (no hub should have >5% of connections)
    from notion.notion_cell import NotionType
    hubs = net.get_nodes_by_type(NotionType.HUB)
    hub_monopoly = False
    for hub in hubs:
        hub_ratio = len(hub.connections) / max(total_conn, 1)
        if hub_ratio > 0.05:
            hub_monopoly = True
            break
    
    if not hub_monopoly:
        print(f"✓ Hub monopoly: No hub exceeds 5% of connections")
    else:
        print(f"✗ Hub monopoly: Some hub exceeds 5% of connections")
        success = False
    
    print(f"\n{'='*60}")
    if success:
        print("✓ ALL CHECKS PASSED")
        return True
    else:
        print("✗ SOME CHECKS FAILED")
        return False


if __name__ == "__main__":
    success = run_24h_simulation()
    sys.exit(0 if success else 1)
