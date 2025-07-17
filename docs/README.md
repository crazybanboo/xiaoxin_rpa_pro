# Xiaoxin RPA Pro

基于Python的RPA（机器人流程自动化）软件，支持图像识别、鼠标操作、窗口管理等功能。

## 功能特性

- **图像识别**：基于OpenCV的模板匹配，支持多种匹配算法
- **鼠标操作**：完整的鼠标自动化功能（点击、拖拽、滚动等）
- **窗口管理**：基于Win32 API的窗口查找、激活、控制
- **模板管理**：多分辨率模板自动适配
- **工作流引擎**：灵活的步骤化任务执行框架
- **配置管理**：支持YAML和JSON格式配置文件

## 系统要求

- Python 3.8+
- Windows 10/11（Win32 API支持）
- 推荐分辨率：1920x1080 或 1366x768

## 安装

### 1. 克隆项目
```bash
git clone <repository-url>
cd xiaoxin_rpa_pro
```

### 2. 创建虚拟环境
```bash
python -m venv .env
.env\\Scripts\\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 创建配置文件
```bash
python -c \"from core.config import create_default_config; create_default_config('config/my_config.yaml')\"
```

### 2. 运行示例工作流
```bash
# 简单点击示例
python main.py -w simple_click

# 基础窗口操作示例
python main.py -w basic_example
```

### 3. 查看帮助
```bash
python main.py --help
```

## 项目结构

```
xiaoxin_rpa_pro/
├── config/              # 配置文件
│   └── default.yaml
├── core/                # 核心模块
│   ├── config.py        # 配置管理
│   ├── logger.py        # 日志系统
│   ├── vision.py        # 图像识别
│   ├── mouse.py         # 鼠标操作
│   ├── window.py        # 窗口管理
│   ├── template.py      # 模板管理
│   └── workflow.py      # 工作流引擎
├── docs/                # 文档
├── examples/            # 示例代码
├── logs/                # 日志文件
├── templates/           # 模板文件
├── workflows/           # 工作流定义
├── tests/               # 测试文件
├── main.py              # 主程序入口
└── requirements.txt     # 依赖清单
```

## 使用指南

### 创建自定义工作流

1. 在 `workflows/` 目录下创建新的Python文件
2. 继承 `BaseWorkflow` 类
3. 实现 `_setup()` 方法定义工作流步骤

```python
from core.workflow import BaseWorkflow, WorkflowStep
from core.mouse import MouseController

class MyWorkflow(BaseWorkflow):
    workflow_name = \"my_workflow\"
    
    def _setup(self):
        self.context['mouse_controller'] = MouseController()
        self.add_step(ClickStep(\"点击按钮\", {'x': 100, 'y': 200}))

class ClickStep(WorkflowStep):
    def execute(self, context):
        mouse = context['mouse_controller']
        return mouse.click(self.config['x'], self.config['y'])
```

### 使用图像识别

```python
from core.vision import VisionEngine

# 创建图像识别引擎
vision = VisionEngine(confidence_threshold=0.8)

# 在屏幕上查找模板
result = vision.find_on_screen(\"templates/button.png\")
if result:
    print(f\"找到模板，位置：{result.center}，置信度：{result.confidence}\")
```

### 使用鼠标操作

```python
from core.mouse import MouseController

# 创建鼠标控制器
mouse = MouseController()

# 点击
mouse.click(100, 200)

# 拖拽
mouse.drag(100, 200, 300, 400)

# 滚动
mouse.scroll(200, 300, 3, 'up')
```

### 使用窗口管理

```python
from core.window import WindowManager

# 创建窗口管理器
window_mgr = WindowManager()

# 查找窗口
window = window_mgr.find_window_by_title(\"记事本\")
if window:
    # 激活窗口
    window_mgr.activate_window(window)
    print(f\"窗口信息：{window.title}, 位置：{window.center}\")
```

## 模板管理

### 创建模板目录结构

```bash
templates/
├── my_workflow/
│   ├── 1920x1080/          # 1920x1080分辨率模板
│   │   ├── button.png
│   │   └── input.png
│   ├── 1366x768/           # 1366x768分辨率模板
│   │   ├── button.png
│   │   └── input.png
│   └── template_config.json # 模板配置
```

### 使用模板

```python
from core.template import TemplateManager

# 创建模板管理器
template_mgr = TemplateManager()

# 获取模板（自动选择合适分辨率）
template = template_mgr.get_template(\"my_workflow.button\")
if template:
    print(f\"模板路径：{template.path}\")
    print(f\"分辨率：{template.resolution}\")
```

## 配置说明

配置文件支持YAML和JSON格式，主要配置项：

```yaml
app:
  name: \"Xiaoxin RPA Pro\"
  version: \"1.0.0\"
  debug: false

logging:
  level: \"INFO\"
  file_enabled: true
  console_enabled: true

vision:
  confidence_threshold: 0.8
  match_method: \"cv2.TM_CCOEFF_NORMED\"
  grayscale: true

mouse:
  click_delay: 0.1
  move_duration: 0.5
  fail_safe: true

window:
  search_timeout: 5.0
  activate_timeout: 2.0

workflow:
  step_delay: 0.5
  error_retry: 3
  screenshot_on_error: true

templates:
  base_path: \"templates\"
  auto_resolution: true
  supported_formats: [\".png\", \".jpg\", \".jpeg\", \".bmp\"]
```

## 测试

### 运行所有测试
```bash
pytest
```

### 运行单元测试
```bash
pytest -m unit
```

### 运行集成测试
```bash
pytest -m integration
```

### 生成测试报告
```bash
pytest --cov=core --cov-report=html
```

## 常见问题

### Q: 图像识别失败怎么办？
A: 
1. 检查模板图片是否清晰
2. 调整置信度阈值
3. 确认分辨率是否匹配
4. 使用调试模式查看匹配结果

### Q: 鼠标操作不准确怎么办？
A:
1. 确认屏幕分辨率设置
2. 检查是否有多显示器
3. 调整鼠标移动速度
4. 禁用DPI缩放

### Q: 窗口查找失败怎么办？
A:
1. 确认窗口标题是否正确
2. 检查窗口是否被其他窗口遮挡
3. 增加搜索超时时间
4. 使用进程名或类名查找

### Q: 工作流执行失败怎么办？
A:
1. 检查日志文件中的错误信息
2. 使用调试模式运行
3. 确认所有依赖组件正常
4. 检查配置文件是否正确

## 开发指南

### 添加新的工作流步骤

1. 继承 `WorkflowStep` 类
2. 实现 `execute()` 方法
3. 添加配置验证（可选）

```python
class CustomStep(WorkflowStep):
    def execute(self, context):
        # 实现具体逻辑
        return True  # 返回执行结果
    
    def validate(self):
        # 验证配置（可选）
        return True
```

### 添加新的匹配算法

1. 在 `VisionEngine` 中添加新的匹配方法
2. 更新 `match_methods` 字典
3. 添加相应的测试用例

### 扩展配置系统

1. 在 `create_default_config()` 中添加新的配置项
2. 更新配置验证规则
3. 在相应模块中使用新配置

## 贡献

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目主页：<repository-url>
- 问题反馈：<issues-url>
- 文档：<docs-url>