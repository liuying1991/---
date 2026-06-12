"""Diagnose network state after full 72h simulation."""

import sys
sys.path.insert(0, '/workspace/nomad_genesis')

from dna.parser import load_dna
from notion.network import NotionNetwork
from notion.notion_cell import NotionType
from monitor.stage_tracker import StageTracker
import numpy as np

def diagnose_full_simulation():
    print("="*80)
    print("FULL 72H SIMULATION DIAGNOSTIC")
    print("="*80)

    # Load config and initialize network
    config = load_dna('/workspace/nomad_genesis/dna/seeds/baseline_v0.2.yaml')
    stage_tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker)
    net.init_stem_cells()

    print(f"\nInitial nodes: {len(net.nodes)}")

    # Run full 72h simulation
    print("\nRunning 72000 cycles (72 sim hours)...")
    for cycle in range(72000):
        sim_hours = cycle / 1000.0
        stage = stage_tracker.get_current_stage()
        stage_tracker.set_cycle_info(cycle, sim_hours)
        net.step(cycle, [], stage)
        if stage_tracker.check_completion(net, cycle, sim_hours):
            stage_tracker.advance_stage()

    print(f"\nFinal nodes: {len(net.nodes)}")
    print(f"Final connections: {net.get_total_connections()}")

    # Analyze connection types
    print("\n" + "="*80)
    print("CONNECTION ANALYSIS")
    print("="*80)

    connection_strengths = []
    inhibitory_connections = []
    excitatory_connections = []

    for node in net.nodes.values():
        for target_id, strength in node.connections.items():
            connection_strengths.append(strength)
            if strength < 0:
                inhibitory_connections.append(strength)
            else:
                excitatory_connections.append(strength)

    print(f"\nTotal connections: {len(connection_strengths)}")
    print(f"Excitatory: {len(excitatory_connections)} ({len(excitatory_connections)/len(connection_strengths)*100:.1f}%)")
    print(f"Inhibitory: {len(inhibitory_connections)} ({len(inhibitory_connections)/len(connection_strengths)*100:.1f}%)")

    if inhibitory_connections:
        print(f"\nInhibitory connection strengths:")
        print(f"  Mean: {np.mean(inhibitory_connections):.3f}")
        print(f"  Std: {np.std(inhibitory_connections):.3f}")
        print(f"  Min: {np.min(inhibitory_connections):.3f}")
        print(f"  Max: {np.max(inhibitory_connections):.3f}")

    # Analyze GATE nodes
    print("\n" + "="*80)
    print("GATE NODE ANALYSIS")
    print("="*80)

    gate_nodes = [n for n in net.nodes.values() if n.type == NotionType.GATE]
    print(f"\nTotal GATE nodes: {len(gate_nodes)}")

    if gate_nodes:
        gate_firing_rates = []
        gate_connections = []
        gate_thresholds = []

        for gate in gate_nodes:
            if gate.activation_history:
                hist = gate.activation_history[-200:]
                firing_rate = sum(1 for v in hist if v > 0) / len(hist)
                gate_firing_rates.append(firing_rate)
            
            gate_connections.append(len(gate.connections))
            gate_thresholds.append(gate.threshold)

        print(f"\nGATE node firing rates (last 200 cycles):")
        print(f"  Mean: {np.mean(gate_firing_rates):.3f}")
        print(f"  Std: {np.std(gate_firing_rates):.3f}")
        print(f"  Min: {np.min(gate_firing_rates):.3f}")
        print(f"  Max: {np.max(gate_firing_rates):.3f}")

        print(f"\nGATE node connections:")
        print(f"  Mean: {np.mean(gate_connections):.1f}")
        print(f"  Std: {np.std(gate_connections):.1f}")

        print(f"\nGATE node thresholds:")
        print(f"  Mean: {np.mean(gate_thresholds):.3f}")
        print(f"  Std: {np.std(gate_thresholds):.3f}")

    # Analyze network activity patterns
    print("\n" + "="*80)
    print("NETWORK ACTIVITY PATTERNS")
    print("="*80)

    firing_rates_by_type = {}
    for node in net.nodes.values():
        if node.activation_history:
            hist = node.activation_history[-200:]
            firing_rate = sum(1 for v in hist if v > 0) / len(hist)
            if node.type.value not in firing_rates_by_type:
                firing_rates_by_type[node.type.value] = []
            firing_rates_by_type[node.type.value].append(firing_rate)

    print("\nFiring rates by type (last 200 cycles):")
    for ntype, rates in sorted(firing_rates_by_type.items()):
        print(f"  {ntype:15s}: {np.mean(rates):.3f} (std: {np.std(rates):.3f}, n={len(rates)})")

    # Check synchronous activity
    print("\n" + "="*80)
    print("SYNCHRONY CHECK")
    print("="*80)

    # Sample nodes and compute correlations
    sample_nodes = list(net.nodes.values())[:50]
    correlations = []

    for i, node_a in enumerate(sample_nodes):
        for j, node_b in enumerate(sample_nodes):
            if i >= j:
                continue
            if len(node_a.activation_history) >= 100 and len(node_b.activation_history) >= 100:
                hist_a = node_a.activation_history[-100:]
                hist_b = node_b.activation_history[-100:]
                if np.std(hist_a) > 1e-10 and np.std(hist_b) > 1e-10:
                    corr = np.corrcoef(hist_a, hist_b)[0, 1]
                    if not np.isnan(corr):
                        correlations.append(corr)

    if correlations:
        print(f"\nPairwise correlations (sample of {len(correlations)} pairs):")
        print(f"  Mean: {np.mean(correlations):.3f}")
        print(f"  Std: {np.std(correlations):.3f}")
        print(f"  Min: {np.min(correlations):.3f}")
        print(f"  Max: {np.max(correlations):.3f}")

    # Check activation persistence
    print("\n" + "="*80)
    print("ACTIVATION PERSISTENCE")
    print("="*80)

    # Count how many nodes have sustained activity
    nodes_with_sustained_activity = 0
    for node in net.nodes.values():
        if node.activation_history:
            hist = node.activation_history[-200:]
            active_cycles = sum(1 for v in hist if v > 0)
            if active_cycles > 50:  # More than 25% of time
                nodes_with_sustained_activity += 1

    print(f"\nNodes with sustained activity (>50 cycles in last 200): {nodes_with_sustained_activity}")
    print(f"Percentage: {nodes_with_sustained_activity/len(net.nodes)*100:.1f}%")

    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)

if __name__ == "__main__":
    diagnose_full_simulation()
