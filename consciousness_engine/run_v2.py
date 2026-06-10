"""
意识引擎主循环 - 集成DNA种子Notion网络
物理法则 + 生物法则 + 意识法则(DNA生长) + 虚拟世界交互

运行模式：纯后端，无需GUI，加速模拟
"""

import sys
import os
import time
import yaml
import random
import numpy as np
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.dna.seed import DNASeed
from engine.dna.notion import NotionType
from engine.dna.notion_network import NotionNetwork
from engine.dna.metrics import ConsciousnessMetrics
from engine.physics.space import Vector3, SpatialRelations
from engine.bio.emotion import EmotionSystem


class ConsciousnessEngineV2:
    """
    意识引擎 v2 - DNA种子驱动的意识体生长
    
    架构:
    1. 虚拟世界层 - 物理空间、资源、事件
    2. 意识体宿主 - 3D位置、能量接口、感官输入
    3. 意识体大脑 - DNA种子驱动的Notion网络
    4. 意识涌现指标 - 7项定量指标 + TEII整合度
    """

    def __init__(self, config_path: str = "config.yaml", dna_params: Dict = None):
        # 加载配置
        self.config = self._load_config(config_path)

        # 加速模拟参数
        self.sim_speed = self.config.get("simulation", {}).get("speed", 10)  # 每tick模拟10个周期
        self.acceleration_mode = True  # 加速模式（无GUI）

        # 虚拟世界
        self.world_time = 0
        self.world_resources = []  # 可采集资源
        self.world_events = []  # 外部事件

        # 意识体宿主
        self.host_position = Vector3(0, 0, 0)
        self.host_energy = 1000.0
        self.host_sensor_input = {}

        # DNA种子 + Notion网络
        self.dna = DNASeed(params=dna_params)
        self.brain = NotionNetwork(self.dna)

        # 意识涌现指标
        self.metrics = ConsciousnessMetrics()

        # 情绪系统（门控学习率）
        self.emotion_system = EmotionSystem(self.config)

        # 空间关系
        self.spatial = SpatialRelations(self.config)

        # 统计
        self.stats = {
            "total_cycles": 0,
            "peak_notion_count": 0,
            "stage_history": [],
            "action_history": [],
        }

        # 初始化世界
        self._init_world()

    def _load_config(self, config_path: str) -> Dict:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _init_world(self):
        """初始化虚拟世界"""
        # 生成初始资源
        for i in range(20):
            self.world_resources.append({
                "id": f"resource_{i}",
                "position": Vector3(
                    random.uniform(-30, 30),
                    random.uniform(-5, 5),
                    random.uniform(-30, 30),
                ),
                "energy": random.uniform(20, 80),
                "type": random.choice(["food", "light", "signal"]),
            })

    def step(self) -> Dict:
        """
        引擎单步执行
        
        流程: 世界更新 → 感官输入 → 大脑处理 → 行为输出 → 指标记录
        """
        step_result = {
            "world_time": self.world_time,
            "notion_count": len(self.brain.notions),
            "stage": self.brain.development_stage,
            "host_energy": self.host_energy,
            "actions": [],
            "brain_steps": [],
        }

        # 执行sim_speed个模拟周期
        for _ in range(self.sim_speed):
            self.stats["total_cycles"] += 1

            # === 1. 世界更新 ===
            self._update_world()

            # === 2. 感官输入 ===
            sensory_input = self._gather_sensory_input()

            # === 3. 大脑处理 ===
            brain_result = self.brain.step(
                external_input=sensory_input,
                energy_gain=self._compute_energy_gain(),
            )

            step_result["brain_steps"].append(brain_result)

            # === 4. 行为输出 → 世界交互 ===
            actions = brain_result.get("actions", [])
            self._execute_actions(actions)
            step_result["actions"].extend(actions)

            # === 5. 情绪更新 ===
            self.emotion_system.update(dt=0.1)

            # === 6. 指标记录 ===
            self._record_metrics(sensory_input)

        self.world_time += 1

        # 更新峰值
        self.stats["peak_notion_count"] = max(
            self.stats["peak_notion_count"],
            len(self.brain.notions),
        )

        return step_result

    def _update_world(self):
        """更新虚拟世界"""
        # 资源再生
        if len(self.world_resources) < 20 and random.random() < 0.1:
            self.world_resources.append({
                "id": f"resource_{self.world_time}_{random.randint(0,999)}",
                "position": Vector3(
                    random.uniform(-30, 30),
                    random.uniform(-5, 5),
                    random.uniform(-30, 30),
                ),
                "energy": random.uniform(20, 80),
                "type": random.choice(["food", "light", "signal"]),
            })

        # 随机事件
        if random.random() < 0.05:
            self.world_events.append({
                "type": random.choice(["collision", "light_change", "social_signal"]),
                "intensity": random.uniform(0.1, 1.0),
                "time": self.world_time,
            })

        # 清理旧事件
        self.world_events = [e for e in self.world_events
                            if self.world_time - e["time"] < 10]

    def _gather_sensory_input(self) -> Dict[str, float]:
        """收集感官输入"""
        sensory = {}

        # 碰撞事件 → sensor激活
        collision_events = [e for e in self.world_events if e["type"] == "collision"]
        if collision_events:
            sensory["collision"] = sum(e["intensity"] for e in collision_events)

        # 光照强度/方向
        light_events = [e for e in self.world_events if e["type"] == "light_change"]
        if light_events:
            sensory["light"] = sum(e["intensity"] for e in light_events)

        # 资源接近信号
        nearby_resources = [r for r in self.world_resources
                          if (self.host_position - r["position"]).magnitude() < 10]
        if nearby_resources:
            sensory["resource"] = sum(r["energy"] for r in nearby_resources) / 100

        # 社交信号
        social_events = [e for e in self.world_events if e["type"] == "social_signal"]
        if social_events:
            sensory["social"] = sum(e["intensity"] for e in social_events)

        # 如果没有外部输入，添加微弱的随机噪声（保持网络活性）
        if not sensory:
            sensory["noise"] = random.uniform(0.01, 0.05)

        self.host_sensor_input = sensory
        return sensory

    def _compute_energy_gain(self) -> float:
        """计算本周期获得的能量"""
        # 加速模式下增加能量供给
        return max(0, len(self.world_resources) * 5 + 50)

    def _execute_actions(self, actions: List[Dict]):
        """执行动作"""
        for action in actions:
            action_name = action.get("action", "")
            weight = action.get("weight", 0)

            self.stats["action_history"].append(action_name)

            if action_name == "CONSUME":
                # 消耗最近资源
                self._consume_resource()
            elif action_name == "MOVE_FORWARD":
                self.host_position = Vector3(
                    self.host_position.x,
                    self.host_position.y,
                    self.host_position.z + 1,
                )
            elif action_name == "MOVE_BACKWARD":
                self.host_position = Vector3(
                    self.host_position.x,
                    self.host_position.y,
                    self.host_position.z - 1,
                )
            elif action_name == "TURN_LEFT":
                self.host_position = Vector3(
                    self.host_position.x - 1,
                    self.host_position.y,
                    self.host_position.z,
                )
            elif action_name == "TURN_RIGHT":
                self.host_position = Vector3(
                    self.host_position.x + 1,
                    self.host_position.y,
                    self.host_position.z,
                )
            elif action_name == "APPROACH":
                # 接近最近资源
                if self.world_resources:
                    nearest = min(self.world_resources,
                                key=lambda r: (self.host_position - r["position"]).magnitude())
                    direction = nearest["position"] - self.host_position
                    self.host_position = Vector3(
                        self.host_position.x + direction.x * 0.1,
                        self.host_position.y + direction.y * 0.1,
                        self.host_position.z + direction.z * 0.1,
                    )
            elif action_name == "RETREAT":
                self.host_position = Vector3(
                    self.host_position.x - 1,
                    self.host_position.y,
                    self.host_position.z - 1,
                )
            elif action_name == "REST":
                # 节能模式
                self.host_energy += 5
            elif action_name == "EMIT_SIGNAL":
                self.world_events.append({
                    "type": "social_signal",
                    "intensity": abs(weight),
                    "time": self.world_time,
                })
            elif action_name == "SELF_MONITOR":
                # 加强内部采样
                pass

            self.host_energy = min(1000, self.host_energy + weight * 2)

    def _consume_resource(self):
        """消耗最近资源"""
        if not self.world_resources:
            return
        nearest = min(self.world_resources,
                     key=lambda r: (self.host_position - r["position"]).magnitude())
        dist = (self.host_position - nearest["position"]).magnitude()
        if dist < 5:
            self.host_energy += nearest["energy"]
            self.world_resources.remove(nearest)

    def _record_metrics(self, sensory_input: Dict[str, float]):
        """记录意识涌现指标数据"""
        # 输入模式
        input_pattern = np.array(list(sensory_input.values()), dtype=np.float32)

        # 激活模式
        activation_pattern = self.brain.get_activation_pattern()

        # self-sensor（全局平均能量）
        avg_energy = np.mean([n.energy for n in self.brain.notions.values()
                            if n.is_alive]) / 100

        # gate平均阈值
        gate_nodes = [n for n in self.brain.notions.values()
                     if n.type == NotionType.GATE]
        gate_avg_threshold = (np.mean([n.threshold for n in gate_nodes])
                             if gate_nodes else 0.5)

        # 预测误差（简化：当前激活与上一步的差）
        if len(self.brain.global_activation_history) > 1:
            prev = self.brain.global_activation_history[-2]
            curr = self.brain.global_activation_history[-1]
            pred_error = abs(curr - prev)
        else:
            pred_error = 0.0

        self.metrics.record_cycle(
            input_pattern=input_pattern,
            activation_pattern=activation_pattern,
            self_sensor_value=avg_energy,
            gate_avg_threshold=gate_avg_threshold,
            prediction_error=pred_error,
        )

    def get_state_summary(self) -> Dict:
        """获取引擎状态摘要"""
        # 类型统计
        type_counts = {}
        for notion in self.brain.notions.values():
            t = notion.type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        # 连接统计
        total_connections = self.brain._total_connections()
        avg_connections = (total_connections / max(1, len(self.brain.notions)))

        return {
            "world_time": self.world_time,
            "total_cycles": self.stats["total_cycles"],
            "notion_count": len(self.brain.notions),
            "type_distribution": type_counts,
            "total_connections": total_connections,
            "avg_connections_per_node": avg_connections,
            "connection_density": self.brain._connection_density(),
            "development_stage": self.brain.development_stage,
            "host_energy": self.host_energy,
            "host_position": (self.host_position.x, self.host_position.y, self.host_position.z),
            "peak_notion_count": self.stats["peak_notion_count"],
            "action_distribution": self._action_distribution(),
        }

    def _action_distribution(self) -> Dict[str, int]:
        """动作分布统计"""
        dist = {}
        for action in self.stats["action_history"][-1000:]:
            dist[action] = dist.get(action, 0) + 1
        return dist

    def compute_metrics(self) -> Dict:
        """计算意识涌现指标"""
        return self.metrics.compute_all(self.stats["total_cycles"])

    def print_metrics_report(self):
        """打印指标报告"""
        self.metrics.print_report(self.stats["total_cycles"])

    def run(self, steps: int = 100, report_interval: int = 20, verbose: bool = True):
        """
        运行引擎指定步数
        
        Args:
            steps: 运行步数
            report_interval: 报告间隔
            verbose: 是否输出详细信息
        """
        start_time = time.time()

        if verbose:
            print("\n" + "="*60)
            print("意识引擎 v2 - DNA种子驱动")
            print(f"目标: {steps}步, 加速: {self.sim_speed}周期/步")
            print(f"初始Notion: {len(self.brain.notions)}")
            print("="*60 + "\n")

        for i in range(steps):
            result = self.step()

            if verbose and (i + 1) % report_interval == 0:
                state = self.get_state_summary()
                print(f"[步 {i+1}/{steps}] "
                      f"Notion: {state['notion_count']}, "
                      f"阶段: {state['development_stage']}, "
                      f"连接: {state['total_connections']}, "
                      f"密度: {state['connection_density']:.4f}, "
                      f"能量: {state['host_energy']:.0f}")

                # 打印类型分布
                types = state['type_distribution']
                type_str = ", ".join(f"{k}:{v}" for k, v in sorted(types.items()))
                print(f"  类型: {type_str}")

        elapsed = time.time() - start_time

        if verbose:
            print(f"\n{'='*60}")
            print(f"运行完成: {steps}步, {elapsed:.2f}s")
            print(f"总模拟周期: {self.stats['total_cycles']}")
            print(f"{'='*60}")

            # 打印指标报告
            self.print_metrics_report()

            # 最终状态
            final_state = self.get_state_summary()
            print(f"\n最终状态:")
            print(f"  Notion: {final_state['notion_count']}")
            print(f"  阶段: {final_state['development_stage']}")
            print(f"  连接: {final_state['total_connections']}")
            print(f"  类型分布: {final_state['type_distribution']}")

    def close(self):
        """关闭引擎"""
        pass


def main():
    """主入口"""
    engine = ConsciousnessEngineV2("config.yaml")

    # 创建初始干细胞
    stem_cells = engine.dna.create_initial_stem_cells()
    for cell in stem_cells:
        engine.brain.notions[cell.id] = cell

    # 运行500步（500×10=5000个模拟周期，足够积累指标数据）
    engine.run(steps=500, report_interval=50, verbose=True)

    engine.close()


if __name__ == "__main__":
    main()
