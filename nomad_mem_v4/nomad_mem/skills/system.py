"""
系统信息技能 - system_info, process, disk_usage, memory_usage
"""
import os
import platform
import psutil
from nomad_mem.skills.base import BaseSkill


class SystemInfo(BaseSkill):
    """获取系统信息"""

    @property
    def name(self) -> str:
        return "system_info"

    @property
    def description(self) -> str:
        return "获取当前系统的基本信息，包括操作系统版本、CPU、内存、主机名等。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, args: dict) -> str:
        info = []
        info.append(f"操作系统: {platform.system()} {platform.release()}")
        info.append(f"主机名: {platform.node()}")
        info.append(f"架构: {platform.machine()}")
        info.append(f"Python: {platform.python_version()}")
        info.append(f"CPU核心: {os.cpu_count()}")

        mem = psutil.virtual_memory()
        info.append(f"内存总量: {mem.total / (1024**3):.1f} GB")
        info.append(f"内存可用: {mem.available / (1024**3):.1f} GB")

        return "\n".join(info)


class Process(BaseSkill):
    """进程管理"""

    @property
    def name(self) -> str:
        return "process"

    @property
    def description(self) -> str:
        return "管理进程：list列出所有进程，find查找特定进程，stop停止进程。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作: list/查找/停止",
                    "enum": ["list", "find", "stop"],
                },
                "name": {
                    "type": "string",
                    "description": "进程名称（find/stop时需要）",
                },
                "limit": {
                    "type": "integer",
                    "description": "列出进程的最大数量，默认20",
                    "default": 20,
                },
            },
            "required": ["action"],
        }

    def execute(self, args: dict) -> str:
        action = args.get("action", "list")
        name = args.get("name", "")
        limit = args.get("limit", 20)

        try:
            if action == "list":
                processes = []
                for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                    try:
                        info = proc.info
                        processes.append(
                            f"PID: {info['pid']}, "
                            f"名称: {info['name']}, "
                            f"CPU: {info['cpu_percent'] or 0:.1f}%, "
                            f"内存: {info['memory_percent'] or 0:.1f}%"
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                return f"前{limit}个进程:\n" + "\n".join(processes[:limit])

            elif action == "find":
                if not name:
                    return "find操作需要提供进程名称"

                results = []
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        if name.lower() in proc.info["name"].lower():
                            results.append(f"PID: {proc.info['pid']}, 名称: {proc.info['name']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if not results:
                    return f"未找到包含'{name}'的进程"
                return f"匹配的进程:\n" + "\n".join(results)

            elif action == "stop":
                if not name:
                    return "stop操作需要提供进程名称"

                stopped = []
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        if name.lower() in proc.info["name"].lower():
                            proc.terminate()
                            stopped.append(proc.info["pid"])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if not stopped:
                    return f"未找到包含'{name}'的进程"
                return f"已停止PID为 {', '.join(map(str, stopped))} 的进程"
            else:
                return f"未知操作: {action}"

        except Exception as e:
            return f"操作错误: {e}"


class DiskUsage(BaseSkill):
    """磁盘使用情况"""

    @property
    def name(self) -> str:
        return "disk_usage"

    @property
    def description(self) -> str:
        return "查看磁盘使用情况，包括总容量、已用空间、可用空间和百分比。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "查看路径，默认根目录",
                    "default": "/",
                },
            },
            "required": [],
        }

    def execute(self, args: dict) -> str:
        path = args.get("path", "/")

        try:
            usage = psutil.disk_usage(path)
            return (
                f"路径: {path}\n"
                f"总容量: {usage.total / (1024**3):.1f} GB\n"
                f"已使用: {usage.used / (1024**3):.1f} GB\n"
                f"可用: {usage.free / (1024**3):.1f} GB\n"
                f"使用率: {usage.percent:.1f}%"
            )
        except Exception as e:
            return f"获取磁盘信息错误: {e}"


class MemoryUsage(BaseSkill):
    """内存使用情况"""

    @property
    def name(self) -> str:
        return "memory_usage"

    @property
    def description(self) -> str:
        return "查看内存使用情况，包括总量、已用、可用、使用率等。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, args: dict) -> str:
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            lines = [
                "=== 物理内存 ===",
                f"总量: {mem.total / (1024**3):.1f} GB",
                f"已使用: {mem.used / (1024**3):.1f} GB",
                f"可用: {mem.available / (1024**3):.1f} GB",
                f"使用率: {mem.percent:.1f}%",
                "",
                "=== 交换内存 ===",
                f"总量: {swap.total / (1024**3):.1f} GB",
                f"已使用: {swap.used / (1024**3):.1f} GB",
                f"可用: {swap.free / (1024**3):.1f} GB",
                f"使用率: {swap.percent:.1f}%",
            ]

            return "\n".join(lines)
        except Exception as e:
            return f"获取内存信息错误: {e}"
