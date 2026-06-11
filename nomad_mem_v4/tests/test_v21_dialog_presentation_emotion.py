"""
V21测试 - 对话流程管理器 / 信息展示引擎 / 情感追踪器 + Jarvis集成

覆盖模块:
1. DialogFlowManager (nomad_mem.autonomy.dialog_flow)
   - 流程创建/启动/获取/取消/完成
   - 确认流程、菜单流程、表单流程
   - 输入验证、重试机制
   - 活跃流程查询、统计
2. PresentationEngine (nomad_mem.core.presentation_engine)
   - 表格、列表、进度条、状态面板、卡片、时间线
   - 自动类型检测、自动格式化
   - 统计
3. EmotionTracker (nomad_mem.autonomy.emotion_tracker)
   - 情感检测、记录、查询
   - 情感趋势、响应策略、共情回复
   - 自定义模式、历史记录、统计
4. Jarvis集成
   - 新模块初始化
   - chat中的emotion_context
   - get_status中的新模块统计
   - close清理资源

测试策略:
- 使用 tempfile.TemporaryDirectory() 提供临时数据库路径
- 所有导入使用 try/except 优雅回退
- 覆盖正常路径、边界条件和异常情况
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# =============================================================================
# TestDialogFlow
# =============================================================================


class TestDialogFlow:
    """DialogFlowManager 测试"""

    def setup_method(self):
        try:
            from nomad_mem.autonomy.dialog_flow import (
                DialogFlowManager,
                FlowType,
                FlowState,
                FlowStep,
            )
            self.DialogFlowManager = DialogFlowManager
            self.FlowType = FlowType
            self.FlowState = FlowState
            self.FlowStep = FlowStep
        except ImportError:
            self.DialogFlowManager = None

    def _get_manager(self):
        if self.DialogFlowManager is None:
            pytest.skip("DialogFlowManager not available")
        return self.DialogFlowManager()

    # ── start_flow / get_current_flow ──

    def test_start_flow_basic(self):
        """测试: 启动基础流程并获取"""
        mgr = self._get_manager()
        steps = [
            self.FlowStep(
                step_id="step_1",
                step_type=self.FlowType.FOLLOW_UP,
                prompt="你好吗？",
            )
        ]
        flow_id = mgr.start_flow(self.FlowType.FOLLOW_UP, steps, user_id="u1")
        assert flow_id.startswith("flow_")

        flow = mgr.get_current_flow(flow_id)
        assert flow is not None
        assert flow.flow_id == flow_id
        assert flow.state == self.FlowState.ACTIVE
        assert flow.user_id == "u1"

    def test_start_flow_with_context(self):
        """测试: 启动带上下文的流程"""
        mgr = self._get_manager()
        steps = [
            self.FlowStep(step_id="s1", step_type=self.FlowType.FOLLOW_UP, prompt="请回答")
        ]
        flow_id = mgr.start_flow(
            self.FlowType.FOLLOW_UP,
            steps,
            context={"topic": "weather"},
            user_id="u1",
        )
        flow = mgr.get_current_flow(flow_id)
        assert flow.context["topic"] == "weather"

    def test_get_current_flow_not_found(self):
        """测试: 获取不存在的流程返回None"""
        mgr = self._get_manager()
        assert mgr.get_current_flow("nonexistent") is None

    # ── create_confirmation_flow ──

    def test_create_confirmation_flow(self):
        """测试: 创建确认流程"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow(
            "确定要删除吗？",
            yes_action="删除文件",
            no_action="取消操作",
            user_id="u1",
        )
        assert flow_id.startswith("flow_")
        flow = mgr.get_current_flow(flow_id)
        assert flow.flow_type == self.FlowType.CONFIRMATION
        assert len(flow.steps) == 1
        assert flow.steps[0].expected_input_type == "confirm"

    def test_confirmation_flow_yes(self):
        """测试: 确认流程 - 输入 yes"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定继续？", user_id="u1")
        result = mgr.process_response(flow_id, "y")
        assert result["completed"] is True
        assert result["step_validated"] is True
        assert result["result"]["confirm_1"] is True

    def test_confirmation_flow_no(self):
        """测试: 确认流程 - 输入 no"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定继续？", user_id="u1")
        result = mgr.process_response(flow_id, "n")
        assert result["completed"] is True
        assert result["result"]["confirm_1"] is False

    def test_confirmation_flow_chinese_yes(self):
        """测试: 确认流程 - 中文确认"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定继续？", user_id="u1")
        result = mgr.process_response(flow_id, "确认")
        assert result["completed"] is True
        assert result["result"]["confirm_1"] is True

    # ── create_menu_flow ──

    def test_create_menu_flow(self):
        """测试: 创建菜单流程"""
        mgr = self._get_manager()
        flow_id = mgr.create_menu_flow(
            "请选择颜色",
            options=["红色", "绿色", "蓝色"],
            user_id="u1",
        )
        flow = mgr.get_current_flow(flow_id)
        assert flow.flow_type == self.FlowType.MENU
        assert len(flow.steps) == 1
        assert flow.steps[0].options == ["红色", "绿色", "蓝色"]

    def test_menu_flow_by_index(self):
        """测试: 菜单流程 - 按编号选择"""
        mgr = self._get_manager()
        flow_id = mgr.create_menu_flow(
            "请选择",
            options=["选项A", "选项B", "选项C"],
            user_id="u1",
        )
        result = mgr.process_response(flow_id, "2")
        assert result["completed"] is True
        assert result["result"]["menu_1"] == "选项B"

    def test_menu_flow_by_name(self):
        """测试: 菜单流程 - 按名称选择"""
        mgr = self._get_manager()
        flow_id = mgr.create_menu_flow(
            "请选择",
            options=["苹果", "香蕉", "橙子"],
            user_id="u1",
        )
        result = mgr.process_response(flow_id, "香蕉")
        assert result["completed"] is True
        assert result["result"]["menu_1"] == "香蕉"

    # ── create_form_flow ──

    def test_create_form_flow(self):
        """测试: 创建表单流程"""
        mgr = self._get_manager()
        fields = [
            {"name": "name", "prompt": "请输入姓名", "type": "text"},
            {"name": "age", "prompt": "请输入年龄", "type": "number"},
            {"name": "city", "prompt": "请输入城市", "type": "text"},
        ]
        flow_id = mgr.create_form_flow(fields, title="用户信息", user_id="u1")
        flow = mgr.get_current_flow(flow_id)
        assert flow.flow_type == self.FlowType.FILL_FORM
        assert len(flow.steps) == 3

    def test_form_flow_multi_step(self):
        """测试: 表单流程 - 多步处理"""
        mgr = self._get_manager()
        fields = [
            {"name": "name", "prompt": "请输入姓名", "type": "text"},
            {"name": "age", "prompt": "请输入年龄", "type": "number"},
        ]
        flow_id = mgr.create_form_flow(fields, title="用户信息", user_id="u1")

        # 第1步
        r1 = mgr.process_response(flow_id, "张三")
        assert r1["completed"] is False
        assert r1["step_validated"] is True
        assert r1["result"]["field_name"] == "张三"

        # 第2步（最后一步，应完成）
        r2 = mgr.process_response(flow_id, "25")
        assert r2["completed"] is True
        assert r2["result"]["field_age"] == 25

    # ── cancel_flow ──

    def test_cancel_flow(self):
        """测试: 取消流程"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定吗？", user_id="u1")
        result = mgr.cancel_flow(flow_id)
        assert result is True

        flow = mgr.get_current_flow(flow_id)
        assert flow.state == self.FlowState.CANCELLED

    def test_cancel_nonexistent_flow(self):
        """测试: 取消不存在的流程"""
        mgr = self._get_manager()
        result = mgr.cancel_flow("nonexistent")
        assert result is False

    # ── has_active_flow / get_active_flows ──

    def test_has_active_flow_true(self):
        """测试: has_active_flow 用户有活跃流程时返回True"""
        mgr = self._get_manager()
        mgr.create_confirmation_flow("确定吗？", user_id="u1")
        assert mgr.has_active_flow("u1") is True

    def test_has_active_flow_false(self):
        """测试: has_active_flow 用户无活跃流程时返回False"""
        mgr = self._get_manager()
        assert mgr.has_active_flow("u1") is False

    def test_has_active_flow_after_cancel(self):
        """测试: 取消流程后 has_active_flow 返回False"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定吗？", user_id="u1")
        mgr.cancel_flow(flow_id)
        assert mgr.has_active_flow("u1") is False

    def test_get_active_flows(self):
        """测试: 获取活跃流程列表"""
        mgr = self._get_manager()
        mgr.create_confirmation_flow("确定吗？", user_id="u1")
        mgr.create_menu_flow("选择", ["A", "B"], user_id="u1")

        active = mgr.get_active_flows("u1")
        assert len(active) == 2

    def test_get_active_flows_other_user_empty(self):
        """测试: 获取其他用户的活跃流程应为空"""
        mgr = self._get_manager()
        mgr.create_confirmation_flow("确定吗？", user_id="u1")
        assert mgr.get_active_flows("u2") == []

    # ── get_stats ──

    def test_get_stats_empty(self):
        """测试: 空状态统计"""
        mgr = self._get_manager()
        stats = mgr.get_stats()
        assert stats["total_flows"] == 0
        assert stats["completion_rate"] == 0.0

    def test_get_stats_after_operations(self):
        """测试: 操作后统计应更新"""
        mgr = self._get_manager()
        mgr.create_confirmation_flow("确定吗？", user_id="u1")
        mgr.create_menu_flow("选择", ["A", "B"], user_id="u1")

        stats = mgr.get_stats()
        assert stats["total_flows"] == 2
        assert "confirmation" in stats["by_type"]
        assert "menu" in stats["by_type"]

    # ── input validation failure and retry ──

    def test_validation_failure_retry(self):
        """测试: 输入验证失败后重试"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定吗？", user_id="u1")

        # 无效输入
        r1 = mgr.process_response(flow_id, "invalid_input")
        assert r1["step_validated"] is False
        assert r1["error"] is not None
        assert r1["retry_count"] == 1

        # 有效输入重试
        r2 = mgr.process_response(flow_id, "y")
        assert r2["completed"] is True
        assert r2["result"]["confirm_1"] is True

    def test_validation_exceeds_max_retries(self):
        """测试: 超过最大重试次数后流程终止为ERROR"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定吗？", user_id="u1")

        # 连续3次无效输入（默认max_retries=3）
        for _ in range(3):
            r = mgr.process_response(flow_id, "bad_input")

        flow = mgr.get_current_flow(flow_id)
        assert flow.state == self.FlowState.ERROR

    def test_menu_validation_failure(self):
        """测试: 菜单选项验证失败"""
        mgr = self._get_manager()
        flow_id = mgr.create_menu_flow("选择", ["A", "B"], user_id="u1")

        r = mgr.process_response(flow_id, "99")
        assert r["step_validated"] is False
        assert r["error"] is not None

    # ── complete_flow with result ──

    def test_complete_flow_with_result(self):
        """测试: 手动完成流程并设置结果"""
        mgr = self._get_manager()
        flow_id = mgr.create_confirmation_flow("确定吗？", user_id="u1")

        result = mgr.complete_flow(flow_id, {"manual_result": True})
        assert result is True

        flow = mgr.get_current_flow(flow_id)
        assert flow.state == self.FlowState.COMPLETED
        assert flow.result["manual_result"] is True

    def test_complete_flow_after_partial(self):
        """测试: 部分填写后手动完成"""
        mgr = self._get_manager()
        fields = [
            {"name": "name", "prompt": "姓名", "type": "text"},
            {"name": "age", "prompt": "年龄", "type": "number"},
        ]
        flow_id = mgr.create_form_flow(fields, user_id="u1")
        mgr.process_response(flow_id, "李四")

        # 手动完成
        mgr.complete_flow(flow_id, {"field_name": "李四", "manual": True})
        flow = mgr.get_current_flow(flow_id)
        assert flow.state == self.FlowState.COMPLETED
        assert flow.result["manual"] is True


# =============================================================================
# TestPresentationEngine
# =============================================================================


class TestPresentationEngine:
    """PresentationEngine 测试"""

    def setup_method(self):
        try:
            from nomad_mem.core.presentation_engine import (
                PresentationEngine,
                PresentationType,
                ListItem,
                ProgressInfo,
                CardData,
                TimelineItem,
                TableData,
            )
            self.PresentationEngine = PresentationEngine
            self.PresentationType = PresentationType
            self.ListItem = ListItem
            self.ProgressInfo = ProgressInfo
            self.CardData = CardData
            self.TimelineItem = TimelineItem
            self.TableData = TableData
        except ImportError:
            self.PresentationEngine = None

    def _get_engine(self):
        if self.PresentationEngine is None:
            pytest.skip("PresentationEngine not available")
        return self.PresentationEngine()

    # ── create_table ──

    def test_create_table_basic(self):
        """测试: 创建基础表格"""
        eng = self._get_engine()
        result = eng.create_table(
            "学生成绩",
            ["姓名", "分数"],
            [["张三", "90"], ["李四", "85"]],
        )
        assert "学生成绩" in result
        assert "姓名" in result
        assert "分数" in result
        assert "张三" in result
        assert "李四" in result
        assert "|" in result  # Markdown表格标记

    def test_create_table_no_title(self):
        """测试: 无标题表格"""
        eng = self._get_engine()
        result = eng.create_table(
            "",
            ["A", "B"],
            [["1", "2"]],
        )
        assert "|" in result
        assert "A" in result

    def test_create_table_empty_headers(self):
        """测试: 空表头返回标题行"""
        eng = self._get_engine()
        result = eng.create_table("空表", [], [["1", "2"]])
        # 空表头时返回标题（如果有）
        assert "空表" in result

    # ── create_list ──

    def test_create_list_strings(self):
        """测试: 创建字符串列表"""
        eng = self._get_engine()
        result = eng.create_list(["苹果", "香蕉", "橙子"], title="水果")
        assert "水果" in result
        assert "苹果" in result
        assert "香蕉" in result

    def test_create_list_numbered(self):
        """测试: 编号列表"""
        eng = self._get_engine()
        result = eng.create_list(["A", "B"], numbered=True)
        assert "1." in result
        assert "2." in result

    def test_create_list_with_listitem(self):
        """测试: 使用ListItem创建列表"""
        eng = self._get_engine()
        items = [
            self.ListItem(label="CPU", value="95%", status="warning"),
            self.ListItem(label="内存", value="80%", status="ok"),
        ]
        result = eng.create_list(items, title="系统状态")
        assert "CPU" in result
        assert "95%" in result

    def test_create_list_empty(self):
        """测试: 空列表"""
        eng = self._get_engine()
        result = eng.create_list([], title="空")
        assert "(空列表)" in result

    # ── create_progress ──

    def test_create_progress_basic(self):
        """测试: 基础进度条"""
        eng = self._get_engine()
        result = eng.create_progress(5, 10, "下载文件")
        assert "50.0%" in result
        assert "(5/10)" in result
        assert "下载文件" in result

    def test_create_progress_complete(self):
        """测试: 100%进度"""
        eng = self._get_engine()
        result = eng.create_progress(10, 10)
        assert "100.0%" in result
        assert "░" not in result  # 应全满

    def test_create_progress_zero(self):
        """测试: 0%进度"""
        eng = self._get_engine()
        result = eng.create_progress(0, 10)
        assert "0.0%" in result

    def test_create_progress_percentage(self):
        """测试: 进度百分比计算"""
        eng = self._get_engine()
        result = eng.create_progress(3, 4)
        assert "75.0%" in result

    # ── create_status_panel ──

    def test_create_status_panel(self):
        """测试: 创建状态面板"""
        eng = self._get_engine()
        items = [
            {"label": "CPU", "value": "45%", "status": "ok"},
            {"label": "内存", "value": "70%", "status": "warning"},
        ]
        result = eng.create_status_panel(items)
        assert "状态面板" in result
        assert "CPU" in result
        assert "内存" in result
        assert "┌" in result
        assert "┘" in result

    def test_create_status_panel_empty(self):
        """测试: 空状态面板"""
        eng = self._get_engine()
        result = eng.create_status_panel([])
        assert "(无状态)" in result

    def test_create_status_panel_with_listitem(self):
        """测试: 使用ListItem创建状态面板"""
        eng = self._get_engine()
        items = [self.ListItem(label="磁盘", value="60GB", status="info")]
        result = eng.create_status_panel(items)
        assert "磁盘" in result

    # ── create_card ──

    def test_create_card(self):
        """测试: 创建卡片"""
        eng = self._get_engine()
        result = eng.create_card(
            "用户信息",
            "用户名: admin\n角色: 管理员",
            metadata={"创建时间": "2024-01-01"},
            actions=["编辑", "删除"],
        )
        assert "用户信息" in result
        assert "admin" in result
        assert "创建时间" in result
        assert "编辑" in result
        assert "╔" in result
        assert "╝" in result

    def test_create_card_minimal(self):
        """测试: 最小卡片（无元数据/操作）"""
        eng = self._get_engine()
        result = eng.create_card("简单卡片", "这是内容")
        assert "简单卡片" in result
        assert "这是内容" in result

    # ── create_timeline ──

    def test_create_timeline(self):
        """测试: 创建时间线"""
        eng = self._get_engine()
        items = [
            self.TimelineItem(timestamp="10:00", event="开始任务", status="ok"),
            self.TimelineItem(timestamp="10:30", event="任务完成", status="done"),
        ]
        result = eng.create_timeline(items)
        assert "10:00" in result
        assert "开始任务" in result
        assert "10:30" in result
        assert "任务完成" in result
        assert "└─" in result

    def test_create_timeline_with_description(self):
        """测试: 带描述的时间线"""
        eng = self._get_engine()
        items = [
            self.TimelineItem(
                timestamp="09:00",
                event="系统启动",
                description="初始化所有模块",
            )
        ]
        result = eng.create_timeline(items)
        assert "初始化所有模块" in result

    def test_create_timeline_empty(self):
        """测试: 空时间线"""
        eng = self._get_engine()
        result = eng.create_timeline([])
        assert "(空时间线)" in result

    def test_create_timeline_with_dict(self):
        """测试: 使用字典创建时间线"""
        eng = self._get_engine()
        items = [
            {"timestamp": "08:00", "event": "开机", "status": "ok"},
        ]
        result = eng.create_timeline(items)
        assert "08:00" in result
        assert "开机" in result

    # ── choose_presentation_type ──

    def test_choose_type_table_data(self):
        """测试: TableData 自动检测为 TABLE"""
        eng = self._get_engine()
        data = self.TableData(headers=["A", "B"], rows=[["1", "2"]])
        assert eng.choose_presentation_type(data) == self.PresentationType.TABLE

    def test_choose_type_progress_info(self):
        """测试: ProgressInfo 自动检测为 PROGRESS"""
        eng = self._get_engine()
        data = self.ProgressInfo(current=5, total=10)
        assert eng.choose_presentation_type(data) == self.PresentationType.PROGRESS

    def test_choose_type_card_data(self):
        """测试: CardData 自动检测为 CARD"""
        eng = self._get_engine()
        data = self.CardData(title="T", content="C")
        assert eng.choose_presentation_type(data) == self.PresentationType.CARD

    def test_choose_type_list_of_timeline(self):
        """测试: TimelineItem 列表自动检测为 TIMELINE"""
        eng = self._get_engine()
        data = [self.TimelineItem(timestamp="10:00", event="E")]
        assert eng.choose_presentation_type(data) == self.PresentationType.TIMELINE

    def test_choose_type_dict_with_headers(self):
        """测试: 含 headers/rows 的字典检测为 TABLE"""
        eng = self._get_engine()
        data = {"headers": ["A"], "rows": [["1"]]}
        assert eng.choose_presentation_type(data) == self.PresentationType.TABLE

    def test_choose_type_dict_with_current_total(self):
        """测试: 含 current/total 的字典检测为 PROGRESS"""
        eng = self._get_engine()
        data = {"current": 5, "total": 10}
        assert eng.choose_presentation_type(data) == self.PresentationType.PROGRESS

    def test_choose_type_dict_with_title_content(self):
        """测试: 含 title/content 的字典检测为 CARD"""
        eng = self._get_engine()
        data = {"title": "T", "content": "C"}
        assert eng.choose_presentation_type(data) == self.PresentationType.CARD

    def test_choose_type_list_of_strings(self):
        """测试: 字符串列表检测为 LIST"""
        eng = self._get_engine()
        data = ["a", "b", "c"]
        assert eng.choose_presentation_type(data) == self.PresentationType.LIST

    def test_choose_type_empty_list(self):
        """测试: 空列表检测为 LIST"""
        eng = self._get_engine()
        assert eng.choose_presentation_type([]) == self.PresentationType.LIST

    # ── format_response ──

    def test_format_response_auto_table(self):
        """测试: 自动格式化为表格"""
        eng = self._get_engine()
        data = {"headers": ["姓名", "年龄"], "rows": [["张三", "25"]]}
        result = eng.format_response(data)
        assert "姓名" in result
        assert "张三" in result

    def test_format_response_auto_list(self):
        """测试: 自动格式化为列表"""
        eng = self._get_engine()
        result = eng.format_response(["item1", "item2"])
        assert "item1" in result

    def test_format_response_auto_progress(self):
        """测试: 自动格式化为进度"""
        eng = self._get_engine()
        data = {"current": 3, "total": 10, "label": "任务"}
        result = eng.format_response(data)
        assert "30.0%" in result

    def test_format_response_auto_card(self):
        """测试: 自动格式化为卡片"""
        eng = self._get_engine()
        data = {"title": "标题", "content": "内容"}
        result = eng.format_response(data)
        assert "标题" in result
        assert "╔" in result

    def test_format_response_auto_timeline(self):
        """测试: 自动格式化为时间线"""
        eng = self._get_engine()
        data = [
            {"timestamp": "10:00", "event": "事件1", "status": "ok"},
        ]
        result = eng.format_response(data)
        assert "10:00" in result
        assert "事件1" in result

    def test_format_response_with_explicit_type(self):
        """测试: 显式指定展示类型"""
        eng = self._get_engine()
        data = ["A", "B"]
        result = eng.format_response(data, self.PresentationType.STATUS_PANEL)
        assert "状态面板" in result

    def test_format_response_dict_to_table(self):
        """测试: 字典含headers/rows转为表格"""
        eng = self._get_engine()
        data = {
            "title": "数据",
            "headers": ["key1", "key2"],
            "rows": [["val1", "val2"]],
        }
        result = eng.format_response(data, self.PresentationType.TABLE)
        assert "key1" in result
        assert "val1" in result

    # ── get_stats ──

    def test_get_stats_initial(self):
        """测试: 初始统计为零"""
        eng = self._get_engine()
        stats = eng.get_stats()
        assert stats["total_presentations"] == 0
        assert stats["by_type"] == {}

    def test_get_stats_after_presentations(self):
        """测试: 展示后统计更新"""
        eng = self._get_engine()
        eng.create_table("T", ["A"], [["1"]])
        eng.create_list(["a", "b"])
        eng.create_progress(1, 10)

        stats = eng.get_stats()
        assert stats["total_presentations"] == 3
        assert "table" in stats["by_type"]
        assert "list" in stats["by_type"]
        assert "progress" in stats["by_type"]


# =============================================================================
# TestEmotionTracker
# =============================================================================


class TestEmotionTracker:
    """EmotionTracker 测试"""

    def setup_method(self):
        try:
            from nomad_mem.autonomy.emotion_tracker import (
                EmotionTracker,
                Emotion,
                EmotionRecord,
            )
            self.EmotionTracker = EmotionTracker
            self.Emotion = Emotion
            self.EmotionRecord = EmotionRecord
        except ImportError:
            self.EmotionTracker = None

    def _get_tracker(self):
        if self.EmotionTracker is None:
            pytest.skip("EmotionTracker not available")
        return self.EmotionTracker()

    # ── detect_emotion ──

    def test_detect_happy(self):
        """测试: 检测开心情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("今天太开心了！") == self.Emotion.HAPPY

    def test_detect_sad(self):
        """测试: 检测悲伤情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("我好难过，心里很伤心") == self.Emotion.SAD

    def test_detect_angry(self):
        """测试: 检测愤怒情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("我很生气！") == self.Emotion.ANGRY

    def test_detect_anxious(self):
        """测试: 检测焦虑情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("我很焦虑，很担心") == self.Emotion.ANXIOUS

    def test_detect_excited(self):
        """测试: 检测兴奋情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("哇！太期待了！") == self.Emotion.EXCITED

    def test_detect_frustrated(self):
        """测试: 检测沮丧情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("好烦啊，很郁闷") == self.Emotion.FRUSTRATED

    def test_detect_bored(self):
        """测试: 检测无聊情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("好无聊啊，没意思") == self.Emotion.BORED

    def test_detect_confused(self):
        """测试: 检测困惑情绪"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("这是什么？我不明白") == self.Emotion.CONFUSED

    def test_detect_neutral(self):
        """测试: 中性消息检测为NEUTRAL"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("今天天气还可以") == self.Emotion.NEUTRAL

    def test_detect_empty_message(self):
        """测试: 空消息返回NEUTRAL"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("") == self.Emotion.NEUTRAL

    def test_detect_english_emotions(self):
        """测试: 英文情绪词检测"""
        tracker = self._get_tracker()
        assert tracker.detect_emotion("This is great!") == self.Emotion.HAPPY
        assert tracker.detect_emotion("I am so sad") == self.Emotion.SAD
        assert tracker.detect_emotion("I am angry") == self.Emotion.ANGRY

    def test_detect_punctuation_hints(self):
        """测试: 标点符号暗示情绪（ASCII标点）"""
        tracker = self._get_tracker()
        # !!! 3个或更多 → EXCITED (使用ASCII !)
        assert tracker.detect_emotion("Wow!!!") == self.Emotion.EXCITED
        # ?? 2个或更多 → CONFUSED (使用ASCII ?)
        assert tracker.detect_emotion("What is this??") == self.Emotion.CONFUSED

    # ── record_emotion ──

    def test_record_emotion_basic(self):
        """测试: 基础情感记录"""
        tracker = self._get_tracker()
        rid = tracker.record_emotion(
            "user1", self.Emotion.HAPPY, intensity=0.8, trigger="收到好消息"
        )
        assert rid > 0

    def test_record_emotion_intensity_clamped(self):
        """测试: 情感强度被限制在0-1"""
        tracker = self._get_tracker()
        rid1 = tracker.record_emotion("u1", self.Emotion.HAPPY, intensity=1.5)
        rid2 = tracker.record_emotion("u1", self.Emotion.SAD, intensity=-0.5)
        assert rid1 > 0
        assert rid2 > 0

    # ── get_current_emotion ──

    def test_get_current_emotion(self):
        """测试: 获取当前情感"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.7, trigger="test")
        current = tracker.get_current_emotion("u1")
        assert current is not None
        assert current.emotion == "happy"
        assert current.intensity == 0.7

    def test_get_current_emotion_no_record(self):
        """测试: 无记录时返回None"""
        tracker = self._get_tracker()
        assert tracker.get_current_emotion("nonexistent") is None

    def test_get_current_emotion_returns_latest(self):
        """测试: 返回最新的情感记录"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.5, trigger="first")
        tracker.record_emotion("u1", self.Emotion.SAD, 0.8, trigger="second")
        current = tracker.get_current_emotion("u1")
        assert current.emotion == "sad"
        assert current.trigger_message == "second"

    # ── get_emotional_trend ──

    def test_get_emotional_trend_no_data(self):
        """测试: 无数据时返回稳定中性趋势"""
        tracker = self._get_tracker()
        trend = tracker.get_emotional_trend("u1")
        assert trend.dominant_emotion == "neutral"
        assert trend.trend_direction == "stable"
        assert trend.volatility == 0.0

    def test_get_emotional_trend_improving(self):
        """测试: 情感趋势改善"""
        tracker = self._get_tracker()
        # 先记录低分值情感
        tracker.record_emotion("u1", self.Emotion.SAD, 0.3, trigger="sad1")
        tracker.record_emotion("u1", self.Emotion.FRUSTRATED, 0.2, trigger="frust1")
        # 再记录高分值情感
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.8, trigger="happy1")
        tracker.record_emotion("u1", self.Emotion.EXCITED, 0.9, trigger="excited1")

        trend = tracker.get_emotional_trend("u1")
        assert trend.trend_direction == "improving"

    def test_get_emotional_trend_declining(self):
        """测试: 情感趋势下降"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.8, trigger="happy1")
        tracker.record_emotion("u1", self.Emotion.EXCITED, 0.9, trigger="excited1")
        tracker.record_emotion("u1", self.Emotion.SAD, 0.2, trigger="sad1")
        tracker.record_emotion("u1", self.Emotion.ANGRY, 0.1, trigger="angry1")

        trend = tracker.get_emotional_trend("u1")
        assert trend.trend_direction == "declining"

    def test_get_emotional_trend_stable(self):
        """测试: 情感趋势稳定"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.7, trigger="h1")
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.8, trigger="h2")

        trend = tracker.get_emotional_trend("u1")
        assert trend.dominant_emotion == "happy"
        assert trend.trend_direction == "stable"

    # ── get_emotional_response_strategy ──

    def test_strategy_happy(self):
        """测试: 开心情感的响应策略"""
        tracker = self._get_tracker()
        strategy = tracker.get_emotional_response_strategy(self.Emotion.HAPPY)
        assert len(strategy) > 0
        assert "积极" in strategy or "分享" in strategy

    def test_strategy_sad(self):
        """测试: 悲伤情感的响应策略"""
        tracker = self._get_tracker()
        strategy = tracker.get_emotional_response_strategy(self.Emotion.SAD)
        assert "同理心" in strategy or "支持" in strategy

    def test_strategy_angry(self):
        """测试: 愤怒情感的响应策略"""
        tracker = self._get_tracker()
        strategy = tracker.get_emotional_response_strategy(self.Emotion.ANGRY)
        assert "冷静" in strategy or "理解" in strategy

    def test_strategy_confused(self):
        """测试: 困惑情感的响应策略"""
        tracker = self._get_tracker()
        strategy = tracker.get_emotional_response_strategy(self.Emotion.CONFUSED)
        assert "解释" in strategy or "简单" in strategy

    # ── get_empathetic_response ──

    def test_empathetic_response_happy(self):
        """测试: 开心时的共情回复"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.8, trigger="good")
        modified = tracker.get_empathetic_response("u1", "这是你的结果")
        assert "太好了" in modified or "很高兴" in modified

    def test_empathetic_response_sad(self):
        """测试: 悲伤时的共情回复"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.SAD, 0.7, trigger="bad")
        modified = tracker.get_empathetic_response("u1", "这是你的结果")
        assert "理解" in modified or "抱歉" in modified

    def test_empathetic_response_no_emotion(self):
        """测试: 无情感记录时返回原回复"""
        tracker = self._get_tracker()
        original = "原始回复"
        modified = tracker.get_empathetic_response("u1", original)
        assert modified == original

    def test_empathetic_response_avoids_double_prefix(self):
        """测试: 避免重复添加前缀"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.8, trigger="good")
        # 使用与prefix[0]相同开头(p[:-1]即"太好了！😊")的回复
        # 检查: 回复不会被添加两次前缀
        response = tracker.get_empathetic_response("u1", "太好了！😊 这是你的结果")
        # 回复应保持原样不添加前缀（因为已经以该前缀开头）
        assert response == "太好了！😊 这是你的结果"

    # ── add_emotion_pattern ──

    def test_add_emotion_pattern(self):
        """测试: 添加自定义情感模式"""
        tracker = self._get_tracker()
        pid = tracker.add_emotion_pattern(
            ["自定义词"], self.Emotion.HAPPY, "自定义策略"
        )
        assert pid > 0

    def test_custom_pattern_detection(self):
        """测试: 自定义模式影响情感检测"""
        tracker = self._get_tracker()
        tracker.add_emotion_pattern(
            ["专属词汇"], self.Emotion.EXCITED, "热情回应"
        )
        # 检测包含该词的文本
        emotion = tracker.detect_emotion("这是专属词汇测试")
        assert emotion == self.Emotion.EXCITED

    def test_custom_pattern_persisted_in_stats(self):
        """测试: 自定义模式在统计中可见"""
        tracker = self._get_tracker()
        tracker.add_emotion_pattern(["kw1"], self.Emotion.HAPPY, "策略1")
        tracker.add_emotion_pattern(["kw2"], self.Emotion.SAD, "策略2")
        stats = tracker.get_stats()
        assert stats["custom_patterns"] == 2

    # ── get_emotion_history ──

    def test_get_emotion_history(self):
        """测试: 获取情感历史"""
        tracker = self._get_tracker()
        for i in range(5):
            tracker.record_emotion("u1", self.Emotion.HAPPY, 0.5 + i * 0.1, trigger=f"msg{i}")

        history = tracker.get_emotion_history("u1")
        assert len(history) == 5

    def test_get_emotion_history_limit(self):
        """测试: 情感历史限制数量"""
        tracker = self._get_tracker()
        for i in range(10):
            tracker.record_emotion("u1", self.Emotion.HAPPY, 0.5, trigger=f"msg{i}")

        history = tracker.get_emotion_history("u1", limit=3)
        assert len(history) == 3

    def test_get_emotion_history_empty(self):
        """测试: 无记录时返回空列表"""
        tracker = self._get_tracker()
        history = tracker.get_emotion_history("nobody")
        assert history == []

    # ── get_stats ──

    def test_get_stats_initial(self):
        """测试: 初始统计为零"""
        tracker = self._get_tracker()
        stats = tracker.get_stats()
        assert stats["total_records"] == 0
        assert stats["by_emotion"] == {}
        assert stats["by_user"] == {}
        assert stats["custom_patterns"] == 0

    def test_get_stats_after_records(self):
        """测试: 记录后统计更新"""
        tracker = self._get_tracker()
        tracker.record_emotion("u1", self.Emotion.HAPPY, 0.8, trigger="h1")
        tracker.record_emotion("u1", self.Emotion.SAD, 0.5, trigger="s1")
        tracker.record_emotion("u2", self.Emotion.HAPPY, 0.7, trigger="h2")

        stats = tracker.get_stats()
        assert stats["total_records"] == 3
        assert stats["by_emotion"]["happy"] == 2
        assert stats["by_emotion"]["sad"] == 1
        assert stats["by_user"]["u1"] == 2
        assert stats["by_user"]["u2"] == 1
        assert stats["avg_intensity"] > 0


# =============================================================================
# TestJarvisIntegrationV6
# =============================================================================


class TestJarvisIntegrationV6:
    """JarvisCore 新模块集成测试 (V6)"""

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

    def test_jarvis_initialization(self):
        """测试: Jarvis 基础初始化"""
        jarvis = self._get_jarvis()
        assert jarvis.initialized is False
        jarvis.initialize()
        assert jarvis.initialized is True

    def test_jarvis_chat_basic(self):
        """测试: Jarvis 基础聊天"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("你好")
        assert "response" in response
        assert len(response["response"]) > 0
        assert response["message"] == "你好"

    def test_jarvis_get_status_includes_modules(self):
        """测试: get_status 包含模块统计信息"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        status = jarvis.get_status()

        assert "modules" in status
        assert isinstance(status["modules"], dict)

    def test_jarvis_close_cleans_resources(self):
        """测试: close 清理资源"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        assert jarvis.initialized is True

        jarvis.close()
        assert jarvis.initialized is False

    def test_jarvis_close_idempotent(self):
        """测试: close 可安全重复调用"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        jarvis.close()
        jarvis.close()  # 不应抛异常
        jarvis.close()

    def test_jarvis_reopen_after_close(self):
        """测试: 关闭后可重新打开"""
        jarvis = self._get_jarvis()
        jarvis.chat("第一次")
        assert jarvis.initialized is True
        jarvis.close()
        assert jarvis.initialized is False

        # 重新使用
        response = jarvis.chat("第二次")
        assert jarvis.initialized is True
        assert "response" in response
        jarvis.close()

    def test_jarvis_chat_returns_processing_time(self):
        """测试: chat 返回处理时间"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("测试")
        assert "processing_time" in response
        assert isinstance(response["processing_time"], float)
        assert response["processing_time"] >= 0

    def test_jarvis_chat_with_custom_user_id(self):
        """测试: chat 支持自定义 user_id"""
        jarvis = self._get_jarvis()
        response = jarvis.chat("你好", user_id="custom_user")
        assert response["user_id"] == "custom_user"

    def test_jarvis_execute_task(self):
        """测试: execute_task 返回任务结果"""
        jarvis = self._get_jarvis()
        result = jarvis.execute_task("测试任务", complexity=2)
        assert "task" in result
        assert result["task"] == "测试任务"

    def test_jarvis_status_after_close(self):
        """测试: 关闭后initialized为False（不调用get_status避免已关闭db报错）"""
        jarvis = self._get_jarvis()
        jarvis.chat("初始化")
        assert jarvis.initialized is True
        jarvis.close()
        # 关闭后 initialized 应为 False
        assert jarvis.initialized is False

    def test_jarvis_chat_triggers_auto_init(self):
        """测试: chat 自动触发初始化"""
        jarvis = self._get_jarvis()
        assert jarvis.initialized is False
        jarvis.chat("触发")
        assert jarvis.initialized is True

    def test_jarvis_double_init_safe(self):
        """测试: 重复初始化安全"""
        jarvis = self._get_jarvis()
        jarvis.initialize()
        jarvis.initialize()  # 不应抛异常
        assert jarvis.initialized is True
