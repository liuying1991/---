"""Notion Cell — single node in the self-organizing network."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np


class NotionType(str, Enum):
    STEM = "STEM"
    SENSOR = "SENSOR"
    INTERNEURON = "INTERNEURON"
    INHIBITOR = "INHIBITOR"
    OSCILLATOR = "OSCILLATOR"
    PROJECTOR = "PROJECTOR"
    HUB = "HUB"
    MEMORY = "MEMORY"
    GATE = "GATE"


@dataclass
class Notion:
    id: str
    type: NotionType
    vector: np.ndarray                # shape=(dim,)
    threshold: float                  # activation threshold
    plasticity: float                 # [0,1]
    energy: float                     # current energy
    position: np.ndarray              # (3,) spatial coordinates
    activation: float = 0.0           # current activation [0,1]
    potential: float = 0.0            # internal potential (pre-activation)
    activation_history: field = field(default_factory=lambda: [])
    division_count: int = 0
    connections: Dict[str, float] = field(default_factory=dict)  # neighbor_id → weight
    oscillator_period: Optional[int] = None
    oscillator_phase: Optional[int] = None
    born_at_stage: str = ""
    idle_cycles: int = 0              # cycles since last fire
    inhibitory_cycles: int = 0        # consecutive cycles receiving inhibitory signals
    last_activation_cycle: int = -1   # cycle of last activation

    # Statistics tracking
    total_input_signal: float = 0.0   # accumulated input for differentiation
    input_count: int = 0              # number of inputs received
    fire_count: int = 0               # total fires

    def receive_signal(self, strength: float):
        """Receive an input signal, accumulate to internal potential."""
        self.potential += strength
        self.total_input_signal += strength
        self.input_count += 1

    def fire(self, base_metabolism: float = 1.0) -> bool:
        """
        Check if the node fires this cycle.
        Firing condition: potential > threshold × energy_coefficient
        """
        energy_coeff = min(1.0, self.energy / max(base_metabolism, 0.001))
        # If energy too low, cannot fire
        if energy_coeff < 0.1:
            return False
        effective_threshold = self.threshold / energy_coeff
        if self.potential > effective_threshold:
            self.fire_count += 1
            self.last_activation_cycle = -1  # will be set by caller
            return True
        return False

    def reset_potential(self):
        """Reset internal potential after firing or silence."""
        self.potential = 0.0

    def can_divide(self, division_rules) -> bool:
        """Check if this node satisfies division conditions."""
        if self.division_count >= division_rules.max_divisions:
            return False
        if self.energy < division_rules.energy_threshold:
            return False
        if self.type != NotionType.STEM:
            return False
        return True

    @classmethod
    def create_stem(cls, vector_dim: int, position: np.ndarray,
                    base_metabolism: float = 1.0, born_at_stage: str = "embryonic") -> "Notion":
        """Create a new STEM cell with random vector."""
        return cls(
            id=str(uuid.uuid4())[:8],
            type=NotionType.STEM,
            vector=np.random.randn(vector_dim) * 0.1,
            threshold=0.5,
            plasticity=1.0,
            energy=base_metabolism * 2.0,
            position=position.copy(),
            born_at_stage=born_at_stage,
        )

    @property
    def degree(self) -> int:
        return len(self.connections)
