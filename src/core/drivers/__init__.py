"""
Serial port drivers module.

This module provides an abstraction layer for serial port drivers,
supporting multiple driver types including CH340, CP2102, and generic serial.
"""

from .base import (
    SerialDriver,
    SerialPortInfo,
    SerialDriverError,
    DriverNotAvailableError,
    SerialConnectionError,
    DriverType,
)
from .ch340 import CH340Driver
from .cp2102 import CP2102Driver
from .generic import GenericSerialDriver
from .manager import DriverManager

__all__ = [
    "SerialDriver",
    "SerialPortInfo",
    "SerialDriverError",
    "DriverNotAvailableError",
    "SerialConnectionError",
    "DriverType",
    "CH340Driver",
    "CP2102Driver",
    "GenericSerialDriver",
    "DriverManager",
]
