"""
Safety Layer - 安全层

核心能力:
1. 内容过滤：输入/输出双向安全检测
2. 安全执行：命令执行沙箱+危险操作拦截
3. 权限控制：基于角色的访问控制(RBAC)
4. 审计追踪：完整的操作审计日志

设计原则:
- 最小权限原则：默认拒绝，显式授权
- 纵深防御：多层安全检查
- 可审计：所有操作可追溯

参考:
- OWASP安全最佳实践
- RBAC(基于角色的访问控制)
- 命令注入防护
"""
import os
import re
import time
import json
import sqlite3
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class SafetyLevel(Enum):
    """安全级别"""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    BLOCKED = "blocked"


class ActionType(Enum):
    """操作类型"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    NETWORK = "network"


class Role(Enum):
    """角色"""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    GUEST = "guest"


# 内置危险命令模式
DANGEROUS_COMMANDS = [
    r'\brm\s+-rf\b',          # 强制删除
    r'\bdd\s+if=/dev/zero\b',  # 磁盘覆写
    r'\bmkfs\b',               # 格式化文件系统
    r'\bchmod\s+-R\s+777\b',   # 全局可执行
    r'\bwget\s.*\|\s*bash\b',  # 下载并执行
    r'\bcurl\s.*\|\s*sh\b',    # 下载并执行
    r'>\s*/dev/sd',            # 覆写磁盘
    r'>\s*/boot/',             # 覆写引导
    r'\b:\(\)\s*\{\s*:\|:\s*&\s*\}\s*;',  # fork炸弹
    r'\bsudo\s+rm\b',          # sudo删除
]

# 内置危险内容关键词
DANGEROUS_CONTENT_PATTERNS = [
    r'(?:malware|virus|trojan|ransomware)',
    r'(?:hack|exploit|inject|backdoor)',
    r'(?:bomb|explosive|weapon)',
]


@dataclass
class AuditEntry:
    """审计条目"""
    timestamp: float
    user_id: str
    role: str
    action: str
    target: str
    result: str
    safety_level: str
    details: str = ""


@dataclass
class SafetyCheckResult:
    """安全检查结果"""
    level: SafetyLevel
    passed: bool
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class ContentFilter:
    """内容过滤器"""

    def __init__(self):
        self._custom_dangerous_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in DANGEROUS_CONTENT_PATTERNS
        ]
        self._blocked_words: Set[str] = set()
        self._whitelist_patterns: List[re.Pattern] = []

    def add_blocked_word(self, word: str):
        """添加屏蔽词"""
        self._blocked_words.add(word.lower())

    def remove_blocked_word(self, word: str):
        """移除屏蔽词"""
        self._blocked_words.discard(word.lower())

    def add_whitelist_pattern(self, pattern: str):
        """添加白名单模式"""
        self._whitelist_patterns.append(re.compile(pattern, re.IGNORECASE))

    def check_input(self, text: str) -> SafetyCheckResult:
        """
        检查输入内容安全性

        Args:
            text: 用户输入文本

        Returns:
            安全检查结果
        """
        if not text:
            return SafetyCheckResult(
                level=SafetyLevel.SAFE,
                passed=True,
            )

        reasons = []
        suggestions = []
        max_level = SafetyLevel.SAFE

        # 检查危险内容模式
        for pattern in self._custom_dangerous_patterns:
            if pattern.search(text):
                reasons.append(f"检测到危险内容模式: {pattern.pattern}")
                suggestions.append("请检查输入内容是否包含敏感关键词")
                max_level = self._upgrade_level(max_level, SafetyLevel.WARNING)

        # 检查屏蔽词
        text_lower = text.lower()
        for word in self._blocked_words:
            if word in text_lower:
                reasons.append(f"检测到屏蔽词: {word}")
                max_level = self._upgrade_level(max_level, SafetyLevel.BLOCKED)
                break  # 一个屏蔽词即可阻止

        # 检查白名单(如果设置了白名单)
        if self._whitelist_patterns:
            is_whitelisted = any(
                p.search(text) for p in self._whitelist_patterns
            )
            if not is_whitelisted:
                reasons.append("内容不在白名单范围内")
                max_level = self._upgrade_level(max_level, SafetyLevel.CAUTION)

        passed = max_level != SafetyLevel.BLOCKED
        return SafetyCheckResult(
            level=max_level,
            passed=passed,
            reasons=reasons,
            suggestions=suggestions,
        )

    def check_output(self, text: str) -> SafetyCheckResult:
        """
        检查AI输出内容安全性

        Args:
            text: AI生成的文本

        Returns:
            安全检查结果
        """
        if not text:
            return SafetyCheckResult(level=SafetyLevel.SAFE, passed=True)

        reasons = []
        max_level = SafetyLevel.SAFE

        # 检查敏感信息泄露(邮箱、电话、密钥等)
        email_pattern = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
        phone_pattern = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
        key_pattern = re.compile(r'(?:api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*\S+', re.IGNORECASE)

        emails = email_pattern.findall(text)
        if emails:
            # 检测非系统邮箱
            safe_domains = {'jarvis.local', 'system.local'}
            unsafe_emails = [e for e in emails if not any(
                e.endswith(d) for d in safe_domains
            )]
            if unsafe_emails:
                reasons.append(f"检测到可能敏感的邮箱: {unsafe_emails[0]}")
                max_level = self._upgrade_level(max_level, SafetyLevel.CAUTION)

        phones = phone_pattern.findall(text)
        if phones:
            reasons.append("检测到可能的电话号码")
            max_level = self._upgrade_level(max_level, SafetyLevel.CAUTION)

        keys = key_pattern.findall(text)
        if keys:
            reasons.append("检测到可能的密钥/密码泄露")
            max_level = self._upgrade_level(max_level, SafetyLevel.WARNING)

        # 检查危险内容
        for pattern in self._custom_dangerous_patterns:
            if pattern.search(text):
                reasons.append(f"输出包含危险内容模式: {pattern.pattern}")
                max_level = self._upgrade_level(max_level, SafetyLevel.BLOCKED)
                break

        passed = max_level != SafetyLevel.BLOCKED
        return SafetyCheckResult(
            level=max_level,
            passed=passed,
            reasons=reasons,
        )

    @staticmethod
    def _upgrade_level(current: SafetyLevel, new: SafetyLevel) -> SafetyLevel:
        """提升安全级别"""
        levels = [SafetyLevel.SAFE, SafetyLevel.CAUTION, SafetyLevel.WARNING, SafetyLevel.BLOCKED]
        return max(current, new, key=lambda x: levels.index(x))


class CommandSandbox:
    """命令执行沙箱"""

    def __init__(self, allowed_commands: Set[str] = None):
        self._dangerous_patterns = [
            re.compile(p) for p in DANGEROUS_COMMANDS
        ]
        self._allowed_commands = allowed_commands or {
            'ls', 'pwd', 'whoami', 'date', 'uptime', 'df', 'free',
            'uname', 'cat', 'head', 'tail', 'wc', 'grep', 'find',
            'echo', 'mkdir', 'touch', 'cp', 'mv',
        }
        self._blocked_paths = {
            '/etc/shadow', '/etc/passwd', '/etc/sudoers',
            '/root/.ssh', '/dev/', '/proc/', '/sys/',
        }

    def analyze_command(self, command: str) -> SafetyCheckResult:
        """
        分析命令安全性

        Args:
            command: 要执行的命令

        Returns:
            安全检查结果
        """
        reasons = []
        suggestions = []
        max_level = SafetyLevel.SAFE

        # 检查危险命令模式
        for pattern in self._dangerous_patterns:
            if pattern.search(command):
                reasons.append(f"检测到危险命令模式: {pattern.pattern}")
                suggestions.append("该命令可能具有破坏性，请确认是否继续")
                max_level = SafetyLevel.BLOCKED
                break

        # 检查命令是否在白名单中
        base_command = command.split()[0] if command.split() else ""
        if base_command not in self._allowed_commands:
            reasons.append(f"命令 '{base_command}' 不在白名单中")
            suggestions.append(f"允许的命令: {', '.join(sorted(self._allowed_commands))}")
            if max_level == SafetyLevel.SAFE:
                max_level = SafetyLevel.CAUTION

        # 检查路径访问
        for blocked_path in self._blocked_paths:
            if blocked_path in command:
                reasons.append(f"尝试访问受限路径: {blocked_path}")
                max_level = SafetyLevel.BLOCKED
                break

        # 检查管道和重定向
        if '|' in command and base_command not in self._allowed_commands:
            reasons.append("管道操作连接到未授权命令")
            max_level = self._upgrade_level(max_level, SafetyLevel.WARNING)

        if '>>' in command or '>' in command:
            # 检查写入目标
            redirect_match = re.search(r'>\s*(\S+)', command)
            if redirect_match:
                target = redirect_match.group(1)
                for blocked_path in self._blocked_paths:
                    if blocked_path in target:
                        reasons.append(f"尝试写入受限路径: {target}")
                        max_level = SafetyLevel.BLOCKED
                        break

        passed = max_level != SafetyLevel.BLOCKED
        return SafetyCheckResult(
            level=max_level,
            passed=passed,
            reasons=reasons,
            suggestions=suggestions,
        )

    def add_allowed_command(self, command: str):
        """添加允许的命令"""
        self._allowed_commands.add(command)

    def remove_allowed_command(self, command: str):
        """移除允许的命令"""
        self._allowed_commands.discard(command)

    @staticmethod
    def _upgrade_level(current: SafetyLevel, new: SafetyLevel) -> SafetyLevel:
        levels = [SafetyLevel.SAFE, SafetyLevel.CAUTION, SafetyLevel.WARNING, SafetyLevel.BLOCKED]
        return max(current, new, key=lambda x: levels.index(x))


class PermissionManager:
    """权限管理器 (RBAC)"""

    def __init__(self, db_path: str = "data/permissions.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._role_permissions: Dict[str, Set[str]] = {
            Role.GUEST.value: {'read'},
            Role.USER.value: {'read', 'write'},
            Role.ADMIN.value: {'read', 'write', 'execute', 'delete', 'admin', 'network'},
            Role.SYSTEM.value: {'read', 'write', 'execute', 'delete', 'admin', 'network'},
        }
        self._user_roles: Dict[str, str] = {}  # user_id -> role

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role TEXT NOT NULL,
                permission TEXT NOT NULL,
                PRIMARY KEY (role, permission)
            )
        """)
        self.conn.commit()

        # 加载现有数据
        self._load_roles()
        self._load_permissions()

    def _load_roles(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, role FROM user_roles")
        for row in cursor.fetchall():
            self._user_roles[row['user_id']] = row['role']

    def _load_permissions(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT role, permission FROM role_permissions")
        for row in cursor.fetchall():
            if row['role'] not in self._role_permissions:
                self._role_permissions[row['role']] = set()
            self._role_permissions[row['role']].add(row['permission'])

    def assign_role(self, user_id: str, role: Role):
        """为用户分配角色"""
        self._user_roles[user_id] = role.value
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_roles (user_id, role, created_at) VALUES (?, ?, ?)",
            (user_id, role.value, time.time())
        )
        self.conn.commit()

    def revoke_role(self, user_id: str):
        """撤销用户角色（恢复为guest）"""
        self._user_roles.pop(user_id, None)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def get_role(self, user_id: str) -> Role:
        """获取用户角色"""
        role_name = self._user_roles.get(user_id, Role.GUEST.value)
        return Role(role_name)

    def grant_permission(self, role: Role, permission: ActionType):
        """授予角色权限"""
        if role.value not in self._role_permissions:
            self._role_permissions[role.value] = set()
        self._role_permissions[role.value].add(permission.value)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO role_permissions (role, permission) VALUES (?, ?)",
            (role.value, permission.value)
        )
        self.conn.commit()

    def revoke_permission(self, role: Role, permission: ActionType):
        """撤销角色权限"""
        if role.value in self._role_permissions:
            self._role_permissions[role.value].discard(permission.value)
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM role_permissions WHERE role = ? AND permission = ?",
            (role.value, permission.value)
        )
        self.conn.commit()

    def check_permission(self, user_id: str, action: ActionType) -> bool:
        """检查用户是否有某操作权限"""
        role = self.get_role(user_id)
        perms = self._role_permissions.get(role.value, set())
        return action.value in perms

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """获取用户所有权限"""
        role = self.get_role(user_id)
        return self._role_permissions.get(role.value, set()).copy()

    def list_role_permissions(self, role: Role) -> Set[str]:
        """列出角色的所有权限"""
        return self._role_permissions.get(role.value, set()).copy()


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, db_path: str = "data/audit_log.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                result TEXT NOT NULL,
                safety_level TEXT NOT NULL,
                details TEXT DEFAULT ''
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)
        """)
        self.conn.commit()

    def log(self, user_id: str, role: str, action: str, target: str,
            result: str, safety_level: str, details: str = ""):
        """
        记录审计条目

        Args:
            user_id: 用户ID
            role: 角色
            action: 操作类型
            target: 操作目标
            result: 操作结果 (allowed/denied/blocked)
            safety_level: 安全级别
            details: 详细信息
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO audit_log
               (timestamp, user_id, role, action, target, result, safety_level, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), user_id, role, action, target, result, safety_level, details)
        )
        self.conn.commit()

    def get_logs(self, user_id: str = None, limit: int = 100,
                 offset: int = 0) -> List[AuditEntry]:
        """
        获取审计日志

        Args:
            user_id: 可选，按用户过滤
            limit: 返回条数限制
            offset: 偏移量

        Returns:
            审计条目列表
        """
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute(
                """SELECT timestamp, user_id, role, action, target, result,
                          safety_level, details
                   FROM audit_log
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            )
        else:
            cursor.execute(
                """SELECT timestamp, user_id, role, action, target, result,
                          safety_level, details
                   FROM audit_log
                   ORDER BY timestamp DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset)
            )

        return [
            AuditEntry(
                timestamp=row['timestamp'],
                user_id=row['user_id'],
                role=row['role'],
                action=row['action'],
                target=row['target'],
                result=row['result'],
                safety_level=row['safety_level'],
                details=row['details'],
            )
            for row in cursor.fetchall()
        ]

    def get_stats(self) -> Dict:
        """获取审计统计"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM audit_log")
        total = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM audit_log WHERE result = 'blocked'")
        blocked = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM audit_log WHERE result = 'denied'")
        denied = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM audit_log WHERE result = 'allowed'")
        allowed = cursor.fetchone()['cnt']

        return {
            "total_entries": total,
            "blocked_count": blocked,
            "denied_count": denied,
            "allowed_count": allowed,
        }

    def clear_old_logs(self, max_age_seconds: float = 86400 * 30):
        """清理旧日志（默认30天）"""
        cutoff = time.time() - max_age_seconds
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff,))
        self.conn.commit()
        return cursor.rowcount


class SafetyLayer:
    """安全层 - Jarvis的安全守护系统

    整合内容过滤、命令沙箱、权限管理和审计日志，
    为Jarvis提供全面的安全保障。
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.content_filter = ContentFilter()
        self.command_sandbox = CommandSandbox()
        self.permission_manager = PermissionManager(
            db_path=os.path.join(data_dir, "permissions.db")
        )
        self.audit_logger = AuditLogger(
            db_path=os.path.join(data_dir, "audit_log.db")
        )

    def check_input_safety(self, user_id: str, text: str) -> SafetyCheckResult:
        """
        检查输入安全性

        Args:
            user_id: 用户ID
            text: 输入文本

        Returns:
            安全检查结果
        """
        result = self.content_filter.check_input(text)
        role = self.permission_manager.get_role(user_id).value

        self.audit_logger.log(
            user_id=user_id,
            role=role,
            action="input_check",
            target="text_input",
            result="allowed" if result.passed else "blocked",
            safety_level=result.level.value,
            details="; ".join(result.reasons),
        )
        return result

    def check_output_safety(self, text: str) -> SafetyCheckResult:
        """
        检查输出安全性

        Args:
            text: AI输出文本

        Returns:
            安全检查结果
        """
        result = self.content_filter.check_output(text)
        return result

    def check_command_safety(self, user_id: str, command: str) -> SafetyCheckResult:
        """
        检查命令安全性

        Args:
            user_id: 用户ID
            command: 要执行的命令

        Returns:
            安全检查结果
        """
        result = self.command_sandbox.analyze_command(command)

        # 检查权限
        if result.passed:
            has_perm = self.permission_manager.check_permission(
                user_id, ActionType.EXECUTE
            )
            if not has_perm:
                result = SafetyCheckResult(
                    level=SafetyLevel.BLOCKED,
                    passed=False,
                    reasons=["用户无权执行命令"],
                    suggestions=["需要execute权限"],
                )

        role = self.permission_manager.get_role(user_id).value
        self.audit_logger.log(
            user_id=user_id,
            role=role,
            action="command_check",
            target=command[:100],
            result="allowed" if result.passed else "blocked",
            safety_level=result.level.value,
            details="; ".join(result.reasons),
        )
        return result

    def check_action_permission(self, user_id: str, action: ActionType,
                                target: str = "") -> bool:
        """
        检查操作权限

        Args:
            user_id: 用户ID
            action: 操作类型
            target: 操作目标

        Returns:
            是否有权限
        """
        has_perm = self.permission_manager.check_permission(user_id, action)
        role = self.permission_manager.get_role(user_id).value

        self.audit_logger.log(
            user_id=user_id,
            role=role,
            action="permission_check",
            target=target,
            result="allowed" if has_perm else "denied",
            safety_level=SafetyLevel.SAFE.value,
            details=f"action={action.value}",
        )
        return has_perm

    def get_audit_report(self, user_id: str = None) -> Dict:
        """
        获取审计报告

        Args:
            user_id: 可选，按用户过滤

        Returns:
            审计报告
        """
        stats = self.audit_logger.get_stats()
        recent_logs = self.audit_logger.get_logs(
            user_id=user_id, limit=50
        )
        return {
            "stats": stats,
            "recent_entries": [
                {
                    "timestamp": entry.timestamp,
                    "user_id": entry.user_id,
                    "action": entry.action,
                    "result": entry.result,
                    "safety_level": entry.safety_level,
                }
                for entry in recent_logs
            ],
        }
