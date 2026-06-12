"""Motor Output — projector activation → 12 action primitives decoding."""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from dna.schema import ACTION_PRIMITIVES
from notion.notion_cell import NotionType


class MotorDecoder:
    """
    Decode projector node activations into 12 action primitive weights.
    """

    def __init__(self, decode_matrix: np.ndarray = None, vector_dim: int = 64):
        """
        Args:
            decode_matrix: shape=(vector_dim, 12). If None, randomly initialized.
            vector_dim: dimension of projector vectors.
        """
        if decode_matrix is not None:
            self.decode_matrix = decode_matrix
        else:
            # Random initialization, fixed during development
            self.decode_matrix = np.random.randn(vector_dim, len(ACTION_PRIMITIVES)) * 0.1

    def decode(self, projector_nodes: List) -> Dict[str, float]:
        """
        Sum all projector node activation vectors, multiply by decode matrix.
        Returns dict of action_name → weight.
        """
        if not projector_nodes:
            return {name: 0.0 for name in ACTION_PRIMITIVES}

        # Sum all projector activations
        total_activation = np.zeros(self.decode_matrix.shape[0])
        for node in projector_nodes:
            if node.activation > 0:
                # Weight by activation strength
                node_vec = node.vector * node.activation
                # Pad or trim to match decode_matrix input dimension
                dim = min(len(node_vec), len(total_activation))
                total_activation[:dim] += node_vec[:dim]

        # Decode to action weights
        action_weights = total_activation @ self.decode_matrix

        # Softmax-like normalization to [0, 1]
        action_weights = action_weights - action_weights.min()
        total = action_weights.sum()
        if total > 0:
            action_weights = action_weights / total

        return {name: float(w) for name, w in zip(ACTION_PRIMITIVES, action_weights)}

    def select_actions(self, weights: Dict[str, float],
                        top_k: int = 3) -> List[tuple]:
        """
        Select top_k actions by weight.
        Returns list of (action_name, weight) sorted by weight desc.
        """
        sorted_actions = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        return sorted_actions[:top_k]

    def execute_action(self, action_name: str, weight: float, world_state: dict):
        """
        Execute a single action, modifying world state.
        
        Args:
            action_name: one of ACTION_PRIMITIVES
            weight: action weight/strength [0, 1]
            world_state: dict with keys like 'position', 'energy', 'resources', etc.
        """
        if action_name == "MOVE_FORWARD":
            pos = world_state.get('position')
            heading = world_state.get('heading', np.array([1, 0, 0]))
            if pos is not None:
                world_state['position'] = pos + heading * weight * 2.0

        elif action_name == "MOVE_BACKWARD":
            pos = world_state.get('position')
            heading = world_state.get('heading', np.array([1, 0, 0]))
            if pos is not None:
                world_state['position'] = pos - heading * weight * 2.0

        elif action_name == "TURN_LEFT":
            heading = world_state.get('heading', np.array([1, 0, 0]))
            # Rotate 90 degrees left in x-y plane
            angle = weight * np.pi / 4
            c, s = np.cos(angle), np.sin(angle)
            rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            world_state['heading'] = rot @ heading

        elif action_name == "TURN_RIGHT":
            heading = world_state.get('heading', np.array([1, 0, 0]))
            angle = -weight * np.pi / 4
            c, s = np.cos(angle), np.sin(angle)
            rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            world_state['heading'] = rot @ heading

        elif action_name == "APPROACH":
            target = world_state.get('nearest_resource_pos')
            pos = world_state.get('position')
            if target is not None and pos is not None:
                direction = target - pos
                dist = np.linalg.norm(direction)
                if dist > 0:
                    world_state['position'] = pos + (direction / dist) * weight * 3.0

        elif action_name == "RETREAT":
            threat = world_state.get('nearest_threat_pos')
            pos = world_state.get('position')
            if threat is not None and pos is not None:
                direction = pos - threat
                dist = np.linalg.norm(direction)
                if dist > 0:
                    world_state['position'] = pos + (direction / dist) * weight * 3.0

        elif action_name == "CONSUME":
            resources = world_state.get('resources')
            pos = world_state.get('position')
            if resources and pos is not None:
                visible = resources.get_visible_resources(pos, vision_radius=5.0)
                if visible:
                    res = visible[0]  # Consume nearest
                    gained = resources.consume(res.id, weight * 10.0)
                    world_state['energy'] = world_state.get('energy', 0) + gained

        elif action_name == "REST":
            # Restore energy slowly
            world_state['energy'] = world_state.get('energy', 0) + weight * 0.5

        elif action_name == "EMIT_SIGNAL":
            # Publish a signal event (handled by world engine)
            world_state.setdefault('emitted_signals', []).append({
                'strength': weight,
                'position': world_state.get('position'),
            })

        elif action_name == "GROW_SPLIT":
            # Signal desire to split (handled by network division logic)
            world_state['split_request'] = weight

        elif action_name == "CONNECT_ATTEMPT":
            # Signal desire to form new connections
            world_state['connect_request'] = weight

        elif action_name == "SELF_MONITOR":
            # Internal state monitoring (no external effect)
            pass
