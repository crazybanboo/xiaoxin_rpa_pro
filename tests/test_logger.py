"""
测试日志模块
"""

import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from core.logger import setup_logger, get_logger, LoggerMixin, CustomFormatter


@pytest.mark.unit
class TestSetupLogger:
    """测试设置日志记录器"""
    
    def test_setup_logger_default(self):
        """测试默认参数设置日志记录器"""
        logger = setup_logger()
        
        assert logger.name == "xiaoxin_rpa"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1
    
    def test_setup_logger_with_params(self):
        """测试带参数设置日志记录器"""
        temp_dir = tempfile.mkdtemp()
        try:
            logger = setup_logger(
                name="test_logger_unique",
                level="DEBUG",
                log_dir=temp_dir,
                debug=False
            )
            
            assert logger.name == "test_logger_unique"
            assert logger.level == logging.DEBUG
            assert len(logger.handlers) >= 2  # 控制台 + 文件
            
        finally:
            # 强制关闭所有文件处理器
            for handler in logger.handlers:
                if hasattr(handler, 'close'):
                    handler.close()
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_setup_logger_debug_mode(self):
        """测试调试模式下的日志设置"""
        logger = setup_logger(debug=True)
        
        assert logger.level == logging.INFO
        # 调试模式下不应该有文件处理器（除了错误日志）
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1  # 只有错误日志文件
    
    def test_setup_logger_level_setting(self):
        """测试不同日志级别设置"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        for level in levels:
            logger = setup_logger(name=f"test_{level.lower()}", level=level, debug=True)
            assert logger.level == getattr(logging, level)
    
    def test_setup_logger_creates_log_dir(self):
        """测试日志记录器创建日志目录"""
        temp_dir = tempfile.mkdtemp()
        try:
            log_dir = Path(temp_dir) / "custom_logs"
            logger = setup_logger(name="test_dir_logger", log_dir=str(log_dir), debug=False)
            
            assert log_dir.exists()
            assert log_dir.is_dir()
            
        finally:
            # 强制关闭所有文件处理器
            for handler in logger.handlers:
                if hasattr(handler, 'close'):
                    handler.close()
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
class TestGetLogger:
    """测试获取日志记录器"""
    
    def test_get_logger_default(self):
        """测试获取默认日志记录器"""
        logger = get_logger()
        assert logger.name == "xiaoxin_rpa"
    
    def test_get_logger_with_name(self):
        """测试获取指定名称的日志记录器"""
        logger = get_logger("test_logger")
        assert logger.name == "test_logger"
    
    def test_get_logger_same_instance(self):
        """测试获取相同实例的日志记录器"""
        logger1 = get_logger("same_logger")
        logger2 = get_logger("same_logger")
        
        assert logger1 is logger2


@pytest.mark.unit
class TestLoggerMixin:
    """测试日志混入类"""
    
    def test_logger_mixin_property(self):
        """测试日志混入类的logger属性"""
        class TestClass(LoggerMixin):
            pass
        
        test_obj = TestClass()
        logger = test_obj.logger
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "xiaoxin_rpa"
    
    def test_logger_mixin_usage(self):
        """测试日志混入类的使用"""
        class TestClass(LoggerMixin):
            def test_method(self):
                self.logger.info("Test message")
                return "success"
        
        test_obj = TestClass()
        result = test_obj.test_method()
        
        assert result == "success"
        assert hasattr(test_obj, 'logger')


@pytest.mark.unit
class TestCustomFormatter:
    """测试自定义格式化器"""
    
    def test_custom_formatter_format(self):
        """测试自定义格式化器的格式化功能"""
        formatter = CustomFormatter(
            "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # 新的实现直接使用 record 中的信息
        formatted = formatter.format(record)
        
        # 验证输出格式
        assert "test" in formatted  # module_name 现在使用 record.name
        assert "file.py:123" in formatted  # caller_file 现在使用 record.pathname
        assert "Test message" in formatted
    
    def test_custom_formatter_no_caller_info(self):
        """测试自定义格式化器的路径转换功能"""
        formatter = CustomFormatter(
            "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # 新的实现总是使用 record 中的信息
        formatted = formatter.format(record)
        
        # 验证输出格式
        assert "test" in formatted  # module_name 使用 record.name
        assert "123" in formatted  # caller_line 使用 record.lineno
        assert "Test message" in formatted
    
    def test_custom_formatter_relative_path(self):
        """测试自定义格式化器的相对路径转换功能"""
        formatter = CustomFormatter(
            "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"
        )
        
        # 模拟当前工作目录下的文件
        import os
        cwd = os.getcwd()
        test_file_path = os.path.join(cwd, "tests", "test_file.py")
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=test_file_path,
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # 验证相对路径转换
        assert "tests" in formatted or "test_file.py" in formatted
        assert "123" in formatted
        assert "Test message" in formatted


@pytest.mark.unit
class TestLoggingFunctionality:
    """测试日志记录功能"""
    
    def test_logging_output(self, caplog):
        """测试日志输出"""
        logger = setup_logger("test_output", debug=True)
        
        with caplog.at_level(logging.INFO):
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
        
        assert "Test info message" in caplog.text
        assert "Test warning message" in caplog.text
        assert "Test error message" in caplog.text
    
    def test_logging_levels(self, caplog):
        """测试日志级别过滤"""
        logger = setup_logger("test_levels", level="WARNING", debug=True)
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
        
        # 只有WARNING及以上级别的消息应该被记录
        assert "Debug message" not in caplog.text
        assert "Info message" not in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
    
    def test_file_logging(self):
        """测试文件日志记录"""
        temp_dir = tempfile.mkdtemp()
        try:
            logger = setup_logger(
                name="file_test",
                log_dir=temp_dir,
                debug=False
            )
            
            logger.info("File log test message")
            logger.error("File error message")
            
            # 强制刷新文件句柄
            for handler in logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            log_dir = Path(temp_dir)
            
            # 检查是否创建了日志文件
            log_files = list(log_dir.glob("*.log"))
            assert len(log_files) >= 1
            
            # 检查错误日志文件是否存在
            error_log = log_dir / "file_test_error.log"
            assert error_log.exists()
            
        finally:
            # 强制关闭所有文件处理器
            for handler in logger.handlers:
                if hasattr(handler, 'close'):
                    handler.close()
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_logger_handler_cleanup(self):
        """测试日志处理器清理"""
        logger_name = "cleanup_test"
        
        # 第一次设置
        logger1 = setup_logger(logger_name, debug=True)
        handler_count1 = len(logger1.handlers)
        
        # 第二次设置（应该清理之前的处理器）
        logger2 = setup_logger(logger_name, debug=True)
        handler_count2 = len(logger2.handlers)
        
        # 处理器数量应该相同（因为清理了之前的处理器）
        assert handler_count1 == handler_count2
        assert logger1 is logger2  # 应该是同一个logger实例