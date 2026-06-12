"""Diagnostic script to analyze network activity patterns."""

import sys
sys.path.insert(0, '/workspace/nomad_genesis')

from dna.parser import load_dna
from notion.network import NotionNetwork
from notion.notion_cell import NotionType
from monitor.stage_tracker import StageTracker
import numpy as np

def diagnose_network_activity():
    print("="*80)
    print("NETWORK ACTIVITY DIAGNOSTIC")
    print("="*80)

    # Load config and initialize network
    config = load_dna('/workspace/nomad_genesis/dna/seeds/baseline_v0.2.yaml')
    stage_tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker)
    net.init_stem_cells()

    print(f"\nInitial nodes: {len(net.nodes)}")
    print(f"Initial connections: {net.get_total_connections()}")

    # Run for 1000 cycles (1 sim hour) to get some activity
    print("\nRunning 1000 cycles...")
    for cycle in range(1000):
        sim_hours = cycle / 1000.0
        stage = stage_tracker.get_current_stage()
        stage_tracker.set_cycle_info(cycle, sim_hours)
        net.step(cycle, [], stage)
        if stage_tracker.check_completion(net, cycle, sim_hours):
            stage_tracker.advance_stage()

    print(f"\nAfter 1000 cycles:")
    print(f"  Nodes: {len(net.nodes)}")
    print(f"  Connections: {net.get_total_connections()}")

    # Analyze firing patterns
    print("\n" + "="*80)
    print("FIRING PATTERN ANALYSIS")
    print("="*80)

    firing_rates = {}
    total_potential = {}
    connection_strengths = []

    for node_id, node in net.nodes.items():
        if node.activation_history:
            hist = node.activation_history[-100:]
            firing_rate = sum(1 for v in hist if v > 0) / len(hist)
            firing_rates[node.type.value] = firing_rates.get(node.type.value, [])
            firing_rates[node.type.value].append(firing_rate)

            # Track internal potential
            total_potential[node.type.value] = total_potential.get(node.type.value, [])
            total_potential[node.type.value].append(node.potential)

        # Track connection strengths
        for target_id, strength in node.connections.items():
            connection_strengths.append(strength)

    print("\nFiring rates by type (last 100 cycles):")
    for ntype, rates in sorted(firing_rates.items()):
        avg_rate = np.mean(rates)
        print(f"  {ntype:15s}: {avg_rate:.3f} (std: {np.std(rates):.3f})")

    print("\nInternal potential by type:")
    for ntype, potentials in sorted(total_potential.items()):
        avg_pot = np.mean(potentials)
        print(f"  {ntype:15s}: {avg_pot:.3f} (std: {np.std(potentials):.3f})")

    if connection_strengths:
        print(f"\nConnection strength distribution:")
        print(f"  Mean: {np.mean(connection_strengths):.3f}")
        print(f"  Std: {np.std(connection_strengths):.3f}")
        print(f"  Min: {np.min(connection_strengths):.3f}")
        print(f"  Max: {np.max(connection_strengths):.3f}")

        # Count positive vs negative connections
        pos_conns = sum(1 for s in connection_strengths if s > 0)
        neg_conns = sum(1 for s in connection_strengths if s < 0)
        print(f"  Positive: {pos_conns} ({pos_conns/len(connection_strengths)*100:.1f}%)")
        print(f"  Negative: {neg_conns} ({neg_conns/len(connection_strengths)*100:.1f}%)")

    # Check signal propagation
    print("\n" + "="*80)
    print("SIGNAL PROPAGATION CHECK")
    print("="*80)

    # Find a node with connections and trace signal flow
    sample_node = None
    for node in net.nodes.values():
        if len(node.connections) >= 5:
            sample_node = node
            break

    if sample_node:
        print(f"\nSample node: {sample_node.id[:8]}...")
        print(f"  Type: {sample_node.type.value}")
        print(f"  Connections: {len(sample_node.connections)}")
        print(f"  Current potential: {sample_node.potential:.3f}")
        print(f"  Threshold: {sample_node.threshold:.3f}")
        print(f"  Energy: {sample_node.energy:.3f}")

        # Check connected nodes
        connected_types = {}
        for target_id in list(sample_node.connections.keys())[:10]:
            target = net.nodes.get(target_id)
            if target:
                connected_types[target.type.value] = connected_types.get(target.type.value, 0) + 1

        print(f"  Connected to (first 10): {connected_types}")

    # Check activation history patterns
    print("\n" + "="*80)
    print("ACTIVATION HISTORY PATTERNS")
    print("="*80)

    # Sample a few nodes
    sampled_nodes = list(net.nodes.values())[:5]
    for i, node in enumerate(sampled_nodes):
        if node.activation_history:
            hist = node.activation_history[-50:]
            active_count = sum(1 for v in hist if v > 0)
            print(f"\nNode {i} ({node.type.value}):")
            print(f"  Active cycles: {active_count}/{len(hist)} ({active_count/len(hist)*100:.1f}%)")
            print(f"  Last 20 activations: {[1 if v > 0 else 0 for v in hist[-20:]]}")

    # Check for synchronous activity
    print("\n" + "="*80)
    print("SYNCHRONY CHECK")
    print("="*80)

    # Compute correlation between node pairs
    if len(net.nodes) >= 10:
        sample_nodes = list(net.nodes.values())[:20]
        correlations = []

        for i, node_a in enumerate(sample_nodes):
            for j, node_b in enumerate(sample_nodes):
                if i >= j:
                    continue
                if len(node_a.activation_history) >= 50 and len(node_b.activation_history) >= 50:
                    hist_a = node_a.activation_history[-50:]
                    hist_b = node_b.activation_history[-50:]
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

    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)

if __name__ == "__main__":
    diagnose_network_activity()
