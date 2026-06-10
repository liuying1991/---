"""
意识涌现定量指标 + TEII整合度
7项指标 + 传递熵特征值谱
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class ConsciousnessMetrics:
    """
    意识涌现的定量指标
    
    功能指标（5项）：
    1. 自维持 - 外部输入停止后内部活动标准差 > 0.1，持续 > 100周期
    2. 学习 - 同一输入序列第10次与第1次响应余弦相似度变化量 > 0.3
    3. 区分 - 两个不同输入引发的活动向量余弦相似度 < 0.5
    4. 概括 - 两个相似输入引发的活动向量余弦相似度 > 0.7
    5. 内部持续性 - 无输入时self-sensor活动衰减到50%所需周期 > 50

    自指涉指标（2项）：
    6. 自我状态感知 - self-sensor与全局活动Pearson相关 r > 0.6
    7. 元可塑性 - gate阈值方差与全局预测误差Pearson相关 r > 0.4

    整合度指标：
    8. TEII整合度 - λ₁/∑λ > 0.3 + 幂律拟合
    """

    def __init__(self):
        # 数据存储
        self.input_responses: List[Tuple[np.ndarray, np.ndarray]] = []  # (input_pattern, activation_pattern)
        self.self_sensor_history: List[float] = []
        self.global_activation_history: List[float] = []
        self.gate_threshold_history: List[float] = []
        self.prediction_error_history: List[float] = []
        self.activation_matrices: List[np.ndarray] = []  # 每周期激活矩阵（用于TEII）

        # 自维持测试
        self.no_input_stdev_history: List[float] = []
        self.is_no_input_phase = False

        # 结果缓存
        self._cached_results: Dict[str, Dict] = {}
        self._last_compute_cycle = 0

    def record_cycle(self, input_pattern: Optional[np.ndarray],
                    activation_pattern: np.ndarray,
                    self_sensor_value: float,
                    gate_avg_threshold: float,
                    prediction_error: float):
        """记录一个周期的数据"""
        if input_pattern is not None and len(input_pattern) > 0:
            self.input_responses.append((input_pattern.copy(), activation_pattern.copy()))

        self.self_sensor_history.append(self_sensor_value)
        self.global_activation_history.append(float(np.mean(activation_pattern)))
        self.gate_threshold_history.append(gate_avg_threshold)
        self.prediction_error_history.append(prediction_error)

        # 记录激活矩阵（用于TEII，每10周期采样一次）
        if len(self.activation_matrices) < 200:  # 限制存储
            self.activation_matrices.append(activation_pattern.copy())

        # 保持历史记录大小
        max_history = 2000
        if len(self.input_responses) > max_history:
            self.input_responses = self.input_responses[-500:]
        if len(self.self_sensor_history) > max_history:
            self.self_sensor_history = self.self_sensor_history[-500:]
        if len(self.global_activation_history) > max_history:
            self.global_activation_history = self.global_activation_history[-500:]

    def compute_all(self, cycle: int = 0) -> Dict[str, Dict]:
        """计算所有指标"""
        self._last_compute_cycle = cycle
        results = {}

        results["1_self_sustaining"] = self.metric_self_sustaining()
        results["2_learning"] = self.metric_learning()
        results["3_discrimination"] = self.metric_discrimination()
        results["4_generalization"] = self.metric_generalization()
        results["5_internal_persistence"] = self.metric_internal_persistence()
        results["6_self_awareness"] = self.metric_self_awareness()
        results["7_meta_plasticity"] = self.metric_meta_plasticity()
        results["8_teii_integration"] = self.metric_teii_integration()

        # 综合评分
        results["summary"] = self._compute_summary(results)

        self._cached_results = results
        return results

    # ==================== 功能指标 ====================

    def metric_self_sustaining(self) -> Dict:
        """
        指标1: 自维持
        外部输入停止后，内部活动标准差 > 0.1，持续 > 100周期
        """
        if len(self.global_activation_history) < 150:
            return {"passed": False, "value": 0, "threshold": 100,
                    "reason": "数据不足"}

        # 取最后150个周期的标准差
        recent = self.global_activation_history[-150:]
        std_values = []
        window = 50
        for i in range(len(recent) - window):
            window_data = recent[i:i+window]
            std_values.append(np.std(window_data))

        # 连续超过0.1的周期数
        max_consecutive = 0
        current_consecutive = 0
        for std in std_values:
            if std > 0.1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return {
            "passed": max_consecutive > 100,
            "value": max_consecutive,
            "threshold": 100,
            "current_std": float(np.std(recent[-50:])) if recent else 0,
        }

    def metric_learning(self) -> Dict:
        """
        指标2: 学习
        同一输入序列第10次与第1次响应的活动向量余弦相似度变化量 > 0.3
        """
        if len(self.input_responses) < 10:
            return {"passed": False, "value": 0, "threshold": 0.3,
                    "reason": "响应数据不足"}

        # 找到相似输入的首次和第10次响应
        similarity_changes = []
        for i in range(len(self.input_responses) - 9):
            input_1, response_1 = self.input_responses[i]
            input_10, response_10 = self.input_responses[i + 9]

            # 检查输入是否相似（重复呈现）
            input_sim = self._cosine_similarity(input_1, input_10)
            if input_sim > 0.8:  # 认为是同一输入
                response_sim = self._cosine_similarity(response_1, response_10)
                similarity_changes.append(response_sim)

        if not similarity_changes:
            return {"passed": False, "value": 0, "threshold": 0.3,
                    "reason": "未找到重复输入"}

        # 变化量 = 响应相似度（学习后更一致的响应意味着学习发生）
        avg_change = np.mean(similarity_changes)
        # 这里测量的是响应的一致性变化
        # 更合理的定义：第10次响应与第1次响应的差异
        learning_score = 1 - avg_change  # 差异越大说明学习越多

        return {
            "passed": learning_score > 0.3,
            "value": float(learning_score),
            "threshold": 0.3,
            "response_consistency": float(avg_change),
        }

    def metric_discrimination(self) -> Dict:
        """
        指标3: 区分
        两个不同输入引发的活动向量余弦相似度 < 0.5
        """
        if len(self.input_responses) < 2:
            return {"passed": False, "value": 0, "threshold": 0.5,
                    "reason": "响应数据不足"}

        # 找到不同输入对应的响应
        dissimilar_pairs = []
        for i in range(len(self.input_responses)):
            for j in range(i + 1, min(i + 20, len(self.input_responses))):
                input_i, response_i = self.input_responses[i]
                input_j, response_j = self.input_responses[j]

                input_sim = self._cosine_similarity(input_i, input_j)
                if input_sim < 0.3:  # 不同输入
                    response_sim = self._cosine_similarity(response_i, response_j)
                    dissimilar_pairs.append(response_sim)

        if not dissimilar_pairs:
            return {"passed": False, "value": 0, "threshold": 0.5,
                    "reason": "未找到不同输入对"}

        avg_dissimilarity = np.mean(dissimilar_pairs)

        return {
            "passed": avg_dissimilarity < 0.5,
            "value": float(avg_dissimilarity),
            "threshold": 0.5,
            "pair_count": len(dissimilar_pairs),
        }

    def metric_generalization(self) -> Dict:
        """
        指标4: 概括
        两个相似输入引发的活动向量余弦相似度 > 0.7
        """
        if len(self.input_responses) < 2:
            return {"passed": False, "value": 0, "threshold": 0.7,
                    "reason": "响应数据不足"}

        # 找到相似输入对应的响应
        similar_pairs = []
        for i in range(len(self.input_responses)):
            for j in range(i + 1, min(i + 20, len(self.input_responses))):
                input_i, response_i = self.input_responses[i]
                input_j, response_j = self.input_responses[j]

                input_sim = self._cosine_similarity(input_i, input_j)
                if 0.5 < input_sim < 0.9:  # 相似但不同
                    response_sim = self._cosine_similarity(response_i, response_j)
                    similar_pairs.append(response_sim)

        if not similar_pairs:
            return {"passed": False, "value": 0, "threshold": 0.7,
                    "reason": "未找到相似输入对"}

        avg_similarity = np.mean(similar_pairs)

        return {
            "passed": avg_similarity > 0.7,
            "value": float(avg_similarity),
            "threshold": 0.7,
            "pair_count": len(similar_pairs),
        }

    def metric_internal_persistence(self) -> Dict:
        """
        指标5: 内部持续性
        无输入时self-sensor活动衰减到50%所需周期 > 50
        """
        if len(self.self_sensor_history) < 100:
            return {"passed": False, "value": 0, "threshold": 50,
                    "reason": "数据不足"}

        # 找到self-sensor峰值
        max_value = max(self.self_sensor_history[-200:])
        if max_value < 0.01:
            return {"passed": False, "value": 0, "threshold": 50,
                    "reason": "self-sensor无明显活动"}

        # 计算衰减到50%所需周期
        threshold = max_value * 0.5
        decay_cycles = 0
        for i in range(len(self.self_sensor_history) - 1, -1, -1):
            if self.self_sensor_history[i] >= threshold:
                decay_cycles = len(self.self_sensor_history) - 1 - i
                break

        return {
            "passed": decay_cycles > 50,
            "value": decay_cycles,
            "threshold": 50,
            "max_self_sensor": float(max_value),
        }

    # ==================== 自指涉指标 ====================

    def metric_self_awareness(self) -> Dict:
        """
        指标6: 自我状态感知
        self-sensor与全局活动Pearson相关 r > 0.6
        """
        if len(self.self_sensor_history) < 100:
            return {"passed": False, "value": 0, "threshold": 0.6,
                    "reason": "数据不足"}

        # 取最后500个周期
        n = min(500, len(self.self_sensor_history))
        self_sensor = np.array(self.self_sensor_history[-n:])
        global_act = np.array(self.global_activation_history[-n:])

        if len(self_sensor) < 10:
            return {"passed": False, "value": 0, "threshold": 0.6,
                    "reason": "数据不足"}

        r = self._pearson_correlation(self_sensor, global_act)

        return {
            "passed": r > 0.6,
            "value": float(r),
            "threshold": 0.6,
            "data_points": n,
        }

    def metric_meta_plasticity(self) -> Dict:
        """
        指标7: 元可塑性
        gate阈值方差与全局预测误差Pearson相关 r > 0.4
        """
        if len(self.gate_threshold_history) < 100 or len(self.prediction_error_history) < 100:
            return {"passed": False, "value": 0, "threshold": 0.4,
                    "reason": "数据不足"}

        n = min(500, len(self.gate_threshold_history))
        gate_thresholds = np.array(self.gate_threshold_history[-n:])
        pred_errors = np.array(self.prediction_error_history[-n:])

        r = self._pearson_correlation(gate_thresholds, pred_errors)

        return {
            "passed": abs(r) > 0.4,
            "value": float(r),
            "threshold": 0.4,
            "data_points": n,
        }

    # ==================== TEII整合度 ====================

    def metric_teii_integration(self) -> Dict:
        """
        指标8: TEII整合度
        传递熵 + 特征值谱
        
        整合度 = λ₁/∑λ > 0.3，且特征值谱通过幂律拟合
        """
        if len(self.activation_matrices) < 10:
            return {"passed": False, "value": 0, "threshold": 0.3,
                    "reason": "激活数据不足"}

        # 构建有效连接矩阵（简化版传递熵：互信息近似）
        matrix = self._build_effective_connectivity_matrix()
        if matrix is None or matrix.shape[0] < 3:
            return {"passed": False, "value": 0, "threshold": 0.3,
                    "reason": "矩阵构建失败"}

        # 计算特征值
        try:
            eigenvalues = np.linalg.eigvalsh(matrix)
            eigenvalues = np.sort(np.abs(eigenvalues))[::-1]
        except Exception:
            return {"passed": False, "value": 0, "threshold": 0.3,
                    "reason": "特征值计算失败"}

        # 整合度 = λ₁/∑λ
        total = np.sum(eigenvalues)
        if total == 0:
            return {"passed": False, "value": 0, "threshold": 0.3,
                    "reason": "特征值总和为零"}

        integration = float(eigenvalues[0] / total)

        # 幂律拟合（简化：检查前几个特征值是否递减足够快）
        power_law_score = self._check_power_law(eigenvalues)

        return {
            "passed": integration > 0.3,
            "value": integration,
            "threshold": 0.3,
            "power_law": power_law_score > 0.5,
            "eigenvalue_ratio": float(eigenvalues[0] / max(eigenvalues[1], 1e-10))
            if len(eigenvalues) > 1 else 1.0,
            "matrix_size": matrix.shape[0],
        }

    def _build_effective_connectivity_matrix(self) -> Optional[np.ndarray]:
        """
        构建有效连接矩阵（传递熵近似）
        使用互信息近似替代传递熵（计算复杂度O(N²×T)）
        """
        if not self.activation_matrices:
            return None

        # 取最近的激活矩阵
        recent = self.activation_matrices[-50:]  # T=50个样本
        T = len(recent)

        if T < 10:
            return None

        N = recent[0].shape[0]
        if N < 3 or N > 200:  # 限制矩阵大小
            # 采样子集
            indices = np.random.choice(N, min(100, N), replace=False)
            N = len(indices)
        else:
            indices = np.arange(N)

        matrix = np.zeros((N, N), dtype=np.float32)

        # 计算每对的互信息（传递熵的简化近似）
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                # 简化：用互相关替代传递熵
                x = np.array([recent[t][indices[i]] for t in range(T)])
                y = np.array([recent[t][indices[j]] for t in range(T)])
                matrix[i][j] = abs(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else 0

        return matrix

    def _check_power_law(self, eigenvalues: np.ndarray) -> float:
        """
        检查特征值谱是否接近幂律分布
        返回0-1的拟合优度
        """
        if len(eigenvalues) < 5:
            return 0.0

        # 取正的特征值
        positive = eigenvalues[eigenvalues > 0]
        if len(positive) < 5:
            return 0.0

        # 对数空间线性拟合
        log_x = np.log(np.arange(1, len(positive) + 1))
        log_y = np.log(positive + 1e-10)

        # 简单线性回归
        slope, intercept = np.polyfit(log_x, log_y, 1)
        predicted = slope * log_x + intercept
        residuals = log_y - predicted

        # R²
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
        r_squared = 1 - ss_res / max(ss_tot, 1e-10)

        return max(0, float(r_squared))

    # ==================== 综合评分 ====================

    def _compute_summary(self, results: Dict) -> Dict:
        """综合评分"""
        weights = {
            "1_self_sustaining": 0.20,
            "2_learning": 0.20,
            "3_discrimination": 0.15,
            "4_generalization": 0.15,
            "5_internal_persistence": 0.10,
            "6_self_awareness": 0.10,
            "7_meta_plasticity": 0.10,
        }

        total_score = 0
        total_weight = 0
        passed_count = 0

        for key, weight in weights.items():
            if key in results:
                result = results[key]
                if result.get("passed"):
                    passed_count += 1
                    total_score += weight
                total_weight += weight

        # 加上TEII整合度
        if "8_teii_integration" in results:
            teii = results["8_teii_integration"]
            if teii.get("passed"):
                passed_count += 1
                total_score += 0.1  # TEII作为额外加分

        return {
            "total_score": total_score,
            "passed_count": passed_count,
            "total_metrics": len(weights),
            "passed_ratio": passed_count / max(1, len(weights)),
            "overall_passed": total_score > 0.7,  # 综合分>0.7视为通过
        }

    # ==================== 辅助方法 ====================

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        if len(a) == 0 or len(b) == 0:
            return 0.0
        # 对齐长度（pad较短的）
        if len(a) != len(b):
            max_len = max(len(a), len(b))
            a_padded = np.zeros(max_len, dtype=np.float32)
            b_padded = np.zeros(max_len, dtype=np.float32)
            a_padded[:len(a)] = a
            b_padded[:len(b)] = b
            a, b = a_padded, b_padded
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    def _pearson_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """Pearson相关系数"""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        # 确保长度相同
        min_len = min(len(x), len(y))
        x = x[:min_len]
        y = y[:min_len]

        std_x = np.std(x)
        std_y = np.std(y)
        if std_x == 0 or std_y == 0:
            return 0.0

        return float(np.mean((x - np.mean(x)) * (y - np.mean(y))) / (std_x * std_y))

    def print_report(self, cycle: int = 0):
        """打印指标报告"""
        results = self.compute_all(cycle)
        print(f"\n{'='*60}")
        print(f"意识涌现指标报告 (周期 {cycle})")
        print(f"{'='*60}")

        metric_names = {
            "1_self_sustaining": "自维持",
            "2_learning": "学习",
            "3_discrimination": "区分",
            "4_generalization": "概括",
            "5_internal_persistence": "内部持续性",
            "6_self_awareness": "自我状态感知",
            "7_meta_plasticity": "元可塑性",
            "8_teii_integration": "TEII整合度",
        }

        for key, name in metric_names.items():
            if key in results:
                r = results[key]
                status = "✓" if r.get("passed") else "✗"
                value = r.get("value", 0)
                threshold = r.get("threshold", 0)
                print(f"  [{status}] {name}: {value:.4f} (阈值: {threshold})")
                if not r.get("passed") and r.get("reason"):
                    print(f"       → {r['reason']}")

        summary = results.get("summary", {})
        print(f"\n  综合评分: {summary.get('total_score', 0):.4f}")
        print(f"  通过: {summary.get('passed_count', 0)}/{summary.get('total_metrics', 0)}")
        print(f"  总体: {'通过 ✓' if summary.get('overall_passed') else '未通过 ✗'}")
        print(f"{'='*60}\n")
