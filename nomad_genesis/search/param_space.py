"""Parameter Space — defines searchable parameters and sampling."""

from __future__ import annotations

import random
from typing import Dict, List, Tuple


class ParamSpace:
    """
    Define 10 key parameters with search ranges and distributions.
    """

    parameters: Dict[str, Tuple[float, float, str]] = {
        "connection_radius": (5.0, 20.0, "uniform"),
        "hebb_increment": (0.05, 0.30, "uniform"),
        "decay_amount": (0.01, 0.15, "uniform"),
        "prune_threshold": (0.005, 0.05, "log_uniform"),
        "inhibitor_prob": (0.10, 0.30, "uniform"),
        "oscillator_period_min": (5, 50, "uniform"),
        "oscillator_period_max": (100, 500, "uniform"),
        "division_energy_threshold": (1.5, 4.0, "uniform"),
        "embryonic_division_rate": (0.005, 0.05, "log_uniform"),
        "mutation_sigma": (0.01, 0.15, "log_uniform"),
    }

    def sample(self, n: int) -> List[Dict]:
        """Sample n parameter sets from the parameter space."""
        samples = []
        for _ in range(n):
            sample = {}
            for name, (low, high, dist) in self.parameters.items():
                if dist == "uniform":
                    sample[name] = random.uniform(low, high)
                elif dist == "log_uniform":
                    # Sample uniformly in log space
                    log_low = _safe_log(low)
                    log_high = _safe_log(high)
                    sample[name] = _safe_exp(random.uniform(log_low, log_high))
                else:
                    sample[name] = random.uniform(low, high)
            samples.append(sample)
        return samples

    def apply_to_config(self, config, params: Dict):
        """Apply sampled parameters to a DNAConfig object."""
        import copy
        new_config = copy.deepcopy(config)

        if "connection_radius" in params:
            new_config.initial.connection_radius = params["connection_radius"]
        if "hebb_increment" in params:
            new_config.connection.hebb_increment = params["hebb_increment"]
        if "decay_amount" in params:
            new_config.connection.decay_amount = params["decay_amount"]
        if "prune_threshold" in params:
            new_config.connection.prune_threshold = params["prune_threshold"]
        if "inhibitor_prob" in params:
            new_config.differentiation.inhibitor.conversion_prob = params["inhibitor_prob"]
        if "oscillator_period_min" in params:
            p_range = new_config.differentiation.oscillator.period_range
            new_config.differentiation.oscillator.period_range = (
                int(params["oscillator_period_min"]), p_range[1]
            )
        if "oscillator_period_max" in params:
            p_range = new_config.differentiation.oscillator.period_range
            new_config.differentiation.oscillator.period_range = (
                p_range[0], int(params["oscillator_period_max"])
            )
        if "division_energy_threshold" in params:
            new_config.division.energy_threshold = params["division_energy_threshold"]
        if "mutation_sigma" in params:
            new_config.division.mutation_sigma = params["mutation_sigma"]

        return new_config


def _safe_log(x: float) -> float:
    import math
    return math.log(max(x, 1e-10))


def _safe_exp(x: float) -> float:
    import math
    return math.exp(min(x, 50))
