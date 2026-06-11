"""
内置工具集模块 - 文件、系统、网络、时间、搜索、计算工具。

Jarvis 通过工具与外部世界交互 —— 这些是最基本的"感官"和"双手"。
"""
from __future__ import annotations

import os
import pathlib
import platform
import re
import socket
import time as _time_module
from datetime import datetime, timezone
from typing import Dict

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from nomad_mem.skills.tool_registry import (
    ToolCategory,
    ToolParameter,
    ToolRegistry,
)


# ---------------------------------------------------------------------------
# 安全路径检查
# ---------------------------------------------------------------------------

# 默认安全根目录列表：用户 home 和 /tmp
_SAFE_ROOTS = [
    pathlib.Path.home(),
    pathlib.Path("/tmp"),
]


def _is_safe_path(raw_path: str) -> pathlib.Path:
    """
    将路径解析为绝对路径并校验安全性。

    只允许访问用户 home 目录和 /tmp 下的文件，防止路径穿越攻击。

    Returns:
        解析后的绝对路径

    Raises:
        ValueError: 路径不在安全目录内
    """
    resolved = pathlib.Path(raw_path).resolve()
    for root in _SAFE_ROOTS:
        if resolved == root or resolved.is_relative_to(root):
            return resolved
    raise ValueError(
        f"Path '{raw_path}' is outside safe directories "
        f"({', '.join(str(r) for r in _SAFE_ROOTS)})"
    )


# ---------------------------------------------------------------------------
# 工具处理器
# ---------------------------------------------------------------------------

# --- 1. read_file ---

def _handle_read_file(path: str) -> str:
    """读取文件内容。"""
    safe_path = _is_safe_path(path)
    if not safe_path.exists():
        raise FileNotFoundError(f"File not found: {safe_path}")
    if not safe_path.is_file():
        raise IsADirectoryError(f"Not a file: {safe_path}")
    # 限制文件大小 1MB
    size = safe_path.stat().st_size
    if size > 1_048_576:
        raise ValueError(f"File too large ({size} bytes, limit 1MB)")
    return safe_path.read_text(encoding="utf-8", errors="replace")


# --- 2. write_file ---

def _handle_write_file(path: str, content: str, mode: str = "w") -> str:
    """写入内容到文件。"""
    safe_path = _is_safe_path(path)
    if mode not in ("w", "a"):
        raise ValueError(f"Invalid mode '{mode}', use 'w' or 'a'")
    # 确保父目录存在
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(content, encoding="utf-8")
    return f"Written {len(content)} characters to {safe_path}"


# --- 3. list_directory ---

def _handle_list_directory(path: str) -> str:
    """列出目录内容。"""
    safe_path = _is_safe_path(path)
    if not safe_path.exists():
        raise FileNotFoundError(f"Directory not found: {safe_path}")
    if not safe_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {safe_path}")

    lines = []
    try:
        entries = sorted(safe_path.iterdir())
    except PermissionError:
        raise PermissionError(f"Permission denied: {safe_path}")

    for entry in entries:
        prefix = "📁 " if entry.is_dir() else "📄 "
        size = ""
        if entry.is_file():
            try:
                size = f" ({entry.stat().st_size} bytes)"
            except OSError:
                pass
        lines.append(f"{prefix}{entry.name}{size}")

    return "\n".join(lines) if lines else "(empty directory)"


# --- 4. get_time ---

_TIME_FORMATS = {
    "iso": "%Y-%m-%dT%H:%M:%S%z",
    "date": "%Y-%m-%d",
    "time": "%H:%M:%S",
    "datetime": "%Y-%m-%d %H:%M:%S",
    "timestamp": None,  # special
    "human": "%A, %B %d, %Y %H:%M:%S",
}


def _handle_get_time(format: str = "datetime") -> str:
    """获取当前时间/日期。"""
    now = datetime.now(timezone.utc)
    fmt = _TIME_FORMATS.get(format)
    if fmt is None and format != "timestamp":
        available = ", ".join(_TIME_FORMATS.keys())
        raise ValueError(f"Unknown format '{format}'. Available: {available}")
    if format == "timestamp":
        return str(now.timestamp())
    return now.strftime(fmt)


# --- 5. calculate ---

def _handle_calculate(expression: str) -> str:
    """安全地计算数学表达式。"""
    # 只允许数字、运算符、括号、空格、常见数学函数名
    allowed = re.compile(r"^[\d\s\+\-\*/\.\(\)\%]+$")
    if not allowed.match(expression):
        raise ValueError(
            f"Invalid expression '{expression}'. Only numbers and basic operators (+-*/.%) are allowed."
        )
    try:
        result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307 - sandboxed
    except ZeroDivisionError:
        raise ValueError("Division by zero")
    except SyntaxError:
        raise ValueError(f"Syntax error in expression: {expression}")
    return str(result)


# --- 6. web_search ---

def _handle_web_search(query: str, num_results: int = 5) -> str:
    """
    搜索网页。

    注意：实际搜索需要配置 API key。这里提供一个占位实现，
    如果 requests 不可用或没有 API key，会返回友好提示。
    """
    if not HAS_REQUESTS:
        return (
            f"[web_search] The 'requests' library is not installed. "
            f"Install it with: pip install requests\n"
            f"Searched for: {query}"
        )

    # 使用 DuckDuckGo HTML 作为简单回退（不需要 API key）
    try:
        url = "https://html.duckduckgo.com/html/"
        resp = requests.get(
            url,
            params={"q": query},
            timeout=10,
            headers={"User-Agent": "Jarvis/1.0"},
        )
        resp.raise_for_status()

        # 简单提取结果标题
        results = []
        from html.parser import HTMLParser

        class _DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self._in_result = False
                self._in_a = False
                self._current_title = ""
                self._current_href = ""
                self._results: list[dict] = []
                self._collect_text = False

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "a" and "class" in attrs_dict and "result" in attrs_dict.get("class", ""):
                    self._in_a = True
                    self._current_href = attrs_dict.get("href", "")
                if self._in_a and tag in ("span",):
                    self._collect_text = True

            def handle_data(self, data):
                if self._collect_text:
                    self._current_title += data

            def handle_endtag(self, tag):
                if self._collect_text:
                    self._collect_text = False
                if self._in_a and tag == "a":
                    if self._current_title.strip():
                        self._results.append({
                            "title": self._current_title.strip(),
                            "url": self._current_href,
                        })
                    self._in_a = False
                    self._current_title = ""
                    self._current_href = ""

        parser = _DDGParser()
        parser.feed(resp.text)

        if parser._results:
            lines = [f"Search results for '{query}':", ""]
            for i, r in enumerate(parser._results[:num_results], 1):
                lines.append(f"{i}. {r['title']}")
                if r["url"]:
                    lines.append(f"   URL: {r['url']}")
            return "\n".join(lines)
        else:
            return f"[web_search] No results found for: {query}"

    except requests.RequestException as exc:
        return f"[web_search] Request failed: {exc}"


# --- 7. system_info ---

def _handle_system_info(type: str = "all") -> str:
    """获取系统信息。"""
    valid_types = ("all", "os", "hardware", "network", "python")

    if type not in valid_types:
        raise ValueError(f"Invalid type '{type}'. Available: {', '.join(valid_types)}")

    info: Dict[str, str] = {}

    if type in ("all", "os"):
        info["system"] = platform.system()
        info["node"] = platform.node()
        info["release"] = platform.release()
        info["version"] = platform.version()
        info["machine"] = platform.machine()
        info["platform"] = platform.platform()

    if type in ("all", "hardware"):
        import multiprocessing
        info["cpu_count"] = str(multiprocessing.cpu_count())
        try:
            import psutil  # type: ignore[import-not-found]
            mem = psutil.virtual_memory()
            info["total_memory"] = f"{mem.total / (1024**3):.1f} GB"
            info["available_memory"] = f"{mem.available / (1024**3):.1f} GB"
        except ImportError:
            info["total_memory"] = "unavailable (install psutil)"
            info["available_memory"] = "unavailable (install psutil)"

    if type in ("all", "network"):
        try:
            hostname = socket.gethostname()
            info["hostname"] = hostname
            info["ip_address"] = socket.gethostbyname(hostname)
        except Exception:
            info["network"] = "unavailable"

    if type in ("all", "python"):
        info["python_version"] = platform.python_version()
        info["python_implementation"] = platform.python_implementation()

    return "\n".join(f"{k}: {v}" for k, v in info.items())


# --- 8. timer ---

# 活跃定时器: timer_id -> {"thread": ..., "label": ..., "done": False}
_active_timers: Dict[str, Dict] = {}


def _handle_timer(seconds: int, label: str = "timer") -> str:
    """设置一个定时器。"""
    if seconds < 0:
        raise ValueError("Timer duration must be non-negative")
    if seconds > 86400:
        raise ValueError("Timer duration must be <= 86400 seconds (24 hours)")

    timer_id = f"timer_{int(_time_module.time())}"

    def _on_done():
        _time_module.sleep(seconds)
        _active_timers[timer_id]["done"] = True
        _active_timers[timer_id]["finished_at"] = _time_module.time()

    import threading
    t = threading.Thread(target=_on_done, name=f"timer-{label}", daemon=True)
    t.start()

    _active_timers[timer_id] = {
        "thread": t,
        "label": label,
        "seconds": seconds,
        "started_at": _time_module.time(),
        "done": False,
    }

    return f"Timer '{label}' set for {seconds} seconds (ID: {timer_id})"


# ---------------------------------------------------------------------------
# 注册函数
# ---------------------------------------------------------------------------

def register_builtin_tools(tool_registry: ToolRegistry) -> int:
    """
    向 ToolRegistry 注册所有内置工具。

    Args:
        tool_registry: 工具注册表实例

    Returns:
        注册的工具数量
    """
    tools = [
        (
            "read_file", "read_file", "读取指定文件的内容",
            ToolCategory.FILE,
            [ToolParameter("path", "str", "文件路径（相对于安全根目录）", True)],
            _handle_read_file, "str",
        ),
        (
            "write_file", "write_file", "将内容写入指定文件",
            ToolCategory.FILE,
            [
                ToolParameter("path", "str", "文件路径", True),
                ToolParameter("content", "str", "要写入的内容", True),
                ToolParameter("mode", "str", "写入模式: 'w'(覆盖) 或 'a'(追加)", False, "w", ["w", "a"]),
            ],
            _handle_write_file, "str",
        ),
        (
            "list_directory", "list_directory", "列出指定目录下的文件和子目录",
            ToolCategory.FILE,
            [ToolParameter("path", "str", "目录路径", True)],
            _handle_list_directory, "str",
        ),
        (
            "get_time", "get_time", "获取当前时间和日期",
            ToolCategory.TIME,
            [
                ToolParameter(
                    "format", "str",
                    "时间格式: iso, date, time, datetime, timestamp, human",
                    False, "datetime",
                    ["iso", "date", "time", "datetime", "timestamp", "human"],
                ),
            ],
            _handle_get_time, "str",
        ),
        (
            "calculate", "calculate", "执行数学计算表达式",
            ToolCategory.CALCULATION,
            [ToolParameter("expression", "str", "数学表达式（仅支持数字和基本运算符 +-*/.%）", True)],
            _handle_calculate, "str",
        ),
        (
            "web_search", "web_search", "在互联网上搜索信息",
            ToolCategory.SEARCH,
            [
                ToolParameter("query", "str", "搜索关键词", True),
                ToolParameter("num_results", "int", "返回结果数量", False, 5),
            ],
            _handle_web_search, "str",
        ),
        (
            "system_info", "system_info", "获取系统信息（操作系统、硬件、网络、Python 版本等）",
            ToolCategory.SYSTEM,
            [
                ToolParameter(
                    "type", "str",
                    "信息类型: all, os, hardware, network, python",
                    False, "all",
                    ["all", "os", "hardware", "network", "python"],
                ),
            ],
            _handle_system_info, "str",
        ),
        (
            "timer", "timer", "设置一个倒计时定时器",
            ToolCategory.TIME,
            [
                ToolParameter("seconds", "int", "倒计时秒数（最大 86400）", True),
                ToolParameter("label", "str", "定时器标签", False, "timer"),
            ],
            _handle_timer, "str",
        ),
    ]

    count = 0
    for tool_id, name, description, category, params, handler, return_type in tools:
        tool_registry.register_tool(
            tool_id=tool_id,
            name=name,
            description=description,
            category=category,
            parameters=params,
            handler=handler,
            return_type=return_type,
        )
        count += 1

    return count
