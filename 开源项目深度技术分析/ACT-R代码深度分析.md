# ACT-R代码深度分析文档

## 项目概述

ACT-R(Adaptive Control of Thought-Rational)是一个认知架构，旨在模拟人类认知过程，包括感知、记忆、注意、决策和行动等。它结合了符号处理和亚符号处理，提供了对人类认知行为的详细模拟，是认知科学和人工智能研究的重要工具。

## 项目结构分析

### 核心模块结构
```
actr/
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── agent.py               # 智能体核心
│   ├── modules.py             # 模块系统
│   ├── buffers.py             # 缓冲区系统
│   ├── production_system.py   # 产生式系统
│   └── scheduler.py           # 调度器
├── memory/                    # 记忆模块
│   ├── __init__.py
│   ├── declarative_memory.py  # 陈述性记忆
│   ├── procedural_memory.py   # 程序性记忆
│   ├── chunk.py               # 组块表示
│   └── activation.py          # 激活计算
├── modules/                   # 功能模块
│   ├── __init__.py
│   ├── visual.py              # 视觉模块
│   ├── auditory.py            # 听觉模块
│   ├── motor.py               # 运动模块
│   ├── speech.py              # 语音模块
│   └── temporal.py            # 时间模块
├── utilities/                 # 工具模块
│   ├── __init__.py
│   ├── logger.py              # 日志管理
│   ├── config.py              # 配置管理
│   └── helpers.py             # 辅助函数
├── interfaces/                # 接口模块
│   ├── __init__.py
│   ├── cli.py                 # 命令行接口
│   ├── api.py                 # API接口
│   └── gui.py                 # 图形界面
├── tests/                     # 测试模块
└── examples/                  # 示例代码
```

### 主要代码文件分析

#### 1. 智能体核心 (core/agent.py)
- **ACTRAgent类**: ACT-R智能体的核心实现
- **模块管理**: 各功能模块的协调和管理
- **认知循环**: 认知处理的主要循环

#### 2. 产生式系统 (core/production_system.py)
- **产生式规则**: 条件-动作规则表示和匹配
- **规则选择**: 基于效用值的规则选择
- **冲突解决**: 多规则匹配时的冲突解决机制

#### 3. 记忆系统 (memory/)
- **陈述性记忆**: 事实和事件的存储与检索
- **程序性记忆**: 产生式规则的存储与执行
- **激活计算**: 记忆项目的激活度计算

#### 4. 功能模块 (modules/)
- **感知模块**: 视觉、听觉等感知处理
- **运动模块**: 动作执行和运动控制
- **语音模块**: 语音识别和语音合成

## 接口分析

### 1. 核心智能体接口

#### 智能体初始化接口
```python
from actr import ACTRAgent

# 初始化ACT-R智能体
agent = ACTRAgent(
    name="infant_ai_butler",
    model_file="models/infant_ai_model.lisp",
    parameters={
        "visual_attention_delay": 0.085,
        "motor_execution_delay": 0.1,
        "declarative_memory_activation_threshold": -0.5
    }
)

# 加载模型
agent.load_model()

# 启动智能体
agent.start()
```

#### 认知处理接口
```python
# 添加感知输入
visual_input = {
    "type": "visual",
    "object": "baby",
    "state": "crying",
    "location": "crib"
}

agent.add_perceptual_input(visual_input)

# 运行认知循环
agent.run_cycle()

# 获取当前状态
current_state = agent.get_current_state()
print(current_state)

# 执行动作
agent.execute_action("comfort_baby")
```

#### 模型参数接口
```python
# 获取模型参数
parameters = agent.get_parameters()
print(f"Visual attention delay: {parameters['visual_attention_delay']}")

# 设置模型参数
agent.set_parameter("visual_attention_delay", 0.1)
agent.set_parameter("declarative_memory_activation_threshold", -0.3)

# 重置参数为默认值
agent.reset_parameters()
```

### 2. 记忆系统接口
```python
# 陈述性记忆操作
chunk = {
    "isa": "baby-state",
    "name": "baby1",
    "state": "crying",
    "location": "crib",
    "time": "14:30"
}

agent.add_declarative_memory(chunk)

# 检索陈述性记忆
retrieved_chunks = agent.retrieve_declarative_memory({
    "isa": "baby-state",
    "state": "crying"
})

for chunk in retrieved_chunks:
    print(f"Retrieved: {chunk['name']} - {chunk['state']}")

# 程序性记忆操作
production = {
    "name": "comfort-crying-baby",
    "conditions": [
        "?visual-buffer> isa visual-object",
        "?visual-buffer> state crying",
        "?visual-buffer> isa baby"
    ],
    "actions": [
        "!output!> type comfort",
        "!output!> method pick_up",
        "!output!> target ?visual-buffer>"
    ]
}

agent.add_production(production)

# 获取产生式规则统计
stats = agent.get_production_statistics()
print(f"Total productions: {stats['total_productions']}")
print(f"Fired productions: {stats['fired_productions']}")
```

### 3. 模块接口
```python
# 视觉模块操作
agent.visual_module.add_object({
    "type": "baby",
    "state": "crying",
    "location": "crib"
})

# 设置视觉注意
agent.visual_module.set_attention("baby")

# 获取视觉缓冲区内容
visual_buffer = agent.visual_module.get_buffer_contents()
print(f"Visual buffer: {visual_buffer}")

# 运动模块操作
agent.motor_module.prepare_action("pick_up", {"target": "baby"})
agent.motor_module.execute_action()

# 获取运动状态
motor_state = agent.motor_module.get_state()
print(f"Motor state: {motor_state}")
```

## 数据流分析

### 1. 认知循环流程
```
感知输入 → 缓冲区更新 → 产生式匹配 → 冲突解决 → 动作执行 → 模块更新 → 感知输入
```

### 2. 记忆检索流程
```
检索请求 → 激活计算 → 候选选择 → 延迟计算 → 记忆检索 → 缓冲区更新
```

### 3. 动作执行流程
```
动作请求 → 运动准备 → 执行延迟 → 动作执行 → 结果反馈 → 状态更新
```

### 4. 注意力流程
```
环境刺激 → 感知处理 → 注意力分配 → 缓冲区更新 → 产生式触发 → 注意力转移
```

## 关键代码实现细节

### 1. 智能体核心实现
```python
class ACTRAgent:
    """ACT-R智能体核心实现"""
    
    def __init__(self, name, model_file=None, parameters=None):
        self.name = name
        self.model_file = model_file
        self.parameters = parameters or {}
        
        # 初始化模块
        self.modules = {}
        self.buffers = {}
        self.production_system = ProductionSystem()
        self.declarative_memory = DeclarativeMemory()
        self.procedural_memory = ProceduralMemory()
        self.scheduler = Scheduler()
        
        # 初始化默认参数
        self._initialize_default_parameters()
        
        # 应用自定义参数
        self._apply_custom_parameters()
        
        # 初始化核心模块
        self._initialize_modules()
        
        # 加载模型文件
        if model_file:
            self.load_model()
    
    def _initialize_default_parameters(self):
        """初始化默认参数"""
        default_params = {
            "visual_attention_delay": 0.085,  # 视觉注意延迟(秒)
            "motor_execution_delay": 0.1,    # 运动执行延迟(秒)
            "declarative_memory_activation_threshold": -0.5,  # 陈述性记忆激活阈值
            "declarative_fan_parameter": 1.0,  # 陈述性记忆扇形参数
            "production_utility_learning_rate": 0.2,  # 产生式效用学习率
            "base_level_activation": 0.0,     # 基础激活水平
            "latency_factor": 0.1,           # 延迟因子
            "latency_exponent": 1.0          # 延迟指数
        }
        
        for param, value in default_params.items():
            if param not in self.parameters:
                self.parameters[param] = value
    
    def _apply_custom_parameters(self):
        """应用自定义参数"""
        for param, value in self.parameters.items():
            self.set_parameter(param, value)
    
    def _initialize_modules(self):
        """初始化核心模块"""
        # 初始化缓冲区
        self.buffers["visual"] = Buffer("visual")
        self.buffers["aural"] = Buffer("aural")
        self.buffers["manual"] = Buffer("manual")
        self.buffers["vocal"] = Buffer("vocal")
        self.buffers["retrieval"] = Buffer("retrieval")
        self.buffers["goal"] = Buffer("goal")
        
        # 初始化功能模块
        self.modules["visual"] = VisualModule(self.buffers["visual"], self.parameters)
        self.modules["aural"] = AuralModule(self.buffers["aural"], self.parameters)
        self.modules["manual"] = ManualModule(self.buffers["manual"], self.parameters)
        self.modules["vocal"] = VocalModule(self.buffers["vocal"], self.parameters)
        
        # 初始化记忆模块
        self.modules["declarative"] = DeclarativeModule(
            self.declarative_memory, 
            self.buffers["retrieval"], 
            self.parameters
        )
        self.modules["procedural"] = ProceduralModule(
            self.procedural_memory, 
            self.production_system, 
            self.parameters
        )
    
    def load_model(self):
        """加载模型文件"""
        if not self.model_file:
            return
        
        # 解析模型文件
        model_data = self._parse_model_file(self.model_file)
        
        # 加载产生式规则
        for production in model_data.get("productions", []):
            self.add_production(production)
        
        # 加载初始陈述性记忆
        for chunk in model_data.get("chunks", []):
            self.add_declarative_memory(chunk)
        
        # 设置初始缓冲区状态
        for buffer_name, buffer_content in model_data.get("initial_buffers", {}).items():
            if buffer_name in self.buffers:
                self.buffers[buffer_name].set_content(buffer_content)
    
    def add_perceptual_input(self, input_data):
        """添加感知输入"""
        input_type = input_data.get("type")
        
        if input_type == "visual":
            self.modules["visual"].add_input(input_data)
        elif input_type == "aural":
            self.modules["aural"].add_input(input_data)
        else:
            raise ValueError(f"Unknown input type: {input_type}")
    
    def run_cycle(self):
        """运行认知循环"""
        # 更新模块状态
        self._update_modules()
        
        # 匹配产生式规则
        matched_productions = self.production_system.match_productions(self.buffers)
        
        # 选择产生式规则
        selected_production = self._select_production(matched_productions)
        
        if selected_production:
            # 执行产生式规则
            self._execute_production(selected_production)
            
            # 更新产生式效用
            self._update_production_utility(selected_production)
        
        # 推进时间
        self.scheduler.advance_time()
    
    def get_current_state(self):
        """获取当前状态"""
        state = {
            "time": self.scheduler.current_time,
            "buffers": {},
            "modules": {}
        }
        
        # 获取缓冲区状态
        for buffer_name, buffer in self.buffers.items():
            state["buffers"][buffer_name] = buffer.get_content()
        
        # 获取模块状态
        for module_name, module in self.modules.items():
            state["modules"][module_name] = module.get_state()
        
        return state
    
    def execute_action(self, action_name, parameters=None):
        """执行动作"""
        if action_name in self.modules["manual"].actions:
            return self.modules["manual"].execute_action(action_name, parameters)
        elif action_name in self.modules["vocal"].actions:
            return self.modules["vocal"].execute_action(action_name, parameters)
        else:
            raise ValueError(f"Unknown action: {action_name}")
    
    def add_declarative_memory(self, chunk):
        """添加陈述性记忆"""
        chunk_id = self.declarative_memory.add_chunk(chunk)
        return chunk_id
    
    def retrieve_declarative_memory(self, request):
        """检索陈述性记忆"""
        return self.declarative_memory.retrieve(request)
    
    def add_production(self, production):
        """添加产生式规则"""
        production_id = self.procedural_memory.add_production(production)
        return production_id
    
    def get_production_statistics(self):
        """获取产生式规则统计"""
        return {
            "total_productions": len(self.procedural_memory.productions),
            "fired_productions": self.production_system.fired_count,
            "utility_stats": self.procedural_memory.get_utility_statistics()
        }
    
    def get_parameter(self, parameter_name):
        """获取参数值"""
        return self.parameters.get(parameter_name)
    
    def set_parameter(self, parameter_name, value):
        """设置参数值"""
        self.parameters[parameter_name] = value
        
        # 更新相关模块参数
        for module in self.modules.values():
            if hasattr(module, 'set_parameter'):
                module.set_parameter(parameter_name, value)
    
    def reset_parameters(self):
        """重置参数为默认值"""
        self._initialize_default_parameters()
        self._apply_custom_parameters()
    
    def _update_modules(self):
        """更新模块状态"""
        for module in self.modules.values():
            module.update(self.scheduler.current_time)
    
    def _select_production(self, matched_productions):
        """选择产生式规则"""
        if not matched_productions:
            return None
        
        # 计算每个产生式的效用
        for production in matched_productions:
            production["utility"] = self._calculate_production_utility(production)
        
        # 选择效用最高的产生式
        selected = max(matched_productions, key=lambda p: p["utility"])
        return selected
    
    def _execute_production(self, production):
        """执行产生式规则"""
        # 记录产生式触发
        self.production_system.fire_production(production)
        
        # 执行产生式动作
        for action in production["actions"]:
            self._execute_action(action)
    
    def _execute_action(self, action):
        """执行动作"""
        action_type = action.get("type")
        
        if action_type == "buffer-modification":
            buffer_name = action.get("buffer")
            if buffer_name in self.buffers:
                self.buffers[buffer_name].modify(action.get("modifications", {}))
        
        elif action_type == "buffer-clear":
            buffer_name = action.get("buffer")
            if buffer_name in self.buffers:
                self.buffers[buffer_name].clear()
        
        elif action_type == "module-request":
            module_name = action.get("module")
            request = action.get("request")
            
            if module_name in self.modules:
                self.modules[module_name].process_request(request)
        
        elif action_type == "output":
            # 处理输出动作
            output_content = action.get("content")
            print(f"Output: {output_content}")
    
    def _calculate_production_utility(self, production):
        """计算产生式效用"""
        # 获取基础效用
        base_utility = production.get("base_utility", 0)
        
        # 获取学习效用
        learned_utility = self.procedural_memory.get_utility(production["name"])
        
        # 计算噪声
        noise = self._calculate_utility_noise()
        
        return base_utility + learned_utility + noise
    
    def _calculate_utility_noise(self):
        """计算效用噪声"""
        # 简单实现：使用正态分布噪声
        import random
        return random.gauss(0, 0.1)
    
    def _update_production_utility(self, production):
        """更新产生式效用"""
        # 获取当前效用
        current_utility = self.procedural_memory.get_utility(production["name"])
        
        # 计算奖励
        reward = self._calculate_reward(production)
        
        # 更新效用
        learning_rate = self.parameters["production_utility_learning_rate"]
        new_utility = current_utility + learning_rate * (reward - current_utility)
        
        self.procedural_memory.set_utility(production["name"], new_utility)
    
    def _calculate_reward(self, production):
        """计算奖励"""
        # 简单实现：基于目标达成情况计算奖励
        # 实际实现需要更复杂的奖励计算逻辑
        return 0.1  # 固定奖励
    
    def _parse_model_file(self, file_path):
        """解析模型文件"""
        # 简单实现：假设模型文件是JSON格式
        # 实际实现需要支持ACT-R的LISP格式
        import json
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing model file: {e}")
            return {}
```

### 2. 记忆系统核心实现
```python
class DeclarativeMemory:
    """陈述性记忆实现"""
    
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.chunks = {}
        self.activation_values = {}
        self.retrieval_history = {}
        
        # 参数
        self.base_level_activation = self.parameters.get("base_level_activation", 0.0)
        self.fan_parameter = self.parameters.get("declarative_fan_parameter", 1.0)
        self.activation_threshold = self.parameters.get("declarative_memory_activation_threshold", -0.5)
        self.latency_factor = self.parameters.get("latency_factor", 0.1)
        self.latency_exponent = self.parameters.get("latency_exponent", 1.0)
    
    def add_chunk(self, chunk):
        """添加组块"""
        chunk_id = str(uuid.uuid4())
        
        # 添加时间戳
        chunk["creation_time"] = time.time()
        chunk["access_count"] = 0
        chunk["last_access_time"] = chunk["creation_time"]
        
        # 存储组块
        self.chunks[chunk_id] = chunk
        
        # 计算初始激活值
        self._calculate_activation(chunk_id)
        
        return chunk_id
    
    def retrieve(self, request):
        """检索组块"""
        # 计算所有组块的激活值
        for chunk_id in self.chunks:
            self._calculate_activation(chunk_id)
        
        # 筛选符合请求的组块
        matching_chunks = []
        for chunk_id, chunk in self.chunks.items():
            if self._chunk_matches_request(chunk, request):
                matching_chunks.append({
                    "id": chunk_id,
                    "chunk": chunk,
                    "activation": self.activation_values[chunk_id]
                })
        
        # 按激活值排序
        matching_chunks.sort(key=lambda x: x["activation"], reverse=True)
        
        # 过滤低于激活阈值的组块
        matching_chunks = [
            chunk for chunk in matching_chunks 
            if chunk["activation"] >= self.activation_threshold
        ]
        
        # 更新访问历史
        if matching_chunks:
            selected_chunk = matching_chunks[0]
            self._update_access_history(selected_chunk["id"])
            
            # 返回组块内容
            return [selected_chunk["chunk"]]
        
        return []
    
    def _calculate_activation(self, chunk_id):
        """计算组块激活值"""
        chunk = self.chunks[chunk_id]
        current_time = time.time()
        
        # 计算基础水平激活
        time_since_creation = current_time - chunk["creation_time"]
        base_activation = math.log(time_since_creation / self.latency_factor)
        
        # 计算扇形效应
        fan_effect = -self.fan_parameter * math.log(len(chunk) - 1)
        
        # 计算最近激活效应
        recency_effect = 0
        for access_time in chunk.get("access_times", []):
            time_since_access = current_time - access_time
            recency_effect += math.log(time_since_access / self.latency_factor)
        
        # 总激活值
        activation = self.base_level_activation + base_activation + fan_effect + recency_effect
        
        self.activation_values[chunk_id] = activation
        return activation
    
    def _chunk_matches_request(self, chunk, request):
        """检查组块是否匹配请求"""
        # 简单实现：检查请求中的所有键值对是否在组块中
        for key, value in request.items():
            if key not in chunk or chunk[key] != value:
                return False
        
        return True
    
    def _update_access_history(self, chunk_id):
        """更新访问历史"""
        chunk = self.chunks[chunk_id]
        current_time = time.time()
        
        # 更新访问计数
        chunk["access_count"] += 1
        
        # 更新最后访问时间
        chunk["last_access_time"] = current_time
        
        # 添加到访问时间列表
        if "access_times" not in chunk:
            chunk["access_times"] = []
        
        chunk["access_times"].append(current_time)
        
        # 限制访问时间列表长度
        if len(chunk["access_times"]) > 100:
            chunk["access_times"] = chunk["access_times"][-100:]
        
        # 重新计算激活值
        self._calculate_activation(chunk_id)

class ProceduralMemory:
    """程序性记忆实现"""
    
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.productions = {}
        self.production_utilities = {}
        self.production_counts = {}
        
        # 参数
        self.utility_learning_rate = self.parameters.get("production_utility_learning_rate", 0.2)
    
    def add_production(self, production):
        """添加产生式规则"""
        production_id = str(uuid.uuid4())
        
        # 存储产生式
        self.productions[production_id] = production
        
        # 初始化效用值
        self.production_utilities[production["name"]] = production.get("base_utility", 0)
        
        # 初始化计数
        self.production_counts[production["name"]] = {
            "fired": 0,
            "success": 0
        }
        
        return production_id
    
    def get_utility(self, production_name):
        """获取产生式效用"""
        return self.production_utilities.get(production_name, 0)
    
    def set_utility(self, production_name, utility):
        """设置产生式效用"""
        self.production_utilities[production_name] = utility
    
    def update_utility(self, production_name, reward):
        """更新产生式效用"""
        current_utility = self.production_utilities.get(production_name, 0)
        new_utility = current_utility + self.utility_learning_rate * (reward - current_utility)
        self.production_utilities[production_name] = new_utility
        
        # 更新计数
        if production_name in self.production_counts:
            self.production_counts[production_name]["success"] += 1
    
    def increment_fired_count(self, production_name):
        """增加产生式触发计数"""
        if production_name in self.production_counts:
            self.production_counts[production_name]["fired"] += 1
    
    def get_utility_statistics(self):
        """获取效用统计"""
        stats = {}
        
        for production_name, utility in self.production_utilities.items():
            if production_name in self.production_counts:
                counts = self.production_counts[production_name]
                stats[production_name] = {
                    "utility": utility,
                    "fired": counts["fired"],
                    "success": counts["success"],
                    "success_rate": counts["success"] / max(1, counts["fired"])
                }
        
        return stats

class ProductionSystem:
    """产生式系统实现"""
    
    def __init__(self):
        self.fired_productions = []
        self.fired_count = 0
    
    def match_productions(self, buffers):
        """匹配产生式规则"""
        matched_productions = []
        
        # 这里需要访问程序性记忆中的产生式规则
        # 简化实现：假设有一个产生式规则列表
        productions = self._get_productions()
        
        for production in productions:
            if self._production_matches_buffers(production, buffers):
                matched_productions.append(production)
        
        return matched_productions
    
    def fire_production(self, production):
        """触发产生式规则"""
        self.fired_productions.append({
            "production": production,
            "time": time.time()
        })
        self.fired_count += 1
    
    def _get_productions(self):
        """获取产生式规则列表"""
        # 简化实现：返回一个空列表
        # 实际实现需要从程序性记忆中获取
        return []
    
    def _production_matches_buffers(self, production, buffers):
        """检查产生式是否匹配缓冲区状态"""
        # 检查产生式的条件部分
        for condition in production.get("conditions", []):
            if not self._condition_matches_buffers(condition, buffers):
                return False
        
        return True
    
    def _condition_matches_buffers(self, condition, buffers):
        """检查条件是否匹配缓冲区状态"""
        # 简化实现：检查条件中的变量绑定
        # 实际实现需要更复杂的条件匹配逻辑
        buffer_name = condition.get("buffer")
        
        if buffer_name not in buffers:
            return False
        
        buffer_content = buffers[buffer_name].get_content()
        
        # 检查条件是否与缓冲区内容匹配
        for slot, value in condition.items():
            if slot != "buffer" and buffer_content.get(slot) != value:
                return False
        
        return True
```

### 3. 模块系统核心实现
```python
class Buffer:
    """缓冲区实现"""
    
    def __init__(self, name):
        self.name = name
        self.content = {}
        self.state = "empty"  # empty, busy, full, error
        self.last_update_time = 0
    
    def set_content(self, content):
        """设置缓冲区内容"""
        self.content = content
        self.state = "full"
        self.last_update_time = time.time()
    
    def get_content(self):
        """获取缓冲区内容"""
        return self.content.copy()
    
    def clear(self):
        """清空缓冲区"""
        self.content = {}
        self.state = "empty"
        self.last_update_time = time.time()
    
    def modify(self, modifications):
        """修改缓冲区内容"""
        for slot, value in modifications.items():
            if value is None:
                # 删除槽
                if slot in self.content:
                    del self.content[slot]
            else:
                # 设置槽值
                self.content[slot] = value
        
        self.state = "full"
        self.last_update_time = time.time()
    
    def is_busy(self):
        """检查缓冲区是否忙碌"""
        return self.state == "busy"
    
    def is_empty(self):
        """检查缓冲区是否为空"""
        return self.state == "empty" or not self.content
    
    def is_full(self):
        """检查缓冲区是否已满"""
        return self.state == "full" and self.content

class VisualModule:
    """视觉模块实现"""
    
    def __init__(self, buffer, parameters):
        self.buffer = buffer
        self.parameters = parameters
        self.visual_objects = []
        self.attended_object = None
        self.attention_shift_time = 0
        self.state = "idle"
        
        # 参数
        self.attention_delay = parameters.get("visual_attention_delay", 0.085)
    
    def add_input(self, input_data):
        """添加视觉输入"""
        # 将输入数据转换为视觉对象
        visual_object = {
            "type": input_data.get("type"),
            "state": input_data.get("state"),
            "location": input_data.get("location"),
            "color": input_data.get("color"),
            "size": input_data.get("size"),
            "id": str(uuid.uuid4())
        }
        
        # 添加到视觉对象列表
        self.visual_objects.append(visual_object)
        
        # 如果当前没有注意对象，自动注意第一个对象
        if not self.attended_object:
            self.set_attention(visual_object["id"])
    
    def set_attention(self, object_id):
        """设置视觉注意"""
        # 查找对象
        for obj in self.visual_objects:
            if obj["id"] == object_id:
                self.attended_object = obj
                self.attention_shift_time = time.time()
                self.state = "attending"
                
                # 设置缓冲区内容
                self.buffer.set_content(obj)
                
                # 计划注意完成时间
                self.attention_complete_time = time.time() + self.attention_delay
                return True
        
        return False
    
    def update(self, current_time):
        """更新模块状态"""
        # 检查注意是否完成
        if self.state == "attending" and current_time >= self.attention_complete_time:
            self.state = "attended"
            self.buffer.state = "full"
    
    def get_state(self):
        """获取模块状态"""
        return {
            "state": self.state,
            "attended_object": self.attended_object,
            "visual_objects_count": len(self.visual_objects),
            "attention_shift_time": self.attention_shift_time
        }
    
    def process_request(self, request):
        """处理请求"""
        request_type = request.get("type")
        
        if request_type == "attend":
            object_id = request.get("object_id")
            if object_id:
                return self.set_attention(object_id)
        
        return False

class ManualModule:
    """手动模块实现"""
    
    def __init__(self, buffer, parameters):
        self.buffer = buffer
        self.parameters = parameters
        self.current_action = None
        self.action_start_time = 0
        self.state = "idle"
        
        # 参数
        self.execution_delay = parameters.get("motor_execution_delay", 0.1)
        
        # 定义可用动作
        self.actions = {
            "pick_up": self._execute_pick_up,
            "put_down": self._execute_put_down,
            "point": self._execute_point,
            "grasp": self._execute_grasp
        }
    
    def execute_action(self, action_name, parameters=None):
        """执行动作"""
        if action_name not in self.actions:
            return False
        
        if self.state != "idle":
            return False
        
        # 设置当前动作
        self.current_action = {
            "name": action_name,
            "parameters": parameters or {}
        }
        
        # 设置状态
        self.state = "preparing"
        self.buffer.state = "busy"
        
        # 计划动作完成时间
        self.action_complete_time = time.time() + self.execution_delay
        
        return True
    
    def update(self, current_time):
        """更新模块状态"""
        if self.state == "preparing" and current_time >= self.action_complete_time:
            # 执行动作
            if self.current_action and self.current_action["name"] in self.actions:
                self.actions[self.current_action["name"]](self.current_action["parameters"])
            
            # 更新状态
            self.state = "idle"
            self.buffer.state = "full"
            
            # 设置缓冲区内容
            self.buffer.set_content({
                "action": self.current_action["name"],
                "status": "completed",
                "time": current_time
            })
            
            # 清除当前动作
            self.current_action = None
    
    def get_state(self):
        """获取模块状态"""
        return {
            "state": self.state,
            "current_action": self.current_action,
            "action_start_time": self.action_start_time
        }
    
    def _execute_pick_up(self, parameters):
        """执行拾取动作"""
        # 实现拾取动作逻辑
        target = parameters.get("target")
        print(f"执行拾取动作: {target}")
    
    def _execute_put_down(self, parameters):
        """执行放下动作"""
        # 实现放下动作逻辑
        target = parameters.get("target")
        print(f"执行放下动作: {target}")
    
    def _execute_point(self, parameters):
        """执行指向动作"""
        # 实现指向动作逻辑
        target = parameters.get("target")
        print(f"执行指向动作: {target}")
    
    def _execute_grasp(self, parameters):
        """执行抓取动作"""
        # 实现抓取动作逻辑
        target = parameters.get("target")
        print(f"执行抓取动作: {target}")

class Scheduler:
    """调度器实现"""
    
    def __init__(self):
        self.current_time = 0.0
        self.events = []
    
    def advance_time(self, delta=0.05):
        """推进时间"""
        self.current_time += delta
    
    def schedule_event(self, event_time, event_type, event_data):
        """调度事件"""
        self.events.append({
            "time": event_time,
            "type": event_type,
            "data": event_data
        })
        
        # 按时间排序
        self.events.sort(key=lambda e: e["time"])
    
    def get_next_event(self):
        """获取下一个事件"""
        if not self.events:
            return None
        
        # 检查是否有事件到期
        if self.events[0]["time"] <= self.current_time:
            return self.events.pop(0)
        
        return None
    
    def get_pending_events(self):
        """获取待处理事件"""
        return [event for event in self.events if event["time"] <= self.current_time]
```

## 性能优化要点

### 1. 计算优化
- **产生式匹配优化**: RETE网络、条件索引、并行匹配
- **激活计算优化**: 缓存激活值、增量更新、近似计算
- **模块更新优化**: 事件驱动更新、状态变化检测、选择性更新

### 2. 内存优化
- **记忆存储优化**: 组块压缩、索引结构、分层存储
- **缓冲区管理**: 按需分配、自动清理、共享缓冲区
- **事件系统优化**: 事件池、事件合并、事件过滤

### 3. 时间管理优化
- **时间推进策略**: 自适应步长、事件驱动、混合调度
- **延迟计算**: 延迟缓存、预测计算、并行处理
- **事件调度**: 优先级队列、批量处理、延迟合并

## 集成注意事项

### 1. 设备兼容性处理
```python
class DeviceAwareACTRAgent(ACTRAgent):
    """设备感知的ACT-R智能体实现"""
    
    def __init__(self, name, model_file=None, parameters=None, device="auto"):
        self.device = self._determine_device(device)
        parameters = parameters or {}
        
        # 根据设备类型调整参数
        if self.device == "gpu":
            parameters["visual_attention_delay"] = 0.05  # GPU加速，延迟更短
            parameters["motor_execution_delay"] = 0.05
        else:
            parameters["visual_attention_delay"] = 0.085  # CPU默认延迟
            parameters["motor_execution_delay"] = 0.1
        
        super().__init__(name, model_file, parameters)
    
    def _determine_device(self, device):
        """确定最佳设备"""
        if device == "auto":
            # 检查是否有可用的GPU
            try:
                import torch
                if torch.cuda.is_available():
                    return "gpu"
            except ImportError:
                pass
            
            return "cpu"
        
        return device
    
    def _initialize_modules(self):
        """初始化模块"""
        super()._initialize_modules()
        
        # 根据设备类型优化模块
        if self.device == "gpu":
            self._optimize_modules_for_gpu()
        else:
            self._optimize_modules_for_cpu()
    
    def _optimize_modules_for_gpu(self):
        """为GPU优化模块"""
        # 使用GPU加速的模块实现
        self.modules["visual"] = GPUVisualModule(self.buffers["visual"], self.parameters)
        self.modules["declarative"] = GPUDeclarativeModule(
            self.declarative_memory, 
            self.buffers["retrieval"], 
            self.parameters
        )
    
    def _optimize_modules_for_cpu(self):
        """为CPU优化模块"""
        # 使用CPU优化的模块实现
        self.modules["visual"] = OptimizedVisualModule(self.buffers["visual"], self.parameters)
        self.modules["declarative"] = OptimizedDeclarativeModule(
            self.declarative_memory, 
            self.buffers["retrieval"], 
            self.parameters
        )
```

### 2. 内存管理优化
```python
class MemoryOptimizedACTRAgent(ACTRAgent):
    """内存优化的ACT-R智能体实现"""
    
    def __init__(self, name, model_file=None, parameters=None, memory_limit="1GB"):
        self.memory_limit = self._parse_memory_limit(memory_limit)
        self.memory_monitor = MemoryMonitor()
        parameters = parameters or {}
        
        # 设置内存管理参数
        parameters["max_chunks"] = 10000  # 最大组块数
        parameters["chunk_gc_threshold"] = 0.8  # 组块垃圾回收阈值
        
        super().__init__(name, model_file, parameters)
    
    def run_cycle(self):
        """运行认知循环，带内存管理"""
        # 检查内存使用情况
        memory_usage = self.memory_monitor.get_current_usage()
        
        if memory_usage > self.memory_limit * 0.8:  # 80%阈值
            self._optimize_memory_usage()
        
        # 执行认知循环
        super().run_cycle()
    
    def _optimize_memory_usage(self):
        """优化内存使用"""
        # 执行陈述性记忆垃圾回收
        self.declarative_memory.garbage_collect()
        
        # 压缩产生式规则
        self.procedural_memory.compress_productions()
        
        # 清理事件历史
        self.scheduler.cleanup_events()
    
    def _parse_memory_limit(self, limit_str):
        """解析内存限制"""
        if limit_str.endswith("GB"):
            return int(limit_str[:-2]) * 1024 * 1024 * 1024
        elif limit_str.endswith("MB"):
            return int(limit_str[:-2]) * 1024 * 1024
        else:
            return int(limit_str)
```

### 3. 分布式处理配置
```python
class DistributedACTRAgent(ACTRAgent):
    """分布式ACT-R智能体实现"""
    
    def __init__(self, name, model_file=None, parameters=None, worker_nodes=None):
        self.worker_nodes = worker_nodes or []
        self.task_distributor = TaskDistributor()
        parameters = parameters or {}
        
        # 设置分布式参数
        parameters["distributed_matching"] = True
        parameters["parallel_retrieval"] = True
        
        super().__init__(name, model_file, parameters)
    
    def run_cycle(self):
        """分布式认知循环"""
        # 分布式产生式匹配
        matched_productions = self._distributed_production_matching()
        
        # 选择产生式规则
        selected_production = self._select_production(matched_productions)
        
        if selected_production:
            # 执行产生式规则
            self._execute_production(selected_production)
            
            # 更新产生式效用
            self._update_production_utility(selected_production)
        
        # 推进时间
        self.scheduler.advance_time()
    
    def _distributed_production_matching(self):
        """分布式产生式匹配"""
        # 创建匹配任务
        matching_tasks = self._create_matching_tasks()
        
        # 分发任务
        distributed_results = self.task_distributor.distribute_tasks(
            matching_tasks, 
            self.worker_nodes
        )
        
        # 收集匹配结果
        matched_productions = self._collect_matching_results(distributed_results)
        
        return matched_productions
    
    def _create_matching_tasks(self):
        """创建匹配任务"""
        tasks = []
        
        # 分割产生式规则
        productions = list(self.procedural_memory.productions.items())
        productions_per_task = len(productions) // len(self.worker_nodes)
        
        for i in range(0, len(productions), productions_per_task):
            task_productions = dict(productions[i:i + productions_per_task])
            tasks.append({
                "type": "production_matching",
                "productions": task_productions,
                "buffers": {name: buffer.get_content() for name, buffer in self.buffers.items()}
            })
        
        return tasks
    
    def _collect_matching_results(self, distributed_results):
        """收集匹配结果"""
        matched_productions = []
        
        for result in distributed_results:
            matched_productions.extend(result["matched_productions"])
        
        return matched_productions
```

## 测试用例

### 1. 基本功能测试
```python
import unittest
from actr import ACTRAgent

class TestACTRAgent(unittest.TestCase):
    """ACT-R智能体基本功能测试"""
    
    def setUp(self):
        """测试初始化"""
        self.agent = ACTRAgent(
            name="test_agent",
            parameters={
                "visual_attention_delay": 0.05,
                "motor_execution_delay": 0.05,
                "declarative_memory_activation_threshold": -0.3
            }
        )
        
        # 添加测试产生式规则
        self.test_production = {
            "name": "test_production",
            "conditions": [
                "?visual-buffer> isa visual-object",
                "?visual-buffer> state test"
            ],
            "actions": [
                "!output!> type test_action",
                "!output!> value test_result"
            ],
            "base_utility": 10
        }
        
        self.agent.add_production(self.test_production)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.agent.name, "test_agent")
        self.assertEqual(
            self.agent.get_parameter("visual_attention_delay"), 
            0.05
        )
        self.assertEqual(
            self.agent.get_parameter("motor_execution_delay"), 
            0.05
        )
    
    def test_perceptual_input(self):
        """测试感知输入"""
        # 添加视觉输入
        visual_input = {
            "type": "visual",
            "state": "test",
            "location": "center"
        }
        
        self.agent.add_perceptual_input(visual_input)
        
        # 验证视觉模块状态
        visual_state = self.agent.modules["visual"].get_state()
        self.assertEqual(visual_state["state"], "attending")
    
    def test_cognitive_cycle(self):
        """测试认知循环"""
        # 添加视觉输入
        visual_input = {
            "type": "visual",
            "state": "test",
            "location": "center"
        }
        
        self.agent.add_perceptual_input(visual_input)
        
        # 运行认知循环
        self.agent.run_cycle()
        
        # 验证缓冲区状态
        visual_buffer = self.agent.buffers["visual"].get_content()
        self.assertEqual(visual_buffer["state"], "test")
    
    def test_declarative_memory(self):
        """测试陈述性记忆"""
        # 添加组块
        chunk = {
            "isa": "test-chunk",
            "slot1": "value1",
            "slot2": "value2"
        }
        
        chunk_id = self.agent.add_declarative_memory(chunk)
        self.assertIsNotNone(chunk_id)
        
        # 检索组块
        request = {
            "isa": "test-chunk",
            "slot1": "value1"
        }
        
        retrieved_chunks = self.agent.retrieve_declarative_memory(request)
        self.assertGreater(len(retrieved_chunks), 0)
        self.assertEqual(retrieved_chunks[0]["slot1"], "value1")
    
    def test_production_system(self):
        """测试产生式系统"""
        # 添加视觉输入
        visual_input = {
            "type": "visual",
            "state": "test",
            "location": "center"
        }
        
        self.agent.add_perceptual_input(visual_input)
        
        # 运行认知循环
        self.agent.run_cycle()
        
        # 验证产生式统计
        stats = self.agent.get_production_statistics()
        self.assertGreater(stats["fired_productions"], 0)

if __name__ == "__main__":
    unittest.main()
```

### 2. 记忆系统测试
```python
class TestMemorySystem(unittest.TestCase):
    """记忆系统测试"""
    
    def setUp(self):
        """测试初始化"""
        from actr.memory import DeclarativeMemory, ProceduralMemory
        
        self.declarative_memory = DeclarativeMemory()
        self.procedural_memory = ProceduralMemory()
    
    def test_declarative_memory(self):
        """测试陈述性记忆"""
        # 添加组块
        chunk = {
            "isa": "test-chunk",
            "slot1": "value1",
            "slot2": "value2"
        }
        
        chunk_id = self.declarative_memory.add_chunk(chunk)
        self.assertIsNotNone(chunk_id)
        
        # 验证组块存储
        self.assertIn(chunk_id, self.declarative_memory.chunks)
        self.assertEqual(
            self.declarative_memory.chunks[chunk_id]["slot1"], 
            "value1"
        )
        
        # 检索组块
        request = {
            "isa": "test-chunk",
            "slot1": "value1"
        }
        
        retrieved_chunks = self.declarative_memory.retrieve(request)
        self.assertGreater(len(retrieved_chunks), 0)
        self.assertEqual(retrieved_chunks[0]["slot1"], "value1")
    
    def test_activation_calculation(self):
        """测试激活计算"""
        # 添加组块
        chunk = {
            "isa": "test-chunk",
            "slot1": "value1"
        }
        
        chunk_id = self.declarative_memory.add_chunk(chunk)
        
        # 计算激活值
        activation = self.declarative_memory._calculate_activation(chunk_id)
        self.assertIsInstance(activation, float)
        
        # 验证激活值存储
        self.assertIn(chunk_id, self.declarative_memory.activation_values)
        self.assertEqual(
            self.declarative_memory.activation_values[chunk_id], 
            activation
        )
    
    def test_procedural_memory(self):
        """测试程序性记忆"""
        # 添加产生式规则
        production = {
            "name": "test_production",
            "conditions": ["?buffer> slot value"],
            "actions": ["!output!> type test"],
            "base_utility": 10
        }
        
        production_id = self.procedural_memory.add_production(production)
        self.assertIsNotNone(production_id)
        
        # 验证产生式存储
        self.assertIn(production_id, self.procedural_memory.productions)
        self.assertEqual(
            self.procedural_memory.productions[production_id]["name"], 
            "test_production"
        )
        
        # 测试效用管理
        utility = self.procedural_memory.get_utility("test_production")
        self.assertEqual(utility, 10)
        
        # 更新效用
        self.procedural_memory.update_utility("test_production", 15)
        new_utility = self.procedural_memory.get_utility("test_production")
        self.assertGreater(new_utility, utility)

if __name__ == "__main__":
    unittest.main()
```

### 3. 性能基准测试
```python
import time
import psutil
import os

class TestACTRPerformance(unittest.TestCase):
    """ACT-R性能测试"""
    
    def setUp(self):
        """测试初始化"""
        self.agent = ACTRAgent(
            name="performance_test_agent",
            parameters={
                "visual_attention_delay": 0.01,  # 更短的延迟用于测试
                "motor_execution_delay": 0.01
            }
        )
        
        # 添加大量测试数据
        self._setup_test_data()
    
    def _setup_test_data(self):
        """设置测试数据"""
        # 添加大量陈述性记忆
        for i in range(1000):
            chunk = {
                "isa": "test-chunk",
                "id": f"chunk_{i}",
                "value": f"value_{i}"
            }
            self.agent.add_declarative_memory(chunk)
        
        # 添加大量产生式规则
        for i in range(100):
            production = {
                "name": f"test_production_{i}",
                "conditions": [f"?visual-buffer> id chunk_{i % 100}"],
                "actions": ["!output!> type test_action"],
                "base_utility": i % 10
            }
            self.agent.add_production(production)
    
    def test_cognitive_cycle_performance(self):
        """测试认知循环性能"""
        # 添加视觉输入
        visual_input = {
            "type": "visual",
            "id": "chunk_50",
            "location": "center"
        }
        
        self.agent.add_perceptual_input(visual_input)
        
        # 测量认知循环时间
        start_time = time.time()
        
        for _ in range(100):  # 执行100次认知循环
            self.agent.run_cycle()
        
        end_time = time.time()
        cycle_time = end_time - start_time
        
        # 验证认知循环时间在合理范围内
        self.assertLess(cycle_time, 5.0)  # 假设100次循环在5秒内完成
        
        print(f"认知循环时间: {cycle_time:.2f}秒 (100次)")
        print(f"平均认知循环时间: {cycle_time/100:.2f}秒/次")
    
    def test_memory_retrieval_performance(self):
        """测试记忆检索性能"""
        # 创建检索请求
        request = {
            "isa": "test-chunk",
            "value": "value_500"
        }
        
        # 测量检索时间
        start_time = time.time()
        
        for _ in range(100):  # 执行100次检索
            retrieved_chunks = self.agent.retrieve_declarative_memory(request)
        
        end_time = time.time()
        retrieval_time = end_time - start_time
        
        # 验证检索时间在合理范围内
        self.assertLess(retrieval_time, 2.0)  # 假设100次检索在2秒内完成
        
        print(f"记忆检索时间: {retrieval_time:.2f}秒 (100次)")
        print(f"平均检索时间: {retrieval_time/100:.2f}秒/次")
    
    def test_memory_usage(self):
        """测试内存使用"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量认知处理
        for i in range(50):
            # 添加视觉输入
            visual_input = {
                "type": "visual",
                "id": f"chunk_{i % 100}",
                "location": "center"
            }
            
            self.agent.add_perceptual_input(visual_input)
            
            # 运行认知循环
            self.agent.run_cycle()
            
            # 执行记忆检索
            request = {
                "isa": "test-chunk",
                "id": f"chunk_{i % 100}"
            }
            
            self.agent.retrieve_declarative_memory(request)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 验证内存增长在合理范围内
        self.assertLess(memory_increase, 200)  # 假设内存增长不超过200MB
        
        print(f"内存增长: {memory_increase:.2f}MB")

if __name__ == "__main__":
    unittest.main()
```

## 总结

ACT-R作为认知架构，为真实婴儿AI管家系统提供了模拟人类认知过程的强大框架。通过结合符号处理和亚符号处理，ACT-R能够实现感知、注意、记忆、决策和行动等认知功能的模拟，为系统提供更加类人的认知处理能力。

### 关键集成点
1. **认知处理核心**: 与婴儿AI管家系统的大脑核心模块集成，提供认知处理能力
2. **记忆系统**: 与系统的记忆存储模块集成，提供多层次的记忆管理
3. **感知运动系统**: 与系统的感知和执行模块集成，提供感知和行动能力

### 性能要求
1. **认知循环时间**: 认知处理周期应小于100毫秒
2. **记忆检索时间**: 记忆检索响应时间应小于50毫秒
3. **模块更新时间**: 各模块状态更新时间应小于10毫秒

### 扩展功能
1. **多模态感知**: 支持视觉、听觉、触觉等多模态感知处理
2. **情感认知**: 集成情感模型，实现情感理解和情感决策
3. **社会认知**: 支持社会情境理解和社交互动

ACT-R的认知架构能力使其成为婴儿AI管家系统的核心认知引擎，能够实现系统的类人认知处理，为用户提供更加自然和智能的交互体验。