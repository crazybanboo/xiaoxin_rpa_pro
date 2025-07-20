# API 文档

## 核心模块 API

### 配置管理 (core.config)

#### Config 类

配置管理类，支持YAML和JSON格式配置文件。

```python
from core.config import Config

config = Config('config/default.yaml')
```

**方法：**

- `get(key, default=None)` - 获取配置值，支持嵌套键（如 'app.name'）
- `set(key, value)` - 设置配置值
- `save()` - 保存配置到文件
- `validate(schema)` - 验证配置结构
- `get_all()` - 获取所有配置

**示例：**

```python
# 获取配置
app_name = config.get('app.name')
db_host = config.get('database.host', 'localhost')

# 设置配置
config.set('app.debug', True)
config.set('new.section.key', 'value')

# 保存配置
config.save()
```

#### create_default_config 函数

创建默认配置文件。

```python
from core.config import create_default_config

create_default_config('config/default.yaml')
```

### 日志系统 (core.logger)

#### setup_logger 函数

设置日志记录器。

```python
from core.logger import setup_logger

logger = setup_logger(
    name='my_app',
    level='INFO',
    log_dir='logs',
    debug=False
)
```

**参数：**

- `name` - 日志记录器名称
- `level` - 日志级别（DEBUG, INFO, WARNING, ERROR）
- `log_dir` - 日志文件目录
- `debug` - 是否调试模式

#### get_logger 函数

获取日志记录器。

```python
from core.logger import get_logger

logger = get_logger('my_app')
logger.info('This is a log message')
```

#### LoggerMixin 类

日志混入类，为类提供日志功能。

```python
from core.logger import LoggerMixin

class MyClass(LoggerMixin):
    def my_method(self):
        self.logger.info('Method called')
```

### 图像识别 (core.vision)

#### VisionEngine 类

图像识别引擎，基于OpenCV实现。

```python
from core.vision import VisionEngine

engine = VisionEngine(confidence_threshold=0.8)
```

**方法：**

- `take_screenshot(region=None)` - 截取屏幕
- `load_template(template_path)` - 加载模板图像
- `match_template(screenshot, template, method='TM_CCOEFF_NORMED')` - 模板匹配
- `find_on_screen(template_path, region=None)` - 在屏幕上查找模板
- `wait_for_template(template_path, timeout=10.0)` - 等待模板出现
- `find_all_matches(screenshot, template)` - 查找所有匹配项

**示例：**

```python
# 在屏幕上查找模板
result = engine.find_on_screen('templates/button.png')
if result:
    print(f'找到模板，位置：{result.center}')
    
# 等待模板出现
result = engine.wait_for_template('templates/dialog.png', timeout=5.0)
```

#### MatchResult 类

匹配结果类。

**属性：**

- `x, y` - 匹配位置坐标
- `width, height` - 匹配区域尺寸
- `confidence` - 匹配置信度
- `center` - 匹配区域中心点
- `top_left` - 左上角坐标
- `bottom_right` - 右下角坐标

### 鼠标操作 (core.mouse)

#### MouseController 类

鼠标控制器，基于PyAutoGUI实现。

```python
from core.mouse import MouseController

mouse = MouseController(
    click_delay=0.1,
    move_duration=0.5,
    fail_safe=True
)
```

**方法：**

- `get_position()` - 获取鼠标位置
- `move_to(x, y, duration=None)` - 移动鼠标
- `click(x=None, y=None, button=MouseButton.LEFT, clicks=1)` - 点击
- `double_click(x=None, y=None)` - 双击
- `right_click(x=None, y=None)` - 右键点击
- `drag(from_x, from_y, to_x, to_y, duration=None)` - 拖拽
- `scroll(x, y, clicks, direction='up')` - 滚动
- `click_match_result(match_result)` - 点击匹配结果

**示例：**

```python
# 基本点击
mouse.click(100, 200)

# 拖拽操作
mouse.drag(100, 200, 300, 400)

# 滚动
mouse.scroll(200, 300, 3, 'up')

# 点击匹配结果
result = vision_engine.find_on_screen('button.png')
if result:
    mouse.click_match_result(result)
```

#### MouseButton 枚举

鼠标按键枚举。

- `MouseButton.LEFT` - 左键
- `MouseButton.RIGHT` - 右键
- `MouseButton.MIDDLE` - 中键

### 窗口管理 (core.window)

#### WindowManager 类

窗口管理器，基于Win32 API实现。

```python
from core.window import WindowManager

window_mgr = WindowManager(
    search_timeout=5.0,
    activate_timeout=2.0
)
```

**方法：**

- `get_all_windows()` - 获取所有窗口
- `find_window_by_title(title, exact_match=False)` - 根据标题查找窗口
- `find_window_by_class(class_name)` - 根据类名查找窗口
- `find_window_by_process(process_name)` - 根据进程名查找窗口
- `wait_for_window(title=None, class_name=None, process_name=None)` - 等待窗口出现
- `activate_window(window_info)` - 激活窗口
- `close_window(window_info)` - 关闭窗口
- `minimize_window(window_info)` - 最小化窗口
- `maximize_window(window_info)` - 最大化窗口

**示例：**

```python
# 查找窗口
window = window_mgr.find_window_by_title('记事本')
if window:
    # 激活窗口
    window_mgr.activate_window(window)
    print(f'窗口位置：{window.center}')

# 等待窗口出现
window = window_mgr.wait_for_window(title='对话框', timeout=10.0)
```

#### WindowInfo 类

窗口信息类。

**属性：**

- `hwnd` - 窗口句柄
- `title` - 窗口标题
- `class_name` - 窗口类名
- `pid` - 进程ID
- `process_name` - 进程名
- `rect` - 窗口矩形区域
- `state` - 窗口状态
- `visible` - 是否可见
- `enabled` - 是否启用
- `width, height` - 窗口尺寸
- `center` - 窗口中心点

### 模板管理 (core.template)

#### TemplateManager 类

模板管理器，支持多分辨率模板。

```python
from core.template import TemplateManager

template_mgr = TemplateManager(templates_dir='templates')
```

**方法：**

- `get_template(template_name, resolution=None)` - 获取模板
- `list_templates(workflow_name=None)` - 列出模板
- `list_resolutions(template_name)` - 列出模板支持的分辨率
- `create_template_structure(workflow_name, template_names)` - 创建模板目录结构
- `validate_template(template_item)` - 验证模板
- `get_template_info(template_name)` - 获取模板信息

**示例：**

```python
# 获取模板（自动选择分辨率）
template = template_mgr.get_template('my_workflow.button')
if template:
    print(f'模板路径：{template.path}')
    print(f'分辨率：{template.resolution}')

# 创建模板目录结构
template_mgr.create_template_structure('new_workflow', ['button', 'input', 'dialog'])
```

#### TemplateItem 类

模板项类。

**属性：**

- `path` - 模板文件路径
- `resolution` - 分辨率
- `config` - 模板配置

### 工作流引擎 (core.workflow)

#### BaseWorkflow 类

工作流基类。

```python
from core.workflow import BaseWorkflow

class MyWorkflow(BaseWorkflow):
    workflow_name = 'my_workflow'
    
    def _setup(self):
        # 初始化和添加步骤
        self.add_step(MyStep('步骤1', {}))
```

**方法：**

- `add_step(step)` - 添加步骤
- `execute()` - 执行工作流
- `get_context()` - 获取执行上下文
- `set_context(key, value)` - 设置上下文变量

#### WorkflowStep 类

工作流步骤基类。

```python
from core.workflow import WorkflowStep

class MyStep(WorkflowStep):
    def execute(self, context):
        # 实现步骤逻辑
        return True  # 返回执行结果
    
    def validate(self):
        # 验证步骤配置
        return True
```

#### WorkflowManager 类

工作流管理器。

```python
from core.workflow import WorkflowManager

workflow_mgr = WorkflowManager(config)
```

**方法：**

- `get_workflow(name)` - 获取工作流实例
- `execute(name)` - 执行工作流
- `list_workflows()` - 列出所有工作流
- `register_workflow(name, workflow_class)` - 注册工作流

**示例：**

```python
# 执行工作流
success = workflow_mgr.execute('my_workflow')

# 注册自定义工作流
workflow_mgr.register_workflow('custom', CustomWorkflow)
```

## 工厂函数

### create_vision_engine(config)

创建图像识别引擎。

```python
from core.vision import create_vision_engine

engine = create_vision_engine({
    'confidence_threshold': 0.9
})
```

### create_mouse_controller(config)

创建鼠标控制器。

```python
from core.mouse import create_mouse_controller

mouse = create_mouse_controller({
    'click_delay': 0.1,
    'move_duration': 0.5,
    'fail_safe': True
})
```

### create_window_manager(config)

创建窗口管理器。

```python
from core.window import create_window_manager

window_mgr = create_window_manager({
    'search_timeout': 5.0,
    'activate_timeout': 2.0
})
```

### create_template_manager(config)

创建模板管理器。

```python
from core.template import create_template_manager

template_mgr = create_template_manager({
    'base_path': 'templates'
})
```

## 异常处理

### 常见异常

- `FileNotFoundError` - 文件不存在
- `ValueError` - 参数值错误
- `Exception` - 一般异常

### 异常处理示例

```python
from core.vision import VisionEngine

try:
    engine = VisionEngine()
    result = engine.find_on_screen('template.png')
    if result:
        print(f'找到模板：{result.center}')
    else:
        print('未找到模板')
except FileNotFoundError:
    print('模板文件不存在')
except Exception as e:
    print(f'发生错误：{e}')
```

## 配置参数

### 完整配置示例

```yaml
app:
  name: \"Xiaoxin RPA Pro\"
  version: \"1.0.2\"
  debug: false

logging:
  level: \"INFO\"                    # 日志级别
  file_enabled: true                # 是否启用文件日志
  console_enabled: true             # 是否启用控制台日志

vision:
  confidence_threshold: 0.8         # 置信度阈值
  match_method: \"TM_CCOEFF_NORMED\" # 匹配方法
  grayscale: true                   # 是否转换为灰度图

mouse:
  click_delay: 0.1                  # 点击延迟
  move_duration: 0.5                # 移动持续时间
  fail_safe: true                   # 失败保护

window:
  search_timeout: 5.0               # 搜索超时时间
  activate_timeout: 2.0             # 激活超时时间

workflow:
  step_delay: 0.5                   # 步骤延迟
  error_retry: 3                    # 错误重试次数
  screenshot_on_error: true         # 错误时截图

templates:
  base_path: \"templates\"           # 模板基础路径
  auto_resolution: true             # 自动分辨率选择
  supported_formats: [\".png\", \".jpg\", \".jpeg\", \".bmp\"]
```

## 最佳实践

### 1. 错误处理

```python
def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f'执行失败：{e}')
        return None
```

### 2. 配置管理

```python
class ConfigurableComponent:
    def __init__(self, config):
        self.config = config
        self.timeout = config.get('timeout', 5.0)
        self.retry_count = config.get('retry_count', 3)
```

### 3. 日志记录

```python
from core.logger import LoggerMixin

class MyClass(LoggerMixin):
    def process(self):
        self.logger.info('开始处理')
        try:
            # 处理逻辑
            self.logger.info('处理完成')
        except Exception as e:
            self.logger.error(f'处理失败：{e}')
```

### 4. 资源管理

```python
with patch('pyautogui.FAILSAFE', False):
    # 在禁用失败保护的情况下执行操作
    mouse.click(x, y)
```