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
# 构建项目
go build -o jarvis ./cmd/jarvis

# 启动CLI模式
./jarvis chat

# 启动Web服务
./jarvis serve --port 8080

# 启动语音模式
./jarvis voice
```

## 配置

配置文件位于 `config/config.yaml`，支持：

- LLM模型配置
- 语音服务配置
- 系统控制权限
- 日志级别设置

## 架构

```
jarvis/
├── cmd/jarvis/       # 命令行入口
├── internal/
│   ├── core/         # 核心模块（配置、日志）
│   ├── llm/          # LLM引擎接口
│   ├── dialog/       # 对话管理
│   ├── skills/       # 技能模块
│   ├── voice/        # 语音处理
│   └── web/          # Web服务
├── pkg/              # 公共工具库
└── configs/          # 配置文件
```

## License

MIT
