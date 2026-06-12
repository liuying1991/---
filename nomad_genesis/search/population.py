"""Population Management — generate and save DNA seed populations."""

from __future__ import annotations

import yaml
import os
from pathlib import Path
from typing import List

from dna.schema import DNAConfig
from dna.parser import load_dna
from search.param_space import ParamSpace


class Population:
    """
    Manage a population of 200 DNA seeds (parameter combinations + template YAML).
    """

    def __init__(self, template_yaml_path: str):
        self.template = load_dna(template_yaml_path)
        self.param_space = ParamSpace()

    def generate(self, count: int) -> List[DNAConfig]:
        """Generate count DNA seeds from template + parameter sampling."""
        samples = self.param_space.sample(count)
        configs = []
        for i, params in enumerate(samples):
            config = self.param_space.apply_to_config(self.template, params)
            config.meta.name = f"pop_{i:04d}"
            config.meta.version = f"search_{i:04d}"
            configs.append(config)
        return configs

    def save_seed(self, config: DNAConfig, path: str):
        """Save a seed as an independent YAML file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Convert DNAConfig to dict for YAML serialization
        seed_dict = self._config_to_dict(config)

        with open(path, 'w') as f:
            yaml.dump(seed_dict, f, default_flow_style=False, sort_keys=False)

    def save_population(self, configs: List[DNAConfig], output_dir: str):
        """Save entire population as individual YAML files."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        paths = []
        for config in configs:
            filename = f"{config.meta.name}.yaml"
            path = os.path.join(output_dir, filename)
            self.save_seed(config, path)
            paths.append(path)
        return paths

    def _config_to_dict(self, config: DNAConfig) -> dict:
        """Convert DNAConfig to a YAML-serializable dict."""
        return {
            'meta': {
                'version': config.meta.version,
                'name': config.meta.name,
            },
            'initial_config': {
                'stem_count': config.initial.stem_count,
                'vector_dim': config.initial.vector_dim,
                'max_vector_dim': config.initial.max_vector_dim,
                'connection_radius': config.initial.connection_radius,
                'base_metabolism': config.initial.base_metabolism,
            },
            'division_rules': {
                'energy_threshold': config.division.energy_threshold,
                'max_local_density': config.division.max_local_density,
                'max_divisions': config.division.max_divisions,
                'mutation_sigma': config.division.mutation_sigma,
                'apoptosis_energy': config.division.apoptosis_energy,
                'apoptosis_isolation': config.division.apoptosis_isolation,
            },
            'differentiation_rules': {
                'sensor': {
                    'input_density_threshold': config.differentiation.sensor.input_density_threshold,
                },
                'interneuron': {
                    'min_connections': config.differentiation.interneuron.min_connections,
                    'activation_freq_ratio': config.differentiation.interneuron.activation_freq_ratio,
                },
                'inhibitor': {
                    'conversion_prob': config.differentiation.inhibitor.conversion_prob,
                },
                'oscillator': {
                    'idle_cycles': config.differentiation.oscillator.idle_cycles,
                    'energy_multiplier': config.differentiation.oscillator.energy_multiplier,
                    'period_range': list(config.differentiation.oscillator.period_range),
                },
                'projector': {
                    'cosine_similarity_threshold': config.differentiation.projector.cosine_similarity_threshold,
                },
                'hub': {
                    'degree_ratio': config.differentiation.hub.degree_ratio,
                },
                'memory': {
                    'intensity_ratio': config.differentiation.memory.intensity_ratio,
                },
                'gate': {
                    'inhibitory_cycles': config.differentiation.gate.inhibitory_cycles,
                },
            },
            'connection_rules': {
                'base_prob': config.connection.base_prob,
                'min_prob': config.connection.min_prob,
                'hebb_increment': config.connection.hebb_increment,
                'hebb_interval': config.connection.hebb_interval,
                'decay_amount': config.connection.decay_amount,
                'decay_interval': config.connection.decay_interval,
                'prune_threshold': config.connection.prune_threshold,
                'prune_inactive_cycles': config.connection.prune_inactive_cycles,
                'hub_monopoly_threshold': config.connection.hub_monopoly_threshold,
            },
            'development_stages': [
                {
                    'name': s.name,
                    'sim_hours': list(s.sim_hours),
                    'plasticity': s.plasticity,
                    'connection_radius_mult': s.connection_radius_mult,
                    'pruning': s.pruning,
                    'completion_condition': s.completion_condition,
                }
                for s in config.stages
            ],
            'action_primitives': {
                'primitives': config.actions.primitives,
                'decode_matrix': config.actions.decode_matrix,
            },
            'self_reference': {
                'self_sensor_sample_interval': config.self_ref.self_sensor_sample_interval,
                'gate_self_regulation': config.self_ref.gate_self_regulation,
                'teii_sample_window': config.self_ref.teii_sample_window,
            },
            'intergenerational': {
                'experience_encoding': config.intergen.experience_encoding,
                'seed_modification_weight': config.intergen.seed_modification_weight,
                'fallback_memory_sampling': config.intergen.fallback_memory_sampling,
            },
        }
