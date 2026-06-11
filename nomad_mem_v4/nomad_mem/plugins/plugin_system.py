"""
Plugin System - 插件系统

核心能力:
1. 动态加载：运行时加载/卸载插件
2. 生命周期：初始化/启动/停止/销毁
3. 依赖管理：插件间依赖关系解析
4. 钩子系统：事件钩子和拦截器
5. 配置隔离：每个插件独立配置

参考:
- OSGi插件架构
- Python entry points (setuptools)
- VS Code插件模型
"""
import time
import importlib
import os
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class PluginStatus(Enum):
    """插件状态"""
    INSTALLED = "installed"
    LOADED = "loaded"
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class PluginInfo:
    """插件信息"""
    plugin_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    status: PluginStatus = PluginStatus.INSTALLED
    config: Dict[str, Any] = field(default_factory=dict)
    hooks: Dict[str, List[Callable]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    loaded_at: float = 0.0
    started_at: float = 0.0


class PluginSystem:
    """插件系统"""

    def __init__(self, plugin_dir: str = "plugins", config: Dict = None):
        self.plugin_dir = plugin_dir
        self.config = config or {}
        self.plugins: Dict[str, PluginInfo] = {}
        self.hook_registry: Dict[str, List[Callable]] = {}
        self.plugin_instances: Dict[str, Any] = {}  # 插件实例

    def register_plugin(
        self,
        plugin_id: str,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        dependencies: List[str] = None,
        config: Dict = None,
    ) -> PluginInfo:
        """
        注册插件

        Args:
            plugin_id: 插件ID
            name: 名称
            version: 版本
            description: 描述
            dependencies: 依赖插件列表
            config: 配置

        Returns:
            插件信息
        """
        plugin = PluginInfo(
            plugin_id=plugin_id,
            name=name,
            version=version,
            description=description,
            dependencies=dependencies or [],
            config=config or {},
        )
        self.plugins[plugin_id] = plugin
        return plugin

    def load_plugin(self, plugin_id: str) -> bool:
        """
        加载插件

        Args:
            plugin_id: 插件ID

        Returns:
            是否成功
        """
        if plugin_id not in self.plugins:
            return False

        plugin = self.plugins[plugin_id]

        # 检查依赖
        for dep in plugin.dependencies:
            if dep not in self.plugins:
                plugin.status = PluginStatus.ERROR
                plugin.metadata["error"] = f"Missing dependency: {dep}"
                return False
            if self.plugins[dep].status not in (PluginStatus.LOADED, PluginStatus.STARTED):
                # 先加载依赖
                if not self.load_plugin(dep):
                    plugin.status = PluginStatus.ERROR
                    plugin.metadata["error"] = f"Failed to load dependency: {dep}"
                    return False

        plugin.status = PluginStatus.LOADED
        plugin.loaded_at = time.time()
        return True

    def start_plugin(self, plugin_id: str) -> bool:
        """
        启动插件

        Args:
            plugin_id: 插件ID

        Returns:
            是否成功
        """
        if plugin_id not in self.plugins:
            return False

        plugin = self.plugins[plugin_id]

        if plugin.status != PluginStatus.LOADED:
            return False

        try:
            # 调用启动钩子
            self._emit_hook("before_plugin_start", plugin_id)
            plugin.status = PluginStatus.STARTED
            plugin.started_at = time.time()
            self._emit_hook("after_plugin_start", plugin_id)
            return True
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.metadata["error"] = str(e)
            return False

    def stop_plugin(self, plugin_id: str) -> bool:
        """停止插件"""
        if plugin_id not in self.plugins:
            return False

        plugin = self.plugins[plugin_id]
        if plugin.status != PluginStatus.STARTED:
            return False

        try:
            self._emit_hook("before_plugin_stop", plugin_id)
            plugin.status = PluginStatus.STOPPED
            self._emit_hook("after_plugin_stop", plugin_id)
            return True
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.metadata["error"] = str(e)
            return False

    def register_hook(self, hook_name: str, callback: Callable, plugin_id: str = None):
        """
        注册钩子

        Args:
            hook_name: 钩子名称
            callback: 回调函数
            plugin_id: 插件ID
        """
        if hook_name not in self.hook_registry:
            self.hook_registry[hook_name] = []

        self.hook_registry[hook_name].append(callback)

        # 同时记录到插件
        if plugin_id and plugin_id in self.plugins:
            if hook_name not in self.plugins[plugin_id].hooks:
                self.plugins[plugin_id].hooks[hook_name] = []
            self.plugins[plugin_id].hooks[hook_name].append(callback)

    def _emit_hook(self, hook_name: str, *args, **kwargs):
        """触发钩子"""
        if hook_name in self.hook_registry:
            for callback in self.hook_registry[hook_name]:
                try:
                    callback(*args, **kwargs)
                except Exception:
                    pass

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        执行钩子并返回结果

        Args:
            hook_name: 钩子名称

        Returns:
            钩子执行结果列表
        """
        results = []
        if hook_name in self.hook_registry:
            for callback in self.hook_registry[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e)})
        return results

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self.plugins.get(plugin_id)

    def get_active_plugins(self) -> List[PluginInfo]:
        """获取活跃的插件"""
        return [
            p for p in self.plugins.values()
            if p.status == PluginStatus.STARTED
        ]

    def get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """获取插件依赖链"""
        if plugin_id not in self.plugins:
            return []

        visited = set()
        deps = []

        def _resolve(pid):
            if pid in visited:
                return
            visited.add(pid)

            if pid in self.plugins:
                for dep in self.plugins[pid].dependencies:
                    _resolve(dep)
                    deps.append(dep)

        _resolve(plugin_id)
        return deps

    def check_dependency_graph(self) -> List[str]:
        """检查依赖图是否有循环依赖"""
        issues = []

        for plugin_id, plugin in self.plugins.items():
            deps = self.get_plugin_dependencies(plugin_id)
            if plugin_id in deps:
                issues.append(f"Circular dependency detected: {plugin_id}")

        return issues

    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        return [
            {
                "plugin_id": p.plugin_id,
                "name": p.name,
                "version": p.version,
                "status": p.status.value,
                "dependencies": p.dependencies,
            }
            for p in self.plugins.values()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """获取插件系统统计"""
        status_counts = {}
        for plugin in self.plugins.values():
            status = plugin.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_plugins": len(self.plugins),
            "status_distribution": status_counts,
            "registered_hooks": len(self.hook_registry),
        }
