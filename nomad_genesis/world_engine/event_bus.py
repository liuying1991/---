"""Event Bus — publish/subscribe system for world state changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Any
from collections import defaultdict


# Event type constants
EVENT_COLLISION = "EVENT_COLLISION"
EVENT_RESOURCE_NEAR = "EVENT_RESOURCE_NEAR"
EVENT_SIGNAL_RECEIVED = "EVENT_SIGNAL_RECEIVED"
EVENT_TIME_PHASE = "EVENT_TIME_PHASE"
EVENT_DAMAGE = "EVENT_DAMAGE"
EVENT_CONSUME = "EVENT_CONSUME"


@dataclass
class Event:
    type: str
    payload: Dict[str, Any]
    cycle: int = 0


class EventBus:
    """
    World state change event bus.
    All world state changes are published through the event bus.
    """

    def __init__(self):
        self._subscribers: Dict[str, Set[str]] = defaultdict(set)  # entity_id → set of event_types
        self._events: List[Event] = []  # All events this cycle
        self._entity_events: Dict[str, List[Event]] = defaultdict(list)  # entity_id → events
        self._cycle: int = 0

    def publish(self, event_type: str, payload: Dict[str, Any]):
        """Publish an event to the bus."""
        event = Event(type=event_type, payload=payload, cycle=self._cycle)
        self._events.append(event)

        # Route to interested subscribers
        target = payload.get('target_entity')
        if target and target in self._subscribers:
            interested_types = self._subscribers[target]
            if event_type in interested_types or '*' in interested_types:
                self._entity_events[target].append(event)

    def subscribe(self, entity_id: str, event_types: List[str]):
        """Subscribe an entity to specific event types."""
        self._subscribers[entity_id].update(event_types)

    def unsubscribe(self, entity_id: str, event_types: List[str] = None):
        """Unsubscribe an entity from events."""
        if event_types:
            for et in event_types:
                self._subscribers[entity_id].discard(et)
        else:
            self._subscribers.pop(entity_id, None)

    def get_events(self, entity_id: str) -> List[Event]:
        """Get all events for an entity this cycle."""
        return list(self._entity_events.get(entity_id, []))

    def get_all_events(self) -> List[Event]:
        """Get all events this cycle."""
        return list(self._events)

    def clear_cycle(self):
        """Clear events after each cycle."""
        self._events.clear()
        self._entity_events.clear()

    def set_cycle(self, cycle: int):
        """Set current cycle number."""
        self._cycle = cycle

    def publish_collision(self, entity_a: str, entity_b: str, force: float = 1.0):
        """Publish a collision event."""
        self.publish(EVENT_COLLISION, {
            'entity_a': entity_a,
            'entity_b': entity_b,
            'force': force,
        })

    def publish_resource_near(self, resource_id: str, distance: float,
                               direction: List[float], target_entity: str = None):
        """Publish a resource proximity event."""
        self.publish(EVENT_RESOURCE_NEAR, {
            'resource_id': resource_id,
            'distance': distance,
            'direction': direction,
            'target_entity': target_entity,
        })

    def publish_time_phase(self, phase: str):
        """Publish a time phase change event."""
        self.publish(EVENT_TIME_PHASE, {'phase': phase})

    def publish_consume(self, resource_id: str, energy_gained: float,
                         consumer_id: str = None):
        """Publish a resource consumption event."""
        self.publish(EVENT_CONSUME, {
            'resource_id': resource_id,
            'energy_gained': energy_gained,
            'target_entity': consumer_id,
        })
