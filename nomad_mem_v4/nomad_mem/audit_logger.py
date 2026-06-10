"""
审计日志 - 记录所有技能调用、用户交互、系统事件

格式: JSONL (JSON Lines)，每行一个JSON对象
"""
import json
import os
import time
from datetime import datetime
from typing import Optional


class AuditLogger:
    """审计日志"""

    def __init__(self, log_dir: str = "data/audit", max_file_size_mb: int = 10):
        """
        初始化审计日志

        Args:
            log_dir: 日志目录
            max_file_size_mb: 单文件最大MB，超过后轮转
        """
        self.log_dir = log_dir
        self.max_file_size = max_file_size_mb * 1024 * 1024
        os.makedirs(log_dir, exist_ok=True)
        self._current_file = None
        self._current_path = None

    def _get_log_path(self) -> str:
        """获取当前日志文件路径（按日期分割）"""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"audit_{today}.jsonl")

    def _rotate_if_needed(self):
        """检查是否需要轮转文件"""
        path = self._get_log_path()
        if self._current_path != path:
            # 新的一天，切换文件
            if self._current_file:
                self._current_file.close()
                self._current_file = None
            self._current_path = path
        elif self._current_file:
            # 检查文件大小
            try:
                size = os.path.getsize(self._current_path)
                if size > self.max_file_size:
                    self._current_file.close()
                    self._current_file = None
                    # 追加时间戳到旧文件
                    timestamp = datetime.now().strftime("%H%M%S")
                    old_path = self._current_path.replace(".jsonl", f"_{timestamp}.jsonl")
                    os.rename(self._current_path, old_path)
            except OSError:
                pass

    def _get_file(self):
        """获取当前文件句柄"""
        self._rotate_if_needed()
        if self._current_file is None:
            self._current_file = open(self._current_path, "a", encoding="utf-8")
        return self._current_file

    def log(self, event_type: str, **kwargs):
        """
        记录审计事件

        Args:
            event_type: 事件类型 (skill_call/user_message/system_event/memory_operation)
            **kwargs: 事件数据
        """
        record = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "event_type": event_type,
            **kwargs,
        }

        f = self._get_file()
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()

    def log_skill_call(self, skill_name: str, args: dict, result: str,
                       user_id: str = "default", success: bool = True, error: str = ""):
        """记录技能调用"""
        self.log(
            "skill_call",
            user_id=user_id,
            skill_name=skill_name,
            args=args,
            result=result[:500],  # 截断过长结果
            success=success,
            error=error,
        )

    def log_user_message(self, message: str, user_id: str = "default", response: str = ""):
        """记录用户消息和AI回复"""
        self.log(
            "user_message",
            user_id=user_id,
            message=message,
            response=response[:500] if response else "",
        )

    def log_system_event(self, event: str, detail: str = "", level: str = "info"):
        """记录系统事件"""
        self.log(
            "system_event",
            event=event,
            detail=detail,
            level=level,
        )

    def log_memory_operation(self, operation: str, detail: str = "", vector_id: int = 0):
        """记录记忆操作"""
        self.log(
            "memory_operation",
            operation=operation,
            detail=detail,
            vector_id=vector_id,
        )

    def close(self):
        """关闭文件"""
        if self._current_file:
            self._current_file.close()
            self._current_file = None
