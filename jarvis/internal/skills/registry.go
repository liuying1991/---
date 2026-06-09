package skills

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"jarvis/internal/core/logger"
)

// Skill 技能接口
type Skill interface {
	// Name 技能名称
	Name() string
	// Description 技能描述
	Description() string
	// Parameters 参数定义(JSON Schema)
	Parameters() map[string]interface{}
	// Execute 执行技能
	Execute(ctx context.Context, args json.RawMessage) (interface{}, error)
}

// SkillRegistry 技能注册表
type SkillRegistry struct {
	skills map[string]Skill
	config SkillConfig
}

// SkillConfig 技能配置
type SkillConfig struct {
	Enabled          bool
	CommandWhitelist []string
	CommandBlacklist []string
	ConfirmDangerous bool
	WorkDir          string
}

// NewSkillRegistry 创建技能注册表
func NewSkillRegistry(cfg SkillConfig) *SkillRegistry {
	registry := &SkillRegistry{
		skills: make(map[string]Skill),
		config: cfg,
	}

	// 注册默认技能
	if cfg.Enabled {
		registry.Register(NewCommandSkill(cfg))
		registry.Register(NewFileReadSkill(cfg))
		registry.Register(NewFileWriteSkill(cfg))
		registry.Register(NewFileListSkill(cfg))
		registry.Register(NewSystemInfoSkill())
	}

	// 注册扩展技能
	registry.Register(NewHTTPRequestSkill())
	registry.Register(NewCalculatorSkill())
	registry.Register(NewSearchSkill(""))
	registry.Register(NewDateTimeSkill())

	// 注册系统技能
	registry.Register(NewProcessSkill())
	registry.Register(NewDiskUsageSkill())
	registry.Register(NewMemoryUsageSkill())
	registry.Register(NewScheduleTaskSkill())

	return registry
}

// Register 注册技能
func (r *SkillRegistry) Register(skill Skill) {
	r.skills[skill.Name()] = skill
	logger.Infof("注册技能: %s", skill.Name())
}

// Get 获取技能
func (r *SkillRegistry) Get(name string) (Skill, bool) {
	skill, ok := r.skills[name]
	return skill, ok
}

// List 列出所有技能
func (r *SkillRegistry) List() []Skill {
	result := make([]Skill, 0, len(r.skills))
	for _, skill := range r.skills {
		result = append(result, skill)
	}
	return result
}

// GetToolDefinitions 获取工具定义（用于LLM function calling）
func (r *SkillRegistry) GetToolDefinitions() []map[string]interface{} {
	tools := make([]map[string]interface{}, 0, len(r.skills))
	for _, skill := range r.skills {
		tools = append(tools, map[string]interface{}{
			"type": "function",
			"function": map[string]interface{}{
				"name":        skill.Name(),
				"description": skill.Description(),
				"parameters":  skill.Parameters(),
			},
		})
	}
	return tools
}

// CommandSkill 命令执行技能
type CommandSkill struct {
	config SkillConfig
}

// NewCommandSkill 创建命令技能
func NewCommandSkill(cfg SkillConfig) *CommandSkill {
	return &CommandSkill{config: cfg}
}

// Name 技能名称
func (s *CommandSkill) Name() string {
	return "execute_command"
}

// Description 技能描述
func (s *CommandSkill) Description() string {
	return "执行系统命令"
}

// Parameters 参数定义
func (s *CommandSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"command": map[string]interface{}{
				"type":        "string",
				"description": "要执行的命令",
			},
			"args": map[string]interface{}{
				"type":        "array",
				"items":       map[string]interface{}{"type": "string"},
				"description": "命令参数",
			},
		},
		"required": []string{"command"},
	}
}

// Execute 执行命令
func (s *CommandSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Command string   `json:"command"`
		Args    []string `json:"args"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	// 检查黑名单
	for _, blocked := range s.config.CommandBlacklist {
		if strings.Contains(params.Command+" "+strings.Join(params.Args, " "), blocked) {
			return nil, fmt.Errorf("命令被禁止: %s", blocked)
		}
	}

	// 检查白名单
	if len(s.config.CommandWhitelist) > 0 {
		allowed := false
		for _, cmd := range s.config.CommandWhitelist {
			if params.Command == cmd {
				allowed = true
				break
			}
		}
		if !allowed {
			return nil, fmt.Errorf("命令不在白名单中: %s", params.Command)
		}
	}

	// 执行命令
	cmd := exec.CommandContext(ctx, params.Command, params.Args...)
	cmd.Dir = s.config.WorkDir

	output, err := cmd.CombinedOutput()
	if err != nil {
		return map[string]interface{}{
			"success": false,
			"error":   err.Error(),
			"output":  string(output),
		}, nil
	}

	return map[string]interface{}{
		"success": true,
		"output":  string(output),
	}, nil
}

// FileReadSkill 文件读取技能
type FileReadSkill struct {
	config SkillConfig
}

// NewFileReadSkill 创建文件读取技能
func NewFileReadSkill(cfg SkillConfig) *FileReadSkill {
	return &FileReadSkill{config: cfg}
}

// Name 技能名称
func (s *FileReadSkill) Name() string {
	return "read_file"
}

// Description 技能描述
func (s *FileReadSkill) Description() string {
	return "读取文件内容"
}

// Parameters 参数定义
func (s *FileReadSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"path": map[string]interface{}{
				"type":        "string",
				"description": "文件路径",
			},
		},
		"required": []string{"path"},
	}
}

// Execute 执行读取
func (s *FileReadSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Path string `json:"path"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	// 处理相对路径
	path := params.Path
	if !filepath.IsAbs(path) {
		path = filepath.Join(s.config.WorkDir, path)
	}

	content, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取文件失败: %w", err)
	}

	return map[string]interface{}{
		"success": true,
		"content": string(content),
		"path":    path,
	}, nil
}

// FileWriteSkill 文件写入技能
type FileWriteSkill struct {
	config SkillConfig
}

// NewFileWriteSkill 创建文件写入技能
func NewFileWriteSkill(cfg SkillConfig) *FileWriteSkill {
	return &FileWriteSkill{config: cfg}
}

// Name 技能名称
func (s *FileWriteSkill) Name() string {
	return "write_file"
}

// Description 技能描述
func (s *FileWriteSkill) Description() string {
	return "写入文件内容"
}

// Parameters 参数定义
func (s *FileWriteSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"path": map[string]interface{}{
				"type":        "string",
				"description": "文件路径",
			},
			"content": map[string]interface{}{
				"type":        "string",
				"description": "文件内容",
			},
		},
		"required": []string{"path", "content"},
	}
}

// Execute 执行写入
func (s *FileWriteSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Path    string `json:"path"`
		Content string `json:"content"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	// 处理相对路径
	path := params.Path
	if !filepath.IsAbs(path) {
		path = filepath.Join(s.config.WorkDir, path)
	}

	// 创建目录
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return nil, fmt.Errorf("创建目录失败: %w", err)
	}

	if err := os.WriteFile(path, []byte(params.Content), 0644); err != nil {
		return nil, fmt.Errorf("写入文件失败: %w", err)
	}

	return map[string]interface{}{
		"success": true,
		"path":    path,
	}, nil
}

// FileListSkill 文件列表技能
type FileListSkill struct {
	config SkillConfig
}

// NewFileListSkill 创建文件列表技能
func NewFileListSkill(cfg SkillConfig) *FileListSkill {
	return &FileListSkill{config: cfg}
}

// Name 技能名称
func (s *FileListSkill) Name() string {
	return "list_files"
}

// Description 技能描述
func (s *FileListSkill) Description() string {
	return "列出目录中的文件"
}

// Parameters 参数定义
func (s *FileListSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"path": map[string]interface{}{
				"type":        "string",
				"description": "目录路径",
			},
		},
		"required": []string{"path"},
	}
}

// Execute 执行列表
func (s *FileListSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Path string `json:"path"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	// 处理相对路径
	path := params.Path
	if !filepath.IsAbs(path) {
		path = filepath.Join(s.config.WorkDir, path)
	}

	entries, err := os.ReadDir(path)
	if err != nil {
		return nil, fmt.Errorf("读取目录失败: %w", err)
	}

	files := make([]map[string]interface{}, 0, len(entries))
	for _, entry := range entries {
		info, err := entry.Info()
		if err != nil {
			continue
		}
		files = append(files, map[string]interface{}{
			"name":     entry.Name(),
			"is_dir":   entry.IsDir(),
			"size":     info.Size(),
			"modified": info.ModTime().Format(time.RFC3339),
		})
	}

	return map[string]interface{}{
		"success": true,
		"path":    path,
		"files":   files,
	}, nil
}

// SystemInfoSkill 系统信息技能
type SystemInfoSkill struct{}

// NewSystemInfoSkill 创建系统信息技能
func NewSystemInfoSkill() *SystemInfoSkill {
	return &SystemInfoSkill{}
}

// Name 技能名称
func (s *SystemInfoSkill) Name() string {
	return "system_info"
}

// Description 技能描述
func (s *SystemInfoSkill) Description() string {
	return "获取系统信息"
}

// Parameters 参数定义
func (s *SystemInfoSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type":       "object",
		"properties": map[string]interface{}{},
	}
}

// Execute 执行获取系统信息
func (s *SystemInfoSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	hostname, _ := os.Hostname()
	cwd, _ := os.Getwd()

	return map[string]interface{}{
		"success":  true,
		"hostname": hostname,
		"cwd":      cwd,
		"os":       runtime.GOOS,
		"arch":     runtime.GOARCH,
	}, nil
}
