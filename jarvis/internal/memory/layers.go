package memory

import (
	"container/list"
	"sync"
	"time"
)

// WorkingMemory L0: 工作记忆（当前上下文）
type WorkingMemory struct {
	capacity int
	items    map[string]*list.Element
	order    *list.List // LRU顺序
	mu       sync.RWMutex
}

// NewWorkingMemory 创建工作记忆
func NewWorkingMemory(capacity int) *WorkingMemory {
	return &WorkingMemory{
		capacity: capacity,
		items:    make(map[string]*list.Element),
		order:    list.New(),
	}
}

// Store 存储
func (m *WorkingMemory) Store(memory *Memory) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 如果已存在，移到前面
	if elem, ok := m.items[memory.ID]; ok {
		m.order.MoveToFront(elem)
		elem.Value = memory
		return
	}

	// 检查容量
	if m.order.Len() >= m.capacity {
		// 移除最旧的
		oldest := m.order.Back()
		if oldest != nil {
			oldMem := oldest.Value.(*Memory)
			delete(m.items, oldMem.ID)
			m.order.Remove(oldest)
		}
	}

	// 添加新记忆
	elem := m.order.PushFront(memory)
	m.items[memory.ID] = elem
}

// Get 获取
func (m *WorkingMemory) Get(id string) *Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if elem, ok := m.items[id]; ok {
		return elem.Value.(*Memory)
	}
	return nil
}

// GetAll 获取所有
func (m *WorkingMemory) GetAll() []*Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Memory, 0, m.order.Len())
	for elem := m.order.Front(); elem != nil; elem = elem.Next() {
		result = append(result, elem.Value.(*Memory))
	}
	return result
}

// Delete 删除
func (m *WorkingMemory) Delete(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if elem, ok := m.items[id]; ok {
		m.order.Remove(elem)
		delete(m.items, id)
	}
}

// Clear 清空
func (m *WorkingMemory) Clear() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.items = make(map[string]*list.Element)
	m.order = list.New()
}

// SessionMemory L1: 会话记忆
type SessionMemory struct {
	capacity int
	ttl      time.Duration
	items    map[string]*Memory
	sessions map[string]*Session // 会话分组
	mu       sync.RWMutex
}

// Session 会话
type Session struct {
	ID        string
	Memories  []*Memory
	Summary   string
	StartTime time.Time
	EndTime   *time.Time
}

// NewSessionMemory 创建会话记忆
func NewSessionMemory(capacity int, ttl time.Duration) *SessionMemory {
	return &SessionMemory{
		capacity: capacity,
		ttl:      ttl,
		items:    make(map[string]*Memory),
		sessions: make(map[string]*Session),
	}
}

// Store 存储
func (m *SessionMemory) Store(memory *Memory) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.items[memory.ID] = memory
}

// Get 获取
func (m *SessionMemory) Get(id string) *Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.items[id]
}

// GetAll 获取所有
func (m *SessionMemory) GetAll() []*Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Memory, 0, len(m.items))
	for _, item := range m.items {
		// 检查是否过期
		if item.ExpiresAt != nil && time.Now().After(*item.ExpiresAt) {
			continue
		}
		result = append(result, item)
	}
	return result
}

// Delete 删除
func (m *SessionMemory) Delete(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.items, id)
}

// ForEach 遍历
func (m *SessionMemory) ForEach(fn func(*Memory) bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, item := range m.items {
		if !fn(item) {
			break
		}
	}
}

// GetSummary 获取摘要
func (m *SessionMemory) GetSummary() string {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, session := range m.sessions {
		if session.EndTime == nil {
			return session.Summary
		}
	}
	return ""
}

// GetOldSessions 获取旧会话
func (m *SessionMemory) GetOldSessions() []*Session {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Session, 0)
	for _, session := range m.sessions {
		if session.EndTime != nil {
			result = append(result, session)
		}
	}
	return result
}

// EpisodicMemory L2: 情景记忆（事件时间线）
type EpisodicMemory struct {
	items  map[string]*Memory
	timeline []*Memory // 时间顺序
	mu     sync.RWMutex
}

// NewEpisodicMemory 创建情景记忆
func NewEpisodicMemory() *EpisodicMemory {
	return &EpisodicMemory{
		items:    make(map[string]*Memory),
		timeline: make([]*Memory, 0),
	}
}

// Store 存储
func (m *EpisodicMemory) Store(memory *Memory) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.items[memory.ID] = memory

	// 按时间插入
	for i, item := range m.timeline {
		if memory.CreatedAt.Before(item.CreatedAt) {
			m.timeline = append(m.timeline[:i], append([]*Memory{memory}, m.timeline[i:]...)...)
			return
		}
	}
	m.timeline = append(m.timeline, memory)
}

// Get 获取
func (m *EpisodicMemory) Get(id string) *Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.items[id]
}

// GetAll 获取所有
func (m *EpisodicMemory) GetAll() []*Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Memory, len(m.timeline))
	copy(result, m.timeline)
	return result
}

// Delete 删除
func (m *EpisodicMemory) Delete(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	delete(m.items, id)

	for i, item := range m.timeline {
		if item.ID == id {
			m.timeline = append(m.timeline[:i], m.timeline[i+1:]...)
			break
		}
	}
}

// ForEach 遍历
func (m *EpisodicMemory) ForEach(fn func(*Memory) bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, item := range m.timeline {
		if !fn(item) {
			break
		}
	}
}

// GetRange 获取时间范围
func (m *EpisodicMemory) GetRange(start, end time.Time) []*Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Memory, 0)
	for _, item := range m.timeline {
		if item.CreatedAt.After(start) && item.CreatedAt.Before(end) {
			result = append(result, item)
		}
	}
	return result
}

// SemanticMemory L3: 语义记忆（知识图谱）
type SemanticMemory struct {
	items        map[string]*Memory
	userProfile  map[string]Preference // 用户画像
	knowledge    map[string][]Relation // 知识图谱
	skills       map[string]string     // 技能库
	mu           sync.RWMutex
}

// Preference 用户偏好
type Preference struct {
	Key        string
	Value      string
	Confidence float64
	UpdatedAt  time.Time
}

// NewSemanticMemory 创建语义记忆
func NewSemanticMemory() *SemanticMemory {
	return &SemanticMemory{
		items:       make(map[string]*Memory),
		userProfile: make(map[string]Preference),
		knowledge:   make(map[string][]Relation),
		skills:      make(map[string]string),
	}
}

// Store 存储
func (m *SemanticMemory) Store(memory *Memory) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.items[memory.ID] = memory
}

// Get 获取
func (m *SemanticMemory) Get(id string) *Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.items[id]
}

// GetAll 获取所有
func (m *SemanticMemory) GetAll() []*Memory {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Memory, 0, len(m.items))
	for _, item := range m.items {
		result = append(result, item)
	}
	return result
}

// Delete 删除
func (m *SemanticMemory) Delete(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.items, id)
}

// SetUserPreference 设置用户偏好
func (m *SemanticMemory) SetUserPreference(key, value string, confidence float64) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.userProfile[key] = Preference{
		Key:        key,
		Value:      value,
		Confidence: confidence,
		UpdatedAt:  time.Now(),
	}
	return nil
}

// GetUserPreference 获取用户偏好
func (m *SemanticMemory) GetUserPreference(key string) (string, float64, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if pref, ok := m.userProfile[key]; ok {
		return pref.Value, pref.Confidence, true
	}
	return "", 0, false
}

// GetUserProfile 获取用户画像
func (m *SemanticMemory) GetUserProfile() string {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if len(m.userProfile) == 0 {
		return ""
	}

	result := ""
	for key, pref := range m.userProfile {
		if pref.Confidence > 0.5 {
			result += key + ": " + pref.Value + "; "
		}
	}
	return result
}

// AddKnowledge 添加知识
func (m *SemanticMemory) AddKnowledge(entity, relation, value string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	r := Relation{
		From:      entity,
		To:        value,
		Type:      relation,
		Weight:    1.0,
		Timestamp: time.Now(),
	}

	m.knowledge[entity] = append(m.knowledge[entity], r)
	return nil
}

// QueryKnowledge 查询知识
func (m *SemanticMemory) QueryKnowledge(entity string) ([]Relation, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if relations, ok := m.knowledge[entity]; ok {
		return relations, nil
	}
	return []Relation{}, nil
}

// AddSkill 添加技能
func (m *SemanticMemory) AddSkill(name, description string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.skills[name] = description
}

// GetSkills 获取技能
func (m *SemanticMemory) GetSkills() map[string]string {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make(map[string]string)
	for k, v := range m.skills {
		result[k] = v
	}
	return result
}
