"""Nomad Genesis — Population Search Entry Point

Usage:
    python search_main.py                                  # Default: 200 seeds, 8 workers
    python search_main.py --population 100 --workers 4     # Custom population/workers
    python search_main.py --hours 24                       # Shorter simulation
    python search_main.py --top 5                          # Show top 5
"""

from __future__ import annotations

import argparse
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dna.parser import load_dna
from search.population import Population
from search.runner import ParallelRunner
from search.scorer import Scorer


def main():
    parser = argparse.ArgumentParser(description="Nomad Genesis — Population Search")
    parser.add_argument("--seed", default="dna/seeds/baseline_v0.2.yaml", help="Template DNA seed")
    parser.add_argument("--population", type=int, default=200, help="Population size")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers")
    parser.add_argument("--hours", type=float, default=72.0, help="Sim hours per seed")
    parser.add_argument("--top", type=int, default=10, help="Show top N results")
    parser.add_argument("--output", default="data/search_results", help="Output directory")
    args = parser.parse_args()

    print(f"=== Nomad Genesis Population Search ===")
    print(f"Template: {args.seed}")
    print(f"Population: {args.population}")
    print(f"Workers: {args.workers}")
    print(f"Sim hours: {args.hours}")
    print()

    # Generate population
    print("Generating population...")
    pop = Population(args.seed)
    seeds = pop.generate(args.population)
    print(f"Generated {len(seeds)} seeds")

    # Save population
    pop_dir = os.path.join(args.output, "seeds")
    pop.save_population(seeds, pop_dir)
    print(f"Seeds saved to {pop_dir}")

    # Run population
    print(f"\nRunning population ({args.workers} workers)...")
    start_time = time.time()

    runner = ParallelRunner()
    results = runner.run_population(seeds, sim_hours=args.hours, max_workers=args.workers)

    duration = time.time() - start_time
    print(f"Population run completed in {duration:.1f} seconds ({duration/60:.1f} minutes)")

    # Score and rank
    scorer = Scorer()
    scorer_obj = Scorer()

    for r in results:
        r.score = scorer_obj.score(r)

    ranked = scorer_obj.rank(results)

    # Print summary
    print(scorer_obj.summary(results))

    # Save top seeds
    top_seeds = scorer_obj.select_top(results, n=args.top)
    top_dir = os.path.join(args.output, "top_seeds")
    for i, result in enumerate(top_seeds):
        # Find matching seed config and save
        for seed in seeds:
            if seed.meta.name == result.seed_id:
                pop.save_seed(seed, os.path.join(top_dir, f"top_{i+1:02d}_{result.seed_id}.yaml"))
                break

    print(f"\nTop {len(top_seeds)} seeds saved to {top_dir}")
    print("\nDone.")


if __name__ == "__main__":
    main()
