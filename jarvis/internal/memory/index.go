package memory

import (
	"strings"
	"sync"
)

// MemoryIndex 记忆索引
type MemoryIndex struct {
	// 关键词索引
	keywordIndex map[string][]string // keyword -> memory IDs

	// 实体索引
	entityIndex map[string][]string // entity name -> memory IDs

	// 类型索引
	typeIndex map[MemoryType][]string // type -> memory IDs

	// 重要性索引（优先队列）
	importanceQueue *PriorityQueue

	mu sync.RWMutex
}

// NewMemoryIndex 创建索引
func NewMemoryIndex() *MemoryIndex {
	return &MemoryIndex{
		keywordIndex:    make(map[string][]string),
		entityIndex:     make(map[string][]string),
		typeIndex:       make(map[MemoryType][]string),
		importanceQueue: NewPriorityQueue(),
	}
}

// Index 索引记忆
func (idx *MemoryIndex) Index(memory *Memory) {
	idx.mu.Lock()
	defer idx.mu.Unlock()

	// 关键词索引
	keywords := extractKeywords(memory.Content)
	for _, kw := range keywords {
		idx.keywordIndex[kw] = appendUnique(idx.keywordIndex[kw], memory.ID)
	}

	// 实体索引
	for _, entity := range memory.Entities {
		idx.entityIndex[entity.Name] = appendUnique(idx.entityIndex[entity.Name], memory.ID)
	}

	// 类型索引
	idx.typeIndex[memory.Type] = appendUnique(idx.typeIndex[memory.Type], memory.ID)

	// 重要性索引
	idx.importanceQueue.Push(memory.ID, memory.Importance)
}

// Update 更新索引
func (idx *MemoryIndex) Update(memory *Memory) {
	// 简单实现：重新索引
	idx.Remove(memory.ID)
	idx.Index(memory)
}

// Remove 移除索引
func (idx *MemoryIndex) Remove(id string) {
	idx.mu.Lock()
	defer idx.mu.Unlock()

	// 从关键词索引移除
	for kw, ids := range idx.keywordIndex {
		idx.keywordIndex[kw] = removeID(ids, id)
	}

	// 从实体索引移除
	for entity, ids := range idx.entityIndex {
		idx.entityIndex[entity] = removeID(ids, id)
	}

	// 从类型索引移除
	for t, ids := range idx.typeIndex {
		idx.typeIndex[t] = removeID(ids, id)
	}

	// 从重要性索引移除
	idx.importanceQueue.Remove(id)
}

// Search 搜索
func (idx *MemoryIndex) Search(query string, limit int) []string {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	// 提取查询关键词
	keywords := extractKeywords(query)

	// 统计匹配次数
	scores := make(map[string]int)
	for _, kw := range keywords {
		if ids, ok := idx.keywordIndex[kw]; ok {
			for _, id := range ids {
				scores[id]++
			}
		}
	}

	// 按分数排序
	type scored struct {
		id    string
		score int
	}
	var results []scored
	for id, score := range scores {
		results = append(results, scored{id, score})
	}

	// 简单排序
	for i := 0; i < len(results); i++ {
		for j := i + 1; j < len(results); j++ {
			if results[j].score > results[i].score {
				results[i], results[j] = results[j], results[i]
			}
		}
	}

	// 返回结果
	ids := make([]string, 0, limit)
	for i := 0; i < len(results) && i < limit; i++ {
		ids = append(ids, results[i].id)
	}
	return ids
}

// SearchByEntity 按实体搜索
func (idx *MemoryIndex) SearchByEntity(entity string) []string {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	return idx.entityIndex[entity]
}

// SearchByType 按类型搜索
func (idx *MemoryIndex) SearchByType(t MemoryType) []string {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	return idx.typeIndex[t]
}

// GetTopImportant 获取最重要的记忆
func (idx *MemoryIndex) GetTopImportant(limit int) []string {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	return idx.importanceQueue.Top(limit)
}

// PriorityQueue 优先队列
type PriorityQueue struct {
	items []*queueItem
	index map[string]int
}

type queueItem struct {
	id         string
	importance float64
}

// NewPriorityQueue 创建优先队列
func NewPriorityQueue() *PriorityQueue {
	return &PriorityQueue{
		items: make([]*queueItem, 0),
		index: make(map[string]int),
	}
}

// Push 推入
func (q *PriorityQueue) Push(id string, importance float64) {
	if pos, exists := q.index[id]; exists {
		q.items[pos].importance = importance
		q.heapify(pos)
		return
	}

	item := &queueItem{id, importance}
	q.items = append(q.items, item)
	q.index[id] = len(q.items) - 1
	q.heapUp(len(q.items) - 1)
}

// Remove 移除
func (q *PriorityQueue) Remove(id string) {
	if pos, exists := q.index[id]; exists {
		delete(q.index, id)
		q.items = append(q.items[:pos], q.items[pos+1:]...)
		for i := range q.index {
			if q.index[i] > pos {
				q.index[i]--
			}
		}
	}
}

// Top 获取顶部N个
func (q *PriorityQueue) Top(n int) []string {
	if n > len(q.items) {
		n = len(q.items)
	}

	// 复制并排序
	items := make([]*queueItem, len(q.items))
	copy(items, q.items)

	// 简单排序
	for i := 0; i < len(items); i++ {
		for j := i + 1; j < len(items); j++ {
			if items[j].importance > items[i].importance {
				items[i], items[j] = items[j], items[i]
			}
		}
	}

	result := make([]string, 0, n)
	for i := 0; i < n && i < len(items); i++ {
		result = append(result, items[i].id)
	}
	return result
}

func (q *PriorityQueue) heapUp(pos int) {
	for pos > 0 {
		parent := (pos - 1) / 2
		if q.items[parent].importance >= q.items[pos].importance {
			break
		}
		q.items[parent], q.items[pos] = q.items[pos], q.items[parent]
		q.index[q.items[parent].id] = parent
		q.index[q.items[pos].id] = pos
		pos = parent
	}
}

func (q *PriorityQueue) heapify(pos int) {
	q.heapUp(pos)
	q.heapDown(pos)
}

func (q *PriorityQueue) heapDown(pos int) {
	n := len(q.items)
	for {
		left := 2*pos + 1
		right := 2*pos + 2
		largest := pos

		if left < n && q.items[left].importance > q.items[largest].importance {
			largest = left
		}
		if right < n && q.items[right].importance > q.items[largest].importance {
			largest = right
		}

		if largest == pos {
			break
		}

		q.items[pos], q.items[largest] = q.items[largest], q.items[pos]
		q.index[q.items[pos].id] = pos
		q.index[q.items[largest].id] = largest
		pos = largest
	}
}

// 辅助函数
func extractKeywords(text string) []string {
	// 简单的关键词提取
	words := strings.Fields(strings.ToLower(text))
	keywords := make([]string, 0)
	for _, word := range words {
		// 过滤短词和常见词
		if len(word) >= 2 && !isStopWord(word) {
			keywords = append(keywords, word)
		}
	}
	return keywords
}

func isStopWord(word string) bool {
	stopWords := map[string]bool{
		"the": true, "a": true, "an": true, "is": true, "are": true,
		"was": true, "were": true, "be": true, "been": true,
		"have": true, "has": true, "had": true, "do": true,
		"does": true, "did": true, "will": true, "would": true,
		"could": true, "should": true, "may": true, "might": true,
		"must": true, "can": true, "to": true, "of": true,
		"in": true, "for": true, "on": true, "with": true,
		"at": true, "by": true, "from": true, "as": true,
		"的": true, "是": true, "在": true, "有": true,
		"和": true, "了": true, "不": true, "我": true,
	}
	return stopWords[word]
}

func appendUnique(ids []string, id string) []string {
	for _, existing := range ids {
		if existing == id {
			return ids
		}
	}
	return append(ids, id)
}

func removeID(ids []string, id string) []string {
	for i, existing := range ids {
		if existing == id {
			return append(ids[:i], ids[i+1:]...)
		}
	}
	return ids
}
