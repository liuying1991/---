# 贾维斯 JARVIS - 智能AI助手

一个基于本地大模型的智能AI助手，具备系统控制、语音交互、多模态能力。

## 特性

- 🧠 **本地LLM支持** - 支持vLLM/llama.cpp本地部署
- 🎙️ **语音交互** - 语音识别(STT)和语音合成(TTS)
- 💬 **多接口支持** - CLI、Web界面、WebSocket
- ⚡ **系统控制** - 命令执行、文件管理、进程监控
- 🔌 **插件系统** - 可扩展的技能模块
- 🔒 **安全沙箱** - 命令执行安全控制

## 技能模块

| 类别 | 技能 |
|------|------|
| 文件操作 | `read_file`, `write_file`, `list_files` |
| 系统控制 | `execute_command`, `system_info`, `process`, `disk_usage`, `memory_usage` |
| 网络工具 | `http_request`, `web_search` |
| 实用工具 | `calculate`, `datetime`, `schedule` |

## 快速开始

```bash
# 安装依赖
go mod tidy

# 构建项目
go build -o bin/jarvis ./cmd/jarvis

# 启动CLI模式
./bin/jarvis chat

# 启动Web服务
./bin/jarvis serve

# 启动语音模式
./bin/jarvis voice
```

## 配置

配置文件位于 `configs/config.yaml`，支持：

- LLM模型配置（vLLM/llama.cpp）
- 语音服务配置（Whisper/Piper）
- 系统控制权限（命令黑白名单）
- Web服务配置
- 日志级别设置

## 架构

```
jarvis/
├── cmd/jarvis/          # 命令行入口
├── internal/
│   ├── core/            # 核心模块（配置、日志）
│   ├── llm/             # LLM引擎接口
│   ├── dialog/          # 对话管理
│   ├── skills/          # 技能模块
│   │   ├── registry.go  # 技能注册
│   │   ├── extended.go  # 扩展技能
│   │   └── system.go    # 系统技能
│   └── web/             # Web服务
├── configs/             # 配置文件
└── docs/                # 文档
```

## 使用示例

### CLI模式
```
你: 帮我查看当前目录的文件
贾维斯: [调用 list_files 技能]
...
```

### Web模式
访问 http://localhost:8080 使用Web界面

### API调用
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "查看系统信息"}'
```

## License

MIT
