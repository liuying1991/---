package memory

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// MemoryType 记忆类型
type MemoryType int

const (
	MemoryTypeWorking   MemoryType = iota // L0: 工作记忆
	MemoryTypeSession                     // L1: 会话记忆
	MemoryTypeEpisodic                    // L2: 情景记忆
	MemoryTypeSemantic                    // L3: 语义记忆
)

// Memory 记忆单元
type Memory struct {
	ID          string                 `json:"id"`
	Type        MemoryType             `json:"type"`
	Content     string                 `json:"content"`
	Summary     string                 `json:"summary,omitempty"`
	Entities    []Entity               `json:"entities,omitempty"`
	Importance  float64                `json:"importance"`   // 0-1
	Emotion     float64                `json:"emotion"`      // -1 to 1 (负面到正面)
	AccessCount int                    `json:"access_count"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	ExpiresAt   *time.Time             `json:"expires_at,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Entity 实体
type Entity struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Type      string `json:"type"` // person, place, thing, concept
	Value     string `json:"value,omitempty"`
	Confidence float64 `json:"confidence"`
}

// Relation 关系
type Relation struct {
	From      string `json:"from"`
	To        string `json:"to"`
	Type      string `json:"type"` // owns, knows, related_to, caused_by
	Weight    float64 `json:"weight"`
	Timestamp time.Time `json:"timestamp"`
}

// Query 记忆查询
type Query struct {
	Text       string
	Type       MemoryType
	Entities   []string
	TimeRange  *TimeRange
	Importance *Range
	Limit      int
}

// TimeRange 时间范围
type TimeRange struct {
	Start time.Time
	End   time.Time
}

// Range 数值范围
type Range struct {
	Min float64
	Max float64
}

// Brain 记忆大脑
type Brain struct {
	// 四层记忆
	working   *WorkingMemory
	session   *SessionMemory
	episodic  *EpisodicMemory
	semantic  *SemanticMemory

	// 索引
	index *MemoryIndex

	// 压缩器
	compressor *Compressor

	// 配置
	config BrainConfig

	mu sync.RWMutex
}

// BrainConfig 大脑配置
type BrainConfig struct {
	WorkingCapacity  int           // 工作记忆容量
	SessionCapacity  int           // 会话记忆容量
	SessionTTL       time.Duration // 会话存活时间
	DecayRate        float64       // 遗忘衰减率
	ForgettingThreshold float64    // 遗忘阈值
	CompressInterval time.Duration // 压缩间隔
}

// NewBrain 创建记忆大脑
func NewBrain(config BrainConfig) *Brain {
	if config.WorkingCapacity == 0 {
		config.WorkingCapacity = 100
	}
	if config.SessionCapacity == 0 {
		config.SessionCapacity = 1000
	}
	if config.SessionTTL == 0 {
		config.SessionTTL = 7 * 24 * time.Hour
	}
	if config.DecayRate == 0 {
		config.DecayRate = 0.1
	}
	if config.ForgettingThreshold == 0 {
		config.ForgettingThreshold = 0.1
	}
	if config.CompressInterval == 0 {
		config.CompressInterval = time.Hour
	}

	brain := &Brain{
		working:    NewWorkingMemory(config.WorkingCapacity),
		session:    NewSessionMemory(config.SessionCapacity, config.SessionTTL),
		episodic:   NewEpisodicMemory(),
		semantic:   NewSemanticMemory(),
		index:      NewMemoryIndex(),
		compressor: NewCompressor(),
		config:     config,
	}

	return brain
}

// Remember 记忆
func (b *Brain) Remember(ctx context.Context, content string, opts ...RememberOption) (*Memory, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	// 应用选项
	options := &RememberOptions{
		Type:       MemoryTypeWorking,
		Importance: 0.5,
	}
	for _, opt := range opts {
		opt(options)
	}

	// 创建记忆
	memory := &Memory{
		ID:         generateID(),
		Type:       options.Type,
		Content:    content,
		Importance: options.Importance,
		Emotion:    options.Emotion,
		Entities:   options.Entities,
		Metadata:   options.Metadata,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	// 设置过期时间
	if options.TTL > 0 {
		expires := memory.CreatedAt.Add(options.TTL)
		memory.ExpiresAt = &expires
	}

	// 根据类型存储
	switch memory.Type {
	case MemoryTypeWorking:
		b.working.Store(memory)
	case MemoryTypeSession:
		b.session.Store(memory)
	case MemoryTypeEpisodic:
		b.episodic.Store(memory)
	case MemoryTypeSemantic:
		b.semantic.Store(memory)
	}

	// 更新索引
	b.index.Index(memory)

	return memory, nil
}

// Recall 回忆
func (b *Brain) Recall(ctx context.Context, query Query) ([]*Memory, error) {
	b.mu.RLock()
	defer b.mu.RUnlock()

	var results []*Memory

	// 从索引检索
	if query.Text != "" {
		ids := b.index.Search(query.Text, query.Limit)
		for _, id := range ids {
			if m := b.get(id); m != nil {
				results = append(results, m)
			}
		}
	} else {
		// 按类型检索
		switch query.Type {
		case MemoryTypeWorking:
			results = b.working.GetAll()
		case MemoryTypeSession:
			results = b.session.GetAll()
		case MemoryTypeEpisodic:
			results = b.episodic.GetAll()
		case MemoryTypeSemantic:
			results = b.semantic.GetAll()
		default:
			// 全局检索
			results = append(results, b.working.GetAll()...)
			results = append(results, b.session.GetAll()...)
		}
	}

	// 过滤
	results = b.filter(results, query)

	// 限制数量
	if query.Limit > 0 && len(results) > query.Limit {
		results = results[:query.Limit]
	}

	// 更新访问计数
	for _, m := range results {
		m.AccessCount++
	}

	return results, nil
}

// RecallContext 回忆上下文（用于LLM）
func (b *Brain) RecallContext(ctx context.Context, maxTokens int) string {
	b.mu.RLock()
	defer b.mu.RUnlock()

	var context string

	// L0: 工作记忆
	working := b.working.GetAll()
	for _, m := range working {
		context += m.Content + "\n"
	}

	// L1: 会话摘要
	if summary := b.session.GetSummary(); summary != "" {
		context += "[会话摘要] " + summary + "\n"
	}

	// L3: 用户画像
	if profile := b.semantic.GetUserProfile(); profile != "" {
		context += "[用户画像] " + profile + "\n"
	}

	return context
}

// Update 更新记忆
func (b *Brain) Update(ctx context.Context, id string, update func(*Memory)) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	memory := b.get(id)
	if memory == nil {
		return fmt.Errorf("记忆不存在: %s", id)
	}

	update(memory)
	memory.UpdatedAt = time.Now()

	// 更新索引
	b.index.Update(memory)

	return nil
}

// Forget 遗忘
func (b *Brain) Forget(ctx context.Context) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	// 计算记忆强度并移除低强度记忆
	forgetThreshold := b.config.ForgettingThreshold

	// 检查会话记忆
	b.session.ForEach(func(m *Memory) bool {
		strength := b.calculateStrength(m)
		if strength < forgetThreshold {
			b.session.Delete(m.ID)
			b.index.Remove(m.ID)
		}
		return true
	})

	// 检查情景记忆
	b.episodic.ForEach(func(m *Memory) bool {
		strength := b.calculateStrength(m)
		if strength < forgetThreshold {
			b.episodic.Delete(m.ID)
			b.index.Remove(m.ID)
		}
		return true
	})

	return nil
}

// Compress 压缩记忆
func (b *Brain) Compress(ctx context.Context) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	// 压缩工作记忆到会话记忆
	working := b.working.GetAll()
	if len(working) > 0 {
		summary, err := b.compressor.Compress(working)
		if err == nil && summary != nil {
			b.session.Store(summary)
			b.index.Index(summary)
		}
	}

	// 压缩会话记忆到情景记忆
	sessions := b.session.GetOldSessions()
	for _, session := range sessions {
		episodic, err := b.compressor.ToEpisodic(session)
		if err == nil && episodic != nil {
			b.episodic.Store(episodic)
			b.index.Index(episodic)
		}
	}

	return nil
}

// LearnUserPreference 学习用户偏好
func (b *Brain) LearnUserPreference(ctx context.Context, key, value string, confidence float64) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	return b.semantic.SetUserPreference(key, value, confidence)
}

// GetUserPreference 获取用户偏好
func (b *Brain) GetUserPreference(key string) (string, float64, bool) {
	return b.semantic.GetUserPreference(key)
}

// AddKnowledge 添加知识
func (b *Brain) AddKnowledge(ctx context.Context, entity, relation, value string) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	return b.semantic.AddKnowledge(entity, relation, value)
}

// QueryKnowledge 查询知识
func (b *Brain) QueryKnowledge(ctx context.Context, entity string) ([]Relation, error) {
	return b.semantic.QueryKnowledge(entity)
}

// get 获取记忆
func (b *Brain) get(id string) *Memory {
	if m := b.working.Get(id); m != nil {
		return m
	}
	if m := b.session.Get(id); m != nil {
		return m
	}
	if m := b.episodic.Get(id); m != nil {
		return m
	}
	if m := b.semantic.Get(id); m != nil {
		return m
	}
	return nil
}

// filter 过滤记忆
func (b *Brain) filter(memories []*Memory, query Query) []*Memory {
	var result []*Memory

	for _, m := range memories {
		// 时间范围过滤
		if query.TimeRange != nil {
			if m.CreatedAt.Before(query.TimeRange.Start) || m.CreatedAt.After(query.TimeRange.End) {
				continue
			}
		}

		// 重要性过滤
		if query.Importance != nil {
			if m.Importance < query.Importance.Min || m.Importance > query.Importance.Max {
				continue
			}
		}

		// 实体过滤
		if len(query.Entities) > 0 {
			found := false
			for _, e := range m.Entities {
				for _, qe := range query.Entities {
					if e.Name == qe {
						found = true
						break
					}
				}
			}
			if !found {
				continue
			}
		}

		result = append(result, m)
	}

	return result
}

// calculateStrength 计算记忆强度
func (b *Brain) calculateStrength(m *Memory) float64 {
	// S(t) = I × F × e^(-λt) × E
	// I: 初始重要性
	// F: 访问频率因子
	// λ: 衰减系数
	// t: 时间（小时）
	// E: 情感权重

	t := time.Since(m.CreatedAt).Hours()
	lambda := b.config.DecayRate

	// 访问频率因子
	frequencyFactor := 1.0 + float64(m.AccessCount)*0.1

	// 情感权重 (绝对值，情感越强记忆越深)
	emotionWeight := 1.0 + 0.5*abs(m.Emotion)

	// 计算强度
	strength := m.Importance * frequencyFactor * exp(-lambda*t) * emotionWeight

	return strength
}

// RememberOption 记忆选项
type RememberOption func(*RememberOptions)

// RememberOptions 记忆选项
type RememberOptions struct {
	Type       MemoryType
	Importance float64
	Emotion    float64
	Entities   []Entity
	TTL        time.Duration
	Metadata   map[string]interface{}
}

// WithType 设置类型
func WithType(t MemoryType) RememberOption {
	return func(o *RememberOptions) {
		o.Type = t
	}
}

// WithImportance 设置重要性
func WithImportance(i float64) RememberOption {
	return func(o *RememberOptions) {
		o.Importance = i
	}
}

// WithEmotion 设置情感
func WithEmotion(e float64) RememberOption {
	return func(o *RememberOptions) {
		o.Emotion = e
	}
}

// WithEntities 设置实体
func WithEntities(entities []Entity) RememberOption {
	return func(o *RememberOptions) {
		o.Entities = entities
	}
}

// WithTTL 设置存活时间
func WithTTL(ttl time.Duration) RememberOption {
	return func(o *RememberOptions) {
		o.TTL = ttl
	}
}

// 辅助函数
func generateID() string {
	return fmt.Sprintf("mem_%d", time.Now().UnixNano())
}

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

func exp(x float64) float64 {
	// 简化的指数函数
	result := 1.0
	term := 1.0
	for i := 1; i <= 10; i++ {
		term *= x / float64(i)
		result += term
	}
	return result
}

// ToJSON 序列化
func (m *Memory) ToJSON() string {
	data, _ := json.Marshal(m)
	return string(data)
}

// FromJSON 反序列化
func MemoryFromJSON(data string) (*Memory, error) {
	var m Memory
	err := json.Unmarshal([]byte(data), &m)
	return &m, err
}
