"""
Behavior Predictor - 行为预测模块

核心能力:
1. 基于历史模式预测用户需求
2. 追踪时间、序列、上下文三种模式类型
3. 基于频率和近因度的轻量级预测（无ML依赖）
4. 模式随时间衰减（遗忘旧模式）
5. 预测准确度追踪

设计思路:
- 像Jarvis学习Tony Stark的习惯一样，从用户行为历史中学习
- 简单频率统计 + 时间衰减 = 置信度
- SQLite持久化，轻量自包含
"""
import os
import time
import sqlite3
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class NeedPrediction:
    """需求预测结果"""
    predicted_action: str       # 预测的用户下一步行为
    confidence: float           # 置信度 (0.0-1.0)
    trigger_context: str        # 触发该预测的上下文
    suggested_time: float       # 建议执行时间 (unix timestamp)
    pattern_type: str = ""      # 匹配的模式类型: time/sequence/context
    pattern_id: str = ""        # 匹配的模式ID
    frequency: int = 0          # 模式出现频率
    last_seen: float = 0.0      # 模式最近出现时间


class PatternMemory:
    """
    模式记忆存储

    使用SQLite持久化行为模式，支持:
    - 模式存储与检索
    - 频率计数
    - 时间衰减
    - 准确度追踪
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "behavior_patterns.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS behavior_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        context TEXT,
                        timestamp REAL NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS patterns (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,  -- time, sequence, context
                        pattern_key TEXT NOT NULL,   -- 用于快速匹配的模式标识
                        predicted_action TEXT NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        last_seen REAL NOT NULL,
                        first_seen REAL NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        fail_count INTEGER DEFAULT 0,
                        UNIQUE(user_id, pattern_type, pattern_key, predicted_action)
                    );

                    CREATE TABLE IF NOT EXISTS prediction_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        pattern_id TEXT,
                        predicted_action TEXT NOT NULL,
                        actual_action TEXT,
                        confidence REAL,
                        timestamp REAL NOT NULL,
                        matched INTEGER  -- 1=命中, 0=未命中, NULL=待评估
                    );

                    CREATE INDEX IF NOT EXISTS idx_behavior_user
                        ON behavior_records(user_id, timestamp);
                    CREATE INDEX IF NOT EXISTS idx_behavior_action
                        ON behavior_records(user_id, action);
                    CREATE INDEX IF NOT EXISTS idx_patterns_user_type
                        ON patterns(user_id, pattern_type);
                    CREATE INDEX IF NOT EXISTS idx_patterns_key
                        ON patterns(user_id, pattern_key);
                    CREATE INDEX IF NOT EXISTS idx_prediction_log_user
                        ON prediction_log(user_id, timestamp);
                """)
                conn.commit()
            finally:
                conn.close()

    def record_behavior(self, user_id: str, action: str, context: str, timestamp: float):
        """记录一次用户行为"""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO behavior_records (user_id, action, context, timestamp) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, action, context, timestamp),
                )
                conn.commit()
            finally:
                conn.close()

    def store_pattern(
        self,
        user_id: str,
        pattern_type: str,
        pattern_key: str,
        predicted_action: str,
        timestamp: float,
    ) -> str:
        """
        存储或更新一个模式

        Returns:
            pattern_id
        """
        import hashlib
        pattern_id = hashlib.md5(
            f"{user_id}:{pattern_type}:{pattern_key}:{predicted_action}".encode()
        ).hexdigest()[:12]

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """INSERT INTO patterns
                       (id, user_id, pattern_type, pattern_key, predicted_action,
                        frequency, last_seen, first_seen)
                       VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                       ON CONFLICT(user_id, pattern_type, pattern_key, predicted_action)
                       DO UPDATE SET
                           frequency = frequency + 1,
                           last_seen = excluded.last_seen""",
                    (pattern_id, user_id, pattern_type, pattern_key,
                     predicted_action, timestamp, timestamp),
                )
                conn.commit()
            finally:
                conn.close()

        return pattern_id

    def get_patterns(
        self,
        user_id: str,
        pattern_type: str = None,
        pattern_key: str = None,
        min_frequency: int = 1,
    ) -> List[Dict]:
        """检索匹配的模式"""
        with self._lock:
            conn = self._get_conn()
            try:
                query = "SELECT * FROM patterns WHERE user_id = ? AND frequency >= ?"
                params: list = [user_id, min_frequency]

                if pattern_type:
                    query += " AND pattern_type = ?"
                    params.append(pattern_type)
                if pattern_key:
                    query += " AND pattern_key = ?"
                    params.append(pattern_key)

                query += " ORDER BY frequency DESC, last_seen DESC"

                cursor = conn.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            finally:
                conn.close()

    def update_pattern_frequency(self, user_id: str, pattern_id: str, success: bool):
        """更新模式的成功/失败计数"""
        with self._lock:
            conn = self._get_conn()
            try:
                if success:
                    conn.execute(
                        "UPDATE patterns SET success_count = success_count + 1, "
                        "last_seen = ? WHERE id = ? AND user_id = ?",
                        (time.time(), pattern_id, user_id),
                    )
                else:
                    conn.execute(
                        "UPDATE patterns SET fail_count = fail_count + 1 "
                        "WHERE id = ? AND user_id = ?",
                        (pattern_id, user_id),
                    )
                conn.commit()
            finally:
                conn.close()

    def log_prediction(
        self,
        user_id: str,
        pattern_id: str,
        predicted_action: str,
        actual_action: str = None,
        confidence: float = 0.0,
    ):
        """记录一次预测及结果"""
        with self._lock:
            conn = self._get_conn()
            try:
                matched = None
                if actual_action is not None:
                    matched = 1 if actual_action == predicted_action else 0

                conn.execute(
                    """INSERT INTO prediction_log
                       (user_id, pattern_id, predicted_action, actual_action,
                        confidence, timestamp, matched)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, pattern_id, predicted_action, actual_action,
                     confidence, time.time(), matched),
                )
                conn.commit()
            finally:
                conn.close()

    def get_prediction_accuracy(self, user_id: str) -> Dict:
        """获取用户预测准确度统计"""
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute(
                    """SELECT
                         COUNT(*) as total,
                         SUM(CASE WHEN matched = 1 THEN 1 ELSE 0 END) as hits,
                         SUM(CASE WHEN matched = 0 THEN 1 ELSE 0 END) as misses,
                         AVG(CASE WHEN matched IS NOT NULL THEN confidence ELSE NULL END)
                           as avg_confidence
                       FROM prediction_log
                       WHERE user_id = ? AND matched IS NOT NULL""",
                    (user_id,),
                )
                row = cursor.fetchone()
                if row and row[0] > 0:
                    total, hits, misses, avg_conf = row
                    return {
                        "total_predictions": total,
                        "hits": hits,
                        "misses": misses,
                        "accuracy": round(hits / total, 3) if total > 0 else 0.0,
                        "avg_confidence": round(avg_conf, 3) if avg_conf else 0.0,
                    }
                return {
                    "total_predictions": 0,
                    "hits": 0,
                    "misses": 0,
                    "accuracy": 0.0,
                    "avg_confidence": 0.0,
                }
            finally:
                conn.close()

    def get_behavior_history(
        self,
        user_id: str,
        limit: int = 100,
        since: float = None,
    ) -> List[Dict]:
        """获取用户行为历史"""
        with self._lock:
            conn = self._get_conn()
            try:
                query = "SELECT * FROM behavior_records WHERE user_id = ?"
                params: list = [user_id]

                if since is not None:
                    query += " AND timestamp >= ?"
                    params.append(since)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            finally:
                conn.close()

    def prune_old_patterns(self, user_id: str, max_age_days: int = 90):
        """清理超过指定天数的陈旧模式（低频率优先）"""
        cutoff = time.time() - (max_age_days * 86400)
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """DELETE FROM patterns
                       WHERE user_id = ?
                         AND last_seen < ?
                         AND frequency <= 1
                         AND success_count = 0""",
                    (user_id, cutoff),
                )
                conn.commit()
            finally:
                conn.close()

    def close(self):
        """关闭连接（SQLite使用文件级锁，此处为兼容性保留）"""
        pass


class BehaviorPredictor:
    """
    行为预测器

    像Jarvis学习Tony Stark的习惯一样，从用户行为历史中发现模式并预测需求。

    三种模式类型:
    1. time:      基于时间规律（"用户通常在X时间做Y"）
    2. sequence:  基于行为序列（"做完A之后通常做B"）
    3. context:   基于上下文情境（"在X情境下需要Y"）

    置信度计算:
    confidence = base_frequency_score * recency_decay * accuracy_bonus
    - base_frequency_score: 模式出现频率的归一化分数
    - recency_decay:       近因衰减因子（越近越高）
    - accuracy_bonus:      历史准确度加成
    """

    # 模式衰减参数
    RECENCY_HALF_LIFE = 7 * 86400        # 近因半衰期: 7天
    MAX_CONFIDENCE = 0.95                # 置信度上限
    MIN_CONFIDENCE = 0.1                 # 置信度下限
    MIN_FREQUENCY = 2                    # 最低出现次数才参与预测
    MAX_PREDICTIONS = 5                  # 单次最多返回预测数

    def __init__(self, db_path: str = None):
        self.memory = PatternMemory(db_path)
        self._user_cache: Dict[str, Dict] = {}  # 轻量缓存
        self._cache_ttl = 300                   # 缓存5分钟

    def record_behavior(self, user_id: str, action: str, context: str, timestamp: float = None):
        """
        记录用户行为并自动发现模式

        Args:
            user_id:  用户标识
            action:   行为/动作
            context:  上下文（JSON字符串或简单描述）
            timestamp: 时间戳，默认当前时间
        """
        if timestamp is None:
            timestamp = time.time()

        # 1. 记录原始行为
        self.memory.record_behavior(user_id, action, context, timestamp)

        # 2. 自动发现和更新模式
        self._discover_patterns(user_id, action, context, timestamp)

        # 3. 清除用户缓存
        self._invalidate_cache(user_id)

    def predict_next_action(
        self,
        user_id: str,
        current_context: Dict[str, Any],
        max_predictions: int = None,
    ) -> List[NeedPrediction]:
        """
        基于当前上下文预测用户下一步需求

        Args:
            user_id:         用户标识
            current_context: 当前上下文，包含:
                - time:       当前时间戳（或hour/dayofweek）
                - last_action: 上一个行为
                - situation:  当前情境描述
                - 其他自定义字段

        Returns:
            按置信度降序排列的预测列表
        """
        max_predictions = max_predictions or self.MAX_PREDICTIONS
        now = current_context.get("time", time.time())

        predictions: List[NeedPrediction] = []
        seen_actions = set()  # 去重

        # --- 1. 时间模式预测 ---
        hour = self._extract_hour(now)
        day_part = self._extract_day_part(now)
        time_key = f"hour:{hour}|daypart:{day_part}"
        time_patterns = self.memory.get_patterns(user_id, "time", time_key)

        for p in time_patterns:
            if p["predicted_action"] not in seen_actions:
                confidence = self._calculate_confidence(p, now)
                if confidence >= self.MIN_CONFIDENCE:
                    predictions.append(NeedPrediction(
                        predicted_action=p["predicted_action"],
                        confidence=confidence,
                        trigger_context=f"时间模式: {day_part} {hour}:00",
                        suggested_time=now,
                        pattern_type="time",
                        pattern_id=p["id"],
                        frequency=p["frequency"],
                        last_seen=p["last_seen"],
                    ))
                    seen_actions.add(p["predicted_action"])

        # --- 2. 序列模式预测 ---
        last_action = current_context.get("last_action")
        if last_action:
            seq_key = f"after:{last_action}"
            seq_patterns = self.memory.get_patterns(user_id, "sequence", seq_key)

            for p in seq_patterns:
                if p["predicted_action"] not in seen_actions:
                    confidence = self._calculate_confidence(p, now) * 1.1  # 序列模式加权
                    confidence = min(confidence, self.MAX_CONFIDENCE)
                    if confidence >= self.MIN_CONFIDENCE:
                        predictions.append(NeedPrediction(
                            predicted_action=p["predicted_action"],
                            confidence=confidence,
                            trigger_context=f"序列模式: 在 {last_action} 之后",
                            suggested_time=now + 60,  # 建议稍后执行
                            pattern_type="sequence",
                            pattern_id=p["id"],
                            frequency=p["frequency"],
                            last_seen=p["last_seen"],
                        ))
                        seen_actions.add(p["predicted_action"])

        # --- 3. 上下文模式预测 ---
        situation = current_context.get("situation")
        if situation:
            ctx_key = f"situation:{situation}"
            ctx_patterns = self.memory.get_patterns(user_id, "context", ctx_key)

            for p in ctx_patterns:
                if p["predicted_action"] not in seen_actions:
                    confidence = self._calculate_confidence(p, now)
                    if confidence >= self.MIN_CONFIDENCE:
                        predictions.append(NeedPrediction(
                            predicted_action=p["predicted_action"],
                            confidence=confidence,
                            trigger_context=f"情境模式: {situation}",
                            suggested_time=now,
                            pattern_type="context",
                            pattern_id=p["id"],
                            frequency=p["frequency"],
                            last_seen=p["last_seen"],
                        ))
                        seen_actions.add(p["predicted_action"])

        # 按置信度降序排序，取Top-N
        predictions.sort(key=lambda p: p.confidence, reverse=True)
        return predictions[:max_predictions]

    def get_common_patterns(self, user_id: str) -> List[Dict]:
        """
        获取用户常见模式

        Returns:
            模式列表，包含模式描述、频率、准确度等信息
        """
        all_patterns = self.memory.get_patterns(user_id, min_frequency=self.MIN_FREQUENCY)

        result = []
        now = time.time()

        for p in all_patterns:
            accuracy = self._pattern_accuracy(p)
            recency_days = (now - p["last_seen"]) / 86400

            description = self._describe_pattern(p)

            result.append({
                "pattern_id": p["id"],
                "type": p["pattern_type"],
                "description": description,
                "predicted_action": p["predicted_action"],
                "frequency": p["frequency"],
                "accuracy": accuracy,
                "recency_days": round(recency_days, 1),
                "last_seen": p["last_seen"],
            })

        # 按综合得分排序 (频率*40% + 准确度*40% + 近因*20%)
        def score(item):
            recency_score = max(0, 1 - item["recency_days"] / 30)  # 30天内满分
            return (
                item["frequency"] * 0.4 +
                item["accuracy"] * 0.4 +
                recency_score * 0.2
            )

        result.sort(key=score, reverse=True)
        return result

    def update_pattern_frequency(self, user_id: str, pattern_id: str, success: bool):
        """
        更新模式的命中/未命中记录

        Args:
            user_id:   用户标识
            pattern_id: 模式ID
            success:   预测是否成功命中
        """
        self.memory.update_pattern_frequency(user_id, pattern_id, success)

    def get_prediction_accuracy(self, user_id: str) -> Dict:
        """
        获取用户维度的预测准确度统计

        Returns:
            {
                "total_predictions": int,
                "hits": int,
                "misses": int,
                "accuracy": float,    # 0.0-1.0
                "avg_confidence": float,
            }
        """
        return self.memory.get_prediction_accuracy(user_id)

    def close(self):
        """关闭资源"""
        self.memory.close()
        self._user_cache.clear()

    # ------------------------------------------------------------------ #
    #  内部方法                                                            #
    # ------------------------------------------------------------------ #

    def _discover_patterns(
        self, user_id: str, action: str, context: str, timestamp: float
    ):
        """自动发现并存储模式"""
        history = self.memory.get_behavior_history(user_id, limit=10)

        if not history:
            return

        # --- 时间模式 ---
        hour = self._extract_hour(timestamp)
        day_part = self._extract_day_part(timestamp)
        time_key = f"hour:{hour}|daypart:{day_part}"
        self.memory.store_pattern(user_id, "time", time_key, action, timestamp)

        # --- 序列模式 ---
        if len(history) >= 1:
            last_action = history[0]["action"]
            if last_action != action:  # 忽略自环
                seq_key = f"after:{last_action}"
                self.memory.store_pattern(
                    user_id, "sequence", seq_key, action, timestamp
                )

        # --- 上下文模式 ---
        if context:
            ctx_key = f"situation:{context}"
            self.memory.store_pattern(user_id, "context", ctx_key, action, timestamp)

    def _calculate_confidence(self, pattern: Dict, current_time: float) -> float:
        """
        计算模式置信度

        confidence = base_frequency * recency_decay * accuracy_bonus
        """
        freq = pattern["frequency"]
        last_seen = pattern["last_seen"]
        success_count = pattern.get("success_count", 0)
        fail_count = pattern.get("fail_count", 0)

        # 1. 频率分数: log归一化
        base_score = min(1.0, (freq ** 0.5) / 3.0)  # freq=9时约1.0

        # 2. 近因衰减: 指数衰减
        age = current_time - last_seen
        recency_decay = 2 ** (-age / self.RECENCY_HALF_LIFE)

        # 3. 准确度加成
        total_feedback = success_count + fail_count
        if total_feedback > 0:
            accuracy_rate = success_count / total_feedback
            accuracy_bonus = 0.7 + 0.3 * accuracy_rate  # [0.7, 1.0]
        else:
            accuracy_bonus = 0.85  # 无反馈时给默认值

        confidence = base_score * recency_decay * accuracy_bonus
        return round(min(confidence, self.MAX_CONFIDENCE), 3)

    @staticmethod
    def _pattern_accuracy(pattern: Dict) -> float:
        """计算单个模式的历史准确度"""
        total = pattern.get("success_count", 0) + pattern.get("fail_count", 0)
        if total == 0:
            return 0.5  # 无反馈时中性值
        return round(pattern["success_count"] / total, 3)

    @staticmethod
    def _describe_pattern(pattern: Dict) -> str:
        """生成模式的可读描述"""
        ptype = pattern["pattern_type"]
        pkey = pattern["pattern_key"]
        action = pattern["predicted_action"]

        if ptype == "time":
            # 解析 time_key = "hour:X|daypart:Y"
            parts = dict(part.split(":") for part in pkey.split("|") if ":" in part)
            hour = parts.get("hour", "?")
            day_part = parts.get("daypart", "")
            return f"通常在{day_part}{hour}:00会{action}"

        elif ptype == "sequence":
            prev = pkey.replace("after:", "")
            return f"{prev}之后通常会{action}"

        elif ptype == "context":
            situation = pkey.replace("situation:", "")
            return f"在{situation}情境下通常会{action}"

        return f"{pkey} -> {action}"

    @staticmethod
    def _extract_hour(timestamp: float) -> int:
        """从时间戳提取小时"""
        import datetime
        return datetime.datetime.fromtimestamp(timestamp).hour

    @staticmethod
    def _extract_day_part(timestamp: float) -> str:
        """从时间戳提取时间段"""
        import datetime
        hour = datetime.datetime.fromtimestamp(timestamp).hour
        if 5 <= hour < 9:
            return "早晨"
        elif 9 <= hour < 12:
            return "上午"
        elif 12 <= hour < 14:
            return "中午"
        elif 14 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:
            return "深夜"

    def _invalidate_cache(self, user_id: str):
        """清除用户缓存"""
        self._user_cache.pop(user_id, None)
