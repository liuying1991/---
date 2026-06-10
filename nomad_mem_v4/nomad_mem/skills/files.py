"""
文件操作技能 - read_file, write_file, list_files
包含路径沙箱保护
"""
import os
from pathlib import Path
from nomad_mem.skills.base import BaseSkill


class Sandbox:
    """路径沙箱"""

    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def resolve_path(self, rel_path: str) -> Path:
        """
        将相对路径解析为绝对路径，并确保在沙箱内

        Raises:
            PermissionError: 如果路径逃出沙箱
        """
        p = (self.root / rel_path).resolve()
        if self.root not in p.parents and p != self.root:
            raise PermissionError(f"路径逃出沙箱: {rel_path}")
        return p


class ReadFile(BaseSkill):
    """读取文件内容"""

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "读取指定路径的文件内容。用于查看代码、配置文件、日志等文本文件。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径（相对于工作目录）",
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "最大读取字节数，默认32000",
                    "default": 32000,
                },
            },
            "required": ["path"],
        }

    def execute(self, args: dict) -> str:
        path = args.get("path", "")
        max_bytes = args.get("max_bytes", 32000)

        try:
            p = self.sandbox.resolve_path(path)
            content = p.read_bytes()[:max_bytes].decode("utf-8", errors="replace")
            return f"[文件: {p.relative_to(self.sandbox.root)}]\n{content}"
        except PermissionError as e:
            return f"权限拒绝: {e}"
        except FileNotFoundError:
            return f"文件不存在: {path}"
        except Exception as e:
            return f"读取错误: {e}"


class WriteFile(BaseSkill):
    """写入文件内容"""

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "写入内容到指定路径的文件。如果文件不存在会自动创建父目录。用于创建/修改配置文件、代码、文档等。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径（相对于工作目录）",
                },
                "content": {
                    "type": "string",
                    "description": "要写入的文件内容",
                },
                "mode": {
                    "type": "string",
                    "description": "写入模式: 'write'覆盖 或 'append'追加",
                    "enum": ["write", "append"],
                    "default": "write",
                },
            },
            "required": ["path", "content"],
        }

    def execute(self, args: dict) -> str:
        path = args.get("path", "")
        content = args.get("content", "")
        mode = args.get("mode", "write")

        try:
            p = self.sandbox.resolve_path(path)
            p.parent.mkdir(parents=True, exist_ok=True)

            if mode == "append":
                with open(p, "a", encoding="utf-8") as f:
                    f.write(content)
                return f"内容已追加到: {p.relative_to(self.sandbox.root)}"
            else:
                p.write_text(content, encoding="utf-8")
                return f"文件已写入: {p.relative_to(self.sandbox.root)}"
        except PermissionError as e:
            return f"权限拒绝: {e}"
        except Exception as e:
            return f"写入错误: {e}"


class ListFiles(BaseSkill):
    """列出目录内容"""

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "列出指定目录下的文件和子目录。用于浏览文件系统结构。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目录路径（相对于工作目录），默认当前目录",
                    "default": ".",
                },
            },
            "required": [],
        }

    def execute(self, args: dict) -> str:
        path = args.get("path", ".")

        try:
            p = self.sandbox.resolve_path(path)
            if not p.is_dir():
                return f"不是目录: {path}"

            entries = []
            for entry in sorted(p.iterdir()):
                prefix = "📁" if entry.is_dir() else "📄"
                entries.append(f"{prefix} {entry.name}")

            if not entries:
                return f"目录为空: {p.relative_to(self.sandbox.root)}"

            return f"[目录: {p.relative_to(self.sandbox.root)}]\n" + "\n".join(entries)
        except PermissionError as e:
            return f"权限拒绝: {e}"
        except FileNotFoundError:
            return f"目录不存在: {path}"
        except Exception as e:
            return f"列出错误: {e}"
