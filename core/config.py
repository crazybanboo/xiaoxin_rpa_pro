"""
配置管理模块
支持YAML和JSON格式的配置文件
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .logger import LoggerMixin


class Config(LoggerMixin):
    """配置管理类"""
    
    def __init__(self, config_path: Union[str, Path]):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._data = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    self._data = yaml.safe_load(f) or {}
                elif self.config_path.suffix.lower() == '.json':
                    self._data = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_path.suffix}")
            
            self.logger.info(f"配置文件加载成功: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持嵌套键访问
        
        Args:
            key: 配置键，支持点号分隔的嵌套访问，如 'database.host'
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        data = self._data
        
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        
        return data
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        data = self._data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(self._data, f, default_flow_style=False, allow_unicode=True)
                elif self.config_path.suffix.lower() == '.json':
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置文件保存成功: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
            raise
    
    def validate(self, schema: Dict[str, Any]) -> bool:
        """
        验证配置是否符合模式
        
        Args:
            schema: 配置模式
        
        Returns:
            验证结果
        """
        try:
            self._validate_recursive(self._data, schema)
            return True
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return False
    
    def _validate_recursive(self, data: Any, schema: Any) -> None:
        """递归验证配置"""
        if isinstance(schema, dict):
            if not isinstance(data, dict):
                raise ValueError(f"期望字典类型，实际为: {type(data)}")
            
            for key, value_schema in schema.items():
                if key.endswith('?'):  # 可选字段
                    key = key[:-1]
                    if key not in data:
                        continue
                else:  # 必需字段
                    if key not in data:
                        raise ValueError(f"缺少必需字段: {key}")
                
                self._validate_recursive(data[key], value_schema)
        
        elif isinstance(schema, type):
            if not isinstance(data, schema):
                raise ValueError(f"期望类型 {schema.__name__}，实际为: {type(data).__name__}")
        
        elif callable(schema):
            if not schema(data):
                raise ValueError(f"验证函数失败: {schema}")
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._data.copy()
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典式设置"""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.get(key) is not None


def create_default_config(config_path: Union[str, Path]) -> None:
    """
    创建默认配置文件
    
    Args:
        config_path: 配置文件路径
    """
    default_config = {
        'app': {
            'name': 'Xiaoxin RPA Pro',
            'version': '1.0.0',
            'debug': False
        },
        'logging': {
            'level': 'INFO',
            'file_enabled': True,
            'console_enabled': True,
            'rotation': {
                'enabled': True,
                'max_bytes': 10485760,  # 10MB
                'backup_count': 5
            }
        },
        'vision': {
            'confidence_threshold': 0.8,
            'match_method': 'cv2.TM_CCOEFF_NORMED',
            'grayscale': True
        },
        'mouse': {
            'click_delay': 0.1,
            'move_duration': 0.5,
            'fail_safe': True
        },
        'window': {
            'search_timeout': 5.0,
            'activate_timeout': 2.0
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
    
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            yaml.safe_dump(default_config, f, default_flow_style=False, allow_unicode=True)
        else:
            json.dump(default_config, f, indent=2, ensure_ascii=False)