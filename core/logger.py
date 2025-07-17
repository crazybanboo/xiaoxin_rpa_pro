"""
日志模块
提供统一的日志记录功能
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import inspect


class CustomFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    def format(self, record):
        # 获取调用者信息
        frame = inspect.currentframe()
        try:
            # 向上查找到实际的调用者
            caller_frame = frame.f_back.f_back.f_back
            if caller_frame:
                caller_file = os.path.basename(caller_frame.f_code.co_filename)
                caller_line = caller_frame.f_lineno
                module_name = caller_frame.f_globals.get('__name__', 'unknown')
            else:
                caller_file = 'unknown'
                caller_line = 0
                module_name = 'unknown'
        finally:
            del frame
        
        # 设置自定义字段
        record.caller_file = caller_file
        record.caller_line = caller_line
        record.module_name = module_name
        
        return super().format(record)


def setup_logger(
    name: str = "xiaoxin_rpa", 
    level: str = "INFO",
    log_dir: str = "logs",
    debug: bool = False
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_dir: 日志目录
        debug: 是否调试模式
    
    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 日志格式
    log_format = "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"
    formatter = CustomFormatter(log_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if not debug:
        # 按日期创建日志文件
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_path / f"{name}_{today}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 错误日志文件
    error_log_file = log_path / f"{name}_error.log"
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str = "xiaoxin_rpa") -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志器名称
    
    Returns:
        日志记录器
    """
    return logging.getLogger(name)


class LoggerMixin:
    """日志混入类，为类提供日志功能"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        return get_logger()