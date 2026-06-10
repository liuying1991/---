"""
Consciousness Engine - 意识引擎主循环
感知 → 编码 → 记忆 → 决策 → 行动
"""

import sys
import os
import time
import yaml
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.physics.space import Vector3, SpatialRelations
from engine.bio.perception import PerceptionSystem
from engine.bio.nervous import NervousSystem
from engine.bio.emotion import EmotionSystem
from engine.consciousness.memory_bridge import MemoryBridge
from engine.consciousness.attention_system import AttentionSystem
from engine.vr.renderer import Renderer3D
from engine.vr.interface import ConsciousnessInterface


class ConsciousnessEngine:
    """
    意识引擎 - 3D虚拟意识空间
    
    架构层级:
    1. 物理法则层 - 空间几何、时间流、因果律
    2. 生物法则层 - 感知系统、神经系统、情绪系统
    3. 意识法则层 - 记忆大脑(NomadMem v4.0)、注意力系统
    4. 虚拟现实层 - 3D渲染、交互界面
    """

    def __init__(self, config_path: str = "config.yaml"):
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 引擎状态
        self.is_running = False
        self.current_time = 0.0
        self.tick_count = 0
        
        # 统计信息
        self.stats = {
            "total_perceptions": 0,
            "total_memories_encoded": 0,
            "total_decisions": 0,
            "total_actions": 0,
            "start_time": 0.0,
        }
        
        # 初始化各层
        self._init_layers()
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        print(f"[Engine] Config not found at {config_path}, using defaults")
        return {}
    
    def _init_layers(self):
        """初始化所有层级"""
        print("[Engine] Initializing layers...")
        
        # === 物理法则层 ===
        self.spatial_relations = SpatialRelations(self.config)
        
        # === 生物法则层 ===
        self.perception_system = PerceptionSystem(self.config)
        self.nervous_system = NervousSystem(self.config)
        self.emotion_system = EmotionSystem(self.config)
        
        # === 意识法则层 ===
        self.memory_bridge = MemoryBridge(self.config)
        self.memory_bridge.initialize()
        self.attention_system = AttentionSystem(self.config)
        
        # === 虚拟现实层 ===
        self.renderer = Renderer3D(self.config)
        self.interface = ConsciousnessInterface()
        
        # 设置摄像机初始位置
        camera_config = self.config.get("vr", {}).get("camera", {})
        self.renderer.set_camera_position(
            camera_config.get("x", 0),
            camera_config.get("y", 0),
            camera_config.get("z", 10),
        )
        
        print("[Engine] All layers initialized.")
    
    def tick(self, dt: float = 0.1) -> Dict:
        """
        引擎主循环 - 单步执行
        
        流程: 感知 → 编码 → 记忆 → 决策 → 行动
        
        Args:
            dt: 时间步长（秒）
            
        Returns:
            本步执行结果
        """
        self.current_time += dt
        self.tick_count += 1
        
        result = {
            "tick": self.tick_count,
            "time": self.current_time,
            "perceptions": [],
            "memories_encoded": 0,
            "decisions": [],
            "actions": [],
        }
        
        # === 1. 感知阶段 ===
        perceptions = self._perceive(dt)
        result["perceptions"] = perceptions
        self.stats["total_perceptions"] += len(perceptions)
        
        # === 2. 编码阶段 ===
        encoded_count = self._encode_perceptions(perceptions)
        result["memories_encoded"] = encoded_count
        self.stats["total_memories_encoded"] += encoded_count
        
        # === 3. 记忆检索 ===
        relevant_memories = self._retrieve_memories(perceptions)
        
        # === 4. 决策阶段 ===
        decisions = self._decide(perceptions, relevant_memories)
        result["decisions"] = decisions
        self.stats["total_decisions"] += len(decisions)
        
        # === 5. 行动阶段 ===
        actions = self._act(decisions)
        result["actions"] = actions
        self.stats["total_actions"] += len(actions)
        
        # === 6. 更新3D场景 ===
        self.renderer.update(dt)
        
        # === 7. 神经系统更新 ===
        self.nervous_system.update(dt)
        
        # === 8. 情绪系统更新 ===
        self.emotion_system.update(dt, self.perception_system)
        
        return result
    
    def _perceive(self, dt: float) -> List[Dict]:
        """感知阶段 - 收集3D空间中的感知数据"""
        perceptions = []
        
        # 获取摄像机位置作为感知中心
        camera_pos = self.renderer.scene.camera.position
        observer_pos = (camera_pos.x, camera_pos.y, camera_pos.z)
        
        # 获取视野内对象
        visible_objects = self.renderer.scene.get_objects_in_range(
            camera_pos, radius=50.0
        )
        
        for obj in visible_objects:
            # 视觉感知
            visual = self.perception_system.process_visual(
                object_id=obj.id,
                object_type=obj.type,
                distance=(camera_pos - obj.position).magnitude(),
                position=(obj.position.x, obj.position.y, obj.position.z),
            )
            if visual:
                perceptions.append(visual)
            
            # 如果对象有声音属性，处理听觉感知
            if obj.properties.get("emits_sound"):
                audio = self.perception_system.process_audio(
                    object_id=obj.id,
                    sound_type=obj.properties.get("sound_type", "ambient"),
                    distance=(camera_pos - obj.position).magnitude(),
                )
                if audio:
                    perceptions.append(audio)
        
        # 更新注意力系统
        if visible_objects:
            objects_for_attention = [
                {
                    "id": obj.id,
                    "position": (obj.position.x, obj.position.y, obj.position.z),
                    "salience": obj.properties.get("salience", 0.5),
                }
                for obj in visible_objects
            ]
            self.attention_system.update_focus_from_perception(
                objects_for_attention, observer_pos
            )
        
        return perceptions
    
    def _encode_perceptions(self, perceptions: List[Dict]) -> int:
        """编码阶段 - 将感知数据写入记忆大脑"""
        encoded = 0
        
        for perception in perceptions:
            # 获取情绪触发
            emotion_score = self.emotion_system.get_current_emotion_score()
            
            # 编码到记忆
            vector_id = self.memory_bridge.encode_perception(
                content=perception.get("description", ""),
                perception_type=perception.get("type", "visual"),
                spatial_location=perception.get("position"),
                emotion_trigger=emotion_score,
            )
            
            if vector_id is not None:
                encoded += 1
                
                # 更新对象注意力
                obj_id = perception.get("object_id", "")
                self.renderer.update_object_attention(
                    obj_id,
                    attention=perception.get("salience", 0.5),
                    emotion=emotion_score,
                )
        
        return encoded
    
    def _retrieve_memories(self, perceptions: List[Dict]) -> List[Dict]:
        """记忆检索 - 根据当前感知检索相关记忆"""
        if not perceptions:
            return []
        
        # 使用最新感知作为查询
        latest = perceptions[-1]
        query = latest.get("description", "")
        
        memories = self.memory_bridge.retrieve_relevant_memories(
            query=query,
            top_k=3,
            min_similarity=0.2,
        )
        
        return memories
    
    def _decide(self, perceptions: List[Dict], memories: List[Dict]) -> List[Dict]:
        """决策阶段 - 基于感知和记忆做出决策"""
        decisions = []
        
        # 获取工作记忆焦点
        wm_focus = self.memory_bridge.get_working_memory_focus()
        
        # 获取注意力分布
        top_attention = self.attention_system.get_top_focused_objects(3)
        
        # 获取情绪状态
        emotion_state = self.emotion_system.get_emotion_state()
        
        # 基于记忆和感知做出决策
        if memories:
            # 有相关记忆，基于记忆决策
            for memory in memories[:2]:
                decisions.append({
                    "type": "memory_recall",
                    "content": memory.get("content", ""),
                    "similarity": memory.get("similarity", 0),
                    "confidence": memory.get("similarity", 0) * emotion_state.get("arousal", 0.5),
                })
        
        # 基于注意力决策
        if top_attention:
            top_obj_id, top_attention_score = top_attention[0]
            decisions.append({
                "type": "focus_shift",
                "target": top_obj_id,
                "attention": top_attention_score,
            })
        
        # 基于工作记忆决策
        if wm_focus:
            decisions.append({
                "type": "working_memory_active",
                "items_count": len(wm_focus),
                "items": [item.get("content", "") for item in wm_focus[:2]],
            })
        
        return decisions
    
    def _act(self, decisions: List[Dict]) -> List[Dict]:
        """行动阶段 - 执行决策"""
        actions = []
        
        for decision in decisions:
            action_type = decision.get("type", "")
            
            if action_type == "memory_recall":
                # 记忆召回行动 - 调整摄像机朝向
                actions.append({
                    "type": "camera_adjust",
                    "reason": "memory_recall",
                    "content": decision.get("content", ""),
                })
            
            elif action_type == "focus_shift":
                # 焦点转移行动 - 移动摄像机
                actions.append({
                    "type": "focus_shift",
                    "target": decision.get("target", ""),
                    "attention": decision.get("attention", 0),
                })
            
            elif action_type == "working_memory_active":
                # 工作记忆活跃 - 保持当前状态
                actions.append({
                    "type": "maintain_focus",
                    "reason": "working_memory_active",
                })
        
        return actions
    
    def add_object(self, obj_id: str, x: float, y: float, z: float, 
                   obj_type: str = "default", properties: Dict = None):
        """向3D空间添加对象"""
        self.renderer.add_object(obj_id, x, y, z, obj_type, properties)
    
    def remove_object(self, obj_id: str):
        """从3D空间移除对象"""
        self.renderer.scene.remove_object(obj_id)
    
    def get_state_summary(self) -> Dict:
        """获取引擎状态摘要"""
        return {
            "time": self.current_time,
            "ticks": self.tick_count,
            "objects": len(self.renderer.scene.objects),
            "working_memory_focus": self.memory_bridge.get_working_memory_focus(),
            "cortex_summary": self.memory_bridge.get_cortex_summary(),
            "emotion_state": self.emotion_system.get_emotion_state(),
            "attention_top": self.attention_system.get_top_focused_objects(3),
            "stats": self.stats,
        }
    
    def render(self) -> str:
        """渲染当前帧"""
        return self.renderer.render_frame()
    
    def run(self, steps: int = 10, dt: float = 0.1, verbose: bool = True):
        """
        运行引擎指定步数
        
        Args:
            steps: 运行步数
            dt: 每步时间
            verbose: 是否输出详细信息
        """
        self.is_running = True
        self.stats["start_time"] = time.time()
        
        if verbose:
            print("\n" + "="*50)
            print("Consciousness Engine - Starting")
            print("="*50 + "\n")
        
        for i in range(steps):
            result = self.tick(dt)
            
            if verbose:
                print(f"[Tick {result['tick']}] Perceptions: {len(result['perceptions'])}, "
                      f"Memories: {result['memories_encoded']}, "
                      f"Decisions: {len(result['decisions'])}, "
                      f"Actions: {len(result['actions'])}")
                
                # 每5步渲染一次场景
                if (i + 1) % 5 == 0:
                    print("\n" + self.render())
                    print(self.renderer.render_state_summary() + "\n")
        
        self.is_running = False
        
        if verbose:
            elapsed = time.time() - self.stats["start_time"]
            print(f"\nEngine stopped after {steps} ticks ({elapsed:.2f}s)")
            print(f"State summary: {self.get_state_summary()}")
    
    def close(self):
        """关闭引擎"""
        self.is_running = False
        self.memory_bridge.close()
        print("[Engine] Shut down.")


def main():
    """主入口"""
    # 创建引擎
    engine = ConsciousnessEngine("config.yaml")
    
    # 添加一些初始对象
    engine.add_object("tree_1", 5, 0, 0, "nature", 
                     {"salience": 0.7, "emits_sound": False})
    engine.add_object("river_1", -3, 0, 2, "nature",
                     {"salience": 0.8, "emits_sound": True, "sound_type": "water"})
    engine.add_object("building_1", 0, 3, -5, "structure",
                     {"salience": 0.9, "emits_sound": False})
    engine.add_object("person_1", 2, 0, 3, "entity",
                     {"salience": 0.95, "emits_sound": True, "sound_type": "voice"})
    engine.add_object("bird_1", 8, 5, 1, "creature",
                     {"salience": 0.6, "emits_sound": True, "sound_type": "chirp"})
    
    # 运行引擎
    engine.run(steps=15, dt=0.5, verbose=True)
    
    # 关闭引擎
    engine.close()


if __name__ == "__main__":
    main()
