#!/usr/bin/env python3
"""Debug script to analyze network development and differentiation."""

import sys
from dna.parser import load_dna
from notion.network import NotionNetwork
from notion.notion_cell import NotionType
from monitor.stage_tracker import StageTracker


def debug_network_development():
    """Run a longer simulation and track what's happening."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()
    
    print(f"Initial: {len(net.nodes)} nodes")
    print(f"Config - base_prob: {config.connection.base_prob}, min_prob: {config.connection.min_prob}")
    print(f"Config - connection_radius: {config.initial.connection_radius}")
    print(f"Config - interneuron min_connections: {config.differentiation.interneuron.min_connections}")
    print(f"Config - sensor input_density_threshold: {config.differentiation.sensor.input_density_threshold}")
    
    ticks = 2000  # 2 sim hours
    for cycle in range(1, ticks + 1):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
            print(f"\n[Cycle {cycle}] Stage advanced to: {stage.name}")
        
        net.step(cycle, [], stage)
        
        # Print stats every 500 cycles
        if cycle % 500 == 0:
            types = {}
            for n in net.nodes.values():
                types[n.type.value] = types.get(n.type.value, 0) + 1
            
            total_conn = net.get_total_connections()
            avg_degree = total_conn * 2 / max(len(net.nodes), 1)
            
            print(f"\n[Cycle {cycle} / {sim_hours:.2f}h]")
            print(f"  Nodes: {len(net.nodes)}")
            print(f"  Connections: {total_conn}, Avg degree: {avg_degree:.2f}")
            print(f"  Stage: {stage.name}")
            print(f"  Types: {types}")
            
            # Sample some nodes to see their state
            sample_nodes = list(net.nodes.values())[:5]
            print(f"  Sample nodes:")
            for node in sample_nodes:
                print(f"    {node.id[:8]}... type={node.type.value}, "
                      f"degree={node.degree}, idle={node.idle_cycles}, "
                      f"energy={node.energy:.2f}, activation={node.activation:.3f}, "
                      f"input_count={node.input_count}, total_input={node.total_input_signal:.3f}")
            
            # Check why differentiation isn't happening
            stem_nodes = [n for n in net.nodes.values() if n.type == NotionType.STEM]
            if stem_nodes:
                print(f"  STEM node analysis (first 3):")
                for node in stem_nodes[:3]:
                    print(f"    {node.id[:8]}... idle={node.idle_cycles}, "
                          f"degree={node.degree}, activation={node.activation:.3f}, "
                          f"energy={node.energy:.2f}, inhibitory_cycles={node.inhibitory_cycles}")
                    
                    # Check each differentiation condition
                    if node.idle_cycles < 100:
                        print(f"      → Too young (idle < 100)")
                    else:
                        # MEMORY check
                        if net.global_stats.mean_activation > 0:
                            mem_threshold = net.global_stats.mean_activation * config.differentiation.memory.intensity_ratio
                            print(f"      → MEMORY: activation={node.activation:.3f} vs threshold={mem_threshold:.3f}")
                        
                        # OSCILLATOR check
                        osc_threshold = config.initial.base_metabolism * config.differentiation.oscillator.energy_multiplier
                        print(f"      → OSCILLATOR: idle={node.idle_cycles} > {config.differentiation.oscillator.idle_cycles}, "
                              f"energy={node.energy:.2f} > {osc_threshold:.2f}, "
                              f"divisions={node.division_count} >= {config.division.max_divisions}")
                        
                        # GATE check
                        print(f"      → GATE: inhibitory_cycles={node.inhibitory_cycles} > {config.differentiation.gate.inhibitory_cycles}")
                        
                        # SENSOR check
                        if node.input_count > 0:
                            input_density = node.total_input_signal / node.input_count
                            print(f"      → SENSOR: input_density={input_density:.3f} > {config.differentiation.sensor.input_density_threshold}")
                        else:
                            print(f"      → SENSOR: no inputs yet")
                        
                        # INTERNEURON check
                        act_freq_ratio = 0.0
                        if node.activation_history:
                            node_freq = sum(node.activation_history[-100:]) / max(len(node.activation_history[-100:]), 1)
                            if net.global_stats.mean_activation > 0:
                                act_freq_ratio = node_freq / net.global_stats.mean_activation
                        print(f"      → INTERNEURON: degree={node.degree} >= {config.differentiation.interneuron.min_connections}, "
                              f"act_freq_ratio={act_freq_ratio:.3f} >= {config.differentiation.interneuron.activation_freq_ratio}")
    
    print(f"\n{'='*60}")
    print(f"Final: {len(net.nodes)} nodes, {net.get_total_connections()} connections")
    types = {}
    for n in net.nodes.values():
        types[n.type.value] = types.get(n.type.value, 0) + 1
    print(f"Types: {types}")
    print(f"Global stats: mean_activation={net.global_stats.mean_activation:.4f}, "
          f"mean_degree={net.global_stats.mean_degree:.2f}")


if __name__ == "__main__":
    debug_network_development()
