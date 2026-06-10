package memory

import (
	"strings"
	"time"
)

// Compressor 记忆压缩器
type Compressor struct {
	// 可以注入LLM进行智能压缩
	// llm LLMEngine
}

// NewCompressor 创建压缩器
func NewCompressor() *Compressor {
	return &Compressor{}
}

// Compress 压缩工作记忆到会话摘要
func (c *Compressor) Compress(memories []*Memory) (*Memory, error) {
	if len(memories) == 0 {
		return nil, nil
	}

	// 提取关键信息
	keyInfo := c.extractKeyInfo(memories)

	// 生成摘要
	summary := c.generateSummary(memories, keyInfo)

	// 计算平均重要性
	avgImportance := 0.0
	for _, m := range memories {
		avgImportance += m.Importance
	}
	avgImportance /= float64(len(memories))

	// 创建压缩后的记忆
	compressed := &Memory{
		ID:         generateID(),
		Type:       MemoryTypeSession,
		Content:    summary,
		Summary:    summary,
		Importance: avgImportance,
		Entities:   keyInfo.Entities,
		CreatedAt:  memories[0].CreatedAt,
		UpdatedAt:  time.Now(),
		Metadata: map[string]interface{}{
			"compressed_count": len(memories),
			"compression_type": "session_summary",
		},
	}

	return compressed, nil
}

// ToEpisodic 转换为情景记忆
func (c *Compressor) ToEpisodic(session *Session) (*Memory, error) {
	if session == nil || len(session.Memories) == 0 {
		return nil, nil
	}

	// 提取事件
	events := c.extractEvents(session.Memories)

	// 生成事件描述
	description := c.generateEventDescription(events)

	// 计算重要性
	importance := c.calculateSessionImportance(session)

	// 创建情景记忆
	episodic := &Memory{
		ID:         generateID(),
		Type:       MemoryTypeEpisodic,
		Content:    description,
		Summary:    session.Summary,
		Importance: importance,
		Entities:   c.extractEntities(session.Memories),
		CreatedAt:  session.StartTime,
		UpdatedAt:  time.Now(),
		Metadata: map[string]interface{}{
			"session_id":    session.ID,
			"event_count":   len(events),
			"duration":      session.EndTime.Sub(session.StartTime).String(),
		},
	}

	return episodic, nil
}

// KeyInfo 关键信息
type KeyInfo struct {
	Entities   []Entity
	Decisions  []string
	Preferences map[string]string
	Facts      []string
}

// extractKeyInfo 提取关键信息
func (c *Compressor) extractKeyInfo(memories []*Memory) *KeyInfo {
	info := &KeyInfo{
		Entities:    make([]Entity, 0),
		Decisions:   make([]string, 0),
		Preferences: make(map[string]string),
		Facts:       make([]string, 0),
	}

	entityMap := make(map[string]Entity)

	for _, m := range memories {
		// 收集实体
		for _, e := range m.Entities {
			entityMap[e.Name] = e
		}

		// 识别决策
		if c.isDecision(m.Content) {
			info.Decisions = append(info.Decisions, m.Content)
		}

		// 识别偏好
		if pref, value := c.extractPreference(m.Content); pref != "" {
			info.Preferences[pref] = value
		}

		// 识别事实
		if c.isFact(m.Content) {
			info.Facts = append(info.Facts, m.Content)
		}
	}

	// 转换实体map为slice
	for _, e := range entityMap {
		info.Entities = append(info.Entities, e)
	}

	return info
}

// generateSummary 生成摘要
func (c *Compressor) generateSummary(memories []*Memory, keyInfo *KeyInfo) string {
	var parts []string

	// 添加决策
	if len(keyInfo.Decisions) > 0 {
		parts = append(parts, "关键决策: "+strings.Join(keyInfo.Decisions[:min(3, len(keyInfo.Decisions))], "; "))
	}

	// 添加事实
	if len(keyInfo.Facts) > 0 {
		parts = append(parts, "重要信息: "+strings.Join(keyInfo.Facts[:min(3, len(keyInfo.Facts))], "; "))
	}

	// 添加偏好
	if len(keyInfo.Preferences) > 0 {
		var prefs []string
		for k, v := range keyInfo.Preferences {
			prefs = append(prefs, k+"="+v)
		}
		parts = append(parts, "用户偏好: "+strings.Join(prefs[:min(3, len(prefs))], ", "))
	}

	if len(parts) == 0 {
		// 简单摘要
		return "会话包含 " + string(rune(len(memories))) + " 条交互"
	}

	return strings.Join(parts, " | ")
}

// extractEvents 提取事件
func (c *Compressor) extractEvents(memories []*Memory) []string {
	events := make([]string, 0)

	for _, m := range memories {
		// 识别事件类型
		eventType := c.identifyEventType(m.Content)
		if eventType != "" {
			events = append(events, "["+eventType+"] "+m.Content)
		}
	}

	return events
}

// generateEventDescription 生成事件描述
func (c *Compressor) generateEventDescription(events []string) string {
	if len(events) == 0 {
		return "无显著事件"
	}

	// 限制长度
	if len(events) > 10 {
		events = events[:10]
	}

	return strings.Join(events, "\n")
}

// calculateSessionImportance 计算会话重要性
func (c *Compressor) calculateSessionImportance(session *Session) float64 {
	importance := 0.0

	for _, m := range session.Memories {
		importance += m.Importance
	}

	if len(session.Memories) > 0 {
		importance /= float64(len(session.Memories))
	}

	// 会话长度因子
	lengthFactor := 1.0
	if len(session.Memories) > 20 {
		lengthFactor = 1.2 // 长会话更重要
	}

	return importance * lengthFactor
}

// extractEntities 提取实体
func (c *Compressor) extractEntities(memories []*Memory) []Entity {
	entityMap := make(map[string]Entity)

	for _, m := range memories {
		for _, e := range m.Entities {
			if existing, ok := entityMap[e.Name]; !ok || e.Confidence > existing.Confidence {
				entityMap[e.Name] = e
			}
		}
	}

	entities := make([]Entity, 0, len(entityMap))
	for _, e := range entityMap {
		entities = append(entities, e)
	}

	return entities
}

// isDecision 判断是否为决策
func (c *Compressor) isDecision(content string) bool {
	decisionKeywords := []string{
		"决定", "选择", "确定", "采用", "使用",
		"decide", "choose", "select", "determine",
	}
	content = strings.ToLower(content)
	for _, kw := range decisionKeywords {
		if strings.Contains(content, kw) {
			return true
		}
	}
	return false
}

// extractPreference 提取偏好
func (c *Compressor) extractPreference(content string) (string, string) {
	// 简单的偏好提取
	patterns := []struct {
		keyword string
		key     string
	}{
		{"我喜欢", "preference"},
		{"我偏好", "preference"},
		{"我习惯", "habit"},
		{"我喜欢用", "tool_preference"},
		{"I prefer", "preference"},
		{"I like", "preference"},
	}

	content = strings.ToLower(content)
	for _, p := range patterns {
		if idx := strings.Index(content, p.keyword); idx != -1 {
			value := strings.TrimSpace(content[idx+len(p.keyword):])
			if len(value) > 0 && len(value) < 50 {
				return p.key, value
			}
		}
	}

	return "", ""
}

// isFact 判断是否为事实
func (c *Compressor) isFact(content string) bool {
	factKeywords := []string{
		"是", "有", "在", "位于", "属于",
		"is", "are", "was", "were", "has", "have",
	}

	// 简单判断：包含事实关键词且不太长
	content = strings.ToLower(content)
	if len(content) > 100 {
		return false
	}

	for _, kw := range factKeywords {
		if strings.Contains(content, kw) {
			return true
		}
	}
	return false
}

// identifyEventType 识别事件类型
func (c *Compressor) identifyEventType(content string) string {
	content = strings.ToLower(content)

	// 任务相关
	if strings.Contains(content, "执行") || strings.Contains(content, "运行") ||
		strings.Contains(content, "execute") || strings.Contains(content, "run") {
		return "任务执行"
	}

	// 查询相关
	if strings.Contains(content, "查询") || strings.Contains(content, "搜索") ||
		strings.Contains(content, "query") || strings.Contains(content, "search") {
		return "信息查询"
	}

	// 文件操作
	if strings.Contains(content, "文件") || strings.Contains(content, "读取") ||
		strings.Contains(content, "file") || strings.Contains(content, "read") {
		return "文件操作"
	}

	// 系统操作
	if strings.Contains(content, "系统") || strings.Contains(content, "进程") ||
		strings.Contains(content, "system") || strings.Contains(content, "process") {
		return "系统操作"
	}

	return ""
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
