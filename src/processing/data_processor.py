"""
B4: 数据后处理系统
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器"""

    def __init__(self):
        self.filters = []
        self.transformers = []
        self.colorizers = []
        self.processed_data = []

    def add_filter(self, filter_func):
        """添加过滤器"""
        self.filters.append(filter_func)

    def add_transformer(self, transformer_func):
        """添加转换器"""
        self.transformers.append(transformer_func)

    def add_colorizer(self, colorizer_func):
        """添加着色器"""
        self.colorizers.append(colorizer_func)

    def process_packet(self, packet):
        """处理数据包"""
        # 应用过滤器
        for filter_func in self.filters:
            if not filter_func(packet):
                return None

        # 应用转换器
        result = packet.copy()
        for transformer in self.transformers:
            try:
                result = transformer(result)
            except Exception as e:
                logger.error(f"Transformer error: {e}")

        # 应用着色器
        for colorizer in self.colorizers:
            try:
                color = colorizer(result)
                if color:
                    result["_color"] = color
            except Exception as e:
                logger.error(f"Colorizer error: {e}")

        self.processed_data.append(result)
        return result


class FieldFilter:
    """字段过滤器"""

    def __init__(self, field_name, value, operator="eq"):
        self.field_name = field_name
        self.value = value
        self.operator = operator.lower()

    def __call__(self, packet):
        if self.field_name not in packet:
            return False

        field_value = packet[self.field_name]

        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "in":
            return field_value in self.value

        return False


class FieldTransformer:
    """字段转换器"""

    def __init__(self, field_name, transform_func):
        self.field_name = field_name
        self.transform_func = transform_func

    def __call__(self, packet):
        result = packet.copy()
        if self.field_name in result:
            result[self.field_name] = self.transform_func(result[self.field_name])
        return result


class FieldColorizer:
    """字段着色器"""

    def __init__(self, field_name, color_map):
        self.field_name = field_name
        self.color_map = color_map

    def __call__(self, packet):
        if self.field_name in packet:
            field_value = packet[self.field_name]
            return self.color_map.get(field_value, "default")
        return "default"


def create_field_filter(field_name, value, operator="eq"):
    """创建字段过滤器"""
    return FieldFilter(field_name, value, operator)


def create_field_transformer(field_name, transform_func):
    """创建字段转换器"""
    return FieldTransformer(field_name, transform_func)


def create_field_colorizer(field_name, color_map):
    """创建字段着色器"""
    return FieldColorizer(field_name, color_map)


def create_packet_processor(filters=None, transformers=None, colorizers=None):
    """创建数据处理器"""
    processor = DataProcessor()

    if filters:
        for filter_item in filters:
            processor.add_filter(filter_item)

    if transformers:
        for transformer_item in transformers:
            processor.add_transformer(transformer_item)

    if colorizers:
        for colorizer_item in colorizers:
            processor.add_colorizer(colorizer_item)

    return processor
