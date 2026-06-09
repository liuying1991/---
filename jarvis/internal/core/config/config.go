package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

// Config 主配置结构
type Config struct {
	LLM    LLMConfig    `mapstructure:"llm"`
	Voice  VoiceConfig  `mapstructure:"voice"`
	System SystemConfig `mapstructure:"system"`
	Web    WebConfig    `mapstructure:"web"`
	Log    LogConfig    `mapstructure:"log"`
	Dialog DialogConfig `mapstructure:"dialog"`
}

// LLMConfig 大模型配置
type LLMConfig struct {
	Backend       string  `mapstructure:"backend"`
	ModelPath     string  `mapstructure:"model_path"`
	APIBase       string  `mapstructure:"api_base"`
	ContextLength int     `mapstructure:"context_length"`
	Temperature   float64 `mapstructure:"temperature"`
	MaxTokens     int     `mapstructure:"max_tokens"`
}

// VoiceConfig 语音配置
type VoiceConfig struct {
	Enabled       bool   `mapstructure:"enabled"`
	STTBackend    string `mapstructure:"stt_backend"`
	TTSBackend    string `mapstructure:"tts_backend"`
	WhisperModel  string `mapstructure:"whisper_model"`
	PiperModel    string `mapstructure:"piper_model"`
	WakeWord      string `mapstructure:"wake_word"`
}

// SystemConfig 系统控制配置
type SystemConfig struct {
	Enabled          bool     `mapstructure:"enabled"`
	CommandWhitelist []string `mapstructure:"command_whitelist"`
	CommandBlacklist []string `mapstructure:"command_blacklist"`
	ConfirmDangerous bool     `mapstructure:"confirm_dangerous"`
	WorkDir          string   `mapstructure:"work_dir"`
}

// WebConfig Web服务配置
type WebConfig struct {
	Host       string `mapstructure:"host"`
	Port       int    `mapstructure:"port"`
	WebSocket  bool   `mapstructure:"websocket"`
	StaticDir  string `mapstructure:"static_dir"`
}

// LogConfig 日志配置
type LogConfig struct {
	Level      string `mapstructure:"level"`
	File       string `mapstructure:"file"`
	Console    bool   `mapstructure:"console"`
	MaxSize    int    `mapstructure:"max_size"`
	MaxBackups int    `mapstructure:"max_backups"`
	MaxAge     int    `mapstructure:"max_age"`
}

// DialogConfig 对话配置
type DialogConfig struct {
	SystemPrompt  string `mapstructure:"system_prompt"`
	HistoryLength int    `mapstructure:"history_length"`
	Stream        bool   `mapstructure:"stream"`
}

var globalConfig *Config

// Load 加载配置
func Load(configPath string) (*Config, error) {
	if configPath == "" {
		// 默认配置路径
		configPath = "./configs/config.yaml"
	}

	v := viper.New()
	v.SetConfigFile(configPath)

	// 设置默认值
	setDefaults(v)

	// 读取配置文件
	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("解析配置失败: %w", err)
	}

	// 处理相对路径
	if err := resolvePaths(&cfg, filepath.Dir(configPath)); err != nil {
		return nil, err
	}

	globalConfig = &cfg
	return &cfg, nil
}

// Get 获取全局配置
func Get() *Config {
	if globalConfig == nil {
		panic("配置未初始化，请先调用 config.Load()")
	}
	return globalConfig
}

// setDefaults 设置默认值
func setDefaults(v *viper.Viper) {
	v.SetDefault("llm.backend", "llama_cpp")
	v.SetDefault("llm.context_length", 4096)
	v.SetDefault("llm.temperature", 0.7)
	v.SetDefault("llm.max_tokens", 2048)

	v.SetDefault("voice.enabled", false)
	v.SetDefault("voice.stt_backend", "whisper_local")
	v.SetDefault("voice.tts_backend", "piper")
	v.SetDefault("voice.wake_word", "贾维斯")

	v.SetDefault("system.enabled", true)
	v.SetDefault("system.confirm_dangerous", true)
	v.SetDefault("system.work_dir", "/tmp")

	v.SetDefault("web.host", "0.0.0.0")
	v.SetDefault("web.port", 8080)
	v.SetDefault("web.websocket", true)

	v.SetDefault("log.level", "info")
	v.SetDefault("log.console", true)
	v.SetDefault("log.max_size", 100)
	v.SetDefault("log.max_backups", 5)
	v.SetDefault("log.max_age", 30)

	v.SetDefault("dialog.history_length", 20)
	v.SetDefault("dialog.stream", true)
}

// resolvePaths 解析相对路径为绝对路径
func resolvePaths(cfg *Config, baseDir string) error {
	var err error

	if cfg.LLM.ModelPath != "" && !filepath.IsAbs(cfg.LLM.ModelPath) {
		cfg.LLM.ModelPath = filepath.Join(baseDir, cfg.LLM.ModelPath)
	}

	if cfg.Voice.WhisperModel != "" && !filepath.IsAbs(cfg.Voice.WhisperModel) {
		cfg.Voice.WhisperModel = filepath.Join(baseDir, cfg.Voice.WhisperModel)
	}

	if cfg.Voice.PiperModel != "" && !filepath.IsAbs(cfg.Voice.PiperModel) {
		cfg.Voice.PiperModel = filepath.Join(baseDir, cfg.Voice.PiperModel)
	}

	if cfg.Log.File != "" && !filepath.IsAbs(cfg.Log.File) {
		cfg.Log.File = filepath.Join(baseDir, cfg.Log.File)
		// 创建日志目录
		logDir := filepath.Dir(cfg.Log.File)
		if err = os.MkdirAll(logDir, 0755); err != nil {
			return fmt.Errorf("创建日志目录失败: %w", err)
		}
	}

	if cfg.Web.StaticDir != "" && !filepath.IsAbs(cfg.Web.StaticDir) {
		cfg.Web.StaticDir = filepath.Join(baseDir, cfg.Web.StaticDir)
	}

	return nil
}
