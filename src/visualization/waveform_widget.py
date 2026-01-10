"""
波形显示组件

提供协议数据的时序波形图展示功能。
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from collections import deque

from ..core.protocol_parser import ParsedPacket
from ..processing.data_processor import DataProcessor
from .protocol_visualizer import FieldExtractor, ColorScheme

logger = logging.getLogger(__name__)


class WaveformRenderer:
    """波形渲染器"""

    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self.data_cache: Dict[str, deque] = {}
        self.render_cache: Dict[str, Any] = {}
        self.last_update_time = 0

    def add_data_point(self, channel: str, x: float, y: float) -> None:
        """添加数据点"""
        if channel not in self.data_cache:
            self.data_cache[channel] = deque(maxlen=self.max_points)

        self.data_cache[channel].append((x, y))

    def get_channel_data(self, channel: str) -> List[Tuple[float, float]]:
        """获取通道数据"""
        if channel not in self.data_cache:
            return []
        return list(self.data_cache[channel])

    def clear_channel(self, channel: str) -> None:
        """清空通道数据"""
        if channel in self.data_cache:
            self.data_cache[channel].clear()

    def clear_all_channels(self) -> None:
        """清空所有通道数据"""
        for channel_name in self.data_cache:
            channel = self.data_cache[channel_name]
            channel.clear()

    def get_channel_stats(self, channel: str) -> Dict[str, Any]:
        """获取通道统计信息"""
        data = self.get_channel_data(channel)
        if not data:
            return {}

        x_values = [point[0] for point in data]
        y_values = [point[1] for point in data]

        return {
            "count": len(data),
            "x_range": {"min": min(x_values), "max": max(x_values)},
            "y_range": {"min": min(y_values), "max": max(y_values)},
            "avg_y": sum(y_values) / len(y_values),
            "latest_y": y_values[-1] if y_values else None,
        }


class WaveformChannel:
    """波形通道配置"""

    def __init__(
        self,
        name: str,
        field_name: str,
        color: str,
        scale: float = 1.0,
        offset: float = 0.0,
        line_width: int = 2,
        visible: bool = True,
    ):
        self.name = name
        self.field_name = field_name
        self.color = color
        self.scale = scale
        self.offset = offset
        self.line_width = line_width
        self.visible = visible

    def process_packet(self, packet: ParsedPacket) -> Optional[Tuple[float, float]]:
        """处理数据包，返回(x, y)坐标"""
        value = FieldExtractor.extract_numeric_field(packet, self.field_name)
        if value is None:
            return None

        x = getattr(packet, "timestamp", time.time())
        y = value * self.scale + self.offset

        return (x, y)


class WaveformWidget:
    """波形显示组件"""

    def __init__(self, width: int = 800, height: int = 400):
        self.width = width
        self.height = height
        self.renderer = WaveformRenderer()
        self.channels: List[WaveformChannel] = []
        self.time_window: float = 10.0  # 显示时间窗口(秒)
        self.auto_scroll: bool = True
        self.show_grid: bool = True
        self.show_crosshair: bool = True
        self.zoom_level: float = 1.0
        self.pan_offset: float = 0.0

        # 交互状态
        self.mouse_pos: Tuple[int, int] = (0, 0)
        self.crosshair_value: Optional[float] = None
        self.selected_channels: List[str] = []

    def add_channel(self, channel: WaveformChannel) -> None:
        """添加波形通道"""
        self.channels.append(channel)
        logger.info(f"Added waveform channel: {channel.name}")

    def remove_channel(self, channel_name: str) -> None:
        """移除波形通道"""
        self.channels = [ch for ch in self.channels if ch.name != channel_name]
        logger.info(f"Removed waveform channel: {channel_name}")

    def get_channel(self, channel_name: str) -> Optional[WaveformChannel]:
        """获取指定通道"""
        for channel in self.channels:
            if channel.name == channel_name:
                return channel
        return None

    def set_time_window(self, seconds: float) -> None:
        """设置时间窗口"""
        self.time_window = max(0.1, seconds)  # 最小0.1秒
        logger.debug(f"Time window set to {seconds}s")

    def set_zoom(self, zoom_level: float) -> None:
        """设置缩放级别"""
        self.zoom_level = max(0.1, zoom_level)
        logger.debug(f"Zoom level set to {zoom_level}")

    def pan(self, offset: float) -> None:
        """平移视图"""
        self.pan_offset += offset
        logger.debug(f"Pan offset: {self.pan_offset}")

    def toggle_grid(self) -> None:
        """切换网格显示"""
        self.show_grid = not self.show_grid

    def toggle_crosshair(self) -> None:
        """切换十字线显示"""
        self.show_crosshair = not self.show_crosshair

    def toggle_channel_visibility(self, channel_name: str) -> None:
        """切换通道可见性"""
        channel = self.get_channel(channel_name)
        if channel:
            channel.visible = not channel.visible

    def process_packet(self, packet: ParsedPacket) -> None:
        """处理数据包"""
        current_time = getattr(packet, "timestamp", time.time())

        # 移除超出时间窗口的旧数据
        cutoff_time = current_time - self.time_window
        self._remove_old_data(cutoff_time)

        # 添加新数据点
        for channel in self.channels:
            if channel.visible:
                point = channel.process_packet(packet)
                if point:
                    self.renderer.add_data_point(channel.name, point[0], point[1])

    def get_display_data(self) -> Dict[str, Any]:
        """获取显示数据"""
        channels_data = {}

        for channel in self.channels:
            if not channel.visible:
                continue

            channel_data = self.renderer.get_channel_data(channel.name)
            if not channel_data:
                continue

            # 应用缩放和平移
            filtered_data = self._apply_filters(channel_data, current_time)
            
            channels_data[channel.name] = {
                "data": filtered_data,
                "color": channel.color,
                "line_width": channel.line_width,
                "stats": self.renderer.get_channel_stats(channel.name),
            }

        return {
            "channels": channels_data,
            "time_window": self.time_window,
            "zoom_level": self.zoom_level,
            "pan_offset": self.pan_offset,
            "mouse_pos": self.mouse_pos,
            "crosshair_value": self.crosshair_value,
            "show_grid": self.show_grid,
            "show_crosshair": self.show_crosshair,
        }

    def _remove_old_data(self, cutoff_time: float) -> None:
        """移除旧数据"""
        for channel in self.channels:
            channel_data = self.renderer.get_channel_data(channel.name)
            if not channel_data:
                continue

            # 从前面开始删除超出时间窗口的数据
            while channel_data and channel_data[0][0] < cutoff_time:
                # 手动移除第一个元素（因为deque的 maxlen特性）
                if channel.name in self.renderer.data_cache:
                    cache = self.renderer.data_cache[channel.name]
                    if cache:
                        cache.popleft()

    def _apply_filters(
        self, data: List[Tuple[float, float]], cutoff_time: float
    ) -> List[Tuple[float, float]]:
        """应用缩放、平移等过滤器"""
        if not data:
            return []

        filtered_data = []
        current_time = time.time()

        for x, y in data:
            # 时间窗口过滤
            if x < cutoff_time:
                continue

            # 应用缩放和平移
            display_x = (x - current_time) * self.zoom_level + self.pan_offset
            display_y = y * self.zoom_level

            # 只显示在窗口范围内的点
            if -self.width // 2 <= display_x <= self.width // 2:
                filtered_data.append((display_x, display_y))

        return filtered_data

    def handle_mouse_move(self, x: int, y: int) -> Optional[float]:
        """处理鼠标移动"""
        self.mouse_pos = (x, y)

        if not self.show_crosshair:
            return None

        # 计算鼠标位置对应的数值
        center_x = self.width // 2
        time_offset = (x - center_x) / self.zoom_level - self.pan_offset
        actual_time = time.time() + time_offset

        # 找到最接近的时间点
        closest_value = None
        min_distance = float("inf")

        for channel in self.channels:
            if not channel.visible:
                continue

            channel_data = self.renderer.get_channel_data(channel.name)
            for data_x, data_y in channel_data:
                if abs(data_x - actual_time) < min_distance:
                    min_distance = abs(data_x - actual_time)
                    closest_value = data_y

        self.crosshair_value = closest_value
        return closest_value

    def get_channel_list(self) -> List[Dict[str, Any]]:
        """获取通道列表"""
        return [
            {
                "name": ch.name,
                "field_name": ch.field_name,
                "color": ch.color,
                "visible": ch.visible,
                "scale": ch.scale,
                "offset": ch.offset,
                "stats": self.renderer.get_channel_stats(ch.name),
            }
            for ch in self.channels
        ]

    def export_data(self, filename: str, channels: Optional[List[str]] = None) -> bool:
        """导出波形数据"""
        try:
            import json

            export_data = {}

            for channel in self.channels:
                if channels and channel.name not in channels:
                    continue

                channel_data = self.renderer.get_channel_data(channel.name)
                export_data[channel.name] = {
                    "field_name": channel.field_name,
                    "color": channel.color,
                    "scale": channel.scale,
                    "offset": channel.offset,
                    "data": channel_data,
                }

            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Waveform data exported to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to export waveform data: {e}")
            return False


# 工厂函数
def create_waveform_channel(
    name: str,
    field_name: str,
    color: Optional[str] = None,
    scale: float = 1.0,
    offset: float = 0.0,
) -> WaveformChannel:
    """创建波形通道"""
    if color is None:
        color = ColorScheme.get_protocol_color("serial")

    return WaveformChannel(name, field_name, color, scale, offset)


def create_waveform_widget(width: int = 800, height: int = 400) -> WaveformWidget:
    """创建波形显示组件"""
    return WaveformWidget(width, height)


def create_default_channels(protocol_name: str) -> List[WaveformChannel]:
    """创建默认通道配置"""
    common_channels = [
        create_waveform_channel("Data", "data", "#00ff88"),
        create_waveform_channel("Length", "length", "#ff8800"),
        create_waveform_channel("Checksum", "checksum", "#8800ff"),
    ]

    # 根据协议类型调整
    if "bluetooth" in protocol_name.lower():
        common_channels.append(create_waveform_channel("RSSI", "rssi", "#ff0088"))
    elif "network" in protocol_name.lower():
        common_channels.append(
            create_waveform_channel("Sequence", "sequence", "#0088ff")
        )

    return common_channels
