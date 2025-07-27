"""
管理客户端测试用例
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from core.admin_client import AdminClient
from core.config import Config


@pytest.fixture
def mock_config():
    """创建模拟配置"""
    config = Mock(spec=Config)
    config.get.side_effect = lambda key, default=None: {
        # 管理客户端配置已硬编码，不再从配置文件读取
        'app.version': '1.0.2'
    }.get(key, default)
    return config


@pytest.fixture
def admin_client(mock_config):
    """创建AdminClient实例"""
    return AdminClient(mock_config)


class TestAdminClient:
    """AdminClient测试类"""
    
    def test_init(self, admin_client):
        """测试初始化"""
        assert admin_client.client_id is not None
        assert admin_client.hostname is not None
        assert admin_client.ip_address is not None
        assert admin_client.version == '1.0.2'
        assert admin_client.running is True
        assert admin_client.connected is False
        assert admin_client.is_enabled is True
    
    def test_generate_client_id(self, admin_client):
        """测试客户端ID生成"""
        client_id = admin_client._generate_client_id()
        assert client_id is not None
        assert '_' in client_id
        assert len(client_id) > 10
    
    def test_get_local_ip(self, admin_client):
        """测试获取本地IP"""
        ip = admin_client._get_local_ip()
        assert ip is not None
        assert '.' in ip
    
    @pytest.mark.asyncio
    async def test_register_success(self, admin_client):
        """测试成功注册"""
        with patch('core.admin_client.aiohttp.ClientSession') as mock_session:
            # 模拟成功的 HTTP 响应
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'code': 20000, 'data': {}})
            
            # 模拟 session.post 的上下文管理器
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post_context.__aexit__ = AsyncMock(return_value=False)
            
            # 模拟 session 实例
            mock_session_instance = AsyncMock()
            mock_session_instance.post = Mock(return_value=mock_post_context)
            
            # 模拟 ClientSession 的上下文管理器
            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_context.__aexit__ = AsyncMock(return_value=False)
            
            mock_session.return_value = mock_session_context
            
            result = await admin_client.register()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_register_failure(self, admin_client):
        """测试注册失败"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value='Bad Request')
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            result = await admin_client.register()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_heartbeat(self, admin_client):
        """测试发送心跳"""
        admin_client.websocket = AsyncMock()
        admin_client.connected = True
        
        await admin_client.send_heartbeat()
        
        # 验证心跳数据被发送
        assert admin_client.websocket.send.called
        call_args = admin_client.websocket.send.call_args[0][0]
        heartbeat_data = json.loads(call_args)
        
        assert heartbeat_data['type'] == 'heartbeat'
        assert heartbeat_data['client_id'] == admin_client.client_id
        assert heartbeat_data['status'] == 'online'
    
    @pytest.mark.asyncio
    async def test_handle_enable_command(self, admin_client):
        """测试处理启用命令"""
        command = {'type': 'enable', 'id': 'test-id'}
        
        result = await admin_client._handle_enable(command)
        
        assert admin_client.is_enabled is True
        assert result == "客户端已启用"
    
    @pytest.mark.asyncio
    async def test_handle_disable_command(self, admin_client):
        """测试处理禁用命令"""
        command = {'type': 'disable', 'id': 'test-id'}
        
        result = await admin_client._handle_disable(command)
        
        assert admin_client.is_enabled is False
        assert result == "客户端已禁用"
    
    @pytest.mark.asyncio
    async def test_handle_get_status_command(self, admin_client):
        """测试处理获取状态命令"""
        command = {'type': 'get_status', 'id': 'test-id'}
        
        result = await admin_client._handle_get_status(command)
        
        assert isinstance(result, dict)
        assert result['client_id'] == admin_client.client_id
        assert result['hostname'] == admin_client.hostname
        assert result['is_enabled'] == admin_client.is_enabled
    
    @pytest.mark.asyncio
    async def test_handle_ping_command(self, admin_client):
        """测试处理ping命令"""
        command = {'type': 'ping', 'id': 'test-id'}
        
        result = await admin_client._handle_ping(command)
        
        assert result == "pong"
    
    def test_register_command_handler(self, admin_client):
        """测试注册命令处理器"""
        async def custom_handler(command):
            return "custom result"
        
        admin_client.register_command_handler('custom', custom_handler)
        
        assert 'custom' in admin_client.command_handlers
        assert admin_client.command_handlers['custom'] == custom_handler
    
    @pytest.mark.asyncio
    async def test_handle_command_with_ack(self, admin_client):
        """测试处理命令并发送确认"""
        admin_client.websocket = AsyncMock()
        admin_client.connected = True
        
        command = {'type': 'ping', 'id': 'test-id'}
        await admin_client.handle_command(command)
        
        # 验证确认消息被发送
        assert admin_client.websocket.send.called
        call_args = admin_client.websocket.send.call_args[0][0]
        ack_data = json.loads(call_args)
        
        assert ack_data['type'] == 'command_ack'
        assert ack_data['command_type'] == 'ping'
        assert ack_data['status'] == 'success'
        assert ack_data['result'] == 'pong'
    
    def test_is_client_enabled(self, admin_client):
        """测试检查客户端是否启用"""
        admin_client.is_enabled = True
        assert admin_client.is_client_enabled() is True
        
        admin_client.is_enabled = False
        assert admin_client.is_client_enabled() is False
    
    @pytest.mark.asyncio
    async def test_stop(self, admin_client):
        """测试停止客户端"""
        # 使用 patch 来模拟 asyncio.gather
        with patch('core.admin_client.asyncio.gather', new_callable=AsyncMock) as mock_gather:
            # 创建模拟任务
            mock_task = Mock()
            mock_task.done = Mock(return_value=False)
            mock_task.cancel = Mock()
            
            mock_websocket = AsyncMock()
            mock_websocket.close = AsyncMock()
            admin_client.websocket = mock_websocket
            admin_client.tasks = [mock_task]
            
            await admin_client.stop()
            
            assert admin_client.running is False
            # 检查 websocket.close 被调用
            mock_websocket.close.assert_called_once()
            assert admin_client.websocket is None
            # 检查任务被取消
            mock_task.cancel.assert_called_once()
            # 检查 asyncio.gather 被调用
            mock_gather.assert_called_once()