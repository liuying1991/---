# 真实婴儿AI管家系统API接口文档

## 1. 概述

### 1.1 文档目的
本文档详细描述了真实婴儿AI管家系统的应用程序接口(API)，包括所有可用的端点、请求/响应格式、认证方式和错误处理机制。本API文档旨在为开发人员提供集成和使用真实婴儿AI管家系统所需的所有技术信息。

### 1.2 API基本信息
- **基础URL**: `https://api.realinfantai.com/v1`
- **协议**: HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **API版本**: v1.0

### 1.3 认证方式
本API使用OAuth 2.0 Bearer Token认证方式。所有API请求必须在HTTP头部包含有效的访问令牌：

```
Authorization: Bearer <access_token>
```

获取访问令牌的端点：`POST /oauth/token`

### 1.4 通用响应格式
所有API响应都遵循统一的JSON格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "参数无效",
    "details": "用户名不能为空"
  },
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 2. 认证与授权API

### 2.1 获取访问令牌

**端点**: `POST /oauth/token`

**描述**: 使用客户端凭据获取访问令牌，用于后续API调用。

**请求参数**:
```json
{
  "grant_type": "client_credentials",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "scope": "api_access"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
    "scope": "api_access"
  },
  "message": "令牌获取成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2.2 刷新访问令牌

**端点**: `POST /oauth/refresh`

**描述**: 使用刷新令牌获取新的访问令牌。

**请求参数**:
```json
{
  "grant_type": "refresh_token",
  "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
    "scope": "api_access"
  },
  "message": "令牌刷新成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2.3 撤销访问令牌

**端点**: `POST /oauth/revoke`

**描述**: 撤销访问令牌，使其失效。

**请求参数**:
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type_hint": "access_token"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": null,
  "message": "令牌已撤销",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 3. 用户管理API

### 3.1 创建用户

**端点**: `POST /users`

**描述**: 创建新用户账户。

**请求参数**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "timezone": "America/New_York"
  },
  "preferences": {
    "language": "en",
    "notification_settings": {
      "email": true,
      "sms": false,
      "push": true
    }
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "profile": {
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+1234567890",
      "timezone": "America/New_York"
    },
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:00:00Z"
  },
  "message": "用户创建成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3.2 获取用户信息

**端点**: `GET /users/{user_id}`

**描述**: 获取指定用户的详细信息。

**路径参数**:
- `user_id`: 用户ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "profile": {
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+1234567890",
      "timezone": "America/New_York",
      "avatar_url": "https://cdn.example.com/avatars/john_doe.jpg"
    },
    "preferences": {
      "language": "en",
      "notification_settings": {
        "email": true,
        "sms": false,
        "push": true
      }
    },
    "status": "active",
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:00:00Z",
    "last_login_at": "2023-01-01T11:30:00Z"
  },
  "message": "获取用户信息成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3.3 更新用户信息

**端点**: `PUT /users/{user_id}`

**描述**: 更新指定用户的信息。

**路径参数**:
- `user_id`: 用户ID

**请求参数**:
```json
{
  "profile": {
    "first_name": "John",
    "last_name": "Smith",
    "phone": "+1234567890",
    "timezone": "America/Los_Angeles"
  },
  "preferences": {
    "language": "en",
    "notification_settings": {
      "email": true,
      "sms": true,
      "push": false
    }
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "profile": {
      "first_name": "John",
      "last_name": "Smith",
      "phone": "+1234567890",
      "timezone": "America/Los_Angeles",
      "avatar_url": "https://cdn.example.com/avatars/john_doe.jpg"
    },
    "preferences": {
      "language": "en",
      "notification_settings": {
        "email": true,
        "sms": true,
        "push": false
      }
    },
    "status": "active",
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:30:00Z",
    "last_login_at": "2023-01-01T11:30:00Z"
  },
  "message": "用户信息更新成功",
  "timestamp": "2023-01-01T12:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3.4 删除用户

**端点**: `DELETE /users/{user_id}`

**描述**: 删除指定用户账户。

**路径参数**:
- `user_id`: 用户ID

**响应示例**:
```json
{
  "success": true,
  "data": null,
  "message": "用户删除成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3.5 用户认证

**端点**: `POST /users/authenticate`

**描述**: 验证用户凭据并返回访问令牌。

**请求参数**:
```json
{
  "username": "john_doe",
  "password": "secure_password",
  "remember_me": false
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "tGzv3JOkF0XG5Qx2TlKWIA",
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "认证成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 4. 感知系统API

### 4.1 语音识别

**端点**: `POST /perception/speech/recognize`

**描述**: 将音频数据转换为文本。

**请求参数**:
```json
{
  "audio_data": "base64_encoded_audio_data",
  "audio_format": "wav",
  "sample_rate": 16000,
  "channels": 1,
  "language": "zh-CN",
  "options": {
    "enable_punctuation": true,
    "enable_timestamps": true,
    "max_alternatives": 3
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "text": "你好，真实婴儿AI管家",
    "confidence": 0.95,
    "alternatives": [
      {
        "text": "你好，真实婴儿AI管家",
        "confidence": 0.95
      },
      {
        "text": "你好，真实婴儿AI官家",
        "confidence": 0.80
      },
      {
        "text": "你好，真实婴儿AI管佳",
        "confidence": 0.75
      }
    ],
    "words": [
      {
        "word": "你好",
        "start_time": 0.1,
        "end_time": 0.5,
        "confidence": 0.98
      },
      {
        "word": "真实",
        "start_time": 0.6,
        "end_time": 0.9,
        "confidence": 0.96
      },
      {
        "word": "婴儿",
        "start_time": 1.0,
        "end_time": 1.3,
        "confidence": 0.94
      },
      {
        "word": "AI",
        "start_time": 1.4,
        "end_time": 1.6,
        "confidence": 0.97
      },
      {
        "word": "管家",
        "start_time": 1.7,
        "end_time": 2.0,
        "confidence": 0.95
      }
    ]
  },
  "message": "语音识别成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 4.2 图像识别

**端点**: `POST /perception/vision/recognize`

**描述**: 识别图像中的对象、场景和文本。

**请求参数**:
```json
{
  "image_data": "base64_encoded_image_data",
  "image_format": "jpeg",
  "options": {
    "detect_objects": true,
    "detect_faces": true,
    "detect_text": true,
    "detect_scenes": true,
    "analyze_emotions": true
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "objects": [
      {
        "name": "人",
        "confidence": 0.98,
        "bounding_box": {
          "x": 100,
          "y": 50,
          "width": 200,
          "height": 300
        }
      },
      {
        "name": "桌子",
        "confidence": 0.92,
        "bounding_box": {
          "x": 50,
          "y": 250,
          "width": 300,
          "height": 150
        }
      }
    ],
    "faces": [
      {
        "face_id": "face_001",
        "bounding_box": {
          "x": 150,
          "y": 100,
          "width": 100,
          "height": 120
        },
        "landmarks": {
          "left_eye": { "x": 170, "y": 130 },
          "right_eye": { "x": 230, "y": 130 },
          "nose": { "x": 200, "y": 150 },
          "left_mouth": { "x": 180, "y": 180 },
          "right_mouth": { "x": 220, "y": 180 }
        },
        "emotions": {
          "happy": 0.85,
          "neutral": 0.10,
          "surprise": 0.05
        },
        "age_range": { "low": 25, "high": 35 },
        "gender": { "value": "female", "confidence": 0.95 }
      }
    ],
    "text": [
      {
        "text": "欢迎来到真实婴儿AI管家",
        "bounding_box": {
          "x": 100,
          "y": 20,
          "width": 200,
          "height": 30
        },
        "confidence": 0.97
      }
    ],
    "scenes": [
      {
        "name": "室内",
        "confidence": 0.98
      },
      {
        "name": "办公室",
        "confidence": 0.85
      }
    ]
  },
  "message": "图像识别成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 4.3 情感识别

**端点**: `POST /perception/emotion/recognize`

**描述**: 从文本、语音或图像中识别情感。

**请求参数**:
```json
{
  "input_type": "text",
  "input_data": "我今天心情很好，因为天气晴朗",
  "language": "zh-CN"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "dominant_emotion": "happy",
    "emotions": {
      "happy": 0.75,
      "neutral": 0.20,
      "excited": 0.05
    },
    "sentiment": {
      "polarity": 0.8,
      "subjectivity": 0.6
    },
    "keywords": [
      {
        "word": "心情很好",
        "emotion": "happy",
        "confidence": 0.9
      },
      {
        "word": "天气晴朗",
        "emotion": "happy",
        "confidence": 0.85
      }
    ]
  },
  "message": "情感识别成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 5. 交互系统API

### 5.1 文本对话

**端点**: `POST /interaction/chat/text`

**描述**: 与AI管家进行文本对话。

**请求参数**:
```json
{
  "message": "今天天气怎么样？",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_001",
  "context": {
    "location": "北京",
    "date": "2023-01-01"
  },
  "options": {
    "include_knowledge": true,
    "max_response_length": 200,
    "response_style": "friendly"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "response": "今天北京天气晴朗，气温在5到15摄氏度之间，适合外出活动。记得多穿衣服保暖哦！",
    "session_id": "session_001",
    "response_id": "resp_001",
    "intent": "weather_query",
    "entities": [
      {
        "type": "location",
        "value": "北京",
        "confidence": 0.95
      },
      {
        "type": "date",
        "value": "今天",
        "confidence": 0.90
      }
    ],
    "confidence": 0.92,
    "response_time_ms": 350
  },
  "message": "对话响应生成成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5.2 语音对话

**端点**: `POST /interaction/chat/voice`

**描述**: 与AI管家进行语音对话。

**请求参数**:
```json
{
  "audio_data": "base64_encoded_audio_data",
  "audio_format": "wav",
  "sample_rate": 16000,
  "channels": 1,
  "language": "zh-CN",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_001",
  "options": {
    "include_knowledge": true,
    "max_response_length": 200,
    "response_style": "friendly",
    "voice": "female_child",
    "speech_rate": 1.0
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "recognized_text": "今天天气怎么样？",
    "response": "今天北京天气晴朗，气温在5到15摄氏度之间，适合外出活动。记得多穿衣服保暖哦！",
    "response_audio": "base64_encoded_response_audio",
    "audio_format": "wav",
    "sample_rate": 16000,
    "session_id": "session_001",
    "response_id": "resp_001",
    "intent": "weather_query",
    "entities": [
      {
        "type": "location",
        "value": "北京",
        "confidence": 0.95
      },
      {
        "type": "date",
        "value": "今天",
        "confidence": 0.90
      }
    ],
    "confidence": 0.92,
    "recognition_confidence": 0.95,
    "response_time_ms": 850
  },
  "message": "语音对话响应生成成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5.3 文本转语音

**端点**: `POST /interaction/tts`

**描述**: 将文本转换为语音。

**请求参数**:
```json
{
  "text": "你好，我是真实婴儿AI管家，很高兴为您服务！",
  "language": "zh-CN",
  "voice": "female_child",
  "options": {
    "speech_rate": 1.0,
    "pitch": 1.0,
    "volume": 1.0,
    "emotion": "happy",
    "output_format": "wav",
    "sample_rate": 16000
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "audio_data": "base64_encoded_audio_data",
    "audio_format": "wav",
    "sample_rate": 16000,
    "duration_ms": 3200,
    "text": "你好，我是真实婴儿AI管家，很高兴为您服务！",
    "voice": "female_child",
    "emotion": "happy"
  },
  "message": "文本转语音成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5.4 语音转文本

**端点**: `POST /interaction/stt`

**描述**: 将语音转换为文本。

**请求参数**:
```json
{
  "audio_data": "base64_encoded_audio_data",
  "audio_format": "wav",
  "sample_rate": 16000,
  "channels": 1,
  "language": "zh-CN",
  "options": {
    "enable_punctuation": true,
    "enable_timestamps": true,
    "max_alternatives": 3
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "text": "你好，我是真实婴儿AI管家，很高兴为您服务！",
    "confidence": 0.95,
    "alternatives": [
      {
        "text": "你好，我是真实婴儿AI管家，很高兴为您服务！",
        "confidence": 0.95
      },
      {
        "text": "你好，我是真实婴儿AI官家，很高兴为您服务！",
        "confidence": 0.80
      }
    ],
    "words": [
      {
        "word": "你好",
        "start_time": 0.1,
        "end_time": 0.5,
        "confidence": 0.98
      },
      {
        "word": "我是",
        "start_time": 0.6,
        "end_time": 0.9,
        "confidence": 0.96
      },
      {
        "word": "真实",
        "start_time": 1.0,
        "end_time": 1.3,
        "confidence": 0.94
      },
      {
        "word": "婴儿",
        "start_time": 1.4,
        "end_time": 1.7,
        "confidence": 0.97
      },
      {
        "word": "AI",
        "start_time": 1.8,
        "end_time": 2.0,
        "confidence": 0.95
      },
      {
        "word": "管家",
        "start_time": 2.1,
        "end_time": 2.4,
        "confidence": 0.93
      }
    ]
  },
  "message": "语音转文本成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 6. 思维系统API

### 6.1 推理分析

**端点**: `POST /thinking/reasoning/analyze`

**描述**: 对输入信息进行推理分析。

**请求参数**:
```json
{
  "input": "如果今天下雨，那么小明会带伞。今天下雨了。",
  "reasoning_type": "logical",
  "options": {
    "include_explanation": true,
    "include_confidence": true,
    "max_depth": 5
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "conclusion": "小明会带伞",
    "reasoning_type": "logical",
    "confidence": 0.95,
    "explanation": "根据给定的前提条件'如果今天下雨，那么小明会带伞'和'今天下雨了'，通过演绎推理可以得出结论'小明会带伞'。",
    "reasoning_steps": [
      {
        "step": 1,
        "description": "识别前提条件",
        "content": "如果今天下雨，那么小明会带伞。今天下雨了。"
      },
      {
        "step": 2,
        "description": "应用演绎推理",
        "content": "从'如果P，那么Q'和'P'可以推出'Q'"
      },
      {
        "step": 3,
        "description": "得出结论",
        "content": "小明会带伞"
      }
    ],
    "logic_form": {
      "premises": [
        "如果今天下雨，那么小明会带伞",
        "今天下雨了"
      ],
      "conclusion": "小明会带伞",
      "rule": "Modus Ponens"
    }
  },
  "message": "推理分析完成",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 6.2 知识查询

**端点**: `POST /thinking/knowledge/query`

**描述**: 从知识库中查询相关信息。

**请求参数**:
```json
{
  "query": "北京的人口是多少？",
  "query_type": "factual",
  "options": {
    "include_sources": true,
    "max_results": 5,
    "result_format": "detailed"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "answer": "根据最新数据，北京市的人口约为2189万人。",
    "confidence": 0.92,
    "sources": [
      {
        "title": "北京市统计局2022年人口数据",
        "url": "http://www.bjstats.gov.cn/",
        "reliability": 0.95,
        "publication_date": "2022-12-31"
      }
    ],
    "related_entities": [
      {
        "name": "北京",
        "type": "城市",
        "description": "中华人民共和国首都"
      },
      {
        "name": "人口",
        "type": "统计指标",
        "description": "居住在某一地区的人口总数"
      }
    ],
    "query_results": [
      {
        "title": "北京市人口统计数据",
        "snippet": "截至2022年底，北京市常住人口为2189.3万人...",
        "url": "http://www.bjstats.gov.cn/",
        "relevance_score": 0.95
      }
    ]
  },
  "message": "知识查询完成",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 6.3 决策支持

**端点**: `POST /thinking/decision/support`

**描述**: 为决策提供建议和分析。

**请求参数**:
```json
{
  "decision_context": "我正在考虑是否要购买一辆电动车",
  "options": [
    {
      "name": "购买电动车",
      "pros": ["环保", "运行成本低", "驾驶体验好"],
      "cons": ["初始成本高", "充电不便", "续航里程焦虑"]
    },
    {
      "name": "继续使用燃油车",
      "pros": ["加油方便", "续航里程长", "初始成本低"],
      "cons": ["污染环境", "运行成本高", "未来可能受限"]
    }
  ],
  "criteria": [
    {
      "name": "成本",
      "weight": 0.4
    },
    {
      "name": "便利性",
      "weight": 0.3
    },
    {
      "name": "环保性",
      "weight": 0.3
    }
  ],
  "options": {
    "include_explanation": true,
    "include_sensitivity_analysis": true
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "recommended_option": "购买电动车",
    "confidence": 0.75,
    "option_scores": {
      "购买电动车": 0.75,
      "继续使用燃油车": 0.25
    },
    "criteria_scores": {
      "购买电动车": {
        "成本": 0.6,
        "便利性": 0.4,
        "环保性": 0.95
      },
      "继续使用燃油车": {
        "成本": 0.8,
        "便利性": 0.9,
        "环保性": 0.2
      }
    },
    "explanation": "基于您提供的标准和权重，购买电动车得分更高。虽然初始成本较高，但在环保性方面表现优异，且长期运行成本较低。随着充电基础设施的不断完善，便利性问题也在逐步解决。",
    "sensitivity_analysis": {
      "most_sensitive_criteria": "成本",
      "break_even_point": "如果成本权重增加到0.6，继续使用燃油车将成为更优选择",
      "scenario_analysis": {
        "高油价情景": {
          "recommended_option": "购买电动车",
          "confidence": 0.85
        },
        "充电设施完善情景": {
          "recommended_option": "购买电动车",
          "confidence": 0.9
        }
      }
    },
    "additional_considerations": [
      "考虑您的日常行驶里程，如果每天通勤距离较长，电动车的经济优势更明显",
      "评估您居住地附近的充电设施可用性",
      "考虑政府的电动车补贴政策"
    ]
  },
  "message": "决策支持分析完成",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 7. 学习系统API

### 7.1 记录学习数据

**端点**: `POST /learning/data/record`

**描述**: 记录用户的学习数据和交互历史。

**请求参数**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_001",
  "interaction_type": "chat",
  "interaction_data": {
    "user_input": "今天天气怎么样？",
    "system_response": "今天北京天气晴朗，气温在5到15摄氏度之间...",
    "context": {
      "location": "北京",
      "time": "2023-01-01T12:00:00Z"
    },
    "metrics": {
      "response_time_ms": 350,
      "user_satisfaction": 5
    }
  },
  "timestamp": "2023-01-01T12:00:00Z"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "record_id": "rec_001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "session_001",
    "timestamp": "2023-01-01T12:00:00Z"
  },
  "message": "学习数据记录成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 7.2 获取用户画像

**端点**: `GET /learning/profile/{user_id}`

**描述**: 获取基于学习数据生成的用户画像。

**路径参数**:
- `user_id`: 用户ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "profile": {
      "demographics": {
        "age_range": "25-35",
        "location": "北京",
        "language": "zh-CN"
      },
      "preferences": {
        "topics": ["科技", "天气", "旅游"],
        "interaction_style": "friendly",
        "response_length": "medium"
      },
      "behavior_patterns": {
        "active_hours": ["08:00-10:00", "18:00-20:00"],
        "interaction_frequency": "daily",
        "preferred_device": "mobile"
      },
      "interests": {
        "high": ["人工智能", "科技新闻", "天气预报"],
        "medium": ["旅游", "美食", "电影"],
        "low": ["体育", "政治", "财经"]
      },
      "personality_traits": {
        "openness": 0.75,
        "conscientiousness": 0.65,
        "extraversion": 0.60,
        "agreeableness": 0.80,
        "neuroticism": 0.40
      }
    },
    "updated_at": "2023-01-01T12:00:00Z",
    "confidence": 0.85
  },
  "message": "用户画像获取成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 7.3 个性化推荐

**端点**: `POST /learning/recommendation/personalize`

**描述**: 基于用户画像和学习数据提供个性化推荐。

**请求参数**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendation_type": "content",
  "context": {
    "current_topic": "天气",
    "time_of_day": "morning",
    "device": "mobile"
  },
  "options": {
    "max_results": 5,
    "include_explanation": true,
    "diversity_factor": 0.3
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "id": "rec_001",
        "type": "news",
        "title": "北京今日天气预报",
        "content": "今天北京天气晴朗，气温在5到15摄氏度之间...",
        "relevance_score": 0.95,
        "explanation": "基于您对天气话题的兴趣和当前时间推荐"
      },
      {
        "id": "rec_002",
        "type": "tip",
        "title": "冬季穿衣小贴士",
        "content": "在气温较低的早晨，建议您多穿一件保暖外套...",
        "relevance_score": 0.85,
        "explanation": "根据当前天气和您的穿衣习惯推荐"
      },
      {
        "id": "rec_003",
        "type": "activity",
        "title": "今日适合的户外活动",
        "content": "今天天气晴朗，适合晨跑或散步...",
        "relevance_score": 0.80,
        "explanation": "基于您的运动习惯和今日天气推荐"
      }
    ],
    "recommendation_id": "rec_batch_001",
    "generated_at": "2023-01-01T12:00:00Z"
  },
  "message": "个性化推荐生成成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 8. 进化系统API

### 8.1 获取系统性能指标

**端点**: `GET /evolution/performance/metrics`

**描述**: 获取系统性能指标和进化状态。

**查询参数**:
- `time_range`: 时间范围 (1h, 24h, 7d, 30d)
- `metric_type`: 指标类型 (all, response_time, accuracy, resource_usage)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "time_range": "24h",
    "metrics": {
      "response_time": {
        "average_ms": 320,
        "p50_ms": 280,
        "p95_ms": 450,
        "p99_ms": 650,
        "trend": "improving"
      },
      "accuracy": {
        "speech_recognition": 0.94,
        "image_recognition": 0.92,
        "intent_classification": 0.89,
        "entity_extraction": 0.87,
        "trend": "stable"
      },
      "resource_usage": {
        "cpu_percent": 45.2,
        "memory_percent": 62.8,
        "disk_usage_percent": 38.5,
        "network_throughput_mbps": 125.6,
        "trend": "stable"
      },
      "user_satisfaction": {
        "average_rating": 4.6,
        "positive_feedback_percent": 87.3,
        "negative_feedback_percent": 5.2,
        "trend": "improving"
      }
    },
    "evolution_status": {
      "current_generation": 3,
      "last_evolution": "2023-01-01T00:00:00Z",
      "next_evolution": "2023-01-08T00:00:00Z",
      "improvements": [
        "语音识别准确率提升2%",
        "响应时间减少15%",
        "多轮对话连贯性提升10%"
      ]
    }
  },
  "message": "系统性能指标获取成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 8.2 触发系统进化

**端点**: `POST /evolution/trigger`

**描述**: 手动触发系统进化过程。

**请求参数**:
```json
{
  "evolution_type": "incremental",
  "target_components": [
    "speech_recognition",
    "natural_language_understanding"
  ],
  "training_data": {
    "use_recent_interactions": true,
    "time_range_days": 7,
    "include_feedback": true
  },
  "options": {
    "max_training_time_hours": 4,
    "validation_split": 0.2,
    "early_stopping": true
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "evolution_id": "evo_001",
    "status": "initiated",
    "estimated_completion_time": "2023-01-01T16:00:00Z",
    "target_components": [
      "speech_recognition",
      "natural_language_understanding"
    ],
    "training_data_size": 15000,
    "validation_data_size": 3000
  },
  "message": "系统进化已启动",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 8.3 获取进化状态

**端点**: `GET /evolution/status/{evolution_id}`

**描述**: 获取指定进化过程的状态。

**路径参数**:
- `evolution_id`: 进化ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "evolution_id": "evo_001",
    "status": "in_progress",
    "progress_percent": 65,
    "started_at": "2023-01-01T12:00:00Z",
    "estimated_completion": "2023-01-01T15:30:00Z",
    "target_components": [
      {
        "name": "speech_recognition",
        "status": "training",
        "progress_percent": 70,
        "current_accuracy": 0.94,
        "target_accuracy": 0.96
      },
      {
        "name": "natural_language_understanding",
        "status": "validation",
        "progress_percent": 60,
        "current_accuracy": 0.89,
        "target_accuracy": 0.91
      }
    ],
    "metrics": {
      "training_loss": 0.32,
      "validation_loss": 0.38,
      "training_accuracy": 0.92,
      "validation_accuracy": 0.89
    },
    "logs": [
      {
        "timestamp": "2023-01-01T14:00:00Z",
        "level": "info",
        "message": "语音识别模型训练进度: 70%"
      },
      {
        "timestamp": "2023-01-01T14:15:00Z",
        "level": "info",
        "message": "自然语言理解模型验证进度: 60%"
      }
    ]
  },
  "message": "进化状态获取成功",
  "timestamp": "2023-01-01T14:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 9. 数据收集API

### 9.1 创建数据收集任务

**端点**: `POST /data-collection/tasks`

**描述**: 创建新的数据收集任务。

**请求参数**:
```json
{
  "task_name": "天气相关对话数据收集",
  "data_type": "conversation",
  "source": "user_interactions",
  "filters": {
    "keywords": ["天气", "气温", "下雨", "晴天"],
    "min_interaction_length": 2,
    "user_satisfaction_min": 4
  },
  "schedule": {
    "start_time": "2023-01-01T00:00:00Z",
    "end_time": "2023-01-07T23:59:59Z",
    "frequency": "daily"
  },
  "privacy_settings": {
    "anonymize_user_data": true,
    "exclude_pii": true,
    "retention_days": 30
  },
  "output_format": "json",
  "destination": {
    "type": "s3",
    "bucket": "realinfantai-data",
    "prefix": "weather-conversations/"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_001",
    "task_name": "天气相关对话数据收集",
    "status": "scheduled",
    "created_at": "2023-01-01T12:00:00Z",
    "next_run": "2023-01-01T23:59:59Z"
  },
  "message": "数据收集任务创建成功",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 9.2 获取数据收集任务状态

**端点**: `GET /data-collection/tasks/{task_id}`

**描述**: 获取指定数据收集任务的状态。

**路径参数**:
- `task_id`: 任务ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_001",
    "task_name": "天气相关对话数据收集",
    "status": "running",
    "progress": {
      "total_records": 5000,
      "collected_records": 3250,
      "progress_percent": 65
    },
    "schedule": {
      "start_time": "2023-01-01T00:00:00Z",
      "end_time": "2023-01-07T23:59:59Z",
      "frequency": "daily",
      "last_run": "2023-01-02T00:00:00Z",
      "next_run": "2023-01-03T00:00:00Z"
    },
    "output": {
      "format": "json",
      "destination": {
        "type": "s3",
        "bucket": "realinfantai-data",
        "prefix": "weather-conversations/",
        "files": [
          "weather-conversations-2023-01-01.json",
          "weather-conversations-2023-01-02.json"
        ]
      },
      "total_size_mb": 125.6
    },
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-02T12:00:00Z"
  },
  "message": "数据收集任务状态获取成功",
  "timestamp": "2023-01-02T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 9.3 获取收集的数据

**端点**: `GET /data-collection/data/{task_id}`

**描述**: 获取指定任务收集的数据。

**路径参数**:
- `task_id`: 任务ID

**查询参数**:
- `date`: 日期 (YYYY-MM-DD)
- `format`: 输出格式 (json, csv)
- `limit`: 返回记录数限制
- `offset`: 偏移量

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_001",
    "date": "2023-01-01",
    "format": "json",
    "records": [
      {
        "id": "rec_001",
        "timestamp": "2023-01-01T12:00:00Z",
        "user_id": "user_001_anonymized",
        "conversation": [
          {
            "role": "user",
            "content": "今天天气怎么样？",
            "timestamp": "2023-01-01T12:00:00Z"
          },
          {
            "role": "assistant",
            "content": "今天北京天气晴朗，气温在5到15摄氏度之间...",
            "timestamp": "2023-01-01T12:00:01Z"
          }
        ],
        "metadata": {
          "location": "北京",
          "device": "mobile",
          "language": "zh-CN",
          "user_satisfaction": 5
        }
      },
      {
        "id": "rec_002",
        "timestamp": "2023-01-01T12:30:00Z",
        "user_id": "user_002_anonymized",
        "conversation": [
          {
            "role": "user",
            "content": "明天会下雨吗？",
            "timestamp": "2023-01-01T12:30:00Z"
          },
          {
            "role": "assistant",
            "content": "根据天气预报，明天北京有30%的降雨概率...",
            "timestamp": "2023-01-01T12:30:01Z"
          }
        ],
        "metadata": {
          "location": "北京",
          "device": "desktop",
          "language": "zh-CN",
          "user_satisfaction": 4
        }
      }
    ],
    "total_records": 2,
    "returned_records": 2
  },
  "message": "数据获取成功",
  "timestamp": "2023-01-02T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 10. 错误代码

### 10.1 认证与授权错误

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| INVALID_CREDENTIALS | 401 | 用户名或密码无效 |
| TOKEN_EXPIRED | 401 | 访问令牌已过期 |
| TOKEN_REVOKED | 401 | 访问令牌已被撤销 |
| INSUFFICIENT_PERMISSIONS | 403 | 权限不足 |
| ACCOUNT_LOCKED | 403 | 账户已被锁定 |
| ACCOUNT_DISABLED | 403 | 账户已被禁用 |

### 10.2 请求参数错误

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| INVALID_PARAMETER | 400 | 参数无效 |
| MISSING_PARAMETER | 400 | 缺少必需参数 |
| INVALID_FORMAT | 400 | 参数格式无效 |
| PARAMETER_OUT_OF_RANGE | 400 | 参数超出有效范围 |

### 10.3 资源错误

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| RESOURCE_NOT_FOUND | 404 | 资源不存在 |
| RESOURCE_ALREADY_EXISTS | 409 | 资源已存在 |
| RESOURCE_IN_USE | 409 | 资源正在使用中 |
| RESOURCE_LIMIT_EXCEEDED | 429 | 资源使用超过限制 |

### 10.4 系统错误

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| INTERNAL_SERVER_ERROR | 500 | 内部服务器错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |
| DATABASE_ERROR | 500 | 数据库错误 |
| NETWORK_ERROR | 500 | 网络错误 |
| TIMEOUT | 408 | 请求超时 |

### 10.5 业务逻辑错误

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| INVALID_OPERATION | 400 | 无效操作 |
| OPERATION_NOT_ALLOWED | 403 | 不允许的操作 |
| QUOTA_EXCEEDED | 429 | 配额已超出 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超过限制 |

## 11. API使用限制

### 11.1 请求频率限制

| 端点类型 | 限制 | 时间窗口 |
|---------|------|---------|
| 认证相关 | 10次/IP | 1分钟 |
| 用户管理 | 100次/用户 | 1小时 |
| 感知系统 | 1000次/用户 | 1小时 |
| 交互系统 | 5000次/用户 | 1小时 |
| 思维系统 | 2000次/用户 | 1小时 |
| 学习系统 | 500次/用户 | 1小时 |
| 进化系统 | 10次/用户 | 1天 |
| 数据收集 | 100次/用户 | 1小时 |

### 11.2 数据大小限制

| 端点 | 最大数据大小 |
|------|-------------|
| 语音识别 | 10MB |
| 图像识别 | 5MB |
| 文本对话 | 10KB |
| 语音对话 | 10MB |
| 文本转语音 | 1KB |
| 语音转文本 | 10MB |

### 11.3 并发连接限制

| 用户类型 | 最大并发连接数 |
|---------|---------------|
| 免费用户 | 5 |
| 基础用户 | 20 |
| 高级用户 | 100 |
| 企业用户 | 500 |

## 12. SDK与示例代码

### 12.1 Python SDK

```python
# 安装SDK
pip install realinfantai-sdk

# 使用示例
from realinfantai import RealInfantAI

# 初始化客户端
client = RealInfantAI(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# 文本对话
response = client.chat.text(
    message="今天天气怎么样？",
    user_id="user_001",
    options={"include_knowledge": True}
)
print(response.response)

# 语音识别
with open("audio.wav", "rb") as f:
    audio_data = f.read()
    
response = client.perception.speech.recognize(
    audio_data=audio_data,
    language="zh-CN"
)
print(response.text)

# 图像识别
with open("image.jpg", "rb") as f:
    image_data = f.read()
    
response = client.perception.vision.recognize(
    image_data=image_data,
    options={"detect_objects": True}
)
print(response.objects)
```

### 12.2 JavaScript SDK

```javascript
// 安装SDK
npm install realinfantai-sdk

// 使用示例
import { RealInfantAI } from 'realinfantai-sdk';

// 初始化客户端
const client = new RealInfantAI({
    clientId: 'your_client_id',
    clientSecret: 'your_client_secret'
});

// 文本对话
async function chatExample() {
    try {
        const response = await client.chat.text({
            message: '今天天气怎么样？',
            userId: 'user_001',
            options: { includeKnowledge: true }
        });
        console.log(response.response);
    } catch (error) {
        console.error('Error:', error);
    }
}

// 语音识别
async function speechRecognitionExample() {
    try {
        const audioData = /* 获取音频数据 */;
        const response = await client.perception.speech.recognize({
            audioData: audioData,
            language: 'zh-CN'
        });
        console.log(response.text);
    } catch (error) {
        console.error('Error:', error);
    }
}
```

### 12.3 REST API示例

```bash
# 获取访问令牌
curl -X POST https://api.realinfantai.com/v1/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "scope": "api_access"
  }'

# 文本对话
curl -X POST https://api.realinfantai.com/v1/interaction/chat/text \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "今天天气怎么样？",
    "user_id": "user_001",
    "options": {
      "include_knowledge": true
    }
  }'

# 语音识别
curl -X POST https://api.realinfantai.com/v1/perception/speech/recognize \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_encoded_audio_data",
    "language": "zh-CN"
  }'
```

## 13. 更新日志

### v1.0.0 (2023-01-01)
- 初始API版本发布
- 包含所有核心功能API
- 支持文本和语音交互
- 提供感知、思维、学习和进化系统API

### v1.1.0 (计划中)
- 增加批量操作API
- 优化性能指标
- 扩展错误代码
- 增加更多语言支持

## 14. 支持与反馈

如果您在使用API过程中遇到任何问题或有任何建议，请通过以下方式联系我们：

- 技术支持邮箱: support@realinfantai.com
- 开发者社区: https://community.realinfantai.com
- API文档: https://docs.realinfantai.com
- 问题反馈: https://github.com/realinfantai/api/issues

## 15. 附录

### 15.1 术语表

| 术语 | 定义 |
|------|------|
| API | 应用程序编程接口 |
| OAuth 2.0 | 开放授权协议 |
| JWT | JSON Web Token |
| REST | 表现层状态转换 |
| SDK | 软件开发工具包 |
| TTS | 文本转语音 |
| STT | 语音转文本 |
| NLU | 自然语言理解 |
| NLP | 自然语言处理 |

### 15.2 参考资源

- OAuth 2.0规范: https://tools.ietf.org/html/rfc6749
- JWT规范: https://tools.ietf.org/html/rfc7519
- REST API设计指南: https://restfulapi.net/
- JSON格式规范: https://www.json.org/json-en.html