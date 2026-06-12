"""Activation functions and signal strength computation."""

from __future__ import annotations

import numpy as np
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .notion_cell import Notion
    from ..world_engine.event_bus import Event


def sigmoid_activation(potential: float, threshold: float) -> float:
    """
    Sigmoid activation function, output [0,1].
    Steepness factor 10 makes activation switch rapidly near threshold.
    """
    return float(1.0 / (1.0 + np.exp(-10.0 * (potential - threshold))))


def step_activation(potential: float, threshold: float) -> float:
    """Step activation — binary firing."""
    return 1.0 if potential > threshold else 0.0


def compute_signal_strength(events: List, sensor: "Notion") -> float:
    """
    Convert events to signal strength for this sensor.
    Uses dot product of sensor vector with event feature vectors.
    """
    if not events:
        return 0.0
    total = 0.0
    for event in events:
        # Simple: sum of payload magnitudes weighted by sensor type relevance
        payload = getattr(event, 'payload', {})
        if isinstance(payload, dict):
            magnitude = sum(abs(v) for v in payload.values() if isinstance(v, (int, float)))
            total += magnitude
    # Normalize by number of events and sensor's own vector magnitude
    vec_mag = np.linalg.norm(sensor.vector)
    if vec_mag > 0:
        total /= max(len(events), 1)
        total *= min(vec_mag, 1.0)
    return float(total)
