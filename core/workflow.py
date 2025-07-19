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
            
            # 执行步骤
            for i, step in enumerate(self.steps, 1):
                # 检查是否需要停止
                if self.context.get('_stop_check_func') and self.context['_stop_check_func']():
                    self.logger.info("检测到停止信号，工作流执行中断")
                    return False
                
                self.logger.info(f"执行步骤 {i}/{len(self.steps)}: {step.name}")
                
                try:
                    success = step.execute(self.context)
                    if not success:
                        self.logger.error(f"步骤执行失败: {step.name}")
                        return False
                    
                    self.logger.info(f"步骤执行成功: {step.name}")
                    
                except Exception as e:
                    self.logger.error(f"步骤执行异常: {step.name}, 错误: {e}")
                    return False
            
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
    
    def execute(self, name: str, stop_check_func=None) -> bool:
        """
        执行工作流
        
        Args:
            name: 工作流名称
            stop_check_func: 停止检查函数
        
        Returns:
            执行结果
        """
        workflow = self.get_workflow(name)
        if not workflow:
            return False
        
        # 如果提供了停止检查函数，添加到工作流上下文
        if stop_check_func:
            workflow.set_context('_stop_check_func', stop_check_func)
        
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