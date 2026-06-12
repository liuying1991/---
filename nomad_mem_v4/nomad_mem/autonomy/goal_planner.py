"""
Goal Planner - 自主目标规划器

基于经验回放、技能库、场景上下文自动生成目标规划。

核心特性:
- 经验驱动: 从历史成功/失败经验中提取目标模式
- 技能驱动: 基于可用技能推荐可实现的目标
- 场景驱动: 根据当前场景生成适配的目标
- 智能分解: 自动将大目标分解为可执行的子目标

设计原则:
- 规划基于数据，不拍脑袋
- 分解可执行，子目标足够小
- 场景适配，不同场景不同策略
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class GoalPlan:
    """目标规划

    Attributes:
        goal_title: 目标标题
        goal_description: 目标描述
        goal_type: 目标类型
        suggested_priority: 建议优先级
        suggested_subgoals: 建议的子目标列表
        required_skills: 需要的技能列表
        estimated_difficulty: 预估难度(0.0-1.0)
        rationale: 规划依据
    """
    goal_title: str
    goal_description: str
    goal_type: str = "task"
    suggested_priority: str = "medium"
    suggested_subgoals: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    estimated_difficulty: float = 0.5
    rationale: str = ""

    def to_dict(self) -> Dict:
        return {
            "goal_title": self.goal_title,
            "goal_description": self.goal_description,
            "goal_type": self.goal_type,
            "suggested_priority": self.suggested_priority,
            "suggested_subgoals": self.suggested_subgoals,
            "required_skills": self.required_skills,
            "estimated_difficulty": self.estimated_difficulty,
            "rationale": self.rationale,
        }


class GoalPlanner:
    """
    自主目标规划器

    基于经验、技能、场景生成目标规划。

    使用示例:
        >>> planner = GoalPlanner(experience_replay, skill_discoverer, scene_manager)
        >>> plan = planner.suggest_goals("user1", scene="work")
        >>> print(plan.goal_title)
        >>> print(plan.suggested_subgoals)
    """

    def __init__(
        self,
        goal_manager=None,
        experience_replay=None,
        scene_manager=None,
        skill_evolution=None,
        skill_discoverer=None,
    ):
        self.goal_manager = goal_manager
        self.replay = experience_replay
        self.scene_manager = scene_manager
        self.skill_evolution = skill_evolution
        self.skill_discoverer = skill_discoverer

        # 场景到目标类型的映射
        self._scene_goal_templates = {
            "work": {
                "type": "task",
                "templates": [
                    ("完成工作报告", "整理工作成果并生成报告", ["收集数据", "整理成果", "撰写报告"]),
                    ("优化工作流程", "分析并改进当前工作流程", ["分析现状", "识别瓶颈", "制定改进方案"]),
                ],
            },
            "learning": {
                "type": "learning",
                "templates": [
                    ("学习计划", "制定并执行学习计划", ["确定学习目标", "收集学习资源", "制定学习时间表"]),
                ],
            },
            "creation": {
                "type": "creation",
                "templates": [
                    ("创作项目", "完成一个创作项目", ["构思创意", "收集素材", "开始创作", "完善作品"]),
                ],
            },
            "health": {
                "type": "maintenance",
                "templates": [
                    ("健康追踪", "记录和分析健康状况", ["设定健康指标", "记录数据", "分析趋势"]),
                ],
            },
        }

        # 通用目标模板
        self._general_templates = [
            ("整理知识库", "整理和优化知识库", ["回顾知识", "分类整理", "更新内容"], "optimization", "low"),
            ("回顾经验教训", "从历史经验中学习", ["回顾失败经验", "提取教训", "制定改进计划"], "learning", "medium"),
        ]

    def suggest_goals(
        self,
        user_id: str,
        scene: str = "",
        k: int = 3,
    ) -> List[GoalPlan]:
        """
        为用户建议目标

        Args:
            user_id: 用户ID
            scene: 当前场景
            k: 建议数量

        Returns:
            目标规划列表
        """
        plans = []

        # 1. 场景驱动目标
        if scene:
            scene_plans = self._generate_scene_goals(scene)
            plans.extend(scene_plans)

        # 2. 经验驱动目标
        experience_plans = self._generate_experience_goals(user_id)
        plans.extend(experience_plans)

        # 3. 技能驱动目标
        skill_plans = self._generate_skill_goals()
        plans.extend(skill_plans)

        # 4. 通用目标
        if len(plans) < k:
            general_plans = self._generate_general_goals()
            plans.extend(general_plans)

        # 去重并按难度排序
        seen_titles = set()
        unique_plans = []
        for p in plans:
            if p.goal_title not in seen_titles:
                seen_titles.add(p.goal_title)
                unique_plans.append(p)

        unique_plans.sort(key=lambda x: x.estimated_difficulty)
        return unique_plans[:k]

    def decompose_goal(self, goal_title: str, goal_type: str = "task") -> List[str]:
        """
        将目标分解为子目标

        Args:
            goal_title: 目标标题
            goal_type: 目标类型

        Returns:
            子目标列表
        """
        # 查找匹配的模板
        for templates in self._scene_goal_templates.values():
            for title, _, subgoals in templates["templates"]:
                if title == goal_title:
                    return subgoals

        for title, _, subgoals, _, _ in self._general_templates:
            if title == goal_title:
                return subgoals

        # 默认分解策略
        return self._default_decomposition(goal_title, goal_type)

    def estimate_difficulty(self, goal_title: str, required_skills: List[str] = None) -> float:
        """
        预估目标难度

        Args:
            goal_title: 目标标题
            required_skills: 需要的技能列表

        Returns:
            难度(0.0-1.0)
        """
        difficulty = 0.3  # 基础难度

        # 根据子目标数量调整
        subgoals = self.decompose_goal(goal_title)
        difficulty += min(0.3, len(subgoals) * 0.05)

        # 根据所需技能调整
        if required_skills:
            missing_skills = self._check_missing_skills(required_skills)
            difficulty += min(0.4, len(missing_skills) * 0.15)

        return min(difficulty, 1.0)

    def _generate_scene_goals(self, scene: str) -> List[GoalPlan]:
        """基于场景生成目标"""
        plans = []
        scene_data = self._scene_goal_templates.get(scene)
        if not scene_data:
            return plans

        for title, desc, subgoals in scene_data["templates"]:
            plans.append(GoalPlan(
                goal_title=title,
                goal_description=desc,
                goal_type=scene_data["type"],
                suggested_subgoals=subgoals,
                suggested_priority="medium",
                estimated_difficulty=0.4 + len(subgoals) * 0.05,
                rationale=f"基于当前场景 '{scene}' 推荐",
            ))
        return plans

    def _generate_experience_goals(self, user_id: str) -> List[GoalPlan]:
        """基于经验生成目标"""
        plans = []
        if not self.replay:
            return plans

        # 从失败经验中提取改进目标
        failures = self.replay.retrieve_recent_failures(k=3)
        for f in failures:
            if f.lesson_learned:
                plans.append(GoalPlan(
                    goal_title=f"改进: {f.intent}",
                    goal_description=f"基于历史失败经验: {f.lesson_learned}",
                    goal_type="optimization",
                    suggested_subgoals=["分析失败原因", "制定改进方案", "测试改进效果"],
                    suggested_priority="high",
                    estimated_difficulty=0.5,
                    rationale=f"从失败经验中提取: {f.lesson_learned}",
                ))

        return plans

    def _generate_skill_goals(self) -> List[GoalPlan]:
        """基于技能生成目标"""
        plans = []
        if not self.skill_discoverer:
            return plans

        # 从高频技能组合生成目标
        combos = self.skill_discoverer.find_combinations(min_frequency=2)
        for combo in combos[:2]:
            plans.append(GoalPlan(
                goal_title=f"使用技能组合: {', '.join(combo.skills[:2])}",
                goal_description=f"经常一起使用的技能: {combo.skills}",
                goal_type="task",
                suggested_priority="medium",
                estimated_difficulty=combo.success_rate * 0.3 + 0.2,
                rationale=f"基于技能共现模式(频率:{combo.frequency})",
            ))

        return plans

    def _generate_general_goals(self) -> List[GoalPlan]:
        """生成通用目标"""
        plans = []
        for title, desc, subgoals, gtype, priority in self._general_templates:
            plans.append(GoalPlan(
                goal_title=title,
                goal_description=desc,
                goal_type=gtype,
                suggested_subgoals=subgoals,
                suggested_priority=priority,
                estimated_difficulty=0.3 + len(subgoals) * 0.05,
                rationale="通用建议",
            ))
        return plans

    def _default_decomposition(self, goal_title: str, goal_type: str) -> List[str]:
        """默认分解策略"""
        if goal_type == "learning":
            return ["确定学习目标", "收集资源", "制定计划", "执行学习", "总结复盘"]
        elif goal_type == "optimization":
            return ["分析现状", "识别问题", "制定方案", "实施改进", "验证效果"]
        elif goal_type == "creation":
            return ["构思创意", "收集素材", "开始创作", "完善作品", "发布分享"]
        else:
            # 通用分解
            return ["明确目标", "制定计划", "执行任务", "检查结果"]

    def _check_missing_skills(self, required_skills: List[str]) -> List[str]:
        """检查缺失的技能"""
        if not self.skill_evolution:
            return required_skills

        top_skills = self.skill_evolution.get_top_skills(limit=20)
        available = {s["skill_name"] for s in top_skills}
        return [s for s in required_skills if s not in available]
