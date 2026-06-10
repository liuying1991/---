"""意识法则层 - 睡眠系统"""

from typing import Dict, Optional
import time


class SleepSystem:
    """
    意识睡眠系统
    模拟生物睡眠中的记忆巩固过程
    """

    def __init__(self, config: Dict, memory_bridge=None):
        self.config = config
        self.memory_bridge = memory_bridge

        sleep_config = config.get("consciousness", {}).get("sleep", {})
        self.consolidation_interval = sleep_config.get("consolidation_interval", 21600)  # 6小时
        self.importance_threshold = sleep_config.get("importance_threshold", 0.5)

        self.last_consolidation_time = time.time()
        self.is_sleeping = False
        self.sleep_cycle = 0

        self.stats = {
            "total_sleep_cycles": 0,
            "total_consolidated": 0,
            "total_removed": 0,
        }

    def check_and_sleep(self) -> Optional[Dict]:
        """检查是否需要进入睡眠巩固"""
        current_time = time.time()
        elapsed = current_time - self.last_consolidation_time

        if elapsed >= self.consolidation_interval:
            return self.run_sleep_cycle()
        return None

    def run_sleep_cycle(self) -> Dict:
        """执行一个睡眠巩固周期"""
        self.is_sleeping = True
        self.sleep_cycle += 1

        result = {
            "cycle": self.sleep_cycle,
            "reviewed": 0,
            "consolidated": 0,
            "promoted": 0,
            "removed": 0,
        }

        if self.memory_bridge and self.memory_bridge.is_active:
            # 触发海马体→皮层迁移
            # 注意: SleepConsolidation需要直接访问数据库连接
            try:
                from nomad_mem_v4.nomad_mem.sleep.consolidation import SleepConsolidation

                consolidation = SleepConsolidation(
                    self.memory_bridge.vector_store.conn,
                    self.config,
                )
                sleep_result = consolidation.run()
                result.update(sleep_result)
                self.stats["total_consolidated"] += sleep_result.get("consolidated", 0)
                self.stats["total_removed"] += sleep_result.get("removed", 0)
            except (ImportError, Exception):
                pass

            # 触发主动遗忘
            try:
                from nomad_mem_v4.nomad_mem.memory.forget import ForgettingEngine

                forgetting = ForgettingEngine(
                    self.memory_bridge.vector_store.conn,
                    self.config,
                )
                forget_result = forgetting.run()
                result["forgotten"] = forget_result
            except (ImportError, Exception):
                pass

        self.last_consolidation_time = time.time()
        self.is_sleeping = False
        self.stats["total_sleep_cycles"] += 1

        return result

    def force_sleep(self) -> Dict:
        """强制进入睡眠"""
        self.last_consolidation_time = 0
        return self.run_sleep_cycle()

    def get_status(self) -> Dict:
        """获取睡眠系统状态"""
        time_since_last = time.time() - self.last_consolidation_time
        return {
            "is_sleeping": self.is_sleeping,
            "sleep_cycle": self.sleep_cycle,
            "time_since_last_consolidation": time_since_last,
            "next_consolidation_in": max(0, self.consolidation_interval - time_since_last),
            "stats": self.stats,
        }
