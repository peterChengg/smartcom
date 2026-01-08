"""
Data post-processing system for protocol fields.

This module provides data filtering, transformation, and coloring
capabilities for parsed protocol data. Supports conditional processing,
real-time filtering, and visual enhancement.
"""

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Data processor for parsed protocol data.

    Provides filtering, transformation, and visualization enhancement.
    """

    def __init__(self):
        self.filters: List[DataFilter] = []
        self.transformers: List[DataTransformer] = []
        self.colorizers: List[DataColorizer] = []
        self.processed_data: List[Dict[str, Any]] = []

    def add_filter(
        self, filter_func: Union[DataFilter, Callable[[Dict[str, Any]], bool]]
    ) -> None:
        """
        Add a data filter.

        Args:
            filter_func: Filter function or DataFilter instance.
        """
        if callable(filter_func):
            filter_instance = FunctionFilter(filter_func)
        else:
            filter_instance = filter_func

        self.filters.append(filter_instance)

    def add_transformer(
        self,
        transformer_func: Union[
            DataTransformer, Callable[[Dict[str, Any]], Dict[str, Any]]
        ],
    ) -> None:
        """
        Add a data transformer.

        Args:
            transformer_func: Transformer function or DataTransformer instance.
        """
        if callable(transformer_func):
            transformer_instance = FunctionTransformer(transformer_func)
        else:
            transformer_instance = transformer_func

        self.transformers.append(transformer_instance)

    def add_colorizer(
        self, colorizer_func: Union[DataColorizer, Callable[[Dict[str, Any]], str]]
    ) -> None:
        """
        Add a data colorizer.

        Args:
            colorizer_func: Colorizer function or DataColorizer instance.
        """
        if callable(colorizer_func):
            colorizer_instance = FunctionColorizer(colorizer_func)
        else:
            colorizer_instance = colorizer_func

        self.colorizers.append(colorizer_instance)

    def process_packet(self, packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a parsed packet through filters, transformers, and colorizers.

        Args:
            packet: Parsed packet data.

        Returns:
            Processed packet or None if filtered out.
        """
        processed_packet = packet.copy()

        # Apply filters
        for filter_instance in self.filters:
            if not filter_instance.filter(processed_packet):
                logger.debug(f"Packet filtered out by {filter_instance}")
                return None

        # Apply transformers
        for transformer_instance in self.transformers:
            try:
                processed_packet = transformer_instance.transform(processed_packet)
            except Exception as e:
                logger.error(f"Transformer error: {e}")

        # Apply colorizers
        for colorizer_instance in self.colorizers:
            try:
                processed_packet = colorizer_instance.colorize(processed_packet)
            except Exception as e:
                logger.error(f"Colorizer error: {e}")

        self.processed_data.append(processed_packet)
        return processed_packet

    def process_packets(self, packets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple packets.

        Args:
            packets: List of parsed packets.

        Returns:
            List of processed packets.
        """
        processed_packets = []
        for packet in packets:
            processed = self.process_packet(packet)
            if processed is not None:
                processed_packets.append(processed)

        return processed_packets

    def get_processed_data(self) -> List[Dict[str, Any]]:
        """Get all processed data."""
        return self.processed_data.copy()

    def clear_processed_data(self) -> None:
        """Clear processed data."""
        self.processed_data.clear()


class DataFilter:
    """Base class for data filters."""

    def filter(self, packet: Dict[str, Any]) -> bool:
        """
        Filter a packet.

        Args:
            packet: Parsed packet data.

        Returns:
            True if packet should be kept, False if filtered out.
        """
        raise NotImplementedError


class FieldFilter(DataFilter):
    """Filter based on field values."""

    def __init__(self, field_name: str, value: Any, operator: str = "eq"):
        """
        Initialize field filter.

        Args:
            field_name: Name of field to filter on.
            value: Value to compare against.
            operator: Comparison operator (eq, ne, gt, lt, gte, lte, in, not_in, regex, custom).
        """
        self.field_name = field_name
        self.value = value
        self.operator = operator.lower()

    def filter(self, packet: Dict[str, Any]) -> bool:
        """
        Filter packet based on field value.

        Args:
            packet: Parsed packet data.

        Returns:
            True if packet should be kept.
        """
        if self.field_name not in packet:
            return False  # Field not present, filter out

        field_value = packet[self.field_name]

        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "ne":
            return field_value != self.value
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "lt":
            return field_value < self.value
        elif self.operator == "gte":
            return field_value >= self.value
        elif self.operator == "lte":
            return field_value <= self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        elif self.operator == "regex":
            return re.search(self.value, str(field_value)) is not None
        elif self.operator == "custom":
            return self._custom_filter(field_value)

        return True

    def _custom_filter(self, field_value: Any) -> bool:
        """Custom filter - to be overridden."""
        return True


class DataTransformer:
    """Base class for data transformers."""

    def transform(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform packet data.

        Args:
            packet: Input packet data.

        Returns:
            Transformed packet data.
        """
        raise NotImplementedError


class FieldTransformer(DataTransformer):
    """Transform specific field values."""

    def __init__(self, field_name: str, transform_func: Callable[[Any], Any]):
        """
        Initialize field transformer.

        Args:
            field_name: Name of field to transform.
            transform_func: Function to apply to field value.
        """
        self.field_name = field_name
        self.transform_func = transform_func

    def transform(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform field value in packet.

        Args:
            packet: Input packet data.

        Returns:
            Packet with transformed field.
        """
        if self.field_name in packet:
            try:
                packet[self.field_name] = self.transform_func(packet[self.field_name])
            except Exception as e:
                logger.error(f"Field transform error: {e}")

        return packet


class ConditionalTransformer(DataTransformer):
    """Conditional transformer based on field values."""

    def __init__(
        self,
        condition: Callable[[Dict[str, Any]], bool],
        transformer: DataTransformer,
    ):
        """
        Initialize conditional transformer.

        Args:
            condition: Condition function to evaluate.
            transformer: Transformer to apply if condition is true.
        """
        self.condition = condition
        self.transformer = transformer

    def transform(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply conditional transformation.

        Args:
            packet: Input packet data.

        Returns:
            Transformed packet or original packet.
        """
        if self.condition(packet):
            return self.transformer.transform(packet)
        return packet


class DataColorizer:
    """Base class for data colorizers."""

    def colorize(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add color information to packet.

        Args:
            packet: Input packet data.

        Returns:
            Packet with color information.
        """
        raise NotImplementedError


class FieldColorizer(DataColorizer):
    """Colorize based on field values."""

    def __init__(self, field_name: str, color_map: Dict[Any, str]):
        """
        Initialize field colorizer.

        Args:
            field_name: Name of field to colorize.
            color_map: Mapping from field values to color strings.
        """
        self.field_name = field_name
        self.color_map = color_map

    def colorize(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add color information to packet based on field value.

        Args:
            packet: Input packet data.

        Returns:
            Packet with color information.
        """
        if self.field_name in packet:
            field_value = packet[self.field_name]
            color = self.color_map.get(field_value, "default")
            packet["_color"] = color
            packet["_color_field"] = self.field_name

        return packet


class RangeColorizer(DataColorizer):
    """Colorize based on field value ranges."""

    def __init__(self, field_name: str, ranges: List[tuple]):
        """
        Initialize range colorizer.

        Args:
            field_name: Name of field to colorize.
            ranges: List of (min_value, max_value, color) tuples.
        """
        self.field_name = field_name
        self.ranges = ranges

    def colorize(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add color information based on value range.

        Args:
            packet: Input packet data.

        Returns:
            Packet with color information.
        """
        if self.field_name not in packet:
            return packet

        field_value = packet[self.field_name]
        color = "default"

        # Find matching range
        for min_val, max_val, range_color in self.ranges:
            if min_val <= field_value <= max_val:
                color = range_color
                break

        packet["_color"] = color
        packet["_color_field"] = self.field_name
        return packet


class BackgroundColorizer(DataColorizer):
    """Colorize based on field values with background color."""

    def __init__(self, field_name: str, background_map: Dict[Any, str]):
        """
        Initialize background colorizer.

        Args:
            field_name: Name of field to colorize.
            background_map: Mapping from field values to background colors.
        """
        self.field_name = field_name
        self.background_map = background_map

    def colorize(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add background color information.

        Args:
            packet: Input packet data.

        Returns:
            Packet with background color information.
        """
        if self.field_name in packet:
            field_value = packet[self.field_name]
            background_color = self.background_map.get(field_value, "default")
            packet["_background_color"] = background_color
            packet["_background_field"] = self.field_name

        return packet


class FunctionFilter(DataFilter):
    """Filter using a function."""

    def __init__(self, filter_func: Callable[[Dict[str, Any]], bool]):
        """
        Initialize function filter.

        Args:
            filter_func: Filter function.
        """
        self.filter_func = filter_func

    def filter(self, packet: Dict[str, Any]) -> bool:
        """Filter packet using function."""
        try:
            return self.filter_func(packet)
        except Exception as e:
            logger.error(f"Function filter error: {e}")
            return False


class FunctionTransformer(DataTransformer):
    """Transform using a function."""

    def __init__(self, transform_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize function transformer.

        Args:
            transform_func: Transform function.
        """
        self.transform_func = transform_func

    def transform(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """Transform packet using function."""
        try:
            return self.transform_func(packet)
        except Exception as e:
            logger.error(f"Function transformer error: {e}")
            return packet


class FunctionColorizer(DataColorizer):
    """Colorize using a function."""

    def __init__(self, colorizer_func: Callable[[Dict[str, Any]], str]):
        """
        Initialize function colorizer.

        Args:
            colorizer_func: Colorizer function.
        """
        self.colorizer_func = colorizer_func

    def colorize(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """Colorize packet using function."""
        try:
            color = self.colorizer_func(packet)
            packet["_color"] = color
            return packet
        except Exception as e:
            logger.error(f"Function colorizer error: {e}")
            return packet


# Predefined filter functions
def create_field_filter(
    field_name: str, value: Any, operator: str = "eq"
) -> FieldFilter:
    """Create a field filter."""
    return FieldFilter(field_name, value, operator)


def create_regex_filter(field_name: str, pattern: str) -> FieldFilter:
    """Create a regex field filter."""
    return FieldFilter(field_name, pattern, operator="regex")


def create_range_filter(field_name: str, min_val: Any, max_val: Any) -> FieldFilter:
    """Create a range field filter."""
    return RangeFilter(field_name, [(min_val, max_val, "green")])


class RangeFilter(DataFilter):
    """Filter based on numeric ranges."""

    def __init__(self, field_name: str, ranges: List[tuple]):
        self.field_name = field_name
        self.ranges = ranges

    def filter(self, packet: Dict[str, Any]) -> bool:
        """Filter based on numeric range."""
        if self.field_name not in packet:
            return False

        field_value = packet[self.field_name]
        if not isinstance(field_value, (int, float)):
            return True  # Non-numeric values are not filtered

        for min_val, max_val, _ in self.ranges:
            if min_val <= field_value <= max_val:
                return True

        return False


# Predefined transformer functions
def create_field_transformer(
    field_name: str, transform_func: Callable[[Any], Any]
) -> FieldTransformer:
    """Create a field transformer."""
    return FieldTransformer(field_name, transform_func)


def create_conditional_transformer(
    condition: Callable[[Dict[str, Any]], bool],
    transformer: DataTransformer,
) -> ConditionalTransformer:
    """Create a conditional transformer."""
    return ConditionalTransformer(condition, transformer)


# Predefined colorizer functions
def create_field_colorizer(
    field_name: str, color_map: Dict[Any, str]
) -> FieldColorizer:
    """Create a field colorizer."""
    return FieldColorizer(field_name, color_map)


def create_status_colorizer(
    field_name: str,
    success_color: str = "green",
    error_color: str = "red",
) -> FieldColorizer:
    """Create a status field colorizer."""
    return FieldColorizer(
        field_name,
        {
            True: success_color,
            False: error_color,
            "success": success_color,
            "error": error_color,
        },
    )


def create_threshold_colorizer(
    field_name: str,
    threshold: float,
    low_color: str = "blue",
    high_color: str = "red",
) -> FieldColorizer:
    """Create a threshold field colorizer."""
    return FieldColorizer(
        field_name, lambda x: low_color if x <= threshold else high_color
    )


# Utility functions
def combine_processors(processors: List[DataProcessor]) -> DataProcessor:
    """
    Combine multiple data processors into one.

    Args:
        processors: List of data processors.

    Returns:
        Combined data processor.
    """
    combined = DataProcessor()
    for processor in processors:
        combined.filters.extend(processor.filters)
        combined.transformers.extend(processor.transformers)
        combined.colorizers.extend(processor.colorizers)

    return combined


def create_packet_processor(
    filters: Optional[List[Callable[[Dict[str, Any]], bool]]] = None,
    transformers: Optional[List[Callable[[Dict[str, Any]], Dict[str, Any]]]] = None,
    colorizers: Optional[List[Callable[[Dict[str, Any]], str]]] = None,
) -> DataProcessor:
    """
    Create a data processor with specified filters, transformers, and colorizers.

    Args:
        filters: List of filters or filter functions.
        transformers: List of transformers or transformer functions.
        colorizers: List of colorizers or colorizer functions.

    Returns:
        Configured data processor.
    """
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


# Example usage and common patterns
def create_cmd_colorizer() -> FieldColorizer:
    """Create colorizer for CMD field with common color mapping."""
    return FieldColorizer(
        "cmd",
        {
            0x10: "blue",
            0x15: "green",
            0x18: "orange",
            0xFF: "red",
        },
    )


def create_length_validator(min_length: int, max_length: int = None) -> DataFilter:
    """Create a length validator filter."""
    return FieldFilter("length", min_length, "gte" if max_length is None else "lte")


def create_data_size_processor(max_size: int = 1000) -> DataProcessor:
    """Create a processor that limits data field size."""
    return create_packet_processor(
        filters=[create_field_filter("data", max_size, "lt")],
        transformers=[
            create_field_transformer(
                "data", lambda x: x[:max_size] if len(x) > max_size else x
            )
        ],
    )


def create_debug_processor() -> DataProcessor:
    """Create a debug processor that adds debugging information."""
    return create_packet_processor(
        transformers=[
            create_field_transformer("raw_data", lambda x: x.hex()),
        ],
        colorizers=[
            FunctionColorizer(lambda p: "lightgray" if p.get("error") else "white")
        ],
    )
