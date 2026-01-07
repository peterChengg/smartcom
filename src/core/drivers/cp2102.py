"""
CP2102 serial port driver implementation.

This module provides support for CP210x USB-to-serial bridge devices,
which are popular USB-to-UART bridge chips from Silicon Labs.
"""

from typing import Any, Dict, List, Optional

import serial
import serial.tools.list_ports

from .base import (
    DriverNotAvailableError,
    DriverType,
    SerialConnectionError,
    SerialDriver,
    SerialDriverError,
    SerialPortInfo,
)

logger = __import__("logging").getLogger(__name__)


class CP2102Driver(SerialDriver):
    """Driver for CP2102/CP2109 USB-to-UART bridge devices."""

    def __init__(self):
        super().__init__(DriverType.CP2102)
        self.vid_pattern = 0x10C4
        self.pid_pattern = [
            0xEA60,
            0xEA61,
            0xEA70,
            0xEA71,
            0xEA63,
            0xEA64,
            0xEA65,
            0xEA66,
        ]

    def _check_dependencies(self) -> None:
        """Check if CP2102 driver dependencies are available."""
        import serial
        import serial.tools.list_ports

    def detect_devices(self) -> List[SerialPortInfo]:
        """Detect available CP2102 devices."""
        if not self.is_available:
            raise DriverNotAvailableError("CP2102 driver is not available")

        self.logger.info("Scanning for CP2102 devices...")
        devices = []

        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if self._is_cp2102_device(port):
                    device_info = SerialPortInfo(
                        device=port.device,
                        name=port.name or port.device,
                        description=port.description or "CP2102 Device",
                        hwid=port.hwid or "",
                        vid=port.vid or 0,
                        pid=port.pid or 0,
                        driver_type=DriverType.CP2102,
                    )
                    devices.append(device_info)
                    self.logger.info(f"Detected CP2102 device: {device_info}")
        except Exception as e:
            self.logger.error(f"Error scanning for CP2102 devices: {e}")

        return devices

    def _is_cp2102_device(self, port) -> bool:
        """Check if a port is a CP2102 device."""
        if port.vid and port.pid:
            if port.vid == self.vid_pattern:
                if port.pid in self.pid_pattern:
                    return True

        port_info = f"{port.description or ''} {port.hwid or ''}".lower()
        return any(
            keyword in port_info
            for keyword in [
                "cp2102",
                "cp2103",
                "cp2104",
                "cp2105",
                "cp2108",
                "cp2109",
                "silicon labs",
                "uart bridge",
            ]
        )

    async def connect(self, port_info: SerialPortInfo, **kwargs) -> serial.Serial:
        """Connect to a CP2102 device."""
        try:
            connection_params = {
                "baudrate": kwargs.get("baudrate", 9600),
                "bytesize": kwargs.get("bytesize", 8),
                "parity": kwargs.get("parity", serial.PARITY_NONE),
                "stopbits": kwargs.get("stopbits", serial.STOPBITS_ONE),
                "timeout": kwargs.get("timeout", 1.0),
                "xonxoff": kwargs.get("xonxoff", False),
                "rtscts": kwargs.get("rtscts", False),
                "dsrdtr": kwargs.get("dsrdtr", False),
            }

            ser = serial.Serial(port=port_info.device, **connection_params)
            if ser.is_open:
                self.logger.info(f"Successfully connected to {port_info.device}")
                return ser
            else:
                raise SerialConnectionError(f"Failed to open {port_info.device}")
        except serial.SerialException as e:
            raise SerialConnectionError(
                f"Failed to connect to CP2102 {port_info.device}: {str(e)}"
            ) from e

    async def disconnect(self, connection: serial.Serial) -> None:
        """Disconnect from a CP2102 device."""
        try:
            if connection and hasattr(connection, "is_open") and connection.is_open:
                device = getattr(connection, "port", "unknown")
                self.logger.info(f"Disconnecting from CP2102 device: {device}")
                connection.close()
        except Exception as e:
            self.logger.error(f"Error disconnecting from CP2102: {str(e)}")
            raise SerialConnectionError(f"Failed to disconnect: {str(e)}") from e

    async def read_data(self, connection: serial.Serial, size: int = 1024) -> bytes:
        """Read data from CP2102 serial port."""
        try:
            if not connection or not connection.is_open:
                return b""
            data = connection.read(size)
            if data:
                self.logger.debug(f"Read {len(data)} bytes from CP2102")
            return data
        except Exception as e:
            self.logger.error(f"Error reading from CP2102: {str(e)}")
            return b""

    async def write_data(self, connection: serial.Serial, data: bytes) -> int:
        """Write data to CP2102 serial port."""
        try:
            if not connection or not connection.is_open:
                return 0
            bytes_written = connection.write(data)
            connection.flush()
            self.logger.debug(f"Wrote {bytes_written} bytes to CP2102")
            return bytes_written
        except Exception as e:
            self.logger.error(f"Error writing to CP2102: {str(e)}")
            return 0

    def get_supported_properties(self) -> Dict[str, Any]:
        """Get CP2102-specific properties."""
        properties = super().get_supported_properties()
        properties.update(
            {
                "device_vid": self.vid_pattern,
                "device_pids": self.pid_pattern,
                "max_baudrate": 1000000,
                "characteristics": {
                    "professional_grade": True,
                    "silicon_labs": True,
                    "usb_uart_bridge": True,
                    "configurable": True,
                },
            }
        )
        return properties
