"""
工具执行器模块 - 带超时控制、结果校验和错误处理的工具执行器。
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ExecutionResult:
    """单次工具执行结果"""
    tool_id: str
    success: bool
    result_data: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ExecutionStatus = ExecutionStatus.PENDING


# ---------------------------------------------------------------------------
# ToolExecutor
# ---------------------------------------------------------------------------

class ToolExecutor:
    """
    工具执行器 —— 以安全、可控的方式执行已注册工具。

    职责:
    - 带超时控制的工具执行（同步/异步）
    - 结果格式校验
    - 执行历史追踪
    - 执行取消
    - 统计信息
    """

    def __init__(self, default_timeout: float = 30.0, max_history: int = 200):
        self._default_timeout = default_timeout
        self._max_history = max_history
        self._history: Deque[ExecutionResult] = deque(maxlen=max_history)

        # 运行中的线程: execution_id -> threading.Thread
        self._running: Dict[str, threading.Thread] = {}
        # 运行中的结果容器: execution_id -> {"result": ..., "done": threading.Event}
        self._pending_results: Dict[str, Dict[str, Any]] = {}
        # 取消标记: execution_id -> bool
        self._cancel_flags: Dict[str, bool] = {}

    # -- core execution (async, fire-and-forget via thread) ----------------

    def execute(
        self,
        tool_id: str,
        handler: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> ExecutionResult:
        """
        在线程中执行工具，不阻塞调用方。

        立即返回一个 PENDING 状态的 ExecutionResult；实际结果会记录到历史中。

        Args:
            tool_id: 工具 ID
            handler: 工具处理函数
            args: 位置参数
            kwargs: 关键字参数
            timeout: 超时秒数，默认使用 default_timeout

        Returns:
            一个 PENDING 状态的 ExecutionResult（含 execution_id）
        """
        _timeout = timeout if timeout is not None else self._default_timeout
        _kwargs = kwargs or {}
        execution_id = str(uuid.uuid4())
        start_time = time.monotonic()

        pending: Dict[str, Any] = {"result": None, "done": threading.Event()}
        self._pending_results[execution_id] = pending
        self._cancel_flags[execution_id] = False

        def _runner():
            try:
                result_data = handler(*args, **_kwargs)
                elapsed = time.monotonic() - start_time
                if self._cancel_flags.get(execution_id, False):
                    er = ExecutionResult(
                        tool_id=tool_id,
                        success=False,
                        result_data=None,
                        error="Execution cancelled",
                        execution_time=elapsed,
                        execution_id=execution_id,
                        status=ExecutionStatus.CANCELLED,
                    )
                else:
                    er = ExecutionResult(
                        tool_id=tool_id,
                        success=True,
                        result_data=result_data,
                        execution_time=elapsed,
                        execution_id=execution_id,
                        status=ExecutionStatus.SUCCESS,
                    )
            except Exception as exc:
                elapsed = time.monotonic() - start_time
                er = ExecutionResult(
                    tool_id=tool_id,
                    success=False,
                    result_data=None,
                    error=f"{type(exc).__name__}: {exc}",
                    execution_time=elapsed,
                    execution_id=execution_id,
                    status=ExecutionStatus.FAILED,
                )
            finally:
                pending["result"] = er
                pending["done"].set()
                self._pending_results.pop(execution_id, None)
                self._cancel_flags.pop(execution_id, None)
                self._history.append(er)
                self._running.pop(execution_id, None)
                if er.status == ExecutionStatus.SUCCESS:
                    logger.info("Tool %s executed in %.3fs", tool_id, elapsed)
                else:
                    logger.warning(
                        "Tool %s finished with %s after %.3fs: %s",
                        tool_id, er.status.value, elapsed, er.error,
                    )

        t = threading.Thread(target=_runner, name=f"exec-{tool_id}", daemon=True)
        self._running[execution_id] = t
        t.start()

        pending_er = ExecutionResult(
            tool_id=tool_id,
            success=False,
            result_data=None,
            execution_time=0,
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
        )
        return pending_er

    # -- synchronous execution with timeout --------------------------------

    def execute_sync(
        self,
        tool_id: str,
        handler: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> ExecutionResult:
        """
        同步执行工具并等待结果，超时则取消。

        Args:
            tool_id: 工具 ID
            handler: 工具处理函数
            args: 位置参数
            kwargs: 关键字参数
            timeout: 超时秒数

        Returns:
            最终 ExecutionResult（SUCCESS / FAILED / TIMEOUT / CANCELLED）
        """
        _timeout = timeout if timeout is not None else self._default_timeout
        _kwargs = kwargs or {}
        execution_id = str(uuid.uuid4())
        start_time = time.monotonic()

        pending: Dict[str, Any] = {"result": None, "done": threading.Event()}
        self._pending_results[execution_id] = pending
        self._cancel_flags[execution_id] = False

        def _runner():
            try:
                result_data = handler(*args, **_kwargs)
                elapsed = time.monotonic() - start_time
                if self._cancel_flags.get(execution_id, False):
                    er = ExecutionResult(
                        tool_id=tool_id,
                        success=False,
                        result_data=None,
                        error="Execution cancelled",
                        execution_time=elapsed,
                        execution_id=execution_id,
                        status=ExecutionStatus.CANCELLED,
                    )
                else:
                    er = ExecutionResult(
                        tool_id=tool_id,
                        success=True,
                        result_data=result_data,
                        execution_time=elapsed,
                        execution_id=execution_id,
                        status=ExecutionStatus.SUCCESS,
                    )
            except Exception as exc:
                elapsed = time.monotonic() - start_time
                er = ExecutionResult(
                    tool_id=tool_id,
                    success=False,
                    result_data=None,
                    error=f"{type(exc).__name__}: {exc}",
                    execution_time=elapsed,
                    execution_id=execution_id,
                    status=ExecutionStatus.FAILED,
                )
            finally:
                pending["result"] = er
                pending["done"].set()
                self._pending_results.pop(execution_id, None)
                self._cancel_flags.pop(execution_id, None)
                self._history.append(er)
                self._running.pop(execution_id, None)

        t = threading.Thread(target=_runner, name=f"exec-sync-{tool_id}", daemon=True)
        self._running[execution_id] = t
        t.start()

        completed = pending["done"].wait(timeout=_timeout)
        if not completed:
            # Timeout: set cancel flag, return timeout result
            self._cancel_flags[execution_id] = True
            elapsed = time.monotonic() - start_time
            er = ExecutionResult(
                tool_id=tool_id,
                success=False,
                result_data=None,
                error=f"Execution timed out after {_timeout}s",
                execution_time=elapsed,
                execution_id=execution_id,
                status=ExecutionStatus.TIMEOUT,
            )
            # Thread will still run but result won't be stored
            self._pending_results.pop(execution_id, None)
            self._cancel_flags.pop(execution_id, None)
            self._running.pop(execution_id, None)
            self._history.append(er)
            logger.warning("Tool %s timed out after %.3fs", tool_id, elapsed)
            return er

        result = pending["result"]
        return result

    # -- result validation --------------------------------------------------

    def validate_result(self, result: Any, tool_schema: Dict[str, Any]) -> bool:
        """
        校验结果是否符合预期 Schema。

        支持基本类型检查：
        - "type": "string" / "integer" / "number" / "boolean" / "array" / "object"

        Args:
            result: 执行结果数据
            tool_schema: 期望的 JSON Schema 片段

        Returns:
            是否匹配
        """
        expected_type = tool_schema.get("type")
        if expected_type is None:
            # 无 schema 则认为校验通过
            return True

        type_map = {
            "string": str,
            "str": str,
            "integer": int,
            "int": int,
            "number": (int, float),
            "float": (int, float),
            "boolean": bool,
            "bool": bool,
            "array": (list, tuple),
            "list": (list, tuple),
            "object": dict,
            "dict": dict,
        }

        expected_py_type = type_map.get(expected_type)
        if expected_py_type is None:
            logger.warning("Unknown schema type: %s", expected_type)
            return True

        # bool is subclass of int in Python, special-case it
        if expected_py_type == int and isinstance(result, bool):
            return False

        return isinstance(result, expected_py_type)

    # -- history -------------------------------------------------------------

    def get_execution_history(
        self,
        tool_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[ExecutionResult]:
        """
        获取执行历史，按时间倒序排列。

        Args:
            tool_id: 可选，按工具 ID 过滤
            limit: 最大返回条数

        Returns:
            ExecutionResult 列表
        """
        items = list(self._history)
        if tool_id is not None:
            items = [r for r in items if r.tool_id == tool_id]
        # 倒序：最新的在前
        items.reverse()
        return items[:limit]

    # -- cancellation --------------------------------------------------------

    def cancel_execution(self, execution_id: str) -> bool:
        """
        取消一个正在执行的工具调用。

        Args:
            execution_id: 执行 ID

        Returns:
            是否成功标记取消（线程可能仍在运行但结果会被忽略）
        """
        if execution_id in self._running or execution_id in self._pending_results:
            self._cancel_flags[execution_id] = True
            logger.info("Cancelled execution %s", execution_id)
            return True
        return False

    # -- stats ---------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """
        返回执行器统计信息。

        Returns:
            包含 total_executions, success_rate, avg_execution_time, by_tool 的字典
        """
        history = list(self._history)
        total = len(history)
        if total == 0:
            return {
                "total_executions": 0,
                "success_count": 0,
                "failure_count": 0,
                "timeout_count": 0,
                "cancel_count": 0,
                "success_rate": 1.0,
                "avg_execution_time": 0.0,
                "by_tool": {},
            }

        success_count = sum(1 for r in history if r.status == ExecutionStatus.SUCCESS)
        failure_count = sum(1 for r in history if r.status == ExecutionStatus.FAILED)
        timeout_count = sum(1 for r in history if r.status == ExecutionStatus.TIMEOUT)
        cancel_count = sum(1 for r in history if r.status == ExecutionStatus.CANCELLED)
        total_time = sum(r.execution_time for r in history)

        by_tool: Dict[str, Dict[str, Any]] = {}
        for r in history:
            if r.tool_id not in by_tool:
                by_tool[r.tool_id] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "timeout": 0,
                    "cancelled": 0,
                    "total_time": 0.0,
                }
            entry = by_tool[r.tool_id]
            entry["total"] += 1
            if r.status == ExecutionStatus.SUCCESS:
                entry["success"] += 1
            elif r.status == ExecutionStatus.FAILED:
                entry["failed"] += 1
            elif r.status == ExecutionStatus.TIMEOUT:
                entry["timeout"] += 1
            elif r.status == ExecutionStatus.CANCELLED:
                entry["cancelled"] += 1
            entry["total_time"] += r.execution_time

        for entry in by_tool.values():
            entry["avg_time"] = entry["total_time"] / entry["total"] if entry["total"] else 0.0

        return {
            "total_executions": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "timeout_count": timeout_count,
            "cancel_count": cancel_count,
            "success_rate": success_count / total if total else 1.0,
            "avg_execution_time": total_time / total if total else 0.0,
            "by_tool": by_tool,
        }

    # -- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        """清理执行器资源。"""
        self._cancel_flags.clear()
        self._pending_results.clear()
        self._history.clear()
        self._running.clear()
        logger.info("ToolExecutor closed")
