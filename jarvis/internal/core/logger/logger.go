package logger

import (
	"os"
	"sync"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

var globalLogger *zap.Logger
var globalSugar *zap.SugaredLogger
var once sync.Once

// Config 日志配置
type Config struct {
	Level   string
	File    string
	Console bool
}

// Init 初始化日志
func Init(cfg Config) error {
	var err error
	once.Do(func() {
		// 解析日志级别
		var level zapcore.Level
		if err = level.UnmarshalText([]byte(cfg.Level)); err != nil {
			level = zapcore.InfoLevel
			err = nil
		}

		// 编码器配置
		encoderConfig := zapcore.EncoderConfig{
			TimeKey:        "time",
			LevelKey:       "level",
			NameKey:        "logger",
			CallerKey:      "caller",
			FunctionKey:    zapcore.OmitKey,
			MessageKey:     "msg",
			StacktraceKey:  "stacktrace",
			LineEnding:     zapcore.DefaultLineEnding,
			EncodeLevel:    zapcore.CapitalLevelEncoder,
			EncodeTime:     zapcore.ISO8601TimeEncoder,
			EncodeDuration: zapcore.SecondsDurationEncoder,
			EncodeCaller:   zapcore.ShortCallerEncoder,
		}

		// 构建cores
		var cores []zapcore.Core

		// 控制台输出
		if cfg.Console {
			consoleEncoder := zapcore.NewConsoleEncoder(encoderConfig)
			consoleCore := zapcore.NewCore(
				consoleEncoder,
				zapcore.AddSync(os.Stdout),
				level,
			)
			cores = append(cores, consoleCore)
		}

		// 文件输出
		if cfg.File != "" {
			fileEncoder := zapcore.NewJSONEncoder(encoderConfig)
			var file *os.File
			file, err = os.OpenFile(cfg.File, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
			if err != nil {
				return
			}
			fileCore := zapcore.NewCore(
				fileEncoder,
				zapcore.AddSync(file),
				level,
			)
			cores = append(cores, fileCore)
		}

		// 创建logger
		if len(cores) == 0 {
			globalLogger = zap.NewNop()
		} else {
			core := zapcore.NewTee(cores...)
			globalLogger = zap.New(core, zap.AddCaller(), zap.AddCallerSkip(1))
		}
		globalSugar = globalLogger.Sugar()
	})
	return err
}

// L 获取原始logger
func L() *zap.Logger {
	if globalLogger == nil {
		return zap.NewNop()
	}
	return globalLogger
}

// S 获取SugaredLogger
func S() *zap.SugaredLogger {
	if globalSugar == nil {
		return zap.NewNop().Sugar()
	}
	return globalSugar
}

// Debug 调试日志
func Debug(msg string, fields ...zap.Field) {
	L().Debug(msg, fields...)
}

// Info 信息日志
func Info(msg string, fields ...zap.Field) {
	L().Info(msg, fields...)
}

// Warn 警告日志
func Warn(msg string, fields ...zap.Field) {
	L().Warn(msg, fields...)
}

// Error 错误日志
func Error(msg string, fields ...zap.Field) {
	L().Error(msg, fields...)
}

// Fatal 致命错误日志
func Fatal(msg string, fields ...zap.Field) {
	L().Fatal(msg, fields...)
}

// Debugf 格式化调试日志
func Debugf(template string, args ...interface{}) {
	S().Debugf(template, args...)
}

// Infof 格式化信息日志
func Infof(template string, args ...interface{}) {
	S().Infof(template, args...)
}

// Warnf 格式化警告日志
func Warnf(template string, args ...interface{}) {
	S().Warnf(template, args...)
}

// Errorf 格式化错误日志
func Errorf(template string, args ...interface{}) {
	S().Errorf(template, args...)
}

// Fatalf 格式化致命错误日志
func Fatalf(template string, args ...interface{}) {
	S().Fatalf(template, args...)
}

// Sync 同步日志
func Sync() error {
	if globalLogger != nil {
		return globalLogger.Sync()
	}
	return nil
}
