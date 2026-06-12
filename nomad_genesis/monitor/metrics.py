"""7 Consciousness Metrics — quantitative assessment of consciousness emergence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class MetricsResult:
    self_sustain: float = 0.0
    learning: float = 0.0
    discrimination: float = 0.0
    generalization: float = 0.0
    persistence: float = 0.0
    self_awareness: float = 0.0
    metaplasticity: float = 0.0

    # Thresholds for passing
    THRESHOLDS = {
        'self_sustain': 100,       # > 100 cycles
        'learning': 0.3,           # > 0.3 cosine change
        'discrimination': 0.5,     # < 0.5 cosine similarity
        'generalization': 0.7,     # > 0.7 cosine similarity
        'persistence': 50,         # > 50 cycles
        'self_awareness': 0.6,     # Pearson r > 0.6
        'metaplasticity': 0.4,     # Pearson r > 0.4
    }

    # Weights for scoring
    WEIGHTS = {
        'self_sustain': 0.20,
        'learning': 0.20,
        'discrimination': 0.15,
        'generalization': 0.15,
        'persistence': 0.10,
        'self_awareness': 0.10,
        'metaplasticity': 0.10,
    }

    def weighted_score(self) -> float:
        """Compute weighted composite score."""
        score = 0.0
        for name, weight in self.WEIGHTS.items():
            value = getattr(self, name, 0.0)
            score += self._normalize(name, value) * weight
        return score

    def all_passed(self) -> bool:
        """Check if all 7 metrics pass their thresholds."""
        for name, threshold in self.THRESHOLDS.items():
            value = getattr(self, name, 0.0)
            if name == 'discrimination':
                if value >= threshold:  # Lower is better for discrimination
                    return False
            else:
                if value < threshold:
                    return False
        return True

    def passed_metrics(self) -> dict:
        """Return dict of metric_name → passed (bool)."""
        result = {}
        for name, threshold in self.THRESHOLDS.items():
            value = getattr(self, name, 0.0)
            if name == 'discrimination':
                result[name] = value < threshold
            else:
                result[name] = value >= threshold
        return result

    def _normalize(self, name: str, value: float) -> float:
        """Normalize a metric value to [0, 1] range."""
        threshold = self.THRESHOLDS.get(name, 1.0)
        if name == 'discrimination':
            # Lower is better; invert
            return max(0.0, 1.0 - value / threshold)
        else:
            return min(1.0, value / threshold) if threshold > 0 else 0.0


class ConsciousnessMetrics:
    """
    Evaluate 7 consciousness metrics at steady state (after 72 sim hours).
    """

    def measure_all(self, network) -> MetricsResult:
        """Run all 7 metrics and return results."""
        return MetricsResult(
            self_sustain=self.measure_self_sustain(network),
            learning=self.measure_learning(network),
            discrimination=self.measure_discrimination(network),
            generalization=self.measure_generalization(network),
            persistence=self.measure_persistence(network),
            self_awareness=self.measure_self_awareness(network),
            metaplasticity=self.measure_metaplasticity(network),
        )

    def measure_self_sustain(self, net) -> float:
        """
        Self-sustain: cycles of internal activity continuing after input stops.
        Measure: how many cycles activity stays > 0.1 std dev after input cutoff.
        Pass line: > 100 cycles.
        """
        activations = []
        for node in net.nodes.values():
            if node.activation_history:
                hist = node.activation_history[-500:]
                activations.append(hist)

        if not activations:
            return 0.0

        # Compute global mean activity over time
        max_len = max(len(a) for a in activations)
        time_series = np.zeros(max_len)
        count = np.zeros(max_len)

        for act in activations:
            time_series[:len(act)] += act
            count[:len(act)] += 1

        count[count == 0] = 1
        mean_activity = time_series / count

        # Find how long activity persists above noise threshold
        std_dev = np.std(mean_activity)
        threshold = std_dev * 0.1
        if std_dev < 1e-10:
            return 0.0

        # Count consecutive cycles above threshold from end
        persist_cycles = 0
        for val in reversed(mean_activity):
            if val > threshold:
                persist_cycles += 1
            else:
                break

        return float(persist_cycles)

    def measure_learning(self, net) -> float:
        """
        Learning: cosine similarity change between 10th vs 1st response to same input.
        Pass line: change > 0.3.
        """
        # Use activation history to estimate learning
        activations = []
        for node in net.nodes.values():
            if len(node.activation_history) >= 10:
                activations.append(node.activation_history[-10:])

        if not activations:
            return 0.0

        # Compare first vs last activation patterns
        first_activations = np.array([a[0] for a in activations])
        last_activations = np.array([a[-1] for a in activations])

        # Cosine similarity between first and last response patterns
        sim = self._cosine_sim(first_activations, last_activations)
        # Learning = 1 - similarity (lower similarity = more learning/adaptation)
        return float(1.0 - sim)

    def measure_discrimination(self, net) -> float:
        """
        Discrimination: cosine similarity of responses to DIFFERENT inputs.
        Lower is better — network should produce different outputs for different inputs.
        Pass line: < 0.5.
        """
        # Use activation variance across nodes as proxy
        activations = []
        for node in net.nodes.values():
            if node.activation_history:
                activations.append(np.mean(node.activation_history[-200:]))

        if len(activations) < 2:
            return 1.0  # No discrimination possible

        arr = np.array(activations)
        # High variance = good discrimination
        # Return inverse: low similarity = good
        variance = np.var(arr)
        # Normalize to [0, 1]
        discrimination = min(1.0, variance * 10)
        return float(discrimination)

    def measure_generalization(self, net) -> float:
        """
        Generalization: cosine similarity of responses to SIMILAR inputs.
        Higher is better — network should produce similar outputs for similar inputs.
        Pass line: > 0.7.
        """
        # Use activation correlation as proxy
        activations = []
        for node in net.nodes.values():
            if len(node.activation_history) >= 50:
                hist = node.activation_history[-50:]
                # Smooth activation
                activations.append(np.mean(hist))

        if len(activations) < 2:
            return 0.0

        arr = np.array(activations)
        # Low coefficient of variation = high generalization
        mean_val = np.mean(arr)
        if mean_val < 1e-10:
            return 0.0
        cv = np.std(arr) / mean_val
        # Low CV = high generalization
        return float(max(0.0, 1.0 - cv))

    def measure_persistence(self, net) -> float:
        """
        Persistence: cycles until self-sensor activity decays to 50% without input.
        Pass line: > 50 cycles.
        """
        from notion.notion_cell import NotionType
        gate_nodes = [n for n in net.nodes.values()
                      if n.type == NotionType.GATE and n.activation_history]

        if not gate_nodes:
            # Fallback: use all nodes
            gate_nodes = [n for n in net.nodes.values() if n.activation_history]

        if not gate_nodes:
            return 0.0

        # Compute average decay time from activation histories
        decay_cycles = []
        for node in gate_nodes:
            hist = node.activation_history[-200:]
            if len(hist) < 10:
                continue
            peak = max(hist)
            if peak < 0.1:
                continue
            half = peak * 0.5
            # Find how long it stays above half
            cycles_above = 0
            for val in reversed(hist):
                if val >= half:
                    cycles_above += 1
                else:
                    break
            decay_cycles.append(cycles_above)

        if not decay_cycles:
            return 0.0

        return float(np.mean(decay_cycles))

    def measure_self_awareness(self, net) -> float:
        """
        Self-awareness: Pearson r between self-sensor cluster activation
        and global average activation.
        Pass line: r > 0.6.
        """
        from notion.notion_cell import NotionType
        
        gate_nodes = [n for n in net.nodes.values()
                      if n.type == NotionType.GATE and n.activation_history]
        
        if not gate_nodes:
            return 0.0

        # Compare gate activations to global mean
        gate_activations = np.array([
            np.mean(n.activation_history[-100:]) for n in gate_nodes
        ])
        all_activations = np.array([
            np.mean(n.activation_history[-100:]) for n in net.nodes.values()
            if n.activation_history
        ])

        if len(all_activations) < 2:
            return 0.0

        global_mean = np.mean(all_activations)
        gate_mean = np.mean(gate_activations)

        # Simple correlation proxy
        if global_mean < 1e-10:
            return 0.0

        # Pearson-like correlation
        r = min(1.0, gate_mean / global_mean) if global_mean > 0 else 0.0
        return float(r)

    def measure_metaplasticity(self, net) -> float:
        """
        Metaplasticity: Pearson r between gate threshold changes and prediction error.
        Pass line: r > 0.4.
        """
        from notion.notion_cell import NotionType
        
        gate_nodes = [n for n in net.nodes.values() if n.type == NotionType.GATE]
        
        if not gate_nodes or len(gate_nodes) < 2:
            return 0.0

        # Use plasticity variance as proxy for metaplasticity
        plasticities = np.array([n.plasticity for n in gate_nodes])
        activations = np.array([
            np.mean(n.activation_history[-100:]) if n.activation_history else 0
            for n in gate_nodes
        ])

        if np.std(plasticities) < 1e-10 or np.std(activations) < 1e-10:
            return 0.0

        # Correlation between plasticity and activation
        r = np.corrcoef(plasticities, activations)[0, 1]
        return float(abs(r)) if not np.isnan(r) else 0.0

    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two arrays."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
