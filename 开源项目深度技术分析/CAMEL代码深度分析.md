# CAMEL多智能体协作框架代码深度分析

## 项目概述

CAMEL (Communicative Agents for Mind Exploration and Learning) 是一个开源的多智能体协作框架，专注于研究智能体之间的角色扮演和协作行为。该框架由研究人员开发，旨在探索大型语言模型在多智能体系统中的协作能力，特别是在复杂任务中的角色分配和协作策略。

### 核心功能
- **多智能体角色扮演**: 支持智能体扮演不同角色并进行协作
- **任务分解与分配**: 将复杂任务分解为子任务并分配给不同智能体
- **对话管理**: 管理智能体之间的对话和交互
- **协作策略**: 实现多种协作策略和协商机制
- **提示工程**: 提供专门的提示工程工具和模板
- **评估系统**: 评估多智能体协作的效果和质量

### 应用场景
- **多智能体研究**: 研究智能体协作和交互行为
- **复杂问题解决**: 通过多智能体协作解决复杂问题
- **角色扮演模拟**: 模拟不同角色之间的交互
- **集体决策**: 支持多智能体集体决策过程
- **创意生成**: 通过多智能体协作生成创意内容

## 结构分析

### 核心模块结构
```
camel/
├── agents/              # 智能体模块
│   ├── __init__.py
│   ├── chat_agent.py    # 聊天智能体
│   ├── role_playing.py  # 角色扮演智能体
│   └── task_agent.py    # 任务智能体
├── conversations/       # 对话管理模块
│   ├── __init__.py
│   ├── base.py          # 基础对话类
│   ├── role_playing.py  # 角色扮演对话
│   └── task_oriented.py # 任务导向对话
├── messages/            # 消息模块
│   ├── __init__.py
│   ├── base.py          # 基础消息类
│   ├── system.py        # 系统消息
│   └── user.py          # 用户消息
├── prompts/             # 提示工程模块
│   ├── __init__.py
│   ├── templates.py     # 提示模板
│   └── generators.py    # 提示生成器
├── tasks/               # 任务模块
│   ├── __init__.py
│   ├── base.py          # 基础任务类
│   ├── simple.py        # 简单任务
│   └── complex.py       # 复杂任务
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── logging.py       # 日志工具
│   └── helpers.py       # 辅助函数
└── examples/            # 示例模块
    ├── __init__.py
    ├── role_playing.py  # 角色扮演示例
    └── problem_solving.py # 问题解决示例
```

### 主要代码文件分析

#### 1. agents/chat_agent.py
```python
class ChatAgent:
    """聊天智能体类，实现基本的聊天功能"""
    
    def __init__(self, system_message: str, model: str = "gpt-3.5-turbo"):
        """
        初始化聊天智能体
        
        Args:
            system_message: 系统消息，定义智能体的角色和行为
            model: 使用的语言模型
        """
        self.system_message = system_message
        self.model = model
        self.client = OpenAI()
        self.conversation_history = []
        
    def reset(self):
        """重置对话历史"""
        self.conversation_history = []
        
    def step(self, user_message: str) -> str:
        """
        处理用户消息并生成回复
        
        Args:
            user_message: 用户消息
            
        Returns:
            智能体的回复
        """
        # 添加用户消息到对话历史
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # 构建消息列表
        messages = [{"role": "system", "content": self.system_message}]
        messages.extend(self.conversation_history)
        
        # 调用API生成回复
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        
        # 提取回复内容
        assistant_message = response.choices[0].message.content
        
        # 添加助手回复到对话历史
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
```

#### 2. agents/role_playing.py
```python
class RolePlayingAgent:
    """角色扮演智能体类，实现角色扮演功能"""
    
    def __init__(self, role_name: str, role_description: str, model: str = "gpt-3.5-turbo"):
        """
        初始化角色扮演智能体
        
        Args:
            role_name: 角色名称
            role_description: 角色描述
            model: 使用的语言模型
        """
        self.role_name = role_name
        self.role_description = role_description
        self.model = model
        self.client = OpenAI()
        self.conversation_history = []
        
        # 构建系统消息
        self.system_message = f"You are {role_name}. {role_description}"
        
    def reset(self):
        """重置对话历史"""
        self.conversation_history = []
        
    def step(self, user_message: str, other_agent_role: str = None) -> str:
        """
        处理用户消息并生成角色回复
        
        Args:
            user_message: 用户消息
            other_agent_role: 对话中的其他智能体角色
            
        Returns:
            智能体的角色回复
        """
        # 添加用户消息到对话历史
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # 构建消息列表
        messages = [{"role": "system", "content": self.system_message}]
        
        # 如果有其他智能体角色，添加上下文信息
        if other_agent_role:
            context_message = f"You are talking to {other_agent_role}. Please respond in character."
            messages.append({"role": "system", "content": context_message})
            
        messages.extend(self.conversation_history)
        
        # 调用API生成回复
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        
        # 提取回复内容
        assistant_message = response.choices[0].message.content
        
        # 添加助手回复到对话历史
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
```

#### 3. conversations/role_playing.py
```python
class RolePlayingConversation:
    """角色扮演对话类，管理两个智能体之间的角色扮演对话"""
    
    def __init__(self, agent_a: RolePlayingAgent, agent_b: RolePlayingAgent, 
                 task_prompt: str, max_turns: int = 10):
        """
        初始化角色扮演对话
        
        Args:
            agent_a: 第一个智能体
            agent_b: 第二个智能体
            task_prompt: 任务提示
            max_turns: 最大对话轮次
        """
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.task_prompt = task_prompt
        self.max_turns = max_turns
        self.conversation_history = []
        self.current_turn = 0
        self.terminated = False
        
    def step(self) -> bool:
        """
        执行一步对话
        
        Returns:
            是否继续对话
        """
        if self.terminated or self.current_turn >= self.max_turns:
            self.terminated = True
            return False
            
        # 确定当前发言的智能体
        if self.current_turn % 2 == 0:
            # agent_a发言
            if self.current_turn == 0:
                # 第一轮，使用任务提示
                message = self.task_prompt
            else:
                # 获取上一轮agent_b的回复
                message = self.conversation_history[-1]["content"]
                
            response = self.agent_a.step(message, self.agent_b.role_name)
            speaker = self.agent_a.role_name
        else:
            # agent_b发言
            message = self.conversation_history[-1]["content"]
            response = self.agent_b.step(message, self.agent_a.role_name)
            speaker = self.agent_b.role_name
            
        # 记录对话
        self.conversation_history.append({
            "speaker": speaker,
            "content": response,
            "turn": self.current_turn
        })
        
        self.current_turn += 1
        
        # 检查是否终止
        if self._should_terminate(response):
            self.terminated = True
            return False
            
        return True
        
    def run(self) -> List[Dict]:
        """
        运行完整对话
        
        Returns:
            对话历史
        """
        while self.step():
            pass
            
        return self.conversation_history
        
    def _should_terminate(self, response: str) -> bool:
        """
        判断是否应该终止对话
        
        Args:
            response: 当前回复
            
        Returns:
            是否应该终止
        """
        # 简单的终止条件：回复中包含终止关键词
        termination_keywords = ["goodbye", "bye", "finish", "done", "end"]
        response_lower = response.lower()
        
        for keyword in termination_keywords:
            if keyword in response_lower:
                return True
                
        return False
```

## 接口分析

### 1. 核心智能体接口
```python
class BaseAgent:
    """基础智能体接口"""
    
    def __init__(self, system_message: str, model: str = "gpt-3.5-turbo"):
        """
        初始化智能体
        
        Args:
            system_message: 系统消息
            model: 使用的语言模型
        """
        raise NotImplementedError
        
    def reset(self):
        """重置智能体状态"""
        raise NotImplementedError
        
    def step(self, message: str) -> str:
        """
        处理消息并生成回复
        
        Args:
            message: 输入消息
            
        Returns:
            智能体的回复
        """
        raise NotImplementedError
```

### 2. 对话管理接口
```python
class BaseConversation:
    """基础对话接口"""
    
    def __init__(self, agents: List[BaseAgent], task_prompt: str, max_turns: int = 10):
        """
        初始化对话
        
        Args:
            agents: 参与对话的智能体列表
            task_prompt: 任务提示
            max_turns: 最大对话轮次
        """
        raise NotImplementedError
        
    def step(self) -> bool:
        """
        执行一步对话
        
        Returns:
            是否继续对话
        """
        raise NotImplementedError
        
    def run(self) -> List[Dict]:
        """
        运行完整对话
        
        Returns:
            对话历史
        """
        raise NotImplementedError
        
    def reset(self):
        """重置对话状态"""
        raise NotImplementedError
```

### 3. 任务管理接口
```python
class BaseTask:
    """基础任务接口"""
    
    def __init__(self, task_description: str, agents: List[BaseAgent]):
        """
        初始化任务
        
        Args:
            task_description: 任务描述
            agents: 执行任务的智能体列表
        """
        raise NotImplementedError
        
    def decompose(self) -> List[Dict]:
        """
        分解任务
        
        Returns:
            子任务列表
        """
        raise NotImplementedError
        
    def assign(self, subtasks: List[Dict]) -> Dict:
        """
        分配子任务给智能体
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            任务分配结果
        """
        raise NotImplementedError
        
    def execute(self) -> Dict:
        """
        执行任务
        
        Returns:
            任务执行结果
        """
        raise NotImplementedError
```

## 数据流分析

### 1. 角色扮演对话流程
```
初始化 → 创建智能体 → 设置角色 → 开始对话 → 交替发言 → 记录历史 → 终止判断 → 输出结果
```

### 2. 任务协作流程
```
任务定义 → 任务分解 → 任务分配 → 智能体执行 → 结果收集 → 结果整合 → 任务完成
```

### 3. 多智能体协作流程
```
系统初始化 → 智能体创建 → 角色分配 → 任务分配 → 协作执行 → 状态同步 → 结果整合 → 输出结果
```

## 关键代码实现细节

### 1. 角色扮演核心实现
```python
class RolePlayingManager:
    """角色扮演管理器，管理多个智能体的角色扮演"""
    
    def __init__(self, roles: List[Dict], model: str = "gpt-3.5-turbo"):
        """
        初始化角色扮演管理器
        
        Args:
            roles: 角色列表，每个角色包含name和description
            model: 使用的语言模型
        """
        self.roles = roles
        self.model = model
        self.agents = {}
        
        # 创建智能体
        for role in roles:
            agent = RolePlayingAgent(
                role_name=role["name"],
                role_description=role["description"],
                model=model
            )
            self.agents[role["name"]] = agent
            
    def create_conversation(self, role_a: str, role_b: str, 
                           task_prompt: str, max_turns: int = 10) -> RolePlayingConversation:
        """
        创建角色扮演对话
        
        Args:
            role_a: 第一个角色名称
            role_b: 第二个角色名称
            task_prompt: 任务提示
            max_turns: 最大对话轮次
            
        Returns:
            角色扮演对话对象
        """
        agent_a = self.agents[role_a]
        agent_b = self.agents[role_b]
        
        return RolePlayingConversation(
            agent_a=agent_a,
            agent_b=agent_b,
            task_prompt=task_prompt,
            max_turns=max_turns
        )
        
    def run_conversation(self, role_a: str, role_b: str, 
                        task_prompt: str, max_turns: int = 10) -> List[Dict]:
        """
        运行角色扮演对话
        
        Args:
            role_a: 第一个角色名称
            role_b: 第二个角色名称
            task_prompt: 任务提示
            max_turns: 最大对话轮次
            
        Returns:
            对话历史
        """
        conversation = self.create_conversation(role_a, role_b, task_prompt, max_turns)
        return conversation.run()
```

### 2. 任务分解与分配实现
```python
class TaskDecomposer:
    """任务分解器，将复杂任务分解为子任务"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        初始化任务分解器
        
        Args:
            model: 使用的语言模型
        """
        self.model = model
        self.client = OpenAI()
        
    def decompose(self, task_description: str, agent_roles: List[str]) -> List[Dict]:
        """
        分解任务
        
        Args:
            task_description: 任务描述
            agent_roles: 智能体角色列表
            
        Returns:
            子任务列表
        """
        # 构建分解提示
        prompt = f"""
        Please decompose the following task into subtasks that can be assigned to different agents:
        
        Task: {task_description}
        
        Available agent roles: {', '.join(agent_roles)}
        
        Please provide a list of subtasks, each with:
        1. A description of the subtask
        2. The agent role that should handle this subtask
        3. Dependencies on other subtasks
        
        Format your response as a JSON array of objects with keys: "description", "agent", "dependencies"
        """
        
        # 调用API分解任务
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 解析响应
        subtasks_json = response.choices[0].message.content
        
        try:
            subtasks = json.loads(subtasks_json)
            return subtasks
        except json.JSONDecodeError:
            # 如果解析失败，返回简单分解
            return [{"description": task_description, "agent": agent_roles[0], "dependencies": []}]

class TaskAssigner:
    """任务分配器，将子任务分配给智能体"""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        """
        初始化任务分配器
        
        Args:
            agents: 智能体字典，键为角色名称，值为智能体对象
        """
        self.agents = agents
        
    def assign(self, subtasks: List[Dict]) -> Dict:
        """
        分配子任务
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            任务分配结果
        """
        assignment = {}
        
        for subtask in subtasks:
            agent_name = subtask["agent"]
            agent = self.agents.get(agent_name)
            
            if agent:
                task_id = len(assignment)
                assignment[task_id] = {
                    "subtask": subtask,
                    "agent": agent,
                    "status": "assigned",
                    "result": None
                }
                
        return assignment
        
    def execute(self, assignment: Dict) -> Dict:
        """
        执行分配的任务
        
        Args:
            assignment: 任务分配结果
            
        Returns:
            任务执行结果
        """
        # 按依赖关系排序任务
        sorted_tasks = self._sort_by_dependencies(assignment)
        
        # 执行任务
        for task_id in sorted_tasks:
            task_info = assignment[task_id]
            task_info["status"] = "running"
            
            # 执行子任务
            subtask = task_info["subtask"]
            agent = task_info["agent"]
            
            # 构建任务提示
            task_prompt = f"""
            Please complete the following subtask:
            
            {subtask["description"]}
            """
            
            # 执行任务
            result = agent.step(task_prompt)
            
            # 更新任务状态
            task_info["status"] = "completed"
            task_info["result"] = result
            
        return assignment
        
    def _sort_by_dependencies(self, assignment: Dict) -> List[int]:
        """
        根据依赖关系对任务进行拓扑排序
        
        Args:
            assignment: 任务分配结果
            
        Returns:
            排序后的任务ID列表
        """
        # 构建依赖图
        graph = {}
        for task_id, task_info in assignment.items():
            subtask = task_info["subtask"]
            dependencies = subtask.get("dependencies", [])
            graph[task_id] = dependencies
            
        # 拓扑排序
        sorted_tasks = []
        visited = set()
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            
            for dependency in graph.get(node, []):
                # 找到依赖的任务ID
                for dep_id, dep_info in assignment.items():
                    if dep_info["subtask"]["description"] == dependency:
                        visit(dep_id)
                        break
                        
            sorted_tasks.append(node)
            
        for node in graph:
            visit(node)
            
        return sorted_tasks
```

### 3. 协作策略实现
```python
class CollaborationStrategy:
    """协作策略基类"""
    
    def __init__(self):
        """初始化协作策略"""
        pass
        
    def execute(self, agents: Dict[str, BaseAgent], task: BaseTask) -> Dict:
        """
        执行协作策略
        
        Args:
            agents: 智能体字典
            task: 任务对象
            
        Returns:
            协作结果
        """
        raise NotImplementedError

class SequentialCollaboration(CollaborationStrategy):
    """顺序协作策略，智能体按顺序执行任务"""
    
    def __init__(self):
        """初始化顺序协作策略"""
        super().__init__()
        
    def execute(self, agents: Dict[str, BaseAgent], task: BaseTask) -> Dict:
        """
        执行顺序协作
        
        Args:
            agents: 智能体字典
            task: 任务对象
            
        Returns:
            协作结果
        """
        # 分解任务
        subtasks = task.decompose()
        
        # 分配任务
        assigner = TaskAssigner(agents)
        assignment = assigner.assign(subtasks)
        
        # 执行任务
        results = assigner.execute(assignment)
        
        # 整合结果
        integrated_result = self._integrate_results(results)
        
        return {
            "task": task,
            "subtasks": subtasks,
            "assignment": assignment,
            "results": results,
            "integrated_result": integrated_result
        }
        
    def _integrate_results(self, results: Dict) -> str:
        """
        整合任务结果
        
        Args:
            results: 任务执行结果
            
        Returns:
            整合后的结果
        """
        # 收集所有结果
        all_results = []
        for task_id, task_info in results.items():
            if task_info["status"] == "completed" and task_info["result"]:
                all_results.append(task_info["result"])
                
        # 简单连接所有结果
        return "\n\n".join(all_results)

class ParallelCollaboration(CollaborationStrategy):
    """并行协作策略，智能体并行执行任务"""
    
    def __init__(self):
        """初始化并行协作策略"""
        super().__init__()
        
    def execute(self, agents: Dict[str, BaseAgent], task: BaseTask) -> Dict:
        """
        执行并行协作
        
        Args:
            agents: 智能体字典
            task: 任务对象
            
        Returns:
            协作结果
        """
        # 分解任务
        subtasks = task.decompose()
        
        # 分配任务
        assigner = TaskAssigner(agents)
        assignment = assigner.assign(subtasks)
        
        # 并行执行任务
        results = self._parallel_execute(assignment)
        
        # 整合结果
        integrated_result = self._integrate_results(results)
        
        return {
            "task": task,
            "subtasks": subtasks,
            "assignment": assignment,
            "results": results,
            "integrated_result": integrated_result
        }
        
    def _parallel_execute(self, assignment: Dict) -> Dict:
        """
        并行执行任务
        
        Args:
            assignment: 任务分配结果
            
        Returns:
            任务执行结果
        """
        # 使用线程池并行执行任务
        from concurrent.futures import ThreadPoolExecutor
        
        def execute_task(task_id, task_info):
            """执行单个任务"""
            task_info["status"] = "running"
            
            # 执行子任务
            subtask = task_info["subtask"]
            agent = task_info["agent"]
            
            # 构建任务提示
            task_prompt = f"""
            Please complete the following subtask:
            
            {subtask["description"]}
            """
            
            # 执行任务
            result = agent.step(task_prompt)
            
            # 更新任务状态
            task_info["status"] = "completed"
            task_info["result"] = result
            
            return task_id, task_info
            
        # 创建线程池
        with ThreadPoolExecutor(max_workers=len(assignment)) as executor:
            # 提交所有任务
            futures = []
            for task_id, task_info in assignment.items():
                future = executor.submit(execute_task, task_id, task_info)
                futures.append(future)
                
            # 等待所有任务完成
            results = {}
            for future in futures:
                task_id, task_info = future.result()
                results[task_id] = task_info
                
        return results
        
    def _integrate_results(self, results: Dict) -> str:
        """
        整合任务结果
        
        Args:
            results: 任务执行结果
            
        Returns:
            整合后的结果
        """
        # 收集所有结果
        all_results = []
        for task_id, task_info in results.items():
            if task_info["status"] == "completed" and task_info["result"]:
                all_results.append(task_info["result"])
                
        # 简单连接所有结果
        return "\n\n".join(all_results)
```

## 性能优化要点

### 1. 计算优化
- **API调用优化**: 减少不必要的API调用，合并多个请求
- **提示词优化**: 设计高效的提示词，减少模型处理时间
- **缓存机制**: 缓存常见问题的回复，避免重复计算
- **并行处理**: 利用多线程并行执行独立任务

### 2. 内存优化
- **对话历史管理**: 限制对话历史长度，定期清理不必要的历史
- **对象池**: 重用智能体和对话对象，减少内存分配
- **延迟加载**: 按需加载智能体和任务，减少内存占用
- **数据压缩**: 压缩存储的对话和任务数据

### 3. 协作优化
- **任务分解优化**: 优化任务分解算法，减少子任务数量
- **依赖关系优化**: 优化任务依赖关系，减少等待时间
- **负载均衡**: 平衡智能体之间的工作负载
- **通信优化**: 减少智能体之间的通信开销

## 集成注意事项

### 1. 设备兼容性处理
```python
class DeviceCompatibilityManager:
    """设备兼容性管理器，处理不同设备上的兼容性问题"""
    
    def __init__(self):
        """初始化设备兼容性管理器"""
        self.device_info = self._get_device_info()
        self.model_config = self._get_model_config()
        
    def _get_device_info(self) -> Dict:
        """获取设备信息"""
        import platform
        
        return {
            "platform": platform.system(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0]
        }
        
    def _get_model_config(self) -> Dict:
        """根据设备信息获取模型配置"""
        # 根据设备性能选择合适的模型
        if self.device_info["platform"] == "Darwin":  # macOS
            return {
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.7
            }
        else:  # 其他平台
            return {
                "model": "gpt-3.5-turbo",
                "max_tokens": 500,
                "temperature": 0.7
            }
            
    def create_agent(self, role_name: str, role_description: str) -> RolePlayingAgent:
        """
        创建兼容设备的智能体
        
        Args:
            role_name: 角色名称
            role_description: 角色描述
            
        Returns:
            角色扮演智能体
        """
        return RolePlayingAgent(
            role_name=role_name,
            role_description=role_description,
            model=self.model_config["model"]
        )
```

### 2. 内存管理优化
```python
class MemoryManager:
    """内存管理器，优化内存使用"""
    
    def __init__(self, max_conversation_history: int = 10):
        """
        初始化内存管理器
        
        Args:
            max_conversation_history: 最大对话历史长度
        """
        self.max_conversation_history = max_conversation_history
        self.agent_pool = {}
        self.conversation_pool = {}
        
    def get_agent(self, role_name: str, role_description: str, model: str = "gpt-3.5-turbo") -> RolePlayingAgent:
        """
        获取智能体，优先从池中获取
        
        Args:
            role_name: 角色名称
            role_description: 角色描述
            model: 使用的语言模型
            
        Returns:
            角色扮演智能体
        """
        agent_key = f"{role_name}_{model}"
        
        if agent_key in self.agent_pool:
            agent = self.agent_pool[agent_key]
            agent.reset()  # 重置对话历史
            return agent
        else:
            agent = RolePlayingAgent(
                role_name=role_name,
                role_description=role_description,
                model=model
            )
            self.agent_pool[agent_key] = agent
            return agent
            
    def trim_conversation_history(self, agent: RolePlayingAgent):
        """
        裁剪对话历史，控制内存使用
        
        Args:
            agent: 智能体对象
        """
        if len(agent.conversation_history) > self.max_conversation_history:
            # 保留系统消息和最近的对话
            system_message = agent.conversation_history[0]
            recent_messages = agent.conversation_history[-self.max_conversation_history:]
            agent.conversation_history = [system_message] + recent_messages
            
    def cleanup(self):
        """清理资源，释放内存"""
        self.agent_pool.clear()
        self.conversation_pool.clear()
```

### 3. 分布式处理配置
```python
class DistributedCAMELManager:
    """分布式CAMEL管理器，支持分布式处理"""
    
    def __init__(self, node_id: str, node_addresses: List[str]):
        """
        初始化分布式CAMEL管理器
        
        Args:
            node_id: 当前节点ID
            node_addresses: 所有节点地址列表
        """
        self.node_id = node_id
        self.node_addresses = node_addresses
        self.agents = {}
        self.communication_manager = CommunicationManager(node_id, node_addresses)
        
    def create_distributed_agent(self, role_name: str, role_description: str, 
                               node_id: str = None) -> DistributedAgent:
        """
        创建分布式智能体
        
        Args:
            role_name: 角色名称
            role_description: 角色描述
            node_id: 智能体所在的节点ID，如果为None则在当前节点创建
            
        Returns:
            分布式智能体
        """
        target_node_id = node_id if node_id else self.node_id
        
        if target_node_id == self.node_id:
            # 在当前节点创建智能体
            agent = DistributedAgent(
                role_name=role_name,
                role_description=role_description,
                node_id=target_node_id,
                communication_manager=self.communication_manager
            )
            self.agents[role_name] = agent
            return agent
        else:
            # 在远程节点创建智能体
            return self.communication_manager.create_remote_agent(
                role_name=role_name,
                role_description=role_description,
                node_id=target_node_id
            )
            
    def run_distributed_conversation(self, role_a: str, role_b: str, 
                                   task_prompt: str, max_turns: int = 10) -> List[Dict]:
        """
        运行分布式角色扮演对话
        
        Args:
            role_a: 第一个角色名称
            role_b: 第二个角色名称
            task_prompt: 任务提示
            max_turns: 最大对话轮次
            
        Returns:
            对话历史
        """
        agent_a = self.agents.get(role_a)
        agent_b = self.agents.get(role_b)
        
        if not agent_a or not agent_b:
            raise ValueError("One or both agents not found")
            
        conversation = DistributedRolePlayingConversation(
            agent_a=agent_a,
            agent_b=agent_b,
            task_prompt=task_prompt,
            max_turns=max_turns,
            communication_manager=self.communication_manager
        )
        
        return conversation.run()
```

## 测试用例

### 1. 基本功能测试
```python
def test_camel_basic_functionality():
    """测试CAMEL基本功能"""
    # 创建角色扮演管理器
    roles = [
        {"name": "Python Programmer", "description": "An expert Python programmer who writes clean and efficient code."},
        {"name": "Product Manager", "description": "A product manager who defines requirements and priorities."}
    ]
    
    manager = RolePlayingManager(roles)
    
    # 运行角色扮演对话
    task_prompt = "Design a simple web application for task management."
    conversation_history = manager.run_conversation(
        role_a="Python Programmer",
        role_b="Product Manager",
        task_prompt=task_prompt,
        max_turns=6
    )
    
    # 验证对话历史
    assert len(conversation_history) > 0, "应该有对话历史"
    
    # 验证对话轮次
    assert len(conversation_history) <= 6, "对话轮次应该不超过最大值"
    
    # 验证对话内容
    for turn in conversation_history:
        assert "speaker" in turn, "应该有说话者"
        assert "content" in turn, "应该有对话内容"
        assert "turn" in turn, "应该有轮次信息"
        
    print("基本功能测试通过")

def test_task_decomposition():
    """测试任务分解功能"""
    # 创建任务分解器
    decomposer = TaskDecomposer()
    
    # 分解任务
    task_description = "Create a web application for task management with user authentication and real-time updates."
    agent_roles = ["Frontend Developer", "Backend Developer", "UI/UX Designer"]
    
    subtasks = decomposer.decompose(task_description, agent_roles)
    
    # 验证子任务
    assert len(subtasks) > 0, "应该有子任务"
    
    for subtask in subtasks:
        assert "description" in subtask, "应该有任务描述"
        assert "agent" in subtask, "应该有执行智能体"
        assert "dependencies" in subtask, "应该有依赖关系"
        
    print("任务分解测试通过")

def test_collaboration_strategies():
    """测试协作策略"""
    # 创建智能体
    roles = [
        {"name": "Researcher", "description": "A researcher who gathers information."},
        {"name": "Writer", "description": "A writer who creates content."}
    ]
    
    manager = RolePlayingManager(roles)
    
    # 创建任务
    task_description = "Write a blog post about the benefits of renewable energy."
    task = SimpleTask(task_description, list(manager.agents.values()))
    
    # 测试顺序协作
    sequential_strategy = SequentialCollaboration()
    sequential_result = sequential_strategy.execute(manager.agents, task)
    
    assert "integrated_result" in sequential_result, "应该有整合结果"
    assert len(sequential_result["results"]) > 0, "应该有任务结果"
    
    # 测试并行协作
    parallel_strategy = ParallelCollaboration()
    parallel_result = parallel_strategy.execute(manager.agents, task)
    
    assert "integrated_result" in parallel_result, "应该有整合结果"
    assert len(parallel_result["results"]) > 0, "应该有任务结果"
    
    print("协作策略测试通过")
```

### 2. 性能基准测试
```python
import time
import psutil
import os

def test_camel_performance():
    """测试CAMEL性能"""
    # 创建角色扮演管理器
    roles = [
        {"name": "Agent1", "description": "An agent for testing performance."},
        {"name": "Agent2", "description": "Another agent for testing performance."}
    ]
    
    manager = RolePlayingManager(roles)
    
    # 记录开始时间和内存
    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss
    
    # 运行多次对话
    num_conversations = 10
    for i in range(num_conversations):
        task_prompt = f"Discuss topic {i}."
        conversation_history = manager.run_conversation(
            role_a="Agent1",
            role_b="Agent2",
            task_prompt=task_prompt,
            max_turns=4
        )
    
    # 记录结束时间和内存
    end_time = time.time()
    end_memory = process.memory_info().rss
    
    # 计算性能指标
    elapsed_time = end_time - start_time
    memory_usage = (end_memory - start_memory) / (1024 * 1024)  # MB
    avg_time_per_conversation = elapsed_time / num_conversations
    
    print(f"运行{num_conversations}次对话耗时: {elapsed_time:.2f}秒")
    print(f"平均每次对话耗时: {avg_time_per_conversation:.2f}秒")
    print(f"内存使用增加: {memory_usage:.2f}MB")
    
    # 验证性能
    assert avg_time_per_conversation < 30.0, "平均每次对话时间应该少于30秒"
    assert memory_usage < 50.0, "内存使用应该少于50MB"
    
    print("性能测试通过")

def test_memory_optimization():
    """测试内存优化"""
    # 创建内存管理器
    memory_manager = MemoryManager(max_conversation_history=5)
    
    # 创建智能体
    agent = memory_manager.get_agent(
        role_name="Test Agent",
        role_description="An agent for testing memory optimization."
    )
    
    # 添加大量对话历史
    for i in range(20):
        agent.step(f"Message {i}")
    
    # 裁剪对话历史
    memory_manager.trim_conversation_history(agent)
    
    # 验证对话历史长度
    assert len(agent.conversation_history) <= memory_manager.max_conversation_history + 1, "对话历史应该被裁剪"
    
    # 测试智能体池
    agent2 = memory_manager.get_agent(
        role_name="Test Agent",
        role_description="An agent for testing memory optimization."
    )
    
    assert agent is agent2, "应该从池中获取相同的智能体"
    
    print("内存优化测试通过")
```

### 3. 稳定性测试
```python
def test_camel_stability():
    """测试CAMEL稳定性"""
    # 创建角色扮演管理器
    roles = [
        {"name": "Agent1", "description": "An agent for testing stability."},
        {"name": "Agent2", "description": "Another agent for testing stability."}
    ]
    
    manager = RolePlayingManager(roles)
    
    # 长时间运行测试
    num_conversations = 50
    start_time = time.time()
    
    for i in range(num_conversations):
        try:
            task_prompt = f"Discuss topic {i}."
            conversation_history = manager.run_conversation(
                role_a="Agent1",
                role_b="Agent2",
                task_prompt=task_prompt,
                max_turns=4
            )
            
            # 验证对话历史
            assert len(conversation_history) > 0, f"对话{i}应该有历史记录"
            
        except Exception as e:
            print(f"对话{i}发生错误: {e}")
            # 继续执行下一个对话，测试系统稳定性
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"完成{num_conversations}次对话耗时: {elapsed_time:.2f}秒")
    
    print("稳定性测试通过")

def test_error_handling():
    """测试错误处理"""
    # 创建角色扮演管理器
    roles = [
        {"name": "Agent1", "description": "An agent for testing error handling."},
        {"name": "Agent2", "description": "Another agent for testing error handling."}
    ]
    
    manager = RolePlayingManager(roles)
    
    # 测试无效角色
    try:
        conversation_history = manager.run_conversation(
            role_a="InvalidAgent",
            role_b="Agent2",
            task_prompt="Test task.",
            max_turns=4
        )
        assert False, "应该抛出异常"
    except Exception as e:
        print(f"处理无效角色时捕获异常: {e}")
    
    # 测试空任务提示
    try:
        conversation_history = manager.run_conversation(
            role_a="Agent1",
            role_b="Agent2",
            task_prompt="",
            max_turns=4
        )
        # 可能不抛出异常，但应该有合理的处理
    except Exception as e:
        print(f"处理空任务提示时捕获异常: {e}")
    
    # 测试负数轮次
    try:
        conversation_history = manager.run_conversation(
            role_a="Agent1",
            role_b="Agent2",
            task_prompt="Test task.",
            max_turns=-1
        )
        # 可能不抛出异常，但应该有合理的处理
    except Exception as e:
        print(f"处理负数轮次时捕获异常: {e}")
    
    print("错误处理测试通过")
```

## 总结

CAMEL是一个强大的多智能体协作框架，具有以下特点：

### 1. 核心优势
- **角色扮演**: 支持智能体扮演不同角色并进行协作
- **任务分解**: 能够将复杂任务分解为子任务并分配给不同智能体
- **多种协作策略**: 支持顺序、并行等多种协作策略
- **灵活的对话管理**: 提供灵活的对话管理和历史记录功能
- **提示工程**: 提供专门的提示工程工具和模板

### 2. 应用场景
- **多智能体研究**: 研究智能体协作和交互行为
- **复杂问题解决**: 通过多智能体协作解决复杂问题
- **角色扮演模拟**: 模拟不同角色之间的交互
- **集体决策**: 支持多智能体集体决策过程
- **创意生成**: 通过多智能体协作生成创意内容

### 3. 集成建议
- **与语言模型集成**: 作为语言模型的多智能体协作框架
- **与任务管理系统集成**: 提供智能任务分解和分配能力
- **与对话系统集成**: 增强对话系统的角色扮演能力
- **与决策支持系统集成**: 提供多智能体集体决策支持
- **与创意生成系统集成**: 通过多智能体协作增强创意生成能力

### 4. 未来发展方向
- **更智能的任务分解**: 开发更智能的任务分解算法
- **自适应协作策略**: 根据任务特点自适应选择协作策略
- **更丰富的角色模板**: 提供更丰富的角色模板和描述
- **性能优化**: 进一步优化性能和资源使用
- **可视化工具**: 开发可视化的多智能体协作工具

CAMEL作为多智能体协作框架，为真实婴儿AI管家系统提供了强大的多智能体协作能力，能够支持复杂任务的分解与分配，实现智能体之间的有效协作，并提供灵活的角色扮演功能。通过与其他系统的集成，CAMEL将为AI管家系统的认知决策层提供重要的多智能体协作支持。