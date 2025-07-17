#!/usr/bin/env python3
"""
模板管理工具
用于管理RPA项目的模板文件
"""

import argparse
import sys
import shutil
from pathlib import Path
import json
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.template import TemplateManager, TemplateConfig
from core.vision import VisionEngine
from core.logger import setup_logger


class TemplateManagerTool:
    """模板管理工具类"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.template_manager = TemplateManager(str(self.templates_dir))
        self.vision_engine = VisionEngine()
        self.logger = setup_logger("template_manager", debug=True)
        
        # 支持的分辨率
        self.common_resolutions = [
            "1920x1080",
            "1366x768", 
            "1440x900",
            "1280x1024",
            "1600x900",
            "1024x768"
        ]
    
    def create_workflow(self, workflow_name: str, template_names: List[str], 
                       resolutions: Optional[List[str]] = None) -> bool:
        """
        创建工作流模板结构
        
        Args:
            workflow_name: 工作流名称
            template_names: 模板名称列表
            resolutions: 分辨率列表
        
        Returns:
            创建是否成功
        """
        try:
            if resolutions is None:
                resolutions = self.common_resolutions
            
            workflow_dir = self.templates_dir / workflow_name
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建分辨率目录
            for resolution in resolutions:
                resolution_dir = workflow_dir / resolution
                resolution_dir.mkdir(exist_ok=True)
                
                # 创建说明文件
                readme_path = resolution_dir / "README.md"
                self._create_readme(readme_path, workflow_name, resolution, template_names)
            
            # 创建配置文件
            config_path = workflow_dir / "template_config.json"
            self._create_config_file(config_path, workflow_name)
            
            self.logger.info(f"工作流模板结构创建成功: {workflow_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建工作流失败: {e}")
            return False
    
    def _create_readme(self, readme_path: Path, workflow_name: str, 
                      resolution: str, template_names: List[str]) -> None:
        """创建说明文件"""
        content = f"""# {workflow_name} - {resolution}

## 模板文件说明

请将以下模板图片放置在此目录中：

"""
        for template_name in template_names:
            content += f"- **{template_name}.png** - {template_name}的模板图片\n"
        
        content += f"""
## 注意事项

1. 模板图片应该清晰、准确地表示要识别的界面元素
2. 建议使用PNG格式，保证图片质量
3. 模板图片大小不宜过大，建议控制在200x200像素以内
4. 确保模板图片在{resolution}分辨率下能够准确匹配

## 截图建议

1. 使用系统截图工具（如Windows的截图工具）
2. 截图时确保界面元素完整、清晰
3. 避免包含过多背景内容
4. 可以使用图像编辑软件进行裁剪和优化
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_config_file(self, config_path: Path, workflow_name: str) -> None:
        """创建配置文件"""
        config = TemplateConfig(
            name=workflow_name,
            description=f"Template configuration for {workflow_name}",
            confidence_threshold=0.8,
            match_method='TM_CCOEFF_NORMED',
            wait_timeout=10.0,
            retry_count=3,
            retry_interval=0.5
        )
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
    
    def list_workflows(self) -> List[str]:
        """列出所有工作流"""
        if not self.templates_dir.exists():
            return []
        
        workflows = []
        for item in self.templates_dir.iterdir():
            if item.is_dir():
                workflows.append(item.name)
        
        return sorted(workflows)
    
    def list_templates(self, workflow_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        列出模板文件
        
        Args:
            workflow_name: 工作流名称，None表示列出所有
        
        Returns:
            工作流到模板列表的映射
        """
        result = {}
        
        if workflow_name:
            workflows = [workflow_name] if workflow_name in self.list_workflows() else []
        else:
            workflows = self.list_workflows()
        
        for workflow in workflows:
            workflow_dir = self.templates_dir / workflow
            templates = set()
            
            # 扫描所有分辨率目录
            for resolution_dir in workflow_dir.iterdir():
                if resolution_dir.is_dir() and 'x' in resolution_dir.name:
                    for template_file in resolution_dir.iterdir():
                        if template_file.is_file() and template_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
                            templates.add(template_file.stem)
            
            result[workflow] = sorted(list(templates))
        
        return result
    
    def validate_template(self, template_path: str) -> Dict[str, Any]:
        """
        验证模板文件
        
        Args:
            template_path: 模板文件路径
        
        Returns:
            验证结果
        """
        result = {
            'valid': False,
            'path': template_path,
            'exists': False,
            'readable': False,
            'dimensions': None,
            'file_size': 0,
            'format': None,
            'issues': []
        }
        
        try:
            template_file = Path(template_path)
            
            # 检查文件是否存在
            if not template_file.exists():
                result['issues'].append('文件不存在')
                return result
            
            result['exists'] = True
            result['file_size'] = template_file.stat().st_size
            result['format'] = template_file.suffix.lower()
            
            # 检查文件格式
            if result['format'] not in ['.png', '.jpg', '.jpeg', '.bmp']:
                result['issues'].append(f'不支持的文件格式: {result["format"]}')
            
            # 尝试读取图像
            image = cv2.imread(str(template_file))
            if image is None:
                result['issues'].append('无法读取图像文件')
                return result
            
            result['readable'] = True
            result['dimensions'] = image.shape
            
            # 检查图像尺寸
            height, width = image.shape[:2]
            if width > 500 or height > 500:
                result['issues'].append(f'图像尺寸过大: {width}x{height}，建议小于500x500')
            
            if width < 10 or height < 10:
                result['issues'].append(f'图像尺寸过小: {width}x{height}，建议大于10x10')
            
            # 检查文件大小
            if result['file_size'] > 1024 * 1024:  # 1MB
                result['issues'].append(f'文件大小过大: {result["file_size"]} bytes，建议小于1MB')
            
            # 如果没有问题，标记为有效
            if not result['issues']:
                result['valid'] = True
            
        except Exception as e:
            result['issues'].append(f'验证过程中发生错误: {str(e)}')
        
        return result
    
    def optimize_template(self, template_path: str, output_path: Optional[str] = None) -> bool:
        """
        优化模板文件
        
        Args:
            template_path: 输入模板路径
            output_path: 输出路径，None表示覆盖原文件
        
        Returns:
            优化是否成功
        """
        try:
            template_file = Path(template_path)
            if not template_file.exists():
                self.logger.error(f"模板文件不存在: {template_path}")
                return False
            
            # 读取图像
            image = cv2.imread(str(template_file))
            if image is None:
                self.logger.error(f"无法读取图像: {template_path}")
                return False
            
            # 优化操作
            optimized_image = image.copy()
            
            # 1. 调整尺寸（如果过大）
            height, width = optimized_image.shape[:2]
            if width > 300 or height > 300:
                scale = min(300 / width, 300 / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                optimized_image = cv2.resize(optimized_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                self.logger.info(f"图像尺寸调整: {width}x{height} -> {new_width}x{new_height}")
            
            # 2. 降噪
            optimized_image = cv2.bilateralFilter(optimized_image, 9, 75, 75)
            
            # 3. 锐化
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            optimized_image = cv2.filter2D(optimized_image, -1, kernel)
            
            # 保存优化后的图像
            if output_path is None:
                output_path = template_path
            
            success = cv2.imwrite(str(output_path), optimized_image)
            if success:
                self.logger.info(f"模板优化完成: {output_path}")
                return True
            else:
                self.logger.error(f"保存优化图像失败: {output_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"优化模板失败: {e}")
            return False
    
    def copy_template(self, source_workflow: str, target_workflow: str, 
                     source_resolution: str, target_resolution: str) -> bool:
        """
        复制模板文件
        
        Args:
            source_workflow: 源工作流
            target_workflow: 目标工作流
            source_resolution: 源分辨率
            target_resolution: 目标分辨率
        
        Returns:
            复制是否成功
        """
        try:
            source_dir = self.templates_dir / source_workflow / source_resolution
            target_dir = self.templates_dir / target_workflow / target_resolution
            
            if not source_dir.exists():
                self.logger.error(f"源目录不存在: {source_dir}")
                return False
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制所有模板文件
            copied_count = 0
            for template_file in source_dir.iterdir():
                if template_file.is_file() and template_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
                    target_file = target_dir / template_file.name
                    shutil.copy2(template_file, target_file)
                    copied_count += 1
            
            self.logger.info(f"复制完成: {copied_count} 个模板文件从 {source_workflow}/{source_resolution} 到 {target_workflow}/{target_resolution}")
            return True
            
        except Exception as e:
            self.logger.error(f"复制模板失败: {e}")
            return False
    
    def test_template(self, template_path: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        测试模板匹配
        
        Args:
            template_path: 模板文件路径
            screenshot_path: 截图路径，None表示实时截图
        
        Returns:
            测试结果
        """
        result = {
            'success': False,
            'match_found': False,
            'match_result': None,
            'confidence': 0.0,
            'position': None,
            'error': None
        }
        
        try:
            template_file = Path(template_path)
            if not template_file.exists():
                result['error'] = f"模板文件不存在: {template_path}"
                return result
            
            # 获取截图
            if screenshot_path:
                screenshot_file = Path(screenshot_path)
                if not screenshot_file.exists():
                    result['error'] = f"截图文件不存在: {screenshot_path}"
                    return result
                screenshot = cv2.imread(str(screenshot_file))
            else:
                screenshot = self.vision_engine.take_screenshot()
            
            if screenshot is None:
                result['error'] = "无法获取截图"
                return result
            
            # 加载模板
            template = self.vision_engine.load_template(template_file)
            
            # 执行匹配
            match_result = self.vision_engine.match_template(screenshot, template)
            
            result['success'] = True
            
            if match_result:
                result['match_found'] = True
                result['match_result'] = match_result
                result['confidence'] = match_result.confidence
                result['position'] = match_result.center
            
        except Exception as e:
            result['error'] = f"测试过程中发生错误: {str(e)}"
        
        return result
    
    def generate_report(self, workflow_name: Optional[str] = None) -> Dict[str, Any]:
        """
        生成模板报告
        
        Args:
            workflow_name: 工作流名称，None表示所有工作流
        
        Returns:
            报告数据
        """
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'workflows': {},
            'summary': {
                'total_workflows': 0,
                'total_templates': 0,
                'valid_templates': 0,
                'invalid_templates': 0
            }
        }
        
        workflows = [workflow_name] if workflow_name else self.list_workflows()
        
        for workflow in workflows:
            workflow_report = {
                'name': workflow,
                'resolutions': {},
                'templates': {},
                'issues': []
            }
            
            workflow_dir = self.templates_dir / workflow
            if not workflow_dir.exists():
                workflow_report['issues'].append('工作流目录不存在')
                continue
            
            # 检查配置文件
            config_file = workflow_dir / "template_config.json"
            if not config_file.exists():
                workflow_report['issues'].append('缺少配置文件')
            
            # 扫描分辨率目录
            for resolution_dir in workflow_dir.iterdir():
                if resolution_dir.is_dir() and 'x' in resolution_dir.name:
                    resolution = resolution_dir.name
                    resolution_report = {
                        'name': resolution,
                        'template_count': 0,
                        'templates': []
                    }
                    
                    # 扫描模板文件
                    for template_file in resolution_dir.iterdir():
                        if template_file.is_file() and template_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
                            template_name = template_file.stem
                            validation_result = self.validate_template(str(template_file))
                            
                            template_report = {
                                'name': template_name,
                                'path': str(template_file),
                                'valid': validation_result['valid'],
                                'issues': validation_result['issues']
                            }
                            
                            resolution_report['templates'].append(template_report)
                            resolution_report['template_count'] += 1
                            
                            if validation_result['valid']:
                                report['summary']['valid_templates'] += 1
                            else:
                                report['summary']['invalid_templates'] += 1
                            
                            report['summary']['total_templates'] += 1
                    
                    workflow_report['resolutions'][resolution] = resolution_report
            
            report['workflows'][workflow] = workflow_report
            report['summary']['total_workflows'] += 1
        
        return report
    
    def print_report(self, report: Dict[str, Any]) -> None:
        """打印报告"""
        print("\n模板管理报告")
        print("=" * 60)
        
        # 汇总信息
        summary = report['summary']
        print(f"工作流数量: {summary['total_workflows']}")
        print(f"模板总数: {summary['total_templates']}")
        print(f"有效模板: {summary['valid_templates']}")
        print(f"无效模板: {summary['invalid_templates']}")
        
        # 详细信息
        for workflow_name, workflow_report in report['workflows'].items():
            print(f"\n工作流: {workflow_name}")
            print("-" * 40)
            
            if workflow_report['issues']:
                print("问题:")
                for issue in workflow_report['issues']:
                    print(f"  - {issue}")
            
            for resolution, resolution_report in workflow_report['resolutions'].items():
                print(f"\n  分辨率: {resolution} ({resolution_report['template_count']} 个模板)")
                
                for template in resolution_report['templates']:
                    status = "✓" if template['valid'] else "✗"
                    print(f"    {status} {template['name']}")
                    
                    if template['issues']:
                        for issue in template['issues']:
                            print(f"      - {issue}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RPA模板管理工具")
    parser.add_argument('--templates-dir', '-d', default='templates', help='模板目录路径')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建工作流命令
    create_parser = subparsers.add_parser('create', help='创建工作流模板结构')
    create_parser.add_argument('workflow', help='工作流名称')
    create_parser.add_argument('templates', nargs='+', help='模板名称列表')
    create_parser.add_argument('--resolutions', '-r', nargs='+', help='分辨率列表')
    
    # 列出工作流命令
    list_parser = subparsers.add_parser('list', help='列出工作流和模板')
    list_parser.add_argument('--workflow', '-w', help='指定工作流')
    
    # 验证模板命令
    validate_parser = subparsers.add_parser('validate', help='验证模板文件')
    validate_parser.add_argument('template', help='模板文件路径')
    
    # 优化模板命令
    optimize_parser = subparsers.add_parser('optimize', help='优化模板文件')
    optimize_parser.add_argument('template', help='模板文件路径')
    optimize_parser.add_argument('--output', '-o', help='输出路径')
    
    # 复制模板命令
    copy_parser = subparsers.add_parser('copy', help='复制模板文件')
    copy_parser.add_argument('source_workflow', help='源工作流')
    copy_parser.add_argument('target_workflow', help='目标工作流')
    copy_parser.add_argument('source_resolution', help='源分辨率')
    copy_parser.add_argument('target_resolution', help='目标分辨率')
    
    # 测试模板命令
    test_parser = subparsers.add_parser('test', help='测试模板匹配')
    test_parser.add_argument('template', help='模板文件路径')
    test_parser.add_argument('--screenshot', '-s', help='截图文件路径')
    
    # 生成报告命令
    report_parser = subparsers.add_parser('report', help='生成模板报告')
    report_parser.add_argument('--workflow', '-w', help='指定工作流')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tool = TemplateManagerTool(args.templates_dir)
    
    if args.command == 'create':
        success = tool.create_workflow(args.workflow, args.templates, args.resolutions)
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        if args.workflow:
            templates = tool.list_templates(args.workflow)
            if args.workflow in templates:
                print(f"工作流: {args.workflow}")
                for template in templates[args.workflow]:
                    print(f"  - {template}")
            else:
                print(f"工作流不存在: {args.workflow}")
        else:
            workflows = tool.list_workflows()
            templates = tool.list_templates()
            
            print("所有工作流:")
            for workflow in workflows:
                print(f"  {workflow}")
                if workflow in templates:
                    for template in templates[workflow]:
                        print(f"    - {template}")
    
    elif args.command == 'validate':
        result = tool.validate_template(args.template)
        print(f"模板验证结果: {'有效' if result['valid'] else '无效'}")
        if result['issues']:
            print("问题:")
            for issue in result['issues']:
                print(f"  - {issue}")
    
    elif args.command == 'optimize':
        success = tool.optimize_template(args.template, args.output)
        sys.exit(0 if success else 1)
    
    elif args.command == 'copy':
        success = tool.copy_template(
            args.source_workflow, args.target_workflow,
            args.source_resolution, args.target_resolution
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'test':
        result = tool.test_template(args.template, args.screenshot)
        if result['success']:
            if result['match_found']:
                print(f"匹配成功! 位置: {result['position']}, 置信度: {result['confidence']:.3f}")
            else:
                print("未找到匹配")
        else:
            print(f"测试失败: {result['error']}")
    
    elif args.command == 'report':
        report = tool.generate_report(args.workflow)
        tool.print_report(report)


if __name__ == '__main__':
    main()