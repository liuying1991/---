"""
NotionNetwork - 意识体大脑（Notion网络）
实现：分裂/分化/连接/修剪/赫布学习/抑制/振荡/Hub垄断防护
"""

import math
import random
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

from engine.dna.notion import Notion, NotionType
from engine.dna.seed import DNASeed


class NotionNetwork:
    """
    意识体大脑 = Notion网络
    
    局部规则 → 全局结构涌现
    """

    def __init__(self, dna_seed: DNASeed):
        self.dna = dna_seed
        self.notions: Dict[str, Notion] = {}
        self.cycle = 0

        # 发育阶段
        self.development_stage = "embryo"  # embryo/migration/synapse_burst/pruning/differentiation/steady/lifelong

        # 发育统计
        self.stats = {
            "total_splits": 0,
            "total_apoptosis": 0,
            "total_differentiations": defaultdict(int),
            "total_connections_created": 0,
            "total_connections_pruned": 0,
            "stage_entered": {"embryo": 0},
        }

        # 全局活动记录（用于意识涌现指标）
        self.global_activation_history: List[float] = []
        self.input_patterns_history: List[np.ndarray] = []

        # 全局平均激活频率（用于分化阈值比较）
        self.global_mean_activation = 0.0

    # ==================== 核心循环 ====================

    def step(self, external_input: Optional[Dict[str, float]] = None,
             energy_gain: float = 0.0) -> Dict:
        """
        单步执行
        
        Args:
            external_input: 外部感知输入 {sensor_type: strength}
            energy_gain: 本周期获得的能量
        
        Returns:
            本步执行结果
        """
        self.cycle += 1

        result = {
            "cycle": self.cycle,
            "stage": self.development_stage,
            "notion_count": len(self.notions),
            "connection_count": self._total_connections(),
            "actions": [],
        }

        # 1. 更新发育阶段
        self._update_development_stage()

        # 2. 能量代谢
        self._metabolism()

        # 3. 接收外部输入（激活sensor）
        if external_input:
            self._process_external_input(external_input)

        # 4. 能量补充
        if energy_gain > 0:
            self._distribute_energy(energy_gain)

        # 5. 信号传播（网络内传递）
        self._propagate_signals()

        # 6. 振荡器更新（v0.2新增）
        self._update_oscillators()

        # 7. 赫布学习
        self._hebbian_learning()

        # 8. 连接衰减和修剪
        self._connection_decay_and_pruning()

        # 9. 分裂和分化
        if self.development_stage in ("embryo", "migration", "synapse_burst", "differentiation", "lifelong"):
            self._split_and_differentiate()

        # 10. 连接建立（非修剪期才允许新建连接）
        if self.development_stage in ("synapse_burst", "differentiation", "steady", "lifelong"):
            self._create_connections()

        # 11. 凋亡
        self._apoptosis()

        # 12. 更新全局统计
        self._update_global_stats()

        # 13. 动作解码（projector → 行为）
        result["actions"] = self._decode_actions()

        return result

    # ==================== 发育阶段 ====================

    def _update_development_stage(self):
        """完成度触发阶段切换（非硬性时间触发）"""
        dev = self.dna.get_development_params()
        node_count = len(self.notions)

        if self.development_stage == "embryo":
            # 胚胎期→迁移期：节点数达到500 或 分裂速率降至初始的10%以下
            if node_count >= dev["embryo_target_nodes"] or self._split_rate_low():
                self._transition_stage("migration")

        elif self.development_stage == "migration":
            # 迁移期→突触爆发期：90%节点到达梯度目标区域
            if self._migration_ratio_met(dev["migration_target_ratio"]):
                self._transition_stage("synapse_burst")

        elif self.development_stage == "synapse_burst":
            # 突触爆发期→修剪期：连接密度达到目标
            density = self._connection_density()
            if density >= dev["synapse_burst_density"] * 0.8:
                self._transition_stage("pruning")

        elif self.development_stage == "pruning":
            # 修剪期→功能分化期：连接密度降至目标
            density = self._connection_density()
            if density <= dev["pruning_target_density"] * 1.5:
                self._transition_stage("differentiation")

        elif self.development_stage == "differentiation":
            # 功能分化期→稳态期：类型分化基本完成
            if self._differentiation_stable():
                self._transition_stage("steady")

        elif self.development_stage == "steady":
            # 稳态期→终身可塑期（自动过渡，无需条件）
            if self.cycle > 5000:  # 足够长的稳态后
                self._transition_stage("lifelong")

    def _transition_stage(self, new_stage: str):
        """阶段切换"""
        if new_stage != self.development_stage:
            old = self.development_stage
            self.development_stage = new_stage
            self.stats["stage_entered"][new_stage] = self.cycle

            # 阶段特定初始化
            if new_stage == "synapse_burst":
                # 连接半径缩小50%
                pass
            elif new_stage == "steady":
                # 降低全局可塑性
                for notion in self.notions.values():
                    if notion.type == NotionType.MEMORY:
                        notion.plasticity = self.dna.get_development_params()["memory_plasticity"]
                    else:
                        notion.plasticity = self.dna.get_development_params()["steady_global_plasticity"]

    # ==================== 能量代谢 ====================

    def _metabolism(self):
        """所有节点消耗能量"""
        for notion in self.notions.values():
            notion.consume_energy()

    def _distribute_energy(self, total: float):
        """分配获得的能量（平均分配）"""
        if not self.notions:
            return
        per_node = total / len(self.notions)
        for notion in self.notions.values():
            notion.gain_energy(per_node)
            # 胚胎期给额外能量支持快速分裂
            if self.development_stage == "embryo":
                notion.gain_energy(per_node * 2)

    # ==================== 信号传播 ====================

    def _process_external_input(self, input_data: Dict[str, float]):
        """处理外部输入，激活sensor节点"""
        sensor_nodes = [n for n in self.notions.values()
                       if n.type == NotionType.SENSOR]

        if not sensor_nodes:
            # 如果没有sensor，随机选择一些stem或interneuron来接收
            candidates = [n for n in self.notions.values()
                        if n.type in (NotionType.STEM, NotionType.INTERNEURON)]
            if candidates:
                # 选择前30%的候选者
                count = max(1, len(candidates) // 3)
                selected = random.sample(candidates, min(count, len(candidates)))
                for notion in selected:
                    strength = sum(input_data.values()) / max(1, len(input_data))
                    notion.activate(strength)
                    notion.no_external_signal_cycles = 0
            return

        # 分配输入到sensor
        for key, strength in input_data.items():
            if sensor_nodes:
                # 轮询分配
                target = sensor_nodes[self.cycle % len(sensor_nodes)]
                target.activate(strength)
                target.no_external_signal_cycles = 0

    def _propagate_signals(self):
        """信号在网络中传播"""
        # 收集所有激活节点的输出
        activated = {nid: n.activation for nid, n in self.notions.items()
                    if n.is_active and n.is_alive}

        if not activated:
            return

        # 传播到连接目标
        new_activations = defaultdict(float)
        for source_id, activation in activated.items():
            source = self.notions[source_id]
            for target_id, strength in source.connections.items():
                if target_id in self.notions:
                    target = self.notions[target_id]
                    if target.is_alive:
                        from_inhibitor = source.type == NotionType.INHIBITOR
                        new_activations[target_id] += activation * abs(strength)
                        if from_inhibitor:
                            target.activate(activation * abs(strength), from_inhibitor=True)

        # 应用新激活
        for target_id, strength in new_activations.items():
            if target_id in activated:
                continue  # 跳过已经手动激活的节点
            target = self.notions[target_id]
            target.activate(strength)

    def _update_oscillators(self):
        """更新振荡器（v0.2新增）"""
        for notion in self.notions.values():
            notion.update_oscillator(self.cycle)
            # oscillator自主激活时传播信号到邻居
            if notion.type == NotionType.OSCILLATOR and notion.is_active and notion.connections:
                # 随机选择一个连接目标传播振荡信号
                for target_id, strength in list(notion.connections.items())[:3]:
                    if target_id in self.notions and self.notions[target_id].is_alive:
                        self.notions[target_id].activate(notion.activation * abs(strength) * 0.5)

    # ==================== 赫布学习 ====================

    def _hebbian_learning(self):
        """赫布学习：共同激活→连接增强"""
        # 找出共同激活的节点对
        active_ids = [nid for nid, n in self.notions.items()
                     if n.is_active and n.is_alive]

        if len(active_ids) < 2:
            return

        hebbian_interval = self.dna.params["connection"]["hebbian_activation_interval"]
        hebbian_increase = self.dna.params["connection"]["hebbian_strength_increase"]

        # 对每对活跃节点，增强连接
        for i in range(len(active_ids)):
            for j in range(i + 1, len(active_ids)):
                id_a, id_b = active_ids[i], active_ids[j]
                node_a = self.notions[id_a]
                node_b = self.notions[id_b]

                # 如果已有连接，增强
                if id_b in node_a.connections:
                    node_a.connections[id_b] = min(1.0,
                        node_a.connections[id_b] + hebbian_increase * node_a.plasticity)
                if id_a in node_b.connections:
                    node_b.connections[id_a] = min(1.0,
                        node_b.connections[id_a] + hebbian_increase * node_b.plasticity)

    # ==================== 连接衰减和修剪 ====================

    def _connection_decay_and_pruning(self):
        """连接衰减和修剪"""
        params = self.dna.params["connection"]
        to_prune = []

        # 胚胎期和突触爆发期不修剪
        if self.development_stage in ("embryo", "synapse_burst"):
            return

        # 终身可塑期大幅降低修剪（稳定网络结构）
        if self.development_stage == "lifelong":
            # 只修剪完全无活动的连接
            for notion in self.notions.values():
                if not notion.is_alive:
                    continue
                for target_id, strength in list(notion.connections.items()):
                    if notion.connections[target_id] < 0.001:
                        to_prune.append((notion.id, target_id))
            # 执行
            for source_id, target_id in to_prune:
                if source_id in self.notions and target_id in self.notions[source_id].connections:
                    del self.notions[source_id].connections[target_id]
                    self.notions[source_id].out_degree = max(0,
                        self.notions[source_id].out_degree - 1)
                    self.stats["total_connections_pruned"] += 1
            return

        # 修剪期和稳态期/分化期：积极衰减和修剪
        if self.development_stage in ("pruning", "differentiation"):
            decay_rate = params["steady_decay_rate"] * 3  # 3倍衰减速率
            prune_threshold = params["pruning_strength_threshold"]
        else:
            decay_rate = params["steady_decay_rate"]
            prune_threshold = params["pruning_strength_threshold"]

        for notion in self.notions.values():
            if not notion.is_alive:
                continue
            for target_id, strength in list(notion.connections.items()):
                target = self.notions.get(target_id)
                if target is None:
                    to_prune.append((notion.id, target_id))
                    continue

                # 衰减：只有非活跃连接才衰减
                if not notion.is_active or not target.is_active:
                    notion.connections[target_id] = max(0,
                        strength - decay_rate * notion.plasticity)

                # 修剪条件
                if notion.connections[target_id] < prune_threshold:
                    to_prune.append((notion.id, target_id))

        # 执行修剪
        for source_id, target_id in to_prune:
            if source_id in self.notions and target_id in self.notions[source_id].connections:
                del self.notions[source_id].connections[target_id]
                self.notions[source_id].out_degree = max(0,
                    self.notions[source_id].out_degree - 1)
                self.stats["total_connections_pruned"] += 1

    # ==================== 分裂和分化 ====================

    def _split_and_differentiate(self):
        """分裂和分化"""
        new_notions = []
        differentiations = []

        for notion in list(self.notions.values()):
            if not notion.is_alive:
                continue

            # 尝试分裂
            if self._should_split(notion):
                child = notion.clone()
                notion.split_count += 1
                notion.energy -= notion.split_cost * 5
                new_notions.append(child)
                self.stats["total_splits"] += 1

            # 尝试分化
            diff_result = self._try_differentiate(notion)
            if diff_result:
                differentiations.append(diff_result)

        # 添加新节点
        for new_notion in new_notions:
            self.notions[new_notion.id] = new_notion
            # 为子节点建立到父节点的连接
            parent_id = None
            for nid, n in self.notions.items():
                if nid != new_notion.id:
                    parent_id = nid
                    break
            if parent_id:
                self._add_connection(parent_id, new_notion.id, 0.5)

        # 记录分化
        for diff in differentiations:
            notion_id, old_type, new_type = diff
            self.stats["total_differentiations"][new_type] += 1

    def _should_split(self, notion: Notion) -> bool:
        """判断是否应该分裂"""
        split_config = self.dna.params
        if notion.energy < split_config["split_energy_threshold"]:
            return False
        if notion.split_count >= split_config["max_splits_per_lineage"]:
            return False
        if notion.type == NotionType.MEMORY:
            return False  # 记忆节点不分裂

        # 总节点数限制
        max_nodes = split_config.get("max_total_nodes", 300)
        if len(self.notions) >= max_nodes:
            return False

        # 胚胎期放宽分裂条件
        if self.development_stage == "embryo":
            # 只要能量超过阈值且未达分裂上限就分裂
            return True

        # 局部连接密度检查
        local_density = notion.out_degree / max(1, len(self.notions) * 0.1)
        if local_density > split_config["split_local_density_limit"]:
            return False

        return True

    def _try_differentiate(self, notion: Notion) -> Optional[Tuple[str, str, str]]:
        """尝试分化节点（包括干细胞和已分化节点的再分化）"""
        is_stem = notion.type == NotionType.STEM

        # 只有stem或interneuron可以进一步分化
        if not is_stem and notion.type not in (NotionType.INTERNEURON,):
            return None

        old_type = notion.type.value
        diff_params = self.dna.get_differentiation_params()
        new_type = None

        # 胚胎期：延迟分化，先让网络长到足够大
        if self.development_stage == "embryo":
            if len(self.notions) < 150:
                return None
            if not is_stem:
                return None  # 胚胎期只有stem分化
            # 网络足够大后，只分化一部分节点
            if random.random() < 0.15:
                new_type = NotionType.INTERNEURON
                if random.random() < diff_params["inhibitor_conversion_prob"]:
                    new_type = NotionType.INHIBITOR

        # 非胚胎期：按规则分化
        if new_type is None:
            # 分化期/稳态期/修剪期：强制确保类型多样性
            if self.development_stage in ("differentiation", "steady", "pruning", "synapse_burst"):
                type_counts = defaultdict(int)
                for n in self.notions.values():
                    type_counts[n.type.value] += 1

                # 强制确保oscillator存在（从stem或interneuron转化）
                if type_counts.get("oscillator", 0) < 5:
                    if (is_stem or notion.type == NotionType.INTERNEURON) and random.random() < 0.08:
                        new_type = NotionType.OSCILLATOR
                        period_range = diff_params["oscillator_period_range"]
                        notion.oscillator_period = random.randint(period_range[0], period_range[1])

                # 强制确保projector存在
                elif type_counts.get("projector", 0) < 3 and notion.out_degree > 5 and random.random() < 0.05:
                    new_type = NotionType.PROJECTOR

                # 确保sensor
                elif type_counts.get("sensor", 0) < 5 and is_stem and random.random() < 0.02:
                    new_type = NotionType.SENSOR

                # 确保gate节点
                elif type_counts.get("gate", 0) < 3 and notion.inhibitory_signal_count > 20 and random.random() < 0.05:
                    new_type = NotionType.GATE

            # stem分化规则
            if new_type is None and is_stem:
                # stem → memory: 单次激活强度 > 全局均值 × 3
                if (notion.activation > self.global_mean_activation *
                    diff_params["memory_activation_multiplier"]):
                    new_type = NotionType.MEMORY
                    notion.plasticity = 0.2

                # stem → gate: 持续接收抑制性信号
                elif notion.inhibitory_signal_count >= diff_params["gate_inhibitory_cycles"]:
                    new_type = NotionType.GATE

                # stem → hub: 入度+出度 > 周围节点均值 × 2
                elif (notion.in_degree + notion.out_degree >
                      self._mean_degree() * diff_params["hub_degree_multiplier"]):
                    new_type = NotionType.HUB
                    if not self._check_hub_monopoly(notion):
                        notion.plasticity = self.dna.params["connection"]["hub_locked_plasticity"]

                # stem → projector: 向量与另一区域节点余弦相似度 > 0.8
                elif self._has_similar_remote_node(notion, diff_params["projector_similarity_threshold"]):
                    new_type = NotionType.PROJECTOR

                # stem → interneuron: 连接数 > 3 且激活频率 > 全局均值
                elif (notion.out_degree >= diff_params["interneuron_min_connections"]
                      and notion.activation > self.global_mean_activation *
                      diff_params["interneuron_activation_ratio"]):
                    new_type = NotionType.INTERNEURON
                    if random.random() < diff_params["inhibitor_conversion_prob"]:
                        new_type = NotionType.INHIBITOR

                # stem → oscillator: 长期未被外部信号激活
                elif (notion.no_external_signal_cycles >=
                      diff_params["oscillator_no_signal_cycles"]
                      and notion.energy > 10 * diff_params["oscillator_energy_min_multiplier"]):
                    new_type = NotionType.OSCILLATOR
                    period_range = diff_params["oscillator_period_range"]
                    notion.oscillator_period = random.randint(period_range[0], period_range[1])

                # stem → sensor: 最后检查
                elif notion.no_external_signal_cycles < 3 and self.cycle > 500:
                    new_type = NotionType.SENSOR

        if new_type:
            notion.type = new_type
            return (notion.id, old_type, new_type.value)

        return None

    # ==================== 连接建立 ====================

    def _create_connections(self):
        """建立新连接（向量相似度加权随机）"""
        params = self.dna.params["connection"]
        base_prob = params["base_connection_prob"]
        connection_radius = self.dna.params["initial_connection_radius"]

        # 突触爆发期后缩小连接半径
        if self.development_stage in ("pruning", "differentiation", "steady"):
            connection_radius *= self.dna.get_development_params()["synapse_burst_radius_ratio"]

        notion_list = list(self.notions.values())
        if len(notion_list) < 2:
            return

        # 胚胎期增加连接概率促进网络形成
        if self.development_stage == "embryo":
            base_prob *= 3  # 胚胎期3倍连接概率

        # 终身可塑期：极低连接概率，只允许少量新连接
        if self.development_stage == "lifelong":
            base_prob *= 0.05  # 5%概率
            # 连接密度超过10%时停止建立新连接
            if self._connection_density() > 0.10:
                return

        # 随机采样（避免全量O(N²)）
        max_checks = min(5000, len(notion_list) * 10)
        for _ in range(max_checks):
            a = random.choice(notion_list)
            b = random.choice(notion_list)
            if a.id == b.id or not a.is_alive or not b.is_alive:
                continue

            # 空间距离检查
            dist = self._distance(a.position, b.position)
            if dist > connection_radius:
                continue

            # 已存在连接则跳过
            if b.id in a.connections or a.id in b.connections:
                continue

            # Hub垄断防护
            if a.type == NotionType.HUB or b.type == NotionType.HUB:
                if not self._check_hub_monopoly(a if a.type == NotionType.HUB else b):
                    continue

            # 向量相似度加权连接概率
            similarity = self._cosine_similarity(a.vector, b.vector)
            prob = similarity * base_prob if similarity > 0 else params["min_connection_prob"]

            if random.random() < prob:
                # 抑制性节点的传出连接为负值
                strength = 0.5
                if a.type == NotionType.INHIBITOR:
                    strength = -0.5
                self._add_connection(a.id, b.id, strength)
                self.stats["total_connections_created"] += 1

    def _add_connection(self, source_id: str, target_id: str, strength: float):
        """添加连接"""
        if source_id in self.notions and target_id in self.notions:
            self.notions[source_id].connections[target_id] = strength
            self.notions[source_id].out_degree += 1
            self.notions[target_id].in_degree += 1

    # ==================== 凋亡 ====================

    def _apoptosis(self):
        """凋亡：能量<阈值 且 孤立 → 删除"""
        config = self.dna.params
        to_remove = []

        for notion_id, notion in self.notions.items():
            if (notion.energy < config["apoptosis_energy_threshold"]
                and notion.out_degree + notion.in_degree <=
                config["apoptosis_isolation_threshold"]):
                to_remove.append(notion_id)

        for notion_id in to_remove:
            # 清理相关连接
            notion = self.notions[notion_id]
            for target_id in list(notion.connections.keys()):
                if target_id in self.notions:
                    self.notions[target_id].in_degree = max(0,
                        self.notions[target_id].in_degree - 1)
            del self.notions[notion_id]
            self.stats["total_apoptosis"] += 1

    # ==================== 动作解码 ====================

    def _decode_actions(self) -> List[Dict]:
        """
        projector节点的激活向量 → 12个固定动作原语的加权组合
        
        返回执行的1~3个最高权重动作
        """
        projector_nodes = [n for n in self.notions.values()
                          if n.type == NotionType.PROJECTOR and n.is_active]

        if not projector_nodes:
            return []

        # 聚合所有projector的激活向量
        decode_matrix = self.dna.get_action_decode_matrix(
            self.dna.params["initial_vector_dim"]
        )

        # 加权聚合
        combined_vector = np.zeros(self.dna.params["initial_vector_dim"], dtype=np.float32)
        for node in projector_nodes:
            combined_vector += node.activation * node.vector

        # 解码为动作权重
        action_weights = decode_matrix.T @ combined_vector  # (12,)

        # 取最高权重的1~3个动作
        action_names = [
            "MOVE_FORWARD", "MOVE_BACKWARD", "TURN_LEFT", "TURN_RIGHT",
            "APPROACH", "RETREAT", "CONSUME", "REST",
            "EMIT_SIGNAL", "GROW_SPLIT", "CONNECT_ATTEMPT", "SELF_MONITOR",
        ]

        # 排序并取top-k
        indices = np.argsort(np.abs(action_weights))[::-1]
        top_k = min(3, max(1, len(indices)))

        actions = []
        for idx in indices[:top_k]:
            if abs(action_weights[idx]) > 0.1:  # 阈值过滤
                actions.append({
                    "action": action_names[idx],
                    "weight": float(action_weights[idx]),
                })

        return actions

    # ==================== 全局统计更新 ====================

    def _update_global_stats(self):
        """更新全局统计"""
        if not self.notions:
            return

        activations = [n.activation for n in self.notions.values() if n.is_alive]
        self.global_mean_activation = np.mean(activations) if activations else 0
        self.global_activation_history.append(self.global_mean_activation)

        # 保持历史记录大小
        if len(self.global_activation_history) > 1000:
            self.global_activation_history = self.global_activation_history[-500:]

        # 更新节点度信息
        for notion in self.notions.values():
            notion.in_degree = sum(1 for n in self.notions.values()
                                  if notion.id in n.connections)
            notion.out_degree = len(notion.connections)

    # ==================== Hub垄断防护 ====================

    def _check_hub_monopoly(self, hub: Notion) -> bool:
        """
        Hub垄断防护：连接数达到全局总连接数的5% → 锁定
        
        返回True表示可以继续收集连接，False表示应锁定
        """
        total_connections = self._total_connections()
        if total_connections == 0:
            return True

        hub_connections = len(hub.connections)
        ratio = hub_connections / total_connections

        threshold = self.dna.params["connection"]["hub_max_global_connection_ratio"]
        if ratio >= threshold:
            # 锁定：plasticity降至0.01，转为只输出不收集
            hub.plasticity = self.dna.params["connection"]["hub_locked_plasticity"]
            return False
        return True

    # ==================== 辅助方法 ====================

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    def _distance(pos_a: Tuple, pos_b: Tuple) -> float:
        """计算3D距离"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_a, pos_b)))

    def _total_connections(self) -> int:
        """总连接数"""
        return sum(len(n.connections) for n in self.notions.values() if n.is_alive)

    def _connection_density(self) -> float:
        """连接密度 = 实际连接数 / 可能最大连接数"""
        n = len(self.notions)
        if n < 2:
            return 0.0
        max_connections = n * (n - 1)
        return self._total_connections() / max_connections

    def _mean_degree(self) -> float:
        """平均度数"""
        if not self.notions:
            return 0.0
        degrees = [n.in_degree + n.out_degree for n in self.notions.values()]
        return np.mean(degrees)

    def _split_rate_low(self) -> bool:
        """分裂速率是否降至初始的10%以下"""
        # 简化：检查最近50步内的分裂次数
        recent_splits = self.stats["total_splits"]
        if self.cycle < 50:
            return False
        rate = recent_splits / self.cycle
        return rate < 0.01  # 低于1%认为分裂速率很低

    def _migration_ratio_met(self, target_ratio: float) -> bool:
        """迁移完成度检查（简化：检查位置分布收敛）"""
        if len(self.notions) < 10:
            return False
        positions = np.array([n.position for n in self.notions.values()])
        std = np.std(positions, axis=0)
        return np.mean(std) < 8.0  # 位置标准差小于8认为迁移基本完成

    def _differentiation_stable(self) -> bool:
        """分化是否稳定（50周期内无新分化）"""
        total_diffs = sum(self.stats["total_differentiations"].values())
        if self.cycle < 100:
            return False
        # 简化：检查最近节点类型的多样性
        type_counts = defaultdict(int)
        for n in self.notions.values():
            type_counts[n.type.value] += 1
        return len(type_counts) >= 4  # 至少4种类型出现

    def _has_similar_remote_node(self, notion: Notion, threshold: float) -> bool:
        """检查是否有远程相似节点"""
        for other in self.notions.values():
            if other.id == notion.id or not other.is_alive:
                continue
            dist = self._distance(notion.position, other.position)
            if dist > 15:  # 远程
                sim = self._cosine_similarity(notion.vector, other.vector)
                if sim > threshold:
                    return True
        return False

    # ==================== 输入模式记录 ====================

    def record_input_pattern(self, pattern: np.ndarray):
        """记录输入模式（用于学习指标）"""
        self.input_patterns_history.append(pattern.copy())
        if len(self.input_patterns_history) > 100:
            self.input_patterns_history = self.input_patterns_history[-50:]

    def get_activation_pattern(self) -> np.ndarray:
        """获取当前全局激活模式"""
        if not self.notions:
            return np.array([])
        sorted_ids = sorted(self.notions.keys())
        return np.array([self.notions[nid].activation for nid in sorted_ids
                        if self.notions[nid].is_alive])
