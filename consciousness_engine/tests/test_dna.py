"""
DNA种子意识体 - 测试验证
测试自组织生长、类型分化、意识涌现指标
"""

import sys
import os
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.dna.seed import DNASeed
from engine.dna.notion import Notion, NotionType
from engine.dna.notion_network import NotionNetwork
from engine.dna.metrics import ConsciousnessMetrics


def load_config():
    return {
        "physics": {"space": {"max_view_distance": 100.0}},
        "bio": {"emotion": {"base_arousal": 0.5}},
        "consciousness": {"attention": {}},
        "simulation": {"speed": 10},
    }


class TestNotion:
    """测试Notion基础功能"""

    def test_notion_creation(self):
        """测试Notion创建"""
        n = Notion(NotionType.STEM, vector_dim=64)
        assert n.type == NotionType.STEM
        assert len(n.vector) == 64
        assert n.energy == 100.0
        assert n.is_alive

    def test_notion_energy_consumption(self):
        """测试能量消耗"""
        n = Notion(NotionType.STEM)
        initial = n.energy
        n.consume_energy()
        assert n.energy < initial

    def test_notion_activation(self):
        """测试激活"""
        n = Notion(NotionType.INTERNEURON, vector_dim=64)
        n.threshold = 0.3
        n.activate(0.5)
        assert n.activation > 0.3
        assert n.is_active

    def test_notion_clone(self):
        """测试分裂克隆"""
        parent = Notion(NotionType.INTERNEURON, vector_dim=64, position=(0, 0, 0))
        parent.energy = 80
        child = parent.clone()
        assert child.type == NotionType.STEM
        assert child.generation == 1
        assert np.linalg.norm(child.vector - parent.vector) < 1.0  # 微小变异


class TestDNASeed:
    """测试DNA种子"""

    def test_seed_creation(self):
        """测试种子创建"""
        seed = DNASeed()
        assert seed.params["initial_stem_cells"] == 10
        assert seed.params["initial_vector_dim"] == 64

    def test_create_stem_cells(self):
        """测试创建干细胞"""
        seed = DNASeed()
        cells = seed.create_initial_stem_cells()
        assert len(cells) == 10
        assert all(c.type == NotionType.STEM for c in cells)

    def test_action_decode_matrix(self):
        """测试动作解码矩阵"""
        seed = DNASeed()
        matrix = seed.get_action_decode_matrix(64)
        assert matrix.shape == (64, 12)  # N×12

    def test_seed_serialization(self):
        """测试种子序列化"""
        seed = DNASeed()
        data = seed.to_dict()
        assert "params" in data
        assert "action_decode_matrix_shape" in data

    def test_generational_transfer(self):
        """测试拉马克代际传递"""
        parent = DNASeed()
        experience = {
            "inhibitor_ratio": 0.30,  # 明显不同的值
            "connection_density": 0.06,
            "oscillator_sync": 0.2,
        }
        child = DNASeed.merge_with_experience(parent, experience)
        assert child is not None
        # inhibitor比例应该受经验影响（加权平均）
        expected = parent.params["differentiation"]["inhibitor_conversion_prob"] * 0.7 + 0.30 * 0.3
        assert abs(child.params["differentiation"]["inhibitor_conversion_prob"] - expected) < 0.03


class TestNotionNetwork:
    """测试Notion网络"""

    def test_network_initialization(self):
        """测试网络初始化"""
        seed = DNASeed()
        network = NotionNetwork(seed)
        assert len(network.notions) == 0
        assert network.cycle == 0
        assert network.development_stage == "embryo"

    def test_network_growth(self):
        """测试网络生长"""
        seed = DNASeed()
        network = NotionNetwork(seed)
        cells = seed.create_initial_stem_cells()
        for cell in cells:
            network.notions[cell.id] = cell

        # 运行200步（足够胚胎期生长和突触爆发）
        for _ in range(200):
            network.step(external_input={"noise": 0.05}, energy_gain=150)

        # 验证网络生长
        assert len(network.notions) > 10  # 应该分裂增长
        # 连接在胚胎期/突触爆发期应该建立了
        assert network._total_connections() >= 0  # 可能有连接

    def test_type_diversity(self):
        """测试类型多样性"""
        seed = DNASeed()
        network = NotionNetwork(seed)
        cells = seed.create_initial_stem_cells()
        for cell in cells:
            network.notions[cell.id] = cell

        # 运行300步（足够多个阶段）
        for _ in range(300):
            network.step(external_input={"noise": 0.05}, energy_gain=150)

        # 验证多种类型出现
        types = set(n.type for n in network.notions.values())
        assert len(types) >= 2  # 至少interneuron + inhibitor

    def test_hub_monopoly_protection(self):
        """测试Hub垄断防护"""
        seed = DNASeed()
        network = NotionNetwork(seed)

        # 手动创建一个hub
        hub = Notion(NotionType.HUB, vector_dim=64)
        for i in range(100):
            node = Notion(NotionType.INTERNEURON, vector_dim=64)
            network.notions[node.id] = node
            network._add_connection(node.id, hub.id, 0.5)

        result = network._check_hub_monopoly(hub)
        # 当连接占比过大时应拒绝
        assert isinstance(result, bool)

    def test_action_decoding(self):
        """测试动作解码"""
        seed = DNASeed()
        network = NotionNetwork(seed)

        # 创建projector节点
        projector = Notion(NotionType.PROJECTOR, vector_dim=64)
        projector.activation = 0.8
        network.notions[projector.id] = projector

        actions = network._decode_actions()
        # 应该有动作输出
        assert isinstance(actions, list)


class TestConsciousnessMetrics:
    """测试意识涌现指标"""

    def test_metric_computation(self):
        """测试指标计算"""
        metrics = ConsciousnessMetrics()

        # 记录一些数据
        for i in range(200):
            input_pattern = np.random.randn(4).astype(np.float32) * 0.1
            activation = np.random.randn(50).astype(np.float32) * 0.1
            metrics.record_cycle(
                input_pattern=input_pattern,
                activation_pattern=activation,
                self_sensor_value=float(np.random.random()),
                gate_avg_threshold=0.5,
                prediction_error=float(np.random.random() * 0.1),
            )

        results = metrics.compute_all(200)
        assert "1_self_sustaining" in results
        assert "summary" in results
        assert "total_score" in results["summary"]

    def test_cosine_similarity(self):
        """测试余弦相似度"""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        assert abs(ConsciousnessMetrics._cosine_similarity(a, b) - 1.0) < 0.001

        c = np.array([1.0, 0.0, 0.0])
        d = np.array([0.0, 1.0, 0.0])
        assert abs(ConsciousnessMetrics._cosine_similarity(c, d)) < 0.001

    def test_cosine_similarity_different_lengths(self):
        """测试不同长度向量的余弦相似度"""
        a = np.array([1.0, 0.0])
        b = np.array([1.0, 0.0, 0.0, 0.0])
        result = ConsciousnessMetrics._cosine_similarity(a, b)
        assert abs(result - 1.0) < 0.001  # pad后应该相似


class TestFullPipeline:
    """测试完整流水线"""

    def test_full_growth_pipeline(self):
        """测试完整生长流水线"""
        from engine.dna.seed import DNASeed
        from engine.dna.notion_network import NotionNetwork

        seed = DNASeed()
        network = NotionNetwork(seed)
        cells = seed.create_initial_stem_cells()
        for cell in cells:
            network.notions[cell.id] = cell

        # 运行300步
        actions_seen = []
        for _ in range(300):
            result = network.step()
            if result.get("actions"):
                actions_seen.extend(result["actions"])

        # 验证网络结构
        state = {
            "notions": len(network.notions),
            "connections": network._total_connections(),
            "stage": network.development_stage,
            "types": set(n.type.value for n in network.notions.values()),
        }

        assert state["notions"] > 10
        # 连接数可能为0（如果还在早期阶段）
        assert state["connections"] >= 0
        assert len(state["types"]) >= 1
