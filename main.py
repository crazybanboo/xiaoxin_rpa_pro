#!/usr/bin/env python3
"""
Xiaoxin RPA Pro - 基于Python的RPA自动化软件
主程序入口
"""

import sys
import os
import argparse
import threading
import keyboard
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 全局停止标志
stop_flag = threading.Event()

from core.logger import setup_logger
from core.config import Config
from core.workflow import WorkflowManager


def setup_hotkey_listener(logger):
    """设置F12热键监听"""
    def on_f12_press():
        logger.info("检测到F12按键，程序即将停止...")
        stop_flag.set()
    
    # 注册F12热键
    keyboard.add_hotkey('f12', on_f12_press)
    logger.info("F12热键监听已启动，按F12可随时中止程序")


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="Xiaoxin RPA Pro - Python RPA自动化软件"
    )
    parser.add_argument(
        "--config", 
        "-c", 
        default="config/default.yaml",
        help="配置文件路径"
    )
    parser.add_argument(
        "--workflow", 
        "-w", 
        required=True,
        help="要执行的工作流名称"
    )
    parser.add_argument(
        "--debug", 
        "-d", 
        action="store_true",
        help="启用调试模式"
    )
    parser.add_argument(
        "--log-level", 
        "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    try:
        # 先加载配置
        config = Config(args.config)
        
        # 从配置中获取日志配置
        log_config = config.get('logging', {})
        
        # 设置日志
        logger = setup_logger(
            level=args.log_level,
            debug=args.debug,
            config=log_config
        )
        logger.info(f"配置文件加载成功: {args.config}")
        
        # 设置F12热键监听
        setup_hotkey_listener(logger)
        
        # 初始化工作流管理器
        workflow_manager = WorkflowManager(config)
        
        # 执行工作流
        logger.info(f"开始执行工作流: {args.workflow}")
        success = workflow_manager.execute(args.workflow, lambda: stop_flag.is_set())
        
        if success:
            logger.info(f"工作流执行成功: {args.workflow}")
            return 0
        else:
            logger.error(f"工作流执行失败: {args.workflow}")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        return 1
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        # 清理热键监听
        try:
            keyboard.unhook_all()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())