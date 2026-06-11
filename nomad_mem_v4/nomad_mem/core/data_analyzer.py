"""
Data Analysis Engine - 数据分析引擎

Jarvis 数据统计分析、趋势分析和报告生成的核心模块。

核心特性:
- 描述性统计分析: 均值、中位数、标准差、最小值、最大值
- 趋势分析: 方向、速率、预测
- 相关性分析: 变量之间的关系
- 分布分析: 频率、直方图
- 比较分析: 两组数据的对比
- 报告生成: 格式化的 Markdown 报告

设计原则:
- 纯 Python 实现，无需 numpy
- 生成人类可读的 Markdown 报告
- Jarvis 应该能够理解和解释数据，而不仅仅是收集数据
"""
import uuid
import time
import logging
import math
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


# ─── Enums ───────────────────────────────────────────────────────────────────


class AnalysisType(Enum):
    """分析类型"""
    DESCRIPTIVE = "descriptive"       # 描述性统计
    TREND = "trend"                   # 趋势分析
    CORRELATION = "correlation"       # 相关性分析
    DISTRIBUTION = "distribution"     # 分布分析
    COMPARISON = "comparison"         # 比较分析
    SUMMARY = "summary"               # 综合分析


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass
class AnalysisResult:
    """分析结果

    Attributes:
        analysis_type: 分析类型
        title: 分析标题
        findings: 发现列表（人类可读的描述）
        statistics: 统计数据字典
        charts: 图表数据列表
        generated_at: 生成时间戳
    """
    analysis_type: AnalysisType
    title: str
    findings: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["analysis_type"] = self.analysis_type.value
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "AnalysisResult":
        data = dict(data)
        if isinstance(data.get("analysis_type"), str):
            data["analysis_type"] = AnalysisType(data["analysis_type"])
        allowed = {
            "analysis_type", "title", "findings", "statistics",
            "charts", "generated_at",
        }
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


@dataclass
class ReportSection:
    """报告章节

    Attributes:
        section_title: 章节标题
        content: 章节内容
        data_points: 数据点字典
        chart_type: 图表类型（可选）
    """
    section_title: str
    content: str
    data_points: Dict[str, Any] = field(default_factory=dict)
    chart_type: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ReportSection":
        data = dict(data)
        allowed = {"section_title", "content", "data_points", "chart_type"}
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


@dataclass
class Report:
    """分析报告

    Attributes:
        report_id: 报告唯一标识
        title: 报告标题
        sections: 报告章节列表
        summary: 报告摘要
        generated_at: 生成时间戳
        format_type: 格式类型 (markdown/json)
    """
    report_id: str
    title: str
    sections: List[ReportSection] = field(default_factory=list)
    summary: str = ""
    generated_at: float = field(default_factory=time.time)
    format_type: str = "markdown"

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["sections"] = [s.to_dict() for s in self.sections]
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "Report":
        data = dict(data)
        if isinstance(data.get("sections"), list):
            data["sections"] = [
                ReportSection.from_dict(s) if isinstance(s, dict) else s
                for s in data["sections"]
            ]
        allowed = {"report_id", "title", "sections", "summary", "generated_at", "format_type"}
        data = {k: v for k, v in data.items() if k in allowed}
        return cls(**data)


# ─── DataAnalyzer ────────────────────────────────────────────────────────────


class DataAnalyzer:
    """
    数据分析引擎

    提供统计分析和报告生成能力，帮助 Jarvis 理解和解释数据。

    使用示例:
        >>> analyzer = DataAnalyzer()
        >>> result = analyzer.analyze_data([1, 2, 3, 4, 5], "descriptive", "基础统计")
        >>> print(analyzer.format_report_as_markdown(result))
        >>> report = analyzer.create_report("月度报告", [section], summary="...")
    """

    def __init__(self):
        # 分析历史
        self._history: List[AnalysisResult] = []
        # 报告存储
        self._reports: Dict[str, Report] = {}

    # ── Descriptive Statistics ──────────────────────────────────────────

    @staticmethod
    def _extract_numbers(data_points) -> List[float]:
        """从数据点中提取数值列表"""
        if isinstance(data_points, dict):
            values = []
            for v in data_points.values():
                if isinstance(v, (int, float)):
                    values.append(float(v))
            return values
        elif isinstance(data_points, list):
            result = []
            for item in data_points:
                if isinstance(item, (int, float)):
                    result.append(float(item))
                elif isinstance(item, dict):
                    # 尝试提取数值字段
                    for v in item.values():
                        if isinstance(v, (int, float)):
                            result.append(float(v))
            return result
        return []

    @staticmethod
    def _mean(values: List[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _median(values: List[float]) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0
        return sorted_vals[mid]

    @staticmethod
    def _std(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        m = sum(values) / len(values)
        variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    @staticmethod
    def _percentile(values: List[float], p: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)

    # ── Core Analysis ───────────────────────────────────────────────────

    def analyze_data(
        self,
        data_points: Union[List[Union[int, float, Dict]], Dict[str, Union[int, float]]],
        analysis_type: str,
        title: str = "",
    ) -> AnalysisResult:
        """
        对数据点执行指定类型的分析

        Args:
            data_points: 数据点（数值列表或字典）
            analysis_type: 分析类型 (descriptive/trend/correlation/distribution/comparison/summary)
            title: 分析标题

        Returns:
            AnalysisResult: 分析结果

        Raises:
            ValueError: analysis_type 无效
        """
        atype = AnalysisType(analysis_type)
        now = time.time()

        if atype == AnalysisType.DESCRIPTIVE:
            return self._descriptive_analysis(data_points, title or "描述性统计", now)
        elif atype == AnalysisType.TREND:
            return self._trend_analysis(data_points, title or "趋势分析", now)
        elif atype == AnalysisType.CORRELATION:
            return self._correlation_analysis(data_points, title or "相关性分析", now)
        elif atype == AnalysisType.DISTRIBUTION:
            return self._distribution_analysis(data_points, title or "分布分析", now)
        elif atype == AnalysisType.COMPARISON:
            return self._comparison_analysis(data_points, title or "比较分析", now)
        elif atype == AnalysisType.SUMMARY:
            return self._summary_analysis(data_points, title or "综合分析", now)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

    def _descriptive_analysis(
        self, data_points, title: str, timestamp: float
    ) -> AnalysisResult:
        """描述性统计分析"""
        values = self._extract_numbers(data_points)

        if not values:
            return AnalysisResult(
                analysis_type=AnalysisType.DESCRIPTIVE,
                title=title,
                findings=["数据为空，无法计算统计指标"],
                statistics={},
                generated_at=timestamp,
            )

        mean_val = self._mean(values)
        median_val = self._median(values)
        std_val = self._std(values)
        min_val = min(values)
        max_val = max(values)
        p25 = self._percentile(values, 25)
        p75 = self._percentile(values, 75)
        total = sum(values)
        count = len(values)

        stats = {
            "count": count,
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "std": round(std_val, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "range": round(max_val - min_val, 4),
            "sum": round(total, 4),
            "p25": round(p25, 4),
            "p75": round(p75, 4),
            "iqr": round(p75 - p25, 4),
        }

        findings = [
            f"共 {count} 个数据点",
            f"平均值为 {mean_val:.2f}，中位数为 {median_val:.2f}",
            f"标准差为 {std_val:.2f}，表示数据{'较为集中' if std_val < (mean_val * 0.3) else '波动较大'}",
            f"数据范围: {min_val:.2f} ~ {max_val:.2f}（极差 {max_val - min_val:.2f}）",
            f"25分位数为 {p25:.2f}，75分位数为 {p75:.2f}，IQR 为 {p75 - p25:.2f}",
        ]

        # 偏度判断
        if mean_val > median_val:
            findings.append("均值大于中位数，数据可能右偏（正偏态）")
        elif mean_val < median_val:
            findings.append("均值小于中位数，数据可能左偏（负偏态）")
        else:
            findings.append("均值等于中位数，数据分布相对对称")

        result = AnalysisResult(
            analysis_type=AnalysisType.DESCRIPTIVE,
            title=title,
            findings=findings,
            statistics=stats,
            generated_at=timestamp,
        )
        self._history.append(result)
        return result

    def _trend_analysis(
        self, data_points, title: str, timestamp: float
    ) -> AnalysisResult:
        """趋势分析"""
        values = self._extract_numbers(data_points)

        if len(values) < 2:
            return AnalysisResult(
                analysis_type=AnalysisType.TREND,
                title=title,
                findings=["数据点不足，无法进行趋势分析（至少需要2个数据点）"],
                statistics={},
                generated_at=timestamp,
            )

        n = len(values)
        # 计算变化率
        changes = [values[i + 1] - values[i] for i in range(n - 1)]
        avg_change = self._mean(changes)

        # 判断趋势方向
        if avg_change > 0:
            direction = "upward"
            direction_cn = "上升"
        elif avg_change < 0:
            direction = "downward"
            direction_cn = "下降"
        else:
            direction = "stable"
            direction_cn = "平稳"

        # 计算变化率
        change_rate = abs(avg_change / self._mean(values) * 100) if self._mean(values) != 0 else 0

        # 简单线性预测（最小二乘法）
        x_vals = list(range(n))
        x_mean = self._mean(x_vals)
        y_mean = self._mean(values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, values))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        forecast_next = slope * n + intercept

        # 波动性
        std_val = self._std(values)
        volatility = std_val / y_mean * 100 if y_mean != 0 else 0

        stats = {
            "direction": direction,
            "direction_cn": direction_cn,
            "avg_change": round(avg_change, 4),
            "change_rate": round(change_rate, 2),
            "slope": round(slope, 4),
            "intercept": round(intercept, 4),
            "forecast_next": round(forecast_next, 4),
            "volatility": round(volatility, 2),
            "data_points": n,
        }

        # 生成图表数据（简化趋势线）
        trend_line = [round(slope * i + intercept, 2) for i in range(n)]
        charts = [{
            "type": "trend_line",
            "title": "趋势线",
            "data_points": values,
            "trend_line": trend_line,
        }]

        findings = [
            f"共 {n} 个数据点，整体趋势为{direction_cn}",
            f"平均每步变化 {avg_change:.2f}，变化率为 {change_rate:.2f}%",
            f"线性回归斜率为 {slope:.4f}，截距为 {intercept:.4f}",
            f"预测下一个数据点约为 {forecast_next:.2f}",
            f"波动率为 {volatility:.2f}%，{'波动较大' if volatility > 20 else '相对稳定'}",
        ]

        result = AnalysisResult(
            analysis_type=AnalysisType.TREND,
            title=title,
            findings=findings,
            statistics=stats,
            charts=charts,
            generated_at=timestamp,
        )
        self._history.append(result)
        return result

    def _correlation_analysis(
        self, data_points, title: str, timestamp: float
    ) -> AnalysisResult:
        """相关性分析"""
        # 期望数据为字典，键为变量名，值为数值列表
        if isinstance(data_points, list) and len(data_points) > 0:
            if isinstance(data_points[0], dict):
                # 转换为变量字典格式
                var_data = defaultdict(list)
                for item in data_points:
                    for k, v in item.items():
                        if isinstance(v, (int, float)):
                            var_data[k].append(float(v))
                data_dict = dict(var_data)
            else:
                data_dict = {"values": self._extract_numbers(data_points)}
        elif isinstance(data_points, dict):
            data_dict = {}
            for k, v in data_points.items():
                if isinstance(v, list):
                    data_dict[k] = [float(x) for x in v if isinstance(x, (int, float))]
                elif isinstance(v, (int, float)):
                    data_dict[k] = [float(v)]
        else:
            data_dict = {}

        if len(data_dict) < 2:
            return AnalysisResult(
                analysis_type=AnalysisType.CORRELATION,
                title=title,
                findings=["变量不足，无法进行相关性分析（至少需要2个变量）"],
                statistics={"variables": list(data_dict.keys())},
                generated_at=timestamp,
            )

        # 计算变量间的 Pearson 相关系数
        correlations = {}
        var_names = sorted(data_dict.keys())

        for i in range(len(var_names)):
            for j in range(i + 1, len(var_names)):
                x = data_dict[var_names[i]]
                y = data_dict[var_names[j]]
                min_len = min(len(x), len(y))
                if min_len < 2:
                    continue
                x = x[:min_len]
                y = y[:min_len]
                r = self._pearson_correlation(x, y)
                correlations[f"{var_names[i]}_vs_{var_names[j]}"] = round(r, 4)

        findings = []
        for pair, r in correlations.items():
            strength = "强" if abs(r) > 0.7 else ("中等" if abs(r) > 0.4 else "弱")
            direction = "正相关" if r > 0 else "负相关"
            findings.append(f"{pair}: r={r:.4f}（{strength}{direction}）")

        if not findings:
            findings.append("无有效相关性数据")

        # 找最强相关
        if correlations:
            strongest = max(correlations.items(), key=lambda x: abs(x[1]))[0]
            findings.append(f"最强相关性: {strongest} (r={correlations[strongest]:.4f})")

        result = AnalysisResult(
            analysis_type=AnalysisType.CORRELATION,
            title=title,
            findings=findings,
            statistics={
                "variables": var_names,
                "correlations": correlations,
                "strongest": strongest if correlations else None,
            },
            generated_at=timestamp,
        )
        self._history.append(result)
        return result

    @staticmethod
    def _pearson_correlation(x: List[float], y: List[float]) -> float:
        """计算 Pearson 相关系数"""
        n = len(x)
        if n < 2:
            return 0.0

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        cov = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        std_x = math.sqrt(sum((xi - x_mean) ** 2 for xi in x))
        std_y = math.sqrt(sum((yi - y_mean) ** 2 for yi in y))

        if std_x == 0 or std_y == 0:
            return 0.0

        return cov / (std_x * std_y)

    def _distribution_analysis(
        self, data_points, title: str, timestamp: float
    ) -> AnalysisResult:
        """分布分析"""
        values = self._extract_numbers(data_points)

        if not values:
            return AnalysisResult(
                analysis_type=AnalysisType.DISTRIBUTION,
                title=title,
                findings=["数据为空，无法进行分布分析"],
                statistics={},
                generated_at=timestamp,
            )

        # 计算直方图
        n_bins = min(10, max(3, int(math.sqrt(len(values)))))
        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            bins = [{"range": f"{min_val}", "count": len(values), "percentage": 100.0}]
        else:
            bin_width = (max_val - min_val) / n_bins
            bins = []
            for i in range(n_bins):
                low = min_val + i * bin_width
                high = low + bin_width
                count = sum(1 for v in values if low <= v < high)
                if i == n_bins - 1:  # 最后一个 bin 包含最大值
                    count = sum(1 for v in values if low <= v <= high)
                pct = count / len(values) * 100
                bins.append({
                    "range": f"{low:.2f}-{high:.2f}",
                    "count": count,
                    "percentage": round(pct, 2),
                })

        # 频率统计
        counter = Counter(values)
        most_common = counter.most_common(3)

        findings = [
            f"共 {len(values)} 个数据点，分为 {n_bins} 个区间",
            f"数据范围: {min_val:.2f} ~ {max_val:.2f}",
        ]

        if most_common:
            top_str = ", ".join(f"{v} (出现 {c} 次)" for v, c in most_common)
            findings.append(f"最常出现的值: {top_str}")

        result = AnalysisResult(
            analysis_type=AnalysisType.DISTRIBUTION,
            title=title,
            findings=findings,
            statistics={
                "n_bins": n_bins,
                "min": min_val,
                "max": max_val,
                "histogram": bins,
            },
            charts=[{
                "type": "histogram",
                "title": "数据分布",
                "bins": bins,
            }],
            generated_at=timestamp,
        )
        self._history.append(result)
        return result

    def _comparison_analysis(
        self, data_points, title: str, timestamp: float
    ) -> AnalysisResult:
        """比较分析（比较两组数据）"""
        # 尝试从数据中提取两组
        group_a, group_b = self._split_comparison_data(data_points)

        if not group_a or not group_b:
            return AnalysisResult(
                analysis_type=AnalysisType.COMPARISON,
                title=title,
                findings=["无法提取两组数据进行比较"],
                statistics={},
                generated_at=timestamp,
            )

        stats_a = {
            "count": len(group_a),
            "mean": round(self._mean(group_a), 4),
            "median": round(self._median(group_a), 4),
            "std": round(self._std(group_a), 4),
            "min": round(min(group_a), 4),
            "max": round(max(group_a), 4),
        }
        stats_b = {
            "count": len(group_b),
            "mean": round(self._mean(group_b), 4),
            "median": round(self._median(group_b), 4),
            "std": round(self._std(group_b), 4),
            "min": round(min(group_b), 4),
            "max": round(max(group_b), 4),
        }

        mean_diff = stats_a["mean"] - stats_b["mean"]
        mean_diff_pct = abs(mean_diff / stats_b["mean"] * 100) if stats_b["mean"] != 0 else 0

        findings = [
            f"组A: {len(group_a)} 个数据点，均值 {stats_a['mean']:.2f}，中位数 {stats_a['median']:.2f}",
            f"组B: {len(group_b)} 个数据点，均值 {stats_b['mean']:.2f}，中位数 {stats_b['median']:.2f}",
            f"均值差异: {mean_diff:.2f}（差异率 {mean_diff_pct:.2f}%）",
            f"组A波动性 ({stats_a['std']:.2f}) {'大于' if stats_a['std'] > stats_b['std'] else '小于'} 组B ({stats_b['std']:.2f})",
        ]

        if stats_a["mean"] > stats_b["mean"]:
            findings.append("组A整体水平高于组B")
        elif stats_a["mean"] < stats_b["mean"]:
            findings.append("组B整体水平高于组A")
        else:
            findings.append("两组整体水平相当")

        # 简化 t 检验（仅判断显著性）
        n1, n2 = len(group_a), len(group_b)
        if n1 > 1 and n2 > 1 and stats_a["std"] > 0 and stats_b["std"] > 0:
            pooled_se = math.sqrt(stats_a["std"]**2 / n1 + stats_b["std"]**2 / n2)
            if pooled_se > 0:
                t_stat = abs(mean_diff) / pooled_se
                significant = t_stat > 1.96  # alpha=0.05 近似
                findings.append(
                    f"显著性检验: t={t_stat:.2f}，{'差异显著' if significant else '差异不显著'} (alpha=0.05)"
                )

        result = AnalysisResult(
            analysis_type=AnalysisType.COMPARISON,
            title=title,
            findings=findings,
            statistics={
                "group_a": stats_a,
                "group_b": stats_b,
                "mean_diff": round(mean_diff, 4),
                "mean_diff_pct": round(mean_diff_pct, 2),
            },
            generated_at=timestamp,
        )
        self._history.append(result)
        return result

    @staticmethod
    def _split_comparison_data(data_points):
        """从数据中拆分两组比较数据"""
        if isinstance(data_points, dict):
            # 期望 dict 包含两个键
            items = list(data_points.items())
            if len(items) >= 2:
                group_a = [float(v) for v in items[0][1] if isinstance(v, (int, float))] if isinstance(items[0][1], list) else [float(items[0][1])]
                group_b = [float(v) for v in items[1][1] if isinstance(v, (int, float))] if isinstance(items[1][1], list) else [float(items[1][1])]
                return group_a, group_b
            elif len(items) == 1 and isinstance(items[0][1], list):
                # 单个键但值列表很长，平分
                vals = [float(v) for v in items[0][1] if isinstance(v, (int, float))]
                mid = len(vals) // 2
                return vals[:mid], vals[mid:]
        elif isinstance(data_points, list):
            if len(data_points) >= 2 and isinstance(data_points[0], dict):
                # 列表中的字典可能包含分组标记
                group_a = []
                group_b = []
                for item in data_points:
                    vals = [float(v) for v in item.values() if isinstance(v, (int, float))]
                    # 交替分配
                    if len(group_a) <= len(group_b):
                        group_a.extend(vals)
                    else:
                        group_b.extend(vals)
                return group_a, group_b
            else:
                # 平分列表
                vals = [float(v) for v in data_points if isinstance(v, (int, float))]
                mid = len(vals) // 2
                return vals[:mid], vals[mid:]
        return [], []

    def _summary_analysis(
        self, data_points, title: str, timestamp: float
    ) -> AnalysisResult:
        """综合分析：包含描述性、趋势、分布的总结"""
        values = self._extract_numbers(data_points)

        if not values:
            return AnalysisResult(
                analysis_type=AnalysisType.SUMMARY,
                title=title,
                findings=["数据为空，无法生成综合分析"],
                statistics={},
                generated_at=timestamp,
            )

        # 描述性统计
        mean_val = self._mean(values)
        median_val = self._median(values)
        std_val = self._std(values)
        min_val = min(values)
        max_val = max(values)

        # 趋势
        trend_direction = "stable"
        if len(values) >= 2:
            changes = [values[i + 1] - values[i] for i in range(len(values) - 1)]
            avg_change = self._mean(changes)
            if avg_change > 0:
                trend_direction = "upward"
            elif avg_change < 0:
                trend_direction = "downward"

        # 分布
        q1 = self._percentile(values, 25)
        q3 = self._percentile(values, 75)

        trend_cn = {"upward": "上升", "downward": "下降", "stable": "平稳"}

        findings = [
            f"综合分析共 {len(values)} 个数据点",
            f"中心趋势: 均值 {mean_val:.2f}，中位数 {median_val:.2f}",
            f"离散程度: 标准差 {std_val:.2f}，范围 {min_val:.2f} ~ {max_val:.2f}",
            f"整体趋势: {trend_cn.get(trend_direction, trend_direction)}",
            f"四分位距: Q1={q1:.2f}, Q3={q3:.2f}, IQR={q3-q1:.2f}",
        ]

        # 数据质量评估
        null_count = 0
        if isinstance(data_points, list):
            null_count = sum(1 for v in data_points if v is None)
        if null_count > 0:
            findings.append(f"数据质量: 发现 {null_count} 个空值")

        stats = {
            "count": len(values),
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "std": round(std_val, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "trend": trend_direction,
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(q3 - q1, 4),
        }

        result = AnalysisResult(
            analysis_type=AnalysisType.SUMMARY,
            title=title,
            findings=findings,
            statistics=stats,
            generated_at=timestamp,
        )
        self._history.append(result)
        return result

    # ── Multi-Metric Trend ──────────────────────────────────────────────

    def generate_trend_report(
        self,
        metrics: Dict[str, List[Union[int, float]]],
        time_range: str = "",
        title: str = "",
    ) -> AnalysisResult:
        """
        多指标趋势分析报告

        Args:
            metrics: 指标字典，键为指标名，值为数值列表
            time_range: 时间范围描述（如 "2024-01 ~ 2024-06"）
            title: 报告标题

        Returns:
            AnalysisResult: 趋势分析结果
        """
        title = title or f"趋势分析报告 ({time_range})" if time_range else "趋势分析报告"

        findings = []
        all_stats = {}

        for metric_name, values in metrics.items():
            if not values:
                continue

            vals = [float(v) for v in values if isinstance(v, (int, float))]
            if not vals:
                continue

            # 计算趋势
            trend_result = self._trend_analysis(vals, metric_name, time.time())
            all_stats[metric_name] = trend_result.statistics
            findings.extend([f"[{metric_name}] {f}" for f in trend_result.findings])

        result = AnalysisResult(
            analysis_type=AnalysisType.TREND,
            title=title,
            findings=findings,
            statistics={"metrics": all_stats, "time_range": time_range},
            generated_at=time.time(),
        )
        self._history.append(result)
        return result

    # ── Comparison Report ───────────────────────────────────────────────

    def generate_comparison_report(
        self,
        group_a: List[Union[int, float]],
        group_b: List[Union[int, float]],
        title: str = "",
    ) -> AnalysisResult:
        """
        两组数据的比较报告

        Args:
            group_a: A组数据
            group_b: B组数据
            title: 报告标题

        Returns:
            AnalysisResult: 比较分析结果
        """
        data_dict = {
            "group_a": [float(v) for v in group_a if isinstance(v, (int, float))],
            "group_b": [float(v) for v in group_b if isinstance(v, (int, float))],
        }

        result = self._comparison_analysis(data_dict, title or "比较分析报告", time.time())
        self._history.append(result)
        return result

    # ── Summary Report ──────────────────────────────────────────────────

    def generate_summary_report(
        self, data_source: Any, time_range: str = ""
    ) -> AnalysisResult:
        """
        综合摘要报告

        Args:
            data_source: 数据源（数值列表或字典）
            time_range: 时间范围描述

        Returns:
            AnalysisResult: 综合分析结果
        """
        title = f"综合摘要报告 ({time_range})" if time_range else "综合摘要报告"

        # 如果数据源是字典，对每个值做综合分析
        if isinstance(data_source, dict):
            findings = []
            all_stats = {}

            for key, values in data_source.items():
                if isinstance(values, list):
                    vals = [float(v) for v in values if isinstance(v, (int, float))]
                    if vals:
                        summary = self._summary_analysis(vals, key, time.time())
                        findings.extend([f"[{key}] {f}" for f in summary.findings])
                        all_stats[key] = summary.statistics

            return AnalysisResult(
                analysis_type=AnalysisType.SUMMARY,
                title=title,
                findings=findings,
                statistics=all_stats,
                generated_at=time.time(),
            )
        else:
            return self._summary_analysis(data_source, title, time.time())

    # ── Report Generation ───────────────────────────────────────────────

    def create_report(
        self,
        title: str,
        sections: List[ReportSection],
        summary: str = "",
        format_type: str = "markdown",
    ) -> Report:
        """
        构建格式化的报告

        Args:
            title: 报告标题
            sections: 报告章节列表
            summary: 报告摘要
            format_type: 格式类型 (markdown/json)

        Returns:
            Report: 构建的报告
        """
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        report = Report(
            report_id=report_id,
            title=title,
            sections=list(sections),
            summary=summary,
            generated_at=time.time(),
            format_type=format_type,
        )
        self._reports[report_id] = report
        return report

    def format_report_as_markdown(self, report) -> str:
        """
        将报告转换为 Markdown 字符串

        Args:
            report: Report 对象或 AnalysisResult 对象

        Returns:
            str: Markdown 格式的报告
        """
        if isinstance(report, Report):
            lines = [
                f"# {report.title}",
                "",
            ]

            if report.summary:
                lines.extend([
                    "## 摘要",
                    "",
                    report.summary,
                    "",
                ])

            for section in report.sections:
                lines.extend([
                    f"## {section.section_title}",
                    "",
                    section.content,
                    "",
                ])

                if section.data_points:
                    lines.append("### 数据")
                    lines.append("")
                    for k, v in section.data_points.items():
                        lines.append(f"- **{k}**: {v}")
                    lines.append("")

                if section.chart_type:
                    lines.append(f"*[图表类型: {section.chart_type}]*")
                    lines.append("")

            lines.append(
                f"*报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.generated_at))}*"
            )
            return "\n".join(lines)

        elif isinstance(report, AnalysisResult):
            lines = [
                f"# {report.title}",
                "",
                f"**分析类型**: {report.analysis_type.value}",
                "",
            ]

            if report.findings:
                lines.extend(["## 分析发现", ""])
                for finding in report.findings:
                    lines.append(f"- {finding}")
                lines.append("")

            if report.statistics:
                lines.extend(["## 统计数据", ""])
                self._format_stats_md(lines, report.statistics)
                lines.append("")

            if report.charts:
                lines.extend(["## 图表", ""])
                for chart in report.charts:
                    lines.append(f"### {chart.get('title', '图表')}")
                    lines.append(f"*类型: {chart.get('type', 'unknown')}*")
                    lines.append("")

            lines.append(
                f"*分析时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.generated_at))}*"
            )
            return "\n".join(lines)

        return str(report)

    def _format_stats_md(self, lines: List[str], stats: Dict, indent: int = 0):
        """递归格式化统计数据为 Markdown"""
        prefix = "  " * indent
        for key, value in stats.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}- **{key}**:")
                self._format_stats_md(lines, value, indent + 1)
            elif isinstance(value, list):
                lines.append(f"{prefix}- **{key}**: [{len(value)} items]")
            else:
                lines.append(f"{prefix}- **{key}**: {value}")

    # ── Query Methods ───────────────────────────────────────────────────

    def get_analysis_history(self, limit: int = 20) -> List[AnalysisResult]:
        """
        获取分析历史

        Args:
            limit: 返回数量限制

        Returns:
            分析结果列表，按时间降序
        """
        sorted_history = sorted(self._history, key=lambda a: a.generated_at, reverse=True)
        return sorted_history[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典:
            - total_analyses: 总分析次数
            - by_type: 按分析类型分类
            - reports_generated: 生成的报告数
        """
        by_type: Dict[str, int] = defaultdict(int)
        for analysis in self._history:
            by_type[analysis.analysis_type.value] += 1

        return {
            "total_analyses": len(self._history),
            "by_type": dict(by_type),
            "reports_generated": len(self._reports),
        }

    # ── Lifecycle ───────────────────────────────────────────────────────

    def close(self):
        """清理资源"""
        self._history.clear()
        self._reports.clear()
        logger.info("DataAnalyzer closed")
