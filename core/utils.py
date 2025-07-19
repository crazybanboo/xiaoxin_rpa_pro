"""
实用工具模块
提供各种辅助功能
"""

import time
import threading
from typing import Optional, Callable


def interruptible_sleep(duration: float, stop_check_func: Optional[Callable[[], bool]] = None, check_interval: float = 0.1) -> bool:
    """
    可中断的睡眠函数
    
    Args:
        duration: 睡眠时长（秒）
        stop_check_func: 停止检查函数，返回True表示应该中断
        check_interval: 检查间隔（秒），默认0.1秒
    
    Returns:
        True: 正常完成睡眠
        False: 被中断
    """
    if duration <= 0:
        return True
    
    if stop_check_func is None:
        time.sleep(duration)
        return True
    
    # 如果持续时间很短，直接使用time.sleep
    if duration <= check_interval:
        if stop_check_func():
            return False
        time.sleep(duration)
        return not stop_check_func()
    
    # 对于长时间的睡眠，分段检查
    elapsed = 0.0
    while elapsed < duration:
        if stop_check_func():
            return False
        
        # 计算本次睡眠时间
        remaining = duration - elapsed
        sleep_time = min(check_interval, remaining)
        
        time.sleep(sleep_time)
        elapsed += sleep_time
    
    return True


def interruptible_sleep_event(duration: float, stop_event: Optional[threading.Event] = None) -> bool:
    """
    基于Event的可中断睡眠函数
    
    Args:
        duration: 睡眠时长（秒）
        stop_event: 停止事件，当事件被设置时中断睡眠
    
    Returns:
        True: 正常完成睡眠
        False: 被中断
    """
    if duration <= 0:
        return True
    
    if stop_event is None:
        time.sleep(duration)
        return True
    
    # 使用Event.wait()方法，支持超时和中断
    return not stop_event.wait(timeout=duration)