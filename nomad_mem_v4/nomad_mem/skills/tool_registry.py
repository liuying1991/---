"""
工具注册表模块
管理工具注册、发现和 Schema 描述。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ToolStatus(str, Enum):
    """工具状态"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


class ToolCategory(str, Enum):
    """工具类别"""
    FILE = "file"
    SYSTEM = "system"
    NETWORK = "network"
    TIME = "time"
    SEARCH = "search"
    CALCULATION = "calculation"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    param_type: str  # "str", "int", "float", "bool", "list", "dict"
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None


@dataclass
class ToolInfo:
    """工具元信息"""
    tool_id: str
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter] = field(default_factory=list)
    return_type: str = "str"
    status: ToolStatus = ToolStatus.AVAILABLE
    usage_count: int = 0
    success_count: int = 0

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.usage_count == 0:
            return 1.0
        return self.success_count / self.usage_count


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    工具注册表 —— 像工具箱一样管理所有可用工具。

    职责:
    - 注册/注销工具
    - 按类别/状态过滤
    - 全文搜索
    - 生成 JSON Schema
    - 追踪使用统计
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolInfo] = {}
        self._handlers: Dict[str, Callable] = {}

    # -- registration -------------------------------------------------------

    def register_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        category: ToolCategory,
        parameters: Optional[List[ToolParameter]] = None,
        handler: Optional[Callable] = None,
        return_type: str = "str",
    ) -> ToolInfo:
        """注册一个新工具。"""
        if tool_id in self._tools:
            raise ValueError(f"Tool '{tool_id}' is already registered")

        info = ToolInfo(
            tool_id=tool_id,
            name=name,
            description=description,
            category=category,
            parameters=parameters or [],
            return_type=return_type,
        )
        self._tools[tool_id] = info
        if handler is not None:
            self._handlers[tool_id] = handler

        logger.info("Registered tool: %s (%s)", name, tool_id)
        return info

    def unregister_tool(self, tool_id: str) -> bool:
        """注销一个工具。"""
        if tool_id not in self._tools:
            return False
        del self._tools[tool_id]
        self._handlers.pop(tool_id, None)
        logger.info("Unregistered tool: %s", tool_id)
        return True

    # -- retrieval ----------------------------------------------------------

    def get_tool(self, tool_id: str) -> Optional[ToolInfo]:
        """按 ID 获取工具信息。"""
        return self._tools.get(tool_id)

    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        status: Optional[ToolStatus] = None,
    ) -> List[ToolInfo]:
        """列出工具，可按类别和状态过滤。"""
        result = list(self._tools.values())
        if category is not None:
            result = [t for t in result if t.category == category]
        if status is not None:
            result = [t for t in result if t.status == status]
        return result

    def search_tools(self, query: str) -> List[ToolInfo]:
        """按名称或描述搜索工具。"""
        q = query.lower()
        return [
            t for t in self._tools.values()
            if q in t.name.lower() or q in t.description.lower()
        ]

    # -- schema -------------------------------------------------------------

    def get_tool_schema(self, tool_id: str) -> Optional[Dict]:
        """返回工具的 JSON Schema 格式描述。"""
        info = self._tools.get(tool_id)
        if info is None:
            return None

        TYPE_MAP: Dict[str, str] = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
        }

        properties: Dict[str, Dict] = {}
        required: List[str] = []

        for p in info.parameters:
            json_type = TYPE_MAP.get(p.param_type, "string")
            prop: Dict[str, Any] = {"type": json_type, "description": p.description}
            if p.default is not None:
                prop["default"] = p.default
            if p.choices is not None:
                prop["enum"] = p.choices
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    # -- status & handler ---------------------------------------------------

    def update_tool_status(self, tool_id: str, status: ToolStatus) -> bool:
        """更新工具状态。"""
        if tool_id not in self._tools:
            return False
        self._tools[tool_id].status = status
        return True

    def get_tool_handler(self, tool_id: str) -> Optional[Callable]:
        """获取工具对应的处理函数。"""
        return self._handlers.get(tool_id)

    # -- stats --------------------------------------------------------------

    def get_stats(self) -> Dict:
        """返回注册表统计信息。"""
        by_category: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        total_usage = 0

        for t in self._tools.values():
            cat = t.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            st = t.status.value
            by_status[st] = by_status.get(st, 0) + 1
            total_usage += t.usage_count

        return {
            "total_tools": len(self._tools),
            "by_category": by_category,
            "by_status": by_status,
            "total_usage": total_usage,
        }

    # -- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        """清理资源（当前无外部资源，预留接口）。"""
        self._tools.clear()
        self._handlers.clear()
        logger.info("ToolRegistry closed")
