"""Nomad Genesis — Single Run Entry Point

Usage:
    python main.py                          # Uses default config.yaml
    python main.py --seed dna/seeds/baseline_v0.2.yaml
    python main.py --hours 24               # Run for 24 sim hours
    python main.py --no-metrics             # Skip metrics computation
"""

from __future__ import annotations

import argparse
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dna.parser import load_dna, validate_dna
from notion.network import NotionNetwork
from notion.notion_cell import NotionType
from monitor.stage_tracker import StageTracker
from monitor.metrics import ConsciousnessMetrics, MetricsResult
from monitor.transfer_entropy import TransferEntropyCalculator
from monitor.logger import RunLogger
from world_engine.time_system import TICKS_PER_SIM_HOUR


def main():
    parser = argparse.ArgumentParser(description="Nomad Genesis — Single Consciousness Run")
    parser.add_argument("--seed", default=None, help="Path to DNA seed YAML")
    parser.add_argument("--hours", type=float, default=72.0, help="Sim hours to run")
    parser.add_argument("--no-metrics", action="store_true", help="Skip metrics computation")
    parser.add_argument("--log-interval", type=int, default=1000, help="Log every N cycles")
    args = parser.parse_args()

    # Load config
    seed_path = args.seed or "dna/seeds/baseline_v0.2.yaml"
    print(f"Loading DNA seed: {seed_path}")
    config = load_dna(seed_path)
    
    errors = validate_dna(config)
    if errors:
        print(f"DNA validation errors: {errors}")
        sys.exit(1)

    print(f"  Seed: {config.meta.name} v{config.meta.version}")
    print(f"  Stem cells: {config.initial.stem_count}")
    print(f"  Vector dim: {config.initial.vector_dim}")
    print(f"  Stages: {len(config.stages)}")
    print()

    # Initialize
    tracker = StageTracker(config.stages)
    network = NotionNetwork(config, stage_tracker=tracker)
    network.init_stem_cells()

    logger = RunLogger(db_path="data/runs.db")
    run_id = f"run_{int(time.time())}"

    total_ticks = int(args.hours * TICKS_PER_SIM_HOUR)
    start_time = time.time()

    print(f"Starting simulation: {args.hours} sim hours ({total_ticks} ticks)")
    print(f"{'Cycle':>10} {'Sim Hours':>10} {'Stage':<20} {'Nodes':>6} {'Connections':>12} {'Energy':>10}")
    print("-" * 80)

    # Main simulation loop
    for cycle in range(1, total_ticks + 1):
        sim_hours_elapsed = cycle / TICKS_PER_SIM_HOUR
        tracker.set_cycle_info(cycle, sim_hours_elapsed)

        # Check stage completion
        if tracker.check_completion(network, cycle, sim_hours_elapsed):
            old_stage = tracker.get_stage_name()
            tracker.advance_stage()
            new_stage = tracker.get_stage_name()
            if new_stage != old_stage:
                print(f"  >>> Stage transition: {old_stage} → {new_stage}")

        current_stage = tracker.get_current_stage()
        if current_stage is None:
            print("No more stages, stopping.")
            break

        # Run one cycle
        network.step(cycle, [], current_stage)

        # Safety checks
        if len(network.nodes) == 0:
            print("Network completely died, stopping.")
            break

        # Cap network size
        if len(network.nodes) > 1000:
            sorted_nodes = sorted(network.nodes.values(), key=lambda n: n.energy)
            for node in sorted_nodes[:len(sorted_nodes) - 800]:
                network.remove_node(node.id)

        # Periodic logging and status
        if cycle % args.log_interval == 0 or cycle == total_ticks:
            stats = network.global_stats
            print(f"{cycle:10d} {sim_hours_elapsed:10.1f} {tracker.get_stage_name():<20} "
                  f"{stats.node_count:6d} {stats.total_edges:12d} {stats.total_energy:10.1f}")
            logger.log_cycle(cycle, sim_hours_elapsed, tracker.get_stage_name(), network)

    duration = time.time() - start_time
    print("-" * 80)
    print(f"Simulation completed in {duration:.1f} seconds")
    print(f"Final nodes: {len(network.nodes)}")
    print(f"Stage: {tracker.get_stage_name()}")

    # Type distribution
    type_counts = {}
    for node in network.nodes.values():
        type_counts[node.type.value] = type_counts.get(node.type.value, 0) + 1
    print(f"Type distribution: {type_counts}")

    # Compute metrics
    if not args.no_metrics:
        print("\nComputing consciousness metrics...")
        metrics_calc = ConsciousnessMetrics()
        metrics = metrics_calc.measure_all(network)

        print(f"\n{'Metric':<20} {'Value':>10} {'Threshold':>10} {'Status':>8}")
        print("-" * 55)

        passed = metrics.passed_metrics()
        for name in ['self_sustain', 'learning', 'discrimination',
                     'generalization', 'persistence', 'self_awareness', 'metaplasticity']:
            value = getattr(metrics, name, 0.0)
            threshold = metrics.THRESHOLDS[name]
            status = "PASS" if passed.get(name, False) else "FAIL"
            print(f"{name:<20} {value:10.4f} {threshold:10} {status:>8}")

        print(f"\nWeighted Score: {metrics.weighted_score():.4f}")
        print(f"All Passed: {metrics.all_passed()}")

        # TEII
        print("\nComputing TEII (Transfer Entropy Integration Index)...")
        teii_calc = TransferEntropyCalculator(window=min(300, len(network.nodes)))
        teii = teii_calc.calculate(network)
        print(f"TEII: {teii:.4f} (pass line: > 0.3)")

        # Log results
        logger.log_run(run_id, config.meta.name, args.hours,
                       len(network.nodes), metrics.weighted_score(), teii, metrics.all_passed())
        logger.log_metrics(run_id, metrics)
    else:
        metrics = None
        teii = 0.0

    logger.close()
    print("\nDone. Results saved to data/runs.db")


if __name__ == "__main__":
    main()
