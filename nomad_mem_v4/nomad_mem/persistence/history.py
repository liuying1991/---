"""
对话历史持久化

将对话历史保存到SQLite，支持重启后恢复
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Optional


class ConversationHistory:
    """对话历史持久化"""

    def __init__(self, db_path: str):
        """
        初始化

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """初始化表"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT DEFAULT ''
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                skill_name TEXT NOT NULL,
                skill_args TEXT NOT NULL,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT DEFAULT ''
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_time ON conversations(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_user ON skill_calls(user_id)")
        self.conn.commit()

    def save_message(self, role: str, content: str, user_id: str = "default", session_id: str = ""):
        """
        保存单条消息

        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
            user_id: 用户ID
            session_id: 会话ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (user_id, role, content, session_id)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, content, session_id))
        self.conn.commit()

    def save_history(self, messages: list[dict], user_id: str = "default", session_id: str = ""):
        """
        批量保存消息列表

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            user_id: 用户ID
            session_id: 会话ID
        """
        cursor = self.conn.cursor()
        for msg in messages:
            cursor.execute("""
                INSERT INTO conversations (user_id, role, content, session_id)
                VALUES (?, ?, ?, ?)
            """, (user_id, msg.get("role", "user"), msg.get("content", ""), session_id))
        self.conn.commit()

    def load_history(self, user_id: str = "default", limit: int = 50) -> list[dict]:
        """
        加载历史消息

        Args:
            user_id: 用户ID
            limit: 最大加载条数

        Returns:
            消息列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT role, content FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))

        messages = []
        for row in cursor.fetchall():
            messages.append({"role": row["role"], "content": row["content"]})

        # 反转使旧消息在前
        messages.reverse()
        return messages

    def record_skill_call(self, skill_name: str, skill_args: dict, result: str,
                         user_id: str = "default", session_id: str = ""):
        """
        记录技能调用

        Args:
            skill_name: 技能名称
            skill_args: 技能参数
            result: 执行结果
            user_id: 用户ID
            session_id: 会话ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO skill_calls (user_id, skill_name, skill_args, result, session_id)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, skill_name, json.dumps(skill_args, ensure_ascii=False), result, session_id))
        self.conn.commit()

    def get_skill_history(self, user_id: str = "default", limit: int = 20) -> list[dict]:
        """
        获取技能调用历史

        Args:
            user_id: 用户ID
            limit: 最大条数

        Returns:
            技能调用记录列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT skill_name, skill_args, result, timestamp
            FROM skill_calls
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))

        records = []
        for row in cursor.fetchall():
            records.append({
                "skill_name": row["skill_name"],
                "skill_args": json.loads(row["skill_args"]),
                "result": row["result"],
                "timestamp": row["timestamp"],
            })
        return records

    def clear_history(self, user_id: str = "default"):
        """清空指定用户的历史"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM skill_calls WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def get_stats(self, user_id: str = "default") -> dict:
        """获取统计信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM conversations WHERE user_id = ?", (user_id,))
        msg_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM skill_calls WHERE user_id = ?", (user_id,))
        skill_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT MIN(timestamp) as first FROM conversations WHERE user_id = ?", (user_id,))
        first_row = cursor.fetchone()
        first_time = first_row["first"] if first_row else None

        return {
            "message_count": msg_count,
            "skill_call_count": skill_count,
            "first_interaction": first_time,
        }

    def close(self):
        """关闭连接"""
        self.conn.close()
