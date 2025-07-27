"""
管理系统客户端SDK
用于连接到xiaoxin管理后台，实现客户端注册、心跳发送、命令接收等功能
"""

import asyncio
import json
import platform
import socket
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from .logger import LoggerMixin
from .config import Config


class AdminClient(LoggerMixin):
    """管理系统客户端类"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化管理客户端
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        super().__init__()
        
        # 加载配置
        if config is None:
            config_path = Path(__file__).parent.parent / "config" / "default.yaml"
            config = Config(config_path)
        self.config = config
        
        # 管理服务器配置
        self.admin_url = self.config.get('admin.url', 'http://localhost:8000')
        self.api_prefix = self.config.get('admin.api_prefix', '/api/v1')
        self.websocket_url = self.admin_url.replace('http', 'ws') + '/ws/clients'
        
        # 客户端信息
        self.client_id = self._generate_client_id()
        self.hostname = socket.gethostname()
        self.ip_address = self._get_local_ip()
        self.version = self.config.get('app.version', '1.0.2')
        self.platform = platform.platform()
        
        # 连接状态
        self.websocket = None
        self.running = True
        self.connected = False
        self.is_enabled = True
        
        # 心跳配置
        self.heartbeat_interval = self.config.get('admin.heartbeat_interval', 30)
        self.reconnect_delay = self.config.get('admin.reconnect_delay', 5)
        self.max_reconnect_attempts = self.config.get('admin.max_reconnect_attempts', -1)
        self.reconnect_attempts = 0
        
        # 回调函数
        self.command_handlers = {}
        self._register_default_handlers()
        
        # 任务管理
        self.tasks = []
        
    def _generate_client_id(self) -> str:
        """
        生成唯一的客户端ID
        基于主机名和MAC地址
        """
        hostname = socket.gethostname()
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                       for i in range(0, 8*6, 8)][::-1])
        return f"{hostname}_{mac}"
    
    def _get_local_ip(self) -> str:
        """获取本地IP地址"""
        try:
            # 创建一个UDP套接字
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到外部地址（不会真正发送数据）
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def _register_default_handlers(self):
        """注册默认的命令处理器"""
        self.register_command_handler('enable', self._handle_enable)
        self.register_command_handler('disable', self._handle_disable)
        self.register_command_handler('restart', self._handle_restart)
        self.register_command_handler('get_status', self._handle_get_status)
        self.register_command_handler('ping', self._handle_ping)
    
    async def register(self) -> bool:
        """
        向管理服务器注册此客户端
        
        Returns:
            是否注册成功
        """
        registration_data = {
            'client_id': self.client_id,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'version': self.version,
            'platform': self.platform
        }
        
        url = f"{self.admin_url}{self.api_prefix}/clients/register"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=registration_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"成功向管理服务器注册: {self.client_id}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"注册失败 ({response.status}): {error_text}")
                        return False
                        
        except aiohttp.ClientError as e:
            self.logger.error(f"注册请求失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"注册过程发生异常: {e}")
            return False
    
    async def connect_websocket(self):
        """连接到管理WebSocket进行实时通信"""
        try:
            self.logger.info(f"正在连接到WebSocket: {self.websocket_url}")
            
            # 创建WebSocket连接
            self.websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.connected = True
            self.reconnect_attempts = 0
            self.logger.info("WebSocket已连接到管理服务器")
            
            # 发送初始状态
            await self.send_heartbeat()
            
            # 开始监听命令
            await self.listen_for_commands()
            
        except ConnectionClosed:
            self.logger.warning("WebSocket连接已关闭")
            self.connected = False
            await self._handle_reconnect()
            
        except Exception as e:
            self.logger.error(f"WebSocket连接失败: {e}")
            self.connected = False
            await self._handle_reconnect()
    
    async def _handle_reconnect(self):
        """处理重连逻辑"""
        if not self.running:
            return
            
        self.reconnect_attempts += 1
        
        if (self.max_reconnect_attempts > 0 and 
            self.reconnect_attempts > self.max_reconnect_attempts):
            self.logger.error("已达到最大重连次数，停止重连")
            self.running = False
            return
        
        self.logger.info(f"将在{self.reconnect_delay}秒后尝试重连 (第{self.reconnect_attempts}次)")
        await asyncio.sleep(self.reconnect_delay)
        
        if self.running:
            await self.connect_websocket()
    
    async def send_heartbeat(self):
        """发送带有当前客户端状态的心跳包"""
        if not self.websocket or not self.connected:
            return
        
        heartbeat_data = {
            'type': 'heartbeat',
            'client_id': self.client_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'online' if self.is_enabled else 'disabled',
            'is_active': self.is_enabled,
            'system_info': {
                'hostname': self.hostname,
                'ip_address': self.ip_address,
                'platform': self.platform,
                'version': self.version
            }
        }
        
        try:
            await self.websocket.send(json.dumps(heartbeat_data))
            self.logger.debug("心跳包已发送")
        except Exception as e:
            self.logger.error(f"发送心跳包失败: {e}")
            self.connected = False
    
    async def listen_for_commands(self):
        """监听来自管理服务器的命令"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_command(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析命令失败: {e}")
                except Exception as e:
                    self.logger.error(f"处理命令时发生错误: {e}")
                    
        except ConnectionClosed:
            self.logger.warning("WebSocket连接已关闭")
            self.connected = False
        except Exception as e:
            self.logger.error(f"监听命令时发生错误: {e}")
            self.connected = False
    
    async def handle_command(self, command: Dict[str, Any]):
        """
        处理从管理服务器接收的命令
        
        Args:
            command: 命令数据字典
        """
        command_type = command.get('type')
        command_id = command.get('id')
        
        self.logger.info(f"收到命令: {command_type}")
        
        if command_type in self.command_handlers:
            try:
                result = await self.command_handlers[command_type](command)
                await self.send_command_ack(command_type, 'success', command_id, result)
            except Exception as e:
                self.logger.error(f"执行命令失败: {e}")
                await self.send_command_ack(command_type, 'failed', command_id, str(e))
        else:
            self.logger.warning(f"未知命令类型: {command_type}")
            await self.send_command_ack(command_type, 'unknown', command_id)
    
    async def send_command_ack(self, command_type: str, status: str, 
                              command_id: Optional[str] = None,
                              result: Any = None):
        """
        发送命令确认
        
        Args:
            command_type: 命令类型
            status: 执行状态
            command_id: 命令ID
            result: 执行结果
        """
        if not self.websocket or not self.connected:
            return
            
        ack_data = {
            'type': 'command_ack',
            'client_id': self.client_id,
            'command_type': command_type,
            'command_id': command_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if result is not None:
            ack_data['result'] = result
        
        try:
            await self.websocket.send(json.dumps(ack_data))
            self.logger.debug(f"命令确认已发送: {command_type} - {status}")
        except Exception as e:
            self.logger.error(f"发送命令确认失败: {e}")
    
    def register_command_handler(self, command_type: str, handler: Callable):
        """
        注册命令处理器
        
        Args:
            command_type: 命令类型
            handler: 处理函数(协程)
        """
        self.command_handlers[command_type] = handler
        self.logger.info(f"已注册命令处理器: {command_type}")
    
    # 默认命令处理器
    async def _handle_enable(self, command: Dict[str, Any]) -> str:
        """处理启用命令"""
        self.is_enabled = True
        self.logger.info("客户端已被管理员启用")
        return "客户端已启用"
    
    async def _handle_disable(self, command: Dict[str, Any]) -> str:
        """处理禁用命令"""
        self.is_enabled = False
        self.logger.info("客户端已被管理员禁用")
        return "客户端已禁用"
    
    async def _handle_restart(self, command: Dict[str, Any]) -> str:
        """处理重启命令"""
        self.logger.info("收到重启命令")
        # 这里可以实现实际的重启逻辑
        # 例如：设置标志让主程序重启
        return "重启命令已接收"
    
    async def _handle_get_status(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取状态命令"""
        return {
            'client_id': self.client_id,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'version': self.version,
            'platform': self.platform,
            'is_enabled': self.is_enabled,
            'connected': self.connected,
            'uptime': datetime.utcnow().isoformat()
        }
    
    async def _handle_ping(self, command: Dict[str, Any]) -> str:
        """处理ping命令"""
        return "pong"
    
    async def heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            if self.connected:
                await self.send_heartbeat()
            await asyncio.sleep(self.heartbeat_interval)
    
    async def start(self):
        """启动管理客户端"""
        self.logger.info("启动管理客户端")
        
        # 先尝试注册
        if not await self.register():
            self.logger.warning("初始注册失败，但仍将尝试连接")
        
        # 创建任务
        self.tasks = [
            asyncio.create_task(self.connect_websocket()),
            asyncio.create_task(self.heartbeat_loop())
        ]
        
        # 等待所有任务完成
        try:
            await asyncio.gather(*self.tasks)
        except Exception as e:
            self.logger.error(f"管理客户端运行错误: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """停止管理客户端"""
        self.logger.info("正在停止管理客户端")
        self.running = False
        
        # 关闭WebSocket连接
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # 取消所有任务
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.logger.info("管理客户端已停止")
    
    def is_client_enabled(self) -> bool:
        """检查客户端是否被启用"""
        return self.is_enabled