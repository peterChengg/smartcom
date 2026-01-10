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
    create_protocol_config
)
from src.visualization.waveform_widget import (
    WaveformWidget,
    WaveformChannel,
    create_waveform_channel,
    create_waveform_widget,
    create_default_channels
)
from src.visualization.field_panel import (
    FieldPanel,
    FieldTreeNode,
    FieldFilter,
    create_field_panel,
    create_field_filter
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
        config = VisualizationConfig(
            window_width=800,
            window_height=600,
            theme="light"
        )
        
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
        
        packet1 = ParsedPacket(
            raw_data=b"test1", 
            fields={"value": 10}, 
            timestamp=1000.0,
            parse_time=1000.0,
            is_valid=True
        )
        packet2 = ParsedPacket(
            raw_data=b"test2", 
            fields={"value": 20}, 
            timestamp=1001.0,
            parse_time=1001.0,
            is_valid=True
        )
        
        buffer.add_data(packet1)
        buffer.add_data(packet2)
        
        assert buffer.size() == 2
        
        # 添加第3个数据
        packet3 = ParsedPacket(raw_data=b"test3", fields={"value": 30}, timestamp=1002)
        buffer.add_data(packet3)
        
        assert buffer.size() == 3
        
        # 添加第4个数据（应该移除最旧的）
        packet4 = ParsedPacket(raw_data=b"test4", fields={"value": 40}, timestamp=1003)
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
        packet1 = ParsedPacket(raw_data=b"test1", fields={}, timestamp=current_time - 5)
        packet2 = ParsedPacket(raw_data=b"test2", fields={}, timestamp=current_time - 2)
        packet3 = ParsedPacket(raw_data=b"test3", fields={}, timestamp=current_time - 0.5)
        packet4 = ParsedPacket(raw_data=b"test4", fields={}, timestamp=current_time)
        
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
        
        packet = ParsedPacket(raw_data=b"test", fields={"cmd": 0x10, "data": "hello"})
        
        engine.add_protocol("test_protocol", packet)
        
        assert "test_protocol" in engine.active_protocols
        assert engine.data_buffers["test_protocol"].size() == 1
        
        # 添加更多数据
        for i in range(5):
            packet = ParsedPacket(
                raw_data=f"test{i}".encode(),
                fields={"cmd": 0x10 + i, "data": f"data{i}"}
            )
            engine.add_protocol("test_protocol", packet)
            
        assert engine.data_buffers["test_protocol"].size() == 6

    def test_data_retrieval(self):
        """测试数据检索"""
        engine = ProtocolVisualizationEngine(VisualizationConfig())
        
        # 添加测试数据
        for i in range(10):
            packet = ParsedPacket(
                raw_data=f"test{i}".encode(),
                fields={"value": i, "status": i % 2 == 0}
            )
            engine.add_protocol("test_protocol", packet)
            
        # 测试数据检索
        all_data = engine.get_protocol_data("test_protocol")
        assert len(all_data) == 10
        
        recent_data = engine.get_protocol_data("test_protocol", 5)
        assert len(recent_data) == 5
        
        recent_by_time = engine.get_protocol_data_by_time("test_protocol", float('inf'))
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
            packet = ParsedPacket(
                raw_data=f"test{i}".encode(),
                fields=fields,
                timestamp=1000 + i
            )
            engine.add_protocol("test_protocol", packet)
            
        summary = engine.get_data_summary("test_protocol")
        
        assert summary["count"] == 4
        assert "value" in summary["fields"]
        assert "status" in summary["fields"]
        assert "text" in summary["fields"]
        
        value_stats = summary["fields"]["value"]
        assert value_stats["count"] == 4
        assert value_stats["unique_count"] == 4
        assert value_stats["min_value"] == 10
        assert value_stats["max_value"] == 25
        
        status_stats = summary["fields"]["status"]
        assert status_stats["unique_count"] == 2  # True, False


class TestWaveformChannel:
    """测试波形通道"""

    def test_channel_creation(self):
        """测试通道创建"""
        channel = WaveformChannel(
            name="test_channel",
            field_name="value",
            color="#ff0000",
            scale=2.0,
            offset=1.0
        )
        
        assert channel.name == "test_channel"
        assert channel.field_name == "value"
        assert channel.color == "#ff0000"
        assert channel.scale == 2.0
        assert channel.offset == 1.0
        assert channel.visible is True

    def test_packet_processing(self):
        """测试数据包处理"""
        channel = WaveformChannel(
            name="test_channel",
            field_name="value",
            color="#ff0000"
        )
        
        packet = ParsedPacket(
            raw_data=b"test",
            fields={"value": 42.5},
            timestamp=1000
        )
        
        result = channel.process_packet(packet)
        
        assert result is not None
        assert result[0] == 1000  # timestamp
        assert result[1] == 42.5  # value
        
        # 测试缺失字段
        packet_no_field = ParsedPacket(
            raw_data=b"test",
            fields={"other": 123},
            timestamp=1001
        )
        
        result_empty = channel.process_packet(packet_no_field)
        assert result_empty is None


class TestWaveformWidget:
    """测试波形组件"""

    def test_widget_creation(self):
        """测试组件创建"""
        widget = WaveformWidget(width=600, height=300)
        
        assert widget.width == 600
        assert widget.height == 300
        assert len(widget.channels) == 0
        assert widget.time_window == 10.0
        assert widget.zoom_level == 1.0

    def test_channel_management(self):
        """测试通道管理"""
        widget = WaveformWidget()
        
        channel1 = create_waveform_channel("Channel1", "data1", "#ff0000")
        channel2 = create_waveform_channel("Channel2", "data2", "#00ff00")
        
        widget.add_channel(channel1)
        widget.add_channel(channel2)
        
        assert len(widget.channels) == 2
        assert widget.get_channel("Channel1") == channel1
        assert widget.get_channel("Channel3") is None
        
        widget.remove_channel("Channel1")
        assert len(widget.channels) == 1
        assert widget.get_channel("Channel1") is None

    def test_data_processing(self):
        """测试数据处理"""
        widget = WaveformWidget()
        widget.set_time_window(2.0)  # 2秒窗口
        
        channel = create_waveform_channel("test", "value", "#ff0000")
        widget.add_channel(channel)
        
        current_time = time.time()
        
        # 添加一些测试数据
        for i in range(5):
            packet = ParsedPacket(
                raw_data=f"test{i}".encode(),
                fields={"value": float(i * 10)},
                timestamp=current_time - 1 + i
            )
            widget.process_packet(packet)
            
        display_data = widget.get_display_data()
        
        assert "test" in display_data["channels"]
        channel_data = display_data["channels"]["test"]
        
        # 验证数据处理
        assert len(channel_data["data"]) == 5
        assert channel_data["color"] == "#ff0000"
        
        # 验证统计
        stats = channel_data["stats"]
        assert stats["count"] == 5
        assert stats["y_range"]["min"] == 0.0
        assert stats["y_range"]["max"] == 40.0


class TestFieldPanel:
    """测试字段面板"""

    def test_panel_creation(self):
        """测试面板创建"""
        panel = FieldPanel(width=300, height=500)
        
        assert panel.width == 300
        assert panel.height == 500
        assert len(panel.root_nodes) == 0

    def test_protocol_data_addition(self):
        """测试协议数据添加"""
        panel = FieldPanel()
        
        packet = ParsedPacket(
            raw_data=b"test",
            fields={
                "header": {"magic": 0xAA, "version": 1},
                "payload": {"data": "test", "length": 4},
                "checksum": 0x1234
            }
        )
        
        panel.add_protocol_data("test_protocol", packet)
        
        assert "test_protocol" in panel.root_nodes
        root = panel.root_nodes["test_protocol"]
        
        # 验证字段树结构
        assert root.find_child("header") is not None
        assert root.find_child("payload") is not None
        assert root.find_child("checksum") is not None
        
        header_child = root.find_child("header")
        assert header_child.find_child("magic") is not None
        assert header_child.find_child("version") is not None

    def test_field_filtering(self):
        """测试字段过滤"""
        panel = FieldPanel()
        
        # 添加测试数据
        for i in range(3):
            packet = ParsedPacket(
                raw_data=f"test{i}".encode(),
                fields={
                    "numeric_field": i * 10,
                    "text_field": f"text{i}",
                    "boolean_field": i % 2 == 0
                }
            )
            panel.add_protocol_data("test_protocol", packet)
            
        # 测试过滤
        filter_obj = create_field_filter("text_field", "text1")
        panel.set_filter_text("text1")
        
        tree_data = panel.get_filtered_tree_data()
        
        # 应该只包含text_field为text1的协议数据
        assert len(tree_data) == 1
        root_data = tree_data[0]["root"]
        
        # 找到text1节点
        def find_node_by_name(node, name):
            if node["name"] == name:
                return node
            for child in node["children"]:
                result = find_node_by_name(child, name)
                if result:
                    return result
            return None
            
        text_node = find_node_by_name(root_data, "text_field")
        assert text_node is not None
        assert text_node["value"] == "text1"

    def test_field_statistics(self):
        """测试字段统计"""
        panel = FieldPanel()
        
        # 添加多样化的测试数据
        for i in range(10):
            packet = ParsedPacket(
                raw_data=f"test{i}".encode(),
                fields={
                    "count": i,
                    "type": "type" + str(i % 3),
                    "value": i * 5
                }
            )
            panel.add_protocol_data("test_protocol", packet)
            
        stats = panel.get_field_statistics()
        
        assert stats["total_fields"] > 0
        assert "type_distribution" in stats
        assert "update_statistics" in stats


class TestFactoryFunctions:
    """测试工厂函数"""

    def test_create_engine(self):
        """测试创建引擎"""
        engine = create_visualization_engine()
        
        assert isinstance(engine, ProtocolVisualizationEngine)
        assert engine.config.window_width == 1200  # 默认值

    def test_create_config(self):
        """测试创建配置"""
        config = create_protocol_config(
            window_width=1024,
            window_height=768,
            theme="light"
        )
        
        assert config.window_width == 1024
        assert config.window_height == 768
        assert config.theme == "light"

    def test_create_waveform_channel(self):
        """测试创建波形通道"""
        channel = create_waveform_channel("test", "value")
        
        assert isinstance(channel, WaveformChannel)
        assert channel.name == "test"
        assert channel.field_name == "value"

    def test_create_default_channels(self):
        """测试创建默认通道"""
        channels = create_default_channels("serial_protocol")
        
        assert len(channels) >= 3  # 至少有基本通道
        channel_names = [ch.name for ch in channels]
        assert "Data" in channel_names
        assert "Length" in channel_names
        assert "Checksum" in channel_names


if __name__ == "__main__":
    pytest.main([__file__])