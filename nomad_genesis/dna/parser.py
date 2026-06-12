"""DNA Seed Parser — YAML → DNAConfig objects."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import List, Optional

from .schema import (
    DNAConfig, MetaConfig, InitialConfig, DivisionRules,
    DifferentiationRules, ConnectionRules, StageConfig,
    SensorDiffRules, InterneuronDiffRules, InhibitorDiffRules,
    OscillatorDiffRules, ProjectorDiffRules, HubDiffRules,
    MemoryDiffRules, GateDiffRules, ActionConfig,
    SelfReferenceConfig, IntergenerationalConfig,
)


def _parse_stages(raw: list) -> List[StageConfig]:
    stages = []
    for s in raw:
        stages.append(StageConfig(
            name=s["name"],
            sim_hours=tuple(s["sim_hours"]),
            plasticity=s.get("plasticity", 1.0),
            connection_radius_mult=s.get("connection_radius_mult", 1.0),
            pruning=s.get("pruning", False),
            completion_condition=s.get("completion_condition", "never"),
        ))
    return stages


def _parse_diff(raw: dict) -> DifferentiationRules:
    return DifferentiationRules(
        sensor=SensorDiffRules(**raw.get("sensor", {})),
        interneuron=InterneuronDiffRules(**raw.get("interneuron", {})),
        inhibitor=InhibitorDiffRules(**raw.get("inhibitor", {})),
        oscillator=OscillatorDiffRules(**raw.get("oscillator", {})),
        projector=ProjectorDiffRules(**raw.get("projector", {})),
        hub=HubDiffRules(**raw.get("hub", {})),
        memory=MemoryDiffRules(**raw.get("memory", {})),
        gate=GateDiffRules(**raw.get("gate", {})),
    )


def load_dna(yaml_path: str) -> DNAConfig:
    """Load a DNA seed from a YAML file."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"DNA seed not found: {yaml_path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    meta_raw = raw.get("meta", {})
    initial_raw = raw.get("initial_config", {})
    division_raw = raw.get("division_rules", {})
    diff_raw = raw.get("differentiation_rules", {})
    conn_raw = raw.get("connection_rules", {})
    stages_raw = raw.get("development_stages", [])
    actions_raw = raw.get("action_primitives", {})
    self_ref_raw = raw.get("self_reference", {})
    intergen_raw = raw.get("intergenerational", {})

    return DNAConfig(
        meta=MetaConfig(**meta_raw),
        initial=InitialConfig(**initial_raw),
        division=DivisionRules(**division_raw),
        differentiation=_parse_diff(diff_raw),
        connection=ConnectionRules(**conn_raw),
        stages=_parse_stages(stages_raw),
        actions=ActionConfig(**actions_raw),
        self_ref=SelfReferenceConfig(**self_ref_raw),
        intergen=IntergenerationalConfig(**intergen_raw),
    )


def validate_dna(config: DNAConfig) -> List[str]:
    """Validate a DNAConfig, returning a list of error strings (empty = valid)."""
    errors: List[str] = []

    if config.initial.stem_count < 1:
        errors.append("stem_count must be >= 1")
    if config.initial.vector_dim < 1:
        errors.append("vector_dim must be >= 1")
    if config.initial.vector_dim > config.initial.max_vector_dim:
        errors.append("vector_dim must be <= max_vector_dim")
    if config.connection.base_prob < 0 or config.connection.base_prob > 1:
        errors.append("connection base_prob must be in [0, 1]")
    if not config.stages:
        errors.append("at least one development stage is required")
    if config.division.max_divisions < 1:
        errors.append("max_divisions must be >= 1")

    # Validate stage continuity
    for i, stage in enumerate(config.stages):
        if stage.sim_hours[0] is not None and stage.sim_hours[0] < 0:
            errors.append(f"stage '{stage.name}' start time must be >= 0")
        if stage.plasticity < 0 or stage.plasticity > 1:
            errors.append(f"stage '{stage.name}' plasticity must be in [0, 1]")

    return errors


def modify_seed(
    config: DNAConfig,
    feedback: dict,
    modification_weight: float = 0.3
) -> DNAConfig:
    """
    Modify a seed based on experience feedback for intergenerational transfer.
    feedback: dict with keys like 'final_connection_density', 'effective_inhibitor_ratio', etc.
    modification_weight: how much to blend experience into the new seed.
    """
    import copy
    new_config = copy.deepcopy(config)

    # Blend connection rules based on experience
    if "final_connection_density" in feedback:
        target = feedback["final_connection_density"]
        new_config.connection.base_prob = (
            (1 - modification_weight) * config.connection.base_prob
            + modification_weight * target
        )

    if "effective_inhibitor_ratio" in feedback:
        target = feedback["effective_inhibitor_ratio"]
        # Adjust inhibitor conversion probability
        new_config.differentiation.inhibitor.conversion_prob = (
            (1 - modification_weight) * config.differentiation.inhibitor.conversion_prob
            + modification_weight * target
        )

    if "oscillator_sync_index" in feedback:
        sync = feedback["oscillator_sync_index"]
        # Adjust oscillator period range based on sync quality
        current_range = config.differentiation.oscillator.period_range
        new_min = int((1 - modification_weight) * current_range[0] + modification_weight * max(5, current_range[0] * (1 - sync)))
        new_max = int((1 - modification_weight) * current_range[1] + modification_weight * min(1000, current_range[1] * (1 + sync)))
        new_config.differentiation.oscillator.period_range = (new_min, new_max)

    return new_config
