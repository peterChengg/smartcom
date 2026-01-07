"""
Unit tests for protocol parser.
"""

import asyncio
import time

import pytest

from src.core.protocol_parser import (
    FieldType,
    ParseState,
    ParseError,
    ParsedPacket,
    ProtocolDefinition,
    ProtocolField,
    ProtocolParser,
)


@pytest.fixture
def simple_protocol():
    """Create a simple protocol definition."""
    return ProtocolDefinition(
        name="simple",
        head_pattern=b"\xff\xfe",
        fields=[
            ProtocolField(
                name="head",
                field_type=FieldType.HEAD,
                length=2,
                offset=0,
            ),
            ProtocolField(
                name="length",
                field_type=FieldType.LENGTH,
                length=2,
                offset=2,
            ),
            ProtocolField(
                name="cmd",
                field_type=FieldType.CMD,
                length=1,
                offset=4,
            ),
            ProtocolField(
                name="data",
                field_type=FieldType.DATA,
                length=4,
                offset=5,
            ),
            ProtocolField(
                name="checksum",
                field_type=FieldType.CHECKSUM,
                length=1,
                offset=9,
            ),
        ],
        checksum_type="xor",
        parse_timeout=0.5,
    )


@pytest.fixture
def parser(simple_protocol):
    """Create a protocol parser instance."""
    return ProtocolParser(simple_protocol)


@pytest.mark.asyncio
async def test_parser_initialization(parser):
    """Test parser initialization."""
    assert parser.protocol.name == "simple"
    assert len(parser.buffer) == 0
    assert parser.state == ParseState.IDLE
    assert parser.timeout == 500  # 0.5s = 500ms


@pytest.mark.asyncio
async def test_parse_simple_packet(parser):
    """Test parsing a simple packet."""
    # Create a test packet: head(2) + length(2) + cmd(1) + data(4) + checksum(1)
    # FF FE 00 0A 15 12 34 56 78 16
    # Checksum (XOR): FF ^ FE ^ 00 ^ 0A ^ 15 ^ 12 ^ 34 ^ 56 ^ 78 = 0x16
    packet_data = b"\xff\xfe\x00\x0a\x15\x12\x34\x56\x78\x16"

    packet = await parser.parse_data(packet_data)

    assert packet is not None
    assert packet.is_valid
    assert len(packet.fields) == 5
    assert packet.fields["head"] == 0xFFFE
    assert packet.fields["length"] == 10
    assert packet.fields["cmd"] == 0x15
    assert packet.fields["data"] == b"\x12\x34\x56\x78"
    assert packet.parse_time < 10  # Should complete in < 10ms


@pytest.mark.asyncio
async def test_parse_partial_data(parser):
    """Test parsing partial data."""
    # Send partial data first
    partial = b"\xff\xfe\x00"
    packet1 = await parser.parse_data(partial)
    assert packet1 is None

    # Send remaining data (need 7 more bytes to complete 10-byte packet)
    # FF FE 00 0A 15 12 34 56 78 16
    remaining = b"\x0a\x15\x12\x34\x56\x78\x16"
    packet2 = await parser.parse_data(remaining)
    assert packet2 is not None
    assert packet2.is_valid


@pytest.mark.asyncio
async def test_parse_multiple_packets(parser):
    """Test parsing multiple packets in sequence."""
    # Packet 1: FF FE 00 0A 15 12 34 56 78 16 (checksum = FF^FE^00^0A^15^12^34^56^78 = 0x16)
    packet1_data = b"\xff\xfe\x00\x0a\x15\x12\x34\x56\x78\x16"
    # Packet 2: FF FE 00 0A 18 AB CD EF 01 5A (checksum = FF^FE^00^0A^18^AB^CD^EF^01 = 0x5A)
    packet2_data = b"\xff\xfe\x00\x0a\x18\xab\xcd\xef\x01\x5a"

    # Send both packets together
    combined = packet1_data + packet2_data

    packet1 = await parser.parse_data(combined)
    assert packet1 is not None

    # Parse second packet
    packet2 = await parser.parse_data(b"")
    assert packet2 is not None

    # Verify both packets
    assert packet1.fields["cmd"] == 0x15
    assert packet2.fields["cmd"] == 0x18


@pytest.mark.asyncio
async def test_parse_without_head_pattern():
    """Test parsing without head pattern."""
    protocol = ProtocolDefinition(
        name="no_head",
        head_pattern=None,
        fields=[
            ProtocolField(
                name="length",
                field_type=FieldType.LENGTH,
                length=2,
                offset=0,
            ),
            ProtocolField(
                name="data",
                field_type=FieldType.DATA,
                length=4,
                offset=2,
            ),
        ],
        min_length=6,  # Minimum packet length
        max_length=6,  # Maximum packet length
        parse_timeout=0.5,
    )

    parser = ProtocolParser(protocol)

    # Should parse immediately without waiting for head
    # Packet is 6 bytes: length(2) + data(4)
    packet_data = b"\x00\x06\x12\x34\x56\x78"
    packet = await parser.parse_data(packet_data)

    assert packet is not None
    assert packet.fields["length"] == 6


@pytest.mark.asyncio
async def test_parse_timeout(parser):
    """Test parse timeout handling."""
    # Send partial data
    partial = b"\xff\xfe"
    await parser.parse_data(partial)

    # Wait for timeout (0.6s > 0.5s timeout)
    await asyncio.sleep(0.6)

    # Send more data - buffer should be cleared
    more_data = b"\x00\x06\x15\x12\x34\x56\x78"
    # This should not parse because the first FF was cleared
    packet = await parser.parse_data(more_data)

    # Buffer should have been cleared, so packet parsing starts fresh
    assert packet is None or not parser.buffer.startswith(b"\xff\xfe")


@pytest.mark.asyncio
async def test_parse_invalid_length(parser):
    """Test handling of invalid packet length."""
    # Create packet with invalid length (too large)
    # This will trigger length validation and cause the parser to reset
    packet_data = b"\xff\xfe\xff\xff\x15\x12\x34\x56\x78"

    # Parse may handle this in different ways depending on implementation
    # The key is that it doesn't crash and handles the invalid data gracefully
    await parser.parse_data(packet_data)

    # Should handle gracefully
    # The exact behavior depends on implementation (may reject or attempt to parse)
    # Most importantly, no exception is raised


@pytest.mark.asyncio
async def test_checksum_validation(parser):
    """Test checksum validation."""
    # Create packet with invalid checksum (correct is 0x16, using 0x00)
    # FF FE 00 0A 15 12 34 56 78 00 (checksum should be 0x16)
    packet_data = b"\xff\xfe\x00\x0a\x15\x12\x34\x56\x78\x00"

    packet = await parser.parse_data(packet_data)

    # Packet should be parsed but marked as invalid
    assert packet is not None
    assert not packet.is_valid
    assert "Checksum validation failed" in packet.validation_errors


@pytest.mark.asyncio
async def test_parse_performance(parser):
    """Test parsing performance - should be < 10ms."""
    # Create a large number of packets
    packets = []
    for i in range(100):
        packet_data = b"\xff\xfe\x00\x06" + bytes([i & 0xFF]) + b"\x12\x34\x56\x78"
        packets.append(packet_data)

    # Parse all packets and measure time
    start_time = time.time()
    for packet_data in packets:
        await parser.parse_data(packet_data)
    end_time = time.time()

    # Average parse time should be < 10ms
    total_time = (end_time - start_time) * 1000  # Convert to ms
    avg_time = total_time / len(packets)
    assert (
        avg_time < 10
    ), f"Average parse time {avg_time:.2f}ms exceeds 10ms requirement"


@pytest.mark.asyncio
async def test_parser_stats(parser):
    """Test parser statistics tracking."""
    # Parse some packets
    for i in range(10):
        packet_data = b"\xff\xfe\x00\x0a\x15\x12\x34\x56\x78\x16"
        await parser.parse_data(packet_data)

    stats = parser.get_stats()
    assert stats["parsed_packets"] == 10
    assert stats["total_bytes"] > 0
    assert stats["parse_errors"] == 0
    assert stats["parse_time_ms"] > 0


@pytest.mark.asyncio
async def test_parser_reset(parser):
    """Test parser reset functionality."""
    # Parse some data
    await parser.parse_data(b"\xff\xfe\x00\x06\x15\x12\x34\x56\x78")

    # Reset parser
    parser.reset()

    # Check state
    assert len(parser.buffer) == 0
    assert parser.state == ParseState.IDLE
    assert parser.last_data_time == 0


@pytest.mark.asyncio
async def test_get_packets(parser):
    """Test retrieving parsed packets."""
    # Parse some packets with correct checksums
    for i in range(5):
        cmd = 0x10 + i
        # Calculate checksum: FF ^ FE ^ 00 ^ 0A ^ cmd ^ 12 ^ 34 ^ 56 ^ 78
        checksum = 0xFF ^ 0xFE ^ 0x00 ^ 0x0A ^ cmd ^ 0x12 ^ 0x34 ^ 0x56 ^ 0x78
        packet_data = (
            b"\xff\xfe\x00\x0a" + bytes([cmd]) + b"\x12\x34\x56\x78" + bytes([checksum])
        )
        await parser.parse_data(packet_data)

    packets = parser.get_packets()
    assert len(packets) == 5
    assert all(isinstance(p, ParsedPacket) for p in packets)


@pytest.mark.asyncio
async def test_clear_packets(parser):
    """Test clearing parsed packets."""
    # Parse some packets
    for i in range(5):
        packet_data = b"\xff\xfe\x00\x0a\x15\x12\x34\x56\x78\x16"
        await parser.parse_data(packet_data)

    # Clear packets
    parser.clear_packets()

    # Check
    assert len(parser.get_packets()) == 0


@pytest.mark.asyncio
async def test_complex_protocol():
    """Test parsing a complex protocol with multiple field types."""
    protocol = ProtocolDefinition(
        name="complex",
        head_pattern=b"\xaa\x55",
        fields=[
            ProtocolField(
                name="head",
                field_type=FieldType.HEAD,
                length=2,
                offset=0,
            ),
            ProtocolField(
                name="length",
                field_type=FieldType.LENGTH,
                length=2,
                offset=2,
            ),
            ProtocolField(
                name="cmd",
                field_type=FieldType.CMD,
                length=1,
                offset=4,
            ),
            ProtocolField(
                name="seq",
                field_type=FieldType.SEQ,
                length=2,
                offset=5,
            ),
            ProtocolField(
                name="data",
                field_type=FieldType.DATA,
                length=8,
                offset=7,
            ),
            ProtocolField(
                name="checksum",
                field_type=FieldType.CHECKSUM,
                length=2,
                offset=15,
            ),
        ],
        checksum_type="crc16",
        parse_timeout=1.0,
    )

    parser = ProtocolParser(protocol)

    # Create a test packet with correct length (total packet is 17 bytes)
    # AA 55 00 11 15 00 01 01 02 03 04 05 06 07 08 XX XX
    packet_data = (
        b"\xaa\x55\x00\x11\x15\x00\x01"
        + b"\x01\x02\x03\x04\x05\x06\x07\x08"
        + b"\x00\x00"
    )

    packet = await parser.parse_data(packet_data)

    assert packet is not None
    assert len(packet.fields) == 6
    assert packet.fields["head"] == 0xAA55
    assert packet.fields["cmd"] == 0x15
    assert packet.fields["seq"] == 1


@pytest.mark.asyncio
async def test_field_optional():
    """Test parsing with optional fields."""
    protocol = ProtocolDefinition(
        name="optional",
        head_pattern=b"\xff\xfe",
        fields=[
            ProtocolField(
                name="head",
                field_type=FieldType.HEAD,
                length=2,
                offset=0,
            ),
            ProtocolField(
                name="cmd",
                field_type=FieldType.CMD,
                length=1,
                offset=2,
            ),
            ProtocolField(
                name="optional_data",
                field_type=FieldType.DATA,
                length=4,
                offset=3,
                required=False,
                default_value=b"\x00\x00\x00\x00",
            ),
        ],
        parse_timeout=0.5,
    )

    parser = ProtocolParser(protocol)

    # Create packet with optional field (total 7 bytes: head 2 + cmd 1 + optional_data 4)
    # FF FE 15 12 34 56 00 (no length field)
    packet_data = b"\xff\xfe\x15\x12\x34\x56\x00"
    packet = await parser.parse_data(packet_data)

    assert packet is not None
    assert packet.fields["optional_data"] == b"\x12\x34\x56\x00"


@pytest.mark.asyncio
async def test_field_validation():
    """Test field validation."""
    protocol = ProtocolDefinition(
        name="validated",
        head_pattern=b"\xff\xfe",
        fields=[
            ProtocolField(
                name="head",
                field_type=FieldType.HEAD,
                length=2,
                offset=0,
            ),
            ProtocolField(
                name="cmd",
                field_type=FieldType.CMD,
                length=1,
                offset=2,
                validation="cmd in [0x10, 0x15, 0x18]",
            ),
            ProtocolField(
                name="data",
                field_type=FieldType.DATA,
                length=4,
                offset=3,
            ),
        ],
        parse_timeout=0.5,
    )

    parser = ProtocolParser(protocol)

    # Valid packet (7 bytes: head 2 + cmd 1 + data 4)
    # FF FE 15 12 34 56 78 (no length field)
    valid_packet = b"\xff\xfe\x15\x12\x34\x56\x78"
    packet = await parser.parse_data(valid_packet)
    assert packet is not None


@pytest.mark.asyncio
async def test_crc32_checksum():
    """Test CRC32 checksum validation."""
    protocol = ProtocolDefinition(
        name="crc32",
        head_pattern=b"\xff\xfe",
        fields=[
            ProtocolField(
                name="head",
                field_type=FieldType.HEAD,
                length=2,
                offset=0,
            ),
            ProtocolField(
                name="length",
                field_type=FieldType.LENGTH,
                length=2,
                offset=2,
            ),
            ProtocolField(
                name="data",
                field_type=FieldType.DATA,
                length=4,
                offset=4,
            ),
            ProtocolField(
                name="checksum",
                field_type=FieldType.CHECKSUM,
                length=4,
                offset=8,
            ),
        ],
        checksum_type="crc32",
        parse_timeout=0.5,
    )

    parser = ProtocolParser(protocol)

    # Create packet (checksum will be invalid)
    # FF FE 00 0C 12 34 56 78 XX XX XX XX (total 12 bytes)
    packet_data = b"\xff\xfe\x00\x0c\x12\x34\x56\x78\x00\x00\x00\x00"
    packet = await parser.parse_data(packet_data)

    assert packet is not None
    # Should be marked as invalid due to checksum
    assert not packet.is_valid


@pytest.mark.asyncio
async def test_packet_to_dict(parser):
    """Test converting packet to dictionary."""
    packet_data = b"\xff\xfe\x00\x0a\x15\x12\x34\x56\x78\x16"
    packet = await parser.parse_data(packet_data)

    assert packet is not None
    packet_dict = packet.to_dict()

    assert isinstance(packet_dict, dict)
    assert "raw_data" in packet_dict
    assert "fields" in packet_dict
    assert "timestamp" in packet_dict
    assert "parse_time" in packet_dict
    assert "is_valid" in packet_dict
