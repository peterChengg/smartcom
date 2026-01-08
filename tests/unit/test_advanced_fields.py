"""
Tests for advanced protocol fields.
"""

import pytest
from src.core.protocol_parser import FieldType, ProtocolDefinition, ProtocolField
from src.core.protocols.advanced_fields import (
    AdvancedProtocolDefinition,
    AdvancedProtocolParser,
    ConditionalField,
    DynamicField,
    MultiFrameField,
    TransformationField,
    create_multi_frame_field,
    create_dynamic_field,
    create_conditional_field,
    create_transformation_field,
)


class TestMultiFrameField:
    """Test MultiFrameField functionality."""

    def test_multi_frame_field_creation(self):
        """Test creating a multi-frame field."""
        field = MultiFrameField(
            name="data",
            field_type=FieldType.DATA,
            length=100,
            offset=4,
            frame_index=0,
            total_frames=3,
        )

        assert field.name == "data"
        assert field.frame_index == 0
        assert field.total_frames == 3
        assert field.is_multi_frame is True

    def test_single_frame_field(self):
        """Test single frame field."""
        field = MultiFrameField(
            name="data",
            field_type=FieldType.DATA,
            length=100,
            offset=4,
        )

        assert field.is_multi_frame is False
        assert field.validate_frame_index(b"test") is True


class TestDynamicField:
    """Test DynamicField functionality."""

    def test_dynamic_field_creation(self):
        """Test creating a dynamic field."""
        field = DynamicField(
            name="length",
            field_type=FieldType.LENGTH,
            length=2,
            offset=2,
            length_spec=lambda data: len(data),
        )

        assert field.name == "length"
        assert field._length_spec is not None

    def test_calculate_length_with_spec(self):
        """Test dynamic length calculation."""
        field = DynamicField(
            name="length",
            field_type=FieldType.LENGTH,
            length=2,
            offset=2,
            length_spec=lambda data: len(data),
        )

        data = b"test data"
        context = {}
        length = field.calculate_length(data, context)
        assert length == 9

    def test_calculate_offset_with_spec(self):
        """Test dynamic offset calculation."""
        field = DynamicField(
            name="payload",
            field_type=FieldType.DATA,
            length=10,
            offset=4,
            offset_spec=lambda data: 8,
        )

        data = b"test data"
        context = {}
        offset = field.calculate_offset(data, context)
        assert offset == 8


class TestConditionalField:
    """Test ConditionalField functionality."""

    def test_conditional_field_creation(self):
        """Test creating a conditional field."""
        condition = lambda data, ctx: data[0] == 0xAA
        field = ConditionalField(
            name="optional",
            field_type=FieldType.DATA,
            length=4,
            offset=4,
            condition=condition,
        )

        assert field.name == "optional"
        assert callable(field.condition)

    def test_should_appear(self):
        """Test field appearance condition."""
        condition = lambda data, ctx: data[0] == 0xAA
        field = ConditionalField(
            name="optional",
            field_type=FieldType.DATA,
            length=4,
            offset=4,
            condition=condition,
        )

        # Should appear with matching data
        assert field.should_appear(b"\xaa\x01\x02\x03", {}) is True

        # Should not appear with non-matching data
        assert field.should_appear(b"\xbb\x01\x02\x03", {}) is False


class TestTransformationField:
    """Test TransformationField functionality."""

    def test_transformation_field_creation(self):
        """Test creating a transformation field."""
        field = TransformationField(
            name="value",
            field_type=FieldType.DATA,
            length=4,
            offset=4,
            scale=2.0,
            offset_value=10.0,
        )

        assert field.name == "value"
        assert field.scale == 2.0
        assert field.offset_value == 10.0

    def test_bit_field_extraction(self):
        """Test bit field extraction."""
        field = TransformationField(
            name="flags",
            field_type=FieldType.DATA,
            length=1,
            offset=0,
            bit_offset=4,
            bit_length=4,
        )

        # Extract bits 4-7 from byte 0xAB (10101011)
        # With big endian: 0xAB = 171 decimal = 10101011 binary
        # Bits 4-7 (counting from 0) should be 1010 = 10 decimal
        data = b"\xab"
        result = field.extract_value(data)
        assert result == 10

    def test_scale_and_offset(self):
        """Test scale and offset transformation."""
        # Since transformation only applies to numeric values,
        # we need to test with bit field extraction first
        field_with_bits = TransformationField(
            name="value",
            field_type=FieldType.DATA,
            length=2,
            offset=2,
            bit_offset=0,
            bit_length=16,  # Extract 16 bits
            endianess="little",  # Use little endian for expected value
            scale=2.0,
            offset_value=10.0,
        )

        data = b"\x05\x00"  # 5 in little endian
        result = field_with_bits.extract_value(data)
        assert result == 20.0  # (5 * 2.0) + 10.0

    def test_custom_transform(self):
        """Test custom transformation."""

        def hex_transform(data):
            return data.hex().upper()

        field = TransformationField(
            name="hex_value",
            field_type=FieldType.DATA,
            length=4,
            offset=0,
            transform=hex_transform,
        )

        data = b"\xde\xad\xbe\xef"
        result = field.extract_value(data)
        assert result == "DEADBEEF"


class TestAdvancedProtocolDefinition:
    """Test AdvancedProtocolDefinition functionality."""

    def test_advanced_protocol_creation(self):
        """Test creating an advanced protocol definition."""
        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0),
            DynamicField("length", FieldType.LENGTH, 2, 2),
            TransformationField("value", FieldType.DATA, 4, 4, scale=1.5),
        ]

        protocol = AdvancedProtocolDefinition(
            name="test_protocol",
            fields=fields,
            field_dependencies={"value": ["length"]},
        )

        assert protocol.name == "test_protocol"
        assert len(protocol.fields) == 3
        assert protocol.field_dependencies == {"value": ["length"]}

    def test_variant_detection(self):
        """Test protocol variant detection."""

        def detect_variant(data: bytes) -> str:
            if data[0] == 0xAA:
                return "variant_a"
            elif data[0] == 0xBB:
                return "variant_b"
            return "unknown"

        protocol = AdvancedProtocolDefinition(
            name="test_protocol",
            fields=[],
            variant_detection=detect_variant,
        )

        assert protocol.detect_variant(b"\xaa\x01") == "variant_a"
        assert protocol.detect_variant(b"\xbb\x01") == "variant_b"
        # When no variant matches, the function still returns a string
        assert protocol.detect_variant(b"\xcc\x01") == "unknown"

    def test_dynamic_calculation(self):
        """Test dynamic field calculation."""

        def calculate_fields(data):
            return {"dynamic_length": len(data), "checksum": sum(data) % 256}

        protocol = AdvancedProtocolDefinition(
            name="test_protocol",
            fields=[],
            dynamic_calculation=calculate_fields,
        )

        result = protocol.calculate_dynamic_fields(b"test")
        assert result["dynamic_length"] == 4
        assert result["checksum"] == sum(b"test") % 256


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_multi_frame_field(self):
        """Test creating multi-frame field with factory."""
        field = create_multi_frame_field(
            name="data",
            field_type=FieldType.DATA,
            length=100,
            offset=4,
            frame_index=0,
            total_frames=3,
        )

        assert isinstance(field, MultiFrameField)
        assert field.frame_index == 0

    def test_create_dynamic_field(self):
        """Test creating dynamic field with factory."""
        field = create_dynamic_field(
            name="length",
            field_type=FieldType.LENGTH,
            length=2,
            offset=2,
            length_spec=lambda data: len(data),
        )

        assert isinstance(field, DynamicField)
        assert field._length_spec is not None

    def test_create_conditional_field(self):
        """Test creating conditional field with factory."""
        condition = lambda data, ctx: data[0] == 0xAA
        field = create_conditional_field(
            name="optional",
            field_type=FieldType.DATA,
            length=4,
            offset=4,
            condition=condition,
        )

        assert isinstance(field, ConditionalField)
        assert callable(field.condition)

    def test_create_transformation_field(self):
        """Test creating transformation field with factory."""
        field = create_transformation_field(
            name="value",
            field_type=FieldType.DATA,
            length=4,
            offset=4,
            scale=2.0,
        )

        assert isinstance(field, TransformationField)
        assert field.scale == 2.0


if __name__ == "__main__":
    pytest.main([__file__])
