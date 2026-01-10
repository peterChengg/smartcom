"""
协议可视化系统主模块

提供协议解析结果的图形化显示和交互功能。
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass

from ..core.protocol_parser import ParsedPacket
from ..processing.data_processor import DataProcessor

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """可视化配置"""

    window_width: int = 1200
    window_height: int = 800
    max_data_points: int = 10000
    update_frequency: int = 60  # FPS
    buffer_size: int = 1000
    enable_gpu_acceleration: bool = True
    theme: str = "dark"


class DataBuffer:
    """实时数据缓冲区"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)

    def add_data(self, packet: ParsedPacket) -> None:
        """添加数据包到缓冲区"""
        self.buffer.append(packet)
        self.timestamps.append(
            packet.timestamp if hasattr(packet, "timestamp") else time.time()
        )

    def get_data(self, count: Optional[int] = None) -> List[ParsedPacket]:
        """获取最近的n个数据包"""
        if count is None:
            return list(self.buffer)
        return list(self.buffer)[-count:]

    def get_time_range(self, duration: float) -> List[ParsedPacket]:
        """获取指定时间范围内的数据包"""
        if not self.timestamps:
            return []

        current_time = time.time()
        start_time = current_time - duration

        result = []
        for i, timestamp in enumerate(self.timestamps):
            if timestamp >= start_time:
                result.append(self.buffer[i])

        return result

    def clear(self) -> None:
        """清空缓冲区"""
        self.buffer.clear()
        self.timestamps.clear()

    def size(self) -> int:
        """获取当前缓冲区大小"""
        return len(self.buffer)


class ProtocolVisualizationEngine:
    """协议可视化引擎"""

    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.data_processor: Optional[DataProcessor] = None
        self.data_buffers: Dict[str, DataBuffer] = {}
        self.active_protocols: List[str] = []
        self.performance_stats = {
            "frames_rendered": 0,
            "total_render_time": 0.0,
            "avg_render_time": 0.0,
            "fps": 0.0,
        }

    def set_data_processor(self, processor: DataProcessor) -> None:
        """设置数据处理器"""
        self.data_processor = processor
        logger.info("Data processor connected to visualization engine")

    def add_protocol(self, protocol_name: str, packet: ParsedPacket) -> None:
        """添加协议数据包"""
        if protocol_name not in self.data_buffers:
            self.data_buffers[protocol_name] = DataBuffer(self.config.buffer_size)
            self.active_protocols.append(protocol_name)

        # 通过数据处理器处理数据包
        if self.data_processor:
            processed_packet = self.data_processor.process_packet(packet.fields)
            if processed_packet:
                packet.fields.update(processed_packet)

        self.data_buffers[protocol_name].add_data(packet)

    def get_protocol_data(
        self, protocol_name: str, count: Optional[int] = None
    ) -> List[ParsedPacket]:
        """获取指定协议的数据"""
        if protocol_name not in self.data_buffers:
            return []
        return self.data_buffers[protocol_name].get_data(count)

    def get_protocol_data_by_time(
        self, protocol_name: str, duration: float
    ) -> List[ParsedPacket]:
        """获取指定协议时间范围内的数据"""
        if protocol_name not in self.data_buffers:
            return []
        return self.data_buffers[protocol_name].get_time_range(duration)

    def get_active_protocols(self) -> List[str]:
        """获取活跃协议列表"""
        return self.active_protocols.copy()

    def remove_protocol(self, protocol_name: str) -> None:
        """移除协议"""
        if protocol_name in self.data_buffers:
            del self.data_buffers[protocol_name]
            self.active_protocols.remove(protocol_name)
            logger.info(f"Protocol {protocol_name} removed from visualization")

    def clear_protocol_data(self, protocol_name: str) -> None:
        """清空指定协议的数据"""
        if protocol_name in self.data_buffers:
            self.data_buffers[protocol_name].clear()

    def clear_all_data(self) -> None:
        """清空所有协议数据"""
        for buffer in self.data_buffers.values():
            buffer.clear()
        logger.info("All protocol data cleared")

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = self.performance_stats.copy()
        if stats["frames_rendered"] > 0:
            stats["avg_render_time"] = (
                stats["total_render_time"] / stats["frames_rendered"]
            )
        return stats

    def reset_performance_stats(self) -> None:
        """重置性能统计"""
        self.performance_stats = {
            "frames_rendered": 0,
            "total_render_time": 0.0,
            "avg_render_time": 0.0,
            "fps": 0.0,
        }

    def update_performance(self, render_time: float) -> None:
        """更新性能统计"""
        self.performance_stats["frames_rendered"] += 1
        self.performance_stats["total_render_time"] += render_time

        # 计算FPS
        frames = self.performance_stats["frames_rendered"]
        total_time = self.performance_stats["total_render_time"]
        if total_time > 0:
            self.performance_stats["fps"] = frames / total_time

        # 保持最近100帧的平均值
        if frames > 100:
            self.performance_stats["total_render_time"] *= 0.9
            self.performance_stats["frames_rendered"] = int(frames * 0.9)

    def get_data_summary(self, protocol_name: str) -> Dict[str, Any]:
        """获取协议数据摘要"""
        if protocol_name not in self.data_buffers:
            return {}

        buffer = self.data_buffers[protocol_name]
        data = buffer.get_data()

        if not data:
            return {"count": 0, "time_range": None, "fields": {}}

        timestamps = [getattr(packet, "timestamp", 0) for packet in data]

        # 统计字段
        field_stats = {}
        for packet in data:
            for field_name, field_value in packet.fields.items():
                if field_name not in field_stats:
                    field_stats[field_name] = {
                        "count": 0,
                        "unique_values": set(),
                        "type": type(field_value).__name__,
                    }

                field_stats[field_name]["count"] += 1
                field_stats[field_name]["unique_values"].add(field_value)

        # 转换set为list以便JSON序列化
        for field_name in field_stats:
            field_stats[field_name]["unique_values"] = list(
                field_stats[field_name]["unique_values"]
            )
            field_stats[field_name]["unique_count"] = len(
                field_stats[field_name]["unique_values"]
            )

        return {
            "count": len(data),
            "time_range": {
                "start": min(timestamps) if timestamps else None,
                "end": max(timestamps) if timestamps else None,
                "duration": max(timestamps) - min(timestamps) if timestamps else 0,
            },
            "fields": field_stats,
        }

    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """获取所有协议的数据摘要"""
        summaries = {}
        for protocol_name in self.active_protocols:
            summaries[protocol_name] = self.get_data_summary(protocol_name)
        return summaries


class FieldExtractor:
    """字段提取器"""

    @staticmethod
    def extract_numeric_field(packet: ParsedPacket, field_name: str) -> Optional[float]:
        """提取数值字段"""
        if field_name not in packet.fields:
            return None

        value = packet.fields[field_name]
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def extract_text_field(packet: ParsedPacket, field_name: str) -> Optional[str]:
        """提取文本字段"""
        if field_name not in packet.fields:
            return None

        value = packet.fields[field_name]
        return str(value) if value is not None else None

    @staticmethod
    def extract_bytes_field(packet: ParsedPacket, field_name: str) -> Optional[bytes]:
        """提取字节字段"""
        if field_name not in packet.fields:
            return None

        value = packet.fields[field_name]
        if isinstance(value, bytes):
            return value
        elif isinstance(value, str):
            return value.encode("utf-8")
        return None


class ColorScheme:
    """颜色方案"""

    # 默认颜色方案
    DEFAULT_COLORS = {
        "background": "#1e1e1e",
        "foreground": "#ffffff",
        "grid": "#444444",
        "highlight": "#00ff00",
        "warning": "#ffaa00",
        "error": "#ff0000",
        "info": "#0088ff",
    }

    # 协议类型颜色
    PROTOCOL_COLORS = {
        "serial": "#00ff88",
        "network": "#ff8800",
        "bluetooth": "#8800ff",
        "usb": "#ff0088",
        "custom": "#8888ff",
    }

    # 数据类型颜色
    DATA_TYPE_COLORS = {
        "numeric": "#00ffff",
        "text": "#ffff00",
        "binary": "#ff00ff",
        "timestamp": "#888888",
        "status": "#00ff00",
    }

    @classmethod
    def get_protocol_color(cls, protocol_type: str) -> str:
        """获取协议类型对应的颜色"""
        return cls.PROTOCOL_COLORS.get(protocol_type, cls.DEFAULT_COLORS["foreground"])

    @classmethod
    def get_data_type_color(cls, data_type: str) -> str:
        """获取数据类型对应的颜色"""
        return cls.DATA_TYPE_COLORS.get(data_type, cls.DEFAULT_COLORS["foreground"])

    @classmethod
    def get_color_for_value(cls, value: Any, field_name: str) -> str:
        """根据字段值获取颜色"""
        # 使用B4的着色功能
        if hasattr(value, "_color"):
            return getattr(value, "_color")

        # 基于字段名和数据类型推断颜色
        if isinstance(value, (int, float)):
            return cls.get_data_type_color("numeric")
        elif isinstance(value, str):
            return cls.get_data_type_color("text")
        elif isinstance(value, bytes):
            return cls.get_data_type_color("binary")
        elif "timestamp" in field_name.lower() or "time" in field_name.lower():
            return cls.get_data_type_color("timestamp")
        elif "status" in field_name.lower() or "state" in field_name.lower():
            return cls.get_data_type_color("status")

        return cls.DEFAULT_COLORS["foreground"]


# 工厂函数
def create_visualization_engine(
    config: Optional[VisualizationConfig] = None,
) -> ProtocolVisualizationEngine:
    """创建可视化引擎"""
    if config is None:
        config = VisualizationConfig()

    return ProtocolVisualizationEngine(config)


def create_protocol_config(
    window_width: int = 1200,
    window_height: int = 800,
    max_data_points: int = 10000,
    update_frequency: int = 60,
    theme: str = "dark",
) -> VisualizationConfig:
    """创建可视化配置"""
    return VisualizationConfig(
        window_width=window_width,
        window_height=window_height,
        max_data_points=max_data_points,
        update_frequency=update_frequency,
        theme=theme,
    )
