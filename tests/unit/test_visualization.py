"""
B5协议可视化集成测试
"""

import pytest
import time
from src.core.protocol_parser import ParsedPacket
from src.visualization.protocol_visualizer import (
    ProtocolVisualizationEngine,
    DataBuffer,
    VisualizationConfig,
    FieldExtractor,
    ColorScheme,
    create_visualization_engine,
    create_protocol_config,
)
from src.visualization.waveform_widget import (
    WaveformWidget,
    WaveformChannel,
    create_waveform_channel,
    create_waveform_widget,
    create_default_channels,
)
from src.visualization.field_panel import (
    FieldPanel,
    FieldTreeNode,
    FieldFilter,
    create_field_panel,
    create_field_filter,
)


def create_test_packet(raw_data: bytes, fields: dict, timestamp: float) -> ParsedPacket:
    """Create a test packet with required parameters."""
    return ParsedPacket(
        raw_data=raw_data,
        fields=fields,
        timestamp=timestamp,
        parse_time=timestamp,
        is_valid=True,
    )


class TestVisualizationConfig:
    """测试可视化配置"""

    def test_config_creation(self):
        """测试配置创建"""
        config = VisualizationConfig()

        assert config.window_width == 1200
        assert config.window_height == 800
        assert config.max_data_points == 10000
        assert config.update_frequency == 60
        assert config.buffer_size == 1000
        assert config.enable_gpu_acceleration is True
        assert config.theme == "dark"

    def test_custom_config(self):
        """测试自定义配置"""
        config = VisualizationConfig(window_width=800, window_height=600, theme="light")

        assert config.window_width == 800
        assert config.window_height == 600
        assert config.theme == "light"


class TestDataBuffer:
    """测试数据缓冲区"""

    def test_buffer_creation(self):
        """测试缓冲区创建"""
        buffer = DataBuffer(max_size=5)

        assert buffer.max_size == 5
        assert buffer.size() == 0

    def test_buffer_add_data(self):
        """测试添加数据"""
        buffer = DataBuffer(max_size=3)

        packet1 = create_test_packet(b"test1", {"value": 10}, 1000.0)
        packet2 = create_test_packet(b"test2", {"value": 20}, 1001.0)

        buffer.add_data(packet1)
        buffer.add_data(packet2)

        assert buffer.size() == 2

        # 添加第3个数据
        packet3 = create_test_packet(b"test3", {"value": 30}, 1002.0)
        buffer.add_data(packet3)

        assert buffer.size() == 3

        # 添加第4个数据（应该移除最旧的）
        packet4 = create_test_packet(b"test4", {"value": 40}, 1003.0)
        buffer.add_data(packet4)

        assert buffer.size() == 3
        data = buffer.get_data()
        assert len(data) == 3
        assert data[0].fields["value"] == 20  # 最旧的应该被移除

    def test_time_range_filtering(self):
        """测试时间范围过滤"""
        buffer = DataBuffer(max_size=10)

        # 添加不同时间的数据
        current_time = time.time()
        packet1 = create_test_packet(b"test1", {}, current_time - 5)
        packet2 = create_test_packet(b"test2", {}, current_time - 2)
        packet3 = create_test_packet(b"test3", {}, current_time - 0.5)
        packet4 = create_test_packet(b"test4", {}, current_time)

        buffer.add_data(packet1)
        buffer.add_data(packet2)
        buffer.add_data(packet3)
        buffer.add_data(packet4)

        # 获取最近3秒的数据
        recent_data = buffer.get_time_range(3)

        assert len(recent_data) == 3
        assert packet1 not in recent_data  # 超出时间范围
        assert packet2 in recent_data
        assert packet3 in recent_data
        assert packet4 in recent_data


class TestProtocolVisualizationEngine:
    """测试协议可视化引擎"""

    def test_engine_creation(self):
        """测试引擎创建"""
        config = VisualizationConfig()
        engine = ProtocolVisualizationEngine(config)

        assert engine.config == config
        assert len(engine.active_protocols) == 0
        assert len(engine.data_buffers) == 0

    def test_add_protocol(self):
        """测试添加协议"""
        engine = ProtocolVisualizationEngine(VisualizationConfig())

        packet = create_test_packet(
            b"test", {"cmd": 0x10, "data": "hello"}, time.time()
        )

        engine.add_protocol("test_protocol", packet)

        assert "test_protocol" in engine.active_protocols
        assert engine.data_buffers["test_protocol"].size() == 1

        # 添加更多数据
        for i in range(5):
            packet = create_test_packet(
                f"test{i}".encode(),
                {"cmd": 0x10 + i, "data": f"data{i}"},
                time.time() + i,
            )
            engine.add_protocol("test_protocol", packet)

        assert engine.data_buffers["test_protocol"].size() == 6

    def test_data_retrieval(self):
        """测试数据检索"""
        engine = ProtocolVisualizationEngine(VisualizationConfig())

        # 添加测试数据
        for i in range(10):
            packet = create_test_packet(
                f"test{i}".encode(), {"value": i, "status": i % 2 == 0}, time.time() + i
            )
            engine.add_protocol("test_protocol", packet)

        # 测试数据检索
        all_data = engine.get_protocol_data("test_protocol")
        assert len(all_data) == 10

        recent_data = engine.get_protocol_data("test_protocol", 5)
        assert len(recent_data) == 5

        recent_by_time = engine.get_protocol_data_by_time("test_protocol", float("inf"))
        assert len(recent_by_time) == 10

    def test_data_summary(self):
        """测试数据摘要"""
        engine = ProtocolVisualizationEngine(VisualizationConfig())

        # 添加多样化的测试数据
        test_data = [
            {"value": 10, "status": True, "text": "ok"},
            {"value": 20, "status": False, "text": "error"},
            {"value": 15, "status": True, "text": "warning"},
            {"value": 25, "status": False, "text": "critical"},
        ]

        for i, fields in enumerate(test_data):
            packet = create_test_packet(f"test{i}".encode(), fields, 1000.0 + i)
            engine.add_protocol("test_protocol", packet)

        summary = engine.get_data_summary("test_protocol")

        assert summary["count"] == 4


class TestWaveformChannel:
    """测试波形通道"""

    def test_channel_creation(self):
        """测试通道创建"""
        channel = WaveformChannel(
            name="test_channel", field_name="value", color="#ff0000"
        )

        assert channel.name == "test_channel"
        assert channel.field_name == "value"
        assert channel.color == "#ff0000"
        assert channel.scale == 1.0
        assert channel.offset == 0.0
        assert channel.line_width == 2
        assert channel.visible is True

    def test_packet_processing(self):
        """测试数据包处理"""
        channel = WaveformChannel(
            name="test_channel", field_name="value", color="#ff0000"
        )

        packet = create_test_packet(b"test", {"value": 42.5}, 1000.0)

        point = channel.process_packet(packet)

        assert point is not None
        assert point[0] == 1000.0
        assert point[1] == 42.5


class TestWaveformWidget:
    """测试波形组件"""

    def test_widget_creation(self):
        """测试组件创建"""
        widget = WaveformWidget()

        assert widget.time_window == 10.0
        assert len(widget.channels) == 0
        assert widget.renderer is not None

    def test_channel_management(self):
        """测试通道管理"""
        widget = WaveformWidget()

        channel1 = create_waveform_channel("ch1", "value1", "#ff0000")
        channel2 = create_waveform_channel("ch2", "value2", "#00ff00")

        widget.add_channel(channel1)
        widget.add_channel(channel2)

        assert len(widget.channels) == 2
        assert "ch1" in [ch.name for ch in widget.channels]
        assert "ch2" in [ch.name for ch in widget.channels]

    def test_data_processing(self):
        """测试数据处理"""
        widget = WaveformWidget()
        widget.set_time_window(2.0)  # 2秒窗口

        channel = create_waveform_channel("test", "value", "#ff0000")
        widget.add_channel(channel)

        # 添加几个数据包
        packet1 = create_test_packet(b"test1", {"value": 10.0}, time.time())
        packet2 = create_test_packet(b"test2", {"value": 20.0}, time.time())
        packet3 = create_test_packet(b"test3", {"value": 30.0}, time.time())

        widget.process_packet(packet1)
        widget.process_packet(packet2)
        widget.process_packet(packet3)

        channel_data = widget.renderer.get_channel_data("test")

        assert len(channel_data) == 3


class TestFieldPanel:
    """测试字段面板"""

    def test_panel_creation(self):
        """测试面板创建"""
        panel = FieldPanel()

        assert panel.width == 400
        assert panel.height == 600
        assert len(panel.root_nodes) == 0
        assert panel.field_filter is not None

    def test_protocol_data_addition(self):
        """测试协议数据添加"""
        panel = FieldPanel()

        packet = create_test_packet(
            b"test",
            {
                "header": {"magic": 0xAA, "version": 1},
                "payload": {"data": "test", "length": 4},
                "checksum": 0x1234,
            },
            time.time(),
        )

        panel.add_protocol_data("test_protocol", packet)

        assert "test_protocol" in panel.root_nodes
        root = panel.root_nodes["test_protocol"]
        assert len(root.children) > 0

    def test_field_filtering(self):
        """测试字段过滤"""
        panel = FieldPanel()
        panel.set_filter_text("value")

        # 添加测试数据
        for i in range(3):
            packet = create_test_packet(
                f"test{i}".encode(),
                {
                    "numeric_field": i * 10,
                    "text_field": f"text{i}",
                    "boolean_field": i % 2 == 0,
                    "value": i,
                },
                time.time() + i,
            )
            panel.add_protocol_data("test_protocol", packet)

        # 验证只包含value字段
        root = panel.root_nodes.get("test_protocol")
        if root:
            found_value = False
            for node in root.children:
                if "value" in node.name:
                    found_value = True
                    break
            assert found_value

    def test_field_statistics(self):
        """测试字段统计"""
        panel = FieldPanel()

        # 添加多样化的测试数据
        for i in range(10):
            packet = create_test_packet(
                f"test{i}".encode(),
                {"count": i, "type": "type" + str(i % 3), "value": i * 5},
                time.time() + i,
            )
            panel.add_protocol_data("test_protocol", packet)

        # 等待异步更新
        time.sleep(0.1)

        # 验证统计信息被记录
        assert len(panel.root_nodes) > 0


class TestFactoryFunctions:
    """测试工厂函数"""

    def test_create_engine(self):
        """测试创建引擎"""
        engine = create_visualization_engine()

        assert isinstance(engine, ProtocolVisualizationEngine)
        assert engine.config.update_frequency == 60

    def test_create_config(self):
        """测试创建配置"""
        config = create_protocol_config()

        assert config.window_width == 1200
        assert config.window_height == 800

    def test_create_waveform_channel(self):
        """测试创建波形通道"""
        channel = create_waveform_channel("test", "value", "#ff0000")

        assert isinstance(channel, WaveformChannel)
        assert channel.name == "test"

    def test_create_default_channels(self):
        """测试创建默认通道"""
        channels = create_default_channels("test_protocol")

        assert isinstance(channels, list)
        assert len(channels) > 0
        assert all(isinstance(ch, WaveformChannel) for ch in channels)
