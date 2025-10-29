# Apply_记忆存储子系统技术实施

## 1. 阶段概述

### 1.1 阶段目标
Apply阶段是记忆存储子系统开发的第三阶段，主要目标是将Analyze阶段设计的架构转化为具体的代码实现，搭建开发环境，实现核心功能，编写测试用例，确保系统按照设计要求正常运行。

### 1.2 阶段重要性
技术实施是将设计转化为实际产品的关键环节，决定了系统功能的完整性和质量。良好的实施过程可以确保系统功能符合设计要求，代码质量高，系统性能稳定，为后续的测试、部署和维护奠定坚实基础。

### 1.3 阶段主要活动
1. 开发环境搭建
2. 项目结构设计
3. 核心模块实现
4. 接口实现
5. 数据库设计与实现
6. 测试用例编写
7. 集成测试
8. 性能优化

## 2. 技术栈详细选择

### 2.1 开发语言
1. **Python 3.9+**
   - 应用场景：业务逻辑开发、数据处理、机器学习
   - 核心框架：Django、FastAPI
   - 主要库：SQLAlchemy、Pydantic、NumPy、Pandas
   - 开发工具：PyCharm、VS Code

2. **Go 1.19+**
   - 应用场景：高性能服务、中间件、工具开发
   - 核心框架：Gin、Echo
   - 主要库：GORM、Zap、Viper
   - 开发工具：GoLand、VS Code

### 2.2 数据库
1. **PostgreSQL 14+**
   - 应用场景：关系型数据存储
   - 连接库：psycopg2、SQLAlchemy
   - 管理工具：pgAdmin、DBeaver
   - 特性：JSON支持、全文检索、地理信息

2. **MongoDB 5.0+**
   - 应用场景：文档数据存储
   - 连接库：pymongo、mongoengine
   - 管理工具：MongoDB Compass
   - 特性：分片、副本集、事务支持

3. **Redis 6.0+**
   - 应用场景：缓存、会话存储、计数器
   - 连接库：redis-py、aioredis
   - 管理工具：RedisInsight
   - 特性：集群、哨兵、持久化

4. **FAISS 1.7+**
   - 应用场景：向量相似度检索
   - 连接库：faiss-cpu、faiss-gpu
   - 管理工具：自定义管理界面
   - 特性：GPU加速、多种索引、量化

### 2.3 消息队列
1. **RabbitMQ 3.9+**
   - 应用场景：业务消息、任务队列
   - 连接库：pika、celery
   - 管理工具：RabbitMQ Management
   - 特性：持久化、确认机制、集群

2. **Kafka 2.8+**
   - 应用场景：日志收集、事件流
   - 连接库：kafka-python、confluent-kafka
   - 管理工具：Kafka Manager
   - 特性：分区、副本、流处理

### 2.4 搜索引擎
1. **Elasticsearch 7.17+**
   - 应用场景：全文搜索、日志分析
   - 连接库：elasticsearch-py
   - 管理工具：Kibana
   - 特性：分词、聚合、高亮

### 2.5 容器技术
1. **Docker 20.10+**
   - 应用场景：应用容器化
   - 管理工具：Docker Compose
   - 镜像仓库：Harbor、Docker Hub
   - 特性：镜像、容器、仓库

2. **Kubernetes 1.24+**
   - 应用场景：容器编排
   - 管理工具：kubectl、Lens
   - 服务网格：Istio
   - 特性：Pod、Service、Deployment

### 2.6 监控技术
1. **Prometheus 2.33+**
   - 应用场景：指标监控
   - 连接库：prometheus-client
   - 管理工具：Prometheus Web UI
   - 特性：拉取模式、服务发现、告警

2. **Grafana 8.5+**
   - 应用场景：监控可视化
   - 数据源：Prometheus、Elasticsearch
   - 特性：仪表盘、面板、插件

3. **Jaeger 1.35+**
   - 应用场景：链路追踪
   - 连接库：jaeger-client
   - 管理工具：Jaeger Web UI
   - 特性：追踪、采样、存储

## 3. 项目结构设计

### 3.1 整体目录结构
```
memory-storage-subsystem/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python依赖
├── go.mod                       # Go模块定义
├── docker-compose.yml           # Docker Compose配置
├── Dockerfile                   # Docker镜像构建文件
├── k8s/                         # Kubernetes配置
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── config/                      # 配置文件
│   ├── app.yaml
│   ├── database.yaml
│   ├── cache.yaml
│   └── logging.yaml
├── scripts/                     # 脚本文件
│   ├── setup.sh
│   ├── build.sh
│   ├── deploy.sh
│   └── test.sh
├── docs/                        # 文档目录
│   ├── api/
│   ├── architecture/
│   ├── deployment/
│   └── user-guide/
├── tests/                       # 测试目录
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   └── fixtures/
├── python/                      # Python代码目录
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # 应用入口
│   │   ├── config.py            # 配置管理
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务服务
│   │   ├── api/                 # API接口
│   │   ├── utils/               # 工具函数
│   │   └── exceptions.py        # 异常定义
│   ├── requirements.txt
│   └── Dockerfile
├── go/                          # Go代码目录
│   ├── cmd/
│   │   └── main.go              # 应用入口
│   ├── internal/
│   │   ├── config/              # 配置管理
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务服务
│   │   ├── api/                 # API接口
│   │   └── utils/               # 工具函数
│   ├── pkg/                     # 公共包
│   ├── go.mod
│   └── Dockerfile
└── proto/                       # Protobuf定义
    ├── memory_service.proto
    └── search_service.proto
```

### 3.2 Python项目结构
```
python/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI应用入口
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库连接
│   ├── dependencies.py          # 依赖注入
│   ├── exceptions.py            # 异常定义
│   ├── middleware.py            # 中间件
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   ├── memory.py            # 记忆模型
│   │   ├── user.py              # 用户模型
│   │   └── system.py            # 系统模型
│   ├── schemas/                 # Pydantic模型
│   │   ├── __init__.py
│   │   ├── memory.py            # 记忆模式
│   │   ├── user.py              # 用户模式
│   │   └── response.py          # 响应模式
│   ├── services/                # 业务服务
│   │   ├── __init__.py
│   │   ├── memory_service.py    # 记忆服务
│   │   ├── search_service.py    # 检索服务
│   │   ├── management_service.py # 管理服务
│   │   └── analysis_service.py  # 分析服务
│   ├── api/                     # API接口
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── memory.py        # 记忆API
│   │   │   ├── search.py        # 检索API
│   │   │   ├── management.py    # 管理API
│   │   │   └── analysis.py      # 分析API
│   │   └── deps.py              # 依赖
│   ├── repositories/            # 数据访问层
│   │   ├── __init__.py
│   │   ├── memory_repository.py # 记忆仓库
│   │   ├── user_repository.py   # 用户仓库
│   │   └── system_repository.py # 系统仓库
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证工具
│   │   ├── crypto.py            # 加密工具
│   │   ├── logger.py            # 日志工具
│   │   └── validators.py        # 验证工具
│   └── workers/                 # 后台任务
│       ├── __init__.py
│       ├── celery_app.py        # Celery应用
│       └── tasks.py             # 任务定义
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── conftest.py              # 测试配置
│   ├── test_models/             # 模型测试
│   ├── test_services/           # 服务测试
│   ├── test_api/                # API测试
│   └── test_utils/              # 工具测试
├── requirements.txt             # 依赖列表
├── requirements-dev.txt         # 开发依赖
├── Dockerfile                   # Docker镜像
└── alembic.ini                  # 数据库迁移配置
```

### 3.3 Go项目结构
```
go/
├── cmd/
│   └── main.go                  # 应用入口
├── internal/
│   ├── config/                  # 配置管理
│   │   ├── config.go
│   │   └── loader.go
│   ├── models/                  # 数据模型
│   │   ├── memory.go
│   │   ├── user.go
│   │   └── system.go
│   ├── services/                # 业务服务
│   │   ├── memory_service.go
│   │   ├── search_service.go
│   │   ├── management_service.go
│   │   └── analysis_service.go
│   ├── api/                     # API接口
│   │   ├── handlers/
│   │   │   ├── memory_handler.go
│   │   │   ├── search_handler.go
│   │   │   ├── management_handler.go
│   │   │   └── analysis_handler.go
│   │   ├── middleware/
│   │   │   ├── auth.go
│   │   │   ├── cors.go
│   │   │   └── logging.go
│   │   └── routes/
│   │       └── routes.go
│   ├── repositories/            # 数据访问层
│   │   ├── memory_repository.go
│   │   ├── user_repository.go
│   │   └── system_repository.go
│   └── utils/                   # 工具函数
│       ├── auth.go
│       ├── crypto.go
│       ├── logger.go
│       └── validators.go
├── pkg/                         # 公共包
│   ├── errors/
│   │   └── errors.go
│   ├── logger/
│   │   └── logger.go
│   └── validator/
│       └── validator.go
├── api/                         # API定义
│   └── proto/
│       ├── memory_service.proto
│       └── search_service.proto
├── tests/                       # 测试目录
│   ├── models/
│   ├── services/
│   ├── api/
│   └── utils/
├── go.mod                       # Go模块
├── go.sum                       # 依赖校验
├── Dockerfile                   # Docker镜像
└── Makefile                     # 构建脚本
```

## 4. 开发环境搭建

### 4.1 本地开发环境
1. **环境要求**
   - 操作系统：Windows 10/11, macOS 10.15+, Ubuntu 18.04+
   - Python：3.9+
   - Go：1.19+
   - Docker：20.10+
   - Git：2.30+

2. **环境搭建步骤**
   ```bash
   # 1. 克隆代码仓库
   git clone https://github.com/your-org/memory-storage-subsystem.git
   cd memory-storage-subsystem
   
   # 2. 设置Python环境
   python3.9 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r python/requirements.txt
   pip install -r python/requirements-dev.txt
   
   # 3. 设置Go环境
   cd go
   go mod download
   go mod tidy
   
   # 4. 启动基础服务
   docker-compose up -d postgres mongodb redis elasticsearch rabbitmq
   
   # 5. 初始化数据库
   cd python
   alembic upgrade head
   
   # 6. 启动应用
   python app/main.py &
   cd ../go
   go run cmd/main.go
   ```

3. **IDE配置**
   - VS Code：
     - 安装Python和Go扩展
     - 配置Python解释器指向虚拟环境
     - 配置Go路径和工具
   - PyCharm：
     - 配置Python解释器
     - 配置Go SDK
     - 配置代码格式化和检查

### 4.2 Docker开发环境
1. **Docker Compose配置**
   ```yaml
   version: '3.8'
   
   services:
     # Python应用
     memory-storage-python:
       build:
         context: ./python
         dockerfile: Dockerfile
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://user:password@postgres:5432/memory_storage
         - MONGODB_URL=mongodb://mongodb:27017/memory_storage
         - REDIS_URL=redis://redis:6379/0
         - ELASTICSEARCH_URL=http://elasticsearch:9200
         - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
       depends_on:
         - postgres
         - mongodb
         - redis
         - elasticsearch
         - rabbitmq
       volumes:
         - ./python:/app
       command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   
     # Go应用
     memory-storage-go:
       build:
         context: ./go
         dockerfile: Dockerfile
       ports:
         - "8080:8080"
       environment:
         - DATABASE_URL=postgresql://user:password@postgres:5432/memory_storage
         - MONGODB_URL=mongodb://mongodb:27017/memory_storage
         - REDIS_URL=redis://redis:6379/0
         - ELASTICSEARCH_URL=http://elasticsearch:9200
         - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
       depends_on:
         - postgres
         - mongodb
         - redis
         - elasticsearch
         - rabbitmq
       volumes:
         - ./go:/app
       command: go run cmd/main.go
   
     # PostgreSQL数据库
     postgres:
       image: postgres:14
       environment:
         - POSTGRES_DB=memory_storage
         - POSTGRES_USER=user
         - POSTGRES_PASSWORD=password
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./scripts/init-postgres.sql:/docker-entrypoint-initdb.d/init.sql
   
     # MongoDB数据库
     mongodb:
       image: mongo:5.0
       environment:
         - MONGO_INITDB_ROOT_USERNAME=root
         - MONGO_INITDB_ROOT_PASSWORD=password
         - MONGO_INITDB_DATABASE=memory_storage
       ports:
         - "27017:27017"
       volumes:
         - mongodb_data:/data/db
         - ./scripts/init-mongo.js:/docker-entrypoint-initdb.d/init.js
   
     # Redis缓存
     redis:
       image: redis:6.0
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
       command: redis-server --appendonly yes
   
     # Elasticsearch搜索引擎
     elasticsearch:
       image: elasticsearch:7.17.0
       environment:
         - discovery.type=single-node
         - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
       ports:
         - "9200:9200"
       volumes:
         - elasticsearch_data:/usr/share/elasticsearch/data
   
     # RabbitMQ消息队列
     rabbitmq:
       image: rabbitmq:3.9-management
       environment:
         - RABBITMQ_DEFAULT_USER=guest
         - RABBITMQ_DEFAULT_PASS=guest
       ports:
         - "5672:5672"
         - "15672:15672"
       volumes:
         - rabbitmq_data:/var/lib/rabbitmq
   
     # Kibana可视化
     kibana:
       image: kibana:7.17.0
       environment:
         - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
       ports:
         - "5601:5601"
       depends_on:
         - elasticsearch
   
     # Prometheus监控
     prometheus:
       image: prom/prometheus:v2.33.0
       ports:
         - "9090:9090"
       volumes:
         - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
         - prometheus_data:/prometheus
   
     # Grafana可视化
     grafana:
       image: grafana/grafana:8.5.0
       ports:
         - "3000:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin
       volumes:
         - grafana_data:/var/lib/grafana
         - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
         - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
   
   volumes:
     postgres_data:
     mongodb_data:
     redis_data:
     elasticsearch_data:
     rabbitmq_data:
     prometheus_data:
     grafana_data:
   ```

2. **Dockerfile配置**
   ```dockerfile
   # Python Dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8000
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

   ```dockerfile
   # Go Dockerfile
   FROM golang:1.19-alpine AS builder
   
   WORKDIR /app
   
   COPY go.mod go.sum ./
   RUN go mod download
   
   COPY . .
   RUN CGO_ENABLED=0 GOOS=linux go build -o main cmd/main.go
   
   FROM alpine:latest
   
   RUN apk --no-cache add ca-certificates
   
   WORKDIR /root/
   
   COPY --from=builder /app/main .
   
   EXPOSE 8080
   
   CMD ["./main"]
   ```

3. **开发环境启动**
   ```bash
   # 启动所有服务
   docker-compose up -d
   
   # 查看服务状态
   docker-compose ps
   
   # 查看日志
   docker-compose logs -f memory-storage-python
   docker-compose logs -f memory-storage-go
   
   # 停止服务
   docker-compose down
   ```

## 5. 核心模块实现

### 5.1 数据接收模块
数据接收模块负责接收来自感知处理子系统和信号转文字子系统的数据。

1. **Python实现**
   ```python
   # app/api/v1/receiver.py
   from fastapi import APIRouter, Depends, HTTPException, status
   from app.schemas.memory import MemoryCreate, MemoryResponse
   from app.services.memory_service import MemoryService
   from app.api.deps import get_memory_service
   
   router = APIRouter()
   
   @router.post("/perception-data", response_model=MemoryResponse)
   async def receive_perception_data(
       data: dict,
       memory_service: MemoryService = Depends(get_memory_service)
   ):
       """接收感知数据"""
       try:
           # 转换感知数据为记忆数据
           memory_data = MemoryCreate(
               type="perception",
               content=data.get("content"),
               metadata=data.get("metadata", {}),
               source="perception_subsystem"
           )
           
           # 存储记忆数据
           memory = await memory_service.create_memory(memory_data)
           return memory
       except Exception as e:
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail=f"Failed to process perception data: {str(e)}"
           )
   
   @router.post("/text-data", response_model=MemoryResponse)
   async def receive_text_data(
       data: dict,
       memory_service: MemoryService = Depends(get_memory_service)
   ):
       """接收文字数据"""
       try:
           # 转换文字数据为记忆数据
           memory_data = MemoryCreate(
               type="text",
               content=data.get("content"),
               metadata=data.get("metadata", {}),
               source="signal_to_text_subsystem"
           )
           
           # 存储记忆数据
           memory = await memory_service.create_memory(memory_data)
           return memory
       except Exception as e:
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail=f"Failed to process text data: {str(e)}"
           )
   ```

2. **Go实现**
   ```go
   // internal/api/handlers/receiver_handler.go
   package handlers
   
   import (
       "net/http"
       "github.com/gin-gonic/gin"
       "memory-storage/internal/services"
   )
   
   type ReceiverHandler struct {
       memoryService services.MemoryService
   }
   
   func NewReceiverHandler(memoryService services.MemoryService) *ReceiverHandler {
       return &ReceiverHandler{
           memoryService: memoryService,
       }
   }
   
   func (h *ReceiverHandler) ReceivePerceptionData(c *gin.Context) {
       var data map[string]interface{}
       if err := c.ShouldBindJSON(&data); err != nil {
           c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
           return
       }
       
       // 转换感知数据为记忆数据
       memoryData := services.MemoryCreate{
           Type:     "perception",
           Content:  data["content"].(string),
           Metadata: data["metadata"].(map[string]interface{}),
           Source:   "perception_subsystem",
       }
       
       // 存储记忆数据
       memory, err := h.memoryService.CreateMemory(memoryData)
       if err != nil {
           c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
           return
       }
       
       c.JSON(http.StatusOK, memory)
   }
   
   func (h *ReceiverHandler) ReceiveTextData(c *gin.Context) {
       var data map[string]interface{}
       if err := c.ShouldBindJSON(&data); err != nil {
           c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
           return
       }
       
       // 转换文字数据为记忆数据
       memoryData := services.MemoryCreate{
           Type:     "text",
           Content:  data["content"].(string),
           Metadata: data["metadata"].(map[string]interface{}),
           Source:   "signal_to_text_subsystem",
       }
       
       // 存储记忆数据
       memory, err := h.memoryService.CreateMemory(memoryData)
       if err != nil {
           c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
           return
       }
       
       c.JSON(http.StatusOK, memory)
   }
   ```

### 5.2 记忆存储模块
记忆存储模块负责记忆数据的存储和管理。

1. **Python实现**
   ```python
   # app/services/memory_service.py
   from typing import List, Optional
   from app.schemas.memory import MemoryCreate, MemoryUpdate, MemoryResponse
   from app.repositories.memory_repository import MemoryRepository
   from app.models.memory import Memory
   from app.utils.logger import get_logger
   
   logger = get_logger(__name__)
   
   class MemoryService:
       def __init__(self, memory_repository: MemoryRepository):
           self.memory_repository = memory_repository
       
       async def create_memory(self, memory_data: MemoryCreate) -> MemoryResponse:
           """创建记忆"""
           try:
               # 创建记忆对象
               memory = Memory(
                   type=memory_data.type,
                   content=memory_data.content,
                   metadata=memory_data.metadata,
                   source=memory_data.source,
                   user_id=memory_data.user_id,
                   tags=memory_data.tags,
                   level=memory_data.level,
                   created_at=datetime.utcnow(),
                   updated_at=datetime.utcnow()
               )
               
               # 保存记忆
               saved_memory = await self.memory_repository.create(memory)
               
               # 异步处理记忆
               await self._process_memory_async(saved_memory)
               
               return MemoryResponse.from_orm(saved_memory)
           except Exception as e:
               logger.error(f"Failed to create memory: {str(e)}")
               raise
       
       async def get_memory(self, memory_id: str) -> Optional[MemoryResponse]:
           """获取记忆"""
           try:
               memory = await self.memory_repository.get_by_id(memory_id)
               if memory:
                   return MemoryResponse.from_orm(memory)
               return None
           except Exception as e:
               logger.error(f"Failed to get memory {memory_id}: {str(e)}")
               raise
       
       async def update_memory(self, memory_id: str, memory_data: MemoryUpdate) -> Optional[MemoryResponse]:
           """更新记忆"""
           try:
               # 获取现有记忆
               memory = await self.memory_repository.get_by_id(memory_id)
               if not memory:
                   return None
               
               # 更新记忆字段
               update_data = memory_data.dict(exclude_unset=True)
               for field, value in update_data.items():
                   setattr(memory, field, value)
               
               memory.updated_at = datetime.utcnow()
               
               # 保存更新
               updated_memory = await self.memory_repository.update(memory)
               
               # 异步处理记忆
               await self._process_memory_async(updated_memory)
               
               return MemoryResponse.from_orm(updated_memory)
           except Exception as e:
               logger.error(f"Failed to update memory {memory_id}: {str(e)}")
               raise
       
       async def delete_memory(self, memory_id: str) -> bool:
           """删除记忆"""
           try:
               result = await self.memory_repository.delete(memory_id)
               return result
           except Exception as e:
               logger.error(f"Failed to delete memory {memory_id}: {str(e)}")
               raise
       
       async def get_memories_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[MemoryResponse]:
           """获取用户记忆列表"""
           try:
               memories = await self.memory_repository.get_by_user_id(user_id, skip, limit)
               return [MemoryResponse.from_orm(memory) for memory in memories]
           except Exception as e:
               logger.error(f"Failed to get memories for user {user_id}: {str(e)}")
               raise
       
       async def _process_memory_async(self, memory: Memory):
           """异步处理记忆"""
           try:
               # 提取特征向量
               if memory.type in ["text", "image", "audio"]:
                   vector = await self._extract_vector(memory)
                   if vector:
                       memory.vector = vector
                       await self.memory_repository.update(memory)
               
               # 更新索引
               await self._update_index(memory)
               
               # 触发分析任务
               await self._trigger_analysis(memory)
           except Exception as e:
               logger.error(f"Failed to process memory {memory.id}: {str(e)}")
       
       async def _extract_vector(self, memory: Memory) -> Optional[List[float]]:
           """提取记忆特征向量"""
           # 这里实现特征提取逻辑
           # 可以调用AI模型提取特征向量
           return None
       
       async def _update_index(self, memory: Memory):
           """更新搜索索引"""
           # 这里实现索引更新逻辑
           pass
       
       async def _trigger_analysis(self, memory: Memory):
           """触发分析任务"""
           # 这里实现分析任务触发逻辑
           pass
   ```

2. **Go实现**
   ```go
   // internal/services/memory_service.go
   package services
   
   import (
       "context"
       "time"
       "memory-storage/internal/models"
       "memory-storage/internal/repositories"
   )
   
   type MemoryService interface {
       CreateMemory(ctx context.Context, memoryData MemoryCreate) (*models.Memory, error)
       GetMemory(ctx context.Context, memoryID string) (*models.Memory, error)
       UpdateMemory(ctx context.Context, memoryID string, memoryData MemoryUpdate) (*models.Memory, error)
       DeleteMemory(ctx context.Context, memoryID string) error
       GetMemoriesByUser(ctx context.Context, userID string, skip, limit int) ([]*models.Memory, error)
   }
   
   type memoryService struct {
       memoryRepo repositories.MemoryRepository
   }
   
   func NewMemoryService(memoryRepo repositories.MemoryRepository) MemoryService {
       return &memoryService{
           memoryRepo: memoryRepo,
       }
   }
   
   func (s *memoryService) CreateMemory(ctx context.Context, memoryData MemoryCreate) (*models.Memory, error) {
       // 创建记忆对象
       memory := &models.Memory{
           Type:      memoryData.Type,
           Content:   memoryData.Content,
           Metadata:  memoryData.Metadata,
           Source:    memoryData.Source,
           UserID:    memoryData.UserID,
           Tags:      memoryData.Tags,
           Level:     memoryData.Level,
           CreatedAt: time.Now(),
           UpdatedAt: time.Now(),
       }
       
       // 保存记忆
       savedMemory, err := s.memoryRepo.Create(ctx, memory)
       if err != nil {
           return nil, err
       }
       
       // 异步处理记忆
       go s.processMemoryAsync(savedMemory)
       
       return savedMemory, nil
   }
   
   func (s *memoryService) GetMemory(ctx context.Context, memoryID string) (*models.Memory, error) {
       return s.memoryRepo.GetByID(ctx, memoryID)
   }
   
   func (s *memoryService) UpdateMemory(ctx context.Context, memoryID string, memoryData MemoryUpdate) (*models.Memory, error) {
       // 获取现有记忆
       memory, err := s.memoryRepo.GetByID(ctx, memoryID)
       if err != nil {
           return nil, err
       }
       
       // 更新记忆字段
       if memoryData.Type != nil {
           memory.Type = *memoryData.Type
       }
       if memoryData.Content != nil {
           memory.Content = *memoryData.Content
       }
       if memoryData.Metadata != nil {
           memory.Metadata = memoryData.Metadata
       }
       if memoryData.Tags != nil {
           memory.Tags = memoryData.Tags
       }
       if memoryData.Level != nil {
           memory.Level = *memoryData.Level
       }
       
       memory.UpdatedAt = time.Now()
       
       // 保存更新
       updatedMemory, err := s.memoryRepo.Update(ctx, memory)
       if err != nil {
           return nil, err
       }
       
       // 异步处理记忆
       go s.processMemoryAsync(updatedMemory)
       
       return updatedMemory, nil
   }
   
   func (s *memoryService) DeleteMemory(ctx context.Context, memoryID string) error {
       return s.memoryRepo.Delete(ctx, memoryID)
   }
   
   func (s *memoryService) GetMemoriesByUser(ctx context.Context, userID string, skip, limit int) ([]*models.Memory, error) {
       return s.memoryRepo.GetByUserID(ctx, userID, skip, limit)
   }
   
   func (s *memoryService) processMemoryAsync(memory *models.Memory) {
       // 提取特征向量
       if memory.Type == "text" || memory.Type == "image" || memory.Type == "audio" {
           vector, err := s.extractVector(memory)
           if err == nil && vector != nil {
               memory.Vector = vector
               s.memoryRepo.Update(context.Background(), memory)
           }
       }
       
       // 更新索引
       s.updateIndex(memory)
       
       // 触发分析任务
       s.triggerAnalysis(memory)
   }
   
   func (s *memoryService) extractVector(memory *models.Memory) ([]float32, error) {
       // 这里实现特征提取逻辑
       // 可以调用AI模型提取特征向量
       return nil, nil
   }
   
   func (s *memoryService) updateIndex(memory *models.Memory) {
       // 这里实现索引更新逻辑
   }
   
   func (s *memoryService) triggerAnalysis(memory *models.Memory) {
       // 这里实现分析任务触发逻辑
   }
   ```

### 5.3 多模态融合模块
多模态融合模块负责将不同类型的记忆数据进行融合处理。

1. **Python实现**
   ```python
   # app/services/fusion_service.py
   from typing import List, Dict, Any
   from app.models.memory import Memory
   from app.utils.logger import get_logger
   
   logger = get_logger(__name__)
   
   class FusionService:
       def __init__(self):
           self.fusion_strategies = {
               "text_image": self._fuse_text_image,
               "text_audio": self._fuse_text_audio,
               "image_audio": self._fuse_image_audio,
               "text_image_audio": self._fuse_text_image_audio,
           }
       
       async def fuse_memories(self, memories: List[Memory], fusion_type: str) -> Dict[str, Any]:
           """融合记忆数据"""
           try:
               if fusion_type not in self.fusion_strategies:
                   raise ValueError(f"Unsupported fusion type: {fusion_type}")
               
               fusion_func = self.fusion_strategies[fusion_type]
               return await fusion_func(memories)
           except Exception as e:
               logger.error(f"Failed to fuse memories: {str(e)}")
               raise
       
       async def _fuse_text_image(self, memories: List[Memory]) -> Dict[str, Any]:
           """融合文本和图像记忆"""
           text_memories = [m for m in memories if m.type == "text"]
           image_memories = [m for m in memories if m.type == "image"]
           
           if not text_memories or not image_memories:
               raise ValueError("Both text and image memories are required for text-image fusion")
           
           # 提取文本特征
           text_features = await self._extract_text_features(text_memories)
           
           # 提取图像特征
           image_features = await self._extract_image_features(image_memories)
           
           # 融合特征
           fused_features = await self._combine_features(text_features, image_features)
           
           # 创建融合记忆
           fused_memory = {
               "type": "text_image_fusion",
               "content": {
                   "text": [m.content for m in text_memories],
                   "image": [m.content for m in image_memories],
               },
               "features": fused_features,
               "source_memories": [m.id for m in memories],
               "metadata": {
                   "fusion_type": "text_image",
                   "fusion_timestamp": datetime.utcnow().isoformat(),
               }
           }
           
           return fused_memory
       
       async def _fuse_text_audio(self, memories: List[Memory]) -> Dict[str, Any]:
           """融合文本和音频记忆"""
           text_memories = [m for m in memories if m.type == "text"]
           audio_memories = [m for m in memories if m.type == "audio"]
           
           if not text_memories or not audio_memories:
               raise ValueError("Both text and audio memories are required for text-audio fusion")
           
           # 提取文本特征
           text_features = await self._extract_text_features(text_memories)
           
           # 提取音频特征
           audio_features = await self._extract_audio_features(audio_memories)
           
           # 融合特征
           fused_features = await self._combine_features(text_features, audio_features)
           
           # 创建融合记忆
           fused_memory = {
               "type": "text_audio_fusion",
               "content": {
                   "text": [m.content for m in text_memories],
                   "audio": [m.content for m in audio_memories],
               },
               "features": fused_features,
               "source_memories": [m.id for m in memories],
               "metadata": {
                   "fusion_type": "text_audio",
                   "fusion_timestamp": datetime.utcnow().isoformat(),
               }
           }
           
           return fused_memory
       
       async def _fuse_image_audio(self, memories: List[Memory]) -> Dict[str, Any]:
           """融合图像和音频记忆"""
           image_memories = [m for m in memories if m.type == "image"]
           audio_memories = [m for m in memories if m.type == "audio"]
           
           if not image_memories or not audio_memories:
               raise ValueError("Both image and audio memories are required for image-audio fusion")
           
           # 提取图像特征
           image_features = await self._extract_image_features(image_memories)
           
           # 提取音频特征
           audio_features = await self._extract_audio_features(audio_memories)
           
           # 融合特征
           fused_features = await self._combine_features(image_features, audio_features)
           
           # 创建融合记忆
           fused_memory = {
               "type": "image_audio_fusion",
               "content": {
                   "image": [m.content for m in image_memories],
                   "audio": [m.content for m in audio_memories],
               },
               "features": fused_features,
               "source_memories": [m.id for m in memories],
               "metadata": {
                   "fusion_type": "image_audio",
                   "fusion_timestamp": datetime.utcnow().isoformat(),
               }
           }
           
           return fused_memory
       
       async def _fuse_text_image_audio(self, memories: List[Memory]) -> Dict[str, Any]:
           """融合文本、图像和音频记忆"""
           text_memories = [m for m in memories if m.type == "text"]
           image_memories = [m for m in memories if m.type == "image"]
           audio_memories = [m for m in memories if m.type == "audio"]
           
           if not text_memories or not image_memories or not audio_memories:
               raise ValueError("Text, image and audio memories are all required for text-image-audio fusion")
           
           # 提取各类特征
           text_features = await self._extract_text_features(text_memories)
           image_features = await self._extract_image_features(image_memories)
           audio_features = await self._extract_audio_features(audio_memories)
           
           # 融合特征
           fused_features = await self._combine_features(text_features, image_features, audio_features)
           
           # 创建融合记忆
           fused_memory = {
               "type": "text_image_audio_fusion",
               "content": {
                   "text": [m.content for m in text_memories],
                   "image": [m.content for m in image_memories],
                   "audio": [m.content for m in audio_memories],
               },
               "features": fused_features,
               "source_memories": [m.id for m in memories],
               "metadata": {
                   "fusion_type": "text_image_audio",
                   "fusion_timestamp": datetime.utcnow().isoformat(),
               }
           }
           
           return fused_memory
       
       async def _extract_text_features(self, memories: List[Memory]) -> List[float]:
           """提取文本特征"""
           # 这里实现文本特征提取逻辑
           return []
       
       async def _extract_image_features(self, memories: List[Memory]) -> List[float]:
           """提取图像特征"""
           # 这里实现图像特征提取逻辑
           return []
       
       async def _extract_audio_features(self, memories: List[Memory]) -> List[float]:
           """提取音频特征"""
           # 这里实现音频特征提取逻辑
           return []
       
       async def _combine_features(self, *feature_lists: List[float]) -> List[float]:
           """组合特征"""
           # 这里实现特征组合逻辑
           combined = []
           for features in feature_lists:
               combined.extend(features)
           return combined
   ```

2. **Go实现**
   ```go
   // internal/services/fusion_service.go
   package services
   
   import (
       "context"
       "time"
       "memory-storage/internal/models"
   )
   
   type FusionService interface {
       FuseMemories(ctx context.Context, memories []*models.Memory, fusionType string) (map[string]interface{}, error)
   }
   
   type fusionService struct {
       fusionStrategies map[string]func(ctx context.Context, memories []*models.Memory) (map[string]interface{}, error)
   }
   
   func NewFusionService() FusionService {
       s := &fusionService{
           fusionStrategies: make(map[string]func(ctx context.Context, memories []*models.Memory) (map[string]interface{}, error)),
       }
       
       s.fusionStrategies["text_image"] = s.fuseTextImage
       s.fusionStrategies["text_audio"] = s.fuseTextAudio
       s.fusionStrategies["image_audio"] = s.fuseImageAudio
       s.fusionStrategies["text_image_audio"] = s.fuseTextImageAudio
       
       return s
   }
   
   func (s *fusionService) FuseMemories(ctx context.Context, memories []*models.Memory, fusionType string) (map[string]interface{}, error) {
       strategy, exists := s.fusionStrategies[fusionType]
       if !exists {
           return nil, fmt.Errorf("unsupported fusion type: %s", fusionType)
       }
       
       return strategy(ctx, memories)
   }
   
   func (s *fusionService) fuseTextImage(ctx context.Context, memories []*models.Memory) (map[string]interface{}, error) {
       var textMemories, imageMemories []*models.Memory
       
       for _, memory := range memories {
           if memory.Type == "text" {
               textMemories = append(textMemories, memory)
           } else if memory.Type == "image" {
               imageMemories = append(imageMemories, memory)
           }
       }
       
       if len(textMemories) == 0 || len(imageMemories) == 0 {
           return nil, fmt.Errorf("both text and image memories are required for text-image fusion")
       }
       
       // 提取文本特征
       textFeatures, err := s.extractTextFeatures(ctx, textMemories)
       if err != nil {
           return nil, err
       }
       
       // 提取图像特征
       imageFeatures, err := s.extractImageFeatures(ctx, imageMemories)
       if err != nil {
           return nil, err
       }
       
       // 融合特征
       fusedFeatures := s.combineFeatures(textFeatures, imageFeatures)
       
       // 创建融合记忆
       fusedMemory := map[string]interface{}{
           "type": "text_image_fusion",
           "content": map[string]interface{}{
               "text":  s.extractContents(textMemories),
               "image": s.extractContents(imageMemories),
           },
           "features": fusedFeatures,
           "source_memories": s.extractIDs(memories),
           "metadata": map[string]interface{}{
               "fusion_type":       "text_image",
               "fusion_timestamp": time.Now().Format(time.RFC3339),
           },
       }
       
       return fusedMemory, nil
   }
   
   func (s *fusionService) fuseTextAudio(ctx context.Context, memories []*models.Memory) (map[string]interface{}, error) {
       var textMemories, audioMemories []*models.Memory
       
       for _, memory := range memories {
           if memory.Type == "text" {
               textMemories = append(textMemories, memory)
           } else if memory.Type == "audio" {
               audioMemories = append(audioMemories, memory)
           }
       }
       
       if len(textMemories) == 0 || len(audioMemories) == 0 {
           return nil, fmt.Errorf("both text and audio memories are required for text-audio fusion")
       }
       
       // 提取文本特征
       textFeatures, err := s.extractTextFeatures(ctx, textMemories)
       if err != nil {
           return nil, err
       }
       
       // 提取音频特征
       audioFeatures, err := s.extractAudioFeatures(ctx, audioMemories)
       if err != nil {
           return nil, err
       }
       
       // 融合特征
       fusedFeatures := s.combineFeatures(textFeatures, audioFeatures)
       
       // 创建融合记忆
       fusedMemory := map[string]interface{}{
           "type": "text_audio_fusion",
           "content": map[string]interface{}{
               "text":  s.extractContents(textMemories),
               "audio": s.extractContents(audioMemories),
           },
           "features": fusedFeatures,
           "source_memories": s.extractIDs(memories),
           "metadata": map[string]interface{}{
               "fusion_type":       "text_audio",
               "fusion_timestamp": time.Now().Format(time.RFC3339),
           },
       }
       
       return fusedMemory, nil
   }
   
   func (s *fusionService) fuseImageAudio(ctx context.Context, memories []*models.Memory) (map[string]interface{}, error) {
       var imageMemories, audioMemories []*models.Memory
       
       for _, memory := range memories {
           if memory.Type == "image" {
               imageMemories = append(imageMemories, memory)
           } else if memory.Type == "audio" {
               audioMemories = append(audioMemories, memory)
           }
       }
       
       if len(imageMemories) == 0 || len(audioMemories) == 0 {
           return nil, fmt.Errorf("both image and audio memories are required for image-audio fusion")
       }
       
       // 提取图像特征
       imageFeatures, err := s.extractImageFeatures(ctx, imageMemories)
       if err != nil {
           return nil, err
       }
       
       // 提取音频特征
       audioFeatures, err := s.extractAudioFeatures(ctx, audioMemories)
       if err != nil {
           return nil, err
       }
       
       // 融合特征
       fusedFeatures := s.combineFeatures(imageFeatures, audioFeatures)
       
       // 创建融合记忆
       fusedMemory := map[string]interface{}{
           "type": "image_audio_fusion",
           "content": map[string]interface{}{
               "image": s.extractContents(imageMemories),
               "audio": s.extractContents(audioMemories),
           },
           "features": fusedFeatures,
           "source_memories": s.extractIDs(memories),
           "metadata": map[string]interface{}{
               "fusion_type":       "image_audio",
               "fusion_timestamp": time.Now().Format(time.RFC3339),
           },
       }
       
       return fusedMemory, nil
   }
   
   func (s *fusionService) fuseTextImageAudio(ctx context.Context, memories []*models.Memory) (map[string]interface{}, error) {
       var textMemories, imageMemories, audioMemories []*models.Memory
       
       for _, memory := range memories {
           if memory.Type == "text" {
               textMemories = append(textMemories, memory)
           } else if memory.Type == "image" {
               imageMemories = append(imageMemories, memory)
           } else if memory.Type == "audio" {
               audioMemories = append(audioMemories, memory)
           }
       }
       
       if len(textMemories) == 0 || len(imageMemories) == 0 || len(audioMemories) == 0 {
           return nil, fmt.Errorf("text, image and audio memories are all required for text-image-audio fusion")
       }
       
       // 提取各类特征
       textFeatures, err := s.extractTextFeatures(ctx, textMemories)
       if err != nil {
           return nil, err
       }
       
       imageFeatures, err := s.extractImageFeatures(ctx, imageMemories)
       if err != nil {
           return nil, err
       }
       
       audioFeatures, err := s.extractAudioFeatures(ctx, audioMemories)
       if err != nil {
           return nil, err
       }
       
       // 融合特征
       fusedFeatures := s.combineFeatures(textFeatures, imageFeatures, audioFeatures)
       
       // 创建融合记忆
       fusedMemory := map[string]interface{}{
           "type": "text_image_audio_fusion",
           "content": map[string]interface{}{
               "text":  s.extractContents(textMemories),
               "image": s.extractContents(imageMemories),
               "audio": s.extractContents(audioMemories),
           },
           "features": fusedFeatures,
           "source_memories": s.extractIDs(memories),
           "metadata": map[string]interface{}{
               "fusion_type":       "text_image_audio",
               "fusion_timestamp": time.Now().Format(time.RFC3339),
           },
       }
       
       return fusedMemory, nil
   }
   
   func (s *fusionService) extractTextFeatures(ctx context.Context, memories []*models.Memory) ([]float32, error) {
       // 这里实现文本特征提取逻辑
       return nil, nil
   }
   
   func (s *fusionService) extractImageFeatures(ctx context.Context, memories []*models.Memory) ([]float32, error) {
       // 这里实现图像特征提取逻辑
       return nil, nil
   }
   
   func (s *fusionService) extractAudioFeatures(ctx context.Context, memories []*models.Memory) ([]float32, error) {
       // 这里实现音频特征提取逻辑
       return nil, nil
   }
   
   func (s *fusionService) combineFeatures(featureLists ...[]float32) []float32 {
       // 这里实现特征组合逻辑
       var combined []float32
       for _, features := range featureLists {
           combined = append(combined, features...)
       }
       return combined
   }
   
   func (s *fusionService) extractContents(memories []*models.Memory) []string {
       var contents []string
       for _, memory := range memories {
           contents = append(contents, memory.Content)
       }
       return contents
   }
   
   func (s *fusionService) extractIDs(memories []*models.Memory) []string {
       var ids []string
       for _, memory := range memories {
           ids = append(ids, memory.ID)
       }
       return ids
   }
   ```

### 5.4 记忆检索模块
记忆检索模块负责根据查询条件检索相关的记忆数据。

1. **Python实现**
   ```python
   # app/services/search_service.py
   from typing import List, Dict, Any, Optional
   from app.schemas.search import SearchQuery, SearchResult
   from app.repositories.memory_repository import MemoryRepository
   from app.models.memory import Memory
   from app.utils.logger import get_logger
   
   logger = get_logger(__name__)
   
   class SearchService:
       def __init__(self, memory_repository: MemoryRepository):
           self.memory_repository = memory_repository
           self.search_strategies = {
               "full_text": self._full_text_search,
               "vector": self._vector_search,
               "hybrid": self._hybrid_search,
           }
       
       async def search_memories(self, query: SearchQuery) -> SearchResult:
           """搜索记忆"""
           try:
               if query.search_type not in self.search_strategies:
                   raise ValueError(f"Unsupported search type: {query.search_type}")
               
               search_func = self.search_strategies[query.search_type]
               memories = await search_func(query)
               
               # 计算总分页信息
               total = len(memories)
               start = query.skip
               end = start + query.limit
               if end > total:
                   end = total
               
               paginated_memories = memories[start:end]
               
               return SearchResult(
                   memories=paginated_memories,
                   total=total,
                   skip=query.skip,
                   limit=query.limit,
               )
           except Exception as e:
               logger.error(f"Failed to search memories: {str(e)}")
               raise
       
       async def _full_text_search(self, query: SearchQuery) -> List[Memory]:
           """全文搜索"""
           try:
               # 构建全文搜索查询
               search_query = {
                   "query": {
                       "multi_match": {
                           "query": query.text,
                           "fields": ["content", "metadata.title", "metadata.description"],
                           "type": "best_fields",
                           "fuzziness": "AUTO"
                       }
                   },
                   "filter": []
               }
               
               # 添加过滤条件
               if query.user_id:
                   search_query["filter"].append({"term": {"user_id": query.user_id}})
               
               if query.type:
                   search_query["filter"].append({"term": {"type": query.type}})
               
               if query.tags:
                   search_query["filter"].append({"terms": {"tags": query.tags}})
               
               if query.level:
                   search_query["filter"].append({"term": {"level": query.level}})
               
               if query.date_range:
                   date_filter = {"range": {"created_at": {}}}
                   if query.date_range.start:
                       date_filter["range"]["created_at"]["gte"] = query.date_range.start
                   if query.date_range.end:
                       date_filter["range"]["created_at"]["lte"] = query.date_range.end
                   search_query["filter"].append(date_filter)
               
               # 执行搜索
               memories = await self.memory_repository.search(search_query)
               
               return memories
           except Exception as e:
               logger.error(f"Failed to perform full text search: {str(e)}")
               raise
       
       async def _vector_search(self, query: SearchQuery) -> List[Memory]:
           """向量搜索"""
           try:
               if not query.vector:
                   raise ValueError("Vector is required for vector search")
               
               # 执行向量搜索
               memories = await self.memory_repository.vector_search(
                   vector=query.vector,
                   user_id=query.user_id,
                   type=query.type,
                   tags=query.tags,
                   level=query.level,
                   limit=query.limit + query.skip
               )
               
               return memories
           except Exception as e:
               logger.error(f"Failed to perform vector search: {str(e)}")
               raise
       
       async def _hybrid_search(self, query: SearchQuery) -> List[Memory]:
           """混合搜索"""
           try:
               if not query.vector:
                   raise ValueError("Vector is required for hybrid search")
               
               # 执行全文搜索
               text_results = await self._full_text_search(query)
               
               # 执行向量搜索
               vector_results = await self._vector_search(query)
               
               # 合并结果
               text_ids = {memory.id for memory in text_results}
               vector_ids = {memory.id for memory in vector_results}
               
               # 找出交集
               common_ids = text_ids.intersection(vector_ids)
               
               # 找出并集
               all_ids = text_ids.union(vector_ids)
               
               # 为每个记忆计算综合分数
               memory_scores = {}
               
               # 全文搜索结果分数
               for i, memory in enumerate(text_results):
                   memory_scores[memory.id] = {
                       "memory": memory,
                       "text_score": 1.0 - (i / len(text_results)),
                       "vector_score": 0.0,
                   }
               
               # 向量搜索结果分数
               for i, memory in enumerate(vector_results):
                   if memory.id in memory_scores:
                       memory_scores[memory.id]["vector_score"] = 1.0 - (i / len(vector_results))
                   else:
                       memory_scores[memory.id] = {
                           "memory": memory,
                           "text_score": 0.0,
                           "vector_score": 1.0 - (i / len(vector_results)),
                       }
               
               # 计算综合分数
               hybrid_results = []
               for memory_id, scores in memory_scores.items():
                   # 综合分数 = 0.6 * 文本分数 + 0.4 * 向量分数
                   hybrid_score = 0.6 * scores["text_score"] + 0.4 * scores["vector_score"]
                   hybrid_results.append((scores["memory"], hybrid_score))
               
               # 按综合分数排序
               hybrid_results.sort(key=lambda x: x[1], reverse=True)
               
               # 返回排序后的记忆
               return [memory for memory, _ in hybrid_results]
           except Exception as e:
               logger.error(f"Failed to perform hybrid search: {str(e)}")
               raise
       
       async def recommend_memories(self, user_id: str, context: Dict[str, Any], limit: int = 10) -> List[Memory]:
           """推荐记忆"""
           try:
               # 基于上下文提取关键词
               keywords = self._extract_keywords(context)
               
               # 基于用户历史行为获取偏好
               preferences = await self._get_user_preferences(user_id)
               
               # 构建推荐查询
               query = SearchQuery(
                   text=" ".join(keywords),
                   user_id=user_id,
                   search_type="hybrid",
                   limit=limit,
                   skip=0
               )
               
               # 执行搜索
               result = await self.search_memories(query)
               
               # 基于偏好重新排序
               recommended_memories = self._rerank_by_preferences(result.memories, preferences)
               
               return recommended_memories
           except Exception as e:
               logger.error(f"Failed to recommend memories: {str(e)}")
               raise
       
       async def similar_memories(self, memory_id: str, limit: int = 10) -> List[Memory]:
           """查找相似记忆"""
           try:
               # 获取原记忆
               memory = await self.memory_repository.get_by_id(memory_id)
               if not memory:
                   return []
               
               # 如果记忆有向量，使用向量搜索
               if memory.vector:
                   query = SearchQuery(
                       vector=memory.vector,
                       search_type="vector",
                       limit=limit + 1,  # +1 因为会包含自己
                       skip=0
                   )
                   
                   result = await self.search_memories(query)
                   
                   # 过滤掉自己
                   similar_memories = [m for m in result.memories if m.id != memory_id]
                   
                   return similar_memories[:limit]
               else:
                   # 否则使用全文搜索
                   query = SearchQuery(
                       text=memory.content,
                       search_type="full_text",
                       limit=limit + 1,  # +1 因为会包含自己
                       skip=0
                   )
                   
                   result = await self.search_memories(query)
                   
                   # 过滤掉自己
                   similar_memories = [m for m in result.memories if m.id != memory_id]
                   
                   return similar_memories[:limit]
           except Exception as e:
               logger.error(f"Failed to find similar memories: {str(e)}")
               raise
       
       def _extract_keywords(self, context: Dict[str, Any]) -> List[str]:
           """从上下文中提取关键词"""
           # 这里实现关键词提取逻辑
           return []
       
       async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
           """获取用户偏好"""
           # 这里实现用户偏好获取逻辑
           return {}
       
       def _rerank_by_preferences(self, memories: List[Memory], preferences: Dict[str, Any]) -> List[Memory]:
           """基于偏好重新排序"""
           # 这里实现基于偏好的重新排序逻辑
           return memories
   ```

2. **Go实现**
   ```go
   // internal/services/search_service.go
   package services
   
   import (
       "context"
       "fmt"
       "memory-storage/internal/models"
       "memory-storage/internal/repositories"
   )
   
   type SearchService interface {
       SearchMemories(ctx context.Context, query SearchQuery) (*SearchResult, error)
       RecommendMemories(ctx context.Context, userID string, context map[string]interface{}, limit int) ([]*models.Memory, error)
       SimilarMemories(ctx context.Context, memoryID string, limit int) ([]*models.Memory, error)
   }
   
   type searchService struct {
       memoryRepo repositories.MemoryRepository
       searchStrategies map[string]func(ctx context.Context, query SearchQuery) ([]*models.Memory, error)
   }
   
   func NewSearchService(memoryRepo repositories.MemoryRepository) SearchService {
       s := &searchService{
           memoryRepo: memoryRepo,
           searchStrategies: make(map[string]func(ctx context.Context, query SearchQuery) ([]*models.Memory, error)),
       }
       
       s.searchStrategies["full_text"] = s.fullTextSearch
       s.searchStrategies["vector"] = s.vectorSearch
       s.searchStrategies["hybrid"] = s.hybridSearch
       
       return s
   }
   
   func (s *searchService) SearchMemories(ctx context.Context, query SearchQuery) (*SearchResult, error) {
       strategy, exists := s.searchStrategies[query.SearchType]
       if !exists {
           return nil, fmt.Errorf("unsupported search type: %s", query.SearchType)
       }
       
       memories, err := strategy(ctx, query)
       if err != nil {
           return nil, err
       }
       
       // 计算总分页信息
       total := len(memories)
       start := query.Skip
       end := start + query.Limit
       if end > total {
           end = total
       }
       
       var paginatedMemories []*models.Memory
       if start < total {
           paginatedMemories = memories[start:end]
       }
       
       return &SearchResult{
           Memories: paginatedMemories,
           Total:    total,
           Skip:     query.Skip,
           Limit:    query.Limit,
       }, nil
   }
   
   func (s *searchService) fullTextSearch(ctx context.Context, query SearchQuery) ([]*models.Memory, error) {
       // 构建全文搜索查询
       searchQuery := map[string]interface{}{
           "query": map[string]interface{}{
               "multi_match": map[string]interface{}{
                   "query":  query.Text,
                   "fields": []string{"content", "metadata.title", "metadata.description"},
                   "type":   "best_fields",
                   "fuzziness": "AUTO",
               },
           },
           "filter": []map[string]interface{}{},
       }
       
       // 添加过滤条件
       if query.UserID != "" {
           searchQuery["filter"] = append(searchQuery["filter"].([]map[string]interface{}), map[string]interface{}{
               "term": map[string]interface{}{
                   "user_id": query.UserID,
               },
           })
       }
       
       if query.Type != "" {
           searchQuery["filter"] = append(searchQuery["filter"].([]map[string]interface{}), map[string]interface{}{
               "term": map[string]interface{}{
                   "type": query.Type,
               },
           })
       }
       
       if len(query.Tags) > 0 {
           searchQuery["filter"] = append(searchQuery["filter"].([]map[string]interface{}), map[string]interface{}{
               "terms": map[string]interface{}{
                   "tags": query.Tags,
               },
           })
       }
       
       if query.Level != "" {
           searchQuery["filter"] = append(searchQuery["filter"].([]map[string]interface{}), map[string]interface{}{
               "term": map[string]interface{}{
                   "level": query.Level,
               },
           })
       }
       
       if query.DateRange != nil {
           dateFilter := map[string]interface{}{
               "range": map[string]interface{}{
                   "created_at": map[string]interface{}{},
               },
           }
           
           if !query.DateRange.Start.IsZero() {
               dateFilter["range"].(map[string]interface{})["created_at"].(map[string]interface{})["gte"] = query.DateRange.Start
           }
           
           if !query.DateRange.End.IsZero() {
               dateFilter["range"].(map[string]interface{})["created_at"].(map[string]interface{})["lte"] = query.DateRange.End
           }
           
           searchQuery["filter"] = append(searchQuery["filter"].([]map[string]interface{}), dateFilter)
       }
       
       // 执行搜索
       memories, err := s.memoryRepo.Search(ctx, searchQuery)
       if err != nil {
           return nil, fmt.Errorf("failed to perform full text search: %w", err)
       }
       
       return memories, nil
   }
   
   func (s *searchService) vectorSearch(ctx context.Context, query SearchQuery) ([]*models.Memory, error) {
       if len(query.Vector) == 0 {
           return nil, fmt.Errorf("vector is required for vector search")
       }
       
       // 执行向量搜索
       memories, err := s.memoryRepo.VectorSearch(ctx, repositories.VectorSearchRequest{
           Vector:  query.Vector,
           UserID:  query.UserID,
           Type:    query.Type,
           Tags:    query.Tags,
           Level:   query.Level,
           Limit:   query.Limit + query.Skip,
       })
       if err != nil {
           return nil, fmt.Errorf("failed to perform vector search: %w", err)
       }
       
       return memories, nil
   }
   
   func (s *searchService) hybridSearch(ctx context.Context, query SearchQuery) ([]*models.Memory, error) {
       if len(query.Vector) == 0 {
           return nil, fmt.Errorf("vector is required for hybrid search")
       }
       
       // 执行全文搜索
       textResults, err := s.fullTextSearch(ctx, query)
       if err != nil {
           return nil, fmt.Errorf("failed to perform text search in hybrid search: %w", err)
       }
       
       // 执行向量搜索
       vectorResults, err := s.vectorSearch(ctx, query)
       if err != nil {
           return nil, fmt.Errorf("failed to perform vector search in hybrid search: %w", err)
       }
       
       // 合并结果
       textIDs := make(map[string]bool)
       for _, memory := range textResults {
           textIDs[memory.ID] = true
       }
       
       vectorIDs := make(map[string]bool)
       for _, memory := range vectorResults {
           vectorIDs[memory.ID] = true
       }
       
       // 为每个记忆计算综合分数
       memoryScores := make(map[string]*MemoryScore)
       
       // 全文搜索结果分数
       for i, memory := range textResults {
           memoryScores[memory.ID] = &MemoryScore{
               Memory:     memory,
               TextScore:  1.0 - (float64(i) / float64(len(textResults))),
               VectorScore: 0.0,
           }
       }
       
       // 向量搜索结果分数
       for i, memory := range vectorResults {
           if score, exists := memoryScores[memory.ID]; exists {
               score.VectorScore = 1.0 - (float64(i) / float64(len(vectorResults)))
           } else {
               memoryScores[memory.ID] = &MemoryScore{
                   Memory:     memory,
                   TextScore:  0.0,
                   VectorScore: 1.0 - (float64(i) / float64(len(vectorResults))),
               }
           }
       }
       
       // 计算综合分数并排序
       hybridResults := make([]*MemoryWithScore, 0, len(memoryScores))
       for _, score := range memoryScores {
           // 综合分数 = 0.6 * 文本分数 + 0.4 * 向量分数
           hybridScore := 0.6*score.TextScore + 0.4*score.VectorScore
           hybridResults = append(hybridResults, &MemoryWithScore{
               Memory: score.Memory,
               Score:  hybridScore,
           })
       }
       
       // 按综合分数排序
       sort.Slice(hybridResults, func(i, j int) bool {
           return hybridResults[i].Score > hybridResults[j].Score
       })
       
       // 返回排序后的记忆
       memories := make([]*models.Memory, len(hybridResults))
       for i, result := range hybridResults {
           memories[i] = result.Memory
       }
       
       return memories, nil
   }
   
   func (s *searchService) RecommendMemories(ctx context.Context, userID string, context map[string]interface{}, limit int) ([]*models.Memory, error) {
       // 基于上下文提取关键词
       keywords := s.extractKeywords(context)
       
       // 基于用户历史行为获取偏好
       preferences, err := s.getUserPreferences(ctx, userID)
       if err != nil {
           return nil, fmt.Errorf("failed to get user preferences: %w", err)
       }
       
       // 构建推荐查询
       query := SearchQuery{
           Text:       strings.Join(keywords, " "),
           UserID:     userID,
           SearchType: "hybrid",
           Limit:      limit,
           Skip:       0,
       }
       
       // 执行搜索
       result, err := s.SearchMemories(ctx, query)
       if err != nil {
           return nil, fmt.Errorf("failed to search memories for recommendation: %w", err)
       }
       
       // 基于偏好重新排序
       recommendedMemories := s.rerankByPreferences(result.Memories, preferences)
       
       return recommendedMemories, nil
   }
   
   func (s *searchService) SimilarMemories(ctx context.Context, memoryID string, limit int) ([]*models.Memory, error) {
       // 获取原记忆
       memory, err := s.memoryRepo.GetByID(ctx, memoryID)
       if err != nil {
           return nil, fmt.Errorf("failed to get memory: %w", err)
       }
       
       if memory == nil {
           return nil, nil
       }
       
       // 如果记忆有向量，使用向量搜索
       if len(memory.Vector) > 0 {
           query := SearchQuery{
               Vector:     memory.Vector,
               SearchType: "vector",
               Limit:      limit + 1, // +1 因为会包含自己
               Skip:       0,
           }
           
           result, err := s.SearchMemories(ctx, query)
           if err != nil {
               return nil, fmt.Errorf("failed to search similar memories: %w", err)
           }
           
           // 过滤掉自己
           var similarMemories []*models.Memory
           for _, m := range result.Memories {
               if m.ID != memoryID {
                   similarMemories = append(similarMemories, m)
               }
           }
           
           if len(similarMemories) > limit {
               similarMemories = similarMemories[:limit]
           }
           
           return similarMemories, nil
       } else {
           // 否则使用全文搜索
           query := SearchQuery{
               Text:       memory.Content,
               SearchType: "full_text",
               Limit:      limit + 1, // +1 因为会包含自己
               Skip:       0,
           }
           
           result, err := s.SearchMemories(ctx, query)
           if err != nil {
               return nil, fmt.Errorf("failed to search similar memories: %w", err)
           }
           
           // 过滤掉自己
           var similarMemories []*models.Memory
           for _, m := range result.Memories {
               if m.ID != memoryID {
                   similarMemories = append(similarMemories, m)
               }
           }
           
           if len(similarMemories) > limit {
               similarMemories = similarMemories[:limit]
           }
           
           return similarMemories, nil
       }
   }
   
   func (s *searchService) extractKeywords(context map[string]interface{}) []string {
       // 这里实现关键词提取逻辑
       return []string{}
   }
   
   func (s *searchService) getUserPreferences(ctx context.Context, userID string) (map[string]interface{}, error) {
       // 这里实现用户偏好获取逻辑
       return map[string]interface{}{}, nil
   }
   
   func (s *searchService) rerankByPreferences(memories []*models.Memory, preferences map[string]interface{}) []*models.Memory {
       // 这里实现基于偏好的重新排序逻辑
       return memories
   }
   
   // 辅助结构体
   type MemoryScore struct {
       Memory      *models.Memory
       TextScore   float64
       VectorScore float64
   }
   
   type MemoryWithScore struct {
       Memory *models.Memory
       Score  float64
   }
   
   // 查询结构体
   type SearchQuery struct {
       Text       string
       Vector     []float32
       UserID     string
       Type       string
       Tags       []string
       Level      string
       DateRange  *DateRange
       SearchType string
       Skip       int
       Limit      int
   }
   
   type DateRange struct {
       Start time.Time
       End   time.Time
   }
   
   type SearchResult struct {
       Memories []*models.Memory
       Total    int
       Skip     int
       Limit    int
   }
   ```

## 6. 数据库设计与实现

### 6.1 PostgreSQL数据库设计
```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

-- 记忆表
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    source VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    level VARCHAR(20) DEFAULT 'medium',
    vector VECTOR(768), -- 假设使用768维向量
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE
);

-- 记忆关系表
CREATE TABLE memory_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,
    strength FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_memory_id, target_memory_id, relation_type)
);

-- 记忆访问日志表
CREATE TABLE memory_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_type VARCHAR(50) NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_type ON memories(type);
CREATE INDEX idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX idx_memories_level ON memories(level);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_vector ON memories USING ivfflat (vector vector_cosine_ops);
CREATE INDEX idx_memory_relations_source ON memory_relations(source_memory_id);
CREATE INDEX idx_memory_relations_target ON memory_relations(target_memory_id);
CREATE INDEX idx_memory_access_logs_memory_id ON memory_access_logs(memory_id);
CREATE INDEX idx_memory_access_logs_user_id ON memory_access_logs(user_id);
```

### 6.2 MongoDB数据库设计
```javascript
// 记忆文档集合
db.createCollection("memories", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["user_id", "type", "content"],
         properties: {
            user_id: {
               bsonType: "string",
               description: "用户ID"
            },
            type: {
               bsonType: "string",
               enum: ["text", "image", "audio", "video", "fusion"],
               description: "记忆类型"
            },
            content: {
               bsonType: "string",
               description: "记忆内容"
            },
            metadata: {
               bsonType: "object",
               description: "元数据"
            },
            source: {
               bsonType: "string",
               description: "来源"
            },
            tags: {
               bsonType: "array",
               items: {
                  bsonType: "string"
               },
               description: "标签"
            },
            level: {
               bsonType: "string",
               enum: ["low", "medium", "high"],
               description: "重要级别"
            },
            vector: {
               bsonType: "array",
               items: {
                  bsonType: "double"
               },
               description: "特征向量"
            },
            created_at: {
               bsonType: "date",
               description: "创建时间"
            },
            updated_at: {
               bsonType: "date",
               description: "更新时间"
            },
            is_deleted: {
               bsonType: "bool",
               description: "是否删除"
            },
            access_count: {
               bsonType: "int",
               minimum: 0,
               description: "访问次数"
            },
            last_accessed: {
               bsonType: "date",
               description: "最后访问时间"
            }
         }
      }
   }
});

// 创建索引
db.memories.createIndex({ "user_id": 1 });
db.memories.createIndex({ "type": 1 });
db.memories.createIndex({ "tags": 1 });
db.memories.createIndex({ "level": 1 });
db.memories.createIndex({ "created_at": 1 });
db.memories.createIndex({ "vector": "cosine" });
db.memories.createIndex({ "content": "text", "metadata.title": "text", "metadata.description": "text" });

// 记忆关系集合
db.createCollection("memory_relations", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["source_memory_id", "target_memory_id", "relation_type"],
         properties: {
            source_memory_id: {
               bsonType: "string",
               description: "源记忆ID"
            },
            target_memory_id: {
               bsonType: "string",
               description: "目标记忆ID"
            },
            relation_type: {
               bsonType: "string",
               description: "关系类型"
            },
            strength: {
               bsonType: "double",
               minimum: 0,
               maximum: 1,
               description: "关系强度"
            },
            metadata: {
               bsonType: "object",
               description: "元数据"
            },
            created_at: {
               bsonType: "date",
               description: "创建时间"
            }
         }
      }
   }
});

// 创建索引
db.memory_relations.createIndex({ "source_memory_id": 1 });
db.memory_relations.createIndex({ "target_memory_id": 1 });
db.memory_relations.createIndex({ "relation_type": 1 });
```

### 6.3 Redis缓存设计
```python
# Redis键命名规范
REDIS_KEYS = {
    "user_session": "session:user:{user_id}",
    "memory_cache": "memory:{memory_id}",
    "user_memories": "user:{user_id}:memories",
    "memory_tags": "tags:{user_id}",
    "search_cache": "search:{query_hash}",
    "recommendation_cache": "recommend:{user_id}:{context_hash}",
    "vector_index": "vectors:{user_id}:{type}",
    "stats": "stats:{user_id}",
}

# 缓存过期时间（秒）
CACHE_TTL = {
    "user_session": 86400,  # 24小时
    "memory_cache": 3600,   # 1小时
    "user_memories": 1800,  # 30分钟
    "memory_tags": 3600,    # 1小时
    "search_cache": 600,    # 10分钟
    "recommendation_cache": 1800,  # 30分钟
    "vector_index": 86400,  # 24小时
    "stats": 300,           # 5分钟
}
```

## 7. 测试实现

### 7.1 单元测试
```python
# tests/test_services/test_memory_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.memory_service import MemoryService
from app.schemas.memory import MemoryCreate, MemoryUpdate
from app.models.memory import Memory

@pytest.fixture
def mock_memory_repository():
    repo = AsyncMock()
    return repo

@pytest.fixture
def memory_service(mock_memory_repository):
    return MemoryService(mock_memory_repository)

@pytest.fixture
def sample_memory_create():
    return MemoryCreate(
        type="text",
        content="Test memory content",
        metadata={"title": "Test Title"},
        source="test",
        user_id="user123",
        tags=["test", "sample"],
        level="medium"
    )

@pytest.fixture
def sample_memory():
    return Memory(
        id="memory123",
        type="text",
        content="Test memory content",
        metadata={"title": "Test Title"},
        source="test",
        user_id="user123",
        tags=["test", "sample"],
        level="medium",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_create_memory(memory_service, mock_memory_repository, sample_memory_create, sample_memory):
    # 设置mock返回值
    mock_memory_repository.create.return_value = sample_memory
    
    # 调用服务方法
    result = await memory_service.create_memory(sample_memory_create)
    
    # 验证结果
    assert result.id == sample_memory.id
    assert result.type == sample_memory.type
    assert result.content == sample_memory.content
    
    # 验证repository方法被调用
    mock_memory_repository.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_memory(memory_service, mock_memory_repository, sample_memory):
    # 设置mock返回值
    mock_memory_repository.get_by_id.return_value = sample_memory
    
    # 调用服务方法
    result = await memory_service.get_memory("memory123")
    
    # 验证结果
    assert result.id == sample_memory.id
    assert result.type == sample_memory.type
    
    # 验证repository方法被调用
    mock_memory_repository.get_by_id.assert_called_once_with("memory123")

@pytest.mark.asyncio
async def test_update_memory(memory_service, mock_memory_repository, sample_memory):
    # 设置mock返回值
    mock_memory_repository.get_by_id.return_value = sample_memory
    
    updated_memory = sample_memory.copy()
    updated_memory.content = "Updated content"
    mock_memory_repository.update.return_value = updated_memory
    
    # 准备更新数据
    memory_update = MemoryUpdate(content="Updated content")
    
    # 调用服务方法
    result = await memory_service.update_memory("memory123", memory_update)
    
    # 验证结果
    assert result.content == "Updated content"
    
    # 验证repository方法被调用
    mock_memory_repository.get_by_id.assert_called_once_with("memory123")
    mock_memory_repository.update.assert_called_once()

@pytest.mark.asyncio
async def test_delete_memory(memory_service, mock_memory_repository):
    # 设置mock返回值
    mock_memory_repository.delete.return_value = True
    
    # 调用服务方法
    result = await memory_service.delete_memory("memory123")
    
    # 验证结果
    assert result is True
    
    # 验证repository方法被调用
    mock_memory_repository.delete.assert_called_once_with("memory123")

@pytest.mark.asyncio
async def test_get_memories_by_user(memory_service, mock_memory_repository):
    # 准备测试数据
    memories = [
        Memory(id="mem1", user_id="user123", type="text", content="Content 1"),
        Memory(id="mem2", user_id="user123", type="image", content="Content 2"),
    ]
    
    # 设置mock返回值
    mock_memory_repository.get_by_user_id.return_value = memories
    
    # 调用服务方法
    result = await memory_service.get_memories_by_user("user123", 0, 10)
    
    # 验证结果
    assert len(result) == 2
    assert result[0].id == "mem1"
    assert result[1].id == "mem2"
    
    # 验证repository方法被调用
    mock_memory_repository.get_by_user_id.assert_called_once_with("user123", 0, 10)
```

### 7.2 集成测试
```python
# tests/test_integration/test_memory_api.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_memory_data():
    return {
        "type": "text",
        "content": "Test memory content",
        "metadata": {"title": "Test Title"},
        "source": "test",
        "user_id": "user123",
        "tags": ["test", "sample"],
        "level": "medium"
    }

def test_create_memory_api(client, sample_memory_data):
    response = client.post("/api/v1/memories", json=sample_memory_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["type"] == sample_memory_data["type"]
    assert data["content"] == sample_memory_data["content"]

def test_get_memory_api(client, sample_memory_data):
    # 先创建一个记忆
    create_response = client.post("/api/v1/memories", json=sample_memory_data)
    memory_id = create_response.json()["id"]
    
    # 获取记忆
    response = client.get(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == memory_id
    assert data["type"] == sample_memory_data["type"]

def test_update_memory_api(client, sample_memory_data):
    # 先创建一个记忆
    create_response = client.post("/api/v1/memories", json=sample_memory_data)
    memory_id = create_response.json()["id"]
    
    # 更新记忆
    update_data = {"content": "Updated content"}
    response = client.put(f"/api/v1/memories/{memory_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["content"] == "Updated content"

def test_delete_memory_api(client, sample_memory_data):
    # 先创建一个记忆
    create_response = client.post("/api/v1/memories", json=sample_memory_data)
    memory_id = create_response.json()["id"]
    
    # 删除记忆
    response = client.delete(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 204
    
    # 验证记忆已被删除
    get_response = client.get(f"/api/v1/memories/{memory_id}")
    assert get_response.status_code == 404

def test_get_user_memories_api(client, sample_memory_data):
    # 创建多个记忆
    for i in range(5):
        memory_data = sample_memory_data.copy()
        memory_data["content"] = f"Test content {i}"
        client.post("/api/v1/memories", json=memory_data)
    
    # 获取用户记忆列表
    response = client.get(f"/api/v1/users/{sample_memory_data['user_id']}/memories")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert len(data["items"]) == 5
```

### 7.3 性能测试
```python
# tests/test_performance/test_memory_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from app.services.memory_service import MemoryService
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import MemoryCreate

@pytest.fixture
def memory_service():
    # 这里应该使用真实的数据库连接进行性能测试
    # 或者使用专门的测试数据库
    repo = MemoryRepository()
    return MemoryService(repo)

@pytest.fixture
def sample_memory_data():
    return {
        "type": "text",
        "content": "Test memory content for performance testing",
        "metadata": {"title": "Performance Test"},
        "source": "test",
        "user_id": "perf_user",
        "tags": ["test", "performance"],
        "level": "medium"
    }

@pytest.mark.asyncio
async def test_create_memory_performance(memory_service, sample_memory_data):
    """测试创建记忆的性能"""
    memory_create = MemoryCreate(**sample_memory_data)
    
    # 测试单次创建时间
    start_time = time.time()
    await memory_service.create_memory(memory_create)
    single_create_time = time.time() - start_time
    
    # 单次创建时间应小于100ms
    assert single_create_time < 0.1
    
    # 测试批量创建性能
    batch_size = 100
    start_time = time.time()
    
    tasks = []
    for _ in range(batch_size):
        task = memory_service.create_memory(memory_create)
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    batch_create_time = time.time() - start_time
    
    # 平均每次创建时间应小于50ms
    avg_create_time = batch_create_time / batch_size
    assert avg_create_time < 0.05

@pytest.mark.asyncio
async def test_get_memory_performance(memory_service, sample_memory_data):
    """测试获取记忆的性能"""
    # 先创建一些记忆
    memory_ids = []
    for i in range(10):
        memory_data = sample_memory_data.copy()
        memory_data["content"] = f"Test content {i}"
        memory_create = MemoryCreate(**memory_data)
        memory = await memory_service.create_memory(memory_create)
        memory_ids.append(memory.id)
    
    # 测试单次获取时间
    start_time = time.time()
    await memory_service.get_memory(memory_ids[0])
    single_get_time = time.time() - start_time
    
    # 单次获取时间应小于50ms
    assert single_get_time < 0.05
    
    # 测试批量获取性能
    start_time = time.time()
    
    tasks = []
    for memory_id in memory_ids:
        task = memory_service.get_memory(memory_id)
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    batch_get_time = time.time() - start_time
    
    # 平均每次获取时间应小于20ms
    avg_get_time = batch_get_time / len(memory_ids)
    assert avg_get_time < 0.02

@pytest.mark.asyncio
async def test_concurrent_access_performance(memory_service, sample_memory_data):
    """测试并发访问性能"""
    # 创建一个记忆
    memory_create = MemoryCreate(**sample_memory_data)
    memory = await memory_service.create_memory(memory_create)
    
    # 并发读取测试
    concurrent_reads = 50
    start_time = time.time()
    
    async def read_memory():
        return await memory_service.get_memory(memory.id)
    
    tasks = [read_memory() for _ in range(concurrent_reads)]
    await asyncio.gather(*tasks)
    
    concurrent_read_time = time.time() - start_time
    avg_read_time = concurrent_read_time / concurrent_reads
    
    # 平均每次读取时间应小于30ms
    assert avg_read_time < 0.03
```

## 8. 部署与运维

### 8.1 Kubernetes部署配置
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: memory-storage

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: memory-storage-config
  namespace: memory-storage
data:
  app.yaml: |
    debug: false
    log_level: INFO
    api_prefix: /api/v1
  database.yaml: |
    postgres:
      host: postgres-service
      port: 5432
      database: memory_storage
      pool_size: 20
      max_overflow: 30
    mongodb:
      host: mongodb-service
      port: 27017
      database: memory_storage
      pool_size: 20
    redis:
      host: redis-service
      port: 6379
      db: 0
  elasticsearch.yaml: |
    host: elasticsearch-service
    port: 9200
    index_prefix: memory_storage

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: memory-storage-secrets
  namespace: memory-storage
type: Opaque
data:
  postgres-password: cGFzc3dvcmQ=  # base64编码的"password"
  mongodb-password: cGFzc3dvcmQ=  # base64编码的"password"
  jwt-secret: and0LXNlY3JldA==  # base64编码的"jwt-secret"

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-storage-python
  namespace: memory-storage
  labels:
    app: memory-storage
    component: python-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memory-storage
      component: python-api
  template:
    metadata:
      labels:
        app: memory-storage
        component: python-api
    spec:
      containers:
      - name: memory-storage-python
        image: memory-storage/python:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://user:$(POSTGRES_PASSWORD)@postgres-service:5432/memory_storage"
        - name: MONGODB_URL
          value: "mongodb://user:$(MONGODB_PASSWORD)@mongodb-service:27017/memory_storage"
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: ELASTICSEARCH_URL
          value: "http://elasticsearch-service:9200"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: memory-storage-secrets
              key: postgres-password
        - name: MONGODB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: memory-storage-secrets
              key: mongodb-password
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: memory-storage-secrets
              key: jwt-secret
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: memory-storage-config

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-storage-go
  namespace: memory-storage
  labels:
    app: memory-storage
    component: go-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memory-storage
      component: go-api
  template:
    metadata:
      labels:
        app: memory-storage
        component: go-api
    spec:
      containers:
      - name: memory-storage-go
        image: memory-storage/go:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://user:$(POSTGRES_PASSWORD)@postgres-service:5432/memory_storage"
        - name: MONGODB_URL
          value: "mongodb://user:$(MONGODB_PASSWORD)@mongodb-service:27017/memory_storage"
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: ELASTICSEARCH_URL
          value: "http://elasticsearch-service:9200"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: memory-storage-secrets
              key: postgres-password
        - name: MONGODB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: memory-storage-secrets
              key: mongodb-password
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: memory-storage-secrets
              key: jwt-secret
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: memory-storage-config

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: memory-storage-python-service
  namespace: memory-storage
  labels:
    app: memory-storage
    component: python-api
spec:
  selector:
    app: memory-storage
    component: python-api
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: memory-storage-go-service
  namespace: memory-storage
  labels:
    app: memory-storage
    component: go-api
spec:
  selector:
    app: memory-storage
    component: go-api
  ports:
  - name: http
    port: 8080
    targetPort: 8080
    protocol: TCP
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: memory-storage-ingress
  namespace: memory-storage
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
  - host: memory-storage.local
    http:
      paths:
      - path: /api/v1/python
        pathType: Prefix
        backend:
          service:
            name: memory-storage-python-service
            port:
              number: 8000
      - path: /api/v1/go
        pathType: Prefix
        backend:
          service:
            name: memory-storage-go-service
            port:
              number: 8080
```

### 8.2 监控与告警配置
```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "memory_storage_rules.yml"

scrape_configs:
  - job_name: 'memory-storage-python'
    static_configs:
      - targets: ['memory-storage-python-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'memory-storage-go'
    static_configs:
      - targets: ['memory-storage-go-service:8080']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb-exporter:9216']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch-exporter:9114']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

```yaml
# config/memory_storage_rules.yml
groups:
- name: memory-storage-alerts
  rules:
  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage on {{ $labels.instance }}"
      description: "Memory usage is above 90% for more than 5 minutes."

  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage on {{ $labels.instance }}"
      description: "CPU usage is above 80% for more than 5 minutes."

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.instance }}"
      description: "Error rate is above 5% for more than 5 minutes."

  - alert: DatabaseConnectionFailure
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection failure"
      description: "Cannot connect to PostgreSQL database."

  - alert: SlowQueryResponse
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Slow query response"
      description: "95th percentile of query response time is above 1 second."
```

## 9. 实施计划

### 9.1 第一阶段：基础框架搭建（2周）
1. **环境准备**
   - 搭建开发环境
   - 配置CI/CD流水线
   - 设置代码仓库和分支策略

2. **项目初始化**
   - 创建项目结构
   - 配置依赖管理
   - 设置代码规范和格式化工具

3. **基础框架**
   - 实现基础API框架
   - 配置数据库连接
   - 实现基础认证和授权

### 9.2 第二阶段：核心功能实现（4周）
1. **记忆存储功能**
   - 实现记忆创建、读取、更新、删除
   - 实现记忆分类和标签
   - 实现记忆级别管理

2. **记忆检索功能**
   - 实现全文搜索
   - 实现向量相似度搜索
   - 实现混合搜索

3. **多模态融合功能**
   - 实现文本、图像、音频特征提取
   - 实现多模态数据融合
   - 实现融合记忆存储

### 9.3 第三阶段：高级功能开发（3周）
1. **记忆关系管理**
   - 实现记忆关系建立
   - 实现记忆图谱构建
   - 实现关系强度计算

2. **记忆分析功能**
   - 实现记忆统计分析
   - 实现记忆趋势分析
   - 实现记忆推荐算法

3. **记忆管理功能**
   - 实现记忆归档
   - 实现记忆清理
   - 实现记忆备份

### 9.4 第四阶段：性能优化（2周）
1. **数据库优化**
   - 优化数据库查询
   - 实现数据库分片
   - 优化索引策略

2. **缓存优化**
   - 实现多级缓存
   - 优化缓存策略
   - 实现缓存预热

3. **并发优化**
   - 优化并发处理
   - 实现连接池
   - 优化资源利用

### 9.5 第五阶段：测试与部署（2周）
1. **测试**
   - 完善单元测试
   - 实现集成测试
   - 进行性能测试

2. **部署**
   - 配置生产环境
   - 实现自动化部署
   - 配置监控和告警

3. **文档**
   - 完善API文档
   - 编写用户手册
   - 创建运维文档

## 10. 阶段输出

### 10.1 代码输出
1. **源代码**
   - Python服务代码
   - Go服务代码
   - 前端代码（如果有）

2. **配置文件**
   - 应用配置
   - 数据库配置
   - 部署配置

3. **测试代码**
   - 单元测试
   - 集成测试
   - 性能测试

### 10.2 文档输出
1. **技术文档**
   - API文档
   - 架构文档
   - 数据库设计文档

2. **用户文档**
   - 用户手册
   - 开发指南
   - 部署指南

3. **运维文档**
   - 监控指南
   - 故障排查手册
   - 备份恢复指南

### 10.3 部署输出
1. **容器镜像**
   - 应用镜像
   - 基础设施镜像

2. **部署脚本**
   - Kubernetes配置
   - Docker Compose配置

3. **监控配置**
   - Prometheus配置
   - Grafana仪表盘

## 11. 下一阶段衔接

Apply阶段的输出将为Assess阶段提供基础：

1. **可测试的系统**
   - 完整的系统功能
   - 稳定的系统性能
   - 可靠的系统架构

2. **测试环境**
   - 完整的测试环境
   - 测试数据和工具
   - 自动化测试框架

3. **评估基础**
   - 明确的评估标准
   - 评估工具和方法
   - 评估流程和计划

Assess阶段将基于Apply阶段的输出，对系统进行全面的功能、性能、可靠性、安全性和用户体验评估，确保系统满足设计要求，并为后续的Accumulate阶段做好准备。
