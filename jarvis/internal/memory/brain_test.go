package memory

import (
	"context"
	"fmt"
	"testing"
	"time"
)

// ExampleBrain 使用示例
func ExampleBrain() {
	// 创建记忆大脑
	brain := NewBrain(BrainConfig{
		WorkingCapacity:     100,
		SessionCapacity:     1000,
		SessionTTL:          7 * 24 * time.Hour,
		DecayRate:           0.1,
		ForgettingThreshold: 0.1,
	})

	ctx := context.Background()

	// 1. 工作记忆 - 当前对话
	brain.Remember(ctx, "用户询问关于Go语言的问题",
		WithType(MemoryTypeWorking),
		WithImportance(0.7),
		WithEntities([]Entity{
			{Name: "Go", Type: "concept", Confidence: 0.9},
		}),
	)

	// 2. 会话记忆 - 会话摘要
	brain.Remember(ctx, "用户偏好使用Go语言进行系统开发",
		WithType(MemoryTypeSession),
		WithImportance(0.8),
	)

	// 3. 情景记忆 - 事件记录
	brain.Remember(ctx, "成功执行了文件备份任务",
		WithType(MemoryTypeEpisodic),
		WithImportance(0.6),
		WithEntities([]Entity{
			{Name: "backup", Type: "task", Confidence: 0.95},
		}),
	)

	// 4. 语义记忆 - 用户画像
	brain.LearnUserPreference(ctx, "programming_language", "Go", 0.9)
	brain.LearnUserPreference(ctx, "editor", "VSCode", 0.8)

	// 5. 知识图谱
	brain.AddKnowledge(ctx, "Go", "is_a", "programming_language")
	brain.AddKnowledge(ctx, "Go", "created_by", "Google")

	// 检索记忆
	memories, _ := brain.Recall(ctx, Query{
		Text:  "Go语言",
		Limit: 5,
	})

	for _, m := range memories {
		fmt.Println(m.Content)
	}

	// 获取上下文（用于LLM）
	context := brain.RecallContext(ctx, 4000)
	fmt.Println(context)

	// 压缩记忆
	brain.Compress(ctx)

	// 遗忘低重要性记忆
	brain.Forget(ctx)
}

// TestMemoryBrain 测试记忆大脑
func TestMemoryBrain(t *testing.T) {
	brain := NewBrain(BrainConfig{
		WorkingCapacity:     10,
		SessionCapacity:     100,
		SessionTTL:          time.Hour,
		DecayRate:           0.1,
		ForgettingThreshold: 0.05,
	})

	ctx := context.Background()

	// 测试工作记忆
	t.Run("WorkingMemory", func(t *testing.T) {
		for i := 0; i < 15; i++ {
			brain.Remember(ctx, fmt.Sprintf("消息%d", i),
				WithType(MemoryTypeWorking),
				WithImportance(0.5),
			)
		}

		memories, err := brain.Recall(ctx, Query{Type: MemoryTypeWorking})
		if err != nil {
			t.Fatal(err)
		}
		if len(memories) > 10 {
			t.Errorf("工作记忆应该限制在10条以内，实际: %d", len(memories))
		}
	})

	// 测试用户偏好
	t.Run("UserPreference", func(t *testing.T) {
		brain.LearnUserPreference(ctx, "language", "Go", 0.9)
		value, confidence, ok := brain.GetUserPreference("language")
		if !ok {
			t.Error("应该找到用户偏好")
		}
		if value != "Go" {
			t.Errorf("期望 Go, 实际: %s", value)
		}
		if confidence != 0.9 {
			t.Errorf("期望 0.9, 实际: %f", confidence)
		}
	})

	// 测试知识图谱
	t.Run("KnowledgeGraph", func(t *testing.T) {
		brain.AddKnowledge(ctx, "Go", "is_a", "programming_language")
		relations, err := brain.QueryKnowledge(ctx, "Go")
		if err != nil {
			t.Fatal(err)
		}
		if len(relations) == 0 {
			t.Error("应该找到知识关系")
		}
	})

	// 测试记忆压缩
	t.Run("Compress", func(t *testing.T) {
		for i := 0; i < 5; i++ {
			brain.Remember(ctx, fmt.Sprintf("测试消息%d", i),
				WithType(MemoryTypeWorking),
				WithImportance(0.6),
			)
		}
		err := brain.Compress(ctx)
		if err != nil {
			t.Fatal(err)
		}
	})

	// 测试记忆遗忘
	t.Run("Forget", func(t *testing.T) {
		// 添加低重要性记忆
		brain.Remember(ctx, "不重要的信息",
			WithType(MemoryTypeSession),
			WithImportance(0.01),
		)
		err := brain.Forget(ctx)
		if err != nil {
			t.Fatal(err)
		}
	})
}

// TestMemoryIndex 测试记忆索引
func TestMemoryIndex(t *testing.T) {
	index := NewMemoryIndex()

	// 索引记忆
	m1 := &Memory{
		ID:        "1",
		Content:   "Go语言是一种编程语言",
		Type:      MemoryTypeWorking,
		Importance: 0.8,
		Entities:  []Entity{{Name: "Go", Type: "concept"}},
	}
	index.Index(m1)

	m2 := &Memory{
		ID:        "2",
		Content:   "Python是另一种编程语言",
		Type:      MemoryTypeWorking,
		Importance: 0.7,
		Entities:  []Entity{{Name: "Python", Type: "concept"}},
	}
	index.Index(m2)

	// 测试搜索
	t.Run("Search", func(t *testing.T) {
		ids := index.Search("Go", 10)
		if len(ids) == 0 {
			t.Error("应该找到Go相关的记忆")
		}
	})

	// 测试实体搜索
	t.Run("SearchByEntity", func(t *testing.T) {
		ids := index.SearchByEntity("Go")
		if len(ids) == 0 {
			t.Error("应该找到Go实体的记忆")
		}
	})

	// 测试重要性排序
	t.Run("TopImportant", func(t *testing.T) {
		ids := index.GetTopImportant(10)
		if len(ids) == 0 {
			t.Error("应该返回重要性排序的记忆")
		}
	})
}

// TestCompressor 测试压缩器
func TestCompressor(t *testing.T) {
	compressor := NewCompressor()

	memories := []*Memory{
		{ID: "1", Content: "用户决定使用Go语言", Importance: 0.8},
		{ID: "2", Content: "用户偏好VSCode编辑器", Importance: 0.7},
		{ID: "3", Content: "执行了文件读取操作", Importance: 0.5},
	}

	t.Run("Compress", func(t *testing.T) {
		result, err := compressor.Compress(memories)
		if err != nil {
			t.Fatal(err)
		}
		if result == nil {
			t.Fatal("压缩结果不应为空")
		}
		if result.Summary == "" {
			t.Error("摘要不应为空")
		}
	})

	t.Run("ExtractKeyInfo", func(t *testing.T) {
		info := compressor.extractKeyInfo(memories)
		if len(info.Decisions) == 0 {
			t.Error("应该提取到决策信息")
		}
	})
}
