"""
NervousSystem - 神经系统
神经元发放、突触可塑性、赫布学习
"""
import numpy as np
from typing import Dict, Any, List


class NervousSystem:
    """神经系统"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bio_config = config.get("bio", {})
        self.nervous_config = self.bio_config.get("nervous", {})
        self.neuron_count = self.nervous_config.get("neuron_count", 1000)
        self.synapse_plasticity = self.nervous_config.get("synapse_plasticity", 0.1)

        # 神经元状态 [0, 1] 激活程度
        self.neurons = np.zeros(self.neuron_count, dtype=np.float32)

        # 突触连接权重矩阵
        self.synapses = np.zeros((self.neuron_count, self.neuron_count), dtype=np.float32)

        # 命名神经元映射 (name -> index)
        self.named_neurons: Dict[str, int] = {}
        self._next_neuron_id = 0

    def _get_neuron_index(self, name: str) -> int:
        """获取或创建命名神经元的索引"""
        if name not in self.named_neurons:
            self.named_neurons[name] = self._next_neuron_id
            self._next_neuron_id += 1
        return self.named_neurons[name]

    def create_synapse(self, pre_name: str, post_name: str, initial_strength: float = 0.1):
        """创建命名突触"""
        pre_idx = self._get_neuron_index(pre_name)
        post_idx = self._get_neuron_index(post_name)
        self.synapses[pre_idx][post_idx] = initial_strength

    def get_synapse_strength_named(self, pre_name: str, post_name: str) -> float:
        """获取命名突触强度"""
        if pre_name in self.named_neurons and post_name in self.named_neurons:
            return self.get_synapse_strength(
                self.named_neurons[pre_name],
                self.named_neurons[post_name],
            )
        return 0.0

    def hebbian_learning_named(self, pre_name: str, post_name: str, co_activation: float = 1.0):
        """命名赫布学习"""
        if pre_name in self.named_neurons and post_name in self.named_neurons:
            self.hebbian_learning(
                self.named_neurons[pre_name],
                self.named_neurons[post_name],
                intensity=self.synapse_plasticity * co_activation,
            )

    def update(self, dt: float = 0.1):
        """更新神经系统状态"""
        self.propagate(decay=0.95)

    def fire(self, neuron_indices: List[int], intensity: float = 1.0):
        """神经元发放"""
        for idx in neuron_indices:
            if 0 <= idx < self.neuron_count:
                self.neurons[idx] = min(1.0, self.neurons[idx] + intensity)

    def hebbian_learning(self, pre_idx: int, post_idx: int, intensity: float = None):
        """
        赫布学习：一起发放→连接更强
        Δw = η * pre * post
        """
        if intensity is None:
            intensity = self.synapse_plasticity

        if 0 <= pre_idx < self.neuron_count and 0 <= post_idx < self.neuron_count:
            # 突触强化
            self.synapses[pre_idx][post_idx] += intensity * self.neurons[pre_idx] * self.neurons[post_idx]
            self.synapses[pre_idx][post_idx] = min(1.0, self.synapses[pre_idx][post_idx])

    def propagate(self, decay: float = 0.9):
        """神经信号传播"""
        new_activation = np.zeros_like(self.neurons)

        for i in range(self.neuron_count):
            if self.neurons[i] > 0.1:  # 阈值
                for j in range(self.neuron_count):
                    if self.synapses[i][j] > 0.01:
                        new_activation[j] += self.neurons[i] * self.synapses[i][j]

        # 更新神经元状态（衰减+传播）
        self.neurons = self.neurons * decay + new_activation
        self.neurons = np.clip(self.neurons, 0, 1)

    def reset(self):
        """重置神经状态"""
        self.neurons = np.zeros(self.neuron_count, dtype=np.float32)

    def get_active_neurons(self, threshold: float = 0.1) -> List[int]:
        """获取活跃神经元"""
        return [i for i in range(self.neuron_count) if self.neurons[i] > threshold]

    def get_synapse_strength(self, pre_idx: int, post_idx: int) -> float:
        """获取突触强度"""
        if 0 <= pre_idx < self.neuron_count and 0 <= post_idx < self.neuron_count:
            return float(self.synapses[pre_idx][post_idx])
        return 0.0
