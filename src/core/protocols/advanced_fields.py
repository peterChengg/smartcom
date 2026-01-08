"""
Advanced protocol field definitions support.

This module extends the protocol parser with advanced features:
- Multi-frame protocol support
- Dynamic field definitions
- Field dependencies and relationships
- Conditional field parsing
- Advanced validation rules
- Field transformation support
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Union, Literal

from ..protocol_parser import (
    FieldType,
    ParsedPacket,
    ProtocolDefinition,
    ProtocolField,
    ProtocolParser,
    ParseError,
)

logger = logging.getLogger(__name__)


class MultiFrameField(ProtocolField):
    """
    Advanced field for multi-frame protocols.

    Supports:
    - Frame sequence validation
    - Fragmentation and reassembly
    - Cross-frame dependencies
    - Dynamic length calculation
    """

    def __init__(
        self,
        name: str,
        field_type: FieldType,
        length: int,
        offset: int,
        frame_index: Optional[int] = None,
        total_frames: Optional[int] = None,
        fragment_size: Optional[int] = None,
        frame_sequence: Optional[Callable[[bytes], int]] = None,
        reassembly_timeout: float = 1.0,
        **kwargs,
    ):
        super().__init__(
            name=name,
            field_type=field_type,
            length=length,
            offset=offset,
            **kwargs,
        )

        self.frame_index = frame_index
        self.total_frames = total_frames
        self.fragment_size = fragment_size
        self.frame_sequence = frame_sequence
        self.reassembly_timeout = reassembly_timeout

    @property
    def is_multi_frame(self) -> bool:
        """Check if field is part of multi-frame protocol."""
        return self.total_frames is not None and self.total_frames > 1

    def validate_frame_index(self, frame_data: bytes) -> bool:
        """Validate frame index and sequence."""
        if not self.is_multi_frame:
            return True

        # Validate frame sequence
        if self.frame_sequence:
            expected_index = self.frame_sequence(frame_data)
            if expected_index is not None and expected_index != self.frame_index:
                logger.warning(
                    f"Frame sequence mismatch: expected {expected_index}, got {self.frame_index}"
                )
                return False

        return True


class ConditionalField(ProtocolField):
    """
    Conditional field that appears based on specific conditions.

    Supports:
    - Condition-based field presence
    - Alternative field selection
    - Protocol variant handling
    """

    def __init__(
        self,
        name: str,
        field_type: FieldType,
        length: int,
        offset: int,
        condition: Callable[[bytes, Dict[str, Any]], bool],
        alternative_fields: Optional[List["ConditionalField"]] = None,
        protocol_variant: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            field_type=field_type,
            length=length,
            offset=offset,
            required=False,  # Conditional fields are not required by default
            **kwargs,
        )

        self.condition = condition
        self.alternative_fields = alternative_fields or []
        self.protocol_variant = protocol_variant

    def should_appear(self, packet_data: bytes, context: Dict[str, Any]) -> bool:
        """Check if field should appear in packet."""
        return self.condition(packet_data, context)

    def get_active_field(
        self, packet_data: bytes, context: Dict[str, Any]
    ) -> Optional["ConditionalField"]:
        """Get the active conditional field."""
        if self.should_appear(packet_data, context):
            return self

        for field in self.alternative_fields:
            if field.should_appear(packet_data, context):
                return field

        return None


class DynamicField(ProtocolField):
    """
    Dynamic field with runtime length and position calculation.

    Supports:
    - Runtime field length calculation
    - Dynamic offset calculation based on other fields
    - Field value dependencies
    - Conditional field presence
    """

    def __init__(
        self,
        name: str,
        field_type: FieldType,
        length: int,
        offset: int,
        length_spec: Optional[Union[int, str, Callable[[bytes], int]]] = None,
        offset_spec: Optional[Union[int, str, Callable[[bytes], int]]] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            field_type=field_type,
            length=length,
            offset=offset,
            **kwargs,
        )

        self._length_spec = length_spec
        self._offset_spec = offset_spec

    def calculate_length(self, data: bytes, context: Dict[str, Any]) -> int:
        """Calculate dynamic field length."""
        if isinstance(self._length_spec, int):
            return self._length_spec
        elif isinstance(self._length_spec, str):
            # Reference to another field
            return int(context.get(self._length_spec, self.length))
        elif callable(self._length_spec):
            return self._length_spec(data)
        else:
            return self.length

    def calculate_offset(self, data: bytes, context: Dict[str, Any]) -> int:
        """Calculate dynamic field offset."""
        if isinstance(self._offset_spec, int):
            return self._offset_spec
        elif isinstance(self._offset_spec, str):
            # Reference to another field
            return int(context.get(self._offset_spec, self.offset))
        elif callable(self._offset_spec):
            return self._offset_spec(data)
        else:
            return self.offset

    def should_parse(self, data: bytes, context: Dict[str, Any]) -> bool:
        """Check if field should be parsed based on context."""
        return True  # Dynamic fields are parsed by default


class TransformationField(ProtocolField):
    """
    Field with built-in transformation support.

    Supports:
    - Bit field extraction
    - Endianness conversion
    - Scale and offset operations
    - Custom transformations
    """

    def __init__(
        self,
        name: str,
        field_type: FieldType,
        length: int,
        offset: int,
        bit_offset: Optional[int] = None,
        bit_length: Optional[int] = None,
        endianess: str = "big",
        scale: float = 1.0,
        offset_value: float = 0.0,
        transform: Optional[Callable[[bytes], Any]] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            field_type=field_type,
            length=length,
            offset=offset,
            **kwargs,
        )

        self.bit_offset = bit_offset
        self.bit_length = bit_length
        self.endianess = endianess.lower()
        self.scale = scale
        self.offset_value = offset_value
        self.transform = transform

    def extract_value(self, field_data: bytes) -> Any:
        """Extract and transform field value."""
        value = field_data

        # Apply bit field extraction
        if self.bit_offset is not None:
            byteorder: Literal["big", "little"] = "big"
            if self.endianess == "little":
                byteorder = "little"
            bit_value = int.from_bytes(field_data, byteorder=byteorder)
            mask = (1 << self.bit_length) - 1 if self.bit_length else (1 << 32) - 1
            value = (bit_value >> self.bit_offset) & mask
        else:
            value = field_data

        # Apply custom transformation
        if self.transform:
            # Ensure we pass bytes to transform function
            transform_input = value if isinstance(value, bytes) else field_data
            value = self.transform(transform_input)

        # Apply scale and offset (only to numeric values)
        if isinstance(value, (int, float)):
            if self.scale != 1.0:
                value = value * self.scale
            if self.offset_value != 0.0:
                value = value + self.offset_value

        return value

    @property
    def is_bit_field(self) -> bool:
        """Check if field is a bit field."""
        return self.bit_offset is not None


class AdvancedProtocolDefinition(ProtocolDefinition):
    """
    Advanced protocol definition with enhanced field support.

    Extends ProtocolDefinition to support:
    - Multi-frame protocols
    - Dynamic field definitions
    - Field dependencies and transformations
    - Conditional field parsing
    - Advanced validation rules
    """

    def __init__(
        self,
        name: str,
        fields: List[ProtocolField],
        field_dependencies: Optional[Dict[str, List[str]]] = None,
        dynamic_calculation: Optional[Callable[[bytes], Dict[str, Any]]] = None,
        variant_detection: Optional[Callable[[bytes], str]] = None,
        **kwargs,
    ):
        super().__init__(name=name, fields=fields, **kwargs)

        self.field_dependencies = field_dependencies or {}
        self.dynamic_calculation = dynamic_calculation
        self.variant_detection = variant_detection

        # Enhance field processing
        self._enhance_fields()

    def _enhance_fields(self) -> None:
        """Process advanced field features."""
        enhanced_fields = []
        for field in self.fields:
            if isinstance(
                field,
                (MultiFrameField, DynamicField, ConditionalField, TransformationField),
            ):
                enhanced_fields.append(field)
            else:
                # Wrap regular fields with enhanced capabilities
                enhanced_field = self._wrap_field(field)
                enhanced_fields.append(enhanced_field)

        self.fields = enhanced_fields

    def _wrap_field(self, field: ProtocolField) -> ProtocolField:
        """Wrap regular field with transformation capabilities."""
        # Convert regular fields to transformation fields for consistency
        if field.field_type != FieldType.DATA:
            return field  # Non-data fields don't need transformation
        else:
            return TransformationField(
                name=field.name,
                field_type=field.field_type,
                length=field.length,
                offset=field.offset,
                description=field.description,
                validation=field.validation,
                required=field.required,
                default_value=field.default_value,
            )

    def detect_variant(self, packet_data: bytes) -> Optional[str]:
        """Detect protocol variant from packet data."""
        if self.variant_detection:
            try:
                return self.variant_detection(packet_data)
            except Exception as e:
                logger.error(f"Variant detection failed: {e}")
                return None

        return None

    def calculate_dynamic_fields(self, packet_data: bytes) -> Dict[str, Any]:
        """Calculate dynamic field properties."""
        if not self.dynamic_calculation:
            return {}

        try:
            return self.dynamic_calculation(packet_data)
        except Exception as e:
            logger.error(f"Dynamic calculation failed: {e}")
            return {}

    def validate_dependencies(self, parsed_fields: Dict[str, Any]) -> List[str]:
        """Validate field dependencies."""
        errors = []
        for field_name, dependencies in self.field_dependencies.items():
            if field_name not in parsed_fields:
                errors.append(f"Field '{field_name}' not found but has dependencies")
                continue

            for dependency in dependencies:
                if dependency not in parsed_fields:
                    errors.append(
                        f"Field '{field_name}' depends on '{dependency}' which is missing"
                    )

        return errors


class AdvancedProtocolParser(ProtocolParser):
    """
    Advanced protocol parser with multi-frame and dynamic field support.

    Extends ProtocolParser with:
    - Multi-frame protocol parsing
    - Dynamic field calculation
    - Conditional field parsing
    - Field transformation
    - Variant detection
    - Dependency validation
    """

    def __init__(self, protocol: AdvancedProtocolDefinition):
        super().__init__(protocol)

        self.frame_buffer: Dict[
            int, List[bytes]
        ] = {}  # Buffer for incomplete multi-frame packets
        self.current_variant: Optional[str] = None
        self.reassembly_timeout = protocol.parse_timeout

    async def parse_data(self, data: bytes) -> Optional[ParsedPacket]:
        """Parse data with advanced protocol support."""
        # Store protocol as advanced type to access its methods
        advanced_protocol: AdvancedProtocolDefinition = self.protocol  # type: ignore

        # Detect protocol variant
        variant = advanced_protocol.detect_variant(data)
        if variant != self.current_variant:
            self.current_variant = variant
            logger.info(f"Protocol variant detected: {variant}")
            self.reset()

        # Calculate dynamic fields
        dynamic_context = advanced_protocol.calculate_dynamic_fields(data)

        # Use enhanced parsing for multi-frame and dynamic fields
        return await self._advanced_parse(data, dynamic_context)

    async def _advanced_parse(
        self, data: bytes, dynamic_context: Dict[str, Any]
    ) -> Optional[ParsedPacket]:
        """Advanced parsing with multi-frame and dynamic field support."""
        try:
            # Handle multi-frame protocols
            if self._has_multi_frame_fields():
                return await self._parse_multi_frame(data, dynamic_context)

            # Handle dynamic fields
            if self._has_dynamic_fields():
                return await self._parse_dynamic_fields(data, dynamic_context)

            # Handle conditional fields
            if self._has_conditional_fields():
                return await self._parse_conditional_fields(data, dynamic_context)

            # Standard parsing with transformation
            return await self._parse_with_transformation(data, dynamic_context)

        except Exception as e:
            logger.error(f"Advanced parsing failed: {e}")
            return None

    def _has_multi_frame_fields(self) -> bool:
        """Check if protocol has multi-frame fields."""
        return any(isinstance(field, MultiFrameField) for field in self.protocol.fields)

    def _has_dynamic_fields(self) -> bool:
        """Check if protocol has dynamic fields."""
        return any(isinstance(field, DynamicField) for field in self.protocol.fields)

    def _has_conditional_fields(self) -> bool:
        """Check if protocol has conditional fields."""
        return any(
            isinstance(field, ConditionalField) for field in self.protocol.fields
        )

    async def _parse_multi_frame(
        self, data: bytes, dynamic_context: Dict[str, Any]
    ) -> Optional[ParsedPacket]:
        """Parse multi-frame protocol."""
        # Extract frame information
        frame_fields = [
            field
            for field in self.protocol.fields
            if isinstance(field, MultiFrameField)
        ]

        # Buffer and reassembly logic
        for frame_field in frame_fields:
            frame_index = frame_field.frame_index
            if frame_index is None:
                continue

            # Buffer the frame
            if frame_index not in self.frame_buffer:
                self.frame_buffer[frame_index] = []

            self.frame_buffer[frame_index].append(data)

            # Check if reassembly is complete
            if self._is_frame_sequence_complete(frame_field):
                packet_data = b"".join(self.frame_buffer[frame_index])
                del self.frame_buffer[frame_index]
                result = await self._parse_complete_packet(packet_data, dynamic_context)
                return result

        return None

    async def _parse_dynamic_fields(
        self, data: bytes, dynamic_context: Dict[str, Any]
    ) -> Optional[ParsedPacket]:
        """Parse protocol with dynamic fields."""
        # Calculate dynamic field properties
        fields = {}
        context = {"dynamic": dynamic_context}

        for field in self.protocol.fields:
            if isinstance(field, DynamicField):
                # Check if field should be parsed
                if not field.should_parse(data, context):
                    continue

                # Calculate dynamic length and offset
                length = field.calculate_length(data, context)
                offset = field.calculate_offset(data, context)

                # Extract field data
                if offset + length <= len(data):
                    field_data = data[offset : offset + length]
                    fields[field.name] = field_data

        # Parse remaining static fields
        static_packet = await super().parse_data(data)
        if static_packet:
            fields.update(static_packet.fields)

        return ParsedPacket(
            raw_data=data,
            fields=fields,
            timestamp=static_packet.timestamp if static_packet else 0,
            parse_time=0,
            is_valid=True,
        )

    async def _parse_conditional_fields(
        self, data: bytes, dynamic_context: Dict[str, Any]
    ) -> Optional[ParsedPacket]:
        """Parse protocol with conditional fields."""
        # Evaluate conditions and determine active fields
        active_fields: List[ProtocolField] = []
        context = {"dynamic": dynamic_context}

        for field in self.protocol.fields:
            if isinstance(field, ConditionalField):
                active_field = field.get_active_field(data, context)
                if active_field:
                    active_fields.append(active_field)
            else:
                active_fields.append(field)  # Use base field

        # Create temporary protocol with active fields
        temp_protocol = AdvancedProtocolDefinition(
            name=self.protocol.name,
            fields=active_fields,
        )

        # Parse with temporary protocol
        temp_parser = AdvancedProtocolParser(temp_protocol)
        return await temp_parser.parse_data(data)

    async def _parse_with_transformation(
        self, data: bytes, dynamic_context: Dict[str, Any]
    ) -> Optional[ParsedPacket]:
        """Parse with field transformations."""
        # Standard parsing first
        packet = await super().parse_data(data)
        if not packet:
            return None

        # Apply transformations
        transformed_fields = {}
        for field in self.protocol.fields:
            if isinstance(field, TransformationField) and field.name in packet.fields:
                field_data = packet.fields[field.name]
                if isinstance(field_data, bytes):
                    transformed_fields[field.name] = field.extract_value(field_data)
                else:
                    transformed_fields[field.name] = field_data
            else:
                transformed_fields[field.name] = packet.fields[field.name]

        # Update packet with transformed fields
        packet.fields = transformed_fields
        return packet

    def _is_frame_sequence_complete(self, frame_field: MultiFrameField) -> bool:
        """Check if frame sequence is complete."""
        frame_index = frame_field.frame_index
        total_frames = frame_field.total_frames

        if frame_index is None or total_frames is None:
            return False

        return len(self.frame_buffer.get(frame_index, [])) == total_frames

    async def _parse_complete_packet(
        self, packet_data: bytes, dynamic_context: Dict[str, Any]
    ) -> Optional[ParsedPacket]:
        """Parse complete reassembled packet."""
        # Create temporary protocol without multi-frame fields
        temp_fields = []
        for field in self.protocol.fields:
            if not isinstance(field, MultiFrameField):
                temp_fields.append(field)

        temp_protocol = ProtocolDefinition(
            name=self.protocol.name,
            fields=temp_fields,
            head_pattern=self.protocol.head_pattern,
            min_length=self.protocol.min_length,
            max_length=self.protocol.max_length,
            checksum_type=self.protocol.checksum_type,
            encryption=self.protocol.encryption,
            custom_validation=self.protocol.custom_validation,
            parse_timeout=self.protocol.parse_timeout,
        )

        temp_parser = ProtocolParser(temp_protocol)
        return await temp_parser.parse_data(packet_data)

    def reset(self) -> None:
        """Reset advanced parser state."""
        super().reset()
        self.frame_buffer.clear()
        self.current_variant = None


# Factory functions for creating advanced field instances
def create_multi_frame_field(
    name: str,
    field_type: FieldType,
    length: int,
    offset: int,
    **kwargs,
) -> MultiFrameField:
    """Create a multi-frame field."""
    return MultiFrameField(name, field_type, length, offset, **kwargs)


def create_dynamic_field(
    name: str,
    field_type: FieldType,
    length: int,
    offset: int,
    **kwargs,
) -> DynamicField:
    """Create a dynamic field."""
    return DynamicField(name, field_type, length, offset, **kwargs)


def create_conditional_field(
    name: str,
    field_type: FieldType,
    length: int,
    offset: int,
    condition: Callable[[bytes, Dict[str, Any]], bool],
    **kwargs,
) -> ConditionalField:
    """Create a conditional field."""
    return ConditionalField(
        name, field_type, length, offset, condition=condition, **kwargs
    )


def create_transformation_field(
    name: str,
    field_type: FieldType,
    length: int,
    offset: int,
    **kwargs,
) -> TransformationField:
    """Create a transformation field."""
    return TransformationField(name, field_type, length, offset, **kwargs)
