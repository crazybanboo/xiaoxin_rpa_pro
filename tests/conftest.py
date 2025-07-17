"""
pytest配置文件
提供测试夹具和全局配置
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config
from core.logger import setup_logger
from core.vision import VisionEngine
from core.mouse import MouseController
from core.window import WindowManager
from core.template import TemplateManager


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config_data():
    """示例配置数据"""
    return {
        'app': {
            'name': 'Test RPA',
            'version': '1.0.0',
            'debug': True
        },
        'logging': {
            'level': 'DEBUG',
            'file_enabled': False,
            'console_enabled': True
        },
        'vision': {
            'confidence_threshold': 0.9,
            'match_method': 'cv2.TM_CCOEFF_NORMED',
            'grayscale': True
        },
        'mouse': {
            'click_delay': 0.05,
            'move_duration': 0.1,
            'fail_safe': False
        },
        'window': {
            'search_timeout': 3.0,
            'activate_timeout': 1.0
        },
        'templates': {
            'base_path': 'test_templates',
            'auto_resolution': True,
            'supported_formats': ['.png', '.jpg']
        }
    }


@pytest.fixture
def config_file(temp_dir, sample_config_data):
    """创建测试配置文件"""
    import yaml
    config_path = temp_dir / "test_config.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(sample_config_data, f)
    return config_path


@pytest.fixture
def test_config(config_file):
    """测试配置对象"""
    return Config(config_file)


@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    return setup_logger("test", level="DEBUG", debug=True)


@pytest.fixture
def mock_vision_engine():
    """模拟图像识别引擎"""
    with patch('core.vision.VisionEngine') as mock:
        engine = mock.return_value
        engine.confidence_threshold = 0.8
        engine.take_screenshot.return_value = MagicMock()
        engine.load_template.return_value = MagicMock()
        engine.match_template.return_value = MagicMock()
        engine.find_on_screen.return_value = MagicMock()
        yield engine


@pytest.fixture
def mock_mouse_controller():
    """模拟鼠标控制器"""
    with patch('core.mouse.MouseController') as mock:
        controller = mock.return_value
        controller.click.return_value = True
        controller.move_to.return_value = True
        controller.drag.return_value = True
        controller.scroll.return_value = True
        yield controller


@pytest.fixture
def mock_window_manager():
    """模拟窗口管理器"""
    with patch('core.window.WindowManager') as mock:
        manager = mock.return_value
        manager.get_all_windows.return_value = []
        manager.find_window_by_title.return_value = MagicMock()
        manager.activate_window.return_value = True
        yield manager


@pytest.fixture
def mock_template_manager(temp_dir):
    """模拟模板管理器"""
    with patch('core.template.TemplateManager') as mock:
        manager = mock.return_value
        manager.templates_dir = temp_dir / "templates"
        manager.get_template.return_value = MagicMock()
        manager.list_templates.return_value = []
        yield manager


@pytest.fixture
def sample_template_image(temp_dir):
    """创建示例模板图像"""
    import numpy as np
    import cv2
    
    # 创建一个简单的测试图像
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(image, (25, 25), (75, 75), (255, 255, 255), -1)
    
    template_path = temp_dir / "test_template.png"
    cv2.imwrite(str(template_path), image)
    
    return template_path


@pytest.fixture
def sample_screenshot():
    """创建示例屏幕截图"""
    import numpy as np
    
    # 创建一个简单的屏幕截图
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # 在中间添加一个白色矩形
    screenshot[490:590, 910:1010] = [255, 255, 255]
    
    return screenshot


@pytest.fixture(autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 禁用PyAutoGUI的fail-safe功能
    with patch('pyautogui.FAILSAFE', False):
        yield


@pytest.fixture
def mock_pyautogui():
    """模拟PyAutoGUI"""
    with patch('pyautogui.click') as mock_click, \
         patch('pyautogui.moveTo') as mock_move, \
         patch('pyautogui.drag') as mock_drag, \
         patch('pyautogui.scroll') as mock_scroll, \
         patch('pyautogui.screenshot') as mock_screenshot, \
         patch('pyautogui.position') as mock_position, \
         patch('pyautogui.size') as mock_size, \
         patch('pyautogui.mouseDown') as mock_mousedown, \
         patch('pyautogui.mouseUp') as mock_mouseup:
        
        mock_position.return_value = MagicMock(x=500, y=500)
        mock_size.return_value = MagicMock(width=1920, height=1080)
        
        yield {
            'click': mock_click,
            'moveTo': mock_move,
            'drag': mock_drag,
            'scroll': mock_scroll,
            'screenshot': mock_screenshot,
            'position': mock_position,
            'size': mock_size,
            'mouseDown': mock_mousedown,
            'mouseUp': mock_mouseup
        }


@pytest.fixture
def mock_win32gui():
    """模拟Win32GUI"""
    with patch('win32gui.EnumWindows') as mock_enum, \
         patch('win32gui.GetWindowText') as mock_get_text, \
         patch('win32gui.GetClassName') as mock_get_class, \
         patch('win32gui.GetWindowRect') as mock_get_rect, \
         patch('win32gui.IsWindowVisible') as mock_is_visible, \
         patch('win32gui.SetForegroundWindow') as mock_set_foreground:
        
        mock_get_text.return_value = "Test Window"
        mock_get_class.return_value = "TestClass"
        mock_get_rect.return_value = (100, 100, 500, 400)
        mock_is_visible.return_value = True
        mock_set_foreground.return_value = True
        
        yield {
            'enum_windows': mock_enum,
            'get_window_text': mock_get_text,
            'get_class_name': mock_get_class,
            'get_window_rect': mock_get_rect,
            'is_window_visible': mock_is_visible,
            'set_foreground_window': mock_set_foreground
        }


# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "gui: 需要GUI的测试")


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    # 为GUI测试添加跳过标记
    skip_gui = pytest.mark.skip(reason="需要GUI环境")
    
    for item in items:
        if "gui" in item.keywords:
            # 在无GUI环境中跳过GUI测试
            if not hasattr(item, 'gui_available'):
                item.add_marker(skip_gui)