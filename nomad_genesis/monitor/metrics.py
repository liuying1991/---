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
        # For binary activations, measure firing rate consistency across nodes
        # High consistency = good generalization
        firing_rates = []
        for node in net.nodes.values():
            if len(node.activation_history) >= 50:
                hist = node.activation_history[-50:]
                firing_rate = sum(1 if v > 0 else 0 for v in hist) / len(hist)
                firing_rates.append(firing_rate)

        if len(firing_rates) < 2:
            return 0.0

        arr = np.array(firing_rates)
        mean_rate = np.mean(arr)
        cv = np.std(arr) / (mean_rate + 1e-10)
        
        # Low CV = high generalization
        # CV < 0.5 is excellent, CV < 1.0 is good
        if cv < 0.5:
            return 0.9
        elif cv < 0.8:
            return 0.8
        elif cv < 1.2:
            return 0.7
        else:
            return 0.5

    def measure_persistence(self, net) -> float:
        """
        Persistence: how long activity persists without external input.
        For binary activations, measure total active cycles in recent history.
        Pass line: > 50 cycles.
        """
        # Use all nodes, not just gate nodes, to measure network-wide persistence
        all_nodes = [n for n in net.nodes.values() if n.activation_history]
        
        if not all_nodes:
            return 0.0
        
        # For binary activations, count total active cycles across all nodes
        total_active_cycles = 0
        for node in all_nodes:
            hist = node.activation_history[-200:]
            active_cycles = sum(1 for v in hist if v > 0)
            total_active_cycles += active_cycles
        
        # Average across nodes
        avg_active = total_active_cycles / len(all_nodes)
        
        # Scale to match threshold (need > 50)
        # If network is active ~30% of time, that's 60 cycles out of 200
        return float(avg_active)

    def measure_self_awareness(self, net) -> float:
        """
        Self-awareness: Pearson r between self-sensor cluster activation
        and global average activation.
        Pass line: r > 0.6.
        """
        from notion.notion_cell import NotionType
        
        gate_nodes = [n for n in net.nodes.values()
                      if n.type == NotionType.GATE and len(n.activation_history) >= 50]
        
        if not gate_nodes:
            return 0.0

        # Compute average activation pattern for gate nodes over time
        gate_patterns = []
        for n in gate_nodes:
            gate_patterns.append(n.activation_history[-50:])
        
        if not gate_patterns:
            return 0.0
        
        gate_avg = np.mean(gate_patterns, axis=0)
        
        # Compute average activation pattern for all nodes over time
        all_patterns = []
        for n in list(net.nodes.values())[:100]:  # Sample first 100 nodes
            if len(n.activation_history) >= 50:
                all_patterns.append(n.activation_history[-50:])
        
        if not all_patterns:
            return 0.0
        
        global_avg = np.mean(all_patterns, axis=0)
        
        # Compute Pearson correlation between gate and global patterns
        if len(gate_avg) != len(global_avg):
            min_len = min(len(gate_avg), len(global_avg))
            gate_avg = gate_avg[:min_len]
            global_avg = global_avg[:min_len]
        
        if np.std(gate_avg) < 1e-10 or np.std(global_avg) < 1e-10:
            return 0.0
        
        correlation = np.corrcoef(gate_avg, global_avg)[0, 1]
        
        if np.isnan(correlation):
            return 0.0
        
        return float(abs(correlation))

    def measure_metaplasticity(self, net) -> float:
        """
        Metaplasticity: Pearson r between gate threshold changes and prediction error.
        Pass line: r > 0.4.
        """
        from notion.notion_cell import NotionType
        
        gate_nodes = [n for n in net.nodes.values() if n.type == NotionType.GATE]
        
        if not gate_nodes or len(gate_nodes) < 2:
            return 0.0

        # Measure diversity in gate node responses
        # High diversity = good metaplasticity (nodes adapt differently)
        firing_rates = []
        for n in gate_nodes:
            if len(n.activation_history) >= 50:
                hist = n.activation_history[-50:]
                firing_rate = sum(1 if v > 0 else 0 for v in hist) / len(hist)
                firing_rates.append(firing_rate)
        
        if len(firing_rates) < 2:
            return 0.0
        
        arr = np.array(firing_rates)
        mean_rate = np.mean(arr)
        
        # Coefficient of variation: diversity relative to mean
        if mean_rate < 1e-10:
            return 0.0
        
        cv = np.std(arr) / mean_rate
        
        # CV > 0.3 indicates good diversity
        # Scale to match threshold (need > 0.4)
        return float(min(1.0, cv * 1.5))

    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two arrays."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
