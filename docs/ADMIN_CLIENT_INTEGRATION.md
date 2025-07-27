# RPA客户端管理系统集成指南

## 概述

本文档描述了如何在xiaoxin_rpa_pro客户端中集成管理系统功能，实现远程监控、控制和管理。

## 功能特性

### 核心功能
- **自动注册**: 客户端启动时自动向管理服务器注册
- **心跳监控**: 定期发送心跳包保持连接状态
- **远程控制**: 接收并执行管理服务器的命令
- **状态同步**: 实时同步客户端状态到管理服务器
- **自动重连**: 断线后自动重连机制

### 支持的命令
- `enable`: 启用客户端执行功能
- `disable`: 禁用客户端执行功能
- `restart`: 重启客户端（需自定义实现）
- `get_status`: 获取客户端当前状态
- `ping`: 连接测试

## 配置说明

### 默认配置
在 `config/default.yaml` 中添加以下配置：

```yaml
admin:
  enabled: true                    # 是否启用管理客户端
  url: http://localhost:8000      # 管理服务器地址
  api_prefix: /api/v1             # API前缀
  heartbeat_interval: 30          # 心跳间隔（秒）
  reconnect_delay: 5              # 重连延迟（秒）
  max_reconnect_attempts: -1      # 最大重连次数（-1为无限）
  auto_register: true             # 是否自动注册
```

### 环境配置
可以创建特定环境的配置文件，例如 `config/production.yaml`：

```yaml
admin:
  enabled: true
  url: https://admin.example.com
  heartbeat_interval: 60
```

## 使用方法

### 1. 正常启动（启用管理客户端）
```powershell
# 使用默认配置
python main.py

# 使用自定义配置
python main.py --config config/production.yaml
```

### 2. 禁用管理客户端
```powershell
# 通过命令行参数禁用
python main.py --no-admin

# 或在配置文件中设置
# admin.enabled: false
```

### 3. 调试模式
```powershell
# 启用调试日志查看详细信息
python main.py --debug --log-level DEBUG
```

## 工作流程

### 启动流程
1. 主程序启动时检查admin.enabled配置
2. 如果启用，创建AdminClient实例
3. 向管理服务器注册客户端信息
4. 建立WebSocket连接
5. 在后台启动心跳循环和命令监听

### 执行控制
- 执行工作流前检查客户端是否被禁用
- 如果被禁用，拒绝执行并提示用户
- 管理员可以通过管理界面远程启用/禁用客户端

### 状态同步
- 每30秒（可配置）发送一次心跳
- 心跳包含：客户端ID、状态、系统信息等
- 命令执行后立即发送确认消息

## 扩展开发

### 自定义命令处理器
```python
from core.admin_client import AdminClient

# 创建自定义命令处理器
async def handle_custom_command(command):
    # 处理自定义命令
    data = command.get('data', {})
    # 执行操作...
    return "执行结果"

# 注册命令处理器
admin_client = AdminClient(config)
admin_client.register_command_handler('custom_command', handle_custom_command)
```

### 集成到工作流
```python
from core.workflow import BaseWorkflow, WorkflowStep

class AdminAwareWorkflow(BaseWorkflow):
    def _setup(self):
        # 检查管理客户端状态
        if hasattr(self, 'admin_client') and not self.admin_client.is_client_enabled():
            self.logger.warning("客户端已被管理员禁用")
            return False
        
        # 继续正常的工作流设置
        self.add_step(MyWorkflowStep())
```

## 安全考虑

### 网络安全
- 建议在生产环境使用HTTPS
- 考虑使用客户端证书认证
- 限制管理服务器的访问IP

### 权限控制
- 客户端只能接收预定义的命令
- 敏感操作需要额外确认
- 日志记录所有远程操作

## 故障排查

### 常见问题

1. **无法连接到管理服务器**
   - 检查网络连接
   - 确认服务器地址配置正确
   - 查看防火墙设置

2. **WebSocket连接断开**
   - 检查网络稳定性
   - 查看服务器日志
   - 确认心跳间隔设置合理

3. **客户端被意外禁用**
   - 联系管理员启用
   - 检查管理界面操作日志
   - 使用--no-admin临时绕过

### 日志查看
```powershell
# 查看详细日志
python main.py --debug

# 日志文件位置
logs/xiaoxin_rpa.log
```

## API参考

### AdminClient类
```python
class AdminClient:
    def __init__(self, config: Optional[Config] = None)
    async def register(self) -> bool
    async def connect_websocket(self)
    async def send_heartbeat(self)
    async def handle_command(self, command: Dict[str, Any])
    def register_command_handler(self, command_type: str, handler: Callable)
    def is_client_enabled(self) -> bool
    async def start(self)
    async def stop(self)
```

### 心跳数据格式
```json
{
    "type": "heartbeat",
    "client_id": "hostname_mac",
    "timestamp": "2025-01-27T10:00:00Z",
    "status": "online",
    "is_active": true,
    "system_info": {
        "hostname": "DESKTOP-ABC123",
        "ip_address": "192.168.1.100",
        "platform": "Windows-10",
        "version": "1.0.2"
    }
}
```

### 命令格式
```json
{
    "type": "enable|disable|restart|get_status|ping",
    "id": "command-uuid",
    "data": {}
}
```

### 命令确认格式
```json
{
    "type": "command_ack",
    "client_id": "hostname_mac",
    "command_type": "enable",
    "command_id": "command-uuid",
    "status": "success|failed|unknown",
    "result": "执行结果",
    "timestamp": "2025-01-27T10:00:01Z"
}
```

## 版本兼容性

- 需要Python 3.8+
- 需要安装额外依赖：aiohttp, websockets
- 兼容管理后台API v1

## 后续计划

- [ ] 支持批量命令执行
- [ ] 添加文件传输功能
- [ ] 实现远程日志查看
- [ ] 支持自定义插件系统
- [ ] 增强安全认证机制