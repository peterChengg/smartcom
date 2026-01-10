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

    def test_init(self):
        """测试初始化"""
        processor = DataProcessor()
        assert len(processor.filters) == 0
        assert len(processor.transformers) == 0
        assert len(processor.colorizers) == 0

    def test_process_packet(self):
        """测试处理数据包"""
        processor = DataProcessor()
        
        # 添加过滤器、转换器、着色器
        processor.add_filter(lambda p: p.get("value", 0) > 5)
        processor.add_transformer(lambda p: {**p, "doubled": p.get("value", 0) * 2})
        processor.add_colorizer(lambda p: "blue" if p.get("value", 0) > 10 else "gray")
        
        packet = {"value": 15}
        result = processor.process_packet(packet)
        
        assert result is not None
        assert result["doubled"] == 30
        assert result["_color"] == "blue"


class TestFieldFilter:
    """测试字段过滤器"""

    def test_eq_filter(self):
        """测试等值过滤"""
        filter_obj = FieldFilter("cmd", 0x10)
        
        assert filter_obj({"cmd": 0x10}) is True
        assert filter_obj({"cmd": 0x15}) is False

    def test_gt_filter(self):
        """测试大于过滤"""
        filter_obj = FieldFilter("value", 100, "gt")
        
        assert filter_obj({"value": 150}) is True
        assert filter_obj({"value": 50}) is False


class TestFieldTransformer:
    """测试字段转换器"""

    def test_transform(self):
        """测试字段转换"""
        transformer = FieldTransformer("value", lambda x: x * 2)
        
        packet = {"value": 15}
        result = transformer(packet)
        
        assert result["value"] == 30


class TestFieldColorizer:
    """测试字段着色器"""

    def test_colorize(self):
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
    """测试创建数据处理器"""

    def test_create_processor(self):
        """测试创建处理器"""
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