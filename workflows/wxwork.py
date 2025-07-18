"""
企业微信 肥龙工作流
"""

from core.workflow import BaseWorkflow, WorkflowStep
from core.vision import VisionEngine
from core.mouse import MouseController
from core.window import WindowManager
from core.template import TemplateManager

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

        self.add_step(ActivateWindowStep("激活企业微信窗口", {
            'use_current_window': True
        }))

        self.add_step(WaitUserOperationStep("等待用户操作", {
            'timeout': 10.0
        }))

        self.add_step(WaitForTemplateStep("等待多选框出现", {
            'template_name': 'wxwork_semi_auto.multi_box',
            'timeout': 10.0
        }))

        self.add_step(ClickTemplateStep("点击多选框", {
            'template_name': 'wxwork_semi_auto.multi_box',
            'use_last_match': True
        }))

        for i in range(0, 10):
            self.add_step(ClickTemplateStep("点击多选框", {
                'template_name': 'wxwork_semi_auto.multi_box',
                'use_last_match': False
            }))
