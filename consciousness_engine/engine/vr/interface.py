"""
交互界面 - 意识引擎与外部世界的接口
"""

from typing import Dict, List, Optional, Callable, Any
import time


class ConsciousnessInterface:
    """
    意识引擎交互界面
    提供输入感知、输出决策、状态查询等接口
    """

    def __init__(self):
        self._input_handlers: List[Callable] = []
        self._output_handlers: List[Callable] = []
        self._event_log: List[Dict] = []
        self.is_active = True

    def register_input_handler(self, handler: Callable):
        """注册输入处理器"""
        self._input_handlers.append(handler)

    def register_output_handler(self, handler: Callable):
        """注册输出处理器"""
        self._output_handlers.append(handler)

    def process_input(self, input_data: Dict) -> List[Any]:
        """
        处理外部输入

        Args:
            input_data: {"type": str, "content": str, "timestamp": float, ...}

        Returns:
            处理器返回结果列表
        """
        input_data["received_at"] = time.time()
        self._log_event("input", input_data)

        results = []
        for handler in self._input_handlers:
            try:
                result = handler(input_data)
                results.append(result)
            except Exception as e:
                self._log_event("error", {"handler": str(handler), "error": str(e)})

        return results

    def process_output(self, output_data: Dict) -> List[Any]:
        """
        处理引擎输出

        Args:
            output_data: {"type": str, "content": str, "priority": float, ...}

        Returns:
            处理器返回结果列表
        """
        output_data["sent_at"] = time.time()
        self._log_event("output", output_data)

        results = []
        for handler in self._output_handlers:
            try:
                result = handler(output_data)
                results.append(result)
            except Exception as e:
                self._log_event("error", {"handler": str(handler), "error": str(e)})

        return results

    def get_event_log(self, limit: int = 50) -> List[Dict]:
        """获取事件日志"""
        return self._event_log[-limit:]

    def _log_event(self, event_type: str, data: Dict):
        """记录事件"""
        self._event_log.append({
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        })

        # 保持日志大小
        if len(self._event_log) > 1000:
            self._event_log = self._event_log[-500:]
