"""
DNA种子 - 虚拟世界原生意识体的初始条件
结构定义 + 调控规则 + 发育程序 + 环境接口
总计约50KB
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from engine.dna.notion import Notion, NotionType


class DNASeed:
    """
    数字DNA = 结构定义 + 调控规则 + 发育程序 + 环境接口
    
    DNA 不是意识体的设计图，而是生长规则集。
    意识不是写出来的，是在环境约束下长出来的。
    """

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or self._default_params()
        self._build()

    def _default_params(self) -> Dict[str, Any]:
        """默认DNA参数（~50KB参数空间）"""
        return {
            # === 1. 初始配置（~1KB）===
            "initial_stem_cells": 10,
            "max_total_nodes": 300,  # v0.2: 限制总节点数防止指数爆炸
            "initial_vector_dim": 64,
            "max_vector_dim": 256,
            "initial_connection_radius": 10.0,
            "base_metabolic_rate": 1.0,

            # === 2. 分裂规则（~2KB）===
            "split_energy_threshold": 60.0,
            "split_local_density_limit": 0.8,  # 局部连接密度上限
            "split_mutation_sigma": 0.05,
            "max_splits_per_lineage": 7,
            "apoptosis_energy_threshold": 5.0,
            "apoptosis_isolation_threshold": 0,  # 无连接时凋亡

            # === 3. 分化规则（~6KB）===
            "differentiation": {
                # stem → sensor: 外部输入信号密度 > 阈值
                "sensor_signal_density_threshold": 0.3,
                # stem → interneuron: 连接数 > 3 且激活频率 > 全局均值
                "interneuron_min_connections": 3,
                "interneuron_activation_ratio": 1.0,  # > 全局均值
                # stem → inhibitor: interneuron中随机20%转化
                "inhibitor_conversion_prob": 0.2,
                "inhibitor_conversion_search_range": (0.1, 0.3),
                # stem → oscillator: 连续200周期未接收外部信号 且 energy > 生存阈值 × 3
                "oscillator_no_signal_cycles": 200,
                "oscillator_energy_min_multiplier": 3.0,
                "oscillator_period_range": (10, 200),
                # stem → memory: 单次激活强度 > 全局均值 × 3
                "memory_activation_multiplier": 3.0,
                # stem → gate: 连续100周期接收抑制性信号
                "gate_inhibitory_cycles": 100,
                # stem → hub: 入度+出度 > 周围节点均值 × 2
                "hub_degree_multiplier": 2.0,
                # stem → projector: 向量与另一区域节点余弦相似度 > 0.8
                "projector_similarity_threshold": 0.8,
            },

            # === 4. 连接规则（~6KB）===
            "connection": {
                "base_connection_prob": 0.05,
                "min_connection_prob": 0.01,  # 相似度<0时的最小概率
                "hebbian_activation_interval": 10,  # 共同激活次数每增加10
                "hebbian_strength_increase": 0.1,
                "steady_decay_cycles": 100,  # 连续未共同激活周期数
                "steady_decay_rate": 0.05,
                "pruning_strength_threshold": 0.01,
                "pruning_inactive_cycles": 500,
                # Hub垄断防护
                "hub_max_global_connection_ratio": 0.05,  # 5%硬上限
                "hub_locked_plasticity": 0.01,
            },

            # === 5. 发育程序（~4KB）===
            "development": {
                # 7阶段，完成度触发
                "embryo_target_nodes": 200,  # v0.2: 800降到200（最小证明量级）
                "embryo_split_rate_decay_threshold": 0.1,
                "migration_target_ratio": 0.9,  # 90%节点到达目标区域
                "synapse_burst_density": 0.15,  # 突触爆发期连接密度（降低）
                "synapse_burst_radius_ratio": 0.5,  # 连接半径缩小50%
                "pruning_target_density": 0.05,  # 修剪后连接密度~5%
                "steady_global_plasticity": 0.1,
                "memory_plasticity": 0.05,
            },

            # === 6. 环境接口（~4KB）===
            "environment": {
                "sensor_types": ["collision", "light", "resource", "social"],
                "action_primitives": 12,
                "decode_matrix_seed": 42,  # 解码矩阵种子（DNA的一部分）
            },

            # === 7. 自指涉配置（~2KB）===
            "self_reference": {
                "self_sensor_sample_rate": 10,  # 每10周期采样
                "gate_self_regulation_rate": 0.01,
                "teii_window_size": 500,  # 传递熵采样窗口T
                "teii_significance_threshold": 0.05,
            },

            # === 8. 代际传递协议（~3KB，v0.2新增）===
            "generational": {
                "experience_items": ["hub_distribution", "critical_period",
                                     "connection_density", "inhibitor_ratio",
                                     "oscillator_sync"],
                "genetic_weight": 0.7,  # 70%遗传
                "epigenetic_weight": 0.3,  # 30%经验
            },

            # === 暴力搜索范围 ===
            "search_space": {
                "inhibitor_conversion_prob": (0.1, 0.3),
                "connection_base_prob": (0.02, 0.1),
                "hebbian_strength_increase": (0.05, 0.2),
                "embryo_split_rate": (0.5, 2.0),
                "pruning_aggressiveness": (0.5, 2.0),
                "oscillator_period_min": (5, 20),
                "oscillator_period_max": (100, 300),
            },
        }

    def _build(self):
        """根据参数构建DNA种子"""
        # 预生成动作解码矩阵（N×12，N=max_vector_dim）
        np.random.seed(self.params["environment"]["decode_matrix_seed"])
        max_dim = self.params["max_vector_dim"]
        self.action_decode_matrix = np.random.randn(max_dim, 12).astype(np.float32) * 0.1

    def create_initial_stem_cells(self) -> List[Notion]:
        """创建初始10个干细胞"""
        stem_cells = []
        for i in range(self.params["initial_stem_cells"]):
            notion = Notion(
                notion_type=NotionType.STEM,
                vector_dim=self.params["initial_vector_dim"],
            )
            notion.base_metabolic_rate = self.params["base_metabolic_rate"]
            stem_cells.append(notion)
        return stem_cells

    def get_differentiation_params(self) -> Dict:
        """获取分化规则参数"""
        return self.params["differentiation"]

    def get_connection_params(self) -> Dict:
        """获取连接规则参数"""
        return self.params["connection"]

    def get_development_params(self) -> Dict:
        """获取发育程序参数"""
        return self.params["development"]

    def get_action_decode_matrix(self, vector_dim: int) -> np.ndarray:
        """获取动作解码矩阵（N×12）"""
        return self.action_decode_matrix[:vector_dim, :]

    def to_dict(self) -> Dict:
        """序列化DNA种子"""
        return {
            "params": self.params,
            "action_decode_matrix_shape": self.action_decode_matrix.shape,
        }

    def clone_with_params(self, new_params: Dict) -> 'DNASeed':
        """用新参数克隆DNA种子（用于代际传递）"""
        return DNASeed(params=new_params)

    @staticmethod
    def merge_with_experience(parent_seed: 'DNASeed', experience: Dict) -> 'DNASeed':
        """
        拉马克主义代际传递：经验编码 + 种子修改 + 重新发育
        
        经验项：
        1. 最终枢纽分布
        2. 临界期时长
        3. 连接密度终值
        4. inhibitor有效比例
        5. oscillator同步度
        """
        genetic = parent_seed.params.copy()
        epigenetic_weight = genetic["generational"]["epigenetic_weight"]

        # 修改分化参数
        if "inhibitor_ratio" in experience:
            current = genetic["differentiation"]["inhibitor_conversion_prob"]
            genetic["differentiation"]["inhibitor_conversion_prob"] = (
                current * (1 - epigenetic_weight) +
                experience["inhibitor_ratio"] * epigenetic_weight
            )

        # 修改连接参数
        if "connection_density" in experience:
            current = genetic["connection"]["base_connection_prob"]
            target = max(0.01, min(0.15, experience["connection_density"] * 0.1))
            genetic["connection"]["base_connection_prob"] = (
                current * (1 - epigenetic_weight) + target * epigenetic_weight
            )

        # 修改振荡器参数
        if "oscillator_sync" in experience:
            # 同步度低时扩大周期范围
            sync = experience["oscillator_sync"]
            if sync < 0.3:
                genetic["differentiation"]["oscillator_period_range"] = (
                    genetic["differentiation"]["oscillator_period_range"][0],
                    int(genetic["differentiation"]["oscillator_period_range"][1] * 1.5),
                )

        return DNASeed(params=genetic)
