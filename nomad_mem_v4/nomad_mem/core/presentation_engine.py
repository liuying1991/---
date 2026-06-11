"""
信息展示引擎 (Presentation Engine)

结构化展示信息：表格、列表、进度、面板等
设计原则：简洁的文本/Markdown 格式，清晰可读
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


class PresentationType(Enum):
    """展示类型"""
    TABLE = "table"
    LIST = "list"
    PROGRESS = "progress"
    STATUS_PANEL = "status_panel"
    CARD = "card"
    TIMELINE = "timeline"
    CHART_DATA = "chart_data"


@dataclass
class TableData:
    """表格数据"""
    headers: List[str]
    rows: List[List[str]]
    title: str = ""


@dataclass
class ListItem:
    """列表项"""
    label: str
    value: str
    icon: str = ""
    status: str = "ok"  # ok / warning / error / info


@dataclass
class ProgressInfo:
    """进度信息"""
    current: int
    total: int
    label: str = ""
    status: str = "running"  # running / done / failed

    @property
    def percentage(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)


@dataclass
class CardData:
    """卡片数据"""
    title: str
    content: str
    metadata: Dict[str, str] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)


@dataclass
class TimelineItem:
    """时间线项"""
    timestamp: str
    event: str
    description: str = ""
    status: str = "ok"  # ok / warning / error / info


class PresentationEngine:
    """信息展示引擎"""

    STATUS_ICONS = {
        "ok": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "running": "🔄",
        "done": "✅",
        "failed": "❌",
    }

    def __init__(self):
        self._stats: Dict[str, int] = {
            "total_presentations": 0,
            "by_type": {},
        }

    def create_table(self, title: str, headers: List[str], rows: List[List[str]]) -> str:
        """
        格式化为 Markdown 表格

        Args:
            title: 表格标题
            headers: 表头列表
            rows: 数据行列表

        Returns:
            Markdown 表格字符串
        """
        lines = []
        if title:
            lines.append(f"### {title}")
            lines.append("")

        if not headers:
            return "\n".join(lines) if lines else "(空表格)"

        # 计算每列宽度
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # 构建表头
        header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        separator = "|" + "|".join("-" * (col_widths[i] + 2) for i in range(len(headers))) + "|"
        lines.append(header_line)
        lines.append(separator)

        # 构建数据行
        for row in rows:
            cells = [str(row[i]).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i])
                     for i in range(len(headers))]
            lines.append("| " + " | ".join(cells) + " |")

        self._record_stat(PresentationType.TABLE)
        return "\n".join(lines)

    def create_list(self, items: List[Any], title: str = "", numbered: bool = False) -> str:
        """
        格式化为列表

        Args:
            items: 列表项（ListItem 或普通字符串/字典）
            title: 列表标题
            numbered: 是否使用编号列表

        Returns:
            格式化后的列表字符串
        """
        lines = []
        if title:
            lines.append(f"### {title}")
            lines.append("")

        if not items:
            lines.append("(空列表)")
            self._record_stat(PresentationType.LIST)
            return "\n".join(lines)

        for idx, item in enumerate(items):
            if isinstance(item, ListItem):
                icon = item.icon or self.STATUS_ICONS.get(item.status, "")
                prefix = f"{idx + 1}." if numbered else "-"
                line = f"{prefix} {icon} **{item.label}**: {item.value}"
            elif isinstance(item, dict):
                prefix = f"{idx + 1}." if numbered else "-"
                label = item.get("label", item.get("name", ""))
                value = item.get("value", item.get("detail", ""))
                status = item.get("status", "ok")
                icon = self.STATUS_ICONS.get(status, "")
                line = f"{prefix} {icon} **{label}**: {value}"
            else:
                prefix = f"{idx + 1}." if numbered else "-"
                line = f"{prefix} {str(item)}"
            lines.append(line)

        self._record_stat(PresentationType.LIST)
        return "\n".join(lines)

    def create_progress(self, current: int, total: int, label: str = "") -> str:
        """
        格式化进度条（文本形式）

        Args:
            current: 当前进度
            total: 总进度
            label: 进度标签

        Returns:
            进度条字符串
        """
        info = ProgressInfo(current=current, total=total, label=label)
        pct = info.percentage
        bar_width = 30
        filled = int(bar_width * pct / 100)
        empty = bar_width - filled

        icon = self.STATUS_ICONS.get(info.status, "")
        bar = "█" * filled + "░" * empty
        label_str = f" {info.label}" if info.label else ""
        line = f"{icon} [{bar}] {pct:.1f}% ({current}/{total}){label_str}"

        self._record_stat(PresentationType.PROGRESS)
        return line

    def create_status_panel(self, status_items: List[Any]) -> str:
        """
        格式化状态面板

        Args:
            status_items: 状态项列表（ListItem 或字典）

        Returns:
            状态面板字符串
        """
        lines = []
        lines.append("┌" + "─" * 40 + "┐")
        lines.append("│" + " 状态面板 ".center(40) + "│")
        lines.append("├" + "─" * 40 + "┤")

        if not status_items:
            lines.append("│" + " (无状态) ".center(40) + "│")
        else:
            for item in status_items:
                if isinstance(item, ListItem):
                    icon = item.icon or self.STATUS_ICONS.get(item.status, "")
                    text = f" {icon} {item.label}: {item.value}"
                elif isinstance(item, dict):
                    icon = self.STATUS_ICONS.get(item.get("status", "ok"), "")
                    label = item.get("label", item.get("name", ""))
                    value = item.get("value", "")
                    text = f" {icon} {label}: {value}"
                else:
                    text = f"  {str(item)}"

                # 截断过长行
                if len(text) > 38:
                    text = text[:37] + "…"
                lines.append("│" + text.ljust(40) + "│")

        lines.append("└" + "─" * 40 + "┘")

        self._record_stat(PresentationType.STATUS_PANEL)
        return "\n".join(lines)

    def create_card(self, title: str, content: str,
                    metadata: Optional[Dict[str, str]] = None,
                    actions: Optional[List[str]] = None) -> str:
        """
        创建卡片布局

        Args:
            title: 卡片标题
            content: 卡片内容
            metadata: 元数据键值对
            actions: 操作按钮列表

        Returns:
            卡片字符串
        """
        card = CardData(title=title, content=content,
                        metadata=metadata or {}, actions=actions or [])

        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║  **{card.title}**".ljust(52) + "║")
        lines.append("╠" + "═" * 50 + "╣")

        # 内容
        for content_line in card.content.split("\n"):
            padded = f"  {content_line}"
            if len(padded) > 48:
                padded = padded[:47] + "…"
            lines.append("║" + padded.ljust(50) + "║")

        # 元数据
        if card.metadata:
            lines.append("╟" + "─" * 50 + "╢")
            for key, value in card.metadata.items():
                meta_line = f"  📌 {key}: {value}"
                if len(meta_line) > 48:
                    meta_line = meta_line[:47] + "…"
                lines.append("║" + meta_line.ljust(50) + "║")

        # 操作
        if card.actions:
            lines.append("╟" + "─" * 50 + "╢")
            action_str = "  [" + "]  [".join(card.actions) + "]"
            if len(action_str) > 48:
                action_str = action_str[:47] + "…"
            lines.append("║" + action_str.ljust(50) + "║")

        lines.append("╚" + "═" * 50 + "╝")

        self._record_stat(PresentationType.CARD)
        return "\n".join(lines)

    def create_timeline(self, items: List[Any]) -> str:
        """
        创建时间线格式

        Args:
            items: TimelineItem 或字典列表

        Returns:
            时间线字符串
        """
        lines = []

        if not items:
            lines.append("(空时间线)")
            self._record_stat(PresentationType.TIMELINE)
            return "\n".join(lines)

        for idx, item in enumerate(items):
            if isinstance(item, TimelineItem):
                icon = self.STATUS_ICONS.get(item.status, "")
                lines.append(f"  {icon} **{item.timestamp}**")
                lines.append(f"     └─ {item.event}")
                if item.description:
                    lines.append(f"        {item.description}")
            elif isinstance(item, dict):
                icon = self.STATUS_ICONS.get(item.get("status", "ok"), "")
                ts = item.get("timestamp", "")
                event = item.get("event", "")
                desc = item.get("description", "")
                lines.append(f"  {icon} **{ts}**")
                lines.append(f"     └─ {event}")
                if desc:
                    lines.append(f"        {desc}")
            else:
                lines.append(f"  • {str(item)}")

            # 连接线（最后一项除外）
            if idx < len(items) - 1:
                lines.append("     │")

        self._record_stat(PresentationType.TIMELINE)
        return "\n".join(lines)

    def choose_presentation_type(self, data: Any) -> PresentationType:
        """
        自动检测最佳展示类型

        Args:
            data: 待展示数据

        Returns:
            推荐的 PresentationType
        """
        if isinstance(data, TableData):
            return PresentationType.TABLE

        if isinstance(data, ProgressInfo):
            return PresentationType.PROGRESS

        if isinstance(data, CardData):
            return PresentationType.CARD

        if isinstance(data, list):
            if not data:
                return PresentationType.LIST

            first = data[0]
            if isinstance(first, TimelineItem):
                return PresentationType.TIMELINE
            if isinstance(first, ListItem):
                # 检查是否有进度相关信息
                if all(hasattr(i, 'status') and i.status in ('running', 'done', 'failed')
                       for i in data if isinstance(i, ListItem)):
                    return PresentationType.STATUS_PANEL
                return PresentationType.LIST
            if isinstance(first, dict):
                if all('headers' in d and 'rows' in d for d in data):
                    return PresentationType.TABLE
                if all('current' in d and 'total' in d for d in data):
                    return PresentationType.PROGRESS
                if 'timestamp' in first and 'event' in first:
                    return PresentationType.TIMELINE
                if 'label' in first and 'value' in first:
                    return PresentationType.LIST
                return PresentationType.LIST
            return PresentationType.LIST

        if isinstance(data, dict):
            if 'headers' in data and 'rows' in data:
                return PresentationType.TABLE
            if 'current' in data and 'total' in data:
                return PresentationType.PROGRESS
            if 'title' in data and 'content' in data:
                return PresentationType.CARD
            if 'items' in data:
                return self.choose_presentation_type(data['items'])
            return PresentationType.CARD

        return PresentationType.LIST

    def format_response(self, data: Any, presentation_type: Optional[PresentationType] = None) -> str:
        """
        自动格式化任意数据

        Args:
            data: 待格式化数据
            presentation_type: 指定展示类型（None 时自动检测）

        Returns:
            格式化后的字符串
        """
        if presentation_type is None:
            presentation_type = self.choose_presentation_type(data)

        if presentation_type == PresentationType.TABLE:
            if isinstance(data, TableData):
                return self.create_table(data.title, data.headers, data.rows)
            elif isinstance(data, dict):
                return self.create_table(
                    data.get("title", ""),
                    data.get("headers", []),
                    data.get("rows", []),
                )
            return self._dict_to_table(data)

        elif presentation_type == PresentationType.LIST:
            if isinstance(data, list):
                return self.create_list(data)
            return self.create_list([data])

        elif presentation_type == PresentationType.PROGRESS:
            if isinstance(data, ProgressInfo):
                return self.create_progress(data.current, data.total, data.label)
            elif isinstance(data, dict):
                return self.create_progress(
                    data.get("current", 0),
                    data.get("total", 1),
                    data.get("label", ""),
                )
            return "(无效进度数据)"

        elif presentation_type == PresentationType.STATUS_PANEL:
            if isinstance(data, list):
                return self.create_status_panel(data)
            return self.create_status_panel([data])

        elif presentation_type == PresentationType.CARD:
            if isinstance(data, CardData):
                return self.create_card(data.title, data.content, data.metadata, data.actions)
            elif isinstance(data, dict):
                return self.create_card(
                    data.get("title", "Card"),
                    data.get("content", ""),
                    data.get("metadata"),
                    data.get("actions"),
                )
            return self.create_card("Info", str(data))

        elif presentation_type == PresentationType.TIMELINE:
            if isinstance(data, list):
                return self.create_timeline(data)
            return self.create_timeline([data])

        elif presentation_type == PresentationType.CHART_DATA:
            return self._format_chart_data(data)

        return str(data)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取展示统计信息

        Returns:
            统计字典
        """
        return {
            "total_presentations": self._stats["total_presentations"],
            "by_type": dict(self._stats["by_type"]),
        }

    def close(self):
        """关闭引擎（清理资源）"""
        self._stats = {"total_presentations": 0, "by_type": {}}

    # ─── Internal helpers ─────────────────────────────────────────────

    def _record_stat(self, ptype: PresentationType):
        """记录展示统计"""
        self._stats["total_presentations"] += 1
        key = ptype.value
        self._stats["by_type"][key] = self._stats["by_type"].get(key, 0) + 1

    def _dict_to_table(self, data: Any) -> str:
        """将字典转为表格"""
        if isinstance(data, dict):
            headers = ["Key", "Value"]
            rows = [[str(k), str(v)] for k, v in data.items()]
            return self.create_table("", headers, rows)
        return str(data)

    def _format_chart_data(self, data: Any) -> str:
        """格式化图表数据为 ASCII 柱状图"""
        lines = []
        if isinstance(data, dict):
            max_val = max((float(v) for v in data.values()), default=1)
            max_val = max(max_val, 1)  # 避免除零
            bar_max = 40
            for label, value in data.items():
                try:
                    val = float(value)
                except (ValueError, TypeError):
                    val = 0
                bar_len = int(val / max_val * bar_max)
                bar = "▓" * bar_len
                lines.append(f"  {str(label)[:15]:<15s} │ {bar} {val}")
        elif isinstance(data, list):
            max_val = max((float(d.get("value", 0)) if isinstance(d, dict) else float(d)
                           for d in data), default=1)
            max_val = max(max_val, 1)
            bar_max = 40
            for item in data:
                if isinstance(item, dict):
                    label = item.get("label", "")
                    val = float(item.get("value", 0))
                else:
                    label = str(item)
                    val = float(item)
                bar_len = int(val / max_val * bar_max)
                bar = "▓" * bar_len
                lines.append(f"  {label[:15]:<15s} │ {bar} {val}")
        else:
            lines.append(str(data))

        self._record_stat(PresentationType.CHART_DATA)
        return "\n".join(lines)
