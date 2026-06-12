"""Simulation Clock — tick counter, day/night cycle, elapsed time."""

from __future__ import annotations


TICKS_PER_SIM_HOUR = 1000
DAY_LENGTH_HOURS = 24


class SimClock:
    """
    Simulation time system.
    """

    def __init__(self):
        self._cycle: int = 0
        self._sim_hours: float = 0.0

    def tick(self) -> int:
        """Advance one cycle, return current cycle number."""
        self._cycle += 1
        self._sim_hours = self._cycle / TICKS_PER_SIM_HOUR
        return self._cycle

    def get_sim_time(self) -> float:
        """Return sim hours elapsed."""
        return self._sim_hours

    def get_day_night_phase(self) -> float:
        """
        Return 0~1 phase within the day.
        0 = noon (0h), 0.25 = dusk (6h), 0.5 = midnight (12h), 0.75 = dawn (18h)
        """
        hours_in_day = self._sim_hours % DAY_LENGTH_HOURS
        return hours_in_day / DAY_LENGTH_HOURS

    def get_elapsed_since_birth(self) -> float:
        """Sim hours since simulation start."""
        return self._sim_hours

    def get_time_phase_name(self) -> str:
        """Return descriptive phase name."""
        phase = self.get_day_night_phase()
        if phase < 0.2:
            return "dawn"
        elif phase < 0.45:
            return "day"
        elif phase < 0.55:
            return "dusk"
        else:
            return "night"
