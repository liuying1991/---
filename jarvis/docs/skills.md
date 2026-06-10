# 贾维斯技能模块文档

## 已实现的技能

### 文件操作技能

| 技能名称 | 描述 | 参数 |
|---------|------|------|
| `read_file` | 读取文件内容 | `path`: 文件路径 |
| `write_file` | 写入文件内容 | `path`: 文件路径, `content`: 内容 |
| `list_files` | 列出目录文件 | `path`: 目录路径 |

### 系统控制技能

| 技能名称 | 描述 | 参数 |
|---------|------|------|
| `execute_command` | 执行系统命令 | `command`: 命令, `args`: 参数列表 |
| `system_info` | 获取系统信息 | 无 |
| `process` | 进程管理 | `action`: list/start/stop/find, `name`: 进程名, `pid`: 进程ID |
| `disk_usage` | 查看磁盘使用 | 无 |
| `memory_usage` | 查看内存使用 | 无 |

### 网络技能

| 技能名称 | 描述 | 参数 |
|---------|------|------|
| `http_request` | 发送HTTP请求 | `url`: URL, `method`: GET/POST, `headers`: 请求头, `body`: 请求体 |
| `web_search` | 网络搜索 | `query`: 搜索词, `count`: 结果数量 |

### 工具技能

| 技能名称 | 描述 | 参数 |
|---------|------|------|
| `calculate` | 数学计算 | `expression`: 表达式 |
| `datetime` | 获取日期时间 | `format`: 格式 |
| `schedule` | 定时任务管理 | `action`: list/add/remove/run, `name`: 任务名, `command`: 命令, `interval`: 间隔(秒) |

## 使用示例

### 读取文件
```json
{
  "name": "read_file",
  "arguments": {"path": "/home/user/example.txt"}
}
```

### 执行命令
```json
{
  "name": "execute_command",
  "arguments": {"command": "ls", "args": ["-la"]}
}
```

### HTTP请求
```json
{
  "name": "http_request",
  "arguments": {
    "url": "https://api.example.com/data",
    "method": "GET"
  }
}
```

### 数学计算
```json
{
  "name": "calculate",
  "arguments": {"expression": "2+3*4"}
}
```

### 进程管理
```json
{
  "name": "process",
  "arguments": {"action": "find", "name": "nginx"}
}
```

### 定时任务
```json
{
  "name": "schedule",
  "arguments": {
    "action": "add",
    "name": "backup",
    "command": "tar -czf /backup/data.tar.gz /data",
    "interval": 3600
  }
}
```

## 扩展技能

要添加新技能，实现 `Skill` 接口：

```go
type MySkill struct{}

func (s *MySkill) Name() string {
    return "my_skill"
}

func (s *MySkill) Description() string {
    return "我的自定义技能"
}

func (s *MySkill) Parameters() map[string]interface{} {
    return map[string]interface{}{
        "type": "object",
        "properties": map[string]interface{}{
            "param1": map[string]interface{}{
                "type": "string",
                "description": "参数说明",
            },
        },
        "required": []string{"param1"},
    }
}

func (s *MySkill) Execute(ctx context.Context, args json.RawMessage) (interface{}, error) {
    // 实现技能逻辑
    return map[string]interface{}{"success": true}, nil
}
```

然后在 `registry.go` 中注册：
```go
registry.Register(&MySkill{})
```
