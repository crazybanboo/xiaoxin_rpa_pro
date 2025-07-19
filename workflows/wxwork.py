"""
企业微信 肥龙工作流
"""

import time
from pathlib import Path
from core.workflow import BaseWorkflow, WorkflowStep
from core.vision import VisionEngine
from core.mouse import MouseController, MouseButton
from core.window import WindowManager
from core.template import TemplateManager
from core.config import Config

class WaitForWxWorkWindowStep(WorkflowStep):
    """等待企业微信窗口出现"""

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.window_title = config.get('window_title')
        self.window_class = config.get('window_class')
        self.process_name = config.get('process_name')
        self.timeout = config.get('timeout', 10.0)

    def execute(self, context: dict) -> bool:
        """执行步骤"""
        window_manager = context.get('window_manager')
        
        if not isinstance(window_manager, WindowManager):
            return False
        
        # 等待窗口出现
        window_info = window_manager.wait_for_window(
            title=self.window_title,
            class_name=self.window_class,
            process_name=self.process_name,
            timeout=self.timeout
        )
        
        if window_info:
            context['current_window'] = window_info
            return True
        
        return False
    
class ActivateWindowStep(WorkflowStep):
    """激活窗口步骤"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.use_current_window = config.get('use_current_window', True)
        # 窗口位置配置
        self.window_x = config.get('window_x', 100)
        self.window_y = config.get('window_y', 100)
        # 窗口大小配置
        self.window_width = config.get('window_width', 1000)
        self.window_height = config.get('window_height', 1000)
        # 是否启用自动调整
        self.auto_adjust = config.get('auto_adjust', True)
    
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        window_manager = context.get('window_manager')
        
        if not isinstance(window_manager, WindowManager):
            return False
        
        # 获取要激活的窗口
        if self.use_current_window and 'current_window' in context:
            window_info = context['current_window']
        else:
            return False
        
        # 调整窗口位置和大小（如果启用自动调整）
        if self.auto_adjust:
            window_manager.move_window(window_info, self.window_x, self.window_y)
            window_manager.resize_window(window_info, self.window_width, self.window_height)
        
        # 激活窗口
        return window_manager.activate_window(window_info)
    
class WaitUserOperationStep(WorkflowStep):
    """等待用户操作"""

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.timeout = config.get('timeout', 10.0)

    def execute(self, context: dict) -> bool:
        """执行步骤"""
        input("请把转发窗口按出来，如果准备好了，接下来就可以点击y了：")
        return True
        
class WaitForTemplateStep(WorkflowStep):
    """等待模板出现步骤"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.template_name = config.get('template_name')
        self.timeout = config.get('timeout', 10.0)
        self.region = config.get('region')
    
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        
        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager):
            return False
        
        # 获取模板
        template_item = template_manager.get_template(self.template_name)
        if not template_item:
            return False
        
        # 等待模板出现
        result = vision_engine.wait_for_template(
            template_item.path,
            timeout=self.timeout,
            region=self.region
        )
        
        if result:
            context['last_match'] = result
            return True
        
        return False

class ClickTemplateStep(WorkflowStep):
    """点击模板步骤"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.template_name = config.get('template_name')
        self.use_last_match = config.get('use_last_match', False)
    
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        mouse_controller = context.get('mouse_controller')
        
        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager) or not isinstance(mouse_controller, MouseController):
            return False
        
        # 如果使用上次匹配结果
        if self.use_last_match and 'last_match' in context:
            match_result = context['last_match']
        else:
            # 获取模板
            template_item = template_manager.get_template(self.template_name)
            if not template_item:
                return False
            
            # 查找模板
            match_result = vision_engine.find_on_screen(template_item.path)
            if not match_result:
                return False
        
        # 点击模板中心
        success = mouse_controller.click_match_result(match_result)
        if success:
            context['last_click'] = match_result.center
        
        return success
    
class ClickMultiTemplateStep(WorkflowStep):
    """跳开第一个多选框，从第二个开始点选指定数量的多选框"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.template_name = config.get('template_name')
        self.skip_first = config.get('skip_first', True)  # 是否跳过第一个
        self.max_clicks = config.get('max_clicks', 9)  # 最大点击数量
        self.click_delay = config.get('click_delay', 0.1)  # 点击间隔

    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        mouse_controller = context.get('mouse_controller')

        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager) or not isinstance(mouse_controller, MouseController):
            return False

        # 获取模板
        template_item = template_manager.get_template(self.template_name)
        if not template_item:
            return False
        
        # 查找模板匹配到的所有结果
        match_results = vision_engine.find_all_on_screen(template_item.path)
        if not match_results:
            return False

        # 如果找到的匹配结果小于10个，则返回False
        if len(match_results) < 10:
            return False

        # 排序，按照y坐标排序，y坐标最大的排在最前面，y坐标最小的排在最后面
        match_results.sort(key=lambda x: x.y)

        # 确定要点击的结果
        if self.skip_first:
            targets = match_results[1:]  # 跳过第一个
        else:
            targets = match_results

        # 限制点击数量
        if self.max_clicks > 0:
            targets = targets[:self.max_clicks]

        # 点击所有目标
        clicked_count = 0
        for i, match_result in enumerate(targets):
            success = mouse_controller.click_match_result(match_result)
            if success:
                clicked_count += 1
                if self.click_delay > 0:
                    time.sleep(self.click_delay)
            else:
                pass

        return clicked_count > 0

class ClickSpecialTemplateStep(WorkflowStep):
    """特殊点击多选框序列"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.template_name = config.get('template_name')
        
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        mouse_controller = context.get('mouse_controller')
        
        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager) or \
            not isinstance(mouse_controller, MouseController):
            return False
        
        # 往下滚动鼠标
        mouse_controller.scroll(clicks=3, direction='down', strategy='multiple')

        # 获取模板
        template_item = template_manager.get_template(self.template_name)
        if not template_item:
            return False
        
        # 查找模板匹配到的所有结果
        match_results = vision_engine.find_all_on_screen(template_item.path)
        if not match_results:
            return False
        
        # 如果找到的匹配结果小于3个，则返回False
        if len(match_results) < 3:
            return False

        match_results.sort(key=lambda x: x.y)

        # step1: 特殊手法点击一遍
        for match_result in match_results[:3]:
            mouse_controller.mouse_down(match_result.center[0], match_result.center[1], button=MouseButton.LEFT)
            time.sleep(0.05)
            mouse_controller.mouse_down(match_result.center[0], match_result.center[1], button=MouseButton.RIGHT)
            time.sleep(0.05)
            mouse_controller.mouse_up(match_result.center[0], match_result.center[1], button=MouseButton.RIGHT)
            time.sleep(0.05)
            mouse_controller.mouse_up(match_result.center[0], match_result.center[1], button=MouseButton.LEFT)
            time.sleep(0.05)

        # step2: 取消选中他们再选中他们
        for match_result in match_results[:3]:
            mouse_controller.click_match_result(match_result)
        for match_result in match_results[:3]:
            mouse_controller.click_match_result(match_result)
            mouse_controller.click_match_result(match_result)

        # 重新找模板
        match_results = vision_engine.find_all_on_screen(template_item.path)
        if not match_results:
            return False

        # 排序，按照y坐标排序，y坐标最大的排在最前面，y坐标最小的排在最后面
        match_results.sort(key=lambda x: x.y)

        # 点击所有目标
        for match_result in match_results:
            mouse_controller.click_match_result(match_result)

        # 往下滚动鼠标
        mouse_controller.scroll(clicks=1, direction='down', strategy='multiple')

        # 开始疯狂连点
        center_x, center_y = match_results[-1].center
        center_x += 50
        # 1) 获取进程窗口的底部y坐标
        click_y = context['current_window'].rect[3] - 15
        mouse_controller.click(center_x, click_y, clicks=100, interval=0.05)

        return True


class WxworkWorkflow(BaseWorkflow):
    """
    企业微信 肥龙工作流
    半自动模式
    1. 找到企业微信本体窗口，并激活它
    2. 检测是否有待选box
    3. 点击待选box（按照特殊方法）
    """
    
    workflow_name = "wxwork_semi_auto"
    
    def _setup(self) -> None:
        """设置工作流步骤"""
        
        # 加载策略配置
        strategy_config_path = Path("config/wxwork_strategy.yaml")
        strategy_config = {}
        if strategy_config_path.exists():
            strategy_config_loader = Config(strategy_config_path)
            strategy_config = strategy_config_loader.get_all()
        
        # 初始化核心组件
        vision_config = self.config.get('vision', {})
        mouse_config = self.config.get('mouse', {})
        window_config = self.config.get('window', {})
        template_config = self.config.get('templates', {})

        self.context['vision_engine'] = VisionEngine(
            confidence_threshold=vision_config.get('confidence_threshold', 0.8)
        )
        self.context['mouse_controller'] = MouseController(
            click_delay=mouse_config.get('click_delay', 0.1),
            move_duration=mouse_config.get('move_duration', 0.5),
            fail_safe=mouse_config.get('fail_safe', True)
        )
        self.context['window_manager'] = WindowManager(
            search_timeout=window_config.get('search_timeout', 5.0),
            activate_timeout=window_config.get('activate_timeout', 2.0)
        )
        self.context['template_manager'] = TemplateManager(
            templates_dir=template_config.get('base_path', 'templates')
        )

        self.add_step(WaitForWxWorkWindowStep("等待企业微信窗口出现", {
            'window_title': '企业微信',
            'timeout': 10.0
        }))

        # 从策略配置获取窗口设置
        strategy_window_config = strategy_config.get('window', {})
        window_position = strategy_window_config.get('position', {})
        window_size = strategy_window_config.get('size', {})
        
        self.add_step(ActivateWindowStep("激活企业微信窗口", {
            'use_current_window': True,
            'window_x': window_position.get('x', 100),
            'window_y': window_position.get('y', 100),
            'window_width': window_size.get('width', 1000),
            'window_height': window_size.get('height', 1000),
            'auto_adjust': strategy_window_config.get('auto_adjust', True)
        }))

        self.add_step(WaitUserOperationStep("等待用户操作", {
            'timeout': 10.0
        }))

        self.add_step(WaitForTemplateStep("等待多选框出现", {
            'template_name': 'wxwork_semi_auto.multi_box',
            'timeout': 10.0
        }))

        self.add_step(ClickMultiTemplateStep("点击多选框", {
            'template_name': 'wxwork_semi_auto.multi_box',
            'skip_first': True,
            'max_clicks': 9,
            'click_delay': 0
        }))

        self.add_step(ClickSpecialTemplateStep("特殊点击多选框序列", {
            'template_name': 'wxwork_semi_auto.multi_box',
        }))