"""
API Gateway - API网关

核心能力:
1. 统一REST API：所有功能的统一入口
2. 认证中间件：API Key认证
3. 限流器：请求频率限制
4. 路由管理：动态路由注册
5. 请求日志：完整的请求/响应日志

参考:
- FastAPI中间件模式
- API网关设计模式(Kong/Apigee)
- 令牌桶限流算法
"""
import os
import time
import json
import hashlib
import sqlite3
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class RequestLog:
    """请求日志"""
    log_id: str
    method: str
    path: str
    client_id: str
    timestamp: float
    status_code: int = 200
    response_time: float = 0.0
    error: str = ""


@dataclass
class RateLimit:
    """限流配置"""
    max_requests: int = 100
    window_seconds: float = 60.0


class RateLimiter:
    """令牌桶限流器"""

    def __init__(self, rate_limit: RateLimit = None):
        self.rate_limit = rate_limit or RateLimit()
        self._buckets: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求"""
        current_time = time.time()
        window_start = current_time - self.rate_limit.window_seconds

        if client_id not in self._buckets:
            self._buckets[client_id] = []

        # 清理过期记录
        self._buckets[client_id] = [
            t for t in self._buckets[client_id]
            if t > window_start
        ]

        if len(self._buckets[client_id]) >= self.rate_limit.max_requests:
            return False

        self._buckets[client_id].append(current_time)
        return True

    def get_remaining(self, client_id: str) -> int:
        """获取剩余请求数"""
        current_time = time.time()
        window_start = current_time - self.rate_limit.window_seconds

        if client_id not in self._buckets:
            return self.rate_limit.max_requests

        active = [t for t in self._buckets[client_id] if t > window_start]
        return max(0, self.rate_limit.max_requests - len(active))


class AuthManager:
    """认证管理器"""

    def __init__(self, db_path: str = "data/api_keys.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._cache: Dict[str, Dict] = {}

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_hash TEXT PRIMARY KEY,
                name TEXT,
                created_at REAL,
                last_used REAL,
                is_active INTEGER DEFAULT 1,
                permissions TEXT DEFAULT '[]'
            )
        """)
        self.conn.commit()

    def create_key(self, name: str, permissions: List[str] = None) -> str:
        """
        创建API Key

        Args:
            name: 名称
            permissions: 权限列表

        Returns:
            API Key字符串
        """
        import uuid
        key = f"jarvis_{uuid.uuid4().hex}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO api_keys
            (key_hash, name, created_at, last_used, is_active, permissions)
            VALUES (?, ?, ?, 0, 1, ?)
        """, (
            key_hash, name, time.time(),
            json.dumps(permissions or ["read", "write"])
        ))
        self.conn.commit()

        return key

    def validate_key(self, key: str) -> Optional[Dict]:
        """
        验证API Key

        Args:
            key: API Key

        Returns:
            Key信息或None
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        if key_hash in self._cache:
            cached = self._cache[key_hash]
            if cached.get("is_active"):
                return cached
            return None

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE key_hash = ?", (key_hash,))
        row = cursor.fetchone()

        if row and row["is_active"]:
            info = {
                "name": row["name"],
                "permissions": json.loads(row["permissions"]),
                "created_at": row["created_at"],
            }
            self._cache[key_hash] = info

            cursor.execute("UPDATE api_keys SET last_used = ? WHERE key_hash = ?",
                         (time.time(), key_hash))
            self.conn.commit()

            return info

        return None

    def revoke_key(self, key: str) -> bool:
        """撤销API Key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE key_hash = ?", (key_hash,))
        self.conn.commit()
        self._cache.pop(key_hash, None)
        return True


class APIGateway:
    """API网关"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.rate_limiter = RateLimiter(RateLimit(
            max_requests=self.config.get("rate_limit", 100),
            window_seconds=self.config.get("rate_window", 60),
        ))
        self.auth_manager = AuthManager(self.config.get("auth_db", "data/api_keys.db"))
        self.request_logs: List[RequestLog] = []
        self.routes: Dict[str, Callable] = {}
        self.middlewares: List[Callable] = []

    def register_route(self, path: str, handler: Callable, methods: List[str] = None):
        """
        注册路由

        Args:
            path: 路径
            handler: 处理函数
            methods: HTTP方法列表
        """
        methods = methods or ["GET", "POST"]
        for method in methods:
            key = f"{method}:{path}"
            self.routes[key] = handler

    def register_middleware(self, middleware: Callable):
        """注册中间件"""
        self.middlewares.append(middleware)

    def handle_request(
        self,
        method: str,
        path: str,
        client_id: str,
        api_key: str = None,
        body: Dict = None,
    ) -> Dict:
        """
        处理请求

        Args:
            method: HTTP方法
            path: 路径
            client_id: 客户端ID
            api_key: API Key
            body: 请求体

        Returns:
            响应
        """
        import uuid
        start_time = time.time()
        log_id = f"log_{uuid.uuid4().hex[:8]}"

        # 1. 限流检查
        if not self.rate_limiter.is_allowed(client_id):
            return {
                "status": 429,
                "error": "Rate limit exceeded",
                "remaining": 0,
            }

        # 2. 认证检查
        if api_key:
            auth_info = self.auth_manager.validate_key(api_key)
            if not auth_info:
                return {
                    "status": 401,
                    "error": "Invalid API key",
                }
        else:
            # 无API Key时允许有限访问
            auth_info = {"permissions": ["read"]}

        # 3. 路由匹配
        route_key = f"{method}:{path}"
        if route_key not in self.routes:
            return {
                "status": 404,
                "error": f"Route not found: {path}",
            }

        # 4. 执行中间件
        for middleware in self.middlewares:
            try:
                middleware(method, path, client_id, body)
            except Exception:
                pass

        # 5. 执行处理函数
        try:
            handler = self.routes[route_key]
            result = handler(body=body, auth_info=auth_info)
            status_code = 200
        except Exception as e:
            result = {"error": str(e)}
            status_code = 500

        # 6. 记录日志
        response_time = time.time() - start_time
        self.request_logs.append(RequestLog(
            log_id=log_id,
            method=method,
            path=path,
            client_id=client_id,
            timestamp=start_time,
            status_code=status_code,
            response_time=response_time,
        ))

        return {
            "status": status_code,
            "data": result,
            "rate_limit": {
                "remaining": self.rate_limiter.get_remaining(client_id),
            },
        }

    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计"""
        if not self.request_logs:
            return {"total_requests": 0}

        total = len(self.request_logs)
        errors = sum(1 for log in self.request_logs if log.status_code >= 400)
        avg_time = sum(log.response_time for log in self.request_logs) / total

        return {
            "total_requests": total,
            "error_count": errors,
            "error_rate": errors / total if total > 0 else 0,
            "avg_response_time": avg_time,
            "recent_logs": len(self.request_logs[-100:]),
        }

    def get_rate_limit_status(self, client_id: str) -> Dict:
        """获取限流状态"""
        return {
            "remaining": self.rate_limiter.get_remaining(client_id),
            "limit": self.rate_limiter.rate_limit.max_requests,
            "window": self.rate_limiter.rate_limit.window_seconds,
        }
