package config

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// Config 主配置结构
type Config struct {
	LLM    LLMConfig    `yaml:"llm"`
	Voice  VoiceConfig  `yaml:"voice"`
	System SystemConfig `yaml:"system"`
	Web    WebConfig    `yaml:"web"`
	Log    LogConfig    `yaml:"log"`
	Dialog DialogConfig `yaml:"dialog"`
}

// LLMConfig 大模型配置
type LLMConfig struct {
	Backend       string  `yaml:"backend"`
	ModelPath     string  `yaml:"model_path"`
	APIBase       string  `yaml:"api_base"`
	ContextLength int     `yaml:"context_length"`
	Temperature   float64 `yaml:"temperature"`
	MaxTokens     int     `yaml:"max_tokens"`
}

// VoiceConfig 语音配置
type VoiceConfig struct {
	Enabled      bool   `yaml:"enabled"`
	STTBackend   string `yaml:"stt_backend"`
	TTSBackend   string `yaml:"tts_backend"`
	WhisperModel string `yaml:"whisper_model"`
	PiperModel   string `yaml:"piper_model"`
	WakeWord     string `yaml:"wake_word"`
}

// SystemConfig 系统控制配置
type SystemConfig struct {
	Enabled          bool     `yaml:"enabled"`
	CommandWhitelist []string `yaml:"command_whitelist"`
	CommandBlacklist []string `yaml:"command_blacklist"`
	ConfirmDangerous bool     `yaml:"confirm_dangerous"`
	WorkDir          string   `yaml:"work_dir"`
}

// WebConfig Web服务配置
type WebConfig struct {
	Host      string `yaml:"host"`
	Port      int    `yaml:"port"`
	WebSocket bool   `yaml:"websocket"`
	StaticDir string `yaml:"static_dir"`
}

// LogConfig 日志配置
type LogConfig struct {
	Level      string `yaml:"level"`
	File       string `yaml:"file"`
	Console    bool   `yaml:"console"`
	MaxSize    int    `yaml:"max_size"`
	MaxBackups int    `yaml:"max_backups"`
	MaxAge     int    `yaml:"max_age"`
}

// DialogConfig 对话配置
type DialogConfig struct {
	SystemPrompt  string `yaml:"system_prompt"`
	HistoryLength int    `yaml:"history_length"`
	Stream        bool   `yaml:"stream"`
}

var globalConfig *Config

// Load 加载配置
func Load(configPath string) (*Config, error) {
	if configPath == "" {
		configPath = "./configs/config.yaml"
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	cfg := &Config{}
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("解析配置失败: %w", err)
	}

	// 设置默认值
	setDefaults(cfg)

	// 处理相对路径
	if err := resolvePaths(cfg, filepath.Dir(configPath)); err != nil {
		return nil, err
	}

	globalConfig = cfg
	return cfg, nil
}

// Get 获取全局配置
func Get() *Config {
	if globalConfig == nil {
		panic("配置未初始化，请先调用 config.Load()")
	}
	return globalConfig
}

// setDefaults 设置默认值
func setDefaults(cfg *Config) {
	if cfg.LLM.Backend == "" {
		cfg.LLM.Backend = "llama_cpp"
	}
	if cfg.LLM.ContextLength == 0 {
		cfg.LLM.ContextLength = 4096
	}
	if cfg.LLM.Temperature == 0 {
		cfg.LLM.Temperature = 0.7
	}
	if cfg.LLM.MaxTokens == 0 {
		cfg.LLM.MaxTokens = 2048
	}

	if cfg.Voice.STTBackend == "" {
		cfg.Voice.STTBackend = "whisper_local"
	}
	if cfg.Voice.TTSBackend == "" {
		cfg.Voice.TTSBackend = "piper"
	}
	if cfg.Voice.WakeWord == "" {
		cfg.Voice.WakeWord = "贾维斯"
	}

	if cfg.System.WorkDir == "" {
		cfg.System.WorkDir = "/tmp"
	}

	if cfg.Web.Host == "" {
		cfg.Web.Host = "0.0.0.0"
	}
	if cfg.Web.Port == 0 {
		cfg.Web.Port = 8080
	}

	if cfg.Log.Level == "" {
		cfg.Log.Level = "info"
	}
	if cfg.Log.MaxSize == 0 {
		cfg.Log.MaxSize = 100
	}
	if cfg.Log.MaxBackups == 0 {
		cfg.Log.MaxBackups = 5
	}
	if cfg.Log.MaxAge == 0 {
		cfg.Log.MaxAge = 30
	}

	if cfg.Dialog.HistoryLength == 0 {
		cfg.Dialog.HistoryLength = 20
	}
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
