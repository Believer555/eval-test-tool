"""
【模块定位】支撑层 - 计时工具
【核心功能】提供函数计时装饰器，可复用于任何需要统计耗时的场景
"""
import time
from functools import wraps


def timeit(func):
    """
    函数计时装饰器
    用法：在函数上添加 @timeit 注解，自动打印执行耗时
    """
    @wraps(func)  # 保留原函数的元信息（名称、文档等）
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[TIMING] {func.__name__} 耗时: {(end - start):.3f}s")
        return result
    return wrapper
