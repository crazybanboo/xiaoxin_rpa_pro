"""
日志模块
提供统一的日志记录功能
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import inspect


class CustomFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    def format(self, record):
        # 使用 logging record 中已有的信息
        full_path = record.pathname
        
        # 尝试获取相对于项目根目录的路径
        try:
            # 获取当前工作目录
            cwd = os.getcwd()
            if full_path.startswith(cwd):
                caller_file = os.path.relpath(full_path, cwd)
            else:
                caller_file = full_path
        except:
            caller_file = full_path
        
        # 设置自定义字段
        record.caller_file = caller_file
        record.caller_line = record.lineno
        record.module_name = record.name
        
        return super().format(record)


def setup_logger(
    name: str = "xiaoxin_rpa", 
    level: str = "INFO",
    log_dir: str = "logs",
    debug: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_dir: 日志目录
        debug: 是否调试模式
        config: 日志配置字典，包含滚动日志配置
    
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
        # 检查是否启用日志滚动
        rotation_enabled = False
        max_bytes = 10485760  # 默认10MB
        backup_count = 5  # 默认保留5个文件
        
        if config and 'rotation' in config:
            rotation_config = config['rotation']
            rotation_enabled = rotation_config.get('enabled', False)
            max_bytes = rotation_config.get('max_bytes', 10485760)
            backup_count = rotation_config.get('backup_count', 5)
        
        if rotation_enabled:
            # 使用滚动文件处理器
            log_file = log_path / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            # 使用传统的按日期创建日志文件
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = log_path / f"{name}_{today}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 错误日志文件
    error_log_file = log_path / f"{name}_error.log"
    
    # 错误日志也支持滚动
    rotation_enabled = False
    max_bytes = 10485760
    backup_count = 5
    
    if config and 'rotation' in config:
        rotation_config = config['rotation']
        rotation_enabled = rotation_config.get('enabled', False)
        max_bytes = rotation_config.get('max_bytes', 10485760)
        backup_count = rotation_config.get('backup_count', 5)
    
    if rotation_enabled:
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
    else:
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