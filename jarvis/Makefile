.PHONY: build run clean test

# 构建项目
build:
	go build -o bin/jarvis ./cmd/jarvis

# 运行对话模式
run:
	go run ./cmd/jarvis chat

# 运行Web服务
serve:
	go run ./cmd/jarvis serve

# 运行语音模式
voice:
	go run ./cmd/jarvis voice

# 清理
clean:
	rm -rf bin/
	rm -rf logs/

# 测试
test:
	go test -v ./...

# 安装依赖
deps:
	go mod download
	go mod tidy

# 格式化代码
fmt:
	go fmt ./...

# 代码检查
lint:
	golangci-lint run
