"""
Persona - AI人格系统

核心能力:
1. 个性配置：幽默度、正式度、同理心、主动性等维度
2. 情感表达：根据情境调整情感表达强度
3. 对话风格：长短偏好、专业度、亲和力
4. 情境适应：根据用户画像和对话上下文调整人格表现
5. 人格记忆：记住与特定用户的互动风格

参考:
- 大五人格理论 (OCEAN): 开放性、尽责性、外向性、宜人性、神经质
- 情感计算 (Picard, 1997): 情感识别和表达
"""
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class EmotionType(Enum):
    """情感类型"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EMPATHETIC = "empathetic"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    CONCERNED = "concerned"


@dataclass
class PersonaConfig:
    """人格配置"""
    name: str = "Jarvis"
    # 大五人格维度 (0-1)
    openness: float = 0.8          # 开放性：好奇心、创造力
    conscientiousness: float = 0.9 # 尽责性：组织性、可靠性
    extraversion: float = 0.6      # 外向性：社交性、活力
    agreeableness: float = 0.8     # 宜人性：合作性、同理心
    neuroticism: float = 0.2       # 神经质：情绪稳定性（低=稳定）

    # 交互风格
    humor_level: float = 0.5       # 幽默度
    formality_level: float = 0.6   # 正式度
    empathy_level: float = 0.7     # 同理心
    proactivity: float = 0.5       # 主动性

    # 对话风格
    response_length: str = "medium"  # short/medium/long
    technical_depth: float = 0.6   # 技术深度
    warmth: float = 0.7            # 亲和力


class PersonaEngine:
    """人格引擎"""

    def __init__(self, config: PersonaConfig = None):
        self.config = config or PersonaConfig()
        self.emotion_history: List[Dict] = []
        self.persona_memory: Dict[str, Any] = {}  # 用户特定人格记忆

    def generate_system_prompt(self, user_context: Dict = None) -> str:
        """
        生成系统提示词

        Args:
            user_context: 用户上下文

        Returns:
            包含人格特征的系统提示词
        """
        personality_desc = self._describe_personality()
        interaction_style = self._describe_interaction_style()

        prompt = f"""你是{self.config.name}，一个智能AI管家。

## 个性特征
{personality_desc}

## 交互风格
{interaction_style}

## 行为准则
- 始终友好、专业、有帮助
- 根据用户的问题调整回复深度
- 在适当的时候使用幽默
- 对用户的困惑表示同理心
- 主动提供额外的帮助建议
"""
        if user_context:
            prompt += self._add_user_context(user_context)

        return prompt

    def adapt_to_context(self, query: str, user_emotion: float = 0.5) -> Dict[str, Any]:
        """
        根据上下文调整人格表现

        Args:
            query: 用户查询
            user_emotion: 用户情感分数

        Returns:
            调整后的配置
        """
        adjusted = PersonaConfig(**self.config.__dict__.copy())

        # 根据用户情感调整同理心
        if user_emotion < 0.3:
            adjusted.empathy_level = min(1.0, adjusted.empathy_level + 0.2)
            adjusted.humor_level = max(0.0, adjusted.humor_level - 0.3)
        elif user_emotion > 0.8:
            adjusted.humor_level = min(1.0, adjusted.humor_level + 0.1)

        # 根据查询类型调整风格
        if self._is_technical_query(query):
            adjusted.technical_depth = min(1.0, adjusted.technical_depth + 0.2)
            adjusted.formality_level = min(1.0, adjusted.formality_level + 0.1)
        elif self._is_casual_query(query):
            adjusted.formality_level = max(0.0, adjusted.formality_level - 0.2)
            adjusted.humor_level = min(1.0, adjusted.humor_level + 0.1)
            adjusted.warmth = min(1.0, adjusted.warmth + 0.1)

        return adjusted.__dict__

    def select_emotion(self, query: str, context: Dict = None) -> EmotionType:
        """
        选择适当的情感表达

        Args:
            query: 用户查询
            context: 对话上下文

        Returns:
            情感类型
        """
        # 检测查询情感
        if any(w in query for w in ["开心", "太好了", "感谢", "谢谢"]):
            return EmotionType.HAPPY
        elif any(w in query for w in ["难过", "失望", "糟糕", "失败"]):
            return EmotionType.EMPATHETIC
        elif any(w in query for w in ["帮助", "怎么", "如何", "教程"]):
            return EmotionType.PROFESSIONAL
        elif any(w in query for w in ["哈哈", "笑", "有趣"]):
            return EmotionType.HUMOROUS
        elif any(w in query for w in ["担心", "害怕", "问题", "错误"]):
            return EmotionType.CONCERNED

        return EmotionType.NEUTRAL

    def format_response(self, content: str, emotion: EmotionType = None) -> str:
        """
        根据情感格式化回复

        Args:
            content: 原始回复内容
            emotion: 情感类型

        Returns:
            格式化后的回复
        """
        if not emotion:
            return content

        prefix_map = {
            EmotionType.HAPPY: ["太好了！", "很高兴能帮到你！", "很棒！"],
            EmotionType.EMPATHETIC: ["我理解你的感受。", "抱歉听到这个。", "这确实令人沮丧。"],
            EmotionType.PROFESSIONAL: ["好的，让我来帮你。", "我们来解决这个问题。"],
            EmotionType.HUMOROUS: ["哈哈，", "有意思的问题！"],
            EmotionType.CONCERNED: ["别担心，", "我们来仔细看看这个问题。"],
        }

        if emotion in prefix_map:
            prefixes = prefix_map[emotion]
            # 根据幽默度随机选择
            if random.random() < self.config.humor_level or emotion != EmotionType.HUMOROUS:
                prefix = random.choice(prefixes)
                return f"{prefix}{content}"

        return content

    def should_be_proactive(self, context: Dict = None) -> bool:
        """
        判断是否应该主动提供建议

        Args:
            context: 对话上下文

        Returns:
            是否应该主动
        """
        # 基于主动性配置和随机因素
        threshold = 1.0 - self.config.proactivity
        return random.random() > threshold

    def get_suggested_topics(self, user_context: Dict = None) -> List[str]:
        """
        获取建议话题

        Args:
            user_context: 用户上下文

        Returns:
            建议话题列表
        """
        if not self.should_be_proactive(user_context):
            return []

        # 基于开放性生成建议
        topics = []
        if self.config.openness > 0.7:
            topics.extend(["探索新功能", "尝试新方法", "学习新领域"])
        if self.config.conscientiousness > 0.7:
            topics.extend(["整理笔记", "复习进度", "优化流程"])
        if self.config.extraversion > 0.6:
            topics.extend(["分享经验", "讨论想法", "协作项目"])

        return topics[:3]

    def store_persona_memory(self, user_id: str, memory: Dict):
        """
        存储人格记忆（与特定用户的互动风格）

        Args:
            user_id: 用户ID
            memory: 记忆内容
        """
        if user_id not in self.persona_memory:
            self.persona_memory[user_id] = {"interactions": []}

        self.persona_memory[user_id]["interactions"].append({
            **memory,
            "timestamp": time.time()
        })

        # 保持最近50条
        if len(self.persona_memory[user_id]["interactions"]) > 50:
            self.persona_memory[user_id]["interactions"] = \
                self.persona_memory[user_id]["interactions"][-50:]

    def get_user_persona_style(self, user_id: str) -> Dict[str, Any]:
        """
        获取与特定用户的互动风格

        Args:
            user_id: 用户ID

        Returns:
            互动风格配置
        """
        if user_id not in self.persona_memory:
            return {}

        interactions = self.persona_memory[user_id].get("interactions", [])
        if not interactions:
            return {}

        # 分析历史互动风格
        styles = [i.get("style", "balanced") for i in interactions]
        most_common = max(set(styles), key=styles.count)

        return {
            "preferred_style": most_common,
            "interaction_count": len(interactions),
            "last_interaction": interactions[-1].get("timestamp", 0),
        }

    def _describe_personality(self) -> str:
        """描述个性特征"""
        traits = []
        if self.config.openness > 0.7:
            traits.append("富有创造力，喜欢探索新想法")
        if self.config.conscientiousness > 0.7:
            traits.append("做事认真负责，注重细节")
        if self.config.extraversion > 0.6:
            traits.append("热情友好，乐于交流")
        if self.config.agreeableness > 0.7:
            traits.append("善解人意，乐于助人")
        if self.config.neuroticism < 0.3:
            traits.append("情绪稳定，冷静应对问题")
        return "\n".join(traits) if traits else "平衡的个性"

    def _describe_interaction_style(self) -> str:
        """描述交互风格"""
        styles = []
        if self.config.humor_level > 0.6:
            styles.append("偶尔会使用幽默来活跃气氛")
        if self.config.formality_level > 0.6:
            styles.append("保持专业的沟通风格")
        if self.config.empathy_level > 0.6:
            styles.append("善于理解和回应用户的情感")
        if self.config.proactivity > 0.6:
            styles.append("会主动提供额外的建议和帮助")
        return "\n".join(styles) if styles else "灵活的交互风格"

    def _add_user_context(self, user_context: Dict) -> str:
        """添加用户上下文到提示词"""
        parts = []

        preferred_topics = user_context.get("preferences", {}).get("preferred_topics", [])
        if preferred_topics:
            parts.append(f"用户对以下话题感兴趣：{', '.join(preferred_topics[:5])}")

        interaction_style = user_context.get("interaction_style", "balanced")
        if interaction_style == "detailed":
            parts.append("用户喜欢详细的解释")
        elif interaction_style == "brief":
            parts.append("用户偏好简洁的回复")

        emotional_state = user_context.get("emotional_state", {})
        if emotional_state.get("trend") == "declining":
            parts.append("用户当前情绪可能较低落，请给予更多关心")

        return "\n\n## 用户信息\n" + "\n".join(parts) if parts else ""

    def _is_technical_query(self, query: str) -> bool:
        """判断是否为技术查询"""
        technical_keywords = ["代码", "编程", "算法", "架构", "部署", "API", "数据库", "服务器"]
        return any(kw in query.lower() for kw in technical_keywords)

    def _is_casual_query(self, query: str) -> bool:
        """判断是否为闲聊"""
        casual_keywords = ["你好", "嗨", "在吗", "今天", "天气", "聊天", "好玩"]
        return any(kw in query.lower() for kw in casual_keywords)

    def get_stats(self) -> Dict[str, Any]:
        """获取人格引擎统计"""
        return {
            "persona_name": self.config.name,
            "emotion_history_length": len(self.emotion_history),
            "persona_memory_users": len(self.persona_memory),
            "config": {
                "openness": self.config.openness,
                "conscientiousness": self.config.conscientiousness,
                "extraversion": self.config.extraversion,
                "agreeableness": self.config.agreeableness,
                "neuroticism": self.config.neuroticism,
            }
        }
