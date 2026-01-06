"""
Serial port driver abstraction layer.

This module provides an abstract base class for serial port drivers,
allowing for multiple driver implementations (CH340, CP2102, etc.)
with a unified interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class DriverType(Enum):
    """Supported serial port driver types."""

    CH340 = "ch340"
    CP2102 = "cp2102"
    GENERIC = "generic"
    AUTO = "auto"  # Auto-detect


@dataclass
class SerialPortInfo:
    """Information about a serial port."""

    device: str
    name: str
    description: str
    hwid: Optional[str] = None
    vid: Optional[int] = None  # Vendor ID
    pid: Optional[int] = None  # Product ID
    driver_type: Optional[DriverType] = None

    def __str__(self) -> str:
        return f"{self.device} - {self.name} ({self.description})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device": self.device,
            "name": self.name,
            "description": self.description,
            "hwid": self.hwid,
            "vid": self.vid,
            "pid": self.pid,
            "driver_type": self.driver_type.value if self.driver_type else None,
        }


class SerialDriverError(Exception):
    """Base exception for serial driver errors."""

    pass


class DriverNotAvailableError(SerialDriverError):
    """Raised when a specific driver is not available."""

    pass


class SerialConnectionError(SerialDriverError):
    """Raised when serial connection fails."""

    pass


class SerialDriver(ABC):
    """
    Abstract base class for serial port drivers.
    """

    def __init__(self, driver_type: DriverType):
        self.driver_type = driver_type
        self.logger = logging.getLogger(f"{__name__}.{driver_type.value}")
        self.is_available = self._check_availability()

    @abstractmethod
    def detect_devices(self) -> List[SerialPortInfo]:
        """Detect available serial devices supported by this driver."""
        pass

    @abstractmethod
    async def connect(self, port_info: SerialPortInfo, **kwargs) -> Any:
        """Connect to a serial port."""
        pass

    @abstractmethod
    async def disconnect(self, connection: Any) -> None:
        """Disconnect from a serial port."""
        pass

    @abstractmethod
    async def read_data(self, connection: Any, size: int = 1024) -> bytes:
        """Read data from serial port."""
        pass

    @abstractmethod
    async def write_data(self, connection: Any, data: bytes) -> int:
        """Write data to serial port."""
        pass

    def _check_availability(self) -> bool:
        """Check if this driver is available on the current system."""
        try:
            self._check_dependencies()
            return True
        except ImportError:
            return False

    @abstractmethod
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        pass

    def get_supported_baudrates(self) -> List[int]:
        """Get list of supported baud rates."""
        return [
            300,
            600,
            1200,
            2400,
            4800,
            9600,
            14400,
            19200,
            28800,
            38400,
            57600,
            115200,
            230400,
            460800,
            921600,
        ]

    def get_supported_properties(self) -> Dict[str, Any]:
        """Get driver-specific properties."""
        return {
            "driver_type": self.driver_type.value,
            "name": self.driver_type.value.upper(),
            "available": self.is_available,
            "supported_baudrates": self.get_supported_baudrates(),
            "supports_flow_control": True,
            "supports_timeout": True,
        }
