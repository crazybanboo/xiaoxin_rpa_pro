"""
测试鼠标操作模块
"""

import pytest
from unittest.mock import patch, MagicMock, call

from core.mouse import MouseController, MouseButton, create_mouse_controller
from core.vision import MatchResult


@pytest.mark.unit
class TestMouseButton:
    """测试鼠标按键枚举"""
    
    def test_mouse_button_values(self):
        """测试鼠标按键枚举值"""
        assert MouseButton.LEFT.value == 'left'
        assert MouseButton.RIGHT.value == 'right'
        assert MouseButton.MIDDLE.value == 'middle'


@pytest.mark.unit
class TestMouseController:
    """测试鼠标控制器"""
    
    def test_mouse_controller_init(self):
        """测试鼠标控制器初始化"""
        controller = MouseController(
            click_delay=0.2,
            move_duration=1.0,
            fail_safe=False
        )
        
        assert controller.click_delay == 0.2
        assert controller.move_duration == 1.0
    
    def test_mouse_controller_init_default(self):
        """测试鼠标控制器默认初始化"""
        controller = MouseController()
        
        assert controller.click_delay == 0.1
        assert controller.move_duration == 0.5
    
    def test_get_position(self, mock_pyautogui):
        """测试获取鼠标位置"""
        controller = MouseController()
        
        position = controller.get_position()
        
        assert position == (500, 500)
        mock_pyautogui['position'].assert_called_once()
    
    def test_move_to_success(self, mock_pyautogui):
        """测试成功移动鼠标"""
        controller = MouseController()
        
        result = controller.move_to(100, 200)
        
        assert result is True
        mock_pyautogui['moveTo'].assert_called_once_with(100, 200, duration=0.5)
    
    def test_move_to_with_duration(self, mock_pyautogui):
        """测试带持续时间的鼠标移动"""
        controller = MouseController()
        
        result = controller.move_to(100, 200, duration=1.0)
        
        assert result is True
        mock_pyautogui['moveTo'].assert_called_once_with(100, 200, duration=1.0)
    
    def test_move_to_exception(self, mock_pyautogui):
        """测试鼠标移动异常"""
        controller = MouseController()
        mock_pyautogui['moveTo'].side_effect = Exception("Test error")
        
        result = controller.move_to(100, 200)
        
        assert result is False
    
    def test_click_at_position(self, mock_pyautogui):
        """测试在指定位置点击"""
        controller = MouseController()
        
        result = controller.click(100, 200)
        
        assert result is True
        mock_pyautogui['click'].assert_called_once_with(
            100, 200, clicks=1, interval=0.0, button='left'
        )
    
    def test_click_current_position(self, mock_pyautogui):
        """测试在当前位置点击"""
        controller = MouseController()
        
        result = controller.click()
        
        assert result is True
        mock_pyautogui['click'].assert_called_once_with(
            clicks=1, interval=0.0, button='left'
        )
    
    def test_click_with_button(self, mock_pyautogui):
        """测试使用指定按键点击"""
        controller = MouseController()
        
        result = controller.click(100, 200, button=MouseButton.RIGHT)
        
        assert result is True
        mock_pyautogui['click'].assert_called_once_with(
            100, 200, clicks=1, interval=0.0, button='right'
        )
    
    def test_click_multiple_times(self, mock_pyautogui):
        """测试多次点击"""
        controller = MouseController()
        
        result = controller.click(100, 200, clicks=3, interval=0.1)
        
        assert result is True
        mock_pyautogui['click'].assert_called_once_with(
            100, 200, clicks=3, interval=0.1, button='left'
        )
    
    def test_click_exception(self, mock_pyautogui):
        """测试点击异常"""
        controller = MouseController()
        mock_pyautogui['click'].side_effect = Exception("Test error")
        
        result = controller.click(100, 200)
        
        assert result is False
    
    def test_double_click(self, mock_pyautogui):
        """测试双击"""
        controller = MouseController()
        
        result = controller.double_click(100, 200)
        
        assert result is True
        mock_pyautogui['click'].assert_called_once_with(
            100, 200, clicks=2, interval=0.1, button='left'
        )
    
    def test_right_click(self, mock_pyautogui):
        """测试右键点击"""
        controller = MouseController()
        
        result = controller.right_click(100, 200)
        
        assert result is True
        mock_pyautogui['click'].assert_called_once_with(
            100, 200, clicks=1, interval=0.0, button='right'
        )
    
    def test_drag_success(self, mock_pyautogui):
        """测试成功拖拽"""
        controller = MouseController()
        
        result = controller.drag(100, 200, 300, 400)
        
        assert result is True
        mock_pyautogui['drag'].assert_called_once_with(
            200, 200, duration=0.5, button='left'
        )
    
    def test_drag_with_duration(self, mock_pyautogui):
        """测试带持续时间的拖拽"""
        controller = MouseController()
        
        result = controller.drag(100, 200, 300, 400, duration=1.0)
        
        assert result is True
        mock_pyautogui['drag'].assert_called_once_with(
            200, 200, duration=1.0, button='left'
        )
    
    def test_drag_with_button(self, mock_pyautogui):
        """测试使用指定按键拖拽"""
        controller = MouseController()
        
        result = controller.drag(100, 200, 300, 400, button=MouseButton.RIGHT)
        
        assert result is True
        mock_pyautogui['drag'].assert_called_once_with(
            200, 200, duration=0.5, button='right'
        )
    
    def test_drag_exception(self, mock_pyautogui):
        """测试拖拽异常"""
        controller = MouseController()
        mock_pyautogui['drag'].side_effect = Exception("Test error")
        
        result = controller.drag(100, 200, 300, 400)
        
        assert result is False
    
    def test_scroll_up(self, mock_pyautogui):
        """测试向上滚动"""
        controller = MouseController()
        
        result = controller.scroll(100, 200, 3, 'up')
        
        assert result is True
        mock_pyautogui['moveTo'].assert_called_once_with(100, 200, duration=0.5)
        mock_pyautogui['scroll'].assert_called_once_with(3)
    
    def test_scroll_down(self, mock_pyautogui):
        """测试向下滚动"""
        controller = MouseController()
        
        result = controller.scroll(100, 200, 3, 'down')
        
        assert result is True
        mock_pyautogui['moveTo'].assert_called_once_with(100, 200, duration=0.5)
        mock_pyautogui['scroll'].assert_called_once_with(-3)
    
    def test_scroll_move_fail(self, mock_pyautogui):
        """测试滚动时移动失败"""
        controller = MouseController()
        mock_pyautogui['moveTo'].side_effect = Exception("Move failed")
        
        result = controller.scroll(100, 200, 3)
        
        assert result is False
    
    def test_scroll_exception(self, mock_pyautogui):
        """测试滚动异常"""
        controller = MouseController()
        mock_pyautogui['scroll'].side_effect = Exception("Scroll failed")
        
        result = controller.scroll(100, 200, 3)
        
        assert result is False
    
    def test_click_match_result(self, mock_pyautogui):
        """测试点击匹配结果"""
        controller = MouseController()
        match_result = MatchResult(100, 200, 50, 30, 0.95)
        
        result = controller.click_match_result(match_result)
        
        assert result is True
        # 应该点击匹配结果的中心点 (125, 215)
        mock_pyautogui['click'].assert_called_once_with(
            125, 215, clicks=1, interval=0.0, button='left'
        )
    
    def test_hover(self, mock_pyautogui):
        """测试悬停"""
        controller = MouseController()
        
        with patch('time.sleep') as mock_sleep:
            result = controller.hover(100, 200)
            
            assert result is True
            mock_pyautogui['moveTo'].assert_called_once_with(100, 200, duration=0.5)
            mock_sleep.assert_called_once_with(0.1)
    
    def test_hover_with_duration(self, mock_pyautogui):
        """测试带持续时间的悬停"""
        controller = MouseController()
        
        with patch('time.sleep') as mock_sleep:
            result = controller.hover(100, 200, duration=1.0)
            
            assert result is True
            mock_pyautogui['moveTo'].assert_called_once_with(100, 200, duration=1.0)
            mock_sleep.assert_called_once_with(0.1)
    
    def test_hover_exception(self, mock_pyautogui):
        """测试悬停异常"""
        controller = MouseController()
        mock_pyautogui['moveTo'].side_effect = Exception("Hover failed")
        
        result = controller.hover(100, 200)
        
        assert result is False
    
    def test_press_and_hold(self, mock_pyautogui):
        """测试按住鼠标"""
        controller = MouseController()
        
        with patch('time.sleep') as mock_sleep:
            result = controller.press_and_hold(100, 200, duration=2.0)
            
            assert result is True
            mock_pyautogui['moveTo'].assert_called_once_with(100, 200, duration=0.5)
            mock_pyautogui['mouseDown'].assert_called_once()
            mock_pyautogui['mouseUp'].assert_called_once()
            mock_sleep.assert_called_once_with(2.0)
    
    def test_press_and_hold_move_fail(self, mock_pyautogui):
        """测试按住鼠标时移动失败"""
        controller = MouseController()
        mock_pyautogui['moveTo'].side_effect = Exception("Move failed")
        
        result = controller.press_and_hold(100, 200)
        
        assert result is False
    
    def test_click_and_drag(self, mock_pyautogui):
        """测试点击并拖拽"""
        controller = MouseController()
        
        result = controller.click_and_drag(100, 200, 300, 400)
        
        assert result is True
        # 检查moveTo被调用了两次
        assert mock_pyautogui['moveTo'].call_count == 2
        # 检查第一次和第二次调用
        calls = mock_pyautogui['moveTo'].call_args_list
        assert calls[0] == call(100, 200, duration=0.5)
        assert calls[1] == call(300, 400, duration=0.5)
        mock_pyautogui['mouseDown'].assert_called_once()
        mock_pyautogui['mouseUp'].assert_called_once()
    
    def test_click_and_drag_with_duration(self, mock_pyautogui):
        """测试带持续时间的点击并拖拽"""
        controller = MouseController()
        
        result = controller.click_and_drag(100, 200, 300, 400, duration=2.0)
        
        assert result is True
        # 检查moveTo被调用了两次
        assert mock_pyautogui['moveTo'].call_count == 2
        # 检查第一次和第二次调用
        calls = mock_pyautogui['moveTo'].call_args_list
        assert calls[0] == call(100, 200, duration=0.5)
        assert calls[1] == call(300, 400, duration=2.0)
        mock_pyautogui['mouseDown'].assert_called_once()
        mock_pyautogui['mouseUp'].assert_called_once()
    
    def test_click_and_drag_move_fail(self, mock_pyautogui):
        """测试点击并拖拽时移动失败"""
        controller = MouseController()
        mock_pyautogui['moveTo'].side_effect = Exception("Move failed")
        
        result = controller.click_and_drag(100, 200, 300, 400)
        
        assert result is False
    
    def test_is_position_safe_true(self, mock_pyautogui):
        """测试位置安全检查（安全位置）"""
        controller = MouseController()
        
        result = controller.is_position_safe(100, 200)
        
        assert result is True
    
    def test_is_position_safe_false(self, mock_pyautogui):
        """测试位置安全检查（不安全位置）"""
        controller = MouseController()
        
        # 测试边界位置
        assert controller.is_position_safe(0, 100) is False
        assert controller.is_position_safe(100, 0) is False
        assert controller.is_position_safe(1919, 100) is False
        assert controller.is_position_safe(100, 1079) is False
    
    def test_is_position_safe_failsafe_disabled(self, mock_pyautogui):
        """测试位置安全检查（失败保护禁用）"""
        controller = MouseController(fail_safe=False)
        
        with patch('pyautogui.FAILSAFE', False):
            result = controller.is_position_safe(0, 0)
            
            assert result is True
    
    def test_get_screen_size(self, mock_pyautogui):
        """测试获取屏幕尺寸"""
        controller = MouseController()
        
        size = controller.get_screen_size()
        
        assert size == (1920, 1080)
        mock_pyautogui['size'].assert_called_once()
    
    def test_set_click_delay(self, mock_pyautogui):
        """测试设置点击延迟"""
        controller = MouseController()
        
        controller.set_click_delay(0.5)
        
        assert controller.click_delay == 0.5
    
    def test_enable_fail_safe(self, mock_pyautogui):
        """测试启用失败保护"""
        controller = MouseController()
        
        controller.enable_fail_safe(True)
        controller.enable_fail_safe(False)
        
        # 测试调用了两次设置


@pytest.mark.unit
class TestCreateMouseController:
    """测试创建鼠标控制器函数"""
    
    def test_create_mouse_controller_default(self):
        """测试创建默认鼠标控制器"""
        config = {}
        controller = create_mouse_controller(config)
        
        assert isinstance(controller, MouseController)
        assert controller.click_delay == 0.1
        assert controller.move_duration == 0.5
    
    def test_create_mouse_controller_with_config(self):
        """测试使用配置创建鼠标控制器"""
        config = {
            'click_delay': 0.2,
            'move_duration': 1.0,
            'fail_safe': False
        }
        controller = create_mouse_controller(config)
        
        assert isinstance(controller, MouseController)
        assert controller.click_delay == 0.2
        assert controller.move_duration == 1.0


@pytest.mark.integration
class TestMouseControllerIntegration:
    """鼠标控制器集成测试"""
    
    def test_complex_mouse_operations(self, mock_pyautogui):
        """测试复杂的鼠标操作"""
        controller = MouseController()
        
        # 执行一系列鼠标操作
        assert controller.move_to(100, 100) is True
        assert controller.click() is True
        assert controller.drag(100, 100, 200, 200) is True
        assert controller.scroll(150, 150, 3) is True
        assert controller.right_click(200, 200) is True
        
        # 验证调用次数
        assert mock_pyautogui['moveTo'].call_count >= 2
        assert mock_pyautogui['click'].call_count == 2
        assert mock_pyautogui['drag'].call_count == 1
        assert mock_pyautogui['scroll'].call_count == 1
    
    def test_mouse_with_match_result(self, mock_pyautogui):
        """测试鼠标与匹配结果配合使用"""
        controller = MouseController()
        match_result = MatchResult(100, 200, 50, 30, 0.95)
        
        # 点击匹配结果
        result = controller.click_match_result(match_result)
        
        assert result is True
        # 验证点击了中心位置
        mock_pyautogui['click'].assert_called_once_with(
            125, 215, clicks=1, interval=0.0, button='left'
        )