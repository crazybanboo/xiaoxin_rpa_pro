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
        
        # 激活窗口
        window_manager.activate_window(window_info)

        # 调整窗口位置和大小（如果启用自动调整）
        if self.auto_adjust:
            self.logger.info(f"开始调整窗口位置和大小: 位置({self.window_x}, {self.window_y}), 大小({self.window_width}x{self.window_height})")
            self.logger.info(f"当前窗口状态: 标题='{window_info.title}', 位置={window_info.rect}, 状态={window_info.state}")
            
            # 移动窗口并更新窗口信息
            updated_window_info = window_manager.move_window(window_info, self.window_x, self.window_y)
            if updated_window_info:
                window_info = updated_window_info
                context['current_window'] = window_info
            else:
                self.logger.warning(f"窗口移动失败，但继续执行")
            
            # 调整窗口大小并更新窗口信息
            updated_window_info = window_manager.resize_window(window_info, self.window_width, self.window_height)
            if updated_window_info:
                window_info = updated_window_info
                context['current_window'] = window_info
            else:
                self.logger.warning(f"窗口大小调整失败，但继续执行")
        
        return True
    
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
        # 支持单个模板名称或多个模板名称列表
        template_name = config.get('template_name')
        if isinstance(template_name, str):
            self.template_names = [template_name]
        else:
            self.template_names = template_name or []
        self.skip_first = config.get('skip_first', True)  # 是否跳过第一个
        self.max_clicks = config.get('max_clicks', 9)  # 最大点击数量
        self.click_delay = config.get('click_delay', 0.1)  # 点击间隔
        self.min_matches = config.get('min_matches', 10)  # 最少匹配数量

    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        mouse_controller = context.get('mouse_controller')

        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager) or not isinstance(mouse_controller, MouseController):
            return False

        # 尝试每个模板，直到找到匹配结果
        match_results = []
        for template_name in self.template_names:
            template_item = template_manager.get_template(template_name)
            if template_item:
                match_results = vision_engine.find_all_on_screen(template_item.path)
                if match_results:
                    break
        
        if not match_results:
            return False

        # 如果找到的匹配结果小于最少匹配数量，则返回False
        if len(match_results) < self.min_matches:
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
        click_y = context['current_window'].rect[3] - 12
        mouse_controller.click(center_x, click_y, clicks=120, interval=0.05)

        return True

class DelayStep(WorkflowStep):
    """延迟步骤"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.delay = config.get('delay', 1.0)
    
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        time.sleep(self.delay)
        return True

class CalculateChatBoxRectStep(WorkflowStep):
    """计算聊天框矩形区域"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.chatbox_bigadd_template = config.get('chatbox_bigadd_template')
        self.chatbox_rightbottom_template = config.get('chatbox_rightbottom_template')

    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')

        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager):
            return False

        # 获取模板
        chatbox_bigadd_template = template_manager.get_template(self.chatbox_bigadd_template)
        if not chatbox_bigadd_template:
            return False
        # 查找聊天框右下角
        chatbox_rightbottom_template = template_manager.get_template(self.chatbox_rightbottom_template)
        if not chatbox_rightbottom_template:
            return False
        
        # 查找聊天框大加号
        chatbox_bigadd_match = vision_engine.find_on_screen(chatbox_bigadd_template.path)
        if not chatbox_bigadd_match:
            return False

        # 查找聊天框右下角
        chatbox_rightbottom_match = vision_engine.find_on_screen(chatbox_rightbottom_template.path)
        if not chatbox_rightbottom_match:
            return False

        # 计算聊天框矩形区域
        chatbox_rect = (
            chatbox_bigadd_match.x + chatbox_bigadd_match.width,
            chatbox_bigadd_match.y + chatbox_bigadd_match.height,
            chatbox_rightbottom_match.x,
            chatbox_rightbottom_match.y
        )

        context['chatbox_rect'] = chatbox_rect

        # 下面是调试
        # from core.vision import MatchResult
        # rectResult = MatchResult(
        #     x=chatbox_rect[0],
        #     y=chatbox_rect[1],
        #     width=chatbox_rect[2] - chatbox_rect[0],
        #     height=chatbox_rect[3] - chatbox_rect[1],
        #     confidence=1.0
        # )

        # print(f"聊天框矩形区域: {chatbox_rect}")
        # screenshot = vision_engine.take_screenshot()
        # vision_engine.save_debug_image(screenshot, rectResult, "rectResult.png")
        
        return True

class WaitForMessageStep(WorkflowStep):
    """等待消息出现"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.message_templates = config.get('message_templates', [
            'wxwork_auto.at_wechat_message',
            'wxwork_auto.at_wechat_miniprogram', 
            'wxwork_auto.at_wechat_gongzhonghao',
        ])
        self.timeout = config.get('timeout', 10.0)

    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        mouse_controller = context.get('mouse_controller')

        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager) or not isinstance(mouse_controller, MouseController):
            return False
        
        # 获取聊天框矩形区域
        chatbox_rect = context['chatbox_rect']

        # 查找微信消息
        message_found = None
        for template_name in self.message_templates:
            template_item = template_manager.get_template(template_name)
            if template_item:
                match_result = vision_engine.wait_for_template(template_item.path, timeout=self.timeout, region=chatbox_rect)
                if match_result:
                    message_found = match_result
                    break
        
        if not message_found:
            return False
        
        context['message_found'] = message_found
        
        return True

class FindExternalButtonStep(WorkflowStep):
    """查找并点击【外部】按钮"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.template_name = config.get('template_name', 'waibu')
        self.click_delay = config.get('click_delay', 2.0)
    
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
        
        # 查找所有匹配的外部按钮
        match_results = vision_engine.find_all_on_screen(template_item.path)
        if not match_results:
            return False
        
        # 按y坐标排序，点击最上面的按钮
        match_results.sort(key=lambda x: x.y)
        topmost_button = match_results[0]
        
        # 点击外部按钮
        success = mouse_controller.click_match_result(topmost_button)
        if success:
            time.sleep(self.click_delay)
            context['last_click'] = topmost_button.center
        
        return success


class MultiSelectMessagesStep(WorkflowStep):
    """查找微信消息并设置多选"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.multiselect_template = config.get('multiselect_template')
        self.click_delay = config.get('click_delay', 1.0)
    
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        mouse_controller = context.get('mouse_controller')
        template_manager = context.get('template_manager')
        vision_engine = context.get('vision_engine')

        if not isinstance(mouse_controller, MouseController) or not isinstance(template_manager, TemplateManager) or not isinstance(vision_engine, VisionEngine):
            return False
        
        # 查找微信消息
        message_found = context['message_found']
        
        # 右键点击消息打开上下文菜单
        right_bottom_x = message_found.x + message_found.width
        right_bottom_y = message_found.y + message_found.height
        success = mouse_controller.click(right_bottom_x, right_bottom_y, button=MouseButton.RIGHT)
        if not success:
            return False
        
        time.sleep(self.click_delay)
        
        # 查找并点击多选按钮
        multiselect_template = template_manager.get_template(self.multiselect_template)
        if not multiselect_template:
            return False
        
        multiselect_match = vision_engine.find_on_screen(multiselect_template.path)
        if not multiselect_match:
            return False
        
        success = mouse_controller.click_match_result(multiselect_match)
        if success:
            time.sleep(self.click_delay)
            context['last_click'] = multiselect_match.center
        
        return success


class SelectGroupsStep(WorkflowStep):
    """选择群组并执行相关操作"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.group_template = config.get('group_template')
        self.forward_template = config.get('forward_template')
        self.click_delay = config.get('click_delay', 1.0)
    
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        mouse_controller = context.get('mouse_controller')
        
        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager) or not isinstance(mouse_controller, MouseController):
            return False
        
        # 查找群组按钮
        group_template = template_manager.get_template(self.group_template)
        if not group_template:
            return False
        
        group_matches = vision_engine.find_all_on_screen(group_template.path)
        
        # 点击所有群组按钮
        for match_result in group_matches:
            mouse_controller.click_match_result(match_result)
            time.sleep(self.click_delay)
        
        # 查找并点击逐条转发按钮
        forward_template = template_manager.get_template(self.forward_template)
        if not forward_template:
            return True  # 群组选择已完成，转发按钮可选
        
        forward_match = vision_engine.find_on_screen(forward_template.path)
        if forward_match:
            mouse_controller.click_match_result(forward_match)
            time.sleep(self.click_delay)
            context['last_click'] = forward_match.center
        
        return True


class SendMessageStep(WorkflowStep):
    """发送消息并清理聊天记录"""
    
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.send_template = config.get('send_template')
        self.menu_template = config.get('menu_template')
        self.clear_template = config.get('clear_template')
        self.location_template = config.get('location_template')
        self.confirm_template = config.get('confirm_template')
        self.final_wait = config.get('final_wait', 30.0)
    
    def execute(self, context: dict) -> bool:
        """执行步骤"""
        vision_engine = context.get('vision_engine')
        template_manager = context.get('template_manager')
        mouse_controller = context.get('mouse_controller')
        
        if not isinstance(vision_engine, VisionEngine) or not isinstance(template_manager, TemplateManager) or not isinstance(mouse_controller, MouseController):
            return False
        
        # 查找并点击发送按钮
        send_template = template_manager.get_template(self.send_template)
        if not send_template:
            return False
        
        send_match = vision_engine.find_on_screen(send_template.path)
        if not send_match:
            return False
        
        # 点击发送按钮
        success = mouse_controller.click_match_result(send_match)
        if not success:
            return False
        
        # 等待发送完成
        time.sleep(self.final_wait)
        
        # 清理聊天记录
        menu_template = template_manager.get_template(self.menu_template)
        if not menu_template:
            return False
        menu_match = vision_engine.find_on_screen(menu_template.path)
        if not menu_match:
            return False
        success = mouse_controller.click_match_result(menu_match)
        if not success:
            return False
        time.sleep(2.0) 

        # 找到聊天信息这个定位后，鼠标挪过去，并且向下滚动
        location_template = template_manager.get_template(self.location_template)
        if not location_template:
            return False
        location_match = vision_engine.find_on_screen(location_template.path)
        if not location_match:
            return False
        right_bottom_x = location_match.x + location_match.width
        right_bottom_y = location_match.y + location_match.height
        mouse_controller.move_to(right_bottom_x, right_bottom_y)
        mouse_controller.scroll_down(clicks=10, strategy='multiple')

        # 找到清空聊天记录这个定位后，鼠标挪过去，并且点击
        clear_template = template_manager.get_template(self.clear_template)
        if not clear_template:
            return False
        clear_match = vision_engine.find_on_screen(clear_template.path)
        if not clear_match:
            return False
        mouse_controller.click_match_result(clear_match)
        time.sleep(2.0)

        # 找到确认这个定位后，鼠标挪过去，并且点击
        confirm_template = template_manager.get_template(self.confirm_template)
        if not confirm_template:
            return False
        confirm_match = vision_engine.find_on_screen(confirm_template.path)
        if not confirm_match:
            return False
        mouse_controller.click_match_result(confirm_match)
        time.sleep(2.0)

        # 关闭菜单
        mouse_controller.click_match_result(menu_match)

        return True


class WxworkSemiAutoWorkflow(BaseWorkflow):
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

class WxworkAutoWorkflow(BaseWorkflow):
    """
    企业微信 肥龙自动跟单转发功能
    全自动模式
    1. 找到企业微信本体窗口，并激活它，调整窗口位置和大小
    2. 查找并点击【外部】按钮
    3. 查找微信消息并设置多选
    4. 选择群组并执行相关操作
    5. 执行群发操作的核心逻辑
    """
    
    workflow_name = "wxwork_auto"
    
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

        self.add_step(DelayStep("延迟1秒", {
            'delay': 2.0
        }))

        # 添加主要业务逻辑步骤
        # 1. 查找并点击【外部】按钮
        self.add_step(FindExternalButtonStep("查找并点击外部按钮", {
            'template_name': 'wxwork_auto.waibu',
            'click_delay': 2.0
        }))

        # 计算聊天框的矩形区域，放到上下文中
        self.add_step(CalculateChatBoxRectStep("计算聊天框矩形区域", {
            'chatbox_bigadd_template': 'wxwork_auto.chatbox_bigadd',
            'chatbox_rightbottom_template': 'wxwork_auto.chatbox_rightbottom'
        }))

        # 在聊天框的矩形区域里，等待消息出现
        self.add_step(WaitForMessageStep("等待消息出现", {
            'message_templates': [
                'wxwork_auto.at_wechat_message',
                'wxwork_auto.at_wechat_miniprogram', 
                'wxwork_auto.at_wechat_gongzhonghao',
            ],
            'timeout': 10.0
        }))

        # 2. 查找微信消息并设置多选
        self.add_step(MultiSelectMessagesStep("设置消息多选", {
            'multiselect_template': 'wxwork_auto.duoxuan',
            'click_delay': 1.0
        }))

        # 3. 选择群组并执行相关操作
        self.add_step(SelectGroupsStep("选择群组", {
            'group_template': 'wxwork_auto.group_button',
            'forward_template': 'wxwork_auto.zhutiao_zhuanfa',
            'click_delay': 1.0
        }))

        self.add_step(ClickMultiTemplateStep("点击多选框", {
            'template_name': 'wxwork_auto.multi_box',
            'skip_first': True,
            'max_clicks': 9,
            'click_delay': 0
        }))

        # 4. 执行群发操作的核心逻辑 - 使用现有的ClickSpecialTemplateStep
        self.add_step(ClickSpecialTemplateStep("特殊点击多选框序列", {
            'template_name': 'wxwork_auto.multi_box',
        }))

        # 这里的延迟，是为了等待选中动作完成，有些服务器很卡的，需要等待他们彻底完成
        self.add_step(DelayStep("延迟10秒", {
            'delay': 10.0
        }))

        self.add_step(ClickMultiTemplateStep("补点击多选框", {
            'template_name': [
                'wxwork_auto.multi_box',
                'wxwork_auto.multi_box_hover'
            ],
            'skip_first': False,
            'max_clicks': 9,
            'click_delay': 0,
            'min_matches': 0
        }))

        # 5. 发送消息并清理聊天记录
        self.add_step(SendMessageStep("发送消息完等待30s后清理", {
            'send_template': 'wxwork_auto.fasong',
            'menu_template': 'wxwork_auto.three_dot_menu',
            'clear_template': 'wxwork_auto.qingkong_liaotian_jilu',
            'location_template': 'wxwork_auto.liaotian_xinxi',
            'confirm_template': 'wxwork_auto.confirm',
            'final_wait': 30.0,
        }))