"""
Knowledge Graph, Plugin System & API Gateway 测试
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKnowledgeGraph:
    """知识图谱测试"""

    def test_add_entity(self):
        """测试添加实体"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            entity = kg.add_entity("python", "Python", EntityType.CONCEPT,
                                   description="编程语言")
            assert entity.entity_id == "python"
            assert entity.name == "Python"
            assert entity.entity_type == EntityType.CONCEPT

            kg.close()

    def test_get_entity(self):
        """测试获取实体"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("python", "Python", EntityType.CONCEPT)

            entity = kg.get_entity("python")
            assert entity is not None
            assert entity.name == "Python"

            # 缓存命中
            entity2 = kg.get_entity("python")
            assert entity2.access_count > 0

            kg.close()

    def test_add_relation(self):
        """测试添加关系"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType, RelationType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("python", "Python", EntityType.CONCEPT)
            kg.add_entity("programming", "Programming", EntityType.CONCEPT)

            rel_id = kg.add_relation("python", "programming", RelationType.IS_A)
            assert rel_id.startswith("rel_")

            kg.close()

    def test_get_relations(self):
        """测试获取关系"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType, RelationType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("python", "Python", EntityType.CONCEPT)
            kg.add_entity("typing", "Dynamic Typing", EntityType.CONCEPT)

            kg.add_relation("python", "typing", RelationType.HAS_PROPERTY)

            relations = kg.get_relations("python", "outgoing")
            assert len(relations) == 1
            assert relations[0].target_id == "typing"

            kg.close()

    def test_search_entities(self):
        """测试搜索实体"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("python", "Python", EntityType.CONCEPT)
            kg.add_entity("javascript", "JavaScript", EntityType.CONCEPT)
            kg.add_entity("django", "Django", EntityType.SKILL)

            results = kg.search_entities("Python")
            assert len(results) >= 1
            assert any(e.name == "Python" for e in results)

            kg.close()

    def test_find_path(self):
        """测试查找路径"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType, RelationType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            # A -> B -> C
            kg.add_entity("a", "A", EntityType.CONCEPT)
            kg.add_entity("b", "B", EntityType.CONCEPT)
            kg.add_entity("c", "C", EntityType.CONCEPT)

            kg.add_relation("a", "b", RelationType.RELATED_TO)
            kg.add_relation("b", "c", RelationType.RELATED_TO)

            paths = kg.find_path("a", "c")
            assert len(paths) >= 1
            assert paths[0] == ["a", "b", "c"]

            kg.close()

    def test_infer_relations(self):
        """测试关系推理"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType, RelationType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            # Python is_a Language, Language has_property Expressive
            kg.add_entity("python", "Python", EntityType.CONCEPT)
            kg.add_entity("language", "Language", EntityType.CONCEPT)
            kg.add_entity("expressive", "Expressive", EntityType.CONCEPT)

            kg.add_relation("python", "language", RelationType.IS_A)
            kg.add_relation("language", "expressive", RelationType.HAS_PROPERTY)

            inferences = kg.infer_relations("python")
            # 应该有继承属性推理
            assert len(inferences) >= 1

            kg.close()

    def test_entity_neighborhood(self):
        """测试实体邻域"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType, RelationType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("python", "Python", EntityType.CONCEPT)
            kg.add_entity("typing", "Dynamic Typing", EntityType.CONCEPT)
            kg.add_relation("python", "typing", RelationType.HAS_PROPERTY)

            neighborhood = kg.get_entity_neighborhood("python")
            assert "entity" in neighborhood
            assert len(neighborhood["outgoing_relations"]) == 1
            assert len(neighborhood["related_entities"]) == 1

            kg.close()

    def test_update_entity_properties(self):
        """测试更新实体属性"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("python", "Python", EntityType.CONCEPT)
            kg.update_entity_properties("python", {"popularity": "high", "year": 1991})

            entity = kg.get_entity("python")
            assert entity.properties.get("popularity") == "high"
            assert entity.properties.get("year") == 1991

            kg.close()

    def test_delete_entity(self):
        """测试删除实体"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType, RelationType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("temp", "Temporary", EntityType.CONCEPT)
            kg.add_entity("other", "Other", EntityType.CONCEPT)
            kg.add_relation("temp", "other", RelationType.RELATED_TO)

            kg.delete_entity("temp")
            assert kg.get_entity("temp") is None

            kg.close()

    def test_get_stats(self):
        """测试获取统计"""
        from nomad_mem.memory.knowledge_graph import KnowledgeGraph, EntityType

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kg.db")
            kg = KnowledgeGraph(db_path)

            kg.add_entity("python", "Python", EntityType.CONCEPT)
            kg.add_entity("django", "Django", EntityType.SKILL)

            stats = kg.get_stats()
            assert stats["total_entities"] == 2
            assert "entity_types" in stats

            kg.close()


class TestPluginSystem:
    """插件系统测试"""

    def test_register_plugin(self):
        """测试注册插件"""
        from nomad_mem.plugins.plugin_system import PluginSystem

        system = PluginSystem()
        plugin = system.register_plugin("test_plugin", "Test Plugin", "1.0.0")

        assert plugin.plugin_id == "test_plugin"
        assert plugin.name == "Test Plugin"

    def test_load_plugin(self):
        """测试加载插件"""
        from nomad_mem.plugins.plugin_system import PluginSystem, PluginStatus

        system = PluginSystem()
        system.register_plugin("plugin_a", "Plugin A")
        system.register_plugin("plugin_b", "Plugin B", dependencies=["plugin_a"])

        assert system.load_plugin("plugin_a") is True
        assert system.plugins["plugin_a"].status == PluginStatus.LOADED

    def test_load_plugin_with_dependencies(self):
        """测试加载带依赖的插件"""
        from nomad_mem.plugins.plugin_system import PluginSystem, PluginStatus

        system = PluginSystem()
        system.register_plugin("base", "Base Plugin")
        system.register_plugin("extended", "Extended Plugin", dependencies=["base"])

        # 加载extended会自动加载base
        assert system.load_plugin("extended") is True
        assert system.plugins["base"].status == PluginStatus.LOADED
        assert system.plugins["extended"].status == PluginStatus.LOADED

    def test_load_plugin_missing_dependency(self):
        """测试加载缺失依赖的插件"""
        from nomad_mem.plugins.plugin_system import PluginSystem, PluginStatus

        system = PluginSystem()
        system.register_plugin("orphan", "Orphan Plugin", dependencies=["nonexistent"])

        assert system.load_plugin("orphan") is False
        assert system.plugins["orphan"].status == PluginStatus.ERROR

    def test_start_stop_plugin(self):
        """测试启动停止插件"""
        from nomad_mem.plugins.plugin_system import PluginSystem, PluginStatus

        system = PluginSystem()
        system.register_plugin("test", "Test Plugin")
        system.load_plugin("test")

        assert system.start_plugin("test") is True
        assert system.plugins["test"].status == PluginStatus.STARTED

        assert system.stop_plugin("test") is True
        assert system.plugins["test"].status == PluginStatus.STOPPED

    def test_register_hook(self):
        """测试注册钩子"""
        from nomad_mem.plugins.plugin_system import PluginSystem

        system = PluginSystem()
        results = []

        def on_start(plugin_id):
            results.append(f"started: {plugin_id}")

        system.register_hook("after_plugin_start", on_start)
        system.register_plugin("test", "Test Plugin")
        system.load_plugin("test")
        system.start_plugin("test")

        assert len(results) == 1
        assert "started: test" in results[0]

    def test_execute_hook(self):
        """测试执行钩子"""
        from nomad_mem.plugins.plugin_system import PluginSystem

        system = PluginSystem()

        def compute(x):
            return x * 2

        system.register_hook("compute", compute)
        results = system.execute_hook("compute", 5)

        assert results == [10]

    def test_get_plugin_dependencies(self):
        """测试获取插件依赖"""
        from nomad_mem.plugins.plugin_system import PluginSystem

        system = PluginSystem()
        system.register_plugin("a", "A")
        system.register_plugin("b", "B", dependencies=["a"])
        system.register_plugin("c", "C", dependencies=["b"])

        deps = system.get_plugin_dependencies("c")
        assert "a" in deps
        assert "b" in deps

    def test_check_dependency_graph(self):
        """测试检查循环依赖"""
        from nomad_mem.plugins.plugin_system import PluginSystem

        system = PluginSystem()
        system.register_plugin("a", "A", dependencies=["b"])
        system.register_plugin("b", "B", dependencies=["a"])

        issues = system.check_dependency_graph()
        assert len(issues) > 0

    def test_list_plugins(self):
        """测试列出插件"""
        from nomad_mem.plugins.plugin_system import PluginSystem

        system = PluginSystem()
        system.register_plugin("plugin1", "Plugin 1")
        system.register_plugin("plugin2", "Plugin 2")

        plugins = system.list_plugins()
        assert len(plugins) == 2

    def test_get_stats(self):
        """测试获取统计"""
        from nomad_mem.plugins.plugin_system import PluginSystem

        system = PluginSystem()
        system.register_plugin("test", "Test")

        stats = system.get_stats()
        assert stats["total_plugins"] == 1


class TestAPIGateway:
    """API网关测试"""

    def test_register_route(self):
        """测试注册路由"""
        from nomad_mem.web.api_gateway import APIGateway

        gateway = APIGateway()

        def handler(**kwargs):
            return {"message": "OK"}

        gateway.register_route("/test", handler, ["GET"])
        assert "GET:/test" in gateway.routes

    def test_handle_request(self):
        """测试处理请求"""
        from nomad_mem.web.api_gateway import APIGateway

        gateway = APIGateway()

        def handler(**kwargs):
            return {"message": "Hello"}

        gateway.register_route("/hello", handler, ["GET"])

        response = gateway.handle_request("GET", "/hello", "client1")
        assert response["status"] == 200
        assert response["data"]["message"] == "Hello"

    def test_handle_request_not_found(self):
        """测试处理不存在的请求"""
        from nomad_mem.web.api_gateway import APIGateway

        gateway = APIGateway()
        response = gateway.handle_request("GET", "/nonexistent", "client1")

        assert response["status"] == 404

    def test_rate_limiter(self):
        """测试限流器"""
        from nomad_mem.web.api_gateway import RateLimiter, RateLimit

        limiter = RateLimiter(RateLimit(max_requests=3, window_seconds=60))

        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False  # 超出限制

    def test_rate_limit_status(self):
        """测试限流状态"""
        from nomad_mem.web.api_gateway import APIGateway

        gateway = APIGateway()
        status = gateway.get_rate_limit_status("client1")

        assert "remaining" in status
        assert "limit" in status
        assert "window" in status

    def test_request_logging(self):
        """测试请求日志"""
        from nomad_mem.web.api_gateway import APIGateway

        gateway = APIGateway()

        def handler(**kwargs):
            return {"ok": True}

        gateway.register_route("/log", handler, ["GET"])
        gateway.handle_request("GET", "/log", "client1")

        stats = gateway.get_request_stats()
        assert stats["total_requests"] == 1

    def test_request_stats(self):
        """测试请求统计"""
        from nomad_mem.web.api_gateway import APIGateway

        gateway = APIGateway()
        stats = gateway.get_request_stats()

        assert stats["total_requests"] == 0

    def test_register_middleware(self):
        """测试注册中间件"""
        from nomad_mem.web.api_gateway import APIGateway

        gateway = APIGateway()
        called = []

        def middleware(method, path, client_id, body):
            called.append(path)

        gateway.register_middleware(middleware)
        gateway.register_route("/mw", lambda **k: {"ok": True}, ["GET"])
        gateway.handle_request("GET", "/mw", "client1")

        assert "/mw" in called

    def test_auth_manager_create_and_validate(self):
        """测试认证管理器"""
        from nomad_mem.web.api_gateway import AuthManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "auth.db")
            auth = AuthManager(db_path)

            key = auth.create_key("Test Key", ["read", "write"])
            assert key.startswith("jarvis_")

            info = auth.validate_key(key)
            assert info is not None
            assert info["name"] == "Test Key"

            auth.conn.close()

    def test_auth_manager_revoke(self):
        """测试撤销API Key"""
        from nomad_mem.web.api_gateway import AuthManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "auth.db")
            auth = AuthManager(db_path)

            key = auth.create_key("Revocable Key")
            assert auth.validate_key(key) is not None

            auth.revoke_key(key)
            assert auth.validate_key(key) is None

            auth.conn.close()

    def test_api_key_auth_in_request(self):
        """测试请求中API Key认证"""
        from nomad_mem.web.api_gateway import APIGateway, AuthManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "auth.db")
            auth = AuthManager(db_path)
            key = auth.create_key("Test Key")

            gateway = APIGateway(config={"auth_db": db_path})
            gateway.auth_manager = auth

            def handler(**kwargs):
                return {"authenticated": True}

            gateway.register_route("/auth", handler, ["GET"])

            # 有效key
            response = gateway.handle_request("GET", "/auth", "client1", api_key=key)
            assert response["status"] == 200

            # 无效key
            response = gateway.handle_request("GET", "/auth", "client1", api_key="invalid")
            assert response["status"] == 401

            auth.conn.close()
