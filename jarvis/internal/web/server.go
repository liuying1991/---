package web

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"jarvis/internal/core/logger"

	"github.com/gorilla/websocket"
)

// Server Web服务器
type Server struct {
	host       string
	port       int
	server     *http.Server
	upgrader   websocket.Upgrader
	clients    map[*websocket.Conn]bool
	clientsMux sync.RWMutex
	handler    MessageHandler
}

// MessageHandler 消息处理接口
type MessageHandler interface {
	HandleMessage(ctx context.Context, message string) (string, error)
}

// NewServer 创建Web服务器
func NewServer(host string, port int, handler MessageHandler) *Server {
	return &Server{
		host:    host,
		port:    port,
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true
			},
		},
		clients: make(map[*websocket.Conn]bool),
		handler: handler,
	}
}

// Start 启动服务器
func (s *Server) Start() error {
	mux := http.NewServeMux()

	// 静态文件
	mux.HandleFunc("/", s.handleIndex)

	// API端点
	mux.HandleFunc("/api/chat", s.handleChat)
	mux.HandleFunc("/api/skills", s.handleSkills)

	// WebSocket
	mux.HandleFunc("/ws", s.handleWebSocket)

	s.server = &http.Server{
		Addr:    fmt.Sprintf("%s:%d", s.host, s.port),
		Handler: mux,
	}

	logger.Infof("Web服务器启动: http://%s:%d", s.host, s.port)
	return s.server.ListenAndServe()
}

// Stop 停止服务器
func (s *Server) Stop(ctx context.Context) error {
	// 关闭所有WebSocket连接
	s.clientsMux.Lock()
	for client := range s.clients {
		client.Close()
	}
	s.clientsMux.Unlock()

	return s.server.Shutdown(ctx)
}

// handleIndex 处理首页
func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write([]byte(indexHTML))
}

// handleChat 处理聊天API
func (s *Server) handleChat(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Message string `json:"message"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	ctx := r.Context()
	response, err := s.handler.HandleMessage(ctx, req.Message)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(map[string]string{
		"response": response,
	})
}

// handleSkills 处理技能列表API
func (s *Server) handleSkills(w http.ResponseWriter, r *http.Request) {
	// TODO: 返回技能列表
	json.NewEncoder(w).Encode(map[string]interface{}{
		"skills": []string{
			"execute_command",
			"read_file",
			"write_file",
			"list_files",
			"system_info",
			"http_request",
			"calculate",
			"web_search",
			"datetime",
			"process",
			"disk_usage",
			"memory_usage",
			"schedule",
		},
	})
}

// handleWebSocket 处理WebSocket连接
func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		logger.Errorf("WebSocket升级失败: %v", err)
		return
	}
	defer conn.Close()

	// 注册客户端
	s.clientsMux.Lock()
	s.clients[conn] = true
	s.clientsMux.Unlock()

	logger.Info("WebSocket客户端连接")

	// 清理
	defer func() {
		s.clientsMux.Lock()
		delete(s.clients, conn)
		s.clientsMux.Unlock()
		logger.Info("WebSocket客户端断开")
	}()

	// 读取消息
	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			break
		}

		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		response, err := s.handler.HandleMessage(ctx, string(message))
		cancel()

		if err != nil {
			conn.WriteJSON(map[string]string{"error": err.Error()})
		} else {
			conn.WriteJSON(map[string]string{"response": response})
		}
	}
}

// Broadcast 广播消息给所有客户端
func (s *Server) Broadcast(message string) {
	s.clientsMux.RLock()
	defer s.clientsMux.RUnlock()

	for client := range s.clients {
		client.WriteJSON(map[string]string{"message": message})
	}
}

const indexHTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>贾维斯 JARVIS</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            color: #00d4ff;
            font-size: 28px;
            text-shadow: 0 0 20px rgba(0,212,255,0.5);
        }
        .header p {
            color: #888;
            margin-top: 5px;
        }
        .chat-container {
            flex: 1;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 80%;
        }
        .message.user {
            background: #00d4ff;
            color: #000;
            margin-left: auto;
        }
        .message.assistant {
            background: rgba(255,255,255,0.1);
            color: #fff;
        }
        .message.system {
            background: rgba(255,165,0,0.2);
            color: #ffa500;
            max-width: 100%;
            text-align: center;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        .input-area input {
            flex: 1;
            padding: 15px 20px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 16px;
            outline: none;
        }
        .input-area input::placeholder {
            color: #666;
        }
        .input-area button {
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            background: #00d4ff;
            color: #000;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .input-area button:hover {
            background: #00b8e6;
            transform: scale(1.05);
        }
        .typing {
            display: none;
            color: #888;
            font-style: italic;
            margin-bottom: 15px;
        }
        .typing.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 贾维斯 JARVIS</h1>
        <p>智能AI助手 - 本地部署</p>
    </div>
    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="message system">欢迎使用贾维斯！我是你的智能AI助手。</div>
        </div>
        <div class="typing" id="typing">贾维斯正在思考...</div>
        <div class="input-area">
            <input type="text" id="input" placeholder="输入消息..." autofocus>
            <button onclick="sendMessage()">发送</button>
        </div>
    </div>
    <script>
        const messages = document.getElementById('messages');
        const input = document.getElementById('input');
        const typing = document.getElementById('typing');

        function addMessage(content, type) {
            const div = document.createElement('div');
            div.className = 'message ' + type;
            div.textContent = content;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            input.value = '';
            addMessage(message, 'user');
            typing.classList.add('active');

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                const data = await response.json();
                addMessage(data.response || data.error, 'assistant');
            } catch (e) {
                addMessage('连接错误: ' + e.message, 'system');
            }

            typing.classList.remove('active');
        }

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>`
