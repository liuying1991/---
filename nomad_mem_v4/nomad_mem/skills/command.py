"""
execute_command - 执行系统命令技能
包含沙箱保护和黑白名单机制
"""
import subprocess
import os
import shlex
from nomad_mem.skills.base import BaseSkill


class ExecuteCommand(BaseSkill):
    """执行系统命令"""

    def __init__(self, config: dict):
        """
        初始化

        Args:
            config: 技能配置，包含:
                - sandbox_enabled: 是否启用沙箱
                - work_dir: 工作目录
                - command_blacklist: 危险命令黑名单
                - command_whitelist: 命令白名单（空=不启用）
        """
        self.config = config
        self.sandbox_enabled = config.get("sandbox_enabled", True)
        self.work_dir = config.get("work_dir", "/tmp")
        self.blacklist = config.get("command_blacklist", [])
        self.whitelist = config.get("command_whitelist", [])

    @property
    def name(self) -> str:
        return "execute_command"

    @property
    def description(self) -> str:
        return "在系统上执行shell命令。仅用于安全的系统管理和信息查询操作。危险命令会被自动拦截。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的shell命令",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒），默认30",
                    "default": 30,
                },
            },
            "required": ["command"],
        }

    def execute(self, args: dict) -> str:
        command = args.get("command", "")
        timeout = args.get("timeout", 30)

        # 安全检查
        check_result = self._check_command(command)
        if check_result:
            return f"命令被拒绝: {check_result}"

        # 执行命令
        try:
            # 如果使用沙箱，在工作目录下执行
            cwd = self.work_dir if self.sandbox_enabled else None

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env={**os.environ, "PAGER": "cat"},
            )

            output = []
            if result.stdout:
                output.append(result.stdout)
            if result.stderr:
                output.append(f"STDERR: {result.stderr}")

            if not output:
                return f"命令执行成功 (退出码: {result.returncode})"

            return f"退出码: {result.returncode}\n" + "\n".join(output)

        except subprocess.TimeoutExpired:
            return f"命令执行超时 ({timeout}秒)"
        except Exception as e:
            return f"执行错误: {str(e)}"

    def _check_command(self, command: str) -> str | None:
        """
        检查命令是否安全

        Returns:
            如果不安全返回拒绝原因，如果安全返回None
        """
        cmd_lower = command.lower()

        # 检查黑名单
        for blocked in self.blacklist:
            if blocked.lower() in cmd_lower:
                return f"命令包含危险模式: {blocked}"

        # 检查白名单（如果启用了白名单）
        if self.whitelist:
            cmd_parts = shlex.split(command)
            base_cmd = cmd_parts[0] if cmd_parts else ""
            allowed = False
            for allowed_cmd in self.whitelist:
                if base_cmd == allowed_cmd or base_cmd.startswith(allowed_cmd):
                    allowed = True
                    break
            if not allowed:
                return f"命令不在白名单中: {base_cmd}"

        return None
