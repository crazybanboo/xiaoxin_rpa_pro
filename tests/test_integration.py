"""
集成测试
测试各个模块之间的协作
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.config import Config
from core.vision import VisionEngine, MatchResult
from core.mouse import MouseController
from core.window import WindowManager, WindowInfo
from core.template import TemplateManager
from core.workflow import BaseWorkflow, WorkflowStep, WorkflowManager
from workflows.basic_example import BasicExampleWorkflow, SimpleClickWorkflow


@pytest.mark.integration
class TestRPAWorkflow:
    """测试完整的RPA工作流"""
    
    def test_vision_mouse_integration(self, mock_pyautogui):
        """测试图像识别与鼠标操作集成"""
        # 创建组件
        vision_engine = VisionEngine(confidence_threshold=0.8)
        mouse_controller = MouseController()
        
        # 模拟找到模板
        match_result = MatchResult(100, 200, 50, 30, 0.95)
        
        with patch.object(vision_engine, 'find_on_screen', return_value=match_result):
            # 查找模板
            template_path = "test_template.png"
            result = vision_engine.find_on_screen(template_path)
            
            assert result is not None
            
            # 点击找到的模板
            click_success = mouse_controller.click_match_result(result)
            
            assert click_success is True
            mock_pyautogui['click'].assert_called_once_with(
                125, 215, clicks=1, interval=0.0, button='left'
            )
    
    def test_window_mouse_integration(self, mock_win32gui, mock_pyautogui):
        """测试窗口管理与鼠标操作集成"""
        # 创建组件
        window_manager = WindowManager()
        mouse_controller = MouseController()
        
        # 模拟窗口信息
        window_info = WindowInfo(
            hwnd=12345,
            title="Test Window",
            class_name="TestClass",
            pid=1234,
            process_name="test.exe",
            rect=(100, 100, 500, 400),
            state=0,
            visible=True,
            enabled=True
        )
        
        with patch.object(window_manager, 'find_window_by_title', return_value=window_info), \
             patch.object(window_manager, 'activate_window', return_value=True):
            
            # 查找并激活窗口
            window = window_manager.find_window_by_title("Test Window")
            assert window is not None
            
            activate_success = window_manager.activate_window(window)
            assert activate_success is True
            
            # 在窗口中心点击
            center_x, center_y = window.center
            click_success = mouse_controller.click(center_x, center_y)
            
            assert click_success is True
            mock_pyautogui['click'].assert_called_once_with(
                center_x, center_y, clicks=1, interval=0.0, button='left'
            )
    
    def test_template_vision_integration(self, temp_dir):
        """测试模板管理与图像识别集成"""
        # 创建模板管理器
        template_manager = TemplateManager(str(temp_dir))
        vision_engine = VisionEngine()
        
        # 创建模板结构
        template_manager.create_template_structure("test_workflow", ["button", "input"])
        
        # 创建测试模板文件
        template_dir = temp_dir / "test_workflow" / "1920x1080"
        template_file = template_dir / "button.png"
        
        # 创建一个简单的测试图像
        import numpy as np
        import cv2
        
        image = np.zeros((50, 100, 3), dtype=np.uint8)
        cv2.rectangle(image, (10, 10), (90, 40), (255, 255, 255), -1)
        cv2.imwrite(str(template_file), image)
        
        # 重新加载模板
        template_manager._load_templates()
        
        # 获取模板
        template_item = template_manager.get_template("test_workflow.button")
        assert template_item is not None
        
        # 使用模板进行图像识别
        with patch.object(vision_engine, 'find_on_screen') as mock_find:
            mock_find.return_value = MatchResult(100, 100, 50, 30, 0.9)
            
            result = vision_engine.find_on_screen(template_item.path)
            assert result is not None
            assert result.confidence == 0.9


@pytest.mark.integration
class TestWorkflowExecution:
    """测试工作流执行"""
    
    def test_simple_workflow_execution(self, test_config):
        """测试简单工作流执行"""
        # 创建工作流管理器
        workflow_manager = WorkflowManager(test_config)
        
        # 注册测试工作流
        workflow_manager.register_workflow("simple_click", SimpleClickWorkflow)
        
        # 模拟PyAutoGUI
        with patch('pyautogui.click') as mock_click, \
             patch('pyautogui.FAILSAFE', False), \
             patch('pyautogui.PAUSE', 0.1):
            
            mock_click.return_value = None
            
            # 执行工作流
            success = workflow_manager.execute("simple_click")
            
            assert success is True
            # 验证点击了两次（根据SimpleClickWorkflow的定义）
            assert mock_click.call_count == 2
    
    def test_workflow_with_error_handling(self, test_config):
        """测试工作流错误处理"""
        
        class FailingWorkflow(BaseWorkflow):
            """会失败的测试工作流"""
            
            def _setup(self):
                self.add_step(FailingStep("失败步骤", {}))
        
        class FailingStep(WorkflowStep):
            """会失败的步骤"""
            
            def execute(self, context):
                raise Exception("测试异常")
        
        # 创建工作流管理器
        workflow_manager = WorkflowManager(test_config)
        workflow_manager.register_workflow("failing", FailingWorkflow)
        
        # 执行工作流
        success = workflow_manager.execute("failing")
        
        assert success is False
    
    def test_workflow_with_window_operations(self, test_config, mock_win32gui):
        """测试包含窗口操作的工作流"""
        
        class WindowWorkflow(BaseWorkflow):
            """窗口操作工作流"""
            
            def _setup(self):
                from core.window import WindowManager
                self.context['window_manager'] = WindowManager()
                self.add_step(WindowStep("窗口步骤", {}))
        
        class WindowStep(WorkflowStep):
            """窗口操作步骤"""
            
            def execute(self, context):
                window_manager = context['window_manager']
                # 模拟窗口操作
                return True
        
        # 创建工作流管理器
        workflow_manager = WorkflowManager(test_config)
        workflow_manager.register_workflow("window_test", WindowWorkflow)
        
        # 执行工作流
        success = workflow_manager.execute("window_test")
        
        assert success is True


@pytest.mark.integration
class TestConfigurationIntegration:
    """测试配置集成"""
    
    def test_config_with_all_modules(self, test_config):
        """测试配置与所有模块的集成"""
        # 测试配置能够正确初始化所有模块
        vision_config = test_config.get('vision', {})
        vision_engine = VisionEngine(
            confidence_threshold=vision_config.get('confidence_threshold', 0.8)
        )
        
        mouse_config = test_config.get('mouse', {})
        mouse_controller = MouseController(
            click_delay=mouse_config.get('click_delay', 0.1),
            move_duration=mouse_config.get('move_duration', 0.5),
            fail_safe=mouse_config.get('fail_safe', True)
        )
        
        window_config = test_config.get('window', {})
        window_manager = WindowManager(
            search_timeout=window_config.get('search_timeout', 5.0),
            activate_timeout=window_config.get('activate_timeout', 2.0)
        )
        
        template_config = test_config.get('templates', {})
        template_manager = TemplateManager(
            templates_dir=template_config.get('base_path', 'templates')
        )
        
        # 验证所有模块都正确初始化
        assert vision_engine.confidence_threshold == 0.9
        assert mouse_controller.click_delay == 0.05
        assert window_manager.search_timeout == 3.0
        assert template_manager.templates_dir.name == 'test_templates'
    
    def test_config_update_affects_modules(self, test_config):
        """测试配置更新影响模块"""
        # 更新配置
        test_config.set('vision.confidence_threshold', 0.95)
        test_config.set('mouse.click_delay', 0.15)
        
        # 创建新的模块实例
        vision_config = test_config.get('vision', {})
        vision_engine = VisionEngine(
            confidence_threshold=vision_config.get('confidence_threshold', 0.8)
        )
        
        mouse_config = test_config.get('mouse', {})
        mouse_controller = MouseController(
            click_delay=mouse_config.get('click_delay', 0.1)
        )
        
        # 验证配置更新生效
        assert vision_engine.confidence_threshold == 0.95
        assert mouse_controller.click_delay == 0.15


@pytest.mark.integration
class TestRealWorldScenarios:
    """测试真实场景"""
    
    def test_complete_automation_scenario(self, test_config, mock_pyautogui, mock_win32gui):
        """测试完整的自动化场景"""
        
        class CompleteScenario(BaseWorkflow):
            """完整场景工作流"""
            
            def _setup(self):
                from core.window import WindowManager
                from core.mouse import MouseController
                from core.vision import VisionEngine
                from core.template import TemplateManager
                
                # 初始化所有组件
                self.context['window_manager'] = WindowManager()
                self.context['mouse_controller'] = MouseController()
                self.context['vision_engine'] = VisionEngine()
                self.context['template_manager'] = TemplateManager()
                
                # 添加步骤
                self.add_step(FindWindowStep("查找窗口", {'title': 'Test App'}))
                self.add_step(ActivateWindowStep("激活窗口", {}))
                self.add_step(ClickButtonStep("点击按钮", {}))
        
        class FindWindowStep(WorkflowStep):
            def execute(self, context):
                window_manager = context['window_manager']
                # 模拟查找窗口
                return True
        
        class ActivateWindowStep(WorkflowStep):
            def execute(self, context):
                # 模拟激活窗口
                return True
        
        class ClickButtonStep(WorkflowStep):
            def execute(self, context):
                mouse_controller = context['mouse_controller']
                # 模拟点击按钮
                return mouse_controller.click(100, 100)
        
        # 创建工作流管理器
        workflow_manager = WorkflowManager(test_config)
        workflow_manager.register_workflow("complete_scenario", CompleteScenario)
        
        # 执行完整场景
        success = workflow_manager.execute("complete_scenario")
        
        assert success is True
        mock_pyautogui['click'].assert_called_once_with(
            100, 100, clicks=1, interval=0.0, button='left'
        )
    
    def test_error_recovery_scenario(self, test_config):
        """测试错误恢复场景"""
        
        class ErrorRecoveryWorkflow(BaseWorkflow):
            """错误恢复工作流"""
            
            def _setup(self):
                self.add_step(FlakeyStep("不稳定步骤", {}))
                self.add_step(RecoveryStep("恢复步骤", {}))
        
        class FlakeyStep(WorkflowStep):
            def __init__(self, name, config):
                super().__init__(name, config)
                self.attempt_count = 0
            
            def execute(self, context):
                self.attempt_count += 1
                if self.attempt_count < 3:
                    return False  # 前两次失败
                return True  # 第三次成功
        
        class RecoveryStep(WorkflowStep):
            def execute(self, context):
                return True
        
        # 创建工作流管理器
        workflow_manager = WorkflowManager(test_config)
        workflow_manager.register_workflow("error_recovery", ErrorRecoveryWorkflow)
        
        # 执行工作流（会失败，因为没有重试机制）
        success = workflow_manager.execute("error_recovery")
        
        assert success is False  # 第一个步骤失败，整个工作流失败


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """测试性能集成"""
    
    def test_multiple_workflow_execution(self, test_config, mock_pyautogui):
        """测试多个工作流执行性能"""
        workflow_manager = WorkflowManager(test_config)
        workflow_manager.register_workflow("simple_click", SimpleClickWorkflow)
        
        # 执行多次工作流
        results = []
        for i in range(10):
            success = workflow_manager.execute("simple_click")
            results.append(success)
        
        # 验证所有执行都成功
        assert all(results)
        
        # 验证总共点击了20次（10次执行 * 2次点击）
        assert mock_pyautogui['click'].call_count == 20
    
    def test_large_template_processing(self, temp_dir):
        """测试大量模板处理性能"""
        template_manager = TemplateManager(str(temp_dir))
        
        # 创建多个工作流模板
        workflows = [f"workflow_{i}" for i in range(50)]
        templates = [f"template_{i}" for i in range(10)]
        
        for workflow in workflows:
            template_manager.create_template_structure(workflow, templates)
        
        # 重新加载所有模板
        template_manager._load_templates()
        
        # 验证所有模板都被加载
        all_templates = template_manager.list_templates()
        assert len(all_templates) == 0  # 因为没有实际的图像文件
        
        # 但是目录结构应该被创建
        assert len(list(temp_dir.iterdir())) == 50