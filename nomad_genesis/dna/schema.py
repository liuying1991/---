"""DNA Seed Schema — dataclass definitions for all seed configuration sections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# Initial Configuration
# ──────────────────────────────────────────────

@dataclass
class InitialConfig:
    stem_count: int = 10
    vector_dim: int = 64
    max_vector_dim: int = 256
    connection_radius: float = 10.0
    base_metabolism: float = 1.0


# ──────────────────────────────────────────────
# Division Rules
# ──────────────────────────────────────────────

@dataclass
class DivisionRules:
    energy_threshold: float = 2.0
    max_local_density: float = 0.8
    max_divisions: int = 7
    mutation_sigma: float = 0.05
    apoptosis_energy: float = 0.1
    apoptosis_isolation: bool = True


# ──────────────────────────────────────────────
# Differentiation Rules
# ──────────────────────────────────────────────

@dataclass
class SensorDiffRules:
    input_density_threshold: float = 0.3


@dataclass
class InterneuronDiffRules:
    min_connections: int = 3
    activation_freq_ratio: float = 1.0


@dataclass
class InhibitorDiffRules:
    conversion_prob: float = 0.20


@dataclass
class OscillatorDiffRules:
    idle_cycles: int = 200
    energy_multiplier: float = 3.0
    period_range: tuple = field(default_factory=lambda: (10, 200))


@dataclass
class ProjectorDiffRules:
    cosine_similarity_threshold: float = 0.8


@dataclass
class HubDiffRules:
    degree_ratio: float = 2.0


@dataclass
class MemoryDiffRules:
    intensity_ratio: float = 3.0


@dataclass
class GateDiffRules:
    inhibitory_cycles: int = 100


@dataclass
class DifferentiationRules:
    sensor: SensorDiffRules = field(default_factory=SensorDiffRules)
    interneuron: InterneuronDiffRules = field(default_factory=InterneuronDiffRules)
    inhibitor: InhibitorDiffRules = field(default_factory=InhibitorDiffRules)
    oscillator: OscillatorDiffRules = field(default_factory=OscillatorDiffRules)
    projector: ProjectorDiffRules = field(default_factory=ProjectorDiffRules)
    hub: HubDiffRules = field(default_factory=HubDiffRules)
    memory: MemoryDiffRules = field(default_factory=MemoryDiffRules)
    gate: GateDiffRules = field(default_factory=GateDiffRules)


# ──────────────────────────────────────────────
# Connection Rules
# ──────────────────────────────────────────────

@dataclass
class ConnectionRules:
    base_prob: float = 0.05
    min_prob: float = 0.01
    hebb_increment: float = 0.1
    hebb_interval: int = 10
    decay_amount: float = 0.05
    decay_interval: int = 100
    prune_threshold: float = 0.01
    prune_inactive_cycles: int = 500
    hub_monopoly_threshold: float = 0.05


# ──────────────────────────────────────────────
# Development Stage Configuration
# ──────────────────────────────────────────────

@dataclass
class StageConfig:
    name: str
    sim_hours: tuple  # (start, end) — end can be None for last stage
    plasticity: float = 1.0
    connection_radius_mult: float = 1.0
    pruning: bool = False
    completion_condition: str = "never"


# ──────────────────────────────────────────────
# Action Primitives
# ──────────────────────────────────────────────

ACTION_PRIMITIVES = [
    "MOVE_FORWARD", "MOVE_BACKWARD", "TURN_LEFT", "TURN_RIGHT",
    "APPROACH", "RETREAT", "CONSUME", "REST",
    "EMIT_SIGNAL", "GROW_SPLIT", "CONNECT_ATTEMPT", "SELF_MONITOR",
]


@dataclass
class ActionConfig:
    primitives: list = field(default_factory=lambda: list(ACTION_PRIMITIVES))
    decode_matrix: Optional[str] = None  # runtime generated


# ──────────────────────────────────────────────
# Self Reference
# ──────────────────────────────────────────────

@dataclass
class SelfReferenceConfig:
    self_sensor_sample_interval: int = 100
    gate_self_regulation: bool = True
    teii_sample_window: int = 500


# ──────────────────────────────────────────────
# Intergenerational
# ──────────────────────────────────────────────

@dataclass
class IntergenerationalConfig:
    experience_encoding: list = field(default_factory=lambda: [
        "final_hub_distribution",
        "critical_period_durations",
        "final_connection_density",
        "effective_inhibitor_ratio",
        "oscillator_sync_index",
    ])
    seed_modification_weight: float = 0.3
    fallback_memory_sampling: bool = True


# ──────────────────────────────────────────────
# Meta
# ──────────────────────────────────────────────

@dataclass
class MetaConfig:
    version: str = "0.2"
    name: str = "baseline"


# ──────────────────────────────────────────────
# Top-level DNA Configuration
# ──────────────────────────────────────────────

@dataclass
class DNAConfig:
    meta: MetaConfig = field(default_factory=MetaConfig)
    initial: InitialConfig = field(default_factory=InitialConfig)
    division: DivisionRules = field(default_factory=DivisionRules)
    differentiation: DifferentiationRules = field(default_factory=DifferentiationRules)
    connection: ConnectionRules = field(default_factory=ConnectionRules)
    stages: list = field(default_factory=lambda: [])
    actions: ActionConfig = field(default_factory=ActionConfig)
    self_ref: SelfReferenceConfig = field(default_factory=SelfReferenceConfig)
    intergen: IntergenerationalConfig = field(default_factory=IntergenerationalConfig)
