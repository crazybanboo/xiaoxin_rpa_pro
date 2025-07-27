"""
窗口管理模块测试
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from typing import List, Tuple

from core.window import WindowManager, WindowInfo, WindowState, create_window_manager


class TestWindowInfo:
    """测试WindowInfo类"""
    
    def test_window_info_init(self):
        """测试WindowInfo初始化"""
        window_info = WindowInfo(
            hwnd=12345,
            title="Test Window",
            class_name="TestClass",
            pid=1234,
            process_name="test.exe",
            rect=(100, 100, 500, 400),
            state=WindowState.NORMAL,
            visible=True,
            enabled=True
        )
        
        assert window_info.hwnd == 12345
        assert window_info.title == "Test Window"
        assert window_info.class_name == "TestClass"
        assert window_info.pid == 1234
        assert window_info.process_name == "test.exe"
        assert window_info.rect == (100, 100, 500, 400)
        assert window_info.state == WindowState.NORMAL
        assert window_info.visible is True
        assert window_info.enabled is True
    
    def test_window_info_properties(self):
        """测试WindowInfo属性"""
        window_info = WindowInfo(
            hwnd=12345,
            title="Test Window",
            class_name="TestClass",
            pid=1234,
            process_name="test.exe",
            rect=(100, 100, 500, 400),
            state=WindowState.NORMAL,
            visible=True,
            enabled=True
        )
        
        assert window_info.width == 400  # 500 - 100
        assert window_info.height == 300  # 400 - 100
        assert window_info.center == (300, 250)  # (100 + 400//2, 100 + 300//2)
    
    def test_window_info_repr(self):
        """测试WindowInfo字符串表示"""
        window_info = WindowInfo(
            hwnd=12345,
            title="Test Window",
            class_name="TestClass",
            pid=1234,
            process_name="test.exe",
            rect=(100, 100, 500, 400),
            state=WindowState.NORMAL,
            visible=True,
            enabled=True
        )
        
        repr_str = repr(window_info)
        assert "WindowInfo(hwnd=12345, title='Test Window', pid=1234)" == repr_str


class TestWindowState:
    """测试WindowState枚举"""
    
    def test_window_state_values(self):
        """测试WindowState枚举值"""
        assert WindowState.NORMAL.value == 0
        assert WindowState.MINIMIZED.value == 1
        assert WindowState.MAXIMIZED.value == 2
        assert WindowState.HIDDEN.value == 3


class TestWindowManager:
    """测试WindowManager类"""
    
    def test_window_manager_init(self):
        """测试WindowManager初始化"""
        manager = WindowManager(search_timeout=10.0, activate_timeout=3.0)
        
        assert manager.search_timeout == 10.0
        assert manager.activate_timeout == 3.0
    
    def test_window_manager_init_default(self):
        """测试WindowManager默认初始化"""
        manager = WindowManager()
        
        assert manager.search_timeout == 5.0
        assert manager.activate_timeout == 2.0
    
    @patch('core.window.win32gui')
    @patch('core.window.win32process')
    @patch('core.window.psutil')
    def test_get_all_windows_success(self, mock_psutil, mock_win32process, mock_win32gui):
        """测试获取所有窗口成功"""
        # 模拟win32gui
        mock_win32gui.EnumWindows.side_effect = lambda callback, param: callback(12345, param) and callback(12346, param)
        mock_win32gui.IsWindow.return_value = True
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.GetWindowText.side_effect = ["Window 1", "Window 2"]
        mock_win32gui.GetClassName.side_effect = ["Class1", "Class2"]
        mock_win32gui.GetWindowRect.side_effect = [(100, 100, 500, 400), (200, 200, 600, 500)]
        mock_win32gui.GetWindowPlacement.side_effect = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)]
        mock_win32gui.IsWindowEnabled.return_value = True
        
        # 模拟win32process
        mock_win32process.GetWindowThreadProcessId.side_effect = [(1, 1234), (2, 1235)]
        
        # 模拟psutil
        mock_process_1 = Mock()
        mock_process_1.name.return_value = "test1.exe"
        mock_process_2 = Mock()
        mock_process_2.name.return_value = "test2.exe"
        mock_psutil.Process.side_effect = [mock_process_1, mock_process_2]
        
        manager = WindowManager()
        windows = manager.get_all_windows()
        
        assert len(windows) == 2
        assert windows[0].title == "Window 1"
        assert windows[0].hwnd == 12345
        assert windows[0].pid == 1234
        assert windows[0].process_name == "test1.exe"
        assert windows[1].title == "Window 2"
        assert windows[1].hwnd == 12346
        assert windows[1].pid == 1235
        assert windows[1].process_name == "test2.exe"
    
    @patch('core.window.win32gui')
    def test_get_all_windows_enum_exception(self, mock_win32gui):
        """测试枚举窗口异常"""
        mock_win32gui.EnumWindows.side_effect = Exception("Enum error")
        
        manager = WindowManager()
        windows = manager.get_all_windows()
        
        assert windows == []
    
    @patch('core.window.win32gui')
    @patch('core.window.win32process')
    @patch('core.window.psutil')
    def test_get_all_windows_process_exception(self, mock_psutil, mock_win32process, mock_win32gui):
        """测试获取进程信息异常"""
        # 模拟win32gui
        mock_win32gui.EnumWindows.side_effect = lambda callback, param: callback(12345, param)
        mock_win32gui.IsWindow.return_value = True
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.GetWindowText.return_value = "Test Window"
        mock_win32gui.GetClassName.return_value = "TestClass"
        mock_win32gui.GetWindowRect.return_value = (100, 100, 500, 400)
        mock_win32gui.GetWindowPlacement.return_value = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        mock_win32gui.IsWindowEnabled.return_value = True
        
        # 模拟win32process
        mock_win32process.GetWindowThreadProcessId.return_value = (1, 1234)
        
        # 模拟psutil异常
        mock_psutil.Process.side_effect = [Exception("Process error")]
        mock_psutil.NoSuchProcess = Exception
        mock_psutil.AccessDenied = Exception
        
        manager = WindowManager()
        windows = manager.get_all_windows()
        
        assert len(windows) == 1
        assert windows[0].process_name == "Unknown"
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_title_exact_match(self, mock_get_all_windows):
        """测试根据标题精确查找窗口"""
        mock_windows = [
            WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True),
            WindowInfo(12346, "Another Window", "Class2", 1235, "other.exe", (200, 200, 600, 500), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        window = manager.find_window_by_title("Test Window", exact_match=True)
        
        assert window is not None
        assert window.title == "Test Window"
        assert window.hwnd == 12345
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_title_partial_match(self, mock_get_all_windows):
        """测试根据标题部分匹配查找窗口"""
        mock_windows = [
            WindowInfo(12345, "Test Window Application", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True),
            WindowInfo(12346, "Another Window", "Class2", 1235, "other.exe", (200, 200, 600, 500), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        window = manager.find_window_by_title("test window", exact_match=False)
        
        assert window is not None
        assert window.title == "Test Window Application"
        assert window.hwnd == 12345
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_title_not_found(self, mock_get_all_windows):
        """测试根据标题查找窗口失败"""
        mock_windows = [
            WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        window = manager.find_window_by_title("Non-existent Window")
        
        assert window is None
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_class(self, mock_get_all_windows):
        """测试根据类名查找窗口"""
        mock_windows = [
            WindowInfo(12345, "Test Window", "TestClass", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True),
            WindowInfo(12346, "Another Window", "OtherClass", 1235, "other.exe", (200, 200, 600, 500), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        window = manager.find_window_by_class("TestClass")
        
        assert window is not None
        assert window.class_name == "TestClass"
        assert window.hwnd == 12345
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_class_not_found(self, mock_get_all_windows):
        """测试根据类名查找窗口失败"""
        mock_windows = [
            WindowInfo(12345, "Test Window", "TestClass", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        window = manager.find_window_by_class("NonExistentClass")
        
        assert window is None
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_process(self, mock_get_all_windows):
        """测试根据进程名查找窗口"""
        mock_windows = [
            WindowInfo(12345, "Test Window 1", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True),
            WindowInfo(12346, "Test Window 2", "Class2", 1235, "test.exe", (200, 200, 600, 500), WindowState.NORMAL, True, True),
            WindowInfo(12347, "Other Window", "Class3", 1236, "other.exe", (300, 300, 700, 600), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        windows = manager.find_window_by_process("test.exe")
        
        assert len(windows) == 2
        assert windows[0].process_name == "test.exe"
        assert windows[1].process_name == "test.exe"
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_process_case_insensitive(self, mock_get_all_windows):
        """测试根据进程名查找窗口（大小写不敏感）"""
        mock_windows = [
            WindowInfo(12345, "Test Window", "Class1", 1234, "Test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        windows = manager.find_window_by_process("TEST.EXE")
        
        assert len(windows) == 1
        assert windows[0].process_name == "Test.exe"
    
    @patch.object(WindowManager, 'get_all_windows')
    def test_find_window_by_pid(self, mock_get_all_windows):
        """测试根据进程ID查找窗口"""
        mock_windows = [
            WindowInfo(12345, "Test Window 1", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True),
            WindowInfo(12346, "Test Window 2", "Class2", 1234, "test.exe", (200, 200, 600, 500), WindowState.NORMAL, True, True),
            WindowInfo(12347, "Other Window", "Class3", 1235, "other.exe", (300, 300, 700, 600), WindowState.NORMAL, True, True)
        ]
        mock_get_all_windows.return_value = mock_windows
        
        manager = WindowManager()
        windows = manager.find_window_by_pid(1234)
        
        assert len(windows) == 2
        assert windows[0].pid == 1234
        assert windows[1].pid == 1234
    
    @patch.object(WindowManager, 'find_window_by_title')
    @patch.object(WindowManager, 'find_window_by_class')
    @patch.object(WindowManager, 'find_window_by_process')
    @patch('time.sleep')
    def test_wait_for_window_by_title_success(self, mock_sleep, mock_find_by_process, mock_find_by_class, mock_find_by_title):
        """测试等待窗口出现成功（根据标题）"""
        mock_window = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        mock_find_by_title.return_value = mock_window
        
        manager = WindowManager()
        window = manager.wait_for_window(title="Test Window", timeout=1.0)
        
        assert window is not None
        assert window.title == "Test Window"
        mock_find_by_title.assert_called_once_with("Test Window")
    
    @patch.object(WindowManager, 'find_window_by_title')
    @patch.object(WindowManager, 'find_window_by_class')
    @patch.object(WindowManager, 'find_window_by_process')
    @patch('time.sleep')
    def test_wait_for_window_by_class_success(self, mock_sleep, mock_find_by_process, mock_find_by_class, mock_find_by_title):
        """测试等待窗口出现成功（根据类名）"""
        mock_window = WindowInfo(12345, "Test Window", "TestClass", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        mock_find_by_title.return_value = None
        mock_find_by_class.return_value = mock_window
        
        manager = WindowManager()
        window = manager.wait_for_window(class_name="TestClass", timeout=1.0)
        
        assert window is not None
        assert window.class_name == "TestClass"
        mock_find_by_class.assert_called_once_with("TestClass")
    
    @patch.object(WindowManager, 'find_window_by_title')
    @patch.object(WindowManager, 'find_window_by_class')
    @patch.object(WindowManager, 'find_window_by_process')
    @patch('time.sleep')
    def test_wait_for_window_by_process_success(self, mock_sleep, mock_find_by_process, mock_find_by_class, mock_find_by_title):
        """测试等待窗口出现成功（根据进程名）"""
        mock_window = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        mock_find_by_title.return_value = None
        mock_find_by_class.return_value = None
        mock_find_by_process.return_value = [mock_window]
        
        manager = WindowManager()
        window = manager.wait_for_window(process_name="test.exe", timeout=1.0)
        
        assert window is not None
        assert window.process_name == "test.exe"
        mock_find_by_process.assert_called_once_with("test.exe")
    
    @patch.object(WindowManager, 'find_window_by_title')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_window_timeout(self, mock_time, mock_sleep, mock_find_by_title):
        """测试等待窗口超时"""
        mock_find_by_title.return_value = None
        mock_time.side_effect = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
        
        manager = WindowManager()
        window = manager.wait_for_window(title="Non-existent Window", timeout=1.0)
        
        assert window is None
    
    @patch.object(WindowManager, 'find_window_by_title')
    def test_wait_for_window_default_timeout(self, mock_find_by_title):
        """测试等待窗口使用默认超时"""
        mock_find_by_title.return_value = None
        
        manager = WindowManager(search_timeout=10.0)
        
        # 模拟time.time使超时立即触发
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 11.0]
            window = manager.wait_for_window(title="Test Window")
        
        assert window is None
    
    @patch('core.window.win32gui')
    @patch('core.window.win32con')
    def test_activate_window_success(self, mock_win32con, mock_win32gui):
        """测试激活窗口成功"""
        mock_win32gui.IsWindow.return_value = True
        mock_win32con.SW_SHOW = 5
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.activate_window(window_info)
        
        assert result is True
        mock_win32gui.IsWindow.assert_called_once_with(12345)
        mock_win32gui.SetForegroundWindow.assert_called_once_with(12345)
        mock_win32gui.SetActiveWindow.assert_called_once_with(12345)
        mock_win32gui.ShowWindow.assert_called_once_with(12345, 5)
    
    @patch('core.window.win32gui')
    @patch('core.window.win32con')
    def test_activate_window_minimized(self, mock_win32con, mock_win32gui):
        """测试激活最小化窗口"""
        mock_win32gui.IsWindow.return_value = True
        mock_win32con.SW_RESTORE = 9
        mock_win32con.SW_SHOW = 5
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.MINIMIZED, True, True)
        
        manager = WindowManager()
        result = manager.activate_window(window_info)
        
        assert result is True
        mock_win32gui.ShowWindow.assert_has_calls([
            call(12345, 9),
            call(12345, 5)
        ])
    
    @patch('core.window.win32gui')
    def test_activate_window_invalid_handle(self, mock_win32gui):
        """测试激活无效窗口句柄"""
        mock_win32gui.IsWindow.return_value = False
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.activate_window(window_info)
        
        assert result is False
        mock_win32gui.IsWindow.assert_called_once_with(12345)
    
    @patch('core.window.win32gui')
    def test_activate_window_exception(self, mock_win32gui):
        """测试激活窗口异常"""
        mock_win32gui.IsWindow.return_value = True
        mock_win32gui.SetForegroundWindow.side_effect = Exception("Activate error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.activate_window(window_info)
        
        assert result is False
    
    @patch('core.window.win32gui')
    @patch('core.window.win32con')
    def test_close_window_success(self, mock_win32con, mock_win32gui):
        """测试关闭窗口成功"""
        mock_win32con.WM_CLOSE = 0x0010
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.close_window(window_info)
        
        assert result is True
        mock_win32gui.SendMessage.assert_called_once_with(12345, 0x0010, 0, 0)
    
    @patch('core.window.win32gui')
    def test_close_window_exception(self, mock_win32gui):
        """测试关闭窗口异常"""
        mock_win32gui.SendMessage.side_effect = Exception("Close error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.close_window(window_info)
        
        assert result is False
    
    @patch('core.window.win32gui')
    @patch('core.window.win32con')
    def test_minimize_window_success(self, mock_win32con, mock_win32gui):
        """测试最小化窗口成功"""
        mock_win32con.SW_MINIMIZE = 6
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.minimize_window(window_info)
        
        assert result is True
        mock_win32gui.ShowWindow.assert_called_once_with(12345, 6)
    
    @patch('core.window.win32gui')
    def test_minimize_window_exception(self, mock_win32gui):
        """测试最小化窗口异常"""
        mock_win32gui.ShowWindow.side_effect = Exception("Minimize error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.minimize_window(window_info)
        
        assert result is False
    
    @patch('core.window.win32gui')
    @patch('core.window.win32con')
    def test_maximize_window_success(self, mock_win32con, mock_win32gui):
        """测试最大化窗口成功"""
        mock_win32con.SW_MAXIMIZE = 3
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.maximize_window(window_info)
        
        assert result is True
        mock_win32gui.ShowWindow.assert_called_once_with(12345, 3)
    
    @patch('core.window.win32gui')
    def test_maximize_window_exception(self, mock_win32gui):
        """测试最大化窗口异常"""
        mock_win32gui.ShowWindow.side_effect = Exception("Maximize error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.maximize_window(window_info)
        
        assert result is False
    
    @patch('core.window.win32gui')
    def test_resize_window_success(self, mock_win32gui):
        """测试调整窗口大小成功"""
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        # 模拟成功的 Windows API 调用
        mock_win32gui.GetWindowRect.return_value = (100, 100, 700, 600)
        mock_win32gui.GetWindowPlacement.return_value = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        
        manager = WindowManager()
        result = manager.resize_window(window_info, 600, 500)
        
        # 检查返回的是 WindowInfo 对象而不是布尔值
        assert result is not None
        assert isinstance(result, WindowInfo)
        assert result.hwnd == 12345
        mock_win32gui.MoveWindow.assert_called_once_with(12345, 100, 100, 600, 500, True)
    
    @patch('core.window.win32gui')
    def test_resize_window_exception(self, mock_win32gui):
        """测试调整窗口大小异常"""
        mock_win32gui.MoveWindow.side_effect = Exception("Resize error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.resize_window(window_info, 600, 500)
        
        # 异常时应返回 None
        assert result is None
    
    @patch('core.window.win32gui')
    def test_move_window_success(self, mock_win32gui):
        """测试移动窗口成功"""
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        # 模拟成功的 Windows API 调用
        mock_win32gui.GetWindowRect.return_value = (200, 150, 600, 450)
        
        manager = WindowManager()
        result = manager.move_window(window_info, 200, 150)
        
        # 检查返回的是 WindowInfo 对象而不是布尔值
        assert result is not None
        assert isinstance(result, WindowInfo)
        assert result.hwnd == 12345
        mock_win32gui.MoveWindow.assert_called_once_with(12345, 200, 150, 400, 300, True)
    
    @patch('core.window.win32gui')
    def test_move_window_exception(self, mock_win32gui):
        """测试移动窗口异常"""
        mock_win32gui.MoveWindow.side_effect = Exception("Move error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.move_window(window_info, 200, 150)
        
        # 异常时应返回 None
        assert result is None
    
    @patch('core.window.win32gui')
    def test_get_window_text_success(self, mock_win32gui):
        """测试获取窗口文本成功"""
        mock_win32gui.GetWindowText.return_value = "Window Text"
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        text = manager.get_window_text(window_info)
        
        assert text == "Window Text"
        mock_win32gui.GetWindowText.assert_called_once_with(12345)
    
    @patch('core.window.win32gui')
    def test_get_window_text_exception(self, mock_win32gui):
        """测试获取窗口文本异常"""
        mock_win32gui.GetWindowText.side_effect = Exception("Get text error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        text = manager.get_window_text(window_info)
        
        assert text == ""
    
    @patch('core.window.win32gui')
    @patch('core.window.win32process')
    @patch('core.window.psutil')
    def test_get_child_windows_success(self, mock_psutil, mock_win32process, mock_win32gui):
        """测试获取子窗口成功"""
        # 模拟父窗口信息
        parent_window = WindowInfo(12345, "Parent Window", "ParentClass", 1234, "parent.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        # 模拟子窗口枚举
        mock_win32gui.EnumChildWindows.side_effect = lambda hwnd, callback, param: callback(12346, param) and callback(12347, param)
        mock_win32gui.GetWindowText.side_effect = ["Child 1", "Child 2"]
        mock_win32gui.GetClassName.side_effect = ["ChildClass1", "ChildClass2"]
        mock_win32gui.GetWindowRect.side_effect = [(110, 110, 250, 200), (260, 110, 400, 200)]
        mock_win32gui.GetWindowPlacement.side_effect = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)]
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.IsWindowEnabled.return_value = True
        
        # 模拟进程信息
        mock_win32process.GetWindowThreadProcessId.side_effect = [(1, 1234), (2, 1234)]
        mock_process = Mock()
        mock_process.name.return_value = "parent.exe"
        mock_psutil.Process.return_value = mock_process
        
        manager = WindowManager()
        child_windows = manager.get_child_windows(parent_window)
        
        assert len(child_windows) == 2
        assert child_windows[0].title == "Child 1"
        assert child_windows[0].hwnd == 12346
        assert child_windows[1].title == "Child 2"
        assert child_windows[1].hwnd == 12347
    
    @patch('core.window.win32gui')
    def test_get_child_windows_exception(self, mock_win32gui):
        """测试获取子窗口异常"""
        mock_win32gui.EnumChildWindows.side_effect = Exception("Enum child error")
        
        parent_window = WindowInfo(12345, "Parent Window", "ParentClass", 1234, "parent.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        child_windows = manager.get_child_windows(parent_window)
        
        assert child_windows == []
    
    @patch('core.window.win32gui')
    @patch('core.window.win32con')
    def test_is_window_responsive_success(self, mock_win32con, mock_win32gui):
        """测试检查窗口响应成功"""
        mock_win32gui.SendMessageTimeout.return_value = (1, 0)
        mock_win32con.WM_NULL = 0
        mock_win32con.SMTO_ABORTIFHUNG = 2
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.is_window_responsive(window_info, timeout=2.0)
        
        assert result is True
        mock_win32gui.SendMessageTimeout.assert_called_once_with(12345, 0, 0, 0, 2, 2000)
    
    @patch('core.window.win32gui')
    @patch('core.window.win32con')
    def test_is_window_responsive_unresponsive(self, mock_win32con, mock_win32gui):
        """测试检查窗口无响应"""
        mock_win32gui.SendMessageTimeout.return_value = (0, 0)
        mock_win32con.WM_NULL = 0
        mock_win32con.SMTO_ABORTIFHUNG = 2
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.is_window_responsive(window_info, timeout=2.0)
        
        assert result is False
    
    @patch('core.window.win32gui')
    def test_is_window_responsive_exception(self, mock_win32gui):
        """测试检查窗口响应异常"""
        mock_win32gui.SendMessageTimeout.side_effect = Exception("Response check error")
        
        window_info = WindowInfo(12345, "Test Window", "Class1", 1234, "test.exe", (100, 100, 500, 400), WindowState.NORMAL, True, True)
        
        manager = WindowManager()
        result = manager.is_window_responsive(window_info)
        
        assert result is False


class TestCreateWindowManager:
    """测试create_window_manager函数"""
    
    def test_create_window_manager_default(self):
        """测试创建默认窗口管理器"""
        manager = create_window_manager({})
        
        assert isinstance(manager, WindowManager)
        assert manager.search_timeout == 5.0
        assert manager.activate_timeout == 2.0
    
    def test_create_window_manager_with_config(self):
        """测试使用配置创建窗口管理器"""
        config = {
            'search_timeout': 10.0,
            'activate_timeout': 3.0
        }
        
        manager = create_window_manager(config)
        
        assert isinstance(manager, WindowManager)
        assert manager.search_timeout == 10.0
        assert manager.activate_timeout == 3.0


class TestWindowManagerIntegration:
    """测试WindowManager集成功能"""
    
    @patch('core.window.win32gui')
    @patch('core.window.win32process')
    @patch('core.window.psutil')
    def test_full_window_workflow(self, mock_psutil, mock_win32process, mock_win32gui):
        """测试完整窗口工作流"""
        # 模拟获取窗口列表
        mock_win32gui.EnumWindows.side_effect = lambda callback, param: callback(12345, param)
        mock_win32gui.IsWindow.return_value = True
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.GetWindowText.return_value = "Test Application"
        mock_win32gui.GetClassName.return_value = "TestAppClass"
        mock_win32gui.GetWindowRect.return_value = (100, 100, 500, 400)
        mock_win32gui.GetWindowPlacement.return_value = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        mock_win32gui.IsWindowEnabled.return_value = True
        mock_win32gui.SendMessageTimeout.return_value = (1, 0)
        
        mock_win32process.GetWindowThreadProcessId.return_value = (1, 1234)
        
        mock_process = Mock()
        mock_process.name.return_value = "testapp.exe"
        mock_psutil.Process.return_value = mock_process
        
        manager = WindowManager()
        
        # 1. 查找窗口
        window = manager.find_window_by_title("Test Application")
        assert window is not None
        
        # 2. 检查窗口响应
        responsive = manager.is_window_responsive(window)
        assert responsive is True
        
        # 3. 激活窗口
        activate_result = manager.activate_window(window)
        assert activate_result is True
        
        # 4. 获取窗口文本
        text = manager.get_window_text(window)
        assert text == "Test Application"
        
        # 5. 移动窗口
        move_result = manager.move_window(window, 200, 150)
        assert move_result is not None
        assert isinstance(move_result, WindowInfo)
        
        # 6. 调整窗口大小
        resize_result = manager.resize_window(window, 600, 500)
        assert resize_result is not None
        assert isinstance(resize_result, WindowInfo)