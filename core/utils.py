"""
实用工具模块
提供各种辅助功能
"""

import time
import shutil
import psutil
import logging
import argparse
import threading
from .logger import get_logger
from pathlib import Path
from typing import Optional, Callable, List, Dict, Tuple


def interruptible_sleep(duration: float, stop_check_func: Optional[Callable[[], bool]] = None, check_interval: float = 0.1) -> bool:
    """
    可中断的睡眠函数
    
    Args:
        duration: 睡眠时长（秒）
        stop_check_func: 停止检查函数，返回True表示应该中断
        check_interval: 检查间隔（秒），默认0.1秒
    
    Returns:
        True: 正常完成睡眠
        False: 被中断
    """
    if duration <= 0:
        return True
    
    if stop_check_func is None:
        time.sleep(duration)
        return True
    
    # 如果持续时间很短，直接使用time.sleep
    if duration <= check_interval:
        if stop_check_func():
            return False
        time.sleep(duration)
        return not stop_check_func()
    
    # 对于长时间的睡眠，分段检查
    elapsed = 0.0
    while elapsed < duration:
        if stop_check_func():
            return False
        
        # 计算本次睡眠时间
        remaining = duration - elapsed
        sleep_time = min(check_interval, remaining)
        
        time.sleep(sleep_time)
        elapsed += sleep_time
    
    return True


def interruptible_sleep_event(duration: float, stop_event: Optional[threading.Event] = None) -> bool:
    """
    基于Event的可中断睡眠函数
    
    Args:
        duration: 睡眠时长（秒）
        stop_event: 停止事件，当事件被设置时中断睡眠
    
    Returns:
        True: 正常完成睡眠
        False: 被中断
    """
    if duration <= 0:
        return True
    
    if stop_event is None:
        time.sleep(duration)
        return True
    
    # 使用Event.wait()方法，支持超时和中断
    return not stop_event.wait(timeout=duration)

"""
企业微信缓存清理工具
安全删除企业微信缓存文件以节省磁盘空间
支持在企业微信运行时进行清理
"""

class WXWorkCacheCleaner:
    def __init__(self, wxwork_path: Optional[str] = None):
        # 默认企业微信缓存路径
        if wxwork_path is None:
            self.wxwork_path = Path.home() / "Documents" / "WXWork"
        else:
            self.wxwork_path = Path(wxwork_path)
        
        # 使用项目统一的日志
        self.logger = get_logger()
        
        # 可安全删除的文件/目录模式
        self.safe_patterns = {
            'avatar_cache': {
                'paths': ['*/Avator/*'],
                'extensions': ['.jpg', '.png', '.gif', '.webp'],
                'description': '头像缓存文件'
            },
            'avatar_db': {
                'paths': ['*/Avator/*.db'],
                'extensions': [],
                'description': '头像数据库缓存'
            },
            'general_cache': {
                'paths': ['*/Cache', '*/WXWorkCefCache', 'Default/Cache', 'qtCef/Cache'],
                'extensions': [],
                'description': '通用缓存目录'
            },
            'gpu_cache': {
                'paths': ['qtCef/GPUCache', 'qtCef/DawnCache', 'qtCef/DawnGraphiteCache', 'qtCef/DawnWebGPUCache'],
                'extensions': [],
                'description': 'GPU渲染缓存'
            },
            'shader_cache': {
                'paths': ['GrShaderCache', 'GraphiteDawnCache', 'ShaderCache'],
                'extensions': [],
                'description': '着色器缓存'
            },
            'temp_files': {
                'paths': ['**/*.tmp', '**/*.log'],
                'extensions': [],
                'description': '临时文件和日志'
            },
            'component_cache': {
                'paths': ['component_crx_cache'],
                'extensions': [],
                'description': '组件缓存'
            }
        }
    
    def is_wxwork_running(self) -> bool:
        """检查企业微信是否正在运行"""
        wxwork_processes = ['WXWork.exe', 'WXWorkApp.exe']
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] in wxwork_processes:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def get_file_size_mb(self, path: Path) -> float:
        """获取文件或目录大小（MB）"""
        if path.is_file():
            return path.stat().st_size / (1024 * 1024)
        elif path.is_dir():
            total_size = 0
            try:
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            except (PermissionError, OSError):
                pass
            return total_size / (1024 * 1024)
        return 0
    
    def safe_delete(self, path: Path) -> bool:
        """安全删除文件或目录，支持运行时删除"""
        try:
            if path.is_file():
                # 对于文件，尝试重命名后删除（绕过文件锁定）
                temp_path = path.with_suffix(path.suffix + '.del')
                try:
                    path.rename(temp_path)
                    temp_path.unlink()
                    return True
                except OSError:
                    # 如果重命名失败，尝试直接删除
                    path.unlink()
                    return True
            elif path.is_dir():
                # 对于目录，递归删除
                shutil.rmtree(path, ignore_errors=True)
                return True
        except (OSError, PermissionError) as e:
            self.logger.warning(f"无法删除 {path}: {e}")
            return False
        return False
    
    def find_cache_files(self, pattern_type: str) -> List[Path]:
        """根据模式类型查找缓存文件"""
        pattern_info = self.safe_patterns.get(pattern_type)
        if not pattern_info:
            return []
        
        found_files = []
        for pattern in pattern_info['paths']:
            try:
                for path in self.wxwork_path.glob(pattern):
                    if path.exists():
                        # 检查文件扩展名（如果指定）
                        if pattern_info['extensions']:
                            if path.is_file() and path.suffix.lower() in pattern_info['extensions']:
                                found_files.append(path)
                            elif path.is_dir():
                                for ext in pattern_info['extensions']:
                                    found_files.extend(path.glob(f'*{ext}'))
                        else:
                            found_files.append(path)
            except (OSError, PermissionError) as e:
                self.logger.warning(f"访问路径时出错 {pattern}: {e}")
        
        return found_files
    
    def analyze_cache(self) -> Dict[str, Dict]:
        """分析缓存文件占用情况"""
        analysis = {}
        total_size = 0
        total_files = 0
        
        for pattern_type, pattern_info in self.safe_patterns.items():
            files = self.find_cache_files(pattern_type)
            size = sum(self.get_file_size_mb(f) for f in files)
            
            analysis[pattern_type] = {
                'description': pattern_info['description'],
                'files': files,
                'count': len(files),
                'size_mb': size
            }
            
            total_size += size
            total_files += len(files)
        
        analysis['total'] = {
            'size_mb': total_size,
            'files': total_files
        }
        
        return analysis
    
    def clean_cache(self, patterns: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Dict]:
        """清理缓存文件"""
        if patterns is None:
            patterns = list(self.safe_patterns.keys())
        
        results = {}
        total_cleaned_size = 0
        total_cleaned_files = 0
        
        # 检查企业微信运行状态
        is_running = self.is_wxwork_running()
        if is_running:
            self.logger.info("检测到企业微信正在运行，将尝试安全删除...")
        
        for pattern_type in patterns:
            if pattern_type not in self.safe_patterns:
                continue
            
            files = self.find_cache_files(pattern_type)
            cleaned_size = 0
            cleaned_count = 0
            failed_files = []
            
            self.logger.info(f"开始清理: {self.safe_patterns[pattern_type]['description']}")
            
            for file_path in files:
                size_mb = self.get_file_size_mb(file_path)
                
                if dry_run:
                    self.logger.info(f"[预览] 将删除: {file_path} ({size_mb:.2f} MB)")
                    cleaned_size += size_mb
                    cleaned_count += 1
                else:
                    if self.safe_delete(file_path):
                        self.logger.info(f"已删除: {file_path} ({size_mb:.2f} MB)")
                        cleaned_size += size_mb
                        cleaned_count += 1
                    else:
                        failed_files.append(str(file_path))
            
            results[pattern_type] = {
                'description': self.safe_patterns[pattern_type]['description'],
                'cleaned_count': cleaned_count,
                'cleaned_size_mb': cleaned_size,
                'failed_files': failed_files
            }
            
            total_cleaned_size += cleaned_size
            total_cleaned_files += cleaned_count
        
        results['summary'] = {
            'total_cleaned_size_mb': total_cleaned_size,
            'total_cleaned_files': total_cleaned_files,
            'wxwork_running': is_running
        }
        
        return results
    
    def print_analysis(self, analysis: Dict):
        """打印分析结果"""
        self.logger.info("\n" + "="*60)
        self.logger.info("企业微信缓存分析报告")
        self.logger.info("="*60)
        
        for pattern_type, info in analysis.items():
            if pattern_type == 'total':
                continue
            self.logger.info(f"\n{info['description']}:")
            self.logger.info(f"  文件数量: {info['count']}")
            self.logger.info(f"  占用空间: {info['size_mb']:.2f} MB")
        
        self.logger.info(f"\n总计:")
        self.logger.info(f"  文件数量: {analysis['total']['files']}")
        self.logger.info(f"  占用空间: {analysis['total']['size_mb']:.2f} MB")
        self.logger.info("="*60)
    
    def print_results(self, results: Dict):
        """打印清理结果"""
        self.logger.info("\n" + "="*60)
        self.logger.info("缓存清理结果")
        self.logger.info("="*60)
        
        for pattern_type, info in results.items():
            if pattern_type == 'summary':
                continue
            
            self.logger.info(f"\n{info['description']}:")
            self.logger.info(f"  清理文件: {info['cleaned_count']}")
            self.logger.info(f"  释放空间: {info['cleaned_size_mb']:.2f} MB")
            
            if info['failed_files']:
                self.logger.info(f"  失败文件: {len(info['failed_files'])}")
        
        summary = results['summary']
        self.logger.info(f"\n总结:")
        self.logger.info(f"  总清理文件: {summary['total_cleaned_files']}")
        self.logger.info(f"  总释放空间: {summary['total_cleaned_size_mb']:.2f} MB")
        self.logger.info(f"  企业微信运行状态: {'运行中' if summary['wxwork_running'] else '未运行'}")
        self.logger.info("="*60)

def wxwork_cache_cleaner_main():
    parser = argparse.ArgumentParser(description='企业微信缓存清理工具')
    parser.add_argument('--path', type=str, help='企业微信缓存目录路径')
    parser.add_argument('--analyze', action='store_true', help='仅分析缓存占用情况')
    parser.add_argument('--clean', nargs='*', help='清理指定类型缓存 (avatar_cache, general_cache, etc.)')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际删除文件')
    parser.add_argument('--force', action='store_true', help='强制清理，不询问确认')
    
    args = parser.parse_args()
    
    # 创建清理器实例
    cleaner = WXWorkCacheCleaner(args.path)
    
    if not cleaner.wxwork_path.exists():
        print(f"错误: 企业微信缓存目录不存在: {cleaner.wxwork_path}")
        return
    
    # 分析缓存
    print("正在分析缓存文件...")
    analysis = cleaner.analyze_cache()
    cleaner.print_analysis(analysis)
    
    if args.analyze:
        return
    
    # 清理缓存
    if args.clean is not None:
        patterns = args.clean if args.clean else list(cleaner.safe_patterns.keys())
    else:
        if not args.force:
            response = input("\n是否继续清理缓存? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("已取消清理操作")
                return
        patterns = list(cleaner.safe_patterns.keys())
    
    print("\n开始清理缓存...")
    results = cleaner.clean_cache(patterns, dry_run=args.dry_run)
    cleaner.print_results(results)

if __name__ == "__main__":
    wxwork_cache_cleaner_main()
	