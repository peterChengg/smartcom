"""
性能优化模块

提供性能监控和优化功能。
"""

import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, name: str = "default"):
        self.name = name
        self.call_count = 0
        self.total_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0
        self.last_call_time: Optional[float] = None
        self.call_times: List[float] = []
        self.performance_metrics: Dict[str, Any] = {}

    def start_timer(self, operation_name: str) -> None:
        """开始计时"""
        self.last_call_time = time.time()
        return None

    def end_timer(self, operation_name: str, start_time: float) -> float:
        """结束计时并记录"""
        elapsed = time.time() - start_time

        self.call_count += 1
        self.call_times.append(elapsed)
        self.total_time += elapsed

        # 更新统计
        self.min_time = min(self.min_time, elapsed)
        self.max_time = max(self.max_time, elapsed)
        self.avg_time = self.total_time / self.call_count

        self.performance_metrics[operation_name] = {
            "call_count": self.call_count,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "last_time": elapsed
        }

        return elapsed

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "monitor_name": self.name,
            "metrics": self.performance_metrics
        }

    def get_report(self) -> str:
        """生成性能报告"""
        lines = []
        lines.append(f"Performance Report: {self.name}")
        lines.append("-" * 50)

        for op_name, metrics in self.performance_metrics.items():
            lines.append(f"\n{op_name}:")
            lines.append(f"  Calls: {metrics['call_count']}")
            lines.append(f"  Total time: {metrics['total_time']:.3f}s")
            lines.append(f"  Avg time: {metrics['avg_time']*1000:.3f}ms")
            lines.append(f"  Min time: {metrics['min_time']*1000:.3f}ms")
            lines.append(f"  Max time: {metrics['max_time']*1000:.3f}ms")

        return "\n".join(lines)


def performance_monitor(func):
    """性能监控装饰器"""
    monitor = PerformanceMonitor(func.__name__)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start_time
            monitor.end_timer(func.__name__, start_time)

    wrapper.performance_monitor = monitor
    wrapper.__wrapped__ = func

    return wrapper


class CacheManager:
    """缓存管理器"""

    def __init__(self, max_size: int = 1000, ttl: float = 60.0):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Any] = {}
        self.access_time: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        self.hit_count += 1
        self.access_time[key] = time.time()

        if key in self.cache:
            # 检查是否过期
            if time.time() - self.access_time[key] > self.ttl:
                del self.cache[key]
                self.miss_count += 1
                return None

        return self.cache.get(key)

        return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        self.cache[key] = value
        self.access_time[key] = time.time()

        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            # 移除最旧的项
            oldest_key = min(self.access_time, key=lambda k: self.access_time[k])
            del self.cache[oldest_key]

    def clear(self, key: Optional[str] = None) -> None:
        """清空缓存"""
        if key:
            del self.cache[key]
        elif key is None:
            self.cache.clear()

        self.access_time.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "cache_size": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0,
            "keys": list(self.cache.keys())
        }


class OptimizedParser:
    """优化后的解析器包装器"""

    def __init__(self, parser: Any, enable_cache: bool = True):
        self.parser = parser
        self.enable_cache = enable_cache
        self.cache = CacheManager(max_size=500, ttl=30.0)
        self.perf_monitor = PerformanceMonitor("optimized_parser")

    async def parse(self, data: bytes) -> Optional[Any]:
        """带缓存的解析"""
        # 检查缓存
        cache_key = data[:32].hex() if len(data) >= 32 else data.hex()

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 解析新数据
        start_time = self.perf_monitor.start_timer("parse")
        result = await self.parser.parse(data)

        # 缓存结果
        if self.enable_cache and result:
            self.cache.set(cache_key, result)

        elapsed = self.perf_monitor.end_timer("parse", start_time)
        logger.info(f"Parse completed in {elapsed*1000:.3f}ms")

        return result

    def get_performance(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.perf_monitor.get_stats()


def optimize_buffer_processing(processor, chunk_size: int = 1000) -> None:
    """优化缓冲处理"""
    buffer = []

    async def process_chunk(data: bytes) -> None:
        buffer.extend(data)

        if len(buffer) >= chunk_size:
            chunk = bytes(buffer[:chunk_size])
            buffer = buffer[chunk_size:]

            await processor.process_packet(chunk)

    async def process_data_stream(self, data_stream: bytes) -> None:
        """处理数据流"""
        buffer = []

        async for chunk in data_stream:
            buffer.append(chunk)
            if len(buffer) >= chunk_size:
                chunk = bytes(buffer[:chunk_size])
                buffer = buffer[chunk_size:]

                await processor.process_packet(chunk)

    buffer = bytes(buffer)

    return None