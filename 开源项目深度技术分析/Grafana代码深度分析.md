# Grafana代码深度分析文档

## 项目概述

Grafana是一个开源的度量分析和可视化平台，支持多种数据源，提供丰富的图表类型和灵活的仪表板配置，是现代监控体系的可视化核心。

## 项目结构分析

### 核心模块结构
```
grafana/
├── pkg/                           # 核心包
│   ├── api/                      # API接口
│   ├── bus/                      # 消息总线
│   ├── cmd/                      # 命令行工具
│   ├── components/               # UI组件
│   ├── datasources/              # 数据源
│   ├── models/                   # 数据模型
│   ├── plugins/                  # 插件系统
│   ├── services/                 # 服务层
│   ├── setting/                  # 配置管理
│   └── util/                     # 工具类
├── public/                       # 静态资源
├── scripts/                      # 构建脚本
└── conf/                         # 配置文件
```

### 主要代码文件分析

#### 1. 主服务器模块 (pkg/cmd/)
- **grafana-server/main.go**: 主程序入口
- **grafana-cli/main.go**: 命令行工具

#### 2. API接口模块 (pkg/api/)
- **dashboard_api.go**: 仪表板API
- **datasource_api.go**: 数据源API
- **user_api.go**: 用户API
- **alerting_api.go**: 告警API

#### 3. 数据源模块 (pkg/datasources/)
- **prometheus.go**: Prometheus数据源
- **graphite.go**: Graphite数据源
- **influxdb.go**: InfluxDB数据源
- **elasticsearch.go**: Elasticsearch数据源

#### 4. 插件系统模块 (pkg/plugins/)
- **manager.go**: 插件管理器
- **datasource_plugin.go**: 数据源插件
- **panel_plugin.go**: 面板插件
- **app_plugin.go**: 应用插件

## 接口分析

### 1. 配置管理接口

#### 主配置文件 (conf/defaults.ini)
```ini
# 实例配置
[instance_name]
name = Grafana

# 数据库配置
[database]
type = sqlite3
path = grafana.db

# 安全配置
[security]
admin_user = admin
admin_password = admin
secret_key = SW2YcwTIb9zpOOhoPsMm

# 服务器配置
[server]
protocol = http
http_port = 3000
domain = localhost

# 会话配置
[session]
provider = file
provider_config = sessions
cookie_name = grafana_sess

# 数据源配置
[datasources]
# 默认数据源配置

# 用户配置
[users]
allow_sign_up = false
auto_assign_org = true
auto_assign_org_role = Viewer

# 认证配置
[auth]
# LDAP配置
[auth.ldap]
enabled = false
config_file = /etc/grafana/ldap.toml

# OAuth配置
[auth.google]
enabled = false
client_id = some_client_id
client_secret = some_client_secret
scopes = https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email
auth_url = https://accounts.google.com/o/oauth2/auth
token_url = https://accounts.google.com/o/oauth2/token

# 告警配置
[alerting]
enabled = true
execute_alerts = true

# 面板配置
[panels]
enable_alpha = false

# 插件配置
[plugins]
enable_alpha = false
app_tls_skip_verify_insecure = false

# 探索配置
[explore]
enabled = true

# 指标配置
[metrics]
enabled = true
interval_seconds = 10

# 快照配置
[snapshots]
external_enabled = true
external_snapshot_url = https://snapshots-origin.raintank.io
external_snapshot_name = Publish to snapshot.raintank.io

# 指标存储配置
[metrics.graphite]
address = 127.0.0.1:2003
prefix = prod.grafana.%(instance_name)s.

# 日志配置
[log]
mode = console file
level = Info

# 路径配置
[paths]
data = /var/lib/grafana
logs = /var/log/grafana
plugins = /var/lib/grafana/plugins
provisioning = conf/provisioning
```

#### 数据源配置
```yaml
# 数据源配置文件 (datasources.yaml)
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    jsonData:
      timeInterval: 5s
      queryTimeout: 60s
      httpMethod: POST
    secureJsonData:
      basicAuthPassword: password

  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://localhost:8086
    database: metrics
    user: admin
    secureJsonData:
      password: password

  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://localhost:9200
    database: metrics
    jsonData:
      timeField: @timestamp
      esVersion: 7.0.0
      interval: Daily
      timeInterval: 5s

  - name: Graphite
    type: graphite
    access: proxy
    url: http://localhost:8080
```

#### 仪表板配置
```yaml
# 仪表板配置文件 (dashboards.yaml)
apiVersion: 1

providers:
  - name: 'default'
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/dashboards

  - name: 'monitoring'
    folder: 'Monitoring'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/dashboards/monitoring
```

### 2. REST API接口

#### 仪表板API
```bash
# 获取仪表板列表
GET /api/dashboards

# 获取特定仪表板
GET /api/dashboards/uid/:uid

# 创建仪表板
POST /api/dashboards/db
Content-Type: application/json

{
  "dashboard": {
    "id": null,
    "title": "Production Overview",
    "tags": ["templated"],
    "timezone": "browser",
    "panels": [...],
    "templating": {
      "list": [...]
    }
  },
  "overwrite": false
}

# 更新仪表板
PUT /api/dashboards/db

# 删除仪表板
DELETE /api/dashboards/uid/:uid
```

#### 数据源API
```bash
# 获取数据源列表
GET /api/datasources

# 创建数据源
POST /api/datasources
Content-Type: application/json

{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://localhost:9090",
  "access": "proxy",
  "isDefault": true
}

# 测试数据源连接
GET /api/datasources/:id/health

# 查询数据源
POST /api/ds/query
Content-Type: application/json

{
  "from": "now-1h",
  "to": "now",
  "queries": [
    {
      "refId": "A",
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "expr": "rate(http_requests_total[5m])"
    }
  ]
}
```

#### 告警API
```bash
# 获取告警列表
GET /api/alerts

# 获取特定告警
GET /api/alerts/:id

# 暂停告警
POST /api/alerts/:id/pause

# 恢复告警
POST /api/alerts/:id/unpause

# 测试告警规则
POST /api/alerts/test
Content-Type: application/json

{
  "dashboard": {...},
  "panelId": 1,
  "condition": "A",
  "data": [...]
}
```

#### 用户和组织API
```bash
# 获取当前用户
GET /api/user

# 更新用户偏好
PUT /api/user/preferences

# 获取组织列表
GET /api/orgs

# 创建组织
POST /api/orgs

# 获取组织用户
GET /api/orgs/:orgId/users

# 添加用户到组织
POST /api/orgs/:orgId/users
```

### 3. 前端接口

#### React组件接口
```jsx
// 仪表板组件
import { Dashboard } from '@grafana/ui';

const MyDashboard = () => (
  <Dashboard
    title="Production Overview"
    panels={panels}
    timeRange={timeRange}
    onTimeRangeChange={handleTimeRangeChange}
  />
);

// 面板组件
import { Panel } from '@grafana/ui';

const MyPanel = ({ data, options, width, height }) => (
  <Panel
    title="CPU Usage"
    data={data}
    options={options}
    width={width}
    height={height}
  >
    {/* 自定义渲染逻辑 */}
  </Panel>
);

// 数据源选择器
import { DataSourcePicker } from '@grafana/ui';

const DataSourceSelector = ({ value, onChange }) => (
  <DataSourcePicker
    value={value}
    onChange={onChange}
    datasources={datasources}
  />
);
```

#### 插件开发接口
```typescript
// 数据源插件
import { DataSourcePlugin } from '@grafana/data';
import { DataSource } from './datasource';
import { ConfigEditor } from './ConfigEditor';
import { QueryEditor } from './QueryEditor';

class MyDataSource extends DataSourceApi<MyQuery, MyDataSourceOptions> {
  constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {
    super(instanceSettings);
  }
  
  async query(options: DataQueryRequest<MyQuery>): Promise<DataQueryResponse> {
    // 查询实现
  }
  
  async testDatasource(): Promise<TestDataSourceResponse> {
    // 测试连接
  }
}

export const plugin = new DataSourcePlugin(MyDataSource)
  .setConfigEditor(ConfigEditor)
  .setQueryEditor(QueryEditor);

// 面板插件
import { PanelPlugin } from '@grafana/data';
import { MyPanel } from './MyPanel';
import { PanelOptions } from './types';

export const plugin = new PanelPlugin<PanelOptions>(MyPanel)
  .setPanelOptions(builder => {
    return builder
      .addTextInput({
        path: 'text',
        name: 'Simple text option',
        description: 'Description of panel option',
        defaultValue: 'Default value',
      })
      .addBooleanSwitch({
        path: 'showMessage',
        name: 'Show message',
        defaultValue: false,
      });
  });
```

## 数据流分析

### 1. 仪表板渲染流程
```
用户请求 → 权限验证 → 加载仪表板配置 → 解析面板配置 → 查询数据源 → 数据处理 → 组件渲染 → 返回HTML
```

### 2. 数据查询流程
```
面板查询 → 数据源选择 → 查询构建 → 后端查询 → 数据转换 → 返回前端 → 可视化渲染
```

### 3. 告警处理流程
```
告警规则评估 → 状态检查 → 通知发送 → 状态更新 → 仪表板显示
```

## 关键代码实现细节

### 1. 仪表板服务实现
```go
// 仪表板服务
type DashboardService interface {
    GetDashboard(ctx context.Context, query *GetDashboardQuery) (*Dashboard, error)
    SaveDashboard(ctx context.Context, cmd *SaveDashboardCommand) (*Dashboard, error)
    DeleteDashboard(ctx context.Context, cmd *DeleteDashboardCommand) error
    ImportDashboard(ctx context.Context, cmd *ImportDashboardCommand) (*Dashboard, error)
    GetDashboardTags(ctx context.Context, query *GetDashboardTagsQuery) ([]*DashboardTagCloudItem, error)
}

// 仪表板服务实现
type dashboardService struct {
    SQLStore       *sqlstore.SQLStore
    dashboardCache *cache.Cache
    bus            bus.Bus
}

func (s *dashboardService) GetDashboard(ctx context.Context, query *GetDashboardQuery) (*Dashboard, error) {
    // 检查缓存
    if dashboard, found := s.dashboardCache.Get(query.Uid); found {
        return dashboard.(*Dashboard), nil
    }
    
    // 从数据库查询
    dashboard, err := s.SQLStore.GetDashboard(ctx, query)
    if err != nil {
        return nil, err
    }
    
    // 更新缓存
    s.dashboardCache.Set(query.Uid, dashboard, cache.DefaultExpiration)
    
    return dashboard, nil
}

func (s *dashboardService) SaveDashboard(ctx context.Context, cmd *SaveDashboardCommand) (*Dashboard, error) {
    // 验证权限
    if err := s.validateDashboardPermissions(ctx, cmd); err != nil {
        return nil, err
    }
    
    // 保存到数据库
    dashboard, err := s.SQLStore.SaveDashboard(ctx, cmd)
    if err != nil {
        return nil, err
    }
    
    // 清除缓存
    s.dashboardCache.Delete(dashboard.Uid)
    
    // 发布事件
    s.bus.Publish(&events.DashboardSaved{
        Dashboard: dashboard,
        UserId:    cmd.UserId,
    })
    
    return dashboard, nil
}
```

### 2. 数据源服务实现
```go
// 数据源服务
type DataSourceService interface {
    GetDataSource(ctx context.Context, query *GetDataSourceQuery) (*DataSource, error)
    AddDataSource(ctx context.Context, cmd *AddDataSourceCommand) error
    DeleteDataSource(ctx context.Context, cmd *DeleteDataSourceCommand) error
    GetDataSources(ctx context.Context, query *GetDataSourcesQuery) ([]*DataSource, error)
    GetDefaultDataSource(ctx context.Context, query *GetDefaultDataSourceQuery) (*DataSource, error)
}

// 数据源服务实现
type dataSourceService struct {
    SQLStore *sqlstore.SQLStore
    cache    *cache.Cache
}

func (s *dataSourceService) GetDataSource(ctx context.Context, query *GetDataSourceQuery) (*DataSource, error) {
    // 检查缓存
    cacheKey := fmt.Sprintf("datasource_%d", query.Id)
    if datasource, found := s.cache.Get(cacheKey); found {
        return datasource.(*DataSource), nil
    }
    
    // 从数据库查询
    datasource, err := s.SQLStore.GetDataSource(ctx, query)
    if err != nil {
        return nil, err
    }
    
    // 更新缓存
    s.cache.Set(cacheKey, datasource, cache.DefaultExpiration)
    
    return datasource, nil
}

func (s *dataSourceService) AddDataSource(ctx context.Context, cmd *AddDataSourceCommand) error {
    // 验证数据源配置
    if err := s.validateDataSource(cmd); err != nil {
        return err
    }
    
    // 测试数据源连接
    if err := s.testDataSourceConnection(cmd); err != nil {
        return fmt.Errorf("数据源连接测试失败: %v", err)
    }
    
    // 保存到数据库
    err := s.SQLStore.AddDataSource(ctx, cmd)
    if err != nil {
        return err
    }
    
    // 清除相关缓存
    s.clearDataSourceCache()
    
    return nil
}

func (s *dataSourceService) testDataSourceConnection(cmd *AddDataSourceCommand) error {
    // 根据类型创建数据源客户端
    client, err := s.createDataSourceClient(cmd)
    if err != nil {
        return err
    }
    
    // 测试连接
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    return client.TestConnection(ctx)
}
```

### 3. 查询执行引擎
```go
// 查询执行器
type QueryExecutor interface {
    Execute(ctx context.Context, query *Query) (*QueryResult, error)
    ExecuteBatch(ctx context.Context, queries []*Query) ([]*QueryResult, error)
}

// 查询执行器实现
type queryExecutor struct {
    dataSourceService DataSourceService
    queryTransformer QueryTransformer
}

func (e *queryExecutor) Execute(ctx context.Context, query *Query) (*QueryResult, error) {
    // 获取数据源
    datasource, err := e.dataSourceService.GetDataSource(ctx, &GetDataSourceQuery{
        Id: query.DataSourceId,
    })
    if err != nil {
        return nil, err
    }
    
    // 转换查询
    transformedQuery, err := e.queryTransformer.Transform(query, datasource)
    if err != nil {
        return nil, err
    }
    
    // 执行查询
    result, err := e.executeQuery(ctx, transformedQuery, datasource)
    if err != nil {
        return nil, err
    }
    
    // 处理结果
    return e.processResult(result, query)
}

func (e *queryExecutor) executeQuery(ctx context.Context, query *Query, datasource *DataSource) (*QueryResult, error) {
    // 根据数据源类型选择执行器
    switch datasource.Type {
    case "prometheus":
        return e.executePrometheusQuery(ctx, query, datasource)
    case "influxdb":
        return e.executeInfluxDBQuery(ctx, query, datasource)
    case "elasticsearch":
        return e.executeElasticsearchQuery(ctx, query, datasource)
    default:
        return nil, fmt.Errorf("不支持的数据源类型: %s", datasource.Type)
    }
}

func (e *queryExecutor) executePrometheusQuery(ctx context.Context, query *Query, datasource *DataSource) (*QueryResult, error) {
    // 创建Prometheus客户端
    client, err := prometheus.NewClient(prometheus.Config{
        Address: datasource.Url,
        Timeout: 30 * time.Second,
    })
    if err != nil {
        return nil, err
    }
    
    // 执行PromQL查询
    result, warnings, err := client.Query(ctx, query.Expr, time.Now())
    if err != nil {
        return nil, err
    }
    
    // 处理警告
    if len(warnings) > 0 {
        log.Warnf("Prometheus查询警告: %v", warnings)
    }
    
    return &QueryResult{
        Data:    result,
        Status:  "success",
        Warnings: warnings,
    }, nil
}
```

### 4. 插件管理系统
```go
// 插件管理器
type PluginManager interface {
    LoadPlugins() error
    UnloadPlugins() error
    GetPlugins() []*PluginInfo
    GetPlugin(pluginId string) (*PluginInfo, error)
    EnablePlugin(pluginId string) error
    DisablePlugin(pluginId string) error
}

// 插件管理器实现
type pluginManager struct {
    pluginDir     string
    plugins       map[string]*PluginInfo
    dataSources   map[string]datasources.DataSourcePlugin
    panels        map[string]panels.PanelPlugin
    apps          map[string]apps.AppPlugin
}

func (m *pluginManager) LoadPlugins() error {
    // 扫描插件目录
    pluginDirs, err := ioutil.ReadDir(m.pluginDir)
    if err != nil {
        return err
    }
    
    for _, pluginDir := range pluginDirs {
        if !pluginDir.IsDir() {
            continue
        }
        
        pluginPath := filepath.Join(m.pluginDir, pluginDir.Name())
        
        // 读取插件清单
        manifest, err := m.readPluginManifest(pluginPath)
        if err != nil {
            log.Errorf("读取插件清单失败 %s: %v", pluginPath, err)
            continue
        }
        
        // 加载插件
        plugin, err := m.loadPlugin(pluginPath, manifest)
        if err != nil {
            log.Errorf("加载插件失败 %s: %v", pluginPath, err)
            continue
        }
        
        // 注册插件
        m.registerPlugin(plugin)
    }
    
    return nil
}

func (m *pluginManager) loadPlugin(pluginPath string, manifest *PluginManifest) (*PluginInfo, error) {
    // 根据类型加载插件
    switch manifest.Type {
    case "datasource":
        return m.loadDataSourcePlugin(pluginPath, manifest)
    case "panel":
        return m.loadPanelPlugin(pluginPath, manifest)
    case "app":
        return m.loadAppPlugin(pluginPath, manifest)
    default:
        return nil, fmt.Errorf("未知的插件类型: %s", manifest.Type)
    }
}

func (m *pluginManager) loadDataSourcePlugin(pluginPath string, manifest *PluginManifest) (*PluginInfo, error) {
    // 加载数据源插件
    plugin := &PluginInfo{
        Id:      manifest.Id,
        Name:    manifest.Name,
        Type:    manifest.Type,
        Info:    manifest.Info,
        Path:    pluginPath,
        Enabled: true,
    }
    
    // 初始化插件
    if err := plugin.Initialize(); err != nil {
        return nil, err
    }
    
    return plugin, nil
}
```

## 性能优化要点

### 1. 前端优化策略
- **组件懒加载**: 按需加载仪表板组件
- **数据缓存**: 缓存查询结果减少重复请求
- **虚拟滚动**: 大数据集虚拟滚动显示
- **图表优化**: 使用Canvas渲染大量数据点

### 2. 后端优化策略
- **查询缓存**: 缓存常用查询结果
- **连接池**: 数据库连接池管理
- **批量处理**: 批量执行数据源查询
- **异步处理**: 异步处理耗时操作

### 3. 数据库优化策略
- **索引优化**: 优化常用查询字段索引
- **分表策略**: 大数据量表分表存储
- **查询优化**: 避免N+1查询问题

## 集成注意事项

### 1. 数据源集成配置
```go
import (
    "github.com/grafana/grafana/pkg/models"
    "github.com/grafana/grafana/pkg/registry"
)

// 数据源服务注册
func init() {
    registry.RegisterService(&DataSourceService{})
}

// 数据源配置验证
func ValidateDataSourceConfig(dsType string, config map[string]interface{}) error {
    switch dsType {
    case "prometheus":
        return validatePrometheusConfig(config)
    case "influxdb":
        return validateInfluxDBConfig(config)
    case "elasticsearch":
        return validateElasticsearchConfig(config)
    default:
        return fmt.Errorf("未知的数据源类型: %s", dsType)
    }
}

func validatePrometheusConfig(config map[string]interface{}) error {
    // 验证URL
    url, ok := config["url"].(string)
    if !ok || url == "" {
        return fmt.Errorf("Prometheus URL不能为空")
    }
    
    // 验证超时设置
    if timeout, ok := config["timeout"].(string); ok {
        if _, err := time.ParseDuration(timeout); err != nil {
            return fmt.Errorf("无效的超时设置: %v", err)
        }
    }
    
    return nil
}
```

### 2. 仪表板模板配置
```json
{
  "dashboard": {
    "id": null,
    "title": "系统监控仪表板",
    "tags": ["monitoring", "system"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "type": "graph",
        "title": "CPU使用率",
        "gridPos": {
          "x": 0,
          "y": 0,
          "w": 12,
          "h": 8
        },
        "targets": [
          {
            "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}",
            "refId": "A"
          }
        ],
        "options": {
          "legend": {
            "show": true,
            "values": true
          }
        }
      },
      {
        "id": 2,
        "type": "singlestat",
        "title": "内存使用率",
        "gridPos": {
          "x": 12,
          "y": 0,
          "w": 12,
          "h": 8
        },
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "refId": "A"
          }
        ],
        "options": {
          "valueName": "current",
          "unit": "percent",
          "thresholds": "80,90",
          "colors": ["green", "orange", "red"]
        }
      }
    ],
    "templating": {
      "list": [
        {
          "name": "instance",
          "type": "query",
          "query": "label_values(up, instance)",
          "refresh": 1,
          "includeAll": true,
          "multi": true
        }
      ]
    },
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "timepicker": {
      "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"],
      "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"]
    },
    "refresh": "10s"
  },
  "overwrite": false
}
```

### 3. 告警规则配置
```yaml
# 告警规则配置
groups:
- name: system_alerts
  rules:
  - alert: HighCPUUsage
    expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "高CPU使用率 - {{ $labels.instance }}"
      description: "CPU使用率超过80%持续5分钟"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "高内存使用率 - {{ $labels.instance }}"
      description: "内存使用率超过90%持续5分钟"

  - alert: DiskSpaceLow
    expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 85
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "磁盘空间不足 - {{ $labels.instance }}:{{ $labels.mountpoint }}"
      description: "磁盘使用率超过85%持续10分钟"
```

## 测试用例

### 1. 数据源连接测试
```go
import (
    "testing"
    "github.com/grafana/grafana/pkg/models"
)

func TestDataSourceConnection(t *testing.T) {
    testCases := []struct {
        name     string
        config   map[string]interface{}
        expected bool
    }{
        {
            name: "valid prometheus config",
            config: map[string]interface{}{
                "url":     "http://localhost:9090",
                "timeout": "30s",
            },
            expected: true,
        },
        {
            name: "invalid prometheus url",
            config: map[string]interface{}{
                "url": "",
            },
            expected: false,
        },
    }
    
    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            err := ValidateDataSourceConfig("prometheus", tc.config)
            
            if tc.expected && err != nil {
                t.Errorf("期望验证通过但失败: %v", err)
            } else if !tc.expected && err == nil {
                t.Error("期望验证失败但通过了")
            }
        })
    }
}
```

### 2. 仪表板服务测试
```go
func TestDashboardService(t *testing.T) {
    // 创建测试服务
    service := &dashboardService{
        SQLStore:       createTestSQLStore(),
        dashboardCache: cache.New(5*time.Minute, 10*time.Minute),
        bus:            bus.New(),
    }
    
    // 测试获取仪表板
    t.Run("GetDashboard", func(t *testing.T) {
        query := &GetDashboardQuery{
            Uid: "test-dashboard",
        }
        
        dashboard, err := service.GetDashboard(context.Background(), query)
        if err != nil {
            t.Fatalf("获取仪表板失败: %v", err)
        }
        
        if dashboard == nil {
            t.Error("仪表板不应为nil")
        }
        
        if dashboard.Uid != query.Uid {
            t.Errorf("仪表板UID不匹配: 期望%s, 实际%s", query.Uid, dashboard.Uid)
        }
    })
    
    // 测试保存仪表板
    t.Run("SaveDashboard", func(t *testing.T) {
        cmd := &SaveDashboardCommand{
            Dashboard: &models.Dashboard{
                Uid:   "new-dashboard",
                Title: "测试仪表板",
            },
            UserId: 1,
        }
        
        dashboard, err := service.SaveDashboard(context.Background(), cmd)
        if err != nil {
            t.Fatalf("保存仪表板失败: %v", err)
        }
        
        if dashboard.Uid != cmd.Dashboard.Uid {
            t.Errorf("仪表板UID不匹配: 期望%s, 实际%s", cmd.Dashboard.Uid, dashboard.Uid)
        }
    })
}
```

### 3. 查询执行测试
```go
func TestQueryExecution(t *testing.T) {
    executor := &queryExecutor{
        dataSourceService: createTestDataSourceService(),
        queryTransformer: &queryTransformer{},
    }
    
    testCases := []struct {
        name     string
        query    *Query
        expected bool
    }{
        {
            name: "valid prometheus query",
            query: &Query{
                DataSourceId: 1,
                Expr:         "up",
            },
            expected: true,
        },
        {
            name: "invalid datasource",
            query: &Query{
                DataSourceId: 999, // 不存在的ID
                Expr:         "up",
            },
            expected: false,
        },
    }
    
    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            result, err := executor.Execute(context.Background(), tc.query)
            
            if tc.expected {
                if err != nil {
                    t.Errorf("查询执行失败: %v", err)
                }
                if result == nil {
                    t.Error("查询结果不应为nil")
                }
            } else {
                if err == nil {
                    t.Error("期望查询失败但成功了")
                }
            }
        })
    }
}
```

## 总结

Grafana作为可视化平台，在真实婴儿AI管家系统中将负责系统状态的可视化展示、监控数据的分析和告警管理，为系统的运维提供直观的界面。

**关键集成点**:
- 多数据源支持
- 灵活的仪表板配置
- 丰富的可视化组件
- 强大的告警系统
- 可扩展的插件架构

**性能要求**:
- 快速的数据查询响应（<2秒）
- 流畅的仪表板渲染
- 高效的内存使用
- 稳定的并发处理

**扩展功能**:
- 自定义数据源插件
- 自定义面板插件
- 组织多租户支持
- 外部认证集成

Grafana的模块化架构和丰富的API接口使其能够很好地集成到真实婴儿AI管家系统中，为系统监控和运维提供强大的可视化能力。