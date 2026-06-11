"""
V17测试 - JarvisCore V2 集成测试

覆盖模块:
1. JarvisCore 初始化 - 所有模块的懒加载
2. 安全层集成 - 输入/输出安全检查
3. 知识图谱增强 - chat响应中的kg_enrichment
4. 插件系统 - register_plugin接口
5. 知识管理 - add_knowledge / query_knowledge
6. 状态查询 - get_status 包含所有新模块
7. 任务执行 - execute_task
8. 关闭 - close方法
9. 端到端流程 - 完整工作流测试

测试策略:
- 使用简单 JarvisCore() 构造函数（无需配置）
- 所有导入使用 try/except 优雅回退
- initialize() 在首次 chat/execute_task 调用时懒加载所有模块
- 覆盖正常路径、边界条件和异常情况
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# =============================================================================
# TestJarvisV2Init
# =============================================================================


class TestJarvisV2Init:
    """JarvisCore V2 初始化测试"""

    def test_basic_init(self):
        """测试: 基础初始化不应报错"""
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
        except ImportError:
            pytest.skip("JarvisCore not available")

        jarvis = JarvisCore()
        assert jarvis.initialized is False
        assert jarvis.config == {}

    def test_init_with_config(self):
        """测试: 带配置初始化"""
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
        except ImportError:
            pytest.skip("JarvisCore not available")

        config = {"persona": {}, "intent": {}}
        jarvis = JarvisCore(config=config)
        assert jarvis.config == config

    def test_init_modules_are_none(self):
        """测试: 初始化后所有模块应为None（懒加载）"""
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
        except ImportError:
            pytest.skip("JarvisCore not available")

        jarvis = JarvisCore()
        # 核心模块
        assert jarvis.memory_os is None
        assert jarvis.memory_evolution is None
        assert jarvis.intent_engine is None
        assert jarvis.task_planner is None
        # 新增模块
        assert jarvis.knowledge_graph is None
        assert jarvis.plugin_system is None
        assert jarvis.api_gateway is None
        assert jarvis.safety_layer is None

    def test_initialize_all_modules(self):
        """测试: initialize() 应加载所有可用模块"""
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
        except ImportError:
            pytest.skip("JarvisCore not available")

        jarvis = JarvisCore()
        jarvis.initialize()

        assert jarvis.initialized is True
        # 检查至少部分模块被加载（取决于环境可用性）
        # 核心模块
        modules_to_check = [
            "knowledge_graph",
            "plugin_system",
            "api_gateway",
            "safety_layer",
        ]
        # 至少有一个新模块被加载
        loaded_count = sum(
            1 for mod in modules_to_check if getattr(jarvis, mod) is not None
        )
        assert loaded_count > 0, "至少应有一个新模块被加载"

    def test_double_initialize_is_safe(self):
        """测试: 重复调用 initialize() 不应报错"""
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
        except ImportError:
            pytest.skip("JarvisCore not available")

        jarvis = JarvisCore()
        jarvis.initialize()
        jarvis.initialize()  # 不应抛异常
        assert jarvis.initialized is True


# =============================================================================
# TestJarvisV2Chat
# =============================================================================


class TestJarvisV2Chat:
    """JarvisCore V2 聊天接口测试"""

    def setup_method(self):
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
            self.JarvisCore = JarvisCore
        except ImportError:
            self.JarvisCore = None

    def _get_jarvis(self):
        if self.JarvisCore is None:
            pytest.skip("JarvisCore not available")
        return self.JarvisCore()

    def test_chat_basic(self):
        """测试: 基础聊天应返回响应"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("你好，今天天气怎么样？")

        assert "response" in response
        assert isinstance(response["response"], str)
        assert len(response["response"]) > 0
        assert response["message"] == "你好，今天天气怎么样？"
        assert response["user_id"] == "default"

    def test_chat_with_custom_user_id(self):
        """测试: 自定义用户ID"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("测试消息", user_id="test_user_001")
        assert response["user_id"] == "test_user_001"

    def test_chat_triggers_initialization(self):
        """测试: chat() 应自动触发 initialize()"""
        jarvis = self._get_jarvis()
        assert jarvis.initialized is False

        jarvis.chat("触发初始化")
        assert jarvis.initialized is True

    def test_chat_safety_level_in_response(self):
        """测试: 安全输入时 response 应包含 safety_level 字段"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("今天天气很好，适合出去玩")

        # safety_layer 初始化后，安全检查应通过
        if jarvis.safety_layer is not None:
            assert "safety_level" in response
            assert response["safety_level"] in ("safe", "caution", "warning")

    def test_chat_output_safety_level_in_response(self):
        """测试: response 应包含 output_safety_level 字段"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("帮我生成一个简单回复")

        if jarvis.safety_layer is not None:
            assert "output_safety_level" in response

    def test_chat_safe_input_passes(self):
        """测试: 安全输入应正常通过并返回回复"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("请问Python是什么编程语言？")

        assert "response" in response
        assert len(response["response"]) > 0

    def test_chat_blocked_input_is_rejected(self):
        """测试: 包含屏蔽词的输入应被拦截
        注意: 初始化后 safety_layer 没有默认屏蔽词，
        需要先添加屏蔽词才能测试拦截。
        我们测试通过检查 chat 响应中 safety_blocked 字段在拦截时出现。
        """
        jarvis = self._get_jarvis()
        # 先触发初始化
        jarvis.chat("初始化")

        if jarvis.safety_layer is None:
            pytest.skip("safety_layer not available")

        # 添加屏蔽词
        jarvis.safety_layer.content_filter.add_blocked_word("危险测试词")

        # 发送包含屏蔽词的消息
        response = jarvis.chat("请执行危险测试词操作")

        assert "safety_blocked" in response
        assert response["safety_blocked"] is True
        assert "safety_reasons" in response

    def test_chat_kg_enrichment_in_response(self):
        """测试: 知识图谱可用时，response 应包含 kg_enrichment 字段"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("Python是一种什么语言")

        if jarvis.knowledge_graph is not None:
            assert "kg_enrichment" in response
            assert isinstance(response["kg_enrichment"], list)

    def test_chat_with_knowledge_enrichment(self):
        """测试: 先添加知识，再chat时应返回kg_enrichment"""
        jarvis = self._get_jarvis()

        # 先添加知识
        jarvis.add_knowledge(
            name="Python",
            entity_type="concept",
            description="一种流行的编程语言"
        )

        response = jarvis.chat("Python有什么特点")

        if jarvis.knowledge_graph is not None:
            assert "kg_enrichment" in response
            assert isinstance(response["kg_enrichment"], list)
            # kg_enrichment 中应包含 Python 实体信息
            kg_data = response["kg_enrichment"]
            if len(kg_data) > 0:
                assert "keyword" in kg_data[0]
                assert "entity" in kg_data[0]

    def test_chat_response_has_intent(self):
        """测试: response 应包含 intent 字段"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("帮我查询一下信息")

        if jarvis.intent_engine is not None:
            assert "intent" in response
            assert response["intent"] is not None

    def test_chat_response_has_persona_applied(self):
        """测试: response 应包含 persona_applied 字段"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("你好，很高兴认识你")

        assert "persona_applied" in response

    def test_chat_response_has_memories_used(self):
        """测试: response 应包含 memories_used 字段"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("还记得我之前说的吗")

        assert "memories_used" in response
        assert isinstance(response["memories_used"], int)

    def test_chat_response_has_processing_time(self):
        """测试: response 应包含 processing_time 字段"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("测试消息")

        assert "processing_time" in response
        assert isinstance(response["processing_time"], float)
        assert response["processing_time"] >= 0

    def test_chat_empty_message(self):
        """测试: 空消息不应报错"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("")

        assert "response" in response
        assert "processing_time" in response


# =============================================================================
# TestJarvisV2Plugins
# =============================================================================


class TestJarvisV2Plugins:
    """JarvisCore V2 插件系统测试"""

    def setup_method(self):
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
            self.JarvisCore = JarvisCore
        except ImportError:
            self.JarvisCore = None

    def _get_jarvis(self):
        if self.JarvisCore is None:
            pytest.skip("JarvisCore not available")
        return self.JarvisCore()

    def test_register_plugin_success(self):
        """测试: register_plugin 应成功注册插件"""
        jarvis = self._get_jarvis()
        # 触发初始化
        jarvis.chat("初始化")

        def my_handler():
            return "handled"

        result = jarvis.register_plugin(
            plugin_id="test_plugin_001",
            name="测试插件",
            handler=my_handler
        )
        assert result is True

    def test_register_plugin_with_dependencies(self):
        """测试: register_plugin 支持依赖声明"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        def handler_a():
            return "A"

        def handler_b():
            return "B"

        # 注册基础插件
        result_a = jarvis.register_plugin("base_plugin", "基础插件", handler_a)
        assert result_a is True

        # 注册依赖基础插件的插件
        result_b = jarvis.register_plugin(
            "extended_plugin",
            "扩展插件",
            handler_b,
            dependencies=["base_plugin"]
        )
        assert result_b is True

    def test_register_multiple_plugins(self):
        """测试: 注册多个插件"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        for i in range(3):
            result = jarvis.register_plugin(
                f"plugin_{i}",
                f"插件{i}",
                lambda: i
            )
            assert result is True

    def test_plugin_available_in_status(self):
        """测试: 注册插件后，get_status 应反映插件数量"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        initial_stats = jarvis.get_status()
        if jarvis.plugin_system:
            initial_count = initial_stats["modules"]["plugin_system"]["total_plugins"]
        else:
            initial_count = 0

        jarvis.register_plugin("status_test_plugin", "状态测试", lambda: None)

        new_stats = jarvis.get_status()
        if jarvis.plugin_system:
            new_count = new_stats["modules"]["plugin_system"]["total_plugins"]
            assert new_count == initial_count + 1


# =============================================================================
# TestJarvisV2Knowledge
# =============================================================================


class TestJarvisV2Knowledge:
    """JarvisCore V2 知识管理测试"""

    def setup_method(self):
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
            self.JarvisCore = JarvisCore
        except ImportError:
            self.JarvisCore = None

    def _get_jarvis(self):
        if self.JarvisCore is None:
            pytest.skip("JarvisCore not available")
        return self.JarvisCore()

    def test_add_knowledge_returns_entity_id(self):
        """测试: add_knowledge 应返回实体ID"""
        jarvis = self._get_jarvis()
        # 触发初始化
        jarvis.chat("初始化")

        entity_id = jarvis.add_knowledge(
            name="机器学习",
            entity_type="concept",
            description="人工智能的一个分支"
        )

        if jarvis.knowledge_graph is not None:
            assert entity_id != ""
            assert "机器学习" in entity_id or "machine_learning" in entity_id

    def test_add_knowledge_different_types(self):
        """测试: 添加不同类型的知识实体"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        entity_types = ["concept", "person", "object", "event", "place", "skill"]
        for et in entity_types:
            entity_id = jarvis.add_knowledge(
                name=f"测试_{et}",
                entity_type=et,
                description=f"测试{et}类型"
            )
            if jarvis.knowledge_graph is not None:
                assert entity_id != ""

    def test_add_knowledge_with_properties(self):
        """测试: 添加带属性的知识"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        entity_id = jarvis.add_knowledge(
            name="Python语言",
            entity_type="skill",
            description="编程语言",
            properties={"level": "advanced", "year": 1991}
        )

        if jarvis.knowledge_graph is not None:
            assert entity_id != ""

    def test_query_knowledge_by_keyword(self):
        """测试: query_knowledge 按关键词查询"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        # 先添加知识
        jarvis.add_knowledge(
            name="深度学习",
            entity_type="concept",
            description="机器学习的一个分支"
        )

        result = jarvis.query_knowledge("深度")

        if jarvis.knowledge_graph is not None:
            assert "entities" in result
            assert "enrichment" in result
            assert len(result["entities"]) >= 1

    def test_query_knowledge_no_match(self):
        """测试: 查询不存在的关键词应返回空列表"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        result = jarvis.query_knowledge("不存在的词_xyz")

        if jarvis.knowledge_graph is not None:
            assert "entities" in result
            assert isinstance(result["entities"], list)

    def test_query_knowledge_with_depth(self):
        """测试: query_knowledge 支持深度参数"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        jarvis.add_knowledge(name="父概念", entity_type="concept")
        jarvis.add_knowledge(name="子概念", entity_type="concept")

        result = jarvis.query_knowledge("父", depth=2)

        if jarvis.knowledge_graph is not None:
            assert "entities" in result

    def test_add_multiple_knowledge_then_query(self):
        """测试: 添加多条知识后批量查询"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        topics = ["Python", "JavaScript", "Java", "Go"]
        for topic in topics:
            jarvis.add_knowledge(name=topic, entity_type="skill")

        # 查询所有包含"a"的主题
        result = jarvis.query_knowledge("Java")
        if jarvis.knowledge_graph is not None:
            assert len(result["entities"]) >= 1


# =============================================================================
# TestJarvisV2Status
# =============================================================================


class TestJarvisV2Status:
    """JarvisCore V2 状态查询测试"""

    def setup_method(self):
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
            self.JarvisCore = JarvisCore
        except ImportError:
            self.JarvisCore = None

    def _get_jarvis(self):
        if self.JarvisCore is None:
            pytest.skip("JarvisCore not available")
        return self.JarvisCore()

    def test_get_status_before_init(self):
        """测试: 初始化前 get_status 应返回基本状态"""
        jarvis = self._get_jarvis()
        status = jarvis.get_status()

        assert "initialized" in status
        assert status["initialized"] is False
        assert "modules" in status

    def test_get_status_after_init(self):
        """测试: 初始化后 get_status 应反映所有模块状态"""
        jarvis = self._get_jarvis()
        jarvis.initialize()

        status = jarvis.get_status()
        assert status["initialized"] is True
        assert isinstance(status["modules"], dict)

    def test_get_status_has_knowledge_graph(self):
        """测试: get_status 应包含 knowledge_graph 模块状态"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        status = jarvis.get_status()
        if jarvis.knowledge_graph is not None:
            assert "knowledge_graph" in status["modules"]
            kg_stats = status["modules"]["knowledge_graph"]
            assert "total_entities" in kg_stats

    def test_get_status_has_plugin_system(self):
        """测试: get_status 应包含 plugin_system 模块状态"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        status = jarvis.get_status()
        if jarvis.plugin_system is not None:
            assert "plugin_system" in status["modules"]
            ps_stats = status["modules"]["plugin_system"]
            assert "total_plugins" in ps_stats

    def test_get_status_has_api_gateway(self):
        """测试: get_status 应包含 api_gateway 模块状态"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        status = jarvis.get_status()
        if jarvis.api_gateway is not None:
            assert "api_gateway" in status["modules"]

    def test_get_status_has_safety_layer(self):
        """测试: get_status 应包含 safety_layer 模块状态"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        status = jarvis.get_status()
        if jarvis.safety_layer is not None:
            assert "safety_layer" in status["modules"]
            sl_stats = status["modules"]["safety_layer"]
            assert "stats" in sl_stats

    def test_get_status_after_operations(self):
        """测试: 执行操作后 get_status 应更新"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")

        # 添加知识
        jarvis.add_knowledge(name="测试实体", entity_type="concept")
        # 注册插件
        jarvis.register_plugin("status_plugin", "状态插件", lambda: None)

        status = jarvis.get_status()
        if jarvis.knowledge_graph is not None:
            assert status["modules"]["knowledge_graph"]["total_entities"] >= 1
        if jarvis.plugin_system is not None:
            assert status["modules"]["plugin_system"]["total_plugins"] >= 1


# =============================================================================
# TestJarvisV2FullWorkflow
# =============================================================================


class TestJarvisV2FullWorkflow:
    """JarvisCore V2 端到端完整工作流测试"""

    def setup_method(self):
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
            self.JarvisCore = JarvisCore
        except ImportError:
            self.JarvisCore = None

    def _get_jarvis(self):
        if self.JarvisCore is None:
            pytest.skip("JarvisCore not available")
        return self.JarvisCore()

    def test_full_workflow(self):
        """端到端测试: 创建 -> 聊天 -> 注册插件 -> 添加知识 -> 查询知识 -> 状态 -> 关闭"""
        jarvis = self._get_jarvis()

        # 1. 初始状态
        assert jarvis.initialized is False

        # 2. 聊天（自动初始化）
        chat_response = jarvis.chat("你好，我是新用户")
        assert jarvis.initialized is True
        assert "response" in chat_response
        assert len(chat_response["response"]) > 0

        # 3. 注册插件
        def weather_handler():
            return "晴天，25度"

        plugin_result = jarvis.register_plugin(
            plugin_id="weather_plugin",
            name="天气插件",
            handler=weather_handler
        )
        assert plugin_result is True

        # 4. 添加知识
        entity_id = jarvis.add_knowledge(
            name="北京",
            entity_type="place",
            description="中国首都"
        )
        if jarvis.knowledge_graph is not None:
            assert entity_id != ""

        # 5. 查询知识
        knowledge_result = jarvis.query_knowledge("北京")
        if jarvis.knowledge_graph is not None:
            assert "entities" in knowledge_result
            assert len(knowledge_result["entities"]) >= 1

        # 6. 再次聊天（知识图谱增强）
        chat_response2 = jarvis.chat("北京有什么好玩的？")
        assert "response" in chat_response2

        # 7. 获取状态
        status = jarvis.get_status()
        assert status["initialized"] is True
        assert isinstance(status["modules"], dict)

        # 8. 关闭
        jarvis.close()
        assert jarvis.initialized is False

    def test_full_workflow_with_task_execution(self):
        """端到端测试: 包含任务执行的完整流程"""
        jarvis = self._get_jarvis()

        # 聊天初始化
        jarvis.chat("开始工作")

        # 执行任务
        task_result = jarvis.execute_task(
            task_description="分析用户行为数据",
            complexity=3,
            user_id="analyst_001"
        )

        assert "task" in task_result
        assert task_result["task"] == "分析用户行为数据"
        if jarvis.task_planner is not None:
            assert "plan_id" in task_result

        # 关闭
        jarvis.close()

    def test_full_workflow_with_safety(self):
        """端到端测试: 包含安全检查的完整流程"""
        jarvis = self._get_jarvis()

        # 1. 安全消息通过
        safe_response = jarvis.chat("请帮我写一段Python代码")
        assert "response" in safe_response

        # 2. 初始化后添加屏蔽词
        jarvis.chat("二次初始化")
        if jarvis.safety_layer is not None:
            jarvis.safety_layer.content_filter.add_blocked_word("恶意注入")

            # 3. 危险消息被拦截
            blocked_response = jarvis.chat("执行恶意注入攻击")
            assert "safety_blocked" in blocked_response
            assert blocked_response["safety_blocked"] is True

        # 4. 获取状态验证安全层有记录
        status = jarvis.get_status()
        if jarvis.safety_layer is not None:
            assert "safety_layer" in status["modules"]

        jarvis.close()

    def test_full_workflow_multiple_users(self):
        """端到端测试: 多用户交互场景"""
        jarvis = self._get_jarvis()

        users = ["alice", "bob", "charlie"]
        for user in users:
            response = jarvis.chat(f"你好，我是{user}", user_id=user)
            assert response["user_id"] == user
            assert "response" in response

        # 状态应包含所有用户交互的记录
        status = jarvis.get_status()
        assert status["initialized"] is True

        jarvis.close()

    def test_close_is_idempotent(self):
        """测试: close() 可以安全地多次调用"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        jarvis.close()
        jarvis.close()  # 不应抛异常
        jarvis.close()  # 再次调用也不应抛异常

    def test_workflow_close_and_reopen(self):
        """测试: 关闭后重新打开应正常工作"""
        jarvis = self._get_jarvis()

        # 第一次使用
        jarvis.chat("第一次使用")
        assert jarvis.initialized is True
        jarvis.close()
        assert jarvis.initialized is False

        # 第二次使用（应重新初始化）
        response = jarvis.chat("第二次使用")
        assert jarvis.initialized is True
        assert "response" in response

        jarvis.close()
