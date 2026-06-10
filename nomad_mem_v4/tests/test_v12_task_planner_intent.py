"""
Task Planner & Intent Engine 测试
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTaskPlanner:
    """任务规划器测试"""

    def test_decompose_simple_task(self):
        """测试分解简单任务"""
        from nomad_mem.autonomy.task_planner import TaskPlanner

        planner = TaskPlanner()
        plan_id = planner.decompose_task("计算1+1", complexity=1)

        summary = planner.get_plan_summary(plan_id)
        assert summary["total_tasks"] == 1

    def test_decompose_medium_task(self):
        """测试分解中等任务"""
        from nomad_mem.autonomy.task_planner import TaskPlanner

        planner = TaskPlanner()
        plan_id = planner.decompose_task("创建Python项目", complexity=3)

        summary = planner.get_plan_summary(plan_id)
        assert summary["total_tasks"] == 3  # 分析→执行→验证

    def test_decompose_complex_task(self):
        """测试分解复杂任务"""
        from nomad_mem.autonomy.task_planner import TaskPlanner

        planner = TaskPlanner()
        plan_id = planner.decompose_task("构建完整Web应用", complexity=5)

        summary = planner.get_plan_summary(plan_id)
        assert summary["total_tasks"] >= 5

    def test_get_execution_order(self):
        """测试获取执行顺序"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask

        planner = TaskPlanner()
        plan_id = "test_plan"
        task_a = SubTask(task_id="a", title="任务A", description="描述A")
        task_b = SubTask(task_id="b", title="任务B", description="描述B", dependencies=["a"])
        task_c = SubTask(task_id="c", title="任务C", description="描述C", dependencies=["a"])
        task_d = SubTask(task_id="d", title="任务D", description="描述D", dependencies=["b", "c"])

        planner.plans[plan_id] = [task_a, task_b, task_c, task_d]

        order = planner.get_execution_order(plan_id)
        assert order[0] == "a"  # A无依赖，先执行
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_get_ready_tasks(self):
        """测试获取可执行任务"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask, TaskStatus

        planner = TaskPlanner()
        plan_id = "test_plan"
        task_a = SubTask(task_id="a", title="任务A", description="描述A")
        task_b = SubTask(task_id="b", title="任务B", description="描述B", dependencies=["a"])

        planner.plans[plan_id] = [task_a, task_b]

        # 初始只有A可执行
        ready = planner.get_ready_tasks(plan_id)
        assert len(ready) == 1
        assert ready[0].task_id == "a"

        # 完成A后B可执行
        planner.mark_task_completed(plan_id, "a", "result_a")
        ready = planner.get_ready_tasks(plan_id)
        assert len(ready) == 1
        assert ready[0].task_id == "b"

    def test_mark_task_completed(self):
        """测试标记任务完成"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask, TaskStatus

        planner = TaskPlanner()
        plan_id = "test_plan"
        task = SubTask(task_id="a", title="任务A", description="描述A")
        planner.plans[plan_id] = [task]

        planner.mark_task_completed(plan_id, "a", result="成功")

        assert task.status == TaskStatus.COMPLETED
        assert task.result == "成功"
        assert task.completed_at > 0

    def test_mark_task_failed(self):
        """测试标记任务失败"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask, TaskStatus

        planner = TaskPlanner()
        plan_id = "test_plan"
        task_a = SubTask(task_id="a", title="任务A", description="描述A")
        task_b = SubTask(task_id="b", title="任务B", description="描述B", dependencies=["a"])
        planner.plans[plan_id] = [task_a, task_b]

        planner.mark_task_failed(plan_id, "a", error="执行失败")

        assert task_a.status == TaskStatus.FAILED
        assert task_b.status == TaskStatus.SKIPPED  # 依赖失败被跳过

    def test_get_plan_progress(self):
        """测试获取计划进度"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask

        planner = TaskPlanner()
        plan_id = "test_plan"
        tasks = [
            SubTask(task_id=f"t{i}", title=f"任务{i}", description=f"描述{i}")
            for i in range(4)
        ]
        planner.plans[plan_id] = tasks

        # 完成2个
        planner.mark_task_completed(plan_id, "t0")
        planner.mark_task_completed(plan_id, "t1")

        progress = planner.get_plan_progress(plan_id)
        assert progress["progress"] == 0.5
        assert progress["completed"] == 2
        assert progress["total"] == 4

    def test_is_plan_complete(self):
        """测试检查计划完成"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask

        planner = TaskPlanner()
        plan_id = "test_plan"
        tasks = [
            SubTask(task_id=f"t{i}", title=f"任务{i}", description=f"描述{i}")
            for i in range(3)
        ]
        planner.plans[plan_id] = tasks

        assert not planner.is_plan_complete(plan_id)

        for t in tasks:
            planner.mark_task_completed(plan_id, t.task_id)

        assert planner.is_plan_complete(plan_id)

    def test_parallel_groups(self):
        """测试并行任务组"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask

        planner = TaskPlanner()
        plan_id = "test_plan"

        # A和B可并行，C依赖A和B
        task_a = SubTask(task_id="a", title="A", description="A")
        task_b = SubTask(task_id="b", title="B", description="B")
        task_c = SubTask(task_id="c", title="C", description="C", dependencies=["a", "b"])

        planner.plans[plan_id] = [task_a, task_b, task_c]

        groups = planner.get_parallel_groups(plan_id)
        assert len(groups) == 2  # 两个层级
        assert set(groups[0]) == {"a", "b"}  # 第一层可并行
        assert groups[1] == ["c"]

    def test_mark_task_running(self):
        """测试标记任务执行中"""
        from nomad_mem.autonomy.task_planner import TaskPlanner, SubTask, TaskStatus

        planner = TaskPlanner()
        plan_id = "test"
        task = SubTask(task_id="x", title="X", description="X")
        planner.plans[plan_id] = [task]

        planner.mark_task_running(plan_id, "x")
        assert task.status == TaskStatus.RUNNING
        assert task.started_at > 0


class TestIntentEngine:
    """意图引擎测试"""

    def test_recognize_query(self):
        """测试识别查询意图"""
        from nomad_mem.autonomy.intent_engine import IntentEngine, IntentCategory

        engine = IntentEngine()
        intent = engine.recognize_intent("如何学习Python？")

        assert intent.category == IntentCategory.QUERY
        assert intent.confidence > 0.5

    def test_recognize_command(self):
        """测试识别命令意图"""
        from nomad_mem.autonomy.intent_engine import IntentEngine, IntentCategory

        engine = IntentEngine()
        intent = engine.recognize_intent("运行Python脚本")

        assert intent.category == IntentCategory.COMMAND

    def test_recognize_creation(self):
        """测试识别创建意图"""
        from nomad_mem.autonomy.intent_engine import IntentEngine, IntentCategory

        engine = IntentEngine()
        intent = engine.recognize_intent("创建一个新的Python项目")

        assert intent.category == IntentCategory.CREATION

    def test_recognize_conversation(self):
        """测试识别对话意图"""
        from nomad_mem.autonomy.intent_engine import IntentEngine, IntentCategory

        engine = IntentEngine()
        intent = engine.recognize_intent("你好，在吗？")

        assert intent.category == IntentCategory.CONVERSATION

    def test_entity_extraction(self):
        """测试实体提取"""
        from nomad_mem.autonomy.intent_engine import IntentEngine

        engine = IntentEngine()
        intent = engine.recognize_intent("计算1+1等于多少")

        assert len(intent.entities) >= 1
        assert any(e["type"] == "number" for e in intent.entities)

    def test_parameter_extraction(self):
        """测试参数提取"""
        from nomad_mem.autonomy.intent_engine import IntentEngine

        engine = IntentEngine()
        intent = engine.recognize_intent("创建一个Python文件")

        assert intent.parameters.get("target_type") == "file"

    def test_intent_history(self):
        """测试意图历史"""
        from nomad_mem.autonomy.intent_engine import IntentEngine

        engine = IntentEngine()
        engine.recognize_intent("你好", user_id="user1")
        engine.recognize_intent("帮我计算1+1", user_id="user1")

        stats = engine.get_intent_stats("user1")
        assert stats["total_intents"] == 2

    def test_detect_intent_change(self):
        """测试检测意图变化"""
        from nomad_mem.autonomy.intent_engine import IntentEngine, IntentCategory

        engine = IntentEngine()
        engine.recognize_intent("你好", user_id="user1")  # conversation
        engine.recognize_intent("计算1+1", user_id="user1")  # query

        change = engine.detect_intent_change("user1")
        assert change is not None
        assert change[0].category == IntentCategory.CONVERSATION
        assert change[1].category == IntentCategory.QUERY

    def test_suggest_clarification_low_confidence(self):
        """测试低置信度澄清建议"""
        from nomad_mem.autonomy.intent_engine import IntentEngine, Intent

        engine = IntentEngine()
        engine.ambiguity_threshold = 0.5

        # 创建一个低置信度意图
        low_conf_intent = engine.recognize_intent("asdfghjkl")  # 无匹配关键词
        questions = engine.suggest_clarification(low_conf_intent)
        assert len(questions) >= 1

    def test_composite_intent(self):
        """测试复合意图检测"""
        from nomad_mem.autonomy.intent_engine import IntentEngine

        engine = IntentEngine()
        intent = engine.recognize_intent("查询文件并且创建新目录")

        # 包含"并且"应该是复合意图
        assert intent.is_composite
        assert len(intent.sub_intents) >= 1

    def test_followup_detection(self):
        """测试追问检测"""
        from nomad_mem.autonomy.intent_engine import IntentEngine

        engine = IntentEngine()
        assert engine._is_followup("那这个呢？") is True
        assert engine._is_followup("他怎么做？") is True
        assert engine._is_followup("创建一个文件") is False

    def test_context_disambiguation(self):
        """测试上下文消歧"""
        from nomad_mem.autonomy.intent_engine import IntentEngine, Intent, IntentCategory

        engine = IntentEngine()
        engine.ambiguity_threshold = 0.4  # 降低阈值使测试生效

        # 模拟上下文：上一个意图是创建
        context = {
            "recent_intents": [
                Intent(intent_id="prev", category=IntentCategory.CREATION, description="创建", confidence=0.8)
            ]
        }

        # 追问"那这个呢？"应该继承创建意图
        intent = engine.recognize_intent("那这个呢？", context=context)
        assert intent.category == IntentCategory.CREATION
