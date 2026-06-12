"""Scorer — weighted scoring and ranking of run results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from monitor.metrics import MetricsResult


@dataclass
class RunResult:
    seed_id: str
    metrics: MetricsResult
    teii: float = 0.0
    duration_seconds: float = 0.0
    final_node_count: int = 0
    score: float = 0.0

    def __post_init__(self):
        if self.score == 0.0 and self.metrics:
            self.score = self.metrics.weighted_score()


class Scorer:
    """
    Score, rank, and select top performers from run results.
    """

    def score(self, result: RunResult) -> float:
        """
        Weighted formula:
        score = self_sustain×0.20 + learning×0.20 + discrimination×0.15 +
                generalization×0.15 + persistence×0.10 + self_awareness×0.10 +
                metaplasticity×0.10
        """
        return result.metrics.weighted_score()

    def rank(self, results: List[RunResult]) -> List[RunResult]:
        """Rank results by score descending."""
        return sorted(results, key=lambda r: r.score, reverse=True)

    def select_top(self, results: List[RunResult], n: int = 10) -> List[RunResult]:
        """Select top n results."""
        ranked = self.rank(results)
        return ranked[:n]

    def check_pass(self, result: RunResult) -> bool:
        """Check if all 7 metrics pass their thresholds."""
        return result.metrics.all_passed()

    def summary(self, results: List[RunResult]) -> str:
        """Generate a summary string for the results."""
        ranked = self.rank(results)
        if not ranked:
            return "No results to summarize."

        passed_count = sum(1 for r in ranked if self.check_pass(r))
        scores = [r.score for r in ranked]

        summary_lines = [
            f"=== Population Results ===",
            f"Total seeds: {len(ranked)}",
            f"Passed all metrics: {passed_count}/{len(ranked)}",
            f"Score range: {min(scores):.4f} - {max(scores):.4f}",
            f"Mean score: {sum(scores)/len(scores):.4f}",
            f"",
            f"Top 10:",
        ]

        for i, r in enumerate(ranked[:10]):
            passed = "PASS" if self.check_pass(r) else "FAIL"
            summary_lines.append(
                f"  #{i+1} {r.seed_id}: score={r.score:.4f} "
                f"nodes={r.final_node_count} teii={r.teii:.4f} [{passed}]"
            )

        return "\n".join(summary_lines)
