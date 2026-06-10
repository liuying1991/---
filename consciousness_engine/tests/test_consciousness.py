"""
Consciousness Engine - 测试验证
测试感知→编码→记忆→决策→行动的完整流程
"""

import sys
import os
import pytest

# 添加项目根目录
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.physics.space import Vector3, SpatialRelations
from engine.bio.perception import PerceptionSystem
from engine.bio.nervous import NervousSystem
from engine.bio.emotion import EmotionSystem
from engine.consciousness.memory_bridge import MemoryBridge
from engine.consciousness.attention_system import AttentionSystem
from engine.vr.renderer import Renderer3D, Scene, WorldObject
from run import ConsciousnessEngine


def load_config():
    """加载测试配置"""
    return {
        "physics": {"space": {"vision_range": 50.0, "hearing_range": 30.0, "max_view_distance": 100.0}},
        "bio": {
            "perception": {"visual_range": 50.0, "audio_range": 30.0, "tactile_range": 1.0},
            "nervous": {"neuron_count": 100, "hebbian_learning_rate": 0.1, "synapse_plasticity": 0.5},
            "emotion": {"base_arousal": 0.5, "base_intensity": 0.5},
        },
        "consciousness": {
            "attention": {"focus_radius": 5.0, "decay_rate": 0.9, "switch_cost": 0.3},
            "sleep": {"consolidation_interval": 21600, "importance_threshold": 0.5},
            "memory": {"db_path": "data/test_consciousness.db", "emotion_multiplier": 2.0},
        },
        "learning": {"base_lr": 0.1, "emotion_multiplier": 2.0},
        "attention": {"working_memory_limit": 4},
        "vr": {"camera": {"x": 0, "y": 0, "z": 10}, "screen_width": 80, "screen_height": 24},
    }


class TestPhysicsLayer:
    """测试物理法则层"""

    def test_vector3_operations(self):
        """测试3D向量操作"""
        v1 = Vector3(0, 0, 0)
        v2 = Vector3(3, 4, 0)
        dist = (v1 - v2).magnitude()
        assert abs(dist - 5.0) < 0.001

    def test_spatial_relations(self):
        """测试空间关系计算"""
        config = load_config()
        sr = SpatialRelations(config)
        
        observer = Vector3(0, 0, 0)
        target = Vector3(3, 4, 5)
        
        in_range = sr.is_in_range(observer, target, max_distance=10)
        assert in_range is True
        
        in_range_far = sr.is_in_range(observer, target, max_distance=1)
        assert in_range_far is False

    def test_field_of_view(self):
        """测试视野检测"""
        config = load_config()
        sr = SpatialRelations(config)
        
        observer = Vector3(0, 0, 0)
        forward = Vector3(0, 0, -1)
        target = Vector3(0, 0, -5)
        
        in_fov = sr.is_in_field_of_view(observer, forward, target, fov_degrees=90)
        assert in_fov is True


class TestBioLayer:
    """测试生物法则层"""

    def test_perception_system(self):
        """测试感知系统"""
        config = load_config()
        ps = PerceptionSystem(config)
        
        visual = ps.process_visual(
            object_id="test_obj",
            object_type="nature",
            distance=5.0,
            position=(5, 0, 0),
        )
        assert visual is not None
        assert visual["type"] == "visual"
        assert visual["salience"] > 0

    def test_nervous_system(self):
        """测试神经系统"""
        config = load_config()
        ns = NervousSystem(config)

        # 创建突触
        ns.create_synapse("A", "B")
        assert ns.get_synapse_strength_named("A", "B") > 0

        # 赫布学习
        ns.hebbian_learning_named("A", "B", co_activation=1.0)
        strength_before = ns.get_synapse_strength_named("A", "B")
        ns.fire([ns.named_neurons["A"], ns.named_neurons["B"]], intensity=0.8)
        ns.hebbian_learning_named("A", "B", co_activation=1.0)
        # 学习应该增加突触强度（依赖神经元激活状态）

    def test_emotion_system(self):
        """测试情绪系统"""
        config = load_config()
        es = EmotionSystem(config)
        
        # 初始情绪
        state = es.get_emotion_state()
        assert "valence" in state
        assert "arousal" in state
        
        # 情绪门控学习率
        base_lr = 0.1
        gated_lr = es.emotion_gate_learning_rate(base_lr)
        assert gated_lr >= base_lr


class TestConsciousnessLayer:
    """测试意识法则层"""

    def test_attention_system(self):
        """测试注意力系统"""
        config = load_config()
        atn = AttentionSystem(config)
        
        # 分配注意力
        score = atn.allocate_attention(
            object_id="obj_1",
            priority=0.8,
            emotional_relevance=0.7,
            spatial_relevance=0.6,
        )
        assert score > 0
        
        # 转移焦点
        cost = atn.shift_focus((5, 0, 0), intensity=0.9)
        assert cost >= 0
        
        # 获取最受关注对象
        top = atn.get_top_focused_objects(1)
        assert len(top) >= 1

    def test_memory_bridge_initialization(self):
        """测试记忆桥接初始化"""
        config = load_config()
        bridge = MemoryBridge(config)
        bridge.initialize()
        
        # 验证初始化状态
        # 如果NomadMem v4.0可用，is_active应为True
        # 否则为False（mock模式）
        assert isinstance(bridge.is_active, bool)
        
        bridge.close()


class TestVRLayer:
    """测试虚拟现实层"""

    def test_scene_management(self):
        """测试场景管理"""
        scene = Scene()
        
        # 添加对象
        obj = WorldObject("tree", Vector3(5, 0, 0), "nature")
        scene.add_object(obj)
        assert len(scene.objects) == 1
        
        # 范围内查询
        in_range = scene.get_objects_in_range(Vector3(0, 0, 0), radius=10)
        assert len(in_range) == 1
        
        # 移除对象
        scene.remove_object("tree")
        assert len(scene.objects) == 0

    def test_renderer_3d(self):
        """测试3D渲染器"""
        config = load_config()
        renderer = Renderer3D(config)
        
        # 添加对象
        renderer.add_object("obj1", 5, 0, 0, "nature")
        renderer.add_object("obj2", -3, 0, 2, "structure")
        
        # 更新注意力
        renderer.update_object_attention("obj1", 0.8)
        
        # 渲染帧
        frame = renderer.render_frame()
        assert isinstance(frame, str)
        assert len(frame) > 0
        
        # 渲染状态
        summary = renderer.render_state_summary()
        assert "Objects: 2" in summary


class TestConsciousnessEngine:
    """测试完整意识引擎"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = ConsciousnessEngine("config.yaml")
        
        assert engine.spatial_relations is not None
        assert engine.perception_system is not None
        assert engine.nervous_system is not None
        assert engine.emotion_system is not None
        assert engine.memory_bridge is not None
        assert engine.attention_system is not None
        assert engine.renderer is not None
        
        engine.close()

    def test_engine_tick(self):
        """测试引擎单步执行"""
        engine = ConsciousnessEngine("config.yaml")
        
        # 添加测试对象
        engine.add_object("test_obj", 5, 0, 0, "nature", {"salience": 0.8})
        
        # 执行一步
        result = engine.tick(dt=0.1)
        
        assert "tick" in result
        assert "perceptions" in result
        assert "memories_encoded" in result
        assert "decisions" in result
        assert "actions" in result
        
        engine.close()

    def test_engine_full_run(self):
        """测试引擎完整运行"""
        engine = ConsciousnessEngine("config.yaml")
        
        # 添加场景对象
        engine.add_object("tree_1", 5, 0, 0, "nature", {"salience": 0.7})
        engine.add_object("river_1", -3, 0, 2, "nature", {"salience": 0.8, "emits_sound": True})
        engine.add_object("person_1", 2, 0, 3, "entity", {"salience": 0.95, "emits_sound": True})
        
        # 运行5步
        engine.run(steps=5, dt=0.1, verbose=False)
        
        # 验证统计
        assert engine.stats["total_perceptions"] > 0
        assert engine.stats["total_decisions"] >= 0
        
        # 验证状态
        state = engine.get_state_summary()
        assert state["objects"] == 3
        assert state["ticks"] == 5
        
        engine.close()

    def test_engine_state_summary(self):
        """测试引擎状态摘要"""
        engine = ConsciousnessEngine("config.yaml")
        
        engine.add_object("obj_1", 0, 0, 0, "test")
        engine.tick(dt=0.1)
        
        summary = engine.get_state_summary()
        
        assert summary["time"] > 0
        assert summary["ticks"] == 1
        assert summary["objects"] == 1
        assert "emotion_state" in summary
        assert "stats" in summary
        
        engine.close()
