"""Sensory Input — world events → sensor node activation mapping."""

from __future__ import annotations

from typing import List

from notion.notion_cell import Notion, NotionType
from world_engine.event_bus import Event, EVENT_COLLISION, EVENT_RESOURCE_NEAR
from world_engine.event_bus import EVENT_SIGNAL_RECEIVED, EVENT_CONSUME


class SensoryMapper:
    """
    Convert world engine event bus output to structured signals for sensor nodes.
    """

    # Map event types to sensor sensitivity weights
    EVENT_SENSITIVITY = {
        EVENT_COLLISION: 1.0,
        EVENT_RESOURCE_NEAR: 0.8,
        EVENT_SIGNAL_RECEIVED: 0.6,
        EVENT_CONSUME: 0.5,
    }

    def map_events_to_sensors(self, events: List[Event],
                               sensors: List[Notion],
                               self_sensors: List[Notion] = None):
        """
        Route events to appropriate sensor nodes.
        Each sensor receives signals based on its sensitivity to the event type.
        """
        if not sensors or not events:
            return

        for sensor in sensors:
            total_signal = 0.0
            for event in events:
                sensitivity = self.EVENT_SENSITIVITY.get(event.type, 0.3)
                # Compute signal from event payload
                signal = self._compute_event_signal(event, sensor)
                total_signal += signal * sensitivity

            if total_signal > 0:
                sensor.receive_signal(total_signal)

    def _compute_event_signal(self, event: Event, sensor: Notion) -> float:
        """
        Convert a single event to signal strength for this sensor.
        Uses sensor vector magnitude and event payload values.
        """
        import numpy as np
        
        payload = event.payload
        if not payload:
            return 0.0

        if event.type == EVENT_COLLISION:
            force = payload.get('force', 0)
            return float(force * np.linalg.norm(sensor.vector))

        elif event.type == EVENT_RESOURCE_NEAR:
            distance = payload.get('distance', float('inf'))
            if distance <= 0:
                return 0.0
            return 1.0 / distance  # Closer = stronger signal

        elif event.type == EVENT_SIGNAL_RECEIVED:
            sender_vec = payload.get('signal_vector')
            if sender_vec is not None:
                return float(np.dot(sensor.vector, sender_vec))
            return 0.0

        elif event.type == EVENT_CONSUME:
            energy = payload.get('energy_gained', 0)
            return float(energy * 0.1)

        # Default: sum of numeric payload values
        total = sum(abs(v) for v in payload.values() if isinstance(v, (int, float)))
        return float(total * 0.1)

    def route_self_sensors(self, network, self_sensors: List[Notion],
                            sample_interval: int, cycle: int):
        """
        Route internal network state to self-sensor nodes.
        Samples every sample_interval cycles.
        """
        if not self_sensors or cycle % sample_interval != 0:
            return

        import numpy as np
        
        # Sample internal state
        activations = np.array([n.activation for n in network.nodes.values()])
        energies = np.array([n.energy for n in network.nodes.values()])
        
        if len(activations) == 0:
            return

        state_norm = float(np.linalg.norm(activations))
        energy_mean = float(np.mean(energies))
        
        for ss in self_sensors:
            ss.receive_signal(state_norm * 0.1 + energy_mean * 0.05)
