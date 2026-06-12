#!/usr/bin/env python3
"""Diagnostic test to check network growth and differentiation status."""

import sys
sys.path.insert(0, '/workspace/nomad_genesis')

from dna.parser import load_dna
from notion.network import NotionNetwork
from monitor.stage_tracker import StageTracker
from notion.notion_cell import NotionType

def run_diagnostic():
    print("Loading DNA config...")
    config = load_dna('/workspace/nomad_genesis/dna/seeds/baseline_v0.2.yaml')
    
    print("Initializing network...")
    stage_tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker)
    net.init_stem_cells()
    
    print(f"Initial nodes: {len(net.nodes)}")
    
    # Run for 24 hours (24000 cycles)
    target_cycles = 24000
    checkpoint_interval = 2000
    
    for cycle in range(target_cycles):
        sim_hours = cycle / 1000.0
        stage = stage_tracker.get_current_stage()
        stage_tracker.set_cycle_info(cycle, sim_hours)
        net.step(cycle, [], stage)
        if stage_tracker.check_completion(net, cycle, sim_hours):
            stage_tracker.advance_stage()
        
        if cycle % checkpoint_interval == 0:
            type_counts = {}
            for n in net.nodes.values():
                type_counts[n.type.value] = type_counts.get(n.type.value, 0) + 1
            
            total_conn = net.get_total_connections()
            print(f"\nCycle {cycle:5d} | Stage: {stage.name:20s} | "
                  f"Nodes: {len(net.nodes):4d} | Connections: {total_conn:5d} | "
                  f"Types: {len(type_counts)}")
            print(f"  Type distribution: {type_counts}")
            
            # Check STEM cells
            stem_cells = net.get_nodes_by_type(NotionType.STEM)
            if stem_cells:
                sample = stem_cells[0]
                print(f"  Sample STEM: energy={sample.energy:.2f}, "
                      f"divisions={sample.division_count}, "
                      f"connections={len(sample.connections)}")
    
    # Final report
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    
    type_counts = {}
    for n in net.nodes.values():
        type_counts[n.type.value] = type_counts.get(n.type.value, 0) + 1
    
    total_conn = net.get_total_connections()
    print(f"Total nodes: {len(net.nodes)}")
    print(f"Total connections: {total_conn}")
    print(f"Type diversity: {len(type_counts)} types")
    print(f"\nType distribution:")
    for type_name, count in sorted(type_counts.items()):
        ratio = count / len(net.nodes) * 100
        print(f"  {type_name:15s}: {count:4d} ({ratio:5.2f}%)")
    
    # Check for missing types
    required_types = ['STEM', 'SENSOR', 'INTERNEURON', 'INHIBITOR', 
                      'OSCILLATOR', 'PROJECTOR', 'HUB', 'MEMORY', 'GATE']
    missing = [t for t in required_types if t not in type_counts]
    if missing:
        print(f"\n⚠️  Missing types: {missing}")
    else:
        print(f"\n✓ All 9 types present!")
    
    # Check network size
    if 500 <= len(net.nodes) <= 800:
        print(f"✓ Network size in target range (500-800)")
    elif len(net.nodes) < 500:
        print(f"⚠️  Network too small: {len(net.nodes)} < 500")
    else:
        print(f"⚠️  Network too large: {len(net.nodes)} > 800")
    
    # Check inhibitor ratio
    inhibitor_count = type_counts.get('INHIBITOR', 0)
    inhibitor_ratio = inhibitor_count / len(net.nodes)
    if 0.15 <= inhibitor_ratio <= 0.25:
        print(f"✓ Inhibitor ratio healthy: {inhibitor_ratio:.2%}")
    else:
        print(f"⚠️  Inhibitor ratio off: {inhibitor_ratio:.2%} (target: 15-25%)")
    
    # Check hub monopoly
    hubs = net.get_nodes_by_type(NotionType.HUB)
    if hubs:
        max_hub_connections = max(len(h.connections) for h in hubs)
        hub_ratio = max_hub_connections / max(total_conn, 1)
        if hub_ratio < 0.05:
            print(f"✓ Hub monopoly protected: {hub_ratio:.2%} < 5%")
        else:
            print(f"⚠️  Hub monopoly exceeded: {hub_ratio:.2%} >= 5%")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    run_diagnostic()
