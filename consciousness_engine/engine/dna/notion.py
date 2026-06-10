"""
Notion - 意识体信息处理最小原子
9种类型：stem/sensor/interneuron/inhibitor/oscillator/projector/hub/memory/gate
"""

import uuid
import math
import numpy as np
from enum import Enum
from typing import Dict, List, Optional, Tuple


class NotionType(Enum):
    """Notion的9种可分化类型"""
    STEM = "stem"                    # 未分化，干细胞态
    SENSOR = "sensor"                # 接收外部输入
    INTERNEURON = "interneuron"      # 转发和处理信息
    INHIBITOR = "inhibitor"          # 抑制性节点（v0.2新增）
    OSCILLATOR = "oscillator"        # 内源性节律节点（v0.2新增）
    PROJECTOR = "projector"          # 跨区域投射，解码为行为指令
    HUB = "hub"                      # 高连接度中心节点
    MEMORY = "memory"                # 稳定存储，低可塑性
    GATE = "gate"                    # 调制其他节点的激活阈值


class Notion:
    """
    Notion = 信息处理的最小原子

    Notion = {
        id:         全局唯一标识
        type:       当前类型（初始为"stem"干细胞态）
        vector:     N维信息向量（初始64维，可生长至256维）
        threshold:  激活阈值
        plasticity: 可塑性系数（0-1）
        energy:     能量值（代谢约束，耗尽则凋亡）
        position:   虚拟空间位置（影响连接半径）
    }
    """

    def __init__(
        self,
        notion_type: NotionType = NotionType.STEM,
        vector_dim: int = 64,
        position: Optional[Tuple[float, float, float]] = None,
        seed_id: Optional[str] = None,
    ):
        self.id = seed_id or str(uuid.uuid4())[:8]
        self.type = notion_type
        self.vector = np.random.randn(vector_dim).astype(np.float32) * 0.1
        self.threshold = 0.5  # 激活阈值
        self.plasticity = 1.0  # 可塑性系数（干细胞态最高）
        self.energy = 100.0  # 能量值（满能量）
        self.position = position or (
            np.random.uniform(-5, 5),
            np.random.uniform(-5, 5),
            np.random.uniform(-5, 5),
        )

        # 激活状态
        self.activation = 0.0  # 当前激活程度 (0-1)
        self.activation_history: List[float] = []  # 激活历史（用于传递熵计算）

        # 连接信息
        self.in_degree = 0  # 入度
        self.out_degree = 0  # 出度
        self.connections: Dict[str, float] = {}  # {target_id: connection_strength}

        # 代谢
        self.base_metabolic_rate = 1.0  # 基础代谢率（能量/周期）
        self.activation_cost = 2.0  # 激活额外消耗
        self.split_cost = 10.0  # 分裂消耗

        # 分化历史
        self.max_splits = 7  # 最大分裂次数（单谱系最多128个后代）
        self.split_count = 0
        self.generation = 0  # 代际

        # 振荡器特有（v0.2新增）
        self.oscillator_period = 0  # 内生周期（模拟周期）
        self.oscillator_phase = 0.0  # 当前相位

        # 门控特有
        self.threshold_modulation = 0.0  # 阈值调制量

        # 抑制性信号接收计数（用于gate分化）
        self.inhibitory_signal_count = 0

        # 外部信号未激活计数（用于oscillator分化）
        self.no_external_signal_cycles = 0

    @property
    def is_alive(self) -> bool:
        """是否存活（能量>0）"""
        return self.energy > 0

    @property
    def is_active(self) -> bool:
        """是否被激活"""
        return self.activation > self.threshold

    def activate(self, input_strength: float, from_inhibitor: bool = False):
        """
        激活节点

        Args:
            input_strength: 输入信号强度
            from_inhibitor: 是否来自抑制性节点
        """
        if not self.is_alive:
            return

        if from_inhibitor:
            # 抑制性信号降低激活概率
            self.activation = max(0, self.activation - input_strength * 0.5)
            self.inhibitory_signal_count += 1
        else:
            self.activation = min(1.0, self.activation + input_strength)

        # 记录历史
        self.activation_history.append(self.activation)
        # 保持历史记录大小（传递熵需要）
        if len(self.activation_history) > 1000:
            self.activation_history = self.activation_history[-500:]

    def consume_energy(self):
        """消耗能量（每周期）"""
        if not self.is_alive:
            return

        # 基础代谢
        cost = self.base_metabolic_rate

        # 激活额外消耗
        if self.is_active:
            cost *= self.activation_cost

        # 能量低于50%，可塑性降低
        if self.energy < 50:
            self.plasticity *= 0.5

        # 能量低于10%，仅维持生存
        if self.energy < 10:
            self.activation = 0
            cost = self.base_metabolic_rate * 0.5

        self.energy = max(0, self.energy - cost)

    def gain_energy(self, amount: float):
        """获得能量（通过CONSUME动作）"""
        self.energy = min(100.0, self.energy + amount)

    def update_oscillator(self, cycle: int):
        """更新振荡器相位（v0.2新增）"""
        if self.type != NotionType.OSCILLATOR or self.oscillator_period <= 0:
            return

        self.oscillator_phase += (2 * math.pi) / self.oscillator_period
        if self.oscillator_phase > 2 * math.pi:
            self.oscillator_phase -= 2 * math.pi

        # 在相位峰值时自主激活
        if abs(self.oscillator_phase) < 0.3:
            self.activate(0.3)

    def decay_activation(self, decay_rate: float = 0.1):
        """激活衰减"""
        self.activation *= (1.0 - decay_rate)
        if self.activation < 0.001:
            self.activation = 0.0

    def clone(self) -> 'Notion':
        """分裂产生子节点（继承+微小变异）"""
        child = Notion(
            notion_type=NotionType.STEM,  # 子节点初始为干细胞
            vector_dim=len(self.vector),
            position=self.position,
        )

        # 继承父节点向量（加微小高斯变异 σ=0.05）
        child.vector = self.vector.copy() + np.random.randn(len(self.vector)) * 0.05
        child.vector = child.vector.astype(np.float32)

        child.generation = self.generation + 1
        child.energy = self.energy * 0.3  # 子节点从父节点分走30%能量

        return child

    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "vector_dim": len(self.vector),
            "threshold": self.threshold,
            "plasticity": self.plasticity,
            "energy": self.energy,
            "position": self.position,
            "activation": self.activation,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "connection_count": len(self.connections),
            "generation": self.generation,
        }

    def __repr__(self):
        return (f"Notion({self.id[:4]}, type={self.type.value}, "
                f"activation={self.activation:.3f}, energy={self.energy:.1f})")
