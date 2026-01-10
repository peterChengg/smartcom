"""
协议可视化模块

提供协议解析结果的图形化显示和交互功能。
"""

from .protocol_visualizer import (
    DataBuffer,
    FieldExtractor,
    ProtocolVisualizationEngine,
    VisualizationConfig,
    ColorScheme,
    create_visualization_engine,
    create_protocol_config,
)

from .waveform_widget import (
    WaveformChannel,
    WaveformRenderer,
    WaveformWidget,
    create_waveform_channel,
    create_waveform_widget,
    create_default_channels,
)

from .field_panel import (
    FieldTreeNode,
    FieldTreeBuilder,
    FieldFilter,
    FieldPanel,
    create_field_panel,
    create_field_filter,
)

__all__ = [
    # 核心可视化
    "ProtocolVisualizationEngine",
    "DataBuffer",
    "VisualizationConfig",
    "ColorScheme",
    "FieldExtractor",
    # 组件
    "WaveformWidget",
    "WaveformChannel",
    "WaveformRenderer",
    "FieldPanel",
    "FieldTreeNode",
    "FieldTreeBuilder",
    "FieldFilter",
    # 工厂函数
    "create_visualization_engine",
    "create_protocol_config",
    "create_waveform_channel",
    "create_waveform_widget",
    "create_default_channels",
    "create_field_panel",
    "create_field_filter",
]
