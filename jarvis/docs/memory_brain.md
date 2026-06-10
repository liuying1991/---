# 贾维斯记忆大脑系统

## 概述

贾维斯记忆大脑是一个自主创新的四层记忆架构，借鉴了MemGPT、Zep、Cognee等先进技术，但进行了深度优化和创新。

## 架构

```
L0: 工作记忆 (Working Memory)
    - 当前对话上下文
    - 容量: ~100条
    - 存活: 会话内

L1: 会话记忆 (Session Memory)
    - 会话摘要
    - 关键决策
    - 容量: ~1000条
    - 存活: 7天

L2: 情景记忆 (Episodic Memory)
    - 事件时间线
    - 任务执行记录
    - 容量: 无限
    - 存活: 永久(按重要性衰减)

L3: 语义记忆 (Semantic Memory)
    - 用户画像
    - 知识图谱
    - 技能库
    - 容量: 无限
    - 存活: 永久
```

## 核心创新

### 1. 动态记忆压缩
自动将工作记忆压缩为会话摘要，提取关键决策、用户偏好、重要事实。

### 2. 自适应遗忘机制
```
记忆强度 = 重要性 × 访问频率 × e^(-衰减率×时间) × 情感权重
```

### 3. 多维关联网络
- 实体关联 (谁/什么)
- 时间关联 (何时)
- 因果关联 (为什么)
- 情感关联 (感受)
- 上下文关联 (场景)

### 4. 用户画像学习
自动学习和存储用户偏好、习惯、背景信息。

## 使用示例

```go
// 创建记忆大脑
brain := memory.NewBrain(memory.BrainConfig{
    WorkingCapacity:     100,
    SessionCapacity:     1000,
    DecayRate:           0.1,
    ForgettingThreshold: 0.1,
})

// 记忆
brain.Remember(ctx, "用户询问Go语言问题",
    memory.WithType(memory.MemoryTypeWorking),
    memory.WithImportance(0.7),
    memory.WithEntities([]memory.Entity{
        {Name: "Go", Type: "concept"},
    }),
)

// 学习用户偏好
brain.LearnUserPreference(ctx, "language", "Go", 0.9)

// 添加知识
brain.AddKnowledge(ctx, "Go", "is_a", "programming_language")

// 检索
memories, _ := brain.Recall(ctx, memory.Query{
    Text:  "Go语言",
    Limit: 5,
})

// 获取上下文（用于LLM）
context := brain.RecallContext(ctx, 4000)

// 压缩记忆
brain.Compress(ctx)

// 遗忘低重要性记忆
brain.Forget(ctx)
```

## 与现有方案对比

| 特性 | MemGPT | Zep | Cognee | 贾维斯 |
|------|--------|-----|--------|--------|
| 记忆层数 | 2 | 3 | 2 | **4** |
| 时序感知 | ❌ | ✅ | ✅ | **✅** |
| 遗忘机制 | ❌ | ❌ | ❌ | **✅** |
| 自主压缩 | ✅ | ❌ | ❌ | **✅** |
| 多维关联 | ❌ | 部分 | 部分 | **✅** |
| 用户画像 | ❌ | ❌ | ❌ | **✅** |
| 本地部署 | ✅ | ❌ | ✅ | **✅** |

## 文件结构

```
internal/memory/
├── brain.go        # 记忆大脑核心
├── layers.go       # 四层记忆实现
├── index.go        # 多维索引系统
├── compressor.go   # 记忆压缩器
└── brain_test.go   # 测试用例
```

## 技术细节

### 记忆类型
- `MemoryTypeWorking` (0): 工作记忆
- `MemoryTypeSession` (1): 会话记忆
- `MemoryTypeEpisodic` (2): 情景记忆
- `MemoryTypeSemantic` (3): 语义记忆

### 记忆结构
```go
type Memory struct {
    ID          string
    Type        MemoryType
    Content     string
    Summary     string
    Entities    []Entity
    Importance  float64    // 0-1
    Emotion     float64    // -1 to 1
    AccessCount int
    CreatedAt   time.Time
    ExpiresAt   *time.Time
    Metadata    map[string]interface{}
}
```

### 查询接口
```go
type Query struct {
    Text       string
    Type       MemoryType
    Entities   []string
    TimeRange  *TimeRange
    Importance *Range
    Limit      int
}
```

## 性能考虑

- 工作记忆使用LRU缓存，O(1)访问
- 会话记忆使用HashMap，O(1)查找
- 情景记忆按时间排序，支持范围查询
- 语义记忆使用索引加速检索
- 遗忘机制异步执行，不影响主流程
