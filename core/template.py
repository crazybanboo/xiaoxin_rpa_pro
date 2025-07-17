"""
模板管理模块
管理不同分辨率的模板文件和模板配置
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import pyautogui

from .logger import LoggerMixin


@dataclass
class TemplateConfig:
    """模板配置类"""
    name: str
    description: str
    confidence_threshold: float
    match_method: str
    region: Optional[Tuple[int, int, int, int]] = None
    wait_timeout: float = 10.0
    retry_count: int = 3
    retry_interval: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateConfig':
        """从字典创建"""
        return cls(**data)


@dataclass
class TemplateItem:
    """模板项类"""
    path: Path
    resolution: str
    config: TemplateConfig
    
    def __repr__(self) -> str:
        return f"TemplateItem(path={self.path}, resolution={self.resolution})"


class TemplateManager(LoggerMixin):
    """模板管理器"""
    
    def __init__(self, templates_dir: str = "templates"):
        """
        初始化模板管理器
        
        Args:
            templates_dir: 模板目录路径
        """
        self.templates_dir = Path(templates_dir)
        self.templates: Dict[str, Dict[str, TemplateItem]] = {}
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        
        # 确保模板目录存在
        self.templates_dir.mkdir(exist_ok=True)
        
        # 加载所有模板
        self._load_templates()
        
        self.logger.info(f"模板管理器初始化完成，模板目录: {self.templates_dir}")
    
    def _load_templates(self) -> None:
        """加载所有模板"""
        if not self.templates_dir.exists():
            self.logger.warning(f"模板目录不存在: {self.templates_dir}")
            return
        
        # 遍历工作流目录
        for workflow_dir in self.templates_dir.iterdir():
            if workflow_dir.is_dir():
                self._load_workflow_templates(workflow_dir)
    
    def _load_workflow_templates(self, workflow_dir: Path) -> None:
        """
        加载工作流模板
        
        Args:
            workflow_dir: 工作流目录
        """
        workflow_name = workflow_dir.name
        self.templates[workflow_name] = {}
        
        # 加载模板配置
        config_file = workflow_dir / "template_config.json"
        default_config = self._get_default_template_config(workflow_name)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                template_config = TemplateConfig.from_dict(config_data)
            except Exception as e:
                self.logger.error(f"加载模板配置失败: {config_file}, 错误: {e}")
                template_config = default_config
        else:
            template_config = default_config
        
        # 遍历分辨率目录
        for resolution_dir in workflow_dir.iterdir():
            if resolution_dir.is_dir() and self._is_resolution_dir(resolution_dir.name):
                self._load_resolution_templates(workflow_name, resolution_dir, template_config)
    
    def _load_resolution_templates(self, workflow_name: str, resolution_dir: Path, config: TemplateConfig) -> None:
        """
        加载分辨率模板
        
        Args:
            workflow_name: 工作流名称
            resolution_dir: 分辨率目录
            config: 模板配置
        """
        resolution = resolution_dir.name
        
        # 查找模板文件
        for template_file in resolution_dir.iterdir():
            if template_file.is_file() and template_file.suffix.lower() in self.supported_formats:
                template_item = TemplateItem(
                    path=template_file,
                    resolution=resolution,
                    config=config
                )
                
                # 使用模板文件名作为键
                template_key = template_file.stem
                full_key = f"{workflow_name}.{template_key}"
                
                if workflow_name not in self.templates:
                    self.templates[workflow_name] = {}
                
                if full_key not in self.templates[workflow_name]:
                    self.templates[workflow_name][full_key] = {}
                
                self.templates[workflow_name][full_key][resolution] = template_item
                
                self.logger.debug(f"加载模板: {full_key}, 分辨率: {resolution}")
    
    def _is_resolution_dir(self, dir_name: str) -> bool:
        """
        检查是否为分辨率目录
        
        Args:
            dir_name: 目录名称
        
        Returns:
            是否为分辨率目录
        """
        # 检查是否为 "宽度x高度" 格式
        if 'x' in dir_name.lower():
            parts = dir_name.lower().split('x')
            if len(parts) == 2:
                try:
                    int(parts[0])
                    int(parts[1])
                    return True
                except ValueError:
                    pass
        
        return False
    
    def _get_default_template_config(self, workflow_name: str) -> TemplateConfig:
        """
        获取默认模板配置
        
        Args:
            workflow_name: 工作流名称
        
        Returns:
            默认模板配置
        """
        return TemplateConfig(
            name=workflow_name,
            description=f"Default template config for {workflow_name}",
            confidence_threshold=0.8,
            match_method='TM_CCOEFF_NORMED',
            wait_timeout=10.0,
            retry_count=3,
            retry_interval=0.5
        )
    
    def get_current_resolution(self) -> str:
        """
        获取当前屏幕分辨率
        
        Returns:
            分辨率字符串
        """
        size = pyautogui.size()
        return f"{size.width}x{size.height}"
    
    def get_template(self, template_name: str, resolution: Optional[str] = None) -> Optional[TemplateItem]:
        """
        获取模板
        
        Args:
            template_name: 模板名称 (格式: workflow.template_name)
            resolution: 分辨率，None则使用当前分辨率
        
        Returns:
            模板项
        """
        if resolution is None:
            resolution = self.get_current_resolution()
        
        # 解析模板名称
        if '.' not in template_name:
            self.logger.error(f"模板名称格式错误: {template_name}, 应为 'workflow.template_name'")
            return None
        
        workflow_name, template_key = template_name.split('.', 1)
        full_key = f"{workflow_name}.{template_key}"
        
        # 查找模板
        if workflow_name in self.templates and full_key in self.templates[workflow_name]:
            templates = self.templates[workflow_name][full_key]
            
            # 优先使用指定分辨率
            if resolution in templates:
                return templates[resolution]
            
            # 如果没有找到指定分辨率，尝试查找最接近的分辨率
            return self._find_closest_resolution_template(templates, resolution)
        
        self.logger.warning(f"模板不存在: {template_name}")
        return None
    
    def _find_closest_resolution_template(self, templates: Dict[str, TemplateItem], target_resolution: str) -> Optional[TemplateItem]:
        """
        查找最接近的分辨率模板
        
        Args:
            templates: 模板字典
            target_resolution: 目标分辨率
        
        Returns:
            最接近的模板项
        """
        try:
            target_width, target_height = map(int, target_resolution.split('x'))
            target_pixels = target_width * target_height
            
            best_template = None
            min_diff = float('inf')
            
            for resolution, template in templates.items():
                try:
                    width, height = map(int, resolution.split('x'))
                    pixels = width * height
                    diff = abs(pixels - target_pixels)
                    
                    if diff < min_diff:
                        min_diff = diff
                        best_template = template
                        
                except ValueError:
                    continue
            
            if best_template:
                self.logger.info(f"使用最接近的分辨率模板: {best_template.resolution} -> {target_resolution}")
            
            return best_template
            
        except Exception as e:
            self.logger.error(f"查找最接近分辨率模板失败: {e}")
            return None
    
    def list_templates(self, workflow_name: Optional[str] = None) -> List[str]:
        """
        列出模板
        
        Args:
            workflow_name: 工作流名称，None则列出所有
        
        Returns:
            模板名称列表
        """
        template_names = []
        
        if workflow_name:
            if workflow_name in self.templates:
                template_names.extend(self.templates[workflow_name].keys())
        else:
            for workflow, templates in self.templates.items():
                template_names.extend(templates.keys())
        
        return sorted(template_names)
    
    def list_resolutions(self, template_name: str) -> List[str]:
        """
        列出模板支持的分辨率
        
        Args:
            template_name: 模板名称
        
        Returns:
            分辨率列表
        """
        if '.' not in template_name:
            return []
        
        workflow_name, template_key = template_name.split('.', 1)
        full_key = f"{workflow_name}.{template_key}"
        
        if workflow_name in self.templates and full_key in self.templates[workflow_name]:
            return list(self.templates[workflow_name][full_key].keys())
        
        return []
    
    def create_template_structure(self, workflow_name: str, template_names: List[str]) -> None:
        """
        创建模板目录结构
        
        Args:
            workflow_name: 工作流名称
            template_names: 模板名称列表
        """
        workflow_dir = self.templates_dir / workflow_name
        workflow_dir.mkdir(exist_ok=True)
        
        # 创建配置文件
        config_file = workflow_dir / "template_config.json"
        if not config_file.exists():
            config = self._get_default_template_config(workflow_name)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        
        # 创建常见分辨率目录
        common_resolutions = ["1920x1080", "1366x768", "1440x900", "1280x1024"]
        
        for resolution in common_resolutions:
            resolution_dir = workflow_dir / resolution
            resolution_dir.mkdir(exist_ok=True)
            
            # 创建说明文件
            readme_file = resolution_dir / "README.md"
            if not readme_file.exists():
                content = f"""# {workflow_name} - {resolution}

请将以下模板图片放置在此目录中：

"""
                for template_name in template_names:
                    content += f"- {template_name}.png\n"
                
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        self.logger.info(f"模板目录结构创建完成: {workflow_dir}")
    
    def validate_template(self, template_item: TemplateItem) -> bool:
        """
        验证模板文件
        
        Args:
            template_item: 模板项
        
        Returns:
            验证结果
        """
        if not template_item.path.exists():
            self.logger.error(f"模板文件不存在: {template_item.path}")
            return False
        
        if template_item.path.suffix.lower() not in self.supported_formats:
            self.logger.error(f"不支持的模板格式: {template_item.path.suffix}")
            return False
        
        # 可以添加更多验证逻辑，如图像尺寸、文件大小等
        
        return True
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模板信息
        
        Args:
            template_name: 模板名称
        
        Returns:
            模板信息字典
        """
        template_item = self.get_template(template_name)
        if not template_item:
            return None
        
        return {
            'name': template_name,
            'path': str(template_item.path),
            'resolution': template_item.resolution,
            'config': template_item.config.to_dict(),
            'exists': template_item.path.exists(),
            'size': template_item.path.stat().st_size if template_item.path.exists() else 0
        }


def create_template_manager(config: dict) -> TemplateManager:
    """
    创建模板管理器
    
    Args:
        config: 配置字典
    
    Returns:
        模板管理器实例
    """
    return TemplateManager(
        templates_dir=config.get('base_path', 'templates')
    )