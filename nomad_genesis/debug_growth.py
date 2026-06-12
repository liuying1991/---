#!/usr/bin/env python3
"""Debug script to diagnose why network stops growing."""

import sys
from dna.parser import load_dna
from notion.network import NotionNetwork
from notion.notion_cell import NotionType
from monitor.stage_tracker import StageTracker


def debug_network_growth():
    """Run simulation and track growth details."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()
    
    print(f"Initial: {len(net.nodes)} nodes")
    print(f"Division threshold: {config.division.energy_threshold}")
    print(f"Max divisions per node: {config.division.max_divisions}")
    print(f"Max local density: {config.division.max_local_density}")
    
    # Run for 8000 cycles (8 hours)
    for cycle in range(1, 8001):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
        
        # Track divisions
        stem_count_before = len([n for n in net.nodes.values() if n.type == NotionType.STEM])
        
        net.step(cycle, [], stage)
        
        stem_count_after = len([n for n in net.nodes.values() if n.type == NotionType.STEM])
        
        # Print detailed stats every 1000 cycles
        if cycle % 1000 == 0:
            types = {}
            for n in net.nodes.values():
                types[n.type.value] = types.get(n.type.value, 0) + 1
            
            # Check energy levels
            energies = [n.energy for n in net.nodes.values()]
            avg_energy = sum(energies) / len(energies) if energies else 0
            min_energy = min(energies) if energies else 0
            max_energy = max(energies) if energies else 0
            
            # Check division counts
            div_counts = [n.division_count for n in net.nodes.values()]
            avg_divisions = sum(div_counts) / len(div_counts) if div_counts else 0
            max_divisions = max(div_counts) if div_counts else 0
            
            print(f"\n[Cycle {cycle} / {sim_hours:.1f}h]")
            print(f"  Total nodes: {len(net.nodes)}")
            print(f"  Types: {types}")
            print(f"  STEM cells: {stem_count_after}")
            print(f"  Energy - avg: {avg_energy:.2f}, min: {min_energy:.2f}, max: {max_energy:.2f}")
            print(f"  Divisions - avg: {avg_divisions:.2f}, max: {max_divisions}")
            print(f"  Stage: {stage.name}")
            
            # Check why STEM cells aren't dividing
            if stem_count_after > 0:
                stem_samples = [n for n in net.nodes.values() if n.type == NotionType.STEM][:5]
                print(f"  Sample STEM cells:")
                for stem in stem_samples:
                    can_divide = stem.can_divide(config.division)
                    
                    # Check local density
                    nearby = net.spatial_hash.get_nearby_entities(
                        stem.position, config.initial.connection_radius
                    )
                    nearby_count = len(nearby)
                    local_density = len(stem.connections) / nearby_count if nearby_count > 0 else 0.0
                    density_ok = local_density < config.division.max_local_density
                    
                    print(f"    {stem.id[:8]}: energy={stem.energy:.2f}, "
                          f"divisions={stem.division_count}, "
                          f"can_divide={can_divide}, "
                          f"connections={len(stem.connections)}, "
                          f"nearby={nearby_count}, "
                          f"density={local_density:.2f}, "
                          f"density_ok={density_ok}")
                    if not can_divide:
                        if stem.energy < config.division.energy_threshold:
                            print(f"      → Energy too low ({stem.energy:.2f} < {config.division.energy_threshold})")
                        if stem.division_count >= config.division.max_divisions:
                            print(f"      → Max divisions reached ({stem.division_count} >= {config.division.max_divisions})")
                    if can_divide and not density_ok:
                        print(f"      → Local density too high ({local_density:.2f} >= {config.division.max_local_density})")
    
    print(f"\n{'='*60}")
    print(f"Final: {len(net.nodes)} nodes")


if __name__ == "__main__":
    debug_network_growth()
