"""Parallel Runner — multiprocessing for population simulation."""

from __future__ import annotations

import time
import uuid
from typing import List

from dna.schema import DNAConfig
from search.scorer import RunResult
from monitor.metrics import ConsciousnessMetrics, MetricsResult
from monitor.transfer_entropy import TransferEntropyCalculator


def run_single_seed(seed_config: DNAConfig, sim_hours: float = 72.0) -> dict:
    """
    Single seed independent run (top-level function for multiprocessing).
    
    Returns a dict with all result fields (picklable).
    """
    import random
    import numpy as np
    random.seed()  # Each process gets its own seed
    np.random.seed(None)

    start_time = time.time()

    # Import here to avoid circular imports in multiprocessing
    from notion.network import NotionNetwork
    from notion.notion_cell import NotionType
    from monitor.stage_tracker import StageTracker
    from world_engine.time_system import TICKS_PER_SIM_HOUR

    # Initialize
    tracker = StageTracker(seed_config.stages)
    network = NotionNetwork(seed_config, stage_tracker=tracker)
    network.init_stem_cells()

    total_ticks = int(sim_hours * TICKS_PER_SIM_HOUR)
    log_interval = 1000  # Log every 1000 cycles

    # Main simulation loop
    for cycle in range(1, total_ticks + 1):
        sim_hours_elapsed = cycle / TICKS_PER_SIM_HOUR
        tracker.set_cycle_info(cycle, sim_hours_elapsed)

        # Check stage completion
        if tracker.check_completion(network, cycle, sim_hours_elapsed):
            tracker.advance_stage()

        current_stage = tracker.get_current_stage()
        if current_stage is None:
            break

        # Run one cycle
        network.step(cycle, [], current_stage)

        # Safety: if network dies completely, stop early
        if len(network.nodes) == 0:
            break

        # Cap network size to prevent memory issues
        if len(network.nodes) > 1000:
            # Remove lowest energy nodes
            sorted_nodes = sorted(network.nodes.values(), key=lambda n: n.energy)
            for node in sorted_nodes[:len(sorted_nodes) - 800]:
                network.remove_node(node.id)

    # End of simulation — compute metrics
    metrics_calculator = ConsciousnessMetrics()
    metrics = metrics_calculator.measure_all(network)

    # Compute TEII (with reduced window for speed)
    teii_calculator = TransferEntropyCalculator(window=min(300, len(network.nodes)))
    teii = teii_calculator.calculate(network)

    duration = time.time() - start_time

    return {
        'seed_id': seed_config.meta.name,
        'metrics': {
            'self_sustain': metrics.self_sustain,
            'learning': metrics.learning,
            'discrimination': metrics.discrimination,
            'generalization': metrics.generalization,
            'persistence': metrics.persistence,
            'self_awareness': metrics.self_awareness,
            'metaplasticity': metrics.metaplasticity,
        },
        'teii': teii,
        'duration_seconds': duration,
        'final_node_count': len(network.nodes),
    }


class ParallelRunner:
    """
    Run multiple seeds in parallel using multiprocessing.
    """

    def run_population(
        self,
        seeds: List[DNAConfig],
        sim_hours: float = 72.0,
        max_workers: int = 8,
    ) -> List[RunResult]:
        """
        Run entire population in parallel.
        Returns list of RunResult.
        """
        from multiprocessing import Pool
        from tqdm import tqdm

        results_dicts = []

        with Pool(processes=max_workers) as pool:
            async_results = [
                pool.apply_async(run_single_seed, (seed, sim_hours))
                for seed in seeds
            ]

            for ar in tqdm(async_results, desc="Running seeds"):
                results_dicts.append(ar.get())

        # Convert dicts to RunResult objects
        results = []
        for rd in results_dicts:
            metrics = MetricsResult(**rd['metrics'])
            result = RunResult(
                seed_id=rd['seed_id'],
                metrics=metrics,
                teii=rd['teii'],
                duration_seconds=rd['duration_seconds'],
                final_node_count=rd['final_node_count'],
            )
            result.score = metrics.weighted_score()
            results.append(result)

        return results

    @staticmethod
    def run_single(seed_config: DNAConfig, sim_hours: float = 72.0) -> RunResult:
        """
        Run a single seed synchronously.
        """
        rd = run_single_seed(seed_config, sim_hours)
        metrics = MetricsResult(**rd['metrics'])
        result = RunResult(
            seed_id=rd['seed_id'],
            metrics=metrics,
            teii=rd['teii'],
            duration_seconds=rd['duration_seconds'],
            final_node_count=rd['final_node_count'],
        )
        result.score = metrics.weighted_score()
        return result
