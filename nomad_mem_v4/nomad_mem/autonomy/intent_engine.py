"""
Intent Engine - 意图理解引擎

核心能力:
1. 多层意图识别：表面意图→深层意图→隐含意图
2. 上下文消歧：利用对话历史消除意图歧义
3. 意图演化追踪：追踪用户意图的变化
4. 意图组合：识别复合意图（多个意图同时存在）
5. 意图置信度：对识别结果给予置信度

参考:
- 自然语言理解(NLU)意图识别
- 对话状态追踪(DST)
- 意图分类模型
"""
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class IntentCategory(Enum):
    """意图类别"""
    QUERY = "query"           # 查询信息
    COMMAND = "command"       # 执行操作
    CONVERSATION = "conversation"  # 闲聊对话
    CREATION = "creation"     # 创建内容
    MODIFICATION = "modification"  # 修改内容
    DELETION = "deletion"     # 删除内容
    ANALYSIS = "analysis"     # 分析数据
    PROBLEM_SOLVING = "problem_solving"  # 解决问题
    LEARNING = "learning"     # 学习知识
    ENTERTAINMENT = "entertainment"  # 娱乐


@dataclass
class Intent:
    """意图"""
    intent_id: str
    category: IntentCategory
    description: str
    confidence: float = 0.5
    entities: List[Dict] = field(default_factory=list)  # 提取的实体
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_composite: bool = False  # 是否复合意图
    sub_intents: List['Intent'] = field(default_factory=list)
    context_dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class IntentHistory:
    """意图历史"""
    user_id: str
    intents: List[Intent] = field(default_factory=list)
    intent_chains: List[List[str]] = field(default_factory=list)  # 意图链


class IntentEngine:
    """意图理解引擎"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.intent_keywords = self._init_keywords()
        self.intent_history: Dict[str, IntentHistory] = {}
        self.ambiguity_threshold = self.config.get("ambiguity_threshold", 0.3)

    def recognize_intent(
        self,
        user_input: str,
        context: Dict = None,
        user_id: str = "default"
    ) -> Intent:
        """
        识别用户意图

        Args:
            user_input: 用户输入
            context: 对话上下文
            user_id: 用户ID

        Returns:
            识别的意图
        """
        import uuid

        # 1. 识别表面意图
        surface_intent = self._recognize_surface(user_input)

        # 2. 上下文消歧
        if context:
            surface_intent = self._disambiguate(surface_intent, user_input, context)

        # 3. 检测复合意图
        composite = self._detect_composite(user_input)
        if composite and len(composite) > 1:
            surface_intent.is_composite = True
            surface_intent.sub_intents = composite[1:]

        # 4. 提取实体和参数
        surface_intent.entities = self._extract_entities(user_input)
        surface_intent.parameters = self._extract_parameters(user_input, surface_intent)

        # 5. 记录意图历史
        self._record_intent(user_id, surface_intent)

        return surface_intent

    def get_intent_context(self, user_id: str) -> List[Intent]:
        """
        获取用户意图上下文

        Args:
            user_id: 用户ID

        Returns:
            最近的意图列表
        """
        history = self.intent_history.get(user_id)
        if not history:
            return []
        return history.intents[-5:]

    def detect_intent_change(self, user_id: str) -> Optional[Tuple[Intent, Intent]]:
        """
        检测意图变化

        Args:
            user_id: 用户ID

        Returns:
            (旧意图, 新意图) 或 None
        """
        history = self.intent_history.get(user_id)
        if not history or len(history.intents) < 2:
            return None

        prev_intent = history.intents[-2]
        current_intent = history.intents[-1]

        # 意图类别发生变化
        if prev_intent.category != current_intent.category:
            return (prev_intent, current_intent)

        return None

    def suggest_clarification(self, intent: Intent) -> List[str]:
        """
        建议澄清问题

        Args:
            intent: 当前意图

        Returns:
            澄清问题列表
        """
        questions = []

        if intent.confidence < self.ambiguity_threshold:
            questions.append("您能再详细说明一下吗？")

        if intent.category == IntentCategory.COMMAND and not intent.entities:
            questions.append("您希望对哪个对象执行此操作？")

        if intent.is_composite:
            questions.append("您希望我先处理哪个部分？")

        if intent.category == IntentCategory.CREATION:
            if not intent.parameters.get("format"):
                questions.append("您希望创建什么格式的内容？")

        return questions

    def get_intent_stats(self, user_id: str) -> Dict[str, Any]:
        """获取意图统计"""
        history = self.intent_history.get(user_id)
        if not history:
            return {"total_intents": 0}

        category_counts = {}
        for intent in history.intents:
            cat = intent.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_intents": len(history.intents),
            "category_distribution": category_counts,
            "most_common_intent": max(category_counts, key=category_counts.get) if category_counts else None,
            "intent_chains": len(history.intent_chains),
        }

    def _init_keywords(self) -> Dict[IntentCategory, List[str]]:
        """初始化关键词映射"""
        return {
            IntentCategory.QUERY: [
                "查询", "搜索", "查找", "查看", "显示", "获取", "多少", "什么", "如何", "怎么"
            ],
            IntentCategory.COMMAND: [
                "执行", "运行", "启动", "停止", "重启", "打开", "关闭", "切换"
            ],
            IntentCategory.CONVERSATION: [
                "你好", "嗨", "hello", "hi", "在吗", "聊天", "谢谢", "再见"
            ],
            IntentCategory.CREATION: [
                "创建", "新建", "生成", "写", "制作", "添加", "建立", "设计"
            ],
            IntentCategory.MODIFICATION: [
                "修改", "更改", "更新", "调整", "编辑", "优化", "改进", "修复"
            ],
            IntentCategory.DELETION: [
                "删除", "移除", "去掉", "清除", "注销", "取消"
            ],
            IntentCategory.ANALYSIS: [
                "分析", "统计", "对比", "比较", "评估", "检查", "诊断"
            ],
            IntentCategory.PROBLEM_SOLVING: [
                "解决", "帮忙", "帮助", "怎么办", "出错了", "问题", "错误"
            ],
            IntentCategory.LEARNING: [
                "学习", "教程", "入门", "理解", "解释", "说明", "什么是"
            ],
            IntentCategory.ENTERTAINMENT: [
                "讲个", "推荐", "好玩", "有趣", "游戏", "笑话", "故事"
            ],
        }

    def _recognize_surface(self, user_input: str) -> Intent:
        """识别表面意图"""
        import uuid
        input_lower = user_input.lower()

        scores = {}
        for category, keywords in self.intent_keywords.items():
            score = sum(1 for kw in keywords if kw in input_lower)
            if score > 0:
                scores[category] = score

        if not scores:
            # 默认意图
            return Intent(
                intent_id=f"intent_{uuid.uuid4().hex[:8]}",
                category=IntentCategory.QUERY,
                description=user_input[:50],
                confidence=0.3
            )

        # 选择得分最高的类别
        best_category = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_category] * 0.3 + 0.4)

        return Intent(
            intent_id=f"intent_{uuid.uuid4().hex[:8]}",
            category=best_category,
            description=user_input[:50],
            confidence=confidence
        )

    def _disambiguate(self, intent: Intent, user_input: str, context: Dict) -> Intent:
        """上下文消歧"""
        history = context.get("history", [])
        recent_intents = context.get("recent_intents", [])

        # 如果当前意图置信度低，参考历史意图
        if intent.confidence < self.ambiguity_threshold and recent_intents:
            last_intent = recent_intents[-1]
            # 如果是追问（包含代词或省略），继承上一个意图
            if self._is_followup(user_input):
                intent.category = last_intent.category
                intent.confidence = last_intent.confidence * 0.8
                intent.context_dependencies.append(last_intent.intent_id)

        return intent

    def _detect_composite(self, user_input: str) -> List[Intent]:
        """检测复合意图"""
        import uuid

        # 检测连接词
        composite_indicators = ["并且", "然后", "接着", "还有", "另外", "同时", "和"]
        has_composite = any(ind in user_input for ind in composite_indicators)

        if not has_composite:
            return []

        # 简单分割（按连接词）
        parts = self._split_by_indicators(user_input, composite_indicators)
        if len(parts) < 2:
            return []

        intents = []
        for part in parts:
            sub_intent = self._recognize_surface(part.strip())
            intents.append(sub_intent)

        return intents

    def _extract_entities(self, user_input: str) -> List[Dict]:
        """提取实体"""
        entities = []

        # 提取数字
        import re
        numbers = re.findall(r'\d+\.?\d*', user_input)
        for num in numbers:
            entities.append({"type": "number", "value": num})

        # 提取引号内容
        quoted = re.findall(r'["\u201c\u201d](.*?)["\u201c\u201d]', user_input)
        for q in quoted:
            entities.append({"type": "quoted_text", "value": q})

        # 提取文件名模式
        file_patterns = re.findall(r'[\w\-]+\.\w+', user_input)
        for fp in file_patterns:
            entities.append({"type": "filename", "value": fp})

        return entities

    def _extract_parameters(self, user_input: str, intent: Intent) -> Dict[str, Any]:
        """提取参数"""
        params = {}

        # 根据意图类别提取特定参数
        if intent.category == IntentCategory.CREATION:
            if "文件" in user_input:
                params["target_type"] = "file"
            elif "文件夹" in user_input or "目录" in user_input:
                params["target_type"] = "directory"

        if intent.category == IntentCategory.COMMAND:
            if "现在" in user_input or "立即" in user_input:
                params["urgency"] = "high"

        if intent.category == IntentCategory.QUERY:
            if "详细" in user_input or "完整" in user_input:
                params["detail_level"] = "high"

        return params

    def _record_intent(self, user_id: str, intent: Intent):
        """记录意图"""
        if user_id not in self.intent_history:
            self.intent_history[user_id] = IntentHistory(user_id=user_id)

        self.intent_history[user_id].intents.append(intent)

        # 保持最近100条
        if len(self.intent_history[user_id].intents) > 100:
            self.intent_history[user_id].intents = self.intent_history[user_id].intents[-100:]

    def _is_followup(self, user_input: str) -> bool:
        """判断是否为追问"""
        followup_indicators = ["那", "呢", "这个", "那个", "它", "他", "她", "再", "还"]
        return any(ind in user_input for ind in followup_indicators)

    def _split_by_indicators(self, text: str, indicators: List[str]) -> List[str]:
        """按连接词分割文本"""
        parts = [text]
        for indicator in indicators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(indicator))
            parts = new_parts
        return [p.strip() for p in parts if p.strip()]
