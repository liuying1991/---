package dialog

import (
	"context"
	"encoding/json"
	"fmt"

	"jarvis/internal/llm"
	"jarvis/internal/skills"
)

// Manager 对话管理器
type Manager struct {
	engine        llm.Engine
	skillRegistry *skills.SkillRegistry
	history       []llm.Message
	systemPrompt  string
	historyLength int
	stream        bool
}

// NewManager 创建对话管理器
func NewManager(engine llm.Engine, registry *skills.SkillRegistry, systemPrompt string, historyLength int, stream bool) *Manager {
	return &Manager{
		engine:        engine,
		skillRegistry: registry,
		history:       make([]llm.Message, 0),
		systemPrompt:  systemPrompt,
		historyLength: historyLength,
		stream:        stream,
	}
}

// Chat 发起对话
func (m *Manager) Chat(ctx context.Context, userMessage string) (string, error) {
	// 添加用户消息到历史
	m.history = append(m.history, llm.Message{
		Role:    "user",
		Content: userMessage,
	})

	// 构建消息列表
	messages := m.buildMessages()

	// 调用LLM
	result, err := m.engine.Generate(ctx, llm.GenerateOptions{
		Messages: messages,
		Stream:   false,
	})
	if err != nil {
		return "", fmt.Errorf("生成回复失败: %w", err)
	}

	// 处理工具调用
	if len(result.ToolCalls) > 0 {
		// 添加助手消息（包含工具调用）
		m.history = append(m.history, llm.Message{
			Role:      "assistant",
			Content:   result.Content,
			ToolCalls: result.ToolCalls,
		})

		// 执行工具调用
		for _, toolCall := range result.ToolCalls {
			skill, ok := m.skillRegistry.Get(toolCall.Function.Name)
			if !ok {
				continue
			}

			toolResult, err := skill.Execute(ctx, toolCall.Function.Arguments)
			if err != nil {
				toolResult = map[string]interface{}{"error": err.Error()}
			}

			// 添加工具结果消息
			resultJSON, _ := json.Marshal(toolResult)
			m.history = append(m.history, llm.Message{
				Role:       "tool",
				Content:    string(resultJSON),
				ToolCallID: toolCall.ID,
			})
		}

		// 再次调用LLM获取最终回复
		messages = m.buildMessages()
		result, err = m.engine.Generate(ctx, llm.GenerateOptions{
			Messages: messages,
			Stream:   false,
		})
		if err != nil {
			return "", fmt.Errorf("生成最终回复失败: %w", err)
		}
	}

	// 添加助手回复到历史
	m.history = append(m.history, llm.Message{
		Role:    "assistant",
		Content: result.Content,
	})

	// 限制历史长度
	m.trimHistory()

	return result.Content, nil
}

// ChatStream 流式对话
func (m *Manager) ChatStream(ctx context.Context, userMessage string) (<-chan StreamResult, error) {
	// 添加用户消息到历史
	m.history = append(m.history, llm.Message{
		Role:    "user",
		Content: userMessage,
	})

	// 构建消息列表
	messages := m.buildMessages()

	// 调用LLM流式接口
	stream, err := m.engine.Stream(ctx, llm.GenerateOptions{
		Messages: messages,
		Stream:   true,
	})
	if err != nil {
		return nil, fmt.Errorf("创建流失败: %w", err)
	}

	// 转换输出
	resultChan := make(chan StreamResult, 100)
	go func() {
		defer close(resultChan)
		var fullContent string

		for chunk := range stream {
			if chunk.Error != nil {
				resultChan <- StreamResult{Error: chunk.Error}
				return
			}

			fullContent += chunk.Content
			resultChan <- StreamResult{
				Content: chunk.Content,
				Done:    chunk.Done,
			}

			if chunk.Done {
				// 添加完整回复到历史
				m.history = append(m.history, llm.Message{
					Role:    "assistant",
					Content: fullContent,
				})
				m.trimHistory()
			}
		}
	}()

	return resultChan, nil
}

// StreamResult 流式结果
type StreamResult struct {
	Content string
	Done    bool
	Error   error
}

// buildMessages 构建消息列表
func (m *Manager) buildMessages() []llm.Message {
	messages := make([]llm.Message, 0, len(m.history)+1)

	// 添加系统提示
	if m.systemPrompt != "" {
		messages = append(messages, llm.Message{
			Role:    "system",
			Content: m.systemPrompt,
		})
	}

	// 添加历史消息
	messages = append(messages, m.history...)

	return messages
}

// trimHistory 裁剪历史
func (m *Manager) trimHistory() {
	if len(m.history) > m.historyLength {
		m.history = m.history[len(m.history)-m.historyLength:]
	}
}

// ClearHistory 清空历史
func (m *Manager) ClearHistory() {
	m.history = make([]llm.Message, 0)
}

// GetHistory 获取历史
func (m *Manager) GetHistory() []llm.Message {
	return m.history
}
