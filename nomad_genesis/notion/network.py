"""Notion Network Manager — manages the 800-node self-organizing network."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from notion.notion_cell import Notion, NotionType
from world_engine.space import SpatialHashGrid


@dataclass
class NetworkStats:
    """Global network statistics snapshot."""
    node_count: int = 0
    mean_activation: float = 0.0
    total_energy: float = 0.0
    total_edges: int = 0
    type_counts: Dict[str, int] = field(default_factory=dict)
    mean_degree: float = 0.0
    division_rate: float = 0.0
    connection_density: float = 0.0


class NotionNetwork:
    """
    Manage the collection of Notion nodes.
    Provides O(1) node queries, O(k) neighbor queries.
    """

    def __init__(self, config, stage_tracker=None):
        self.config = config
        self.nodes: Dict[str, Notion] = {}
        self.spatial_hash = SpatialHashGrid(cell_size=10.0)
        self.global_stats = NetworkStats()
        self.stage_tracker = stage_tracker
        self._total_divisions_ever: int = 0
        self._last_division_count: int = 0
        self._cycle: int = 0

    def add_node(self, notion: Notion):
        """Add a node to the network."""
        self.nodes[notion.id] = notion
        self.spatial_hash.insert(notion.id, notion.position)

    def remove_node(self, node_id: str):
        """Remove a node from the network."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            # Remove all connections to this node
            for neighbor_id in list(node.connections.keys()):
                neighbor = self.nodes.get(neighbor_id)
                if neighbor:
                    neighbor.connections.pop(node_id, None)
            self.spatial_hash.remove(node_id)
            del self.nodes[node_id]

    def get_node(self, node_id: str) -> Optional[Notion]:
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, max_dist: float) -> List[Notion]:
        """Get spatial neighbors within max_dist."""
        pos = self.nodes[node_id].position if node_id in self.nodes else None
        if pos is None:
            return []
        nearby_ids = self.spatial_hash.get_nearby_entities(pos, max_dist)
        return [self.nodes[nid] for nid in nearby_ids if nid in self.nodes and nid != node_id]

    def get_nodes_by_type(self, ntype: NotionType) -> List[Notion]:
        """Get all nodes of a specific type."""
        return [n for n in self.nodes.values() if n.type == ntype]

    def get_total_connections(self) -> int:
        """Total number of unique connections in the network."""
        total = sum(len(n.connections) for n in self.nodes.values())
        return total // 2  # Each connection counted twice

    def update_stats(self):
        """Update global statistics at end of cycle."""
        n = len(self.nodes)
        if n == 0:
            self.global_stats = NetworkStats()
            return

        activations = [nd.activation for nd in self.nodes.values()]
        degrees = [len(nd.connections) for nd in self.nodes.values()]
        energies = [nd.energy for nd in self.nodes.values()]

        type_counts = {}
        for nd in self.nodes.values():
            type_counts[nd.type.value] = type_counts.get(nd.type.value, 0) + 1

        total_edges = self.get_total_connections()
        max_possible_edges = n * (n - 1) // 2 if n > 1 else 1

        # Division rate: divisions this cycle / total nodes
        divisions_this_cycle = self._total_divisions_ever - self._last_division_count
        self._last_division_count = self._total_divisions_ever

        self.global_stats = NetworkStats(
            node_count=n,
            mean_activation=float(np.mean(activations)) if activations else 0.0,
            total_energy=float(sum(energies)),
            total_edges=total_edges,
            type_counts=type_counts,
            mean_degree=float(np.mean(degrees)) if degrees else 0.0,
            division_rate=divisions_this_cycle / max(n, 1),
            connection_density=total_edges / max_possible_edges,
        )

    def step(self, cycle: int, events, current_stage):
        """
        One cycle of the core processing loop.

        Order:
          1. Input processing (sensor nodes)
          2. Oscillator firing
          3. Signal propagation (all nodes fire/not fire)
          4. Plasticity update
          5. Division
          6. Differentiation
          7. Connection establishment
          8. Metabolism update
          9. Global stats update
        """
        self._cycle = cycle

        # === Step 1: Input processing ===
        self._process_sensors(events)

        # === Step 2: Oscillator firing ===
        from notion.oscillator import update_oscillators
        update_oscillators(self, cycle)

        # === Step 3: Signal propagation ===
        fired_ids = self._propagate_signals(cycle)

        # === Step 4: Plasticity update ===
        from notion.plasticity import update_plasticity
        update_plasticity(self, cycle, current_stage)

        # === Step 5: Division ===
        from notion.division import process_divisions
        new_count = process_divisions(self, cycle)
        self._total_divisions_ever += new_count

        # === Step 6: Differentiation ===
        self._process_differentiations(cycle)

        # === Step 7: Connection establishment ===
        from notion.connection import establish_connections
        if not current_stage.pruning or cycle % 10 == 0:
            establish_connections(self, current_stage)

        # === Step 8: Metabolism update ===
        self._update_metabolism(cycle, fired_ids)

        # === Step 9: Global stats ===
        self.update_stats()

    def _process_sensors(self, events):
        """Route events to sensor nodes and add internal noise for baseline activation."""
        import random
        sensors = self.get_nodes_by_type(NotionType.SENSOR)
        for sensor in sensors:
            if events:
                from notion.activation import compute_signal_strength
                strength = compute_signal_strength(events, sensor)
                sensor.receive_signal(strength)

        # Internal noise: all nodes receive small random signals to maintain baseline activity
        for nd in self.nodes.values():
            noise = random.gauss(0, 0.3)
            nd.receive_signal(abs(noise) * 0.8)
        
        # Spontaneous firing for STEM cells (embryonic spontaneous activity)
        for nd in self.get_nodes_by_type(NotionType.STEM):
            if nd.energy > self.config.initial.base_metabolism * 0.5:
                if random.random() < 0.05:  # 5% chance per cycle
                    nd.receive_signal(1.5)  # Strong enough to fire
        
        # Spontaneous activity for all nodes (baseline neural activity)
        for nd in self.nodes.values():
            if nd.energy > self.config.initial.base_metabolism * 0.3:
                if random.random() < 0.03:  # 3% chance per cycle
                    nd.receive_signal(1.2)  # Strong enough to fire

        # Self-sensor sampling
        self_sensors = self.get_nodes_by_type(NotionType.GATE)  # GATE acts as self-sensor
        interval = self.config.self_ref.self_sensor_sample_interval
        if self._cycle % interval == 0:
            state_vector = self._sample_internal_state()
            norm_state = float(np.linalg.norm(state_vector))
            for ss in self_sensors:
                ss.receive_signal(norm_state)

    def _sample_internal_state(self) -> np.ndarray:
        """Sample internal network state as a vector."""
        activations = np.array([nd.activation for nd in self.nodes.values()])
        energies = np.array([nd.energy for nd in self.nodes.values()])
        # Combine into a summary vector
        state = np.concatenate([
            activations[:self.config.initial.vector_dim],
            energies[:max(0, self.config.initial.vector_dim - len(activations))],
        ])
        # Pad or trim to vector_dim
        if len(state) < self.config.initial.vector_dim:
            state = np.pad(state, (0, self.config.initial.vector_dim - len(state)))
        else:
            state = state[:self.config.initial.vector_dim]
        return state

    def _propagate_signals(self, cycle: int) -> List[str]:
        """
        All nodes determine whether to fire, then propagate signals along connections.
        Returns list of node IDs that fired.
        """
        base_meta = self.config.initial.base_metabolism
        fired = []

        # Determine firing
        for nd in self.nodes.values():
            if nd.fire(base_meta):
                fired.append(nd.id)
                nd.activation = 1.0
                nd.idle_cycles = 0
                nd.inhibitory_cycles = 0
            else:
                nd.activation = 0.0
                nd.idle_cycles += 1
                # Track if receiving inhibitory signals
                has_inhibitory_input = any(
                    w < 0 for w in nd.connections.values()
                )
                if has_inhibitory_input:
                    nd.inhibitory_cycles += 1

            nd.activation_history.append(nd.activation)
            # Keep history bounded
            if len(nd.activation_history) > 1000:
                nd.activation_history = nd.activation_history[-500:]
            nd.last_activation_cycle = cycle

        # Propagate signals from fired nodes
        for src_id in fired:
            src = self.nodes.get(src_id)
            if src is None:
                continue
            for dst_id, weight in src.connections.items():
                dst = self.nodes.get(dst_id)
                if dst is None:
                    continue
                # Amplify signal propagation for better network activity
                signal_strength = weight * src.activation
                if weight > 0:  # Excitatory connections
                    signal_strength *= 1.5  # Boost excitatory signals
                dst.receive_signal(signal_strength)

        # Reset potential for all nodes after propagation
        for nd in self.nodes.values():
            nd.reset_potential()

        return fired

    def _process_differentiations(self, cycle: int):
        """Check and apply differentiation for eligible nodes."""
        from notion.differentiation import check_differentiation, apply_differentiation

        nodes_to_diff = []
        for node_id, nd in list(self.nodes.items()):
            new_type = check_differentiation(nd, self)
            if new_type is not None:
                nodes_to_diff.append((nd, new_type))

        for nd, new_type in nodes_to_diff:
            apply_differentiation(nd, new_type, self)

    def _update_metabolism(self, cycle: int, fired_ids: List[str]):
        """
        Per-cycle metabolism:
          - Each node consumes base metabolic energy
          - Passive energy regeneration from ambient resources (0.015/cycle)
          - Fired nodes consume 2x extra
          - Divided nodes consume 10x extra
          - Low energy -> reduced plasticity
          - Dead nodes (energy <= 0 AND isolated) -> apoptosis
        """
        base_meta = self.config.initial.base_metabolism
        nodes_to_remove = []

        for node_id, nd in self.nodes.items():
            # Base metabolism
            nd.energy -= base_meta * 0.01

            # Passive energy regeneration (ambient resources)
            nd.energy += base_meta * 0.015

            # Cap energy at reasonable level
            max_energy = base_meta * 5.0
            if nd.energy > max_energy:
                nd.energy = max_energy

            # Firing cost
            if node_id in fired_ids:
                nd.energy -= base_meta * 0.02

            # Division cost (approximate)
            if nd.division_count > 0 and cycle % 100 == 0:
                nd.energy -= base_meta * 0.1

            # Low energy effects
            if nd.energy < base_meta * 0.5:
                nd.plasticity *= 0.99
            if nd.energy < base_meta * 0.1:
                nd.activation = 0.0
                nd.plasticity *= 0.9

            # Apoptosis check
            if nd.energy <= 0 and len(nd.connections) == 0:
                nodes_to_remove.append(node_id)

        for node_id in nodes_to_remove:
            self.remove_node(node_id)

    def init_stem_cells(self):
        """Initialize the network with initial stem cells."""
        stem_count = self.config.initial.stem_count
        vector_dim = self.config.initial.vector_dim
        base_meta = self.config.initial.base_metabolism

        for i in range(stem_count):
            # Random position in a larger cluster to reduce initial density
            pos = np.random.randn(3) * 30.0
            stem = Notion.create_stem(vector_dim, pos, base_meta, "embryonic", birth_cycle=0)
            self.add_node(stem)
