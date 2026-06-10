"""
技能注册表
管理所有已注册的技能
"""
from typing import Optional


class SkillRegistry:
    """技能注册表"""

    def __init__(self):
        self._skills = {}

    def register(self, skill):
        """
        注册技能

        Args:
            skill: BaseSkill实例
        """
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[object]:
        """
        获取技能

        Args:
            name: 技能名称

        Returns:
            技能实例，不存在返回None
        """
        return self._skills.get(name)

    def get_all_skills(self) -> list:
        """获取所有已注册的技能"""
        return list(self._skills.values())

    def get_skill_names(self) -> list[str]:
        """获取所有技能名称"""
        return list(self._skills.keys())

    def unregister(self, name: str):
        """注销技能"""
        if name in self._skills:
            del self._skills[name]
