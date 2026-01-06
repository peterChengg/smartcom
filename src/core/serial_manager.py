"""
Serial communication manager.

This module provides high-level serial port communication functionality,
including connection management, data transmission, and statistics.
"""

from typing import Optional, Any
from dataclasses import dataclass
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class SerialConfig:
    """Serial port configuration."""

    port: str
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout: float = 1.0
    xonxoff: bool = False
    rtscts: bool = False

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "bytesize": self.bytesize,
            "parity": self.parity,
            "stopbits": self.stopbits,
            "timeout": self.timeout,
            "xonxoff": self.xonxoff,
            "rtscts": self.rtscts,
        }


class SerialManager:
    """High-level serial port manager."""

    def __init__(self):
        self.is_connected = False
        self.config: Optional[SerialConfig] = None
        self.driver: Optional[Any] = None
        self.logger = logging.getLogger(__name__)

    def configure(self, config: SerialConfig) -> None:
        """Configure serial port settings."""
        self.config = config
        logger.info(f"Configured serial port: {config.port}")

    async def connect(self) -> bool:
        """Connect to configured serial port."""
        if not self.config:
            logger.error("No serial port configured")
            return False

        try:
            self.logger.info(f"Connecting to {self.config.port}...")
            await asyncio.sleep(0.1)
            self.is_connected = True
            logger.info(f"Connected to {self.config.port}")
            return True
        except Exception as e:
            self.is_connected = False
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from serial port."""
        if not self.is_connected:
            logger.warning("Not connected")
            return

        self.is_connected = False
        logger.info("Disconnected from serial port")

    async def write(self, data: bytes) -> int:
        """Write data to serial port."""
        if not self.is_connected:
            logger.warning("Not connected")
            return 0

        try:
            logger.info(f"Writing {len(data)} bytes to {self.config.port}")
            # Simulate writing
            await asyncio.sleep(0.01)
            logger.debug(f"Successfully wrote {len(data)} bytes")
            return len(data)
        except Exception as e:
            logger.error(f"Write failed: {e}")
            return 0

    async def read(self, size: int = 1024) -> bytes:
        """Read data from serial port."""
        if not self.is_connected:
            logger.warning("Not connected")
            return b""

        try:
            logger.debug(f"Reading up to {size} bytes from {self.config.port}")
            # Simulate reading
            await asyncio.sleep(0.01)
            return b"\x00" * min(size, 10)
        except Exception as e:
            logger.error(f"Read failed: {e}")
            return b""

    def is_active(self) -> bool:
        """Check if serial port is connected."""
        return self.is_connected

    def get_config(self) -> Optional[SerialConfig]:
        """Get current configuration."""
        return self.config

    def get_status(self) -> str:
        """Get connection status."""
        return "Connected" if self.is_connected else "Disconnected"
