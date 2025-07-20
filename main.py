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
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 全局停止标志
stop_flag = threading.Event()

from core.logger import setup_logger
from core.config import Config
from core.workflow import WorkflowManager

# 版本信息
__version__ = "1.0.2"
__author__ = "Xiaoxin RPA Pro Team"


def setup_hotkey_listener(logger):
    """设置F12热键监听"""
    def on_f12_press():
        logger.info("检测到F12按键，程序即将停止...")
        stop_flag.set()
    
    # 注册F12热键
    keyboard.add_hotkey('f12', on_f12_press)
    logger.info("F12热键监听已启动，按F12可随时中止程序")


def get_available_workflows(config):
    """获取可用的工作流列表"""
    try:
        # 使用WorkflowManager来获取正确的工作流名称
        workflow_manager = WorkflowManager(config)
        workflows = list(workflow_manager.workflows.keys())
        return sorted(workflows)
    except Exception as e:
        print(f"⚠️  获取工作流列表时出错: {e}")
        return []


def display_menu(workflows):
    """显示工作流选择菜单"""
    print("\n" + "="*60)
    print(f"🤖 Xiaoxin RPA Pro v{__version__} - 工作流选择菜单")
    print("="*60)
    
    if not workflows:
        print("❌ 没有发现可用的工作流")
        return None
    
    print("📋 可用的工作流:")
    for i, workflow in enumerate(workflows, 1):
        print(f"  {i}. {workflow}")
    
    print(f"  0. 退出程序")
    print("\n💡 提示: 运行过程中按F12可随时中止当前工作流")
    print("-"*50)
    
    while True:
        try:
            choice = input("请选择要执行的工作流 (输入数字): ").strip()
            
            if choice == "0":
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(workflows):
                return workflows[choice_num - 1]
            else:
                print(f"❌ 请输入 0-{len(workflows)} 之间的数字")
        except ValueError:
            print("❌ 请输入有效的数字")
        except KeyboardInterrupt:
            print("\n👋 用户取消操作")
            return None


def run_workflow_interactive(config, logger):
    """交互式工作流运行模式"""
    workflows = get_available_workflows(config)
    
    if not workflows:
        logger.error("没有找到可用的工作流")
        return 1
    
    while True:
        try:
            # 重置停止标志
            stop_flag.clear()
            
            # 显示菜单并获取用户选择
            selected_workflow = display_menu(workflows)
            
            if selected_workflow is None:
                logger.info("用户选择退出程序")
                break
            
            logger.info(f"用户选择执行工作流: {selected_workflow}")
            
            # 重新设置F12热键监听
            try:
                keyboard.unhook_all()
            except:
                pass
            setup_hotkey_listener(logger)
            
            # 初始化工作流管理器
            workflow_manager = WorkflowManager(config)
            
            # 执行工作流
            print(f"\n🚀 开始执行工作流: {selected_workflow}")
            print("💡 按F12可随时中止工作流")
            start_time = time.time()
            
            success = workflow_manager.execute(selected_workflow, stop_flag)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if stop_flag.is_set():
                print(f"\n⏹️  工作流已被用户中止: {selected_workflow}")
                logger.info(f"工作流被用户中止: {selected_workflow} (运行时间: {duration:.2f}秒)")
            elif success:
                print(f"\n✅ 工作流执行成功: {selected_workflow}")
                logger.info(f"工作流执行成功: {selected_workflow} (运行时间: {duration:.2f}秒)")
            else:
                print(f"\n❌ 工作流执行失败: {selected_workflow}")
                logger.error(f"工作流执行失败: {selected_workflow} (运行时间: {duration:.2f}秒)")
            
            # 等待用户确认
            print("\n按回车键返回主菜单...")
            input()
            
        except KeyboardInterrupt:
            print("\n👋 程序被用户中断")
            logger.info("程序被用户中断")
            break
        except Exception as e:
            print(f"\n💥 执行过程中出现错误: {e}")
            logger.error(f"执行过程中出现错误: {e}")
            print("\n按回车键返回主菜单...")
            input()
    
    return 0


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="Xiaoxin RPA Pro - Python RPA自动化软件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用方式:
    1. 交互式菜单模式 (推荐):
        xiaoxin_rpa_pro.exe
        
    2. 命令行模式:
        xiaoxin_rpa_pro.exe -w basic_example
        xiaoxin_rpa_pro.exe -w wxwork_auto --config config/wxwork_strategy.yaml
        """
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
        help="要执行的工作流名称 (不指定则进入交互式菜单)"
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
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    try:
        # 先加载配置
        config = Config(args.config)
        
        # 从配置中获取日志配置
        log_config = config.get('logging', {})
        
        # 确定日志级别：优先使用命令行参数，其次使用配置文件
        log_level = args.log_level if args.log_level is not None else log_config.get('level', 'INFO')
        
        # 设置日志
        logger = setup_logger(
            level=log_level,
            debug=args.debug,
            config=log_config
        )
        
        # 记录启动信息和版本号
        logger.info(f"🚀 Xiaoxin RPA Pro v{__version__} 启动")
        logger.info(f"作者: {__author__}")
        logger.info(f"配置文件加载成功: {args.config}")
        logger.info(f"日志级别: {log_level}")
        if args.debug:
            logger.info("调试模式已启用")
        
        # 判断运行模式
        if args.workflow:
            # 命令行模式 - 执行指定工作流
            logger.info("运行模式: 命令行模式")
            
            # 设置F12热键监听
            setup_hotkey_listener(logger)
            
            # 初始化工作流管理器
            workflow_manager = WorkflowManager(config)
            
            # 执行工作流
            logger.info(f"开始执行工作流: {args.workflow}")
            success = workflow_manager.execute(args.workflow, stop_flag)
            
            if success:
                logger.info(f"工作流执行成功: {args.workflow}")
                return 0
            else:
                logger.error(f"工作流执行失败: {args.workflow}")
                return 1
        else:
            # 交互式菜单模式
            logger.info("运行模式: 交互式菜单模式")
            print(f"\n🎉 欢迎使用 Xiaoxin RPA Pro v{__version__}")
            print(f"👥 作者: {__author__}")
            print(f"📁 配置文件: {args.config}")
            print(f"📊 日志级别: {log_level}")
            if args.debug:
                print(f"🐛 调试模式: 已启用")
            
            return run_workflow_interactive(config, logger)
            
    except FileNotFoundError as e:
        if 'logger' in locals():
            logger.error(f"文件未找到: {e}")
        else:
            print(f"❌ 文件未找到: {e}")
        return 1
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"程序执行出错: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ 程序执行出错: {e}")
        return 1
    finally:
        # 清理热键监听
        try:
            keyboard.unhook_all()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())