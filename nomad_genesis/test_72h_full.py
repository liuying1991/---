#!/usr/bin/env python3
"""Full 72h simulation test with metrics evaluation."""

import sys
sys.path.insert(0, '/workspace/nomad_genesis')

from dna.parser import load_dna
from notion.network import NotionNetwork
from monitor.stage_tracker import StageTracker
from monitor.metrics import ConsciousnessMetrics
from monitor.transfer_entropy import TransferEntropyCalculator
from notion.notion_cell import NotionType

def run_72h_simulation():
    print("="*80)
    print("72-HOUR FULL SIMULATION WITH METRICS")
    print("="*80)
    
    print("\nLoading DNA config...")
    config = load_dna('/workspace/nomad_genesis/dna/seeds/baseline_v0.2.yaml')
    
    print("Initializing network...")
    stage_tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker)
    net.init_stem_cells()
    
    print(f"Initial nodes: {len(net.nodes)}")
    
    # Run for 72 hours (72000 cycles)
    target_cycles = 72000
    checkpoint_interval = 12000  # Every 12 hours
    
    print(f"\nRunning {target_cycles} cycles (72 sim hours)...")
    
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
            print(f"  Cycle {cycle:6d} ({sim_hours:5.1f}h) | Stage: {stage.name:20s} | "
                  f"Nodes: {len(net.nodes):4d} | Types: {len(type_counts)}")
    
    # Final report
    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)
    
    type_counts = {}
    for n in net.nodes.values():
        type_counts[n.type.value] = type_counts.get(n.type.value, 0) + 1
    
    total_conn = net.get_total_connections()
    print(f"\nFinal Network State:")
    print(f"  Total nodes: {len(net.nodes)}")
    print(f"  Total connections: {total_conn}")
    print(f"  Type diversity: {len(type_counts)} types")
    print(f"\nType distribution:")
    for type_name, count in sorted(type_counts.items()):
        ratio = count / len(net.nodes) * 100
        print(f"    {type_name:15s}: {count:4d} ({ratio:5.2f}%)")
    
    # Check for missing types
    required_types = ['STEM', 'SENSOR', 'INTERNEURON', 'INHIBITOR', 
                      'OSCILLATOR', 'PROJECTOR', 'HUB', 'MEMORY', 'GATE']
    missing = [t for t in required_types if t not in type_counts]
    if missing:
        print(f"\n⚠️  Missing types: {missing}")
    else:
        print(f"\n✓ All 9 types present!")
    
    # Run consciousness metrics
    print("\n" + "="*80)
    print("COMPUTING CONSCIOUSNESS METRICS")
    print("="*80)
    
    try:
        metrics_calculator = ConsciousnessMetrics()
        metrics = metrics_calculator.measure_all(net)
        
        print(f"\n7 Consciousness Metrics:")
        print(f"  Self-Sustain:      {metrics.self_sustain:.3f} (pass: {metrics.self_sustain > 100})")
        print(f"  Learning:          {metrics.learning:.3f} (pass: {metrics.learning > 0.3})")
        print(f"  Discrimination:    {metrics.discrimination:.3f} (pass: {metrics.discrimination < 0.5})")
        print(f"  Generalization:    {metrics.generalization:.3f} (pass: {metrics.generalization > 0.7})")
        print(f"  Persistence:       {metrics.persistence:.3f} (pass: {metrics.persistence > 50})")
        print(f"  Self-Awareness:    {metrics.self_awareness:.3f} (pass: {metrics.self_awareness > 0.6})")
        print(f"  Meta-Plasticity:   {metrics.metaplasticity:.3f} (pass: {metrics.metaplasticity > 0.4})")
        
        weighted = metrics.weighted_score()
        all_passed = metrics.all_passed()
        
        print(f"\nWeighted Score: {weighted:.3f}")
        print(f"All Metrics Passed: {all_passed}")
        
    except Exception as e:
        print(f"\n⚠️  Metrics computation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Compute TEII
    print("\n" + "="*80)
    print("COMPUTING TEII (Transfer Entropy Integration Index)")
    print("="*80)
    
    try:
        teii_calculator = TransferEntropyCalculator()
        teii = teii_calculator.calculate(net, window=300)
        
        print(f"\nTEII: {teii:.3f}")
        print(f"TEII Passed (>0.3): {teii > 0.3}")
        
    except Exception as e:
        print(f"\n⚠️  TEII computation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    run_72h_simulation()
