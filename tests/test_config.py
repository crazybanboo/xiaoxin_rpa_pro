"""
测试配置管理模块
"""

import pytest
import json
import yaml
from pathlib import Path

from core.config import Config, create_default_config


@pytest.mark.unit
class TestConfig:
    """配置管理测试类"""
    
    def test_init_with_yaml_file(self, config_file):
        """测试使用YAML文件初始化配置"""
        config = Config(config_file)
        assert config.get('app.name') == 'Test RPA'
        assert config.get('app.version') == '1.0.2'
        assert config.get('logging.level') == 'DEBUG'
    
    def test_init_with_json_file(self, temp_dir, sample_config_data):
        """测试使用JSON文件初始化配置"""
        json_file = temp_dir / "test_config.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_config_data, f)
        
        config = Config(json_file)
        assert config.get('app.name') == 'Test RPA'
        assert config.get('vision.confidence_threshold') == 0.9
    
    def test_init_nonexistent_file(self):
        """测试使用不存在的文件初始化配置"""
        with pytest.raises(FileNotFoundError):
            Config("nonexistent.yaml")
    
    def test_init_unsupported_format(self, temp_dir):
        """测试不支持的配置文件格式"""
        txt_file = temp_dir / "config.txt"
        txt_file.write_text("test content")
        
        with pytest.raises(ValueError):
            Config(txt_file)
    
    def test_get_simple_key(self, test_config):
        """测试获取简单键值"""
        assert test_config.get('app') is not None
        assert isinstance(test_config.get('app'), dict)
    
    def test_get_nested_key(self, test_config):
        """测试获取嵌套键值"""
        assert test_config.get('app.name') == 'Test RPA'
        assert test_config.get('vision.confidence_threshold') == 0.9
        assert test_config.get('mouse.click_delay') == 0.05
    
    def test_get_nonexistent_key(self, test_config):
        """测试获取不存在的键值"""
        assert test_config.get('nonexistent') is None
        assert test_config.get('nonexistent.key') is None
        assert test_config.get('app.nonexistent') is None
    
    def test_get_with_default(self, test_config):
        """测试获取键值时提供默认值"""
        assert test_config.get('nonexistent', 'default') == 'default'
        assert test_config.get('app.nonexistent', 42) == 42
    
    def test_set_simple_key(self, test_config):
        """测试设置简单键值"""
        test_config.set('new_key', 'new_value')
        assert test_config.get('new_key') == 'new_value'
    
    def test_set_nested_key(self, test_config):
        """测试设置嵌套键值"""
        test_config.set('new_section.new_key', 'new_value')
        assert test_config.get('new_section.new_key') == 'new_value'
        assert test_config.get('new_section') == {'new_key': 'new_value'}
    
    def test_set_existing_key(self, test_config):
        """测试设置已存在的键值"""
        original_value = test_config.get('app.name')
        test_config.set('app.name', 'Updated Name')
        assert test_config.get('app.name') == 'Updated Name'
        assert test_config.get('app.name') != original_value
    
    def test_save_yaml_file(self, test_config, temp_dir):
        """测试保存YAML文件"""
        test_config.set('new_key', 'new_value')
        
        new_file = temp_dir / "saved_config.yaml"
        test_config.config_path = new_file
        test_config.save()
        
        assert new_file.exists()
        
        # 验证保存的内容
        with open(new_file, 'r', encoding='utf-8') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data['new_key'] == 'new_value'
        assert saved_data['app']['name'] == 'Test RPA'
    
    def test_save_json_file(self, test_config, temp_dir):
        """测试保存JSON文件"""
        test_config.set('new_key', 'new_value')
        
        new_file = temp_dir / "saved_config.json"
        test_config.config_path = new_file
        test_config.save()
        
        assert new_file.exists()
        
        # 验证保存的内容
        with open(new_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['new_key'] == 'new_value'
        assert saved_data['app']['name'] == 'Test RPA'
    
    def test_validate_valid_schema(self, test_config):
        """测试验证有效的配置模式"""
        schema = {
            'app': {
                'name': str,
                'version': str,
                'debug': bool
            },
            'logging': {
                'level': str,
                'file_enabled': bool
            }
        }
        
        assert test_config.validate(schema) is True
    
    def test_validate_invalid_schema(self, test_config):
        """测试验证无效的配置模式"""
        schema = {
            'app': {
                'name': str,
                'version': str,
                'debug': bool,
                'required_missing': str  # 缺少的必需字段
            }
        }
        
        assert test_config.validate(schema) is False
    
    def test_validate_optional_field(self, test_config):
        """测试验证可选字段"""
        schema = {
            'app': {
                'name': str,
                'version': str,
                'debug': bool,
                'optional_field?': str  # 可选字段
            }
        }
        
        assert test_config.validate(schema) is True
    
    def test_validate_type_mismatch(self, test_config):
        """测试验证类型不匹配"""
        schema = {
            'app': {
                'name': int,  # 应该是字符串，但要求整数
                'version': str
            }
        }
        
        assert test_config.validate(schema) is False
    
    def test_get_all(self, test_config):
        """测试获取所有配置"""
        all_config = test_config.get_all()
        assert isinstance(all_config, dict)
        assert 'app' in all_config
        assert 'logging' in all_config
        assert 'vision' in all_config
        
        # 确保返回的是副本
        all_config['new_key'] = 'new_value'
        assert 'new_key' not in test_config.get_all()
    
    def test_dict_access(self, test_config):
        """测试字典式访问"""
        assert test_config['app.name'] == 'Test RPA'
        assert test_config['vision.confidence_threshold'] == 0.9
        
        test_config['new_key'] = 'new_value'
        assert test_config['new_key'] == 'new_value'
    
    def test_contains(self, test_config):
        """测试 in 操作符"""
        assert 'app.name' in test_config
        assert 'vision.confidence_threshold' in test_config
        assert 'nonexistent' not in test_config
        assert 'app.nonexistent' not in test_config


@pytest.mark.unit
class TestCreateDefaultConfig:
    """测试创建默认配置功能"""
    
    def test_create_default_yaml(self, temp_dir):
        """测试创建默认YAML配置"""
        config_path = temp_dir / "default.yaml"
        create_default_config(config_path)
        
        assert config_path.exists()
        
        # 验证配置内容
        config = Config(config_path)
        assert config.get('app.name') == 'Xiaoxin RPA Pro'
        assert config.get('app.version') == '1.0.2'
        assert config.get('vision.confidence_threshold') == 0.8
        assert config.get('mouse.click_delay') == 0.1
    
    def test_create_default_json(self, temp_dir):
        """测试创建默认JSON配置"""
        config_path = temp_dir / "default.json"
        create_default_config(config_path)
        
        assert config_path.exists()
        
        # 验证配置内容
        config = Config(config_path)
        assert config.get('app.name') == 'Xiaoxin RPA Pro'
        assert config.get('templates.base_path') == 'templates'
        assert config.get('workflow.step_delay') == 0.5
    
    def test_create_default_nested_dir(self, temp_dir):
        """测试在嵌套目录中创建默认配置"""
        nested_dir = temp_dir / "nested" / "config"
        config_path = nested_dir / "default.yaml"
        
        create_default_config(config_path)
        
        assert config_path.exists()
        assert nested_dir.exists()
        
        # 验证配置内容
        config = Config(config_path)
        assert config.get('app.name') == 'Xiaoxin RPA Pro'