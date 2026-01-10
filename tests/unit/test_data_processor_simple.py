"""
B4数据后处理系统测试
"""

import pytest
from src.processing.data_processor import (
    DataProcessor,
    FieldFilter,
    FieldTransformer,
    FieldColorizer,
    create_field_filter,
    create_field_transformer,
    create_field_colorizer,
    create_packet_processor,
)


class TestDataProcessor:
    """测试数据处理器"""

    def test_processor_initialization(self):
        """测试处理器初始化"""
        processor = DataProcessor()
        assert len(processor.filters) == 0
        assert len(processor.transformers) == 0
        assert len(processor.colorizers) == 0
        assert len(processor.processed_data) == 0

    def test_add_filter(self):
        """测试添加过滤器"""
        processor = DataProcessor()
        filter_func = lambda packet: packet.get("value", 0) > 10

        processor.add_filter(filter_func)
        assert len(processor.filters) == 1

    def test_process_packet_success(self):
        """测试成功处理数据包"""
        processor = DataProcessor()

        # 添加处理器
        processor.add_filter(lambda p: p.get("value", 0) > 5)
        processor.add_transformer(lambda p: {**p, "doubled": p.get("value", 0) * 2})
        processor.add_colorizer(lambda p: "blue" if p.get("value", 0) > 10 else "gray")

        packet = {"value": 15, "source": "test"}
        result = processor.process_packet(packet)

        assert result is not None
        assert result["doubled"] == 30
        assert result["_color"] == "blue"
        assert len(processor.processed_data) == 1


class TestFieldFilter:
    """测试字段过滤器"""

    def test_eq_filter(self):
        """测试等值过滤"""
        filter_obj = FieldFilter("cmd", 0x10)

        assert filter_obj({"cmd": 0x10}) is True
        assert filter_obj({"cmd": 0x15}) is False
        assert filter_obj({"other": 0x10}) is False


class TestFieldTransformer:
    """测试字段转换器"""

    def test_field_transformer(self):
        """测试字段转换"""
        transformer = FieldTransformer("value", lambda x: x * 2)

        packet = {"value": 15, "other": "data"}
        result = transformer(packet)

        assert result["value"] == 30
        assert result["other"] == "data"


class TestFieldColorizer:
    """测试字段着色器"""

    def test_field_colorizer(self):
        """测试字段着色"""
        color_map = {0x10: "blue", 0x15: "green"}
        colorizer = FieldColorizer("cmd", color_map)

        packet = {"cmd": 0x10}
        result = colorizer(packet)

        assert result == "blue"


class TestFactoryFunctions:
    """测试工厂函数"""

    def test_create_field_filter(self):
        """测试创建字段过滤器"""
        filter_obj = create_field_filter("status", "error")

        assert isinstance(filter_obj, FieldFilter)
        assert filter_obj.field_name == "status"
        assert filter_obj.value == "error"

    def test_create_field_transformer(self):
        """测试创建字段转换器"""
        transformer = create_field_transformer("value", lambda x: x + 10)

        assert isinstance(transformer, FieldTransformer)
        assert transformer.field_name == "value"

    def test_create_field_colorizer(self):
        """测试创建字段着色器"""
        color_map = {"good": "green", "bad": "red"}
        colorizer = create_field_colorizer("status", color_map)

        assert isinstance(colorizer, FieldColorizer)
        assert colorizer.field_name == "status"


class TestCreatePacketProcessor:
    """测试数据处理器创建"""

    def test_create_empty_processor(self):
        """测试创建空处理器"""
        processor = create_packet_processor()

        assert isinstance(processor, DataProcessor)
        assert len(processor.filters) == 0

    def test_create_processor_with_components(self):
        """测试创建带组件的处理器"""
        filters = [lambda p: p.get("value", 0) > 5]
        colorizers = [lambda p: "green" if p.get("status") == "ok" else "red"]

        processor = create_packet_processor(filters=filters, colorizers=colorizers)

        assert len(processor.filters) == 1
        assert len(processor.colorizers) == 1


if __name__ == "__main__":
    pytest.main([__file__])
