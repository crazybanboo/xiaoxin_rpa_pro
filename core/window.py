"""
窗口监控模块
使用Win32 API获取窗口信息和进行窗口操作
"""

import time
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

import win32gui
import win32con
import win32process
import win32api
import psutil

from .logger import LoggerMixin


class WindowState(Enum):
    """窗口状态枚举"""
    NORMAL = 0
    MINIMIZED = 1
    MAXIMIZED = 2
    HIDDEN = 3


@dataclass
class WindowInfo:
    """窗口信息类"""
    hwnd: int
    title: str
    class_name: str
    pid: int
    process_name: str
    rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    state: WindowState
    visible: bool
    enabled: bool
    
    @property
    def width(self) -> int:
        """窗口宽度"""
        return self.rect[2] - self.rect[0]
    
    @property
    def height(self) -> int:
        """窗口高度"""
        return self.rect[3] - self.rect[1]
    
    @property
    def center(self) -> Tuple[int, int]:
        """窗口中心点"""
        return (
            self.rect[0] + self.width // 2,
            self.rect[1] + self.height // 2
        )
    
    def __repr__(self) -> str:
        return f"WindowInfo(hwnd={self.hwnd}, title='{self.title}', pid={self.pid})"


class WindowManager(LoggerMixin):
    """窗口管理器"""
    
    def __init__(self, search_timeout: float = 5.0, activate_timeout: float = 2.0):
        """
        初始化窗口管理器
        
        Args:
            search_timeout: 搜索超时时间
            activate_timeout: 激活超时时间
        """
        self.search_timeout = search_timeout
        self.activate_timeout = activate_timeout
        
        self.logger.info(f"窗口管理器初始化完成，搜索超时: {search_timeout}秒")
    
    def get_all_windows(self) -> List[WindowInfo]:
        """
        获取所有窗口信息
        
        Returns:
            窗口信息列表
        """
        windows = []
        
        def enum_callback(hwnd, param):
            try:
                if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # 获取进程信息
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = "Unknown"
                    
                    # 获取窗口位置
                    rect = win32gui.GetWindowRect(hwnd)
                    
                    # 获取窗口状态
                    placement = win32gui.GetWindowPlacement(hwnd)
                    state = WindowState(placement[1])
                    
                    # 获取窗口属性
                    visible = win32gui.IsWindowVisible(hwnd)
                    enabled = win32gui.IsWindowEnabled(hwnd)
                    
                    window_info = WindowInfo(
                        hwnd=hwnd,
                        title=title,
                        class_name=class_name,
                        pid=pid,
                        process_name=process_name,
                        rect=rect,
                        state=state,
                        visible=visible,
                        enabled=enabled
                    )
                    
                    windows.append(window_info)
                    
            except Exception as e:
                self.logger.debug(f"获取窗口信息失败: {e}")
            
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, None)
            self.logger.debug(f"获取到 {len(windows)} 个窗口")
            return windows
            
        except Exception as e:
            self.logger.error(f"枚举窗口失败: {e}")
            return []
    
    def find_window_by_title(self, title: str, exact_match: bool = False) -> Optional[WindowInfo]:
        """
        根据标题查找窗口
        
        Args:
            title: 窗口标题
            exact_match: 是否精确匹配
        
        Returns:
            窗口信息
        """
        windows = self.get_all_windows()
        
        for window in windows:
            if exact_match:
                if window.title == title:
                    return window
            else:
                if title.lower() in window.title.lower():
                    return window
        
        return None
    
    def find_window_by_class(self, class_name: str) -> Optional[WindowInfo]:
        """
        根据类名查找窗口
        
        Args:
            class_name: 窗口类名
        
        Returns:
            窗口信息
        """
        windows = self.get_all_windows()
        
        for window in windows:
            if window.class_name == class_name:
                return window
        
        return None
    
    def find_window_by_process(self, process_name: str) -> List[WindowInfo]:
        """
        根据进程名查找窗口
        
        Args:
            process_name: 进程名
        
        Returns:
            窗口信息列表
        """
        windows = self.get_all_windows()
        result = []
        
        for window in windows:
            if window.process_name.lower() == process_name.lower():
                result.append(window)
        
        return result
    
    def find_window_by_pid(self, pid: int) -> List[WindowInfo]:
        """
        根据进程ID查找窗口
        
        Args:
            pid: 进程ID
        
        Returns:
            窗口信息列表
        """
        windows = self.get_all_windows()
        result = []
        
        for window in windows:
            if window.pid == pid:
                result.append(window)
        
        return result
    
    def wait_for_window(self, 
                       title: Optional[str] = None,
                       class_name: Optional[str] = None,
                       process_name: Optional[str] = None,
                       timeout: Optional[float] = None) -> Optional[WindowInfo]:
        """
        等待窗口出现
        
        Args:
            title: 窗口标题
            class_name: 窗口类名
            process_name: 进程名
            timeout: 超时时间
        
        Returns:
            窗口信息
        """
        if timeout is None:
            timeout = self.search_timeout
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if title:
                window = self.find_window_by_title(title)
                if window:
                    return window
            
            if class_name:
                window = self.find_window_by_class(class_name)
                if window:
                    return window
            
            if process_name:
                windows = self.find_window_by_process(process_name)
                if windows:
                    return windows[0]
            
            time.sleep(0.1)
        
        return None
    
    def activate_window(self, window_info: WindowInfo) -> bool:
        """
        激活窗口
        
        Args:
            window_info: 窗口信息
        
        Returns:
            操作是否成功
        """
        try:
            hwnd = window_info.hwnd
            
            # 检查窗口是否仍然有效
            if not win32gui.IsWindow(hwnd):
                self.logger.error(f"窗口句柄无效: {hwnd}")
                return False
            
            # 如果窗口最小化，先还原
            if window_info.state == WindowState.MINIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 将窗口置于前台
            win32gui.SetForegroundWindow(hwnd)
            
            # 激活窗口
            win32gui.SetActiveWindow(hwnd)
            
            # 确保窗口可见
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            
            self.logger.info(f"窗口激活成功: {window_info.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"窗口激活失败: {e}")
            return False
    
    def close_window(self, window_info: WindowInfo) -> bool:
        """
        关闭窗口
        
        Args:
            window_info: 窗口信息
        
        Returns:
            操作是否成功
        """
        try:
            hwnd = window_info.hwnd
            
            # 发送关闭消息
            win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            self.logger.info(f"窗口关闭成功: {window_info.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"窗口关闭失败: {e}")
            return False
    
    def minimize_window(self, window_info: WindowInfo) -> bool:
        """
        最小化窗口
        
        Args:
            window_info: 窗口信息
        
        Returns:
            操作是否成功
        """
        try:
            hwnd = window_info.hwnd
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            
            self.logger.info(f"窗口最小化成功: {window_info.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"窗口最小化失败: {e}")
            return False
    
    def maximize_window(self, window_info: WindowInfo) -> bool:
        """
        最大化窗口
        
        Args:
            window_info: 窗口信息
        
        Returns:
            操作是否成功
        """
        try:
            hwnd = window_info.hwnd
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            
            self.logger.info(f"窗口最大化成功: {window_info.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"窗口最大化失败: {e}")
            return False
    
    def resize_window(self, window_info: WindowInfo, width: int, height: int) -> Optional[WindowInfo]:
        """
        调整窗口大小
        
        Args:
            window_info: 窗口信息
            width: 新宽度
            height: 新高度
        
        Returns:
            更新后的窗口信息，失败时返回None
        """
        try:
            hwnd = window_info.hwnd
            x, y = window_info.rect[0], window_info.rect[1]
            
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            
            # 获取更新后的窗口信息
            new_rect = win32gui.GetWindowRect(hwnd)
            placement = win32gui.GetWindowPlacement(hwnd)
            new_state = WindowState(placement[1])
            
            updated_window_info = WindowInfo(
                hwnd=window_info.hwnd,
                title=window_info.title,
                class_name=window_info.class_name,
                pid=window_info.pid,
                process_name=window_info.process_name,
                rect=new_rect,
                state=new_state,
                visible=window_info.visible,
                enabled=window_info.enabled
            )
            
            self.logger.info(f"窗口大小调整成功: {window_info.title}, 新尺寸: {width}x{height}")
            return updated_window_info
            
        except Exception as e:
            self.logger.error(f"窗口大小调整失败: {e}")
            return None
    
    def move_window(self, window_info: WindowInfo, x: int, y: int) -> Optional[WindowInfo]:
        """
        移动窗口
        
        Args:
            window_info: 窗口信息
            x: 新x坐标
            y: 新y坐标
        
        Returns:
            更新后的窗口信息，失败时返回None
        """
        try:
            hwnd = window_info.hwnd
            width, height = window_info.width, window_info.height
            
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            
            # 获取更新后的窗口信息
            new_rect = win32gui.GetWindowRect(hwnd)
            updated_window_info = WindowInfo(
                hwnd=window_info.hwnd,
                title=window_info.title,
                class_name=window_info.class_name,
                pid=window_info.pid,
                process_name=window_info.process_name,
                rect=new_rect,
                state=window_info.state,
                visible=window_info.visible,
                enabled=window_info.enabled
            )
            
            self.logger.info(f"窗口移动成功: {window_info.title}, 新位置: ({x}, {y})")
            return updated_window_info
            
        except Exception as e:
            self.logger.error(f"窗口移动失败: {e}")
            return None
    
    def get_window_text(self, window_info: WindowInfo) -> str:
        """
        获取窗口文本内容
        
        Args:
            window_info: 窗口信息
        
        Returns:
            窗口文本
        """
        try:
            hwnd = window_info.hwnd
            text = win32gui.GetWindowText(hwnd)
            return text
            
        except Exception as e:
            self.logger.error(f"获取窗口文本失败: {e}")
            return ""
    
    def get_child_windows(self, window_info: WindowInfo) -> List[WindowInfo]:
        """
        获取子窗口
        
        Args:
            window_info: 父窗口信息
        
        Returns:
            子窗口信息列表
        """
        child_windows = []
        
        def enum_child_callback(hwnd, param):
            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # 获取进程信息
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "Unknown"
                
                # 获取窗口位置
                rect = win32gui.GetWindowRect(hwnd)
                
                # 获取窗口状态
                placement = win32gui.GetWindowPlacement(hwnd)
                state = WindowState(placement[1])
                
                # 获取窗口属性
                visible = win32gui.IsWindowVisible(hwnd)
                enabled = win32gui.IsWindowEnabled(hwnd)
                
                child_window = WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    class_name=class_name,
                    pid=pid,
                    process_name=process_name,
                    rect=rect,
                    state=state,
                    visible=visible,
                    enabled=enabled
                )
                
                child_windows.append(child_window)
                
            except Exception as e:
                self.logger.debug(f"获取子窗口信息失败: {e}")
            
            return True
        
        try:
            win32gui.EnumChildWindows(window_info.hwnd, enum_child_callback, None)
            return child_windows
            
        except Exception as e:
            self.logger.error(f"枚举子窗口失败: {e}")
            return []
    
    def is_window_responsive(self, window_info: WindowInfo, timeout: float = 1.0) -> bool:
        """
        检查窗口是否响应
        
        Args:
            window_info: 窗口信息
            timeout: 超时时间
        
        Returns:
            窗口是否响应
        """
        try:
            hwnd = window_info.hwnd
            result = win32gui.SendMessageTimeout(
                hwnd, 
                win32con.WM_NULL, 
                0, 
                0, 
                win32con.SMTO_ABORTIFHUNG,
                int(timeout * 1000)
            )
            return result[0] != 0
            
        except Exception as e:
            self.logger.error(f"检查窗口响应失败: {e}")
            return False


def create_window_manager(config: dict) -> WindowManager:
    """
    创建窗口管理器
    
    Args:
        config: 配置字典
    
    Returns:
        窗口管理器实例
    """
    return WindowManager(
        search_timeout=config.get('search_timeout', 5.0),
        activate_timeout=config.get('activate_timeout', 2.0)
    )