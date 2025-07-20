#!/usr/bin/env python3
"""
配置文件生成工具
用于生成和管理RPA项目的配置文件
"""

import argparse
import sys
from pathlib import Path
import yaml
import json
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import create_default_config, Config
from core.logger import setup_logger


class ConfigGenerator:
    """配置文件生成器"""
    
    def __init__(self):
        self.logger = setup_logger("config_generator", debug=True)
        
        # 预定义的配置模板
        self.templates = {
            'minimal': self._get_minimal_config(),
            'development': self._get_development_config(),
            'production': self._get_production_config(),
            'testing': self._get_testing_config()
        }
    
    def _get_minimal_config(self) -> Dict[str, Any]:
        """获取最小配置"""
        return {
            'app': {
                'name': 'Xiaoxin RPA Pro',
                'version': '1.0.2'
            },
            'vision': {
                'confidence_threshold': 0.8
            },
            'mouse': {
                'click_delay': 0.1
            }
        }
    
    def _get_development_config(self) -> Dict[str, Any]:
        """获取开发配置"""
        return {
            'app': {
                'name': 'Xiaoxin RPA Pro',
                'version': '1.0.2',
                'debug': True
            },
            'logging': {
                'level': 'DEBUG',
                'file_enabled': True,
                'console_enabled': True
            },
            'vision': {
                'confidence_threshold': 0.7,
                'match_method': 'TM_CCOEFF_NORMED',
                'grayscale': True
            },
            'mouse': {
                'click_delay': 0.05,
                'move_duration': 0.2,
                'fail_safe': False
            },
            'window': {
                'search_timeout': 3.0,
                'activate_timeout': 1.0
            },
            'workflow': {
                'step_delay': 0.2,
                'error_retry': 1,
                'screenshot_on_error': True
            },
            'templates': {
                'base_path': 'templates',
                'auto_resolution': True,
                'supported_formats': ['.png', '.jpg', '.jpeg']
            }
        }
    
    def _get_production_config(self) -> Dict[str, Any]:
        """获取生产配置"""
        return {
            'app': {
                'name': 'Xiaoxin RPA Pro',
                'version': '1.0.2',
                'debug': False
            },
            'logging': {
                'level': 'INFO',
                'file_enabled': True,
                'console_enabled': False
            },
            'vision': {
                'confidence_threshold': 0.9,
                'match_method': 'TM_CCOEFF_NORMED',
                'grayscale': True
            },
            'mouse': {
                'click_delay': 0.1,
                'move_duration': 0.5,
                'fail_safe': True
            },
            'window': {
                'search_timeout': 10.0,
                'activate_timeout': 3.0
            },
            'workflow': {
                'step_delay': 0.5,
                'error_retry': 3,
                'screenshot_on_error': True
            },
            'templates': {
                'base_path': 'templates',
                'auto_resolution': True,
                'supported_formats': ['.png', '.jpg', '.jpeg', '.bmp']
            }
        }
    
    def _get_testing_config(self) -> Dict[str, Any]:
        """获取测试配置"""
        return {
            'app': {
                'name': 'Xiaoxin RPA Pro Test',
                'version': '1.0.2',
                'debug': True
            },
            'logging': {
                'level': 'DEBUG',
                'file_enabled': False,
                'console_enabled': True
            },
            'vision': {
                'confidence_threshold': 0.5,
                'match_method': 'TM_CCOEFF_NORMED',
                'grayscale': True
            },
            'mouse': {
                'click_delay': 0.01,
                'move_duration': 0.1,
                'fail_safe': False
            },
            'window': {
                'search_timeout': 1.0,
                'activate_timeout': 0.5
            },
            'workflow': {
                'step_delay': 0.1,
                'error_retry': 1,
                'screenshot_on_error': False
            },
            'templates': {
                'base_path': 'test_templates',
                'auto_resolution': False,
                'supported_formats': ['.png']
            }
        }
    
    def generate_config(self, template: str, output_path: str, format: str = 'yaml') -> bool:
        """
        生成配置文件
        
        Args:
            template: 配置模板名称
            output_path: 输出文件路径
            format: 输出格式 ('yaml' 或 'json')
        
        Returns:
            生成是否成功
        """
        try:
            if template not in self.templates:
                self.logger.error(f"未知的配置模板: {template}")
                return False
            
            config_data = self.templates[template]
            output_file = Path(output_path)
            
            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置文件
            with open(output_file, 'w', encoding='utf-8') as f:
                if format.lower() == 'json':
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.safe_dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"配置文件已生成: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成配置文件失败: {e}")
            return False
    
    def validate_config(self, config_path: str) -> bool:
        """
        验证配置文件
        
        Args:
            config_path: 配置文件路径
        
        Returns:
            验证是否通过
        """
        try:
            config = Config(config_path)
            
            # 基本结构验证
            schema = {
                'app': {
                    'name': str,
                    'version': str,
                    'debug?': bool
                },
                'logging?': {
                    'level': str,
                    'file_enabled?': bool,
                    'console_enabled?': bool
                },
                'vision?': {
                    'confidence_threshold': (lambda x: 0.0 <= x <= 1.0),
                    'match_method?': str,
                    'grayscale?': bool
                },
                'mouse?': {
                    'click_delay': (lambda x: x >= 0),
                    'move_duration?': (lambda x: x >= 0),
                    'fail_safe?': bool
                },
                'window?': {
                    'search_timeout': (lambda x: x > 0),
                    'activate_timeout?': (lambda x: x > 0)
                },
                'workflow?': {
                    'step_delay?': (lambda x: x >= 0),
                    'error_retry?': (lambda x: x >= 0),
                    'screenshot_on_error?': bool
                },
                'templates?': {
                    'base_path': str,
                    'auto_resolution?': bool,
                    'supported_formats?': list
                }
            }
            
            if config.validate(schema):
                self.logger.info("配置文件验证通过")
                return True
            else:
                self.logger.error("配置文件验证失败")
                return False
                
        except Exception as e:
            self.logger.error(f"验证配置文件失败: {e}")
            return False
    
    def merge_configs(self, base_config: str, override_config: str, output_path: str) -> bool:
        """
        合并配置文件
        
        Args:
            base_config: 基础配置文件路径
            override_config: 覆盖配置文件路径
            output_path: 输出文件路径
        
        Returns:
            合并是否成功
        """
        try:
            base = Config(base_config)
            override = Config(override_config)
            
            # 合并配置
            merged_data = base.get_all()
            self._deep_merge(merged_data, override.get_all())
            
            # 保存合并后的配置
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_file.suffix.lower() == '.json':
                    json.dump(merged_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.safe_dump(merged_data, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"配置文件合并完成: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"合并配置文件失败: {e}")
            return False
    
    def _deep_merge(self, base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> None:
        """深度合并字典"""
        for key, value in override_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def list_templates(self) -> List[str]:
        """列出可用的配置模板"""
        return list(self.templates.keys())
    
    def show_template(self, template: str) -> None:
        """显示配置模板内容"""
        if template not in self.templates:
            print(f"未知的配置模板: {template}")
            return
        
        config_data = self.templates[template]
        print(f"\n配置模板: {template}")
        print("=" * 50)
        print(yaml.dump(config_data, default_flow_style=False, allow_unicode=True))
    
    def interactive_generate(self) -> None:
        """交互式生成配置"""
        print("欢迎使用配置文件生成工具")
        print("=" * 50)
        
        # 选择模板
        print("\n可用的配置模板:")
        for i, template in enumerate(self.list_templates(), 1):
            print(f"{i}. {template}")
        
        try:
            choice = int(input("\n请选择配置模板 (输入数字): ")) - 1
            template = self.list_templates()[choice]
        except (ValueError, IndexError):
            print("无效的选择，使用默认模板")
            template = 'minimal'
        
        # 输出路径
        output_path = input("\n输出文件路径 (默认: config/generated.yaml): ").strip()
        if not output_path:
            output_path = "config/generated.yaml"
        
        # 输出格式
        format_choice = input("\n输出格式 (yaml/json，默认: yaml): ").strip().lower()
        if format_choice not in ['yaml', 'json']:
            format_choice = 'yaml'
        
        # 生成配置
        if self.generate_config(template, output_path, format_choice):
            print(f"\n配置文件已生成: {output_path}")
        else:
            print("\n配置文件生成失败")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RPA配置文件生成工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 生成配置命令
    generate_parser = subparsers.add_parser('generate', help='生成配置文件')
    generate_parser.add_argument('--template', '-t', choices=['minimal', 'development', 'production', 'testing'],
                                default='minimal', help='配置模板')
    generate_parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    generate_parser.add_argument('--format', '-f', choices=['yaml', 'json'], default='yaml', help='输出格式')
    
    # 验证配置命令
    validate_parser = subparsers.add_parser('validate', help='验证配置文件')
    validate_parser.add_argument('config', help='配置文件路径')
    
    # 合并配置命令
    merge_parser = subparsers.add_parser('merge', help='合并配置文件')
    merge_parser.add_argument('base', help='基础配置文件路径')
    merge_parser.add_argument('override', help='覆盖配置文件路径')
    merge_parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    
    # 列出模板命令
    list_parser = subparsers.add_parser('list', help='列出可用模板')
    
    # 显示模板命令
    show_parser = subparsers.add_parser('show', help='显示模板内容')
    show_parser.add_argument('template', choices=['minimal', 'development', 'production', 'testing'],
                            help='模板名称')
    
    # 交互式生成命令
    interactive_parser = subparsers.add_parser('interactive', help='交互式生成配置')
    
    # 默认配置命令
    default_parser = subparsers.add_parser('default', help='生成默认配置')
    default_parser.add_argument('--output', '-o', default='config/default.yaml', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    generator = ConfigGenerator()
    
    if args.command == 'generate':
        success = generator.generate_config(args.template, args.output, args.format)
        sys.exit(0 if success else 1)
    
    elif args.command == 'validate':
        success = generator.validate_config(args.config)
        sys.exit(0 if success else 1)
    
    elif args.command == 'merge':
        success = generator.merge_configs(args.base, args.override, args.output)
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        print("可用的配置模板:")
        for template in generator.list_templates():
            print(f"  - {template}")
    
    elif args.command == 'show':
        generator.show_template(args.template)
    
    elif args.command == 'interactive':
        generator.interactive_generate()
    
    elif args.command == 'default':
        create_default_config(args.output)
        print(f"默认配置文件已生成: {args.output}")


if __name__ == '__main__':
    main()