"""
Web服务 - FastAPI HTTP + WebSocket聊天界面
"""
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None


class MemoryStatusResponse(BaseModel):
    total_vectors: int
    by_type: dict
    working_memory: str


def create_app(dialog_manager, config: dict = None):
    """
    创建FastAPI应用

    Args:
        dialog_manager: DialogManager实例
        config: Web配置字典

    Returns:
        FastAPI应用实例
    """
    config = config or {}
    app = FastAPI(title="Jarvis v5.0", version="5.0.0")

    # CORS
    origins = config.get("cors_origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # WebSocket连接管理
    active_connections = {}

    @app.get("/")
    async def index():
        """返回内嵌HTML聊天界面"""
        return {
            "status": "ok",
            "version": "5.0.0",
            "endpoints": {
                "GET /": "this page",
                "POST /api/chat": "chat API",
                "GET /ws": "WebSocket chat",
                "GET /api/skills": "list skills",
                "GET /api/memory/status": "memory system status",
            },
        }

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat_api(req: ChatRequest):
        """
        JSON聊天API

        Request:
        {
            "message": "你好",
            "user_id": "default"  // optional
        }

        Response:
        {
            "response": "你好！有什么我可以帮你的？"
        }
        """
        if not req.message.strip():
            raise HTTPException(status_code=400, detail="消息不能为空")

        try:
            response = dialog_manager.chat(req.message, user_id=req.user_id)
            return ChatResponse(response=response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket聊天连接"""
        await websocket.accept()
        user_id = "default"

        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                try:
                    msg_data = json.loads(data)
                    message = msg_data.get("message", data)
                    user_id = msg_data.get("user_id", "default")
                except json.JSONDecodeError:
                    message = data

                if not message.strip():
                    await websocket.send_json({"error": "消息不能为空"})
                    continue

                # 处理对话
                response = dialog_manager.chat(message, user_id=user_id)
                await websocket.send_json({"response": response})

        except WebSocketDisconnect:
            print(f"[WS] 用户 {user_id} 断开连接")

    @app.get("/api/skills")
    async def list_skills():
        """列出所有已注册的技能"""
        skills = []
        if dialog_manager.skill_registry:
            for skill in dialog_manager.skill_registry.get_all_skills():
                skills.append({
                    "name": skill.name,
                    "description": skill.description,
                    "parameters": skill.parameters,
                })
        return {"skills": skills, "count": len(skills)}

    @app.get("/api/memory/status", response_model=MemoryStatusResponse)
    async def memory_status():
        """获取记忆系统状态"""
        if dialog_manager.memory_bridge:
            summary = dialog_manager.memory_bridge.get_memory_summary()
            return MemoryStatusResponse(
                total_vectors=summary["total_vectors"],
                by_type=summary["by_type"],
                working_memory=summary["working_memory"],
            )
        return MemoryStatusResponse(
            total_vectors=0,
            by_type={},
            working_memory="0/0",
        )

    @app.get("/api/history")
    async def get_history(user_id: str = "default"):
        """获取对话历史"""
        return {"history": dialog_manager.get_history()}

    @app.post("/api/history/clear")
    async def clear_history():
        """清空对话历史"""
        dialog_manager.clear_history()
        return {"status": "ok"}

    return app


def generate_chat_html() -> str:
    """生成内嵌HTML聊天界面"""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Jarvis v5.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: #16213e;
            padding: 15px 20px;
            border-bottom: 1px solid #0f3460;
        }
        .header h1 {
            font-size: 1.2em;
            color: #e94560;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .message {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .message.user {
            background: #0f3460;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .message.assistant {
            background: #16213e;
            border: 1px solid #0f3460;
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }
        .input-area {
            background: #16213e;
            padding: 15px 20px;
            border-top: 1px solid #0f3460;
            display: flex;
            gap: 10px;
        }
        .input-area input {
            flex: 1;
            background: #1a1a2e;
            border: 1px solid #0f3460;
            color: #e0e0e0;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 1em;
        }
        .input-area input:focus {
            outline: none;
            border-color: #e94560;
        }
        .input-area button {
            background: #e94560;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
        }
        .input-area button:hover {
            background: #ff6b6b;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Jarvis v5.0</h1>
    </div>
    <div class="chat-container" id="chatContainer"></div>
    <div class="input-area">
        <input type="text" id="messageInput" placeholder="输入消息..."
               onkeypress="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">发送</button>
    </div>
    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        let loading = false;

        function addMessage(text, role) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.textContent = text;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message || loading) return;

            loading = true;
            messageInput.disabled = true;
            addMessage(message, 'user');
            messageInput.value = '';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message}),
                });

                const data = await response.json();
                if (data.response) {
                    addMessage(data.response, 'assistant');
                } else {
                    addMessage('错误: ' + (data.detail || '未知错误'), 'assistant');
                }
            } catch (error) {
                addMessage('网络错误: ' + error.message, 'assistant');
            }

            loading = false;
            messageInput.disabled = false;
            messageInput.focus();
        }

        messageInput.focus();
    </script>
</body>
</html>"""
