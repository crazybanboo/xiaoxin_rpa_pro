"""
图像识别模块
基于OpenCV实现图片匹配定位功能
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Union
import pyautogui

from .logger import LoggerMixin


class MatchResult:
    """匹配结果类"""
    
    def __init__(self, x: int, y: int, width: int, height: int, confidence: float):
        """
        初始化匹配结果
        
        Args:
            x: 匹配位置x坐标
            y: 匹配位置y坐标
            width: 匹配区域宽度
            height: 匹配区域高度
            confidence: 匹配置信度
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
    
    @property
    def center(self) -> Tuple[int, int]:
        """获取匹配区域中心点"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def top_left(self) -> Tuple[int, int]:
        """获取匹配区域左上角坐标"""
        return (self.x, self.y)
    
    @property
    def bottom_right(self) -> Tuple[int, int]:
        """获取匹配区域右下角坐标"""
        return (self.x + self.width, self.y + self.height)
    
    def __repr__(self) -> str:
        return f"MatchResult(center={self.center}, confidence={self.confidence:.3f})"


class VisionEngine(LoggerMixin):
    """图像识别引擎"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        """
        初始化图像识别引擎
        
        Args:
            confidence_threshold: 置信度阈值
        """
        self.confidence_threshold = confidence_threshold
        
        # 支持的匹配方法
        self.match_methods = {
            'TM_CCOEFF': cv2.TM_CCOEFF,
            'TM_CCOEFF_NORMED': cv2.TM_CCOEFF_NORMED,
            'TM_CCORR': cv2.TM_CCORR,
            'TM_CCORR_NORMED': cv2.TM_CCORR_NORMED,
            'TM_SQDIFF': cv2.TM_SQDIFF,
            'TM_SQDIFF_NORMED': cv2.TM_SQDIFF_NORMED
        }
        
        self.default_method = cv2.TM_CCOEFF_NORMED
        
        self.logger.info(f"图像识别引擎初始化完成，置信度阈值: {confidence_threshold}")
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        截取屏幕图像
        
        Args:
            region: 截取区域 (x, y, width, height)
        
        Returns:
            截取的图像数组
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # 转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            return screenshot_cv
            
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            raise
    
    def load_template(self, template_path: Union[str, Path]) -> np.ndarray:
        """
        加载模板图像
        
        Args:
            template_path: 模板图像路径
        
        Returns:
            模板图像数组
        """
        template_path = Path(template_path)
        
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        # 加载图像
        template = cv2.imread(str(template_path))
        if template is None:
            raise ValueError(f"无法读取模板图像: {template_path}")
        
        self.logger.debug(f"加载模板图像: {template_path}, 尺寸: {template.shape}")
        return template
    
    def match_template(
        self, 
        screenshot: np.ndarray, 
        template: np.ndarray,
        method: str = 'TM_CCOEFF_NORMED',
        grayscale: bool = True
    ) -> Optional[MatchResult]:
        """
        执行模板匹配
        
        Args:
            screenshot: 屏幕截图
            template: 模板图像
            method: 匹配方法
            grayscale: 是否转换为灰度图
        
        Returns:
            匹配结果
        """
        try:
            # 获取匹配方法
            cv_method = self.match_methods.get(method, self.default_method)
            
            # 转换为灰度图
            if grayscale:
                screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                screenshot_gray = screenshot
                template_gray = template
            
            # 执行模板匹配
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv_method)
            
            # 获取最佳匹配位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 根据匹配方法选择结果
            if cv_method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                match_val = min_val
                top_left = min_loc
                confidence = 1.0 - min_val  # 转换为置信度
            else:
                match_val = max_val
                top_left = max_loc
                confidence = max_val
            
            # 检查置信度
            if confidence < self.confidence_threshold:
                self.logger.debug(f"匹配置信度不足: {confidence:.3f} < {self.confidence_threshold}")
                return None
            
            # 创建匹配结果
            h, w = template_gray.shape[:2]
            match_result = MatchResult(
                x=top_left[0],
                y=top_left[1],
                width=w,
                height=h,
                confidence=confidence
            )
            
            self.logger.debug(f"模板匹配成功: {match_result}")
            return match_result
            
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return None
    
    def find_all_matches(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        method: str = 'TM_CCOEFF_NORMED',
        grayscale: bool = True,
        threshold: Optional[float] = None
    ) -> List[MatchResult]:
        """
        查找所有匹配项
        
        Args:
            screenshot: 屏幕截图
            template: 模板图像
            method: 匹配方法
            grayscale: 是否转换为灰度图
            threshold: 置信度阈值
        
        Returns:
            匹配结果列表
        """
        if threshold is None:
            threshold = self.confidence_threshold
        
        try:
            # 获取匹配方法
            cv_method = self.match_methods.get(method, self.default_method)
            
            # 转换为灰度图
            if grayscale:
                screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                screenshot_gray = screenshot
                template_gray = template
            
            # 执行模板匹配
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv_method)
            
            h, w = template_gray.shape[:2]
            matches = []
            
            # 根据匹配方法处理结果
            if cv_method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                # 对于SQDIFF方法，值越小越好
                locations = np.where(result <= (1.0 - threshold))
                for pt in zip(*locations[::-1]):
                    confidence = 1.0 - result[pt[1], pt[0]]
                    matches.append(MatchResult(pt[0], pt[1], w, h, confidence))
            else:
                # 对于其他方法，值越大越好
                locations = np.where(result >= threshold)
                for pt in zip(*locations[::-1]):
                    confidence = result[pt[1], pt[0]]
                    matches.append(MatchResult(pt[0], pt[1], w, h, confidence))
            
            # 按置信度排序
            matches.sort(key=lambda x: x.confidence, reverse=True)
            
            self.logger.debug(f"找到 {len(matches)} 个匹配项")
            return matches
            
        except Exception as e:
            self.logger.error(f"查找所有匹配项失败: {e}")
            return []
    
    def find_on_screen(
        self,
        template_path: Union[str, Path],
        region: Optional[Tuple[int, int, int, int]] = None,
        method: str = 'TM_CCOEFF_NORMED',
        grayscale: bool = True
    ) -> Optional[MatchResult]:
        """
        在屏幕上查找模板
        
        Args:
            template_path: 模板图像路径
            region: 搜索区域
            method: 匹配方法
            grayscale: 是否转换为灰度图
        
        Returns:
            匹配结果
        """
        try:
            # 加载模板
            template = self.load_template(template_path)
            
            # 截取屏幕
            screenshot = self.take_screenshot(region)
            
            # 执行匹配
            result = self.match_template(screenshot, template, method, grayscale)
            
            # 如果指定了区域，需要调整坐标
            if result and region:
                result.x += region[0]
                result.y += region[1]
            
            return result
            
        except Exception as e:
            self.logger.error(f"屏幕查找失败: {e}")
            return None
    
    def wait_for_template(
        self,
        template_path: Union[str, Path],
        timeout: float = 10.0,
        interval: float = 0.5,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[MatchResult]:
        """
        等待模板出现
        
        Args:
            template_path: 模板图像路径
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
            region: 搜索区域
        
        Returns:
            匹配结果
        """
        import time
        
        start_time = time.time()
        self.logger.info(f"等待模板出现: {template_path}, 超时: {timeout}秒")
        
        while time.time() - start_time < timeout:
            result = self.find_on_screen(template_path, region)
            if result:
                self.logger.info(f"模板找到: {result}")
                return result
            
            time.sleep(interval)
        
        self.logger.warning(f"等待模板超时: {template_path}")
        return None
    
    def save_debug_image(
        self,
        screenshot: np.ndarray,
        match_result: MatchResult,
        save_path: Union[str, Path]
    ) -> None:
        """
        保存调试图像
        
        Args:
            screenshot: 屏幕截图
            match_result: 匹配结果
            save_path: 保存路径
        """
        try:
            # 在截图上绘制匹配框
            debug_image = screenshot.copy()
            cv2.rectangle(
                debug_image,
                match_result.top_left,
                match_result.bottom_right,
                (0, 255, 0),
                2
            )
            
            # 添加置信度文本
            cv2.putText(
                debug_image,
                f"Confidence: {match_result.confidence:.3f}",
                (match_result.x, match_result.y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )
            
            # 保存图像
            cv2.imwrite(str(save_path), debug_image)
            self.logger.debug(f"调试图像已保存: {save_path}")
            
        except Exception as e:
            self.logger.error(f"保存调试图像失败: {e}")


def create_vision_engine(config: dict) -> VisionEngine:
    """
    创建图像识别引擎
    
    Args:
        config: 配置字典
    
    Returns:
        图像识别引擎实例
    """
    confidence_threshold = config.get('confidence_threshold', 0.8)
    return VisionEngine(confidence_threshold)