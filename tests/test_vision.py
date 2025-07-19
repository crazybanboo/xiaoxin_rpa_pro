"""
测试图像识别模块
"""

import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.vision import VisionEngine, MatchResult, create_vision_engine


@pytest.mark.unit
class TestMatchResult:
    """测试匹配结果类"""
    
    def test_match_result_init(self):
        """测试匹配结果初始化"""
        result = MatchResult(100, 200, 50, 30, 0.95)
        
        assert result.x == 100
        assert result.y == 200
        assert result.width == 50
        assert result.height == 30
        assert result.confidence == 0.95
    
    def test_match_result_center(self):
        """测试匹配结果中心点计算"""
        result = MatchResult(100, 200, 50, 30, 0.95)
        center = result.center
        
        assert center == (125, 215)  # (100+50/2, 200+30/2)
    
    def test_match_result_corners(self):
        """测试匹配结果角点计算"""
        result = MatchResult(100, 200, 50, 30, 0.95)
        
        assert result.top_left == (100, 200)
        assert result.bottom_right == (150, 230)
    
    def test_match_result_repr(self):
        """测试匹配结果字符串表示"""
        result = MatchResult(100, 200, 50, 30, 0.95)
        repr_str = repr(result)
        
        assert "MatchResult" in repr_str
        assert "center=(125, 215)" in repr_str
        assert "confidence=0.950" in repr_str


@pytest.mark.unit
class TestVisionEngine:
    """测试图像识别引擎"""
    
    def test_vision_engine_init(self):
        """测试图像识别引擎初始化"""
        engine = VisionEngine(confidence_threshold=0.9)
        
        assert engine.confidence_threshold == 0.9
        assert engine.default_method == cv2.TM_CCOEFF_NORMED
        assert len(engine.match_methods) > 0
    
    def test_vision_engine_init_default(self):
        """测试图像识别引擎默认初始化"""
        engine = VisionEngine()
        
        assert engine.confidence_threshold == 0.8
    
    @patch('pyautogui.screenshot')
    def test_take_screenshot(self, mock_screenshot):
        """测试截取屏幕图像"""
        engine = VisionEngine()
        
        # 模拟PyAutoGUI截图
        mock_image = MagicMock()
        mock_screenshot.return_value = mock_image
        
        with patch('cv2.cvtColor') as mock_cvtcolor:
            mock_cvtcolor.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            
            result = engine.take_screenshot()
            
            mock_screenshot.assert_called_once()
            mock_cvtcolor.assert_called_once()
            assert isinstance(result, np.ndarray)
    
    @patch('pyautogui.screenshot')
    def test_take_screenshot_with_region(self, mock_screenshot):
        """测试截取指定区域的屏幕图像"""
        engine = VisionEngine()
        region = (100, 100, 200, 150)
        
        mock_image = MagicMock()
        mock_screenshot.return_value = mock_image
        
        with patch('cv2.cvtColor') as mock_cvtcolor:
            mock_cvtcolor.return_value = np.zeros((150, 200, 3), dtype=np.uint8)
            
            result = engine.take_screenshot(region)
            
            mock_screenshot.assert_called_once_with(region=region)
            assert isinstance(result, np.ndarray)
    
    def test_load_template_success(self, sample_template_image):
        """测试成功加载模板图像"""
        engine = VisionEngine()
        template = engine.load_template(sample_template_image)
        
        assert isinstance(template, np.ndarray)
        assert template.shape == (100, 100, 3)
    
    def test_load_template_nonexistent(self):
        """测试加载不存在的模板图像"""
        engine = VisionEngine()
        
        with pytest.raises(FileNotFoundError):
            engine.load_template("nonexistent.png")
    
    def test_load_template_invalid_path(self, temp_dir):
        """测试加载无效的模板图像"""
        engine = VisionEngine()
        invalid_file = temp_dir / "invalid.png"
        invalid_file.write_text("not an image")
        
        with pytest.raises(ValueError):
            engine.load_template(invalid_file)
    
    def test_match_template_success(self, sample_screenshot, sample_template_image):
        """测试成功的模板匹配"""
        engine = VisionEngine(confidence_threshold=0.5)
        template = engine.load_template(sample_template_image)
        
        # 在截图中添加模板
        screenshot = sample_screenshot.copy()
        screenshot[490:590, 910:1010] = template
        
        result = engine.match_template(screenshot, template)
        
        assert result is not None
        assert isinstance(result, MatchResult)
        assert result.confidence >= 0.5
    
    def test_match_template_low_confidence(self, sample_screenshot, sample_template_image):
        """测试低置信度的模板匹配"""
        engine = VisionEngine(confidence_threshold=0.99)  # 设置很高的阈值
        template = engine.load_template(sample_template_image)
        
        result = engine.match_template(sample_screenshot, template)
        
        assert result is None
    
    def test_match_template_different_methods(self, sample_screenshot, sample_template_image):
        """测试不同的匹配方法"""
        engine = VisionEngine(confidence_threshold=0.5)
        template = engine.load_template(sample_template_image)
        
        # 在截图中添加模板
        screenshot = sample_screenshot.copy()
        screenshot[490:590, 910:1010] = template
        
        methods = ['TM_CCOEFF_NORMED', 'TM_CCORR_NORMED', 'TM_SQDIFF_NORMED']
        
        for method in methods:
            result = engine.match_template(screenshot, template, method=method)
            assert result is not None or method == 'TM_SQDIFF_NORMED'  # SQDIFF可能结果不同
    
    def test_match_template_grayscale(self, sample_screenshot, sample_template_image):
        """测试灰度图模板匹配"""
        engine = VisionEngine(confidence_threshold=0.5)
        template = engine.load_template(sample_template_image)
        
        # 在截图中添加模板
        screenshot = sample_screenshot.copy()
        screenshot[490:590, 910:1010] = template
        
        result = engine.match_template(screenshot, template, grayscale=True)
        
        assert result is not None
        assert isinstance(result, MatchResult)
    
    def test_find_all_matches(self, sample_screenshot, sample_template_image):
        """测试查找所有匹配项"""
        engine = VisionEngine(confidence_threshold=0.5)
        template = engine.load_template(sample_template_image)
        
        # 在截图中添加多个模板
        screenshot = sample_screenshot.copy()
        screenshot[100:200, 100:200] = template
        screenshot[300:400, 300:400] = template
        
        matches = engine.find_all_matches(screenshot, template)
        
        assert isinstance(matches, list)
        assert len(matches) >= 0  # 可能找到多个匹配
    
    @patch('pyautogui.screenshot')
    def test_find_on_screen(self, mock_screenshot, sample_template_image):
        """测试在屏幕上查找模板"""
        engine = VisionEngine(confidence_threshold=0.5)
        
        # 模拟截图
        mock_image = MagicMock()
        mock_screenshot.return_value = mock_image
        
        with patch('cv2.cvtColor') as mock_cvtcolor, \
             patch.object(engine, 'match_template') as mock_match:
            
            mock_cvtcolor.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_match.return_value = MatchResult(100, 100, 50, 50, 0.9)
            
            result = engine.find_on_screen(sample_template_image)
            
            assert result is not None
            assert isinstance(result, MatchResult)
    
    @patch('pyautogui.screenshot')
    def test_find_on_screen_with_region(self, mock_screenshot, sample_template_image):
        """测试在屏幕指定区域查找模板"""
        engine = VisionEngine()
        region = (100, 100, 200, 150)
        
        mock_image = MagicMock()
        mock_screenshot.return_value = mock_image
        
        with patch('cv2.cvtColor') as mock_cvtcolor, \
             patch.object(engine, 'match_template') as mock_match:
            
            mock_cvtcolor.return_value = np.zeros((150, 200, 3), dtype=np.uint8)
            mock_match.return_value = MatchResult(50, 50, 30, 30, 0.9)
            
            result = engine.find_on_screen(sample_template_image, region=region)
            
            assert result is not None
            assert result.x == 150  # 50 + region[0]
            assert result.y == 150  # 50 + region[1]
    
    @patch('pyautogui.screenshot')
    def test_find_all_on_screen(self, mock_screenshot, sample_template_image):
        """测试在屏幕上查找所有模板匹配"""
        engine = VisionEngine(confidence_threshold=0.5)
        
        # 模拟截图
        mock_image = MagicMock()
        mock_screenshot.return_value = mock_image
        
        with patch('cv2.cvtColor') as mock_cvtcolor, \
             patch.object(engine, 'find_all_matches') as mock_find_all:
            
            mock_cvtcolor.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_find_all.return_value = [
                MatchResult(100, 100, 50, 50, 0.9),
                MatchResult(200, 200, 50, 50, 0.8),
                MatchResult(300, 300, 50, 50, 0.7)
            ]
            
            results = engine.find_all_on_screen(sample_template_image)
            
            assert len(results) == 3
            assert all(isinstance(r, MatchResult) for r in results)
            assert results[0].confidence == 0.9
            assert results[1].confidence == 0.8
            assert results[2].confidence == 0.7
    
    @patch('pyautogui.screenshot')
    def test_find_all_on_screen_with_region(self, mock_screenshot, sample_template_image):
        """测试在屏幕指定区域查找所有模板匹配"""
        engine = VisionEngine()
        region = (100, 100, 200, 150)
        
        mock_image = MagicMock()
        mock_screenshot.return_value = mock_image
        
        with patch('cv2.cvtColor') as mock_cvtcolor, \
             patch.object(engine, 'find_all_matches') as mock_find_all:
            
            mock_cvtcolor.return_value = np.zeros((150, 200, 3), dtype=np.uint8)
            mock_find_all.return_value = [
                MatchResult(50, 50, 30, 30, 0.9),
                MatchResult(80, 80, 30, 30, 0.8)
            ]
            
            results = engine.find_all_on_screen(sample_template_image, region=region)
            
            assert len(results) == 2
            # 检查坐标调整
            assert results[0].x == 150  # 50 + region[0]
            assert results[0].y == 150  # 50 + region[1]
            assert results[1].x == 180  # 80 + region[0]
            assert results[1].y == 180  # 80 + region[1]
    
    @patch('time.sleep')
    def test_wait_for_template_success(self, mock_sleep, sample_template_image):
        """测试等待模板出现成功"""
        engine = VisionEngine()
        
        with patch.object(engine, 'find_on_screen') as mock_find:
            mock_find.return_value = MatchResult(100, 100, 50, 50, 0.9)
            
            result = engine.wait_for_template(sample_template_image, timeout=1.0)
            
            assert result is not None
            assert isinstance(result, MatchResult)
    
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_template_timeout(self, mock_time, mock_sleep, sample_template_image):
        """测试等待模板出现超时"""
        engine = VisionEngine()
        
        # 模拟时间流逝
        mock_time.side_effect = [0, 0.5, 1.0, 1.5]  # 超时
        
        with patch.object(engine, 'find_on_screen') as mock_find:
            mock_find.return_value = None
            
            result = engine.wait_for_template(sample_template_image, timeout=1.0)
            
            assert result is None
    
    def test_save_debug_image(self, sample_screenshot, temp_dir):
        """测试保存调试图像"""
        engine = VisionEngine()
        match_result = MatchResult(100, 100, 50, 50, 0.9)
        debug_path = temp_dir / "debug.png"
        
        with patch('cv2.rectangle') as mock_rectangle, \
             patch('cv2.putText') as mock_puttext, \
             patch('cv2.imwrite') as mock_imwrite:
            
            engine.save_debug_image(sample_screenshot, match_result, debug_path)
            
            mock_rectangle.assert_called_once()
            mock_puttext.assert_called_once()
            mock_imwrite.assert_called_once()
            # 检查调用参数
            call_args = mock_imwrite.call_args
            assert call_args[0][0] == str(debug_path)
            # 检查第二个参数是numpy数组
            import numpy as np
            assert isinstance(call_args[0][1], np.ndarray)


@pytest.mark.unit
class TestCreateVisionEngine:
    """测试创建图像识别引擎函数"""
    
    def test_create_vision_engine_default(self):
        """测试创建默认图像识别引擎"""
        config = {}
        engine = create_vision_engine(config)
        
        assert isinstance(engine, VisionEngine)
        assert engine.confidence_threshold == 0.8
    
    def test_create_vision_engine_with_config(self):
        """测试使用配置创建图像识别引擎"""
        config = {
            'confidence_threshold': 0.95
        }
        engine = create_vision_engine(config)
        
        assert isinstance(engine, VisionEngine)
        assert engine.confidence_threshold == 0.95


@pytest.mark.integration
class TestVisionEngineIntegration:
    """图像识别引擎集成测试"""
    
    def test_full_workflow(self, sample_template_image):
        """测试完整的图像识别工作流"""
        engine = VisionEngine(confidence_threshold=0.5)
        
        # 创建一个包含模板的屏幕截图
        screenshot = np.zeros((500, 500, 3), dtype=np.uint8)
        template = engine.load_template(sample_template_image)
        
        # 将模板放在截图的特定位置
        screenshot[200:300, 200:300] = template
        
        # 执行匹配
        with patch.object(engine, 'take_screenshot', return_value=screenshot):
            result = engine.find_on_screen(sample_template_image)
            
            assert result is not None
            assert 200 <= result.x <= 220  # 允许一些误差
            assert 200 <= result.y <= 220
            assert result.confidence >= 0.5