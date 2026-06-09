package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"jarvis/internal/core/config"
	"jarvis/internal/core/logger"
	"jarvis/internal/dialog"
	"jarvis/internal/llm"
	"jarvis/internal/skills"
	"jarvis/internal/web"

	"github.com/spf13/cobra"
)

var (
	configPath string
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "jarvis",
		Short: "贾维斯 - 智能AI助手",
		Long:  `贾维斯(JARVIS)是一个基于本地大模型的智能AI助手`,
	}

	rootCmd.PersistentFlags().StringVarP(&configPath, "config", "c", "", "配置文件路径")

	// chat命令
	chatCmd := &cobra.Command{
		Use:   "chat",
		Short: "启动对话模式",
		Run:   runChat,
	}
	rootCmd.AddCommand(chatCmd)

	// serve命令
	serveCmd := &cobra.Command{
		Use:   "serve",
		Short: "启动Web服务",
		Run:   runServe,
	}
	rootCmd.AddCommand(serveCmd)

	// voice命令
	voiceCmd := &cobra.Command{
		Use:   "voice",
		Short: "启动语音模式",
		Run:   runVoice,
	}
	rootCmd.AddCommand(voiceCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runChat(cmd *cobra.Command, args []string) {
	// 加载配置
	cfg, err := config.Load(configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	// 初始化日志
	if err := logger.Init(logger.Config{
		Level:   cfg.Log.Level,
		File:    cfg.Log.File,
		Console: cfg.Log.Console,
	}); err != nil {
		fmt.Fprintf(os.Stderr, "初始化日志失败: %v\n", err)
		os.Exit(1)
	}
	defer logger.Sync()

	logger.Info("贾维斯启动 - 对话模式")

	// 创建LLM引擎
	engine, err := llm.NewEngine(cfg.LLM.Backend, cfg.LLM.APIBase, cfg.LLM.ModelPath)
	if err != nil {
		logger.Fatalf("创建LLM引擎失败: %v", err)
	}
	defer engine.Close()

	// 创建技能注册表
	registry := skills.NewSkillRegistry(skills.SkillConfig{
		Enabled:          cfg.System.Enabled,
		CommandWhitelist: cfg.System.CommandWhitelist,
		CommandBlacklist: cfg.System.CommandBlacklist,
		ConfirmDangerous: cfg.System.ConfirmDangerous,
		WorkDir:          cfg.System.WorkDir,
	})

	// 创建对话管理器
	dialogManager := dialog.NewManager(
		engine,
		registry,
		cfg.Dialog.SystemPrompt,
		cfg.Dialog.HistoryLength,
		cfg.Dialog.Stream,
	)

	// 打印欢迎信息
	fmt.Println("\n╔═══════════════════════════════════════╗")
	fmt.Println("║     贾维斯 JARVIS - 智能AI助手       ║")
	fmt.Println("╚═══════════════════════════════════════╝")
	fmt.Println("\n输入消息开始对话，输入 'quit' 或 'exit' 退出")
	fmt.Println("输入 'clear' 清空对话历史")
	fmt.Println()

	// 设置信号处理
	ctx, cancel := context.WithCancel(context.Background())
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		fmt.Println("\n正在退出...")
		cancel()
	}()

	// 读取输入
	reader := bufio.NewReader(os.Stdin)
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		fmt.Print("你: ")
		input, err := reader.ReadString('\n')
		if err != nil {
			break
		}

		// 去除换行符
		input = input[:len(input)-1]
		if input == "" {
			continue
		}

		// 处理命令
		switch input {
		case "quit", "exit":
			fmt.Println("\n再见!")
			return
		case "clear":
			dialogManager.ClearHistory()
			fmt.Println("对话历史已清空\n")
			continue
		}

		// 发送消息
		fmt.Print("\n贾维斯: ")
		response, err := dialogManager.Chat(ctx, input)
		if err != nil {
			fmt.Printf("错误: %v\n\n", err)
			continue
		}

		fmt.Printf("%s\n\n", response)
	}
}

func runServe(cmd *cobra.Command, args []string) {
	// 加载配置
	cfg, err := config.Load(configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	// 初始化日志
	if err := logger.Init(logger.Config{
		Level:   cfg.Log.Level,
		File:    cfg.Log.File,
		Console: cfg.Log.Console,
	}); err != nil {
		fmt.Fprintf(os.Stderr, "初始化日志失败: %v\n", err)
		os.Exit(1)
	}
	defer logger.Sync()

	logger.Info("贾维斯启动 - Web服务模式")

	// 创建LLM引擎
	engine, err := llm.NewEngine(cfg.LLM.Backend, cfg.LLM.APIBase, cfg.LLM.ModelPath)
	if err != nil {
		logger.Fatalf("创建LLM引擎失败: %v", err)
	}
	defer engine.Close()

	// 创建技能注册表
	registry := skills.NewSkillRegistry(skills.SkillConfig{
		Enabled:          cfg.System.Enabled,
		CommandWhitelist: cfg.System.CommandWhitelist,
		CommandBlacklist: cfg.System.CommandBlacklist,
		ConfirmDangerous: cfg.System.ConfirmDangerous,
		WorkDir:          cfg.System.WorkDir,
	})

	// 创建对话管理器
	dialogManager := dialog.NewManager(
		engine,
		registry,
		cfg.Dialog.SystemPrompt,
		cfg.Dialog.HistoryLength,
		cfg.Dialog.Stream,
	)

	// 创建Web服务器
	server := web.NewServer(cfg.Web.Host, cfg.Web.Port, dialogManager)

	// 设置信号处理
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigChan
		logger.Info("正在关闭服务器...")
		server.Stop(context.Background())
	}()

	// 启动服务器
	if err := server.Start(); err != nil {
		logger.Fatalf("服务器错误: %v", err)
	}
}

func runVoice(cmd *cobra.Command, args []string) {
	// TODO: 实现语音模式
	fmt.Println("语音模式功能开发中...")
}
