"""
Protocol parsing and validation.

This module provides configurable protocol parsing capabilities
for custom serial communication protocols.
"""

import asyncio
import logging
import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import crcmod

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Protocol field types."""

    HEAD = "head"
    LENGTH = "length"
    CMD = "cmd"
    SEQ = "seq"
    DATA = "data"
    CHECKSUM = "checksum"


class ParseState(Enum):
    """Parser state machine states."""

    IDLE = "idle"
    WAITING_FOR_HEAD = "waiting_for_head"
    PARSING_HEADER = "parsing_header"
    PARSING_LENGTH = "parsing_length"
    PARSING_DATA = "parsing_data"
    PARSING_CHECKSUM = "parsing_checksum"
    COMPLETE = "complete"
    ERROR = "error"


class ParseError(Exception):
    """Protocol parsing error."""

    pass


class ValidationError(ParseError):
    """Protocol validation error."""

    pass


@dataclass
class ProtocolField:
    """Protocol field definition."""

    name: str
    field_type: FieldType
    length: int
    offset: int
    description: str = ""
    validation: Optional[str] = None
    required: bool = True
    default_value: Any = None


@dataclass
class ProtocolDefinition:
    """Protocol structure definition."""

    name: str
    fields: List[ProtocolField]
    head_pattern: Optional[bytes] = None
    min_length: int = 0
    max_length: int = 1024
    checksum_type: str = "none"  # none, crc16, crc32, xor, sum
    encryption: Optional[Dict[str, Any]] = None
    custom_validation: Optional[List[Dict[str, Any]]] = None
    parse_timeout: float = 0.5


@dataclass
class ParsedPacket:
    """Successfully parsed protocol packet."""

    raw_data: bytes
    fields: Dict[str, Any]
    timestamp: float
    parse_time: float
    is_valid: bool
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "raw_data": self.raw_data.hex(),
            "fields": self.fields,
            "timestamp": self.timestamp,
            "parse_time": self.parse_time,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


class ProtocolParser:
    """
    Configurable protocol parser with real-time frame identification.

    Features:
    - Real-time frame detection and segmentation
    - Configurable protocol structures
    - Timeout management
    - Checksum validation
    - Custom validation support
    """

    def __init__(self, protocol: ProtocolDefinition):
        self.protocol = protocol
        self.buffer = bytearray()
        self.last_data_time = 0.0
        self.timeout = protocol.parse_timeout * 1000  # Convert to ms
        self.state = ParseState.IDLE
        self.packets: List[ParsedPacket] = []
        self.stats: Dict[str, Any] = {
            "total_bytes": 0,
            "parsed_packets": 0,
            "parse_errors": 0,
            "parse_time_ms": 0.0,
        }

    async def parse_data(self, data: bytes) -> Optional[ParsedPacket]:
        """
        Parse incoming data according to protocol definition.

        Args:
            data: Raw bytes to parse.

        Returns:
            ParsedPacket if a complete packet is found, None otherwise.
        """
        # Allow empty data input to trigger processing of existing buffer
        if data:
            self.buffer.extend(data)
            self.last_data_time = time.time()
            self.stats["total_bytes"] += len(data)

        # Try to extract complete packets - keep processing until no more packets can be extracted
        max_iterations = 100  # Prevent infinite loops
        iteration = 0
        prev_buffer_size = len(self.buffer)
        prev_state = self.state

        while iteration < max_iterations:
            iteration += 1

            # Check for timeout before processing
            if self._is_timeout():
                self._handle_timeout()
                return None

            # Try to extract packet
            packet = await self._try_extract_packet()

            if packet is not None:
                # Successfully extracted a packet
                self.packets.append(packet)
                self.stats["parsed_packets"] += 1
                return packet

            # Check if we should stop processing
            # Stop if we're in a waiting state and don't have enough data
            if self.state in [
                ParseState.WAITING_FOR_HEAD,
                ParseState.PARSING_HEADER,
                ParseState.PARSING_LENGTH,
                ParseState.PARSING_DATA,
            ]:
                # Check if we have minimum required data
                min_required = self._get_minimum_required_data()
                if len(self.buffer) < min_required:
                    break

            # Check if we made progress
            current_buffer_size = len(self.buffer)
            current_state = self.state

            if current_buffer_size < prev_buffer_size:
                # Made progress (consumed data)
                prev_buffer_size = current_buffer_size
                prev_state = current_state
                continue

            if current_state != prev_state:
                # State changed, continue processing
                prev_state = current_state
                continue

            # No progress made, stop
            break

        return None

    async def _try_extract_packet(self) -> Optional[ParsedPacket]:
        """
        Try to extract a complete packet from buffer.

        Returns:
            ParsedPacket if complete packet found, None otherwise.
        """
        if not self.buffer:
            return None

        # State machine for parsing
        if self.state == ParseState.IDLE:
            return await self._state_idle()
        elif self.state == ParseState.WAITING_FOR_HEAD:
            return await self._state_waiting_for_head()
        elif self.state == ParseState.PARSING_HEADER:
            return await self._state_parsing_header()
        elif self.state == ParseState.PARSING_LENGTH:
            return await self._state_parsing_length()
        elif self.state == ParseState.PARSING_DATA:
            return await self._state_parsing_data()
        elif self.state == ParseState.PARSING_CHECKSUM:
            return await self._state_parsing_checksum()

        return None

    async def _state_idle(self) -> Optional[ParsedPacket]:
        """Idle state - look for head pattern."""
        if not self.protocol.head_pattern:
            # No head pattern, try to parse immediately
            self.state = ParseState.PARSING_LENGTH
            return None

        # Look for head pattern in buffer
        head_index = self.buffer.find(self.protocol.head_pattern)
        if head_index == -1:
            # Head not found, discard data up to last potential head position
            if len(self.buffer) > len(self.protocol.head_pattern):
                keep_bytes = len(self.protocol.head_pattern) - 1
                self.buffer = self.buffer[-keep_bytes:]
            self.state = ParseState.WAITING_FOR_HEAD
            return None

        # Remove data before head
        if head_index > 0:
            self.buffer = self.buffer[head_index:]

        self.state = ParseState.PARSING_HEADER
        return None

    async def _state_waiting_for_head(self) -> Optional[ParsedPacket]:
        """Wait for head pattern."""
        if not self.protocol.head_pattern:
            self.state = ParseState.PARSING_LENGTH
            return None

        if self.buffer.startswith(self.protocol.head_pattern):
            self.state = ParseState.PARSING_HEADER
        else:
            # Remove first byte and continue waiting
            self.buffer = self.buffer[1:]

        return None

    async def _state_parsing_header(self) -> Optional[ParsedPacket]:
        """Parse header fields."""
        if self.protocol.head_pattern and not self.buffer.startswith(
            self.protocol.head_pattern
        ):
            self.state = ParseState.WAITING_FOR_HEAD
            return None

        # Check if we have minimum data for header
        header_fields = [
            f for f in self.protocol.fields if f.field_type in [FieldType.HEAD]
        ]
        min_header_size = max([(f.offset + f.length) for f in header_fields], default=0)

        if len(self.buffer) < min_header_size:
            return None

        self.state = ParseState.PARSING_LENGTH
        return None

    async def _state_parsing_length(self) -> Optional[ParsedPacket]:
        """Parse length field."""
        # Find length field
        length_field = next(
            (f for f in self.protocol.fields if f.field_type == FieldType.LENGTH),
            None,
        )

        if length_field is None:
            # No length field, use fixed length or timeout
            self.state = ParseState.PARSING_DATA
            return None

        # Check if we have enough data for length field
        if len(self.buffer) < length_field.offset + length_field.length:
            return None

        # Extract length
        length_bytes = bytes(
            self.buffer[length_field.offset : length_field.offset + length_field.length]
        )
        packet_length = self._extract_int(length_bytes)

        # Validate length
        if (
            packet_length < self.protocol.min_length
            or packet_length > self.protocol.max_length
        ):
            logger.warning(f"Invalid packet length: {packet_length}")
            self.stats["parse_errors"] += 1
            self.buffer = self.buffer[1:]  # Skip first byte
            self.state = ParseState.WAITING_FOR_HEAD
            return None

        # Store expected packet length
        self._expected_packet_length = packet_length
        self.state = ParseState.PARSING_DATA
        return None

    async def _state_parsing_data(self) -> Optional[ParsedPacket]:
        """Parse data fields."""
        # Calculate expected total packet length
        total_length = self._calculate_total_packet_length()

        # Check if we have complete packet
        if len(self.buffer) < total_length:
            return None

        # Extract complete packet
        packet_data = bytes(self.buffer[:total_length])
        self.buffer = self.buffer[total_length:]

        # Try to parse packet fields
        try:
            packet = await self._parse_packet(packet_data)
            self.state = ParseState.IDLE
            return packet
        except ParseError as e:
            logger.warning(f"Parse error: {e}, resetting buffer")
            self.stats["parse_errors"] += 1
            self.buffer.clear()
            self.state = ParseState.WAITING_FOR_HEAD
            return None

    async def _state_parsing_checksum(self) -> Optional[ParsedPacket]:
        """Parse and validate checksum."""
        # This is handled in _parse_packet
        self.state = ParseState.PARSING_DATA
        return None

    async def _parse_packet(self, packet_data: bytes) -> ParsedPacket:
        """
        Parse a complete packet and extract fields.

        Args:
            packet_data: Complete packet data.

        Returns:
            ParsedPacket with extracted fields.

        Raises:
            ParseError: If parsing fails.
        """
        start_time = time.time()
        fields: Dict[str, Any] = {}
        validation_errors: List[str] = []

        # Extract all fields
        for proto_field in self.protocol.fields:
            if proto_field.offset + proto_field.length > len(packet_data):
                if proto_field.required:
                    raise ParseError(
                        f"Field {proto_field.name} extends beyond packet boundary"
                    )
                fields[proto_field.name] = proto_field.default_value
                continue

            # Parse based on field type
            try:
                field_data = bytes(
                    packet_data[
                        proto_field.offset : proto_field.offset + proto_field.length
                    ]
                )
                value = self._parse_field_value(proto_field, field_data)
                fields[proto_field.name] = value
            except Exception as e:
                if proto_field.required:
                    raise ParseError(f"Failed to parse field {proto_field.name}: {e}")
                fields[proto_field.name] = proto_field.default_value

        # Validate packet
        is_valid = True
        if self.protocol.checksum_type != "none":
            if not self._validate_checksum(packet_data, fields):
                is_valid = False
                validation_errors.append("Checksum validation failed")

        # Run custom validation
        if self.protocol.custom_validation:
            custom_valid = self._run_custom_validation(fields)
            if not custom_valid:
                is_valid = False
                validation_errors.append("Custom validation failed")

        parse_time = (time.time() - start_time) * 1000  # Convert to ms
        self.stats["parse_time_ms"] += parse_time

        return ParsedPacket(
            raw_data=packet_data,
            fields=fields,
            timestamp=time.time(),
            parse_time=parse_time,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )

    def _parse_field_value(self, field: ProtocolField, data: bytes) -> Any:
        """
        Parse field value from bytes.

        Args:
            field: Field definition.
            data: Field data bytes.

        Returns:
            Parsed field value.
        """
        # For DATA fields, always return as bytes
        if field.field_type == FieldType.DATA:
            return data

        # Parse other field types based on length
        if field.length == 1:
            return data[0]
        elif field.length == 2:
            return struct.unpack(">H", data)[0]
        elif field.length == 4:
            return struct.unpack(">I", data)[0]
        elif field.length == 8:
            return struct.unpack(">Q", data)[0]
        else:
            # Return as bytes for other lengths
            return data

    def _calculate_total_packet_length(self) -> int:
        """Calculate expected total packet length."""
        if hasattr(self, "_expected_packet_length"):
            return self._expected_packet_length

        # Calculate from field definitions
        max_offset = 0
        for proto_field in self.protocol.fields:
            offset = proto_field.offset + proto_field.length
            if offset > max_offset:
                max_offset = offset

        return max_offset

    def _validate_checksum(self, packet_data: bytes, fields: Dict[str, Any]) -> bool:
        """
        Validate packet checksum.

        Args:
            packet_data: Complete packet data.
            fields: Parsed fields.

        Returns:
            True if checksum is valid.
        """
        checksum_field = next(
            (f for f in self.protocol.fields if f.field_type == FieldType.CHECKSUM),
            None,
        )

        if checksum_field is None:
            return True

        # Extract checksum from packet
        checksum_data = bytes(
            packet_data[
                checksum_field.offset : checksum_field.offset + checksum_field.length
            ]
        )

        # Calculate expected checksum
        data_without_checksum = (
            packet_data[: checksum_field.offset]
            + packet_data[checksum_field.offset + checksum_field.length :]
        )

        calculated_checksum = self._calculate_checksum(data_without_checksum)

        # Compare
        if len(checksum_data) == 1:
            return bool(calculated_checksum == checksum_data[0])
        elif len(checksum_data) == 2:
            return bool(calculated_checksum == struct.unpack(">H", checksum_data)[0])
        elif len(checksum_data) == 4:
            return bool(calculated_checksum == struct.unpack(">I", checksum_data)[0])

        return False

    def _calculate_checksum(self, data: bytes) -> int:
        """
        Calculate checksum based on protocol configuration.

        Args:
            data: Data to calculate checksum for.

        Returns:
            Checksum value.
        """
        checksum_type = self.protocol.checksum_type.lower()

        if checksum_type == "crc16":
            crc_func = crcmod.mkCrcFun(0x11021, initCrc=0, rev=False)
            return int(crc_func(data))
        elif checksum_type == "crc32":
            import zlib

            return int(zlib.crc32(data) & 0xFFFFFFFF)
        elif checksum_type == "xor":
            checksum = 0
            for byte in data:
                checksum ^= byte
            return checksum
        elif checksum_type == "sum":
            return int(sum(data) & 0xFF)
        else:
            return 0

    def _run_custom_validation(self, fields: Dict[str, Any]) -> bool:
        """
        Run custom validation logic.

        Args:
            fields: Parsed fields.

        Returns:
            True if validation passes.
        """
        # Placeholder for custom validation
        # This could execute Python code or call external validation functions
        return True

    def _is_timeout(self) -> bool:
        """Check if parse timeout has occurred."""
        if self.state == ParseState.IDLE:
            return False

        time_since_data = (time.time() - self.last_data_time) * 1000
        return time_since_data > self.timeout

    def _handle_timeout(self) -> None:
        """Handle parse timeout."""
        logger.warning(
            f"Parse timeout: buffer size={len(self.buffer)}, state={self.state.value}"
        )
        self.buffer.clear()
        self.state = ParseState.IDLE

    def _extract_int(self, data: bytes) -> int:
        """Extract integer from bytes (big-endian)."""
        if len(data) == 1:
            return data[0]
        elif len(data) == 2:
            return int(struct.unpack(">H", data)[0])
        elif len(data) == 4:
            return int(struct.unpack(">I", data)[0])
        elif len(data) == 8:
            return int(struct.unpack(">Q", data)[0])
        else:
            return int.from_bytes(data, byteorder="big")

    def _get_minimum_required_data(self) -> int:
        """
        Get minimum bytes required to continue parsing.

        Returns:
            Minimum number of bytes needed.
        """
        if self.state == ParseState.IDLE:
            return 1

        elif self.state == ParseState.WAITING_FOR_HEAD:
            if self.protocol.head_pattern:
                return len(self.protocol.head_pattern)
            return 1

        elif self.state == ParseState.PARSING_HEADER:
            # Need at least head + length field
            head_field = next(
                (f for f in self.protocol.fields if f.field_type == FieldType.HEAD),
                None,
            )
            length_field = next(
                (f for f in self.protocol.fields if f.field_type == FieldType.LENGTH),
                None,
            )

            min_size = 0
            if head_field:
                min_size = max(min_size, head_field.offset + head_field.length)
            if length_field:
                min_size = max(min_size, length_field.offset + length_field.length)
            return min_size

        elif self.state in [ParseState.PARSING_LENGTH, ParseState.PARSING_DATA]:
            # Calculate based on field definitions
            min_size = 0
            for proto_field in self.protocol.fields:
                if proto_field.required:
                    min_size = max(min_size, proto_field.offset + proto_field.length)
            return min_size

        else:
            return 1

    def reset(self) -> None:
        """Reset parser state."""
        self.buffer.clear()
        self.state = ParseState.IDLE
        self.last_data_time = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get parsing statistics."""
        return self.stats.copy()

    def get_packets(self) -> List[ParsedPacket]:
        """Get all parsed packets."""
        return self.packets.copy()

    def clear_packets(self) -> None:
        """Clear stored packets."""
        self.packets.clear()
