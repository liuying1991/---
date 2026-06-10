package skills

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// HTTPRequestSkill HTTP请求技能
type HTTPRequestSkill struct {
	client *http.Client
}

// NewHTTPRequestSkill 创建HTTP请求技能
func NewHTTPRequestSkill() *HTTPRequestSkill {
	return &HTTPRequestSkill{
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Name 技能名称
func (s *HTTPRequestSkill) Name() string {
	return "http_request"
}

// Description 技能描述
func (s *HTTPRequestSkill) Description() string {
	return "发送HTTP请求获取网络数据"
}

// Parameters 参数定义
func (s *HTTPRequestSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"url": map[string]interface{}{
				"type":        "string",
				"description": "请求URL",
			},
			"method": map[string]interface{}{
				"type":        "string",
				"description": "请求方法 (GET/POST)",
				"enum":        []string{"GET", "POST"},
			},
			"headers": map[string]interface{}{
				"type":        "object",
				"description": "请求头",
			},
			"body": map[string]interface{}{
				"type":        "string",
				"description": "请求体 (POST时使用)",
			},
		},
		"required": []string{"url"},
	}
}

// Execute 执行HTTP请求
func (s *HTTPRequestSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		URL     string            `json:"url"`
		Method  string            `json:"method"`
		Headers map[string]string `json:"headers"`
		Body    string            `json:"body"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	// 默认GET方法
	if params.Method == "" {
		params.Method = "GET"
	}

	// 创建请求
	var req *http.Request
	var err error

	if params.Body != "" {
		req, err = http.NewRequestWithContext(ctx, params.Method, params.URL, strings.NewReader(params.Body))
	} else {
		req, err = http.NewRequestWithContext(ctx, params.Method, params.URL, nil)
	}
	if err != nil {
		return nil, fmt.Errorf("创建请求失败: %w", err)
	}

	// 设置请求头
	for key, value := range params.Headers {
		req.Header.Set(key, value)
	}

	// 发送请求
	resp, err := s.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("发送请求失败: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("读取响应失败: %w", err)
	}

	return map[string]interface{}{
		"success":      true,
		"status_code":  resp.StatusCode,
		"headers":      resp.Header,
		"body":         string(body),
		"content_type": resp.Header.Get("Content-Type"),
	}, nil
}

// CalculatorSkill 计算器技能
type CalculatorSkill struct{}

// NewCalculatorSkill 创建计算器技能
func NewCalculatorSkill() *CalculatorSkill {
	return &CalculatorSkill{}
}

// Name 技能名称
func (s *CalculatorSkill) Name() string {
	return "calculate"
}

// Description 技能描述
func (s *CalculatorSkill) Description() string {
	return "执行数学计算"
}

// Parameters 参数定义
func (s *CalculatorSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"expression": map[string]interface{}{
				"type":        "string",
				"description": "数学表达式，如 '2+3*4'",
			},
		},
		"required": []string{"expression"},
	}
}

// Execute 执行计算
func (s *CalculatorSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Expression string `json:"expression"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	// 简单表达式计算（支持加减乘除）
	result, err := evaluateExpression(params.Expression)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"success":    true,
		"expression": params.Expression,
		"result":     result,
	}, nil
}

// evaluateExpression 计算表达式
func evaluateExpression(expr string) (float64, error) {
	// 移除空格
	expr = strings.ReplaceAll(expr, " ", "")

	// 简单实现：处理加减乘除
	// 先处理乘除
	for {
		mulIdx := strings.IndexAny(expr, "*/")
		if mulIdx == -1 {
			break
		}

		// 找到操作符前后的数字
		leftStart := mulIdx - 1
		for leftStart > 0 && (expr[leftStart-1] >= '0' && expr[leftStart-1] <= '9' || expr[leftStart-1] == '.' || expr[leftStart-1] == '-') {
			leftStart--
		}

		rightEnd := mulIdx + 1
		for rightEnd < len(expr) && (expr[rightEnd] >= '0' && expr[rightEnd] <= '9' || expr[rightEnd] == '.') {
			rightEnd++
		}

		// 解析数字并计算
		var left, right float64
		fmt.Sscanf(expr[leftStart:mulIdx], "%f", &left)
		fmt.Sscanf(expr[mulIdx+1:rightEnd], "%f", &right)

		var result float64
		if expr[mulIdx] == '*' {
			result = left * right
		} else {
			if right == 0 {
				return 0, fmt.Errorf("除数不能为零")
			}
			result = left / right
		}

		// 替换表达式
		expr = expr[:leftStart] + fmt.Sprintf("%g", result) + expr[rightEnd:]
	}

	// 再处理加减
	result := 0.0
	sign := 1.0
	num := 0.0
	hasNum := false

	for i := 0; i < len(expr); i++ {
		c := expr[i]
		if c >= '0' && c <= '9' || c == '.' {
			var err error
			num, err = parseNumber(expr[i:])
			if err != nil {
				return 0, err
			}
			// 跳过已解析的数字
			for i < len(expr)-1 && (expr[i+1] >= '0' && expr[i+1] <= '9' || expr[i+1] == '.') {
				i++
			}
			hasNum = true
		} else if c == '+' || c == '-' {
			if hasNum {
				result += sign * num
				hasNum = false
			}
			if c == '+' {
				sign = 1.0
			} else {
				sign = -1.0
			}
		}
	}

	if hasNum {
		result += sign * num
	}

	return result, nil
}

// parseNumber 解析数字
func parseNumber(s string) (float64, error) {
	var num float64
	var err error
	for i := 0; i < len(s); i++ {
		if s[i] >= '0' && s[i] <= '9' || s[i] == '.' {
			_, err = fmt.Sscanf(s[:i+1], "%f", &num)
		} else {
			break
		}
	}
	return num, err
}

// SearchSkill 搜索技能
type SearchSkill struct {
	apiKey string
}

// NewSearchSkill 创建搜索技能
func NewSearchSkill(apiKey string) *SearchSkill {
	return &SearchSkill{apiKey: apiKey}
}

// Name 技能名称
func (s *SearchSkill) Name() string {
	return "web_search"
}

// Description 技能描述
func (s *SearchSkill) Description() string {
	return "网络搜索信息"
}

// Parameters 参数定义
func (s *SearchSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"query": map[string]interface{}{
				"type":        "string",
				"description": "搜索关键词",
			},
			"count": map[string]interface{}{
				"type":        "integer",
				"description": "返回结果数量",
			},
		},
		"required": []string{"query"},
	}
}

// Execute 执行搜索
func (s *SearchSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Query string `json:"query"`
		Count int    `json:"count"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	if params.Count == 0 {
		params.Count = 5
	}

	// 使用DuckDuckGo搜索（无需API Key）
	searchURL := fmt.Sprintf("https://api.duckduckgo.com/?q=%s&format=json&no_html=1", url.QueryEscape(params.Query))

	resp, err := http.Get(searchURL)
	if err != nil {
		return nil, fmt.Errorf("搜索失败: %w", err)
	}
	defer resp.Body.Close()

	var result struct {
		AbstractText   string `json:"AbstractText"`
		AbstractURL    string `json:"AbstractURL"`
		AbstractSource string `json:"AbstractSource"`
		Heading        string `json:"Heading"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("解析搜索结果失败: %w", err)
	}

	return map[string]interface{}{
		"success": true,
		"query":   params.Query,
		"result": map[string]interface{}{
			"heading":    result.Heading,
			"abstract":   result.AbstractText,
			"url":        result.AbstractURL,
			"source":     result.AbstractSource,
		},
	}, nil
}

// DateTimeSkill 日期时间技能
type DateTimeSkill struct{}

// NewDateTimeSkill 创建日期时间技能
func NewDateTimeSkill() *DateTimeSkill {
	return &DateTimeSkill{}
}

// Name 技能名称
func (s *DateTimeSkill) Name() string {
	return "datetime"
}

// Description 技能描述
func (s *DateTimeSkill) Description() string {
	return "获取日期时间信息"
}

// Parameters 参数定义
func (s *DateTimeSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"format": map[string]interface{}{
				"type":        "string",
				"description": "时间格式 (default/iso/rfc)",
			},
		},
	}
}

// Execute 执行获取时间
func (s *DateTimeSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Format string `json:"format"`
	}
	json.Unmarshal(args, &params)

	now := time.Now()

	var formatted string
	switch params.Format {
	case "iso":
		formatted = now.Format(time.RFC3339)
	case "rfc":
		formatted = now.Format(time.RFC1123)
	default:
		formatted = now.Format("2006-01-02 15:04:05")
	}

	return map[string]interface{}{
		"success":   true,
		"timestamp": now.Unix(),
		"formatted": formatted,
		"weekday":   now.Weekday().String(),
		"timezone":  now.Location().String(),
	}, nil
}
