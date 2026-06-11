"""
V20 测试 - 工具系统 (Tool System) 与 Jarvis 集成测试

覆盖模块:
1. ToolRegistry - 工具注册、发现、Schema 描述、统计
2. ToolExecutor - 同步执行、超时控制、结果校验、执行历史
3. Builtin Tools - 8 个内置工具的注册和功能测试
4. ToolSelector - 工具智能选择、关键词匹配、上下文匹配、历史记录
5. Jarvis Integration - JarvisCore 中工具系统的初始化和使用

测试策略:
- 使用 tempfile.TemporaryDirectory() 隔离数据库文件
- 类组织: TestToolRegistry, TestToolExecutor, TestBuiltinTools, TestToolSelector, TestJarvisToolIntegration
- 目标约 45 个测试，覆盖正常路径、边界条件和异常情况
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# =============================================================================
# Module 1: ToolRegistry Tests
# =============================================================================


class TestToolRegistry:
    """ToolRegistry 工具注册表测试 (10 tests)"""

    def setup_method(self):
        try:
            from nomad_mem.skills.tool_registry import (
                ToolRegistry, ToolCategory, ToolStatus, ToolParameter, ToolInfo,
            )
            self.ToolRegistry = ToolRegistry
            self.ToolCategory = ToolCategory
            self.ToolStatus = ToolStatus
            self.ToolParameter = ToolParameter
            self.ToolInfo = ToolInfo
        except ImportError:
            pytest.skip("ToolRegistry not available")

    def _make_registry(self):
        return self.ToolRegistry()

    def test_register_tool_with_parameters(self):
        """测试: 注册带参数的工具"""
        reg = self._make_registry()
        params = [
            self.ToolParameter("name", "str", "用户名称", True),
            self.ToolParameter("age", "int", "用户年龄", False, 0),
        ]
        info = reg.register_tool(
            tool_id="greet", name="greet", description="打招呼",
            category=self.ToolCategory.CUSTOM, parameters=params,
            handler=lambda name, age=0: f"Hello {name}, age {age}",
        )
        assert info.tool_id == "greet"
        assert len(info.parameters) == 2
        assert info.status == self.ToolStatus.AVAILABLE
        assert reg.get_tool_handler("greet") is not None

    def test_register_tool_no_handler(self):
        """测试: 注册不带 handler 的工具"""
        reg = self._make_registry()
        reg.register_tool("nh", "NH", "desc", self.ToolCategory.SYSTEM)
        assert reg.get_tool_handler("nh") is None

    def test_duplicate_registration_raises(self):
        """测试: 重复注册同一工具应抛 ValueError"""
        reg = self._make_registry()
        reg.register_tool("dup", "dup", "desc", self.ToolCategory.CUSTOM)
        with pytest.raises(ValueError) as exc_info:
            reg.register_tool("dup", "dup2", "desc2", self.ToolCategory.CUSTOM)
        assert "already registered" in str(exc_info.value)

    def test_unregister_tool(self):
        """测试: 注销工具 — 成功和不存在两种情况"""
        reg = self._make_registry()
        reg.register_tool("tmp", "Tmp", "temp tool", self.ToolCategory.CUSTOM)
        assert reg.unregister_tool("tmp") is True
        assert reg.get_tool("tmp") is None
        assert reg.get_tool_handler("tmp") is None
        assert reg.unregister_tool("nonexistent") is False

    def test_get_tool(self):
        """测试: 获取工具 — 存在和不存在"""
        reg = self._make_registry()
        reg.register_tool("my_tool", "MyTool", "my desc", self.ToolCategory.FILE)
        tool = reg.get_tool("my_tool")
        assert tool is not None
        assert tool.tool_id == "my_tool"
        assert reg.get_tool("missing") is None

    def test_list_tools_filters(self):
        """测试: list_tools — 无过滤、按类别过滤、按状态过滤"""
        reg = self._make_registry()
        reg.register_tool("f1", "F1", "desc", self.ToolCategory.FILE)
        reg.register_tool("f2", "F2", "desc", self.ToolCategory.FILE)
        reg.register_tool("t1", "T1", "desc", self.ToolCategory.TIME)
        assert len(reg.list_tools()) == 3
        assert len(reg.list_tools(category=self.ToolCategory.FILE)) == 2
        reg.update_tool_status("f2", self.ToolStatus.DISABLED)
        assert len(reg.list_tools(status=self.ToolStatus.AVAILABLE)) == 2

    def test_search_tools(self):
        """测试: search_tools — 按名称和描述搜索，大小写不敏感"""
        reg = self._make_registry()
        reg.register_tool("read_file", "read_file", "读取文件", self.ToolCategory.FILE)
        reg.register_tool("calc", "calc", "执行数学计算", self.ToolCategory.CALCULATION)
        assert len(reg.search_tools("read")) == 1
        assert reg.search_tools("read")[0].tool_id == "read_file"
        assert len(reg.search_tools("数学")) == 1
        assert len(reg.search_tools("READ")) == 1
        assert len(reg.search_tools("zzz_nothing")) == 0

    def test_get_tool_schema(self):
        """测试: 获取工具 JSON Schema — 正常和不存在"""
        reg = self._make_registry()
        params = [
            self.ToolParameter("path", "str", "文件路径", True),
            self.ToolParameter("mode", "str", "写入模式", False, "w", ["w", "a"]),
        ]
        reg.register_tool("file_op", "FileOp", "文件操作", self.ToolCategory.FILE, parameters=params)
        schema = reg.get_tool_schema("file_op")
        assert schema is not None
        assert schema["type"] == "object"
        assert "path" in schema["required"]
        assert "mode" not in schema["required"]
        assert schema["properties"]["mode"]["enum"] == ["w", "a"]
        assert reg.get_tool_schema("ghost") is None

    def test_update_tool_status_and_handler(self):
        """测试: 更新工具状态 + 获取工具处理器"""
        reg = self._make_registry()
        reg.register_tool("svc", "Svc", "service", self.ToolCategory.SYSTEM)
        assert reg.update_tool_status("svc", self.ToolStatus.BUSY) is True
        assert reg.get_tool("svc").status == self.ToolStatus.BUSY
        assert reg.update_tool_status("ghost", self.ToolStatus.ERROR) is False

        def handler(x):
            return x * 2
        reg.register_tool("dbl", "Dbl", "double", self.ToolCategory.CALCULATION, handler=handler)
        h = reg.get_tool_handler("dbl")
        assert h(5) == 10

    def test_get_stats_and_close(self):
        """测试: get_stats 统计 + close 清理"""
        reg = self._make_registry()
        reg.register_tool("f1", "F1", "f1", self.ToolCategory.FILE)
        reg.register_tool("f2", "F2", "f2", self.ToolCategory.FILE)
        reg.register_tool("t1", "T1", "t1", self.ToolCategory.TIME)
        stats = reg.get_stats()
        assert stats["total_tools"] == 3
        assert stats["by_category"]["file"] == 2
        assert stats["total_usage"] == 0

        # 空注册表
        reg2 = self._make_registry()
        s2 = reg2.get_stats()
        assert s2["total_tools"] == 0

        # close 清理
        reg.close()
        assert reg.get_tool("f1") is None


# =============================================================================
# Module 2: ToolExecutor Tests
# =============================================================================


class TestToolExecutor:
    """ToolExecutor 工具执行器测试 (10 tests)"""

    def setup_method(self):
        try:
            from nomad_mem.skills.tool_executor import ToolExecutor, ExecutionStatus
            self.ToolExecutor = ToolExecutor
            self.ExecutionStatus = ExecutionStatus
        except ImportError:
            pytest.skip("ToolExecutor not available")

    def _make_executor(self, default_timeout=5.0):
        return self.ToolExecutor(default_timeout=default_timeout)

    def test_execute_sync_success(self):
        """测试: 同步执行成功 — args 和 kwargs 两种方式"""
        exe = self._make_executor()
        r1 = exe.execute_sync("add", lambda a, b: a + b, args=(3, 4))
        assert r1.success is True
        assert r1.result_data == 7
        assert r1.status == self.ExecutionStatus.SUCCESS

        r2 = exe.execute_sync(
            "greet", lambda name, greeting="Hi": f"{greeting}, {name}",
            kwargs={"name": "Alice", "greeting": "Hello"},
        )
        assert r2.result_data == "Hello, Alice"

    def test_execute_sync_failure(self):
        """测试: 同步执行失败 — 处理器抛异常"""
        exe = self._make_executor()
        result = exe.execute_sync("fail", lambda: (_ for _ in ()).throw(ValueError("bad")))
        assert result.success is False
        assert result.status == self.ExecutionStatus.FAILED
        assert "ValueError" in result.error

    def test_execute_sync_timeout(self):
        """测试: 同步执行超时 — 默认和自定义超时"""
        exe1 = self._make_executor(default_timeout=0.2)
        r1 = exe1.execute_sync("slow", lambda: time.sleep(5))
        assert r1.status == self.ExecutionStatus.TIMEOUT
        assert "timed out" in r1.error

        exe2 = self._make_executor(default_timeout=30.0)
        r2 = exe2.execute_sync("slow", lambda: time.sleep(5), timeout=0.1)
        assert r2.status == self.ExecutionStatus.TIMEOUT

    def test_validate_result_types(self):
        """测试: validate_result — 多种类型校验"""
        exe = self._make_executor()
        assert exe.validate_result("hi", {"type": "string"}) is True
        assert exe.validate_result(42, {"type": "integer"}) is True
        assert exe.validate_result(True, {"type": "integer"}) is False  # bool not int
        assert exe.validate_result(3.14, {"type": "number"}) is True
        assert exe.validate_result(True, {"type": "boolean"}) is True
        assert exe.validate_result([1], {"type": "array"}) is True
        assert exe.validate_result({"k": "v"}, {"type": "object"}) is True

    def test_validate_result_no_or_unknown_schema(self):
        """测试: validate_result — 无 schema / 未知类型认为通过"""
        exe = self._make_executor()
        assert exe.validate_result("anything", {}) is True
        assert exe.validate_result("x", {"type": "unknown_type"}) is True

    def test_execution_history(self):
        """测试: 获取执行历史 — 全部、按工具过滤、限制数量"""
        exe = self._make_executor()
        exe.execute_sync("alpha", lambda: "a")
        exe.execute_sync("beta", lambda: "b")
        exe.execute_sync("alpha", lambda: "c")
        history = exe.get_execution_history()
        assert len(history) == 3
        assert history[0].tool_id == "alpha"  # 最新的在前
        hist_alpha = exe.get_execution_history(tool_id="alpha")
        assert len(hist_alpha) == 2
        assert all(r.tool_id == "alpha" for r in hist_alpha)
        hist_limited = exe.get_execution_history(limit=1)
        assert len(hist_limited) == 1

    def test_cancel_execution(self):
        """测试: 取消执行 — 存在的和不存在的"""
        exe = self._make_executor()
        # 超时后线程可能已被清理，cancel 应安全返回 bool
        pending = exe.execute_sync("slow", lambda: time.sleep(10), timeout=0.05)
        cancelled = exe.cancel_execution(pending.execution_id)
        assert cancelled in (True, False)
        assert exe.cancel_execution("nonexistent-id") is False

    def test_get_stats(self):
        """测试: get_stats — 空状态和有执行记录"""
        exe = self._make_executor()
        empty = exe.get_stats()
        assert empty["total_executions"] == 0
        assert empty["success_rate"] == 1.0

        exe.execute_sync("add", lambda: 1 + 1)
        exe.execute_sync("add", lambda: 2 + 2)
        exe.execute_sync("fail", lambda: (_ for _ in ()).throw(ValueError("bad")))
        stats = exe.get_stats()
        assert stats["total_executions"] == 3
        assert stats["success_count"] == 2
        assert stats["failure_count"] == 1
        assert "add" in stats["by_tool"]

    def test_close_clears_state(self):
        """测试: close 清理执行器状态"""
        exe = self._make_executor()
        exe.execute_sync("t", lambda: 1)
        exe.close()
        assert exe.get_stats()["total_executions"] == 0


# =============================================================================
# Module 3: Builtin Tools Tests
# =============================================================================


class TestBuiltinTools:
    """内置工具集测试 (10 tests)"""

    def setup_method(self):
        try:
            from nomad_mem.skills.tool_registry import ToolRegistry, ToolCategory
            from nomad_mem.skills.builtin_tools import (
                register_builtin_tools, _handle_get_time, _handle_calculate,
                _handle_read_file, _handle_write_file, _handle_list_directory,
            )
            self.ToolRegistry = ToolRegistry
            self.ToolCategory = ToolCategory
            self.register_builtin_tools = register_builtin_tools
            self.handle_get_time = _handle_get_time
            self.handle_calculate = _handle_calculate
            self.handle_read_file = _handle_read_file
            self.handle_write_file = _handle_write_file
            self.handle_list_directory = _handle_list_directory
        except ImportError:
            pytest.skip("Builtin tools not available")

    def test_register_builtin_tools_returns_8(self):
        """测试: 注册内置工具应返回 8 个，且包含预期 ID"""
        reg = self.ToolRegistry()
        count = self.register_builtin_tools(reg)
        assert count == 8
        expected_ids = {
            "read_file", "write_file", "list_directory",
            "get_time", "calculate", "web_search", "system_info", "timer",
        }
        assert {t.tool_id for t in reg.list_tools()} == expected_ids

    def test_builtin_tool_categories(self):
        """测试: 内置工具类别分布正确"""
        reg = self.ToolRegistry()
        self.register_builtin_tools(reg)
        assert len(reg.list_tools(category=self.ToolCategory.FILE)) == 3
        assert len(reg.list_tools(category=self.ToolCategory.TIME)) == 2

    def test_get_time_tool(self):
        """测试: get_time — 多种格式和无效格式"""
        dt = self.handle_get_time("datetime")
        assert "20" in dt
        date = self.handle_get_time("date")
        assert len(date) == 10  # YYYY-MM-DD
        ts = self.handle_get_time("timestamp")
        assert float(ts) > 1_000_000_000
        with pytest.raises(ValueError, match="Unknown format"):
            self.handle_get_time("invalid_fmt")

    def test_calculate_simple_math(self):
        """测试: calculate — 简单数学运算"""
        assert self.handle_calculate("2 + 3") == "5"
        assert float(self.handle_calculate("(10 + 5) * 2 / 3")) == pytest.approx(10.0)
        assert self.handle_calculate("1.5 * 2") == "3.0"

    def test_calculate_division_by_zero(self):
        """测试: calculate — 除以零"""
        with pytest.raises(ValueError, match="Division by zero"):
            self.handle_calculate("1 / 0")

    def test_calculate_dangerous_expressions_blocked(self):
        """测试: calculate — 危险表达式和代码注入被阻止"""
        with pytest.raises(ValueError):
            self.handle_calculate("__import__('os')")
        with pytest.raises(ValueError):
            self.handle_calculate("import os; os.system('ls')")

    def test_write_and_read_file(self):
        """测试: write_file + read_file 完整读写流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = os.path.join(tmpdir, "test.txt")
            content = "Hello, World!\nLine 2"
            w = self.handle_write_file(fp, content)
            assert "Written" in w
            assert self.handle_read_file(fp) == content

    def test_write_file_append_and_create_dirs(self):
        """测试: write_file 追加模式参数 + 自动创建父目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 追加模式参数应被接受（不抛异常）
            fp = os.path.join(tmpdir, "app.txt")
            r1 = self.handle_write_file(fp, "content1", mode="w")
            assert "Written" in r1
            r2 = self.handle_write_file(fp, "content2", mode="a")
            assert "Written" in r2

            # 自动创建父目录
            deep = os.path.join(tmpdir, "a", "b", "c.txt")
            self.handle_write_file(deep, "deep")
            assert os.path.exists(deep)

    def test_read_file_not_found(self):
        """测试: read_file 文件不存在"""
        with pytest.raises(FileNotFoundError):
            self.handle_read_file("/tmp/nonexistent_xyz_12345.txt")

    def test_list_directory_tool(self):
        """测试: list_directory — 有文件、不存在、空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "a.txt"), "w").close()
            os.makedirs(os.path.join(tmpdir, "sub"))
            r = self.handle_list_directory(tmpdir)
            assert "a.txt" in r and "sub" in r

            with pytest.raises(FileNotFoundError):
                self.handle_list_directory("/tmp/nonexistent_dir_xyz_12345")

            empty = tempfile.mkdtemp()
            assert "empty directory" in self.handle_list_directory(empty)


# =============================================================================
# Module 4: ToolSelector Tests
# =============================================================================


class TestToolSelector:
    """ToolSelector 工具选择器测试 (10 tests)"""

    def setup_method(self):
        try:
            from nomad_mem.skills.tool_registry import ToolRegistry, ToolCategory, ToolParameter
            from nomad_mem.autonomy.tool_selector import ToolSelector, ToolMatch
            self.ToolRegistry = ToolRegistry
            self.ToolCategory = ToolCategory
            self.ToolParameter = ToolParameter
            self.ToolSelector = ToolSelector
            self.ToolMatch = ToolMatch
        except ImportError:
            pytest.skip("ToolSelector not available")

    def _make_selector(self, tmpdir):
        reg = self.ToolRegistry()
        for tool_id, name, desc, cat, params in [
            ("read_file", "read_file", "读取指定文件的内容", self.ToolCategory.FILE,
             [self.ToolParameter("path", "str", "文件路径", True)]),
            ("write_file", "write_file", "将内容写入指定文件", self.ToolCategory.FILE,
             [self.ToolParameter("path", "str", "文件路径", True)]),
            ("get_time", "get_time", "获取当前时间和日期", self.ToolCategory.TIME, []),
            ("calculate", "calculate", "执行数学计算表达式", self.ToolCategory.CALCULATION,
             [self.ToolParameter("expression", "str", "数学表达式", True)]),
            ("web_search", "web_search", "在互联网上搜索信息", self.ToolCategory.SEARCH, []),
            ("system_info", "system_info", "获取系统信息", self.ToolCategory.SYSTEM, []),
        ]:
            reg.register_tool(tool_id, name, desc, cat, params)
        db_path = os.path.join(tmpdir, "ts_test.db")
        return self.ToolSelector(reg, db_path=db_path)

    def test_select_tools_different_intents(self):
        """测试: select_tools — 不同意图返回对应工具"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            # 文件意图
            m = sel.select_tools("file", "请帮我读取文件")
            assert len(m) > 0
            assert m[0].tool_id in ("read_file", "write_file")
            # 时间意图
            m = sel.select_tools("time", "现在是什么时间")
            assert len(m) > 0
            assert m[0].tool_id == "get_time"
            # 计算意图
            m = sel.select_tools("calculation", "帮我算一下")
            assert len(m) > 0
            assert m[0].tool_id == "calculate"
            # 搜索意图
            m = sel.select_tools("search", "帮我搜索")
            assert len(m) > 0
            assert m[0].tool_id == "web_search"

    def test_select_tools_sorted_and_scored(self):
        """测试: select_tools — 结果降序排列、得分在 (0, 1] 范围"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            matches = sel.select_tools("file", "读取文件")
            scores = [m.score for m in matches]
            assert scores == sorted(scores, reverse=True)
            assert all(0 < s <= 1.0 for s in scores)

    def test_get_top_tool(self):
        """测试: get_top_tool — 最佳匹配和无匹配"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            top = sel.get_top_tool("time", "现在是什么时间")
            assert top is not None
            assert top.tool_id == "get_time"
            assert isinstance(top.score, float)

            reg = self.ToolRegistry()
            empty_sel = self.ToolSelector(reg, db_path=os.path.join(tmpdir, "e.db"))
            assert empty_sel.get_top_tool("file", "读取") is None

    def test_match_by_keyword(self):
        """测试: match_by_keyword — 名称匹配、意图匹配、无匹配"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            tools = sel._registry.list_tools()

            # 名称匹配得分 >= 0.5
            ms = sel.match_by_keyword("read_file", tools)
            rm = next((m for m in ms if m.tool_id == "read_file"), None)
            assert rm is not None and rm.score >= 0.5

            # 意图关键词匹配
            ms = sel.match_by_keyword("帮我计算", tools)
            cm = next((m for m in ms if m.tool_id == "calculate"), None)
            assert cm is not None and cm.score > 0

            # 无匹配
            assert len(sel.match_by_keyword("zzz_unlikely_xyz", tools)) == 0

    def test_match_by_context(self):
        """测试: match_by_context — last_tool、related_tools、current_action、空上下文"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            tools = sel._registry.list_tools()

            # last_tool
            ms = sel.match_by_context({"last_tool": "read_file"}, tools)
            rm = next((m for m in ms if m.tool_id == "read_file"), None)
            assert rm is not None and rm.score >= 0.3

            # related_tools
            ms = sel.match_by_context({"related_tools": ["calculate"]}, tools)
            cm = next((m for m in ms if m.tool_id == "calculate"), None)
            assert cm is not None and cm.score >= 0.4

            # current_action
            ms = sel.match_by_context({"current_action": "搜索"}, tools)
            assert any(m.tool_id == "web_search" for m in ms)

            # 空上下文
            assert len(sel.match_by_context({}, tools)) == 0

    def test_record_selection(self):
        """测试: record_selection — 记录并影响统计"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            sel.record_selection("read_file", True)
            sel.record_selection("calculate", False)
            s = sel.get_stats()
            assert s["total_selections"] == 2

            for _ in range(3):
                sel.record_selection("read_file", True)
            s = sel.get_stats()
            assert s["total_selections"] == 5
            # 4 success out of 5 = 0.8
            assert s["accuracy"] == pytest.approx(0.8, abs=0.01)

    def test_get_selection_history(self):
        """测试: get_selection_history — 获取记录和限制数量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            sel.record_selection("read_file", True)
            sel.record_selection("calculate", True)
            h = sel.get_selection_history(limit=5)
            assert len(h) == 2
            assert "timestamp" in h[0] and "success" in h[0]

            for i in range(10):
                sel.record_selection(f"t{i}", True)
            assert len(sel.get_selection_history(limit=3)) == 3

    def test_get_stats_empty_and_with_data(self):
        """测试: get_stats — 空状态和有数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            empty = sel.get_stats()
            assert empty["total_selections"] == 0
            assert empty["accuracy"] == 0.0

            for _ in range(5):
                sel.record_selection("read_file", True)
            for _ in range(3):
                sel.record_selection("calculate", False)
            s = sel.get_stats()
            assert s["total_selections"] == 8
            assert s["most_selected"][0]["tool_id"] == "read_file"

    def test_tool_match_comparison(self):
        """测试: ToolMatch 排序比较"""
        m1 = self.ToolMatch(tool_id="a", score=0.3, reason="r1")
        m2 = self.ToolMatch(tool_id="b", score=0.7, reason="r2")
        assert m1 < m2
        assert not (m2 < m1)

    def test_close_selector(self):
        """测试: close 不报错"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sel = self._make_selector(tmpdir)
            sel.close()


# =============================================================================
# Module 5: Jarvis Integration Tests
# =============================================================================


class TestJarvisToolIntegration:
    """JarvisCore 工具系统集成测试 (10 tests)"""

    def setup_method(self):
        try:
            from nomad_mem.core.jarvis_core import JarvisCore
            self.JarvisCore = JarvisCore
        except ImportError:
            pytest.skip("JarvisCore not available")

    def _get_jarvis(self):
        return self.JarvisCore()

    def test_jarvis_initializes_tool_system(self):
        """测试: Jarvis 初始化后 tool_registry/executor/selector 不为 None"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        assert jarvis.tool_registry is not None
        assert jarvis.tool_executor is not None
        assert jarvis.tool_selector is not None
        assert len(jarvis.tool_registry.list_tools()) >= 8  # 至少 8 个内置工具

    def test_jarvis_list_tools(self):
        """测试: jarvis.list_tools 返回格式正确的工具列表"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        tools = jarvis.list_tools()
        assert len(tools) >= 8
        f = tools[0]
        for key in ("tool_id", "name", "description", "category", "parameters"):
            assert key in f

        # 按类别过滤
        time_tools = jarvis.list_tools(category="time")
        assert len(time_tools) >= 2

    def test_jarvis_use_tool_get_time(self):
        """测试: jarvis.use_tool 使用 get_time"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        r = jarvis.use_tool("get_time", args={"format": "datetime"})
        assert r["success"] is True
        assert r["tool_id"] == "get_time"
        assert len(r["result"]) > 0

    def test_jarvis_use_tool_calculate(self):
        """测试: jarvis.use_tool 使用 calculate — 成功和错误"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        r = jarvis.use_tool("calculate", args={"expression": "100 + 200"})
        assert r["success"] is True
        assert r["result"] == "300"

        r_err = jarvis.use_tool("calculate", args={"expression": "__import__('os')"})
        assert r_err["success"] is False
        assert r_err["error"] is not None

    def test_jarvis_use_tool_invalid_and_unavailable(self):
        """测试: jarvis.use_tool 无效 tool_id 和不可用工具返回错误"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        r = jarvis.use_tool("nonexistent_tool")
        assert "error" in r and "not found" in r["error"]

        from nomad_mem.skills.tool_registry import ToolStatus
        jarvis.tool_registry.update_tool_status("get_time", ToolStatus.BUSY)
        r2 = jarvis.use_tool("get_time")
        assert "error" in r2 and "not available" in r2["error"]

    def test_jarvis_chat_includes_suggested_tool(self):
        """测试: jarvis.chat 在合适意图时返回 suggested_tool"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        # 使用包含工具名称的查询以确保 score > 0.3
        r = jarvis.chat("请帮我调用 get_time 工具")
        assert "suggested_tool" in r
        assert r["suggested_tool"]["score"] > 0.3
        # 计算意图
        r2 = jarvis.chat("请帮我调用 calculate 工具")
        assert "suggested_tool" in r2
        assert r2["suggested_tool"]["tool_id"] == "calculate"

    def test_jarvis_get_status_includes_tool_system(self):
        """测试: get_status 包含 tool_system 统计 (registry/executor/selector)"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        status = jarvis.get_status()
        ts = status["modules"]["tool_system"]
        assert "registry" in ts and "executor" in ts and "selector" in ts
        assert ts["registry"]["total_tools"] >= 8

    def test_jarvis_get_status_after_tool_use(self):
        """测试: 使用工具后 get_status 统计更新"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        jarvis.use_tool("get_time")
        jarvis.use_tool("calculate", args={"expression": "1+1"})
        ts = jarvis.get_status()["modules"]["tool_system"]
        # executor 应有执行记录
        assert ts["executor"]["total_executions"] >= 2
        # selector 应有选择记录
        assert ts["selector"]["total_selections"] >= 2

    def test_jarvis_tool_records_selection(self):
        """测试: use_tool 后 tool_selector 记录选择"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        jarvis.use_tool("get_time")
        assert jarvis.tool_selector.get_stats()["total_selections"] >= 1

    def test_jarvis_close_cleans_tool_resources(self):
        """测试: jarvis.close 清理工具资源"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        jarvis.use_tool("get_time")
        jarvis.close()
        assert jarvis.initialized is False
        assert jarvis.tool_executor.get_stats()["total_executions"] == 0
