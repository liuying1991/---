"""Stage Tracker — development stage tracking and automatic switching."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..dna.schema import StageConfig


class StageTracker:
    """
    Track current development stage, switch based on completion conditions.
    """

    def __init__(self, stage_configs):
        self.stage_configs = stage_configs
        self.current_stage_index: int = 0
        self.stage_entry_cycle: int = 0
        self.stage_entry_sim_hours: float = 0.0
        self._prev_node_count: int = 0
        self._prev_connection_density: float = 0.0

    def get_current_stage(self) -> Optional["StageConfig"]:
        """Return current stage configuration."""
        if not self.stage_configs:
            return None
        return self.stage_configs[self.current_stage_index]

    def check_completion(self, network, cycle: int, sim_hours: float) -> bool:
        """
        Check if current stage completion conditions are met.
        Returns True if stage should advance.
        """
        stage = self.get_current_stage()
        if stage is None:
            return False

        condition = stage.completion_condition
        stats = network.global_stats

        if condition == "never":
            return False

        # Time-based completion
        if stage.sim_hours[1] is not None and sim_hours >= stage.sim_hours[1]:
            return True

        # Condition-based checks
        if "node_count" in condition:
            # Parse: "node_count >= 500"
            threshold = self._extract_number(condition, "node_count")
            if stats.node_count >= threshold:
                return True

        if "division_rate" in condition:
            threshold = self._extract_float(condition, "division_rate")
            if stats.division_rate < threshold:
                return True

        if "connection_density" in condition:
            # Parse: "connection_density >= 0.30" or "connection_density <= 0.10"
            if ">=" in condition:
                threshold = self._extract_float(condition, "connection_density")
                if stats.connection_density >= threshold:
                    return True
            elif "<=" in condition:
                threshold = self._extract_float(condition, "connection_density")
                if stats.connection_density <= threshold:
                    return True

        if "sim_hours" in condition:
            threshold = self._extract_number(condition, "sim_hours")
            if sim_hours >= threshold:
                return True

        # Fallback: if we've been in this stage too long, advance
        if sim_hours - self.stage_entry_sim_hours > 100:  # Safety cap
            return True

        return False

    def advance_stage(self):
        """Switch to next development stage."""
        if self.current_stage_index < len(self.stage_configs) - 1:
            old_stage = self.stage_configs[self.current_stage_index]
            self.current_stage_index += 1
            new_stage = self.stage_configs[self.current_stage_index]
            self.stage_entry_cycle = self._current_cycle
            self.stage_entry_sim_hours = self._current_sim_hours
            return True
        return False

    def set_cycle_info(self, cycle: int, sim_hours: float):
        """Update current cycle and sim hours tracking."""
        self._current_cycle = cycle
        self._current_sim_hours = sim_hours

    def get_stage_name(self) -> str:
        stage = self.get_current_stage()
        return stage.name if stage else "unknown"

    @staticmethod
    def _extract_number(text: str, field: str) -> int:
        """Extract integer threshold from condition string."""
        import re
        match = re.search(rf'{field}\s*>=\s*(\d+)', text)
        if match:
            return int(match.group(1))
        match = re.search(rf'{field}\s*<=\s*(\d+)', text)
        if match:
            return int(match.group(1))
        return 0

    @staticmethod
    def _extract_float(text: str, field: str) -> float:
        """Extract float threshold from condition string."""
        import re
        match = re.search(rf'{field}\s*[><=]+\s*([\d.]+)', text)
        if match:
            return float(match.group(1))
        return 0.0
