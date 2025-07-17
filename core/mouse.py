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
               x: int, y: int,
               clicks: int,
               direction: str = 'up') -> bool:
        """
        滚动鼠标滚轮
        
        Args:
            x: 滚动位置x坐标
            y: 滚动位置y坐标
            clicks: 滚动次数
            direction: 滚动方向 ('up' 或 'down')
        
        Returns:
            操作是否成功
        """
        try:
            # 移动到指定位置
            if not self.move_to(x, y):
                return False
            
            # 确定滚动方向
            scroll_clicks = clicks if direction == 'up' else -clicks
            
            self.logger.debug(f"滚动: ({x}, {y}), 方向: {direction}, 次数: {clicks}")
            pyautogui.scroll(scroll_clicks)
            return True
            
        except Exception as e:
            self.logger.error(f"鼠标滚动失败: {e}")
            return False
    
    def click_match_result(self, match_result: MatchResult) -> bool:
        """
        点击匹配结果的中心位置
        
        Args:
            match_result: 图像匹配结果
        
        Returns:
            操作是否成功
        """
        center_x, center_y = match_result.center
        return self.click(center_x, center_y)
    
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