"""Test suite for Nomad Genesis — single seed validation."""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dna.parser import load_dna, validate_dna
from dna.schema import DNAConfig
from notion.network import NotionNetwork
from notion.notion_cell import Notion, NotionType
from monitor.stage_tracker import StageTracker
from monitor.metrics import ConsciousnessMetrics, MetricsResult
from monitor.transfer_entropy import TransferEntropyCalculator
from world_engine.space import Space3D, SpatialHashGrid
from world_engine.time_system import SimClock
from world_engine.event_bus import EventBus
from world_engine.resources import ResourceManager
from world_engine.collision import CollisionDetector
from search.param_space import ParamSpace
from search.scorer import Scorer, RunResult


def test_dna_loading():
    """Test: DNA seed loads and validates."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    assert isinstance(config, DNAConfig)
    assert config.meta.name == "baseline"
    assert config.initial.stem_count == 10
    assert len(config.stages) == 7
    errors = validate_dna(config)
    assert len(errors) == 0, f"Validation errors: {errors}"
    print("[PASS] DNA loading")


def test_space():
    """Test: 3D space operations."""
    space = Space3D()
    space.set_position("a", 0, 0, 0)
    space.set_position("b", 3, 4, 0)
    assert abs(space.distance("a", "b") - 5.0) < 0.01
    nearby = space.get_nearby("a", 10.0)
    assert "b" in nearby
    space.remove_entity("a")
    assert space.get_position("a") is None
    print("[PASS] 3D space")


def test_time():
    """Test: Simulation clock."""
    clock = SimClock()
    for _ in range(1000):
        clock.tick()
    assert clock.get_sim_time() == 1.0
    assert clock.get_day_night_phase() == 1.0 / 24.0
    print("[PASS] Time system")


def test_event_bus():
    """Test: Event bus publish/subscribe."""
    bus = EventBus()
    bus.subscribe("node_1", ["EVENT_COLLISION", "*"])
    bus.publish("EVENT_COLLISION", {"entity_a": "a", "entity_b": "b", "target_entity": "node_1"})
    events = bus.get_events("node_1")
    assert len(events) == 1
    assert events[0].type == "EVENT_COLLISION"
    bus.clear_cycle()
    assert len(bus.get_events("node_1")) == 0
    print("[PASS] Event bus")


def test_resources():
    """Test: Resource management."""
    rm = ResourceManager()
    import numpy as np
    rid = rm.spawn_resource(0, 0, 0, 10.0, 0.1)
    assert rm.consume(rid, 5.0) == 5.0
    assert rm.consume(rid, 5.0) == 5.0
    assert rm.consume(rid, 1.0) == 0.0  # Depleted
    visible = rm.get_visible_resources(np.array([0, 0, 0]), 5.0)
    assert len(visible) >= 1
    print("[PASS] Resources")


def test_collision():
    """Test: Collision detection."""
    space = Space3D()
    space.set_position("a", 0, 0, 0)
    space.set_position("b", 1, 0, 0)
    space.set_position("c", 100, 0, 0)
    detector = CollisionDetector(space)
    assert detector.check_collision("a", "b", 2.0)
    assert not detector.check_collision("a", "c", 2.0)
    collisions = detector.get_collisions(2.0)
    assert ("a", "b") in collisions
    print("[PASS] Collision")


def test_notion_cell():
    """Test: Notion cell creation and firing."""
    import numpy as np
    node = Notion.create_stem(64, np.array([0, 0, 0]))
    assert node.type == NotionType.STEM
    assert node.energy > 0
    node.receive_signal(1.0)
    fired = node.fire(1.0)
    assert fired is True
    node.reset_potential()
    assert node.potential == 0.0
    print("[PASS] Notion cell")


def test_network_growth():
    """Test: Network grows from 10 stem cells in 0.5 sim hour."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()
    assert len(net.nodes) == 10

    ticks = 500  # 0.5 sim hour
    for cycle in range(1, ticks + 1):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
        net.step(cycle, [], stage)
        # Safety cap
        if len(net.nodes) > 200:
            sorted_nodes = sorted(net.nodes.values(), key=lambda n: n.energy)
            for node in sorted_nodes[:len(sorted_nodes) - 150]:
                net.remove_node(node.id)

    # Verify growth
    assert len(net.nodes) >= 15, f"Network didn't grow: {len(net.nodes)} nodes"
    
    # Verify type diversity
    types = set(n.type for n in net.nodes.values())
    assert len(types) >= 2, f"Only {len(types)} types: {types}"
    print(f"[PASS] Network growth: {len(net.nodes)} nodes, {len(types)} types: {net.global_stats.type_counts}")


def test_stage_transitions():
    """Test: Stage transitions occur correctly (simplified, 4 sim hours)."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()

    stages_seen = [tracker.get_stage_name()]
    for cycle in range(1, 2001):  # 2 sim hours
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        if stage is None:
            break
        if tracker.check_completion(net, cycle, sim_hours):
            old = tracker.get_stage_name()
            if tracker.advance_stage():
                new = tracker.get_stage_name()
                stages_seen.append(new)
        net.step(cycle, [], stage)
        if len(net.nodes) > 200:
            sorted_nodes = sorted(net.nodes.values(), key=lambda n: n.energy)
            for node in sorted_nodes[:len(sorted_nodes) - 150]:
                net.remove_node(node.id)

    assert len(stages_seen) >= 2, f"Only {len(stages_seen)} stages seen: {stages_seen}"
    print(f"[PASS] Stage transitions: {len(stages_seen)} stages: {stages_seen}")


def test_metrics_computation():
    """Test: All 7 metrics compute without error."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()

    # Run 2 sim hours
    for cycle in range(1, 2001):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
        net.step(cycle, [], stage)
        if len(net.nodes) > 200:
            sorted_nodes = sorted(net.nodes.values(), key=lambda n: n.energy)
            for node in sorted_nodes[:len(sorted_nodes) - 150]:
                net.remove_node(node.id)

    metrics = ConsciousnessMetrics().measure_all(net)
    assert isinstance(metrics, MetricsResult)
    assert 0 <= metrics.weighted_score() <= 1
    
    # All metric values should be finite
    for name in ['self_sustain', 'learning', 'discrimination',
                 'generalization', 'persistence', 'self_awareness', 'metaplasticity']:
        val = getattr(metrics, name)
        assert val == val, f"{name} is NaN"  # NaN check
    
    print(f"[PASS] Metrics: score={metrics.weighted_score():.4f}")


def test_teii():
    """Test: TEII computation completes without error."""
    config = load_dna("dna/seeds/baseline_v0.2.yaml")
    tracker = StageTracker(config.stages)
    net = NotionNetwork(config, stage_tracker=tracker)
    net.init_stem_cells()

    # Run 2 sim hours
    for cycle in range(1, 2001):
        sim_hours = cycle / 1000.0
        tracker.set_cycle_info(cycle, sim_hours)
        stage = tracker.get_current_stage()
        if tracker.check_completion(net, cycle, sim_hours):
            tracker.advance_stage()
        net.step(cycle, [], stage)

    teii = TransferEntropyCalculator(window=min(100, len(net.nodes))).calculate(net)
    assert 0 <= teii <= 1, f"TEII out of range: {teii}"
    print(f"[PASS] TEII: {teii:.4f}")


def test_param_space():
    """Test: Parameter space sampling."""
    ps = ParamSpace()
    samples = ps.sample(10)
    assert len(samples) == 10
    assert "connection_radius" in samples[0]
    assert "hebb_increment" in samples[0]
    print("[PASS] Parameter space")


def test_scorer():
    """Test: Scoring and ranking."""
    scorer = Scorer()
    results = [
        RunResult(seed_id="a", metrics=MetricsResult(self_sustain=50, learning=0.2)),
        RunResult(seed_id="b", metrics=MetricsResult(self_sustain=80, learning=0.3)),
        RunResult(seed_id="c", metrics=MetricsResult(self_sustain=20, learning=0.1)),
    ]
    for r in results:
        r.score = scorer.score(r)
    ranked = scorer.rank(results)
    assert ranked[0].seed_id == "b"  # Highest score first (normalized score > a)
    top = scorer.select_top(results, n=2)
    assert len(top) == 2
    print("[PASS] Scorer")


def run_all():
    """Run all tests."""
    tests = [
        test_dna_loading,
        test_space,
        test_time,
        test_event_bus,
        test_resources,
        test_collision,
        test_notion_cell,
        test_network_growth,
        test_stage_transitions,
        test_metrics_computation,
        test_teii,
        test_param_space,
        test_scorer,
    ]

    print("=" * 60)
    print("Nomad Genesis — Test Suite")
    print("=" * 60)

    start = time.time()
    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_fn.__name__}: {e}")
            failed += 1

    elapsed = time.time() - start
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {elapsed:.1f}s")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
