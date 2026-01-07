"""
Data statistics and intelligent packet management.

This module provides functionality for tracking data statistics,
packet assembly/disassembly, and smart packet buffering.
"""

import asyncio
import hashlib
import logging
import struct
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import crcmod

logger = logging.getLogger(__name__)


class PacketDirection(Enum):
    """Packet direction."""

    TX = "transmit"
    RX = "receive"


class PacketStatus(Enum):
    """Packet status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    INVALID = "invalid"
    CORRUPTED = "corrupted"


@dataclass
class DataStats:
    """Data transmission statistics."""

    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    bytes_per_second: float = 0.0
    start_time: float = 0.0
    last_activity: float = 0.0

    def reset(self) -> None:
        """Reset statistics."""
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
        self.bytes_per_second = 0.0
        self.start_time = 0.0
        self.last_activity = time.time()

    def add_sent(self, count: int) -> None:
        """Add sent bytes count."""
        self.bytes_sent += count
        self.packets_sent += 1
        self.last_activity = time.time()

    def add_received(self, count: int) -> None:
        """Add received bytes count."""
        self.bytes_received += count
        self.packets_received += 1
        self.last_activity = time.time()

    def get_throughput(self) -> float:
        """Calculate current throughput in bytes/second."""
        uptime = self.get_uptime()
        if uptime > 0:
            return (self.bytes_sent + self.bytes_received) / uptime
        return 0.0

    def get_uptime(self) -> float:
        """Get connection uptime in seconds."""
        return time.time() - self.start_time if self.start_time > 0 else 0.0


@dataclass
class PacketInfo:
    """Information about a data packet."""

    data: bytes
    direction: PacketDirection
    timestamp: float
    sequence: int = 0
    status: PacketStatus = PacketStatus.PENDING
    checksum: Optional[int] = None
    checksum_valid: bool = False
    processing_time: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "data": self.data.hex(),
            "direction": self.direction.value,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "status": self.status.value,
            "checksum": f"0x{self.checksum:04X}" if self.checksum else "N/A",
            "checksum_valid": self.checksum_valid,
            "processing_time": self.processing_time,
        }


@dataclass
class PacketAssembler:
    """
    Intelligent packet assembler for serial data.

    This class handles packet assembly/disassembly with configurable
    timeout handling and buffer management.
    """

    def __init__(self, packet_timeout: float = 0.5):
        self.buffer = bytearray()
        self.expected_length: Optional[int] = None
        self.packet_timeout = packet_timeout
        self.last_data_time: float = 0.0
        self.assembler_state: str = (
            "idle"  # idle, collecting, assembling, complete, timeout
        )
        self.assembler_state: str = "idle"

    def reset(self) -> None:
        """Reset assembler state."""
        self.buffer.clear()
        self.expected_length = None
        self.assembler_state = "idle"
        self.last_data_time = 0.0

    def set_expected_length(self, length: int) -> None:
        """Set expected packet length."""
        self.expected_length = length
        logger.debug(f"Expected packet length set to {length}")

    def clear_expected_length(self) -> None:
        """Clear expected packet length."""
        self.expected_length = None

    def feed_data(self, data: bytes) -> Optional[bytes]:
        """
        Feed data to assembler.

        Args:
            data: Data to add to buffer.

        Returns:
            Complete packet if available, None otherwise.
        """
        if not data:
            return None

        self.buffer.extend(data)
        self.last_data_time = time.time()
        self.assembler_state = "collecting"

        # Try to extract complete packet
        return self._try_extract_packet()

    def _try_extract_packet(self) -> Optional[bytes]:
        """
        Try to extract a complete packet from buffer.

        Returns:
            Complete packet or None.
        """
        if not self.buffer:
            return None

        self.assembler_state = "assembling"

        # Check if timeout
        if self.packet_timeout > 0:
            time_since_data = time.time() - self.last_data_time
            if time_since_data > self.packet_timeout:
                self.logger.warning(
                    f"Packet timeout: {time_since_data:.2f}s, discarding buffer"
                )
                self.buffer.clear()
                self.assembler_state = "idle"
                return None

        # Try different extraction strategies
        strategies = [
            self._extract_by_length,
            self._extract_by_header,
            self._extract_by_timeout,
            self._extract_by_checksum,
        ]

        for strategy in strategies:
            packet = strategy()
            if packet is not None:
                return packet

        # If no strategy succeeded, keep collecting
        self.assembler_state = "collecting"
        return None

    def _extract_by_length(self) -> Optional[bytes]:
        """Extract packet by expected length."""
        if not self.expected_length:
            return None

        if len(self.buffer) >= self.expected_length:
            packet = bytes(self.buffer[: self.expected_length])
            self.buffer = bytearray()
            self.assembler_state = "complete"
            logger.debug(f"Extracted packet by length: {len(packet)} bytes")
            return packet
        return None

    def _extract_by_header(self) -> Optional[bytes]:
        """Extract packet by header detection."""
        if len(self.buffer) < 2:
            return None

        # Simple header detection: look for common patterns
        header_patterns = [
            b"\xaa\x55",
            b"\xab\xcd",
            b"\xff\xff",
            b"\x7e\x80",
            b"\xff",
            b"\xfe",
            b"\xfd",
            b"\xfa",
            b"\xfb",
            b"\xfc",
            b"\xf9",
            b"\xf8",
            b"\xf7",
            b"\xfe\xfe" b"\xfd" b"\xff\xfe",
        ]

        for pattern in header_patterns:
            if self.buffer.startswith(pattern):
                # Try to extract packet ending with timeout
                end_pattern = pattern + b"\x55"  # Example end marker
                end_index = self.buffer.find(end_pattern)

                if end_index > 0:
                    packet = bytes(self.buffer[: end_index + len(end_pattern)])
                    self.buffer = self.buffer[end_index + len(end_pattern) :]
                    self.assembler_state = "complete"
                    logger.debug(
                        f"Extracted packet by header pattern: {len(packet)} bytes"
                    )
                    return packet

        return None

    def _extract_by_timeout(self) -> Optional[bytes]:
        """Extract packet by timeout (no new data for timeout period)."""
        if len(self.buffer) == 0:
            return None

        # Simple timeout: return everything as complete
        packet = bytes(self.buffer)
        self.buffer.clear()
        self.assembler_state = "complete"
        logger.debug(f"Extracted packet by timeout: {len(packet)} bytes")
        return packet

    def _extract_by_checksum(self) -> Optional[bytes]:
        """Extract packet by checksum validation."""
        if len(self.buffer) < 3:
            return None

        # Simple checksum: CRC16
        if len(self.buffer) >= 3:
            # Try to validate last byte as checksum
            data = self.buffer[:-1]
            checksum = self._calculate_crc16(data)

            if checksum == self.buffer[-1]:
                packet = bytes(self.buffer)
                self.buffer.clear()
                self.assembler_state = "complete"
                logger.debug(f"Extracted packet by checksum: {len(packet)} bytes")
                return packet

        return None

    def _calculate_crc16(self, data: bytes) -> int:
        """Calculate CRC16 checksum."""
        crc = crcmod.crc16(data)
        return crc

    def _calculate_modbus_crc(self, data: bytes, polynomial: int = 0xA001) -> int:
        """Calculate Modbus CRC."""
        crc = 0xFFFF

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
        return crc & 0xFFFF

    def _calculate_crc32(self, data: bytes, polynomial: int = 0x04C11DB7) -> int:
        """Calculate CRC32."""
        crc = 0xFFFFFFFF

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ polynomial
                else:
                    crc = crc >> 1

        return crc ^ 0xFFFFFFFF

    def validate_checksum(
        self, data: bytes, packet: PacketInfo, checksum_func: Callable
    ) -> bool:
        """Validate packet checksum."""
        calculated_checksum = checksum_func(data)
        return calculated_checksum == packet.checksum

    def calculate_packet_info(
        self, data: bytes, checksum_func: Callable = _calculate_crc16
    ) -> PacketInfo:
        """
        Calculate packet information.

        Args:
            data: Packet data.
            checksum_func: Checksum function.

        Returns:
            PacketInfo with calculated checksum.
        """
        timestamp = time.time()

        return PacketInfo(
            data=data,
            direction=PacketDirection.RX,
            timestamp=timestamp,
            sequence=0,
            status=PacketStatus.COMPLETED,
            checksum=checksum_func(data),
            checksum_valid=True,
        )


class PacketBuffer:
    """
    Smart packet buffer with intelligent management.

    Features:
    - Configurable buffer size
    - Circular buffer for streaming data
    - Priority queue for important packets
    - Statistics tracking
    """

    def __init__(self, max_size: int = 1024 * 1024):
        self.max_size = max_size
        self.buffer = bytearray()
        self.max_queue_size = 100  # Maximum queued packets
        self.queue: deque[PacketInfo] = deque(maxlen=100)
        self.stats = DataStats()
        self.stats.start_time = time.time()

    def add_packet(self, packet: PacketInfo) -> None:
        """
        Add packet to buffer queue.

        Args:
            packet: Packet information to add.
        """
        self.queue.append(packet)
        self.stats.add_sent(len(packet.data))

        if len(self.buffer) + len(packet.data) > self.max_size:
            # Remove oldest data
            excess = len(self.buffer) + len(packet.data) - self.max_size
            self.buffer = self.buffer[excess:]
            self.logger.debug(f"Buffer overflow, removed {excess} bytes")

    def get_queue_status(self) -> dict:
        """Get buffer queue status."""
        return {
            "queue_size": len(self.queue),
            "max_queue_size": self.max_queue_size,
            "buffer_size": len(self.buffer),
            "stats": self.stats.to_dict(),
        }

    def clear_queue(self) -> None:
        """Clear packet queue."""
        self.queue.clear()

    def process_queue(self) -> None:
        """Process all queued packets."""
        processed = 0
        for packet in self.queue:
            # Process packet here (placeholder)
            processed += 1
        self.queue.popleft()

        self.logger.info(f"Processed {processed} packets from queue")
