"""
Automation package - 场景自动化引擎
"""
from .scene_automation import (
    SceneAutomation,
    AutomationRule,
    AutomationEvent,
    TriggerType,
    ActionType,
)

__all__ = [
    "SceneAutomation",
    "AutomationRule",
    "AutomationEvent",
    "TriggerType",
    "ActionType",
]
