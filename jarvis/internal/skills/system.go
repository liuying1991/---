package skills

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

// ProcessSkill 进程管理技能
type ProcessSkill struct{}

// NewProcessSkill 创建进程管理技能
func NewProcessSkill() *ProcessSkill {
	return &ProcessSkill{}
}

// Name 技能名称
func (s *ProcessSkill) Name() string {
	return "process"
}

// Description 技能描述
func (s *ProcessSkill) Description() string {
	return "管理进程：启动、停止、查看状态"
}

// Parameters 参数定义
func (s *ProcessSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"action": map[string]interface{}{
				"type":        "string",
				"description": "操作类型",
				"enum":        []string{"list", "start", "stop", "find"},
			},
			"name": map[string]interface{}{
				"type":        "string",
				"description": "进程名称",
			},
			"pid": map[string]interface{}{
				"type":        "integer",
				"description": "进程ID",
			},
		},
		"required": []string{"action"},
	}
}

// Execute 执行进程操作
func (s *ProcessSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Action string `json:"action"`
		Name   string `json:"name"`
		Pid    int    `json:"pid"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	switch params.Action {
	case "list":
		return s.listProcesses()
	case "find":
		if params.Name == "" {
			return nil, fmt.Errorf("需要指定进程名称")
		}
		return s.findProcess(params.Name)
	case "stop":
		if params.Pid == 0 {
			return nil, fmt.Errorf("需要指定进程ID")
		}
		return s.stopProcess(params.Pid)
	default:
		return nil, fmt.Errorf("不支持的操作: %s", params.Action)
	}
}

// listProcesses 列出进程
func (s *ProcessSkill) listProcesses() (interface{}, error) {
	// 使用ps命令列出进程
	cmd := exec.Command("ps", "aux")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("获取进程列表失败: %w", err)
	}

	// 解析输出
	lines := strings.Split(string(output), "\n")
	processes := make([]map[string]string, 0)

	for i, line := range lines {
		if i == 0 || line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) >= 11 {
			processes = append(processes, map[string]string{
				"user":    fields[0],
				"pid":     fields[1],
				"cpu":     fields[2],
				"mem":     fields[3],
				"command": strings.Join(fields[10:], " "),
			})
		}
	}

	return map[string]interface{}{
		"success":   true,
		"processes": processes[:min(20, len(processes))], // 最多返回20个
		"total":     len(processes),
	}, nil
}

// findProcess 查找进程
func (s *ProcessSkill) findProcess(name string) (interface{}, error) {
	cmd := exec.Command("pgrep", "-l", name)
	output, err := cmd.Output()
	if err != nil {
		return map[string]interface{}{
			"success": true,
			"found":   false,
			"message": "未找到匹配的进程",
		}, nil
	}

	lines := strings.Split(strings.TrimSpace(string(output)), "\n")
	processes := make([]map[string]string, 0)

	for _, line := range lines {
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) >= 2 {
			processes = append(processes, map[string]string{
				"pid":   fields[0],
				"name":  fields[1],
			})
		}
	}

	return map[string]interface{}{
		"success":   true,
		"found":     len(processes) > 0,
		"processes": processes,
	}, nil
}

// stopProcess 停止进程
func (s *ProcessSkill) stopProcess(pid int) (interface{}, error) {
	process, err := os.FindProcess(pid)
	if err != nil {
		return nil, fmt.Errorf("查找进程失败: %w", err)
	}

	if err := process.Signal(os.Interrupt); err != nil {
		return nil, fmt.Errorf("停止进程失败: %w", err)
	}

	return map[string]interface{}{
		"success": true,
		"message": fmt.Sprintf("已发送停止信号到进程 %d", pid),
		"pid":     pid,
	}, nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// DiskUsageSkill 磁盘使用技能
type DiskUsageSkill struct{}

// NewDiskUsageSkill 创建磁盘使用技能
func NewDiskUsageSkill() *DiskUsageSkill {
	return &DiskUsageSkill{}
}

// Name 技能名称
func (s *DiskUsageSkill) Name() string {
	return "disk_usage"
}

// Description 技能描述
func (s *DiskUsageSkill) Description() string {
	return "查看磁盘使用情况"
}

// Parameters 参数定义
func (s *DiskUsageSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type":       "object",
		"properties": map[string]interface{}{},
	}
}

// Execute 执行查看磁盘
func (s *DiskUsageSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	cmd := exec.Command("df", "-h")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("获取磁盘信息失败: %w", err)
	}

	lines := strings.Split(string(output), "\n")
	disks := make([]map[string]string, 0)

	for i, line := range lines {
		if i == 0 || line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) >= 6 {
			disks = append(disks, map[string]string{
				"filesystem": fields[0],
				"size":       fields[1],
				"used":       fields[2],
				"available":  fields[3],
				"use_percent": fields[4],
				"mountpoint": fields[5],
			})
		}
	}

	return map[string]interface{}{
		"success": true,
		"disks":   disks,
	}, nil
}

// MemoryUsageSkill 内存使用技能
type MemoryUsageSkill struct{}

// NewMemoryUsageSkill 创建内存使用技能
func NewMemoryUsageSkill() *MemoryUsageSkill {
	return &MemoryUsageSkill{}
}

// Name 技能名称
func (s *MemoryUsageSkill) Name() string {
	return "memory_usage"
}

// Description 技能描述
func (s *MemoryUsageSkill) Description() string {
	return "查看内存使用情况"
}

// Parameters 参数定义
func (s *MemoryUsageSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type":       "object",
		"properties": map[string]interface{}{},
	}
}

// Execute 执行查看内存
func (s *MemoryUsageSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	// 读取/proc/meminfo
	data, err := os.ReadFile("/proc/meminfo")
	if err != nil {
		return nil, fmt.Errorf("读取内存信息失败: %w", err)
	}

	memInfo := make(map[string]string)
	lines := strings.Split(string(data), "\n")

	for _, line := range lines {
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) >= 2 {
			key := strings.TrimSuffix(fields[0], ":")
			memInfo[key] = fields[1]
		}
	}

	return map[string]interface{}{
		"success":  true,
		"meminfo":  memInfo,
	}, nil
}

// ScheduleTaskSkill 定时任务技能
type ScheduleTaskSkill struct {
	tasks map[string]*scheduledTask
}

type scheduledTask struct {
	Name     string
	Command  string
	Interval time.Duration
	NextRun  time.Time
	Active   bool
}

// NewScheduleTaskSkill 创建定时任务技能
func NewScheduleTaskSkill() *ScheduleTaskSkill {
	return &ScheduleTaskSkill{
		tasks: make(map[string]*scheduledTask),
	}
}

// Name 技能名称
func (s *ScheduleTaskSkill) Name() string {
	return "schedule"
}

// Description 技能描述
func (s *ScheduleTaskSkill) Description() string {
	return "管理定时任务"
}

// Parameters 参数定义
func (s *ScheduleTaskSkill) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"action": map[string]interface{}{
				"type":        "string",
				"description": "操作类型",
				"enum":        []string{"list", "add", "remove", "run"},
			},
			"name": map[string]interface{}{
				"type":        "string",
				"description": "任务名称",
			},
			"command": map[string]interface{}{
				"type":        "string",
				"description": "要执行的命令",
			},
			"interval": map[string]interface{}{
				"type":        "integer",
				"description": "执行间隔(秒)",
			},
		},
		"required": []string{"action"},
	}
}

// Execute 执行定时任务操作
func (s *ScheduleTaskSkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
	var params struct {
		Action   string `json:"action"`
		Name     string `json:"name"`
		Command  string `json:"command"`
		Interval int    `json:"interval"`
	}
	if err := json.Unmarshal(args, &params); err != nil {
		return nil, fmt.Errorf("解析参数失败: %w", err)
	}

	switch params.Action {
	case "list":
		tasks := make([]map[string]interface{}, 0)
		for name, task := range s.tasks {
			tasks = append(tasks, map[string]interface{}{
				"name":     name,
				"command":  task.Command,
				"interval": task.Interval.Seconds(),
				"next_run": task.NextRun.Format(time.RFC3339),
				"active":   task.Active,
			})
		}
		return map[string]interface{}{
			"success": true,
			"tasks":   tasks,
		}, nil

	case "add":
		if params.Name == "" || params.Command == "" || params.Interval == 0 {
			return nil, fmt.Errorf("需要指定任务名称、命令和间隔")
		}
		s.tasks[params.Name] = &scheduledTask{
			Name:     params.Name,
			Command:  params.Command,
			Interval: time.Duration(params.Interval) * time.Second,
			NextRun:  time.Now().Add(time.Duration(params.Interval) * time.Second),
			Active:   true,
		}
		return map[string]interface{}{
			"success": true,
			"message": fmt.Sprintf("已添加定时任务: %s", params.Name),
		}, nil

	case "remove":
		if params.Name == "" {
			return nil, fmt.Errorf("需要指定任务名称")
		}
		delete(s.tasks, params.Name)
		return map[string]interface{}{
			"success": true,
			"message": fmt.Sprintf("已删除定时任务: %s", params.Name),
		}, nil

	case "run":
		if params.Name == "" {
			return nil, fmt.Errorf("需要指定任务名称")
		}
		task, ok := s.tasks[params.Name]
		if !ok {
			return nil, fmt.Errorf("任务不存在: %s", params.Name)
		}
		// 立即执行
		cmd := exec.Command("sh", "-c", task.Command)
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

	default:
		return nil, fmt.Errorf("不支持的操作: %s", params.Action)
	}
}
