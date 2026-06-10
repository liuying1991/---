package llm

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"

	"jarvis/internal/core/logger"
)

// Message 对话消息
type Message struct {
	Role       string      `json:"role"`                  // system, user, assistant, tool
	Content    string      `json:"content"`               // 消息内容
	ToolCalls  []ToolCall  `json:"tool_calls,omitempty"`  // 工具调用
	ToolCallID string      `json:"tool_call_id,omitempty"`// 工具调用ID（用于tool角色）
}

// ToolCall 工具调用
type ToolCall struct {
	ID       string          `json:"id"`
	Type     string          `json:"type"`
	Function FunctionCall    `json:"function"`
}

// FunctionCall 函数调用
type FunctionCall struct {
	Name      string          `json:"name"`
	Arguments json.RawMessage `json:"arguments"`
}

// GenerateOptions 生成选项
type GenerateOptions struct {
	Messages    []Message
	Temperature float64
	MaxTokens   int
	Stream      bool
}

// GenerateResult 生成结果
type GenerateResult struct {
	Content   string
	ToolCalls []ToolCall
	FinishReason string
}

// Engine LLM引擎接口
type Engine interface {
	// Generate 生成回复
	Generate(ctx context.Context, opts GenerateOptions) (*GenerateResult, error)
	// Stream 流式生成
	Stream(ctx context.Context, opts GenerateOptions) (<-chan StreamChunk, error)
	// Close 关闭引擎
	Close() error
}

// StreamChunk 流式输出块
type StreamChunk struct {
	Content   string
	ToolCalls []ToolCall
	Done      bool
	Error     error
}

// LlamaCppEngine llama.cpp引擎实现
type LlamaCppEngine struct {
	apiBase    string
	modelPath  string
	httpClient *http.Client
}

// NewLlamaCppEngine 创建llama.cpp引擎
func NewLlamaCppEngine(apiBase, modelPath string) *LlamaCppEngine {
	return &LlamaCppEngine{
		apiBase:    apiBase,
		modelPath:  modelPath,
		httpClient: &http.Client{},
	}
}

// Generate 生成回复
func (e *LlamaCppEngine) Generate(ctx context.Context, opts GenerateOptions) (*GenerateResult, error) {
	// 构建请求
	reqBody := map[string]interface{}{
		"messages":    opts.Messages,
		"temperature": opts.Temperature,
		"max_tokens":  opts.MaxTokens,
		"stream":      false,
	}

	reqData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("序列化请求失败: %w", err)
	}

	// 发送请求
	url := fmt.Sprintf("%s/v1/chat/completions", e.apiBase)
	req, err := http.NewRequestWithContext(ctx, "POST", url, strings.NewReader(string(reqData)))
	if err != nil {
		return nil, fmt.Errorf("创建请求失败: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := e.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("发送请求失败: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("请求失败: %s, %s", resp.Status, string(body))
	}

	// 解析响应
	var respData struct {
		Choices []struct {
			Message struct {
				Content   string     `json:"content"`
				ToolCalls []ToolCall `json:"tool_calls"`
			} `json:"message"`
			FinishReason string `json:"finish_reason"`
		} `json:"choices"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, fmt.Errorf("解析响应失败: %w", err)
	}

	if len(respData.Choices) == 0 {
		return nil, fmt.Errorf("无响应内容")
	}

	return &GenerateResult{
		Content:      respData.Choices[0].Message.Content,
		ToolCalls:    respData.Choices[0].Message.ToolCalls,
		FinishReason: respData.Choices[0].FinishReason,
	}, nil
}

// Stream 流式生成
func (e *LlamaCppEngine) Stream(ctx context.Context, opts GenerateOptions) (<-chan StreamChunk, error) {
	ch := make(chan StreamChunk, 100)

	// 构建请求
	reqBody := map[string]interface{}{
		"messages":    opts.Messages,
		"temperature": opts.Temperature,
		"max_tokens":  opts.MaxTokens,
		"stream":      true,
	}

	reqData, err := json.Marshal(reqBody)
	if err != nil {
		close(ch)
		return ch, fmt.Errorf("序列化请求失败: %w", err)
	}

	// 发送请求
	url := fmt.Sprintf("%s/v1/chat/completions", e.apiBase)
	req, err := http.NewRequestWithContext(ctx, "POST", url, strings.NewReader(string(reqData)))
	if err != nil {
		close(ch)
		return ch, fmt.Errorf("创建请求失败: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := e.httpClient.Do(req)
	if err != nil {
		close(ch)
		return ch, fmt.Errorf("发送请求失败: %w", err)
	}

	// 异步读取流
	go func() {
		defer close(ch)
		defer resp.Body.Close()

		decoder := json.NewDecoder(resp.Body)
		for {
			var chunk struct {
				Choices []struct {
					Delta struct {
						Content   string     `json:"content"`
						ToolCalls []ToolCall `json:"tool_calls"`
					} `json:"delta"`
					FinishReason string `json:"finish_reason"`
				} `json:"choices"`
			}

			// 读取SSE数据
			line, err := decoder.Token()
			if err != nil {
				if err == io.EOF {
					ch <- StreamChunk{Done: true}
					return
				}
				ch <- StreamChunk{Error: err}
				return
			}

			// 跳过非数据行
			if line != "data" {
				continue
			}

			if err := decoder.Decode(&chunk); err != nil {
				ch <- StreamChunk{Error: err}
				return
			}

			if len(chunk.Choices) > 0 {
				ch <- StreamChunk{
					Content:   chunk.Choices[0].Delta.Content,
					ToolCalls: chunk.Choices[0].Delta.ToolCalls,
					Done:      chunk.Choices[0].FinishReason == "stop",
				}
			}
		}
	}()

	return ch, nil
}

// Close 关闭引擎
func (e *LlamaCppEngine) Close() error {
	return nil
}

// VLLMEngine vLLM引擎实现
type VLLMEngine struct {
	apiBase    string
	httpClient *http.Client
}

// NewVLLMEngine 创建vLLM引擎
func NewVLLMEngine(apiBase string) *VLLMEngine {
	return &VLLMEngine{
		apiBase:    apiBase,
		httpClient: &http.Client{},
	}
}

// Generate 生成回复（与llama.cpp相同的API）
func (e *VLLMEngine) Generate(ctx context.Context, opts GenerateOptions) (*GenerateResult, error) {
	// vLLM使用OpenAI兼容API，实现与llama.cpp相同
	engine := NewLlamaCppEngine(e.apiBase, "")
	return engine.Generate(ctx, opts)
}

// Stream 流式生成
func (e *VLLMEngine) Stream(ctx context.Context, opts GenerateOptions) (<-chan StreamChunk, error) {
	engine := NewLlamaCppEngine(e.apiBase, "")
	return engine.Stream(ctx, opts)
}

// Close 关闭引擎
func (e *VLLMEngine) Close() error {
	return nil
}

// NewEngine 根据配置创建引擎
func NewEngine(backend, apiBase, modelPath string) (Engine, error) {
	logger.Infof("创建LLM引擎: backend=%s, apiBase=%s", backend, apiBase)

	switch backend {
	case "llama_cpp":
		return NewLlamaCppEngine(apiBase, modelPath), nil
	case "vllm":
		return NewVLLMEngine(apiBase), nil
	case "openai_compatible":
		return NewLlamaCppEngine(apiBase, modelPath), nil
	default:
		return nil, fmt.Errorf("不支持的LLM后端: %s", backend)
	}
}
