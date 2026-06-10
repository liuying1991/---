"""
技能基类
所有技能必须继承此类并实现execute方法
"""
from abc import ABC, abstractmethod


class BaseSkill(ABC):
    """技能基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称（用于LLM tool calling）"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述（告诉LLM何时使用此技能）"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema格式的参数定义"""
        pass

    @abstractmethod
    def execute(self, args: dict) -> str:
        """
        执行技能

        Args:
            args: 参数字典

        Returns:
            执行结果字符串
        """
        pass
