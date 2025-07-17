这是一个空工程，我想实现一个基于python的rpa软件：
1.通过opencv来实现图片匹配定位
2.通过pyautogui来操作鼠标点击
3.通过win32api、win32gui、win32con来监控被操控的应用程序的信息
初步的构想目录结构：
config 用于存放配置信息
core 存放rpa的通用逻辑
docs 存放使用说明
examples 存放例程
logs 存放日志文件，日志前缀 '%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s'
templates 存放需要opencv识别的模板文件，需要根据不同的工作流做区分
workflows 存放不同的工作流，工作流指一种具体的rpa业务逻辑
其中同一个工作流可能对应多套templates，这是因为不同电脑屏幕分辨率不同，需要为电脑做特殊的模板适配，但是工作流业务逻辑又是一样的。

请你帮我做好任务规划，列出任务计划在first_plan.md里面

另外，python环境应使用虚拟环境 python -m venv .env