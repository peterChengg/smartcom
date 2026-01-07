"""
CH340 serial port driver implementation.
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


class CH340Driver(SerialDriver):
    """Driver for CH340-based USB-to-serial adapters."""

    def __init__(self):
        super().__init__(DriverType.CH340)
        self.CH340_VID = 0x1A86
        self.CH340_PID = 0x7523
        self.CH341_PID = 0x5523

    def _check_dependencies(self) -> None:
        """Check if CH340 driver dependencies are available."""
        import serial
        import serial.tools.list_ports

    def detect_devices(self) -> List[SerialPortInfo]:
        """Detect CH340 devices by scanning serial ports."""
        if not self.is_available:
            raise DriverNotAvailableError("CH340 driver is not available")

        devices = []
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if self._is_ch340_device(port):
                    device_info = SerialPortInfo(
                        device=port.device,
                        name=port.name or port.device,
                        description=port.description or "CH340 Device",
                        hwid=port.hwid or "",
                        vid=port.vid or 0,
                        pid=port.pid or 0,
                        driver_type=DriverType.CH340,
                    )
                    devices.append(device_info)
        except Exception as e:
            logger.error(f"Error scanning for CH340 devices: {e}")

        return devices

    def _is_ch340_device(self, port) -> bool:
        """Check if a port is a CH340 device."""
        # Check USB Vendor and Product IDs
        if port.vid and port.pid:
            if port.vid == self.CH340_VID:
                if port.pid in [self.CH340_PID, self.CH341_PID]:
                    return True

        # Check description and hardware ID
        port_info = f"{port.description or ''} {port.hwid or ''}".lower()
        return any(keyword in port_info for keyword in ["ch340", "ch341", "usb-serial"])

    async def connect(self, port_info: SerialPortInfo, **kwargs) -> serial.Serial:
        """Connect to a CH340 serial port."""
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
                return ser
            else:
                raise SerialConnectionError(f"Failed to open {port_info.device}")
        except serial.SerialException as e:
            raise SerialConnectionError(f"Failed to connect to CH340: {str(e)}") from e

    async def disconnect(self, connection: serial.Serial) -> None:
        """Disconnect from CH340 serial port."""
        try:
            if connection and hasattr(connection, "is_open") and connection.is_open:
                connection.close()
        except Exception as e:
            logger.error(f"Error disconnecting from CH340: {str(e)}")

    async def read_data(self, connection: serial.Serial, size: int = 1024) -> bytes:
        """Read data from CH340 serial port."""
        try:
            if not connection or not connection.is_open:
                return b""
            data = connection.read(size)
            if data:
                logger.debug(f"Read {len(data)} bytes from CH340")
            return data
        except Exception as e:
            logger.error(f"Error reading from CH340: {str(e)}")
            return b""

    async def write_data(self, connection: serial.Serial, data: bytes) -> int:
        """Write data to CH340 serial port."""
        try:
            if not connection or not connection.is_open:
                return 0
            bytes_written = connection.write(data)
            connection.flush()
            logger.debug(f"Wrote {bytes_written} bytes to CH340")
            return bytes_written
        except Exception as e:
            logger.error(f"Error writing to CH340: {str(e)}")
            return 0

    def get_supported_properties(self) -> Dict[str, Any]:
        """Get CH340-specific properties."""
        properties = super().get_supported_properties()
        properties.update(
            {
                "device_vid": self.CH340_VID,
                "device_pids": [self.CH340_PID, self.CH341_PID],
                "max_baudrate": 921600,
                "characteristics": {
                    "low_cost": True,
                    "common_in_arduino": True,
                },
            }
        )
        return properties
