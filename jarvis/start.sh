#!/bin/bash

# 贾维斯快速启动脚本

echo "╔═══════════════════════════════════════╗"
echo "║     贾维斯 JARVIS - 智能AI助手       ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# 检查Go是否安装
if ! command -v go &> /dev/null; then
    echo "错误: Go未安装，请先安装Go"
    exit 1
fi

# 下载依赖
echo "正在下载依赖..."
go mod download
go mod tidy

# 构建项目
echo "正在构建项目..."
go build -o bin/jarvis ./cmd/jarvis

if [ $? -eq 0 ]; then
    echo "构建成功!"
    echo ""
    echo "使用方法:"
    echo "  ./bin/jarvis chat   - 启动对话模式"
    echo "  ./bin/jarvis serve  - 启动Web服务"
    echo "  ./bin/jarvis voice  - 启动语音模式"
    echo ""
    read -p "是否立即启动对话模式? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./bin/jarvis chat
    fi
else
    echo "构建失败，请检查错误信息"
    exit 1
fi
