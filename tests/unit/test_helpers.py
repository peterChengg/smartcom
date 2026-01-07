"""
Test helper utilities for protocol parser.
"""

import struct
from typing import Any

from src.core.protocol_parser import ProtocolDefinition, ProtocolField, FieldType


def calculate_xor_checksum(data: bytes) -> int:
    """Calculate XOR checksum for data."""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum


def create_test_packet(protocol: ProtocolDefinition, field_values: dict) -> bytes:
    """
    Create a test packet with given field values.

    Args:
        protocol: Protocol definition.
        field_values: Dictionary of field name -> value.

    Returns:
        Complete packet bytes with checksum.
    """
    # Initialize packet data
    packet_dict = {}

    # Set field values
    for field in protocol.fields:
        if field.name in field_values:
            packet_dict[field.name] = field_values[field.name]
        elif field.default_value is not None:
            packet_dict[field.name] = field.default_value

    # Convert to bytes
    packet_bytes = bytearray()
    for field in protocol.fields:
        value = packet_dict.get(field.name)
        field_bytes = _value_to_bytes(value, field.length, field.field_type)
        packet_bytes.extend(field_bytes)

    # Calculate and add checksum if needed
    if protocol.checksum_type != "none":
        checksum_field = next(
            (f for f in protocol.fields if f.field_type == FieldType.CHECKSUM),
            None,
        )

        if checksum_field:
            # Calculate checksum over all bytes except checksum field
            data_without_checksum = (
                packet_bytes[: checksum_field.offset]
                + packet_bytes[checksum_field.offset + checksum_field.length :]
            )

            checksum = calculate_xor_checksum(bytes(data_without_checksum))

            # Set checksum in packet
            packet_bytes[
                checksum_field.offset : checksum_field.offset + checksum_field.length
            ] = checksum.to_bytes(checksum_field.length, byteorder="big")

    return bytes(packet_bytes)


def _value_to_bytes(value: Any, length: int, field_type: FieldType) -> bytes:
    """Convert value to bytes based on field type and length."""
    if field_type == FieldType.DATA:
        if isinstance(value, bytes):
            return value[:length]
        elif isinstance(value, str):
            return value.encode()[:length]
        elif isinstance(value, int):
            return value.to_bytes(length, byteorder="big")
        else:
            return value

    # For other field types, use standard integer encoding
    if isinstance(value, int):
        return value.to_bytes(length, byteorder="big")
    elif isinstance(value, bytes):
        return value[:length]
    else:
        return value.to_bytes(length, byteorder="big")
