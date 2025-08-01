"""
鼠标操作模块
基于PyAutoGUI实现鼠标点击、拖拽、滚动等操作
"""

import time
from typing import Optional, Tuple, Union
from enum import Enum

import pyautogui

from .logger import LoggerMixin
from .vision import MatchResult

# 添加 Windows API 支持
try:
    import win32api
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class MouseButton(Enum):
    """鼠标按键枚举"""
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


class MouseController(LoggerMixin):
    """鼠标控制器"""
    
    def __init__(self, 
                 click_delay: float = 0.1,
                 move_duration: float = 0.5,
                 fail_safe: bool = True):
        """
        初始化鼠标控制器
        
        Args:
            click_delay: 点击延迟时间（秒）
            move_duration: 鼠标移动持续时间（秒）
            fail_safe: 是否启用失败保护（鼠标移动到屏幕角落时停止）
        """
        self.click_delay = click_delay
        self.move_duration = move_duration
        
        # 设置PyAutoGUI配置
        pyautogui.FAILSAFE = fail_safe
        pyautogui.PAUSE = click_delay
        
        self.logger.info(f"鼠标控制器初始化完成，点击延迟: {click_delay}秒, 移动时长: {move_duration}秒")
    
    def get_position(self) -> Tuple[int, int]:
        """
        获取当前鼠标位置
        
        Returns:
            鼠标位置坐标 (x, y)
        """
        position = pyautogui.position()
        return (int(position.x), int(position.y))
    
    def move_to(self, x: int, y: int, duration: Optional[float] = None) -> bool:
        """
        移动鼠标到指定位置
        
        Args:
            x: 目标x坐标
            y: 目标y坐标
            duration: 移动持续时间，None则使用默认值
        
        Returns:
            操作是否成功
        """
        try:
            if duration is None:
                duration = self.move_duration
            
            self.logger.debug(f"移动鼠标到: ({x}, {y}), 持续时间: {duration}秒")
            pyautogui.moveTo(x, y, duration=duration)
            return True
            
        except Exception as e:
            self.logger.error(f"鼠标移动失败: {e}")
            return False
    
    def click(self, 
              x: Optional[int] = None, 
              y: Optional[int] = None,
              button: MouseButton = MouseButton.LEFT,
              clicks: int = 1,
              interval: float = 0.0) -> bool:
        """
        点击鼠标
        
        Args:
            x: 点击位置x坐标，None则在当前位置点击
            y: 点击位置y坐标，None则在当前位置点击
            button: 鼠标按键
            clicks: 点击次数
            interval: 多次点击间隔
        
        Returns:
            操作是否成功
        """
        try:
            if x is not None and y is not None:
                self.logger.debug(f"点击位置: ({x}, {y}), 按键: {button.value}, 次数: {clicks}")
                pyautogui.click(x, y, clicks=clicks, interval=interval, button=button.value)
            else:
                current_pos = self.get_position()
                self.logger.debug(f"点击当前位置: {current_pos}, 按键: {button.value}, 次数: {clicks}")
                pyautogui.click(clicks=clicks, interval=interval, button=button.value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"鼠标点击失败: {e}")
            return False
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        双击鼠标
        
        Args:
            x: 点击位置x坐标
            y: 点击位置y坐标
        
        Returns:
            操作是否成功
        """
        return self.click(x, y, clicks=2, interval=0.1)
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        右键点击
        
        Args:
            x: 点击位置x坐标
            y: 点击位置y坐标
        
        Returns:
            操作是否成功
        """
        return self.click(x, y, button=MouseButton.RIGHT)
    
    def drag(self, 
             from_x: int, from_y: int,
             to_x: int, to_y: int,
             duration: Optional[float] = None,
             button: MouseButton = MouseButton.LEFT) -> bool:
        """
        拖拽鼠标
        
        Args:
            from_x: 起始x坐标
            from_y: 起始y坐标
            to_x: 结束x坐标
            to_y: 结束y坐标
            duration: 拖拽持续时间
            button: 鼠标按键
        
        Returns:
            操作是否成功
        """
        try:
            if duration is None:
                duration = self.move_duration
            
            self.logger.debug(f"拖拽: ({from_x}, {from_y}) -> ({to_x}, {to_y}), 持续时间: {duration}秒")
            pyautogui.drag(to_x - from_x, to_y - from_y, duration=duration, button=button.value)
            return True
            
        except Exception as e:
            self.logger.error(f"鼠标拖拽失败: {e}")
            return False
    
    def scroll(self, 
               x: Optional[int] = None, 
               y: Optional[int] = None,
               clicks: int = 1,
               direction: str = 'up',
               strategy: str = 'auto') -> bool:
        """
        滚动鼠标滚轮
        
        Args:
            x: 滚动位置x坐标，None则在当前位置滚动
            y: 滚动位置y坐标，None则在当前位置滚动
            clicks: 滚动次数
            direction: 滚动方向 ('up' 或 'down')
            strategy: 滚动策略 ('auto', 'single', 'multiple', 'precise')
        
        Returns:
            操作是否成功
        """
        try:
            # 如果指定了位置，移动到指定位置
            if x is not None and y is not None:
                if not self.move_to(x, y):
                    return False
                self.logger.debug(f"滚动: ({x}, {y}), 方向: {direction}, 次数: {clicks}, 策略: {strategy}")
            else:
                current_pos = self.get_position()
                self.logger.debug(f"在当前位置滚动: {current_pos}, 方向: {direction}, 次数: {clicks}, 策略: {strategy}")
            
            # 确定滚动方向
            scroll_direction = 1 if direction == 'up' else -1
            
            # 根据策略执行滚动
            if strategy == 'single':
                # 单次滚动，发送一个大的滚动值
                scroll_amount = scroll_direction * clicks
                pyautogui.scroll(scroll_amount)
            elif strategy == 'multiple':
                # 多次滚动，逐个发送滚动事件
                for _ in range(clicks):
                    pyautogui.scroll(scroll_direction)
                    time.sleep(0.05)  # 短暂延迟确保事件被处理
            elif strategy == 'precise':
                # 精确滚动，使用键盘模拟
                for _ in range(clicks):
                    if direction == 'up':
                        pyautogui.press('up')
                    else:
                        pyautogui.press('down')
                    time.sleep(0.05)
            else:  # auto
                # 自动选择策略：先尝试单次，如果clicks大于3则使用多次
                if clicks <= 3:
                    scroll_amount = scroll_direction * clicks
                    pyautogui.scroll(scroll_amount)
                else:
                    for _ in range(clicks):
                        pyautogui.scroll(scroll_direction)
                        time.sleep(0.03)
            
            return True
            
        except Exception as e:
            self.logger.error(f"鼠标滚动失败: {e}")
            return False
    
    def scroll_up(self, 
                  x: Optional[int] = None, 
                  y: Optional[int] = None,
                  clicks: int = 1,
                  strategy: str = 'auto') -> bool:
        """
        向上滚动
        
        Args:
            x: 滚动位置x坐标
            y: 滚动位置y坐标
            clicks: 滚动次数
            strategy: 滚动策略
        
        Returns:
            操作是否成功
        """
        return self.scroll(x, y, clicks, 'up', strategy)
    
    def scroll_down(self, 
                    x: Optional[int] = None, 
                    y: Optional[int] = None,
                    clicks: int = 1,
                    strategy: str = 'auto') -> bool:
        """
        向下滚动
        
        Args:
            x: 滚动位置x坐标
            y: 滚动位置y坐标
            clicks: 滚动次数
            strategy: 滚动策略
        
        Returns:
            操作是否成功
        """
        return self.scroll(x, y, clicks, 'down', strategy)
    
    def scroll_to_distance(self, 
                          x: Optional[int] = None, 
                          y: Optional[int] = None,
                          distance: int = 5,
                          direction: str = 'up') -> bool:
        """
        滚动指定距离（自动选择最佳策略）
        
        Args:
            x: 滚动位置x坐标
            y: 滚动位置y坐标
            distance: 滚动距离（1-20）
            direction: 滚动方向
        
        Returns:
            操作是否成功
        """
        # 根据距离自动选择策略
        if distance <= 2:
            strategy = 'single'
        elif distance <= 10:
            strategy = 'multiple'
        else:
            strategy = 'precise'
        
        return self.scroll(x, y, distance, direction, strategy)
    
    def click_match_result(self, match_result: MatchResult, button: MouseButton = MouseButton.LEFT) -> bool:
        """
        点击匹配结果的中心位置
        
        Args:
            match_result: 图像匹配结果
        
        Returns:
            操作是否成功
        """
        center_x, center_y = match_result.center
        return self.click(center_x, center_y, button=button)
    
    def hover(self, x: int, y: int, duration: Optional[float] = None) -> bool:
        """
        悬停鼠标
        
        Args:
            x: 悬停位置x坐标
            y: 悬停位置y坐标
            duration: 悬停持续时间
        
        Returns:
            操作是否成功
        """
        try:
            if duration is None:
                duration = self.move_duration
            
            self.logger.debug(f"悬停: ({x}, {y}), 持续时间: {duration}秒")
            pyautogui.moveTo(x, y, duration=duration)
            time.sleep(0.1)  # 短暂停留
            return True
            
        except Exception as e:
            self.logger.error(f"鼠标悬停失败: {e}")
            return False
    
    def press_and_hold(self, x: int, y: int, duration: float = 1.0) -> bool:
        """
        按住鼠标按键
        
        Args:
            x: 按住位置x坐标
            y: 按住位置y坐标
            duration: 按住持续时间
        
        Returns:
            操作是否成功
        """
        try:
            self.logger.debug(f"按住鼠标: ({x}, {y}), 持续时间: {duration}秒")
            
            # 移动到位置
            if not self.move_to(x, y):
                return False
            
            # 按下鼠标
            pyautogui.mouseDown()
            time.sleep(duration)
            
            # 释放鼠标
            pyautogui.mouseUp()
            return True
            
        except Exception as e:
            self.logger.error(f"按住鼠标失败: {e}")
            return False
    
    def click_and_drag(self, 
                      start_x: int, start_y: int,
                      end_x: int, end_y: int,
                      duration: Optional[float] = None) -> bool:
        """
        点击并拖拽
        
        Args:
            start_x: 起始x坐标
            start_y: 起始y坐标
            end_x: 结束x坐标
            end_y: 结束y坐标
            duration: 拖拽持续时间
        
        Returns:
            操作是否成功
        """
        try:
            if duration is None:
                duration = self.move_duration
            
            self.logger.debug(f"点击并拖拽: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            
            # 移动到起始位置
            if not self.move_to(start_x, start_y):
                return False
            
            # 按下鼠标
            pyautogui.mouseDown()
            
            # 拖拽到结束位置
            pyautogui.moveTo(end_x, end_y, duration=duration)
            
            # 释放鼠标
            pyautogui.mouseUp()
            return True
            
        except Exception as e:
            self.logger.error(f"点击并拖拽失败: {e}")
            return False
    
    def is_position_safe(self, x: int, y: int) -> bool:
        """
        检查位置是否安全（不会触发失败保护）
        
        Args:
            x: x坐标
            y: y坐标
        
        Returns:
            位置是否安全
        """
        if not pyautogui.FAILSAFE:
            return True
        
        screen_size = pyautogui.size()
        
        # 检查是否在屏幕边界附近
        if x <= 0 or y <= 0 or x >= screen_size.width - 1 or y >= screen_size.height - 1:
            return False
        
        return True
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        获取屏幕尺寸
        
        Returns:
            屏幕尺寸 (width, height)
        """
        size = pyautogui.size()
        return (size.width, size.height)
    
    def set_click_delay(self, delay: float) -> None:
        """
        设置点击延迟
        
        Args:
            delay: 延迟时间（秒）
        """
        self.click_delay = delay
        pyautogui.PAUSE = delay
        self.logger.info(f"点击延迟已设置为: {delay}秒")
    
    def enable_fail_safe(self, enabled: bool = True) -> None:
        """
        启用/禁用失败保护
        
        Args:
            enabled: 是否启用
        """
        pyautogui.FAILSAFE = enabled
        self.logger.info(f"失败保护已{'启用' if enabled else '禁用'}")
    
    def mouse_down(self, 
                   x: Optional[int] = None, 
                   y: Optional[int] = None,
                   button: MouseButton = MouseButton.LEFT) -> bool:
        """
        按下鼠标按键
        
        Args:
            x: 按下位置x坐标，None则在当前位置按下
            y: 按下位置y坐标，None则在当前位置按下
            button: 鼠标按键
        
        Returns:
            操作是否成功
        """
        try:
            if x is not None and y is not None:
                self.logger.debug(f"移动并按下鼠标: ({x}, {y}), 按键: {button.value}")
                pyautogui.moveTo(x, y)
                pyautogui.mouseDown(button=button.value)
            else:
                current_pos = self.get_position()
                self.logger.debug(f"在当前位置按下鼠标: {current_pos}, 按键: {button.value}")
                pyautogui.mouseDown(button=button.value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"按下鼠标失败: {e}")
            return False
    
    def mouse_up(self, 
                 x: Optional[int] = None, 
                 y: Optional[int] = None,
                 button: MouseButton = MouseButton.LEFT) -> bool:
        """
        释放鼠标按键
        
        Args:
            x: 释放位置x坐标，None则在当前位置释放
            y: 释放位置y坐标，None则在当前位置释放
            button: 鼠标按键
        
        Returns:
            操作是否成功
        """
        try:
            if x is not None and y is not None:
                self.logger.debug(f"移动并释放鼠标: ({x}, {y}), 按键: {button.value}")
                pyautogui.moveTo(x, y)
                pyautogui.mouseUp(button=button.value)
            else:
                current_pos = self.get_position()
                self.logger.debug(f"在当前位置释放鼠标: {current_pos}, 按键: {button.value}")
                pyautogui.mouseUp(button=button.value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"释放鼠标失败: {e}")
            return False
    
    def win32scroll(self, 
                    pixels: int, 
                    x: Optional[int] = None, 
                    y: Optional[int] = None) -> bool:
        """
        使用Win32 API进行滚动操作（支持像素级滚动）
        
        Args:
            pixels: 滚动像素数（正数向上，负数向下）
            x: 滚动位置x坐标，None则在当前位置滚动
            y: 滚动位置y坐标，None则在当前位置滚动
        
        Returns:
            操作是否成功
        """
        try:
            if not HAS_WIN32:
                self.logger.warning("Windows API 不可用，回退到标准滚动方法")
                # 将像素转换为滚动次数（大概估算：每次滚动约120像素）
                clicks = pixels // 120 if pixels != 0 else (1 if pixels > 0 else -1)
                return self.scroll(x, y, abs(clicks), 'up' if pixels > 0 else 'down')
            
            # 获取滚动位置
            if x is None or y is None:
                current_pos = self.get_position()
                scroll_x = x if x is not None else current_pos[0]
                scroll_y = y if y is not None else current_pos[1]
            else:
                scroll_x, scroll_y = x, y
            
            self.logger.debug(f"Win32滚动: 在位置({scroll_x}, {scroll_y})滚动{pixels}像素")
            
            # 获取窗口句柄
            hwnd = win32gui.WindowFromPoint((scroll_x, scroll_y))
            
            # 计算滚动量（Windows API 使用的是 120 的倍数）
            # 正数表示向上滚动，负数表示向下滚动
            delta = pixels * 120 // 120
            if pixels != 0 and delta == 0:
                delta = 120 if pixels > 0 else -120
            
            # 发送滚动消息
            # WM_MOUSEWHEEL: wParam高位为滚动量，低位为按键状态；lParam为鼠标位置
            win32gui.SendMessage(hwnd, win32con.WM_MOUSEWHEEL, 
                               delta << 16, (scroll_y << 16) | scroll_x)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Win32滚动失败: {e}")
            # 回退到标准滚动方法
            try:
                clicks = abs(pixels // 120) if pixels != 0 else 1
                direction = 'up' if pixels >= 0 else 'down'
                return self.scroll(x, y, clicks, direction)
            except:
                return False


def create_mouse_controller(config: dict) -> MouseController:
    """
    创建鼠标控制器
    
    Args:
        config: 配置字典
    
    Returns:
        鼠标控制器实例
    """
    return MouseController(
        click_delay=config.get('click_delay', 0.1),
        move_duration=config.get('move_duration', 0.5),
        fail_safe=config.get('fail_safe', True)
    )