"""
工作流管理模块
提供工作流的定义、执行和管理功能
"""

import importlib
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .config import Config
from .logger import LoggerMixin


class WorkflowStep(LoggerMixin, ABC):
    """工作流步骤基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化工作流步骤
        
        Args:
            name: 步骤名称
            config: 步骤配置
        """
        super().__init__()
        self.name = name
        self.config = config
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> bool:
        """
        执行步骤
        
        Args:
            context: 执行上下文
        
        Returns:
            执行结果
        """
        pass
    
    def validate(self) -> bool:
        """
        验证步骤配置
        
        Returns:
            验证结果
        """
        return True


class LoopStartStep(WorkflowStep):
    """循环开始标记步骤"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.loop_id = config.get('loop_id', 'default')
    
    def execute(self, context: Dict[str, Any]) -> bool:
        """标记循环开始位置"""
        loop_info = context.setdefault('_loop_info', {})
        loop_info[self.loop_id] = {
            'start_step': context.get('_current_step_index', 0),
            'iteration': loop_info.get(self.loop_id, {}).get('iteration', 0) + 1
        }
        self.logger.info(f"循环 {self.loop_id} 开始，第 {loop_info[self.loop_id]['iteration']} 次迭代")
        return True


class LoopEndStep(WorkflowStep):
    """循环结束步骤"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.loop_id = config.get('loop_id', 'default')
        self.max_iterations = config.get('max_iterations', 1000)
    
    def execute(self, context: Dict[str, Any]) -> bool:
        """无条件回到循环开始"""
        loop_info = context.get('_loop_info', {})
        if self.loop_id not in loop_info:
            self.logger.error(f"找不到循环 {self.loop_id} 的开始标记")
            return False
        
        current_iteration = loop_info[self.loop_id]['iteration']
        if self.max_iterations != 0:
            if current_iteration >= self.max_iterations:
                self.logger.warning(f"循环 {self.loop_id} 达到最大迭代次数 {self.max_iterations}")
                return True
        
        # 设置跳转标记
        start_step = loop_info[self.loop_id]['start_step']
        context['_jump_to_step'] = start_step
        self.logger.info(f"循环 {self.loop_id} 第 {current_iteration} 次迭代完成，跳转到步骤 {start_step}")
        return True


class ConditionalJumpStep(WorkflowStep):
    """条件跳转步骤"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.condition_key = config.get('condition_key')  # 检查上下文中的键
        self.condition_value = config.get('condition_value')  # 期望的值
        self.condition_type = config.get('condition_type', 'equals')  # equals, not_equals, exists, not_exists
        self.jump_to_loop = config.get('jump_to_loop')  # 跳转到哪个循环
        self.on_failure = config.get('on_failure', 'continue')  # 失败时的行为: continue, jump, stop
    
    def execute(self, context: Dict[str, Any]) -> bool:
        """根据条件决定是否跳转"""
        should_jump = False
        
        if not self.condition_key:
            self.logger.error(f"条件跳转步骤 {self.name} 缺少条件键")
            return False

        if self.condition_type == 'exists':
            should_jump = self.condition_key in context
        elif self.condition_type == 'not_exists':
            should_jump = self.condition_key not in context
        elif self.condition_type == 'equals':
            should_jump = context.get(self.condition_key) == self.condition_value
        elif self.condition_type == 'not_equals':
            should_jump = context.get(self.condition_key) != self.condition_value
        
        if should_jump and self.jump_to_loop:
            loop_info = context.get('_loop_info', {})
            if self.jump_to_loop in loop_info:
                start_step = loop_info[self.jump_to_loop]['start_step']
                context['_jump_to_step'] = start_step
                self.logger.info(f"条件满足，跳转到循环 {self.jump_to_loop} (步骤 {start_step})")
                return True
            else:
                self.logger.error(f"找不到循环 {self.jump_to_loop}")
                return self.on_failure != 'stop'
        
        return True


class BaseWorkflow(LoggerMixin, ABC):
    """工作流基类"""
    
    def __init__(self, name: str, config: Config):
        """
        初始化工作流
        
        Args:
            name: 工作流名称
            config: 全局配置
        """
        self.name = name
        self.config = config
        self.steps: List[WorkflowStep] = []
        self.context: Dict[str, Any] = {}
        self._setup()
    
    @abstractmethod
    def _setup(self) -> None:
        """设置工作流步骤"""
        pass
    
    def add_step(self, step: WorkflowStep) -> None:
        """
        添加工作流步骤
        
        Args:
            step: 工作流步骤
        """
        self.steps.append(step)
    
    def execute(self) -> bool:
        """
        执行工作流
        
        Returns:
            执行结果
        """
        self.logger.info(f"开始执行工作流: {self.name}")
        
        try:
            # 验证所有步骤
            for step in self.steps:
                if not step.validate():
                    self.logger.error(f"步骤验证失败: {step.name}")
                    return False
            
            # 执行步骤（支持跳转）
            i = 0
            while i < len(self.steps):
                step = self.steps[i]
                
                # 设置当前步骤索引到上下文，供LoopStartStep使用
                self.context['_current_step_index'] = i
                
                # 检查是否需要停止
                if self.context.get('_stop_check_func') and self.context['_stop_check_func']():
                    self.logger.info("检测到停止信号，工作流执行中断")
                    return False
                
                self.logger.info(f"执行步骤 {i+1}/{len(self.steps)}: {step.name}")
                
                try:
                    success = step.execute(self.context)
                    if not success:
                        self.logger.error(f"步骤执行失败: {step.name}")
                        return False
                    
                    self.logger.info(f"步骤执行成功: {step.name}")
                    
                    # 检查是否需要跳转
                    if '_jump_to_step' in self.context:
                        jump_to = self.context.pop('_jump_to_step')
                        if 0 <= jump_to < len(self.steps):
                            i = jump_to
                            self.logger.info(f"跳转到步骤 {i+1}")
                            continue
                        else:
                            self.logger.error(f"无效的跳转目标: {jump_to}")
                            return False
                    
                except Exception as e:
                    self.logger.error(f"步骤执行异常: {step.name}, 错误: {e}")
                    return False
                
                i += 1
            
            self.logger.info(f"工作流执行完成: {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"工作流执行异常: {self.name}, 错误: {e}")
            return False
    
    def get_context(self) -> Dict[str, Any]:
        """获取执行上下文"""
        return self.context.copy()
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文变量"""
        self.context[key] = value


class WorkflowManager(LoggerMixin):
    """工作流管理器"""
    
    def __init__(self, config: Config):
        """
        初始化工作流管理器
        
        Args:
            config: 全局配置
        """
        self.config = config
        self.workflows: Dict[str, Type[BaseWorkflow]] = {}
        self._load_workflows()
    
    def _load_workflows(self) -> None:
        """加载工作流"""
        workflows_dir = Path("workflows")
        if not workflows_dir.exists():
            self.logger.warning("工作流目录不存在: workflows")
            return
        
        # 添加workflows目录到Python路径
        sys.path.insert(0, str(workflows_dir.parent))
        
        # 搜索工作流文件
        for workflow_file in workflows_dir.glob("*.py"):
            if workflow_file.name.startswith("__"):
                continue
            
            try:
                module_name = f"workflows.{workflow_file.stem}"
                module = importlib.import_module(module_name)
                
                # 查找工作流类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseWorkflow) and 
                        attr != BaseWorkflow):
                        
                        workflow_name = getattr(attr, 'workflow_name', workflow_file.stem)
                        self.workflows[workflow_name] = attr
                        self.logger.info(f"加载工作流: {workflow_name}")
                
            except Exception as e:
                self.logger.error(f"加载工作流失败: {workflow_file}, 错误: {e}")
    
    def get_workflow(self, name: str) -> Optional[BaseWorkflow]:
        """
        获取工作流实例
        
        Args:
            name: 工作流名称
        
        Returns:
            工作流实例
        """
        if name not in self.workflows:
            self.logger.error(f"工作流不存在: {name}")
            return None
        
        try:
            return self.workflows[name](name, self.config)
        except Exception as e:
            self.logger.error(f"创建工作流实例失败: {name}, 错误: {e}")
            return None
    
    def execute(self, name: str, stop_event=None) -> bool:
        """
        执行工作流
        
        Args:
            name: 工作流名称
            stop_event: 停止事件 (threading.Event)
        
        Returns:
            执行结果
        """
        workflow = self.get_workflow(name)
        if not workflow:
            return False
        
        # 如果提供了停止事件，添加到工作流上下文
        if stop_event:
            workflow.set_context('_stop_event', stop_event)
            workflow.set_context('_stop_check_func', lambda: stop_event.is_set())
        
        return workflow.execute()
    
    def list_workflows(self) -> List[str]:
        """获取所有工作流名称"""
        return list(self.workflows.keys())
    
    def register_workflow(self, name: str, workflow_class: Type[BaseWorkflow]) -> None:
        """
        注册工作流
        
        Args:
            name: 工作流名称
            workflow_class: 工作流类
        """
        self.workflows[name] = workflow_class
        self.logger.info(f"注册工作流: {name}")


class WorkflowContext:
    """工作流上下文管理器"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.screenshots: List[str] = []
        self.errors: List[str] = []
    
    def set(self, key: str, value: Any) -> None:
        """设置上下文变量"""
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文变量"""
        return self.data.get(key, default)
    
    def add_screenshot(self, path: str) -> None:
        """添加截图路径"""
        self.screenshots.append(path)
    
    def add_error(self, error: str) -> None:
        """添加错误信息"""
        self.errors.append(error)
    
    def clear(self) -> None:
        """清空上下文"""
        self.data.clear()
        self.screenshots.clear()
        self.errors.clear()