"""
Generic serial port driver implementation.

This is a fallback driver that can handle most standard serial ports
that are not specifically supported by CH340 or CP2102 drivers.
"""

from typing import List, Dict, Any, Optional
import serial
import serial.tools.list_ports

from .base import (
    SerialDriver,
    SerialPortInfo,
    DriverType,
    SerialConnectionError,
    DriverNotAvailableError,
    SerialDriverError,
)

logger = __import__("logging").getLogger(__name__)


class GenericSerialDriver(SerialDriver):
    """
    Generic serial driver for devices not specifically supported.

    This is a fallback driver that can handle most standard serial ports
    using the standard pyserial library.
    """

    def __init__(self):
        super().__init__(DriverType.GENERIC)

    def _check_dependencies(self) -> None:
        """Check if generic driver dependencies are available."""
        import serial
        import serial.tools.list_ports

    def detect_devices(self) -> List[SerialPortInfo]:
        """
        Detect all serial ports (generic detection).

        Returns:
            List of all available serial ports.
        """
        if not self.is_available:
            raise DriverNotAvailableError("Generic serial driver is not available")

        self.logger.info("Scanning for generic serial devices...")
        devices = []

        try:
            ports = serial.tools.list_ports.comports()

            for port in ports:
                device_info = SerialPortInfo(
                    device=port.device,
                    name=port.name or port.device,
                    description=port.description or "Generic Serial Device",
                    hwid=port.hwid or "",
                    vid=port.vid or 0,
                    pid=port.pid or 0,
                    driver_type=DriverType.GENERIC,
                )
                devices.append(device_info)
                self.logger.debug(f"Found generic serial device: {device_info}")

        except Exception as e:
            self.logger.error(f"Error scanning generic serial devices: {e}")
            raise DriverNotAvailableError(f"Failed to scan serial ports: {e}")

        self.logger.info(f"Found {len(devices)} generic serial device(s)")
        return devices

    async def connect(self, port_info: SerialPortInfo, **kwargs) -> serial.Serial:
        """
        Connect to a generic serial port.

        Args:
            port_info: Information about the serial port.
            **kwargs: Additional connection parameters.

        Returns:
            Serial connection object.

        Raises:
            SerialConnectionError: If connection fails.
        """
        try:
            self.logger.info(f"Connecting to generic serial device: {port_info.device}")

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
            error_msg = f"Failed to connect to generic serial device {port_info.device}: {str(e)}"
            self.logger.error(error_msg)
            raise SerialConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error connecting to generic serial device {port_info.device}: {str(e)}"
            self.logger.error(error_msg)
            raise SerialConnectionError(error_msg) from e

    async def disconnect(self, connection: serial.Serial) -> None:
        """
        Disconnect from a generic serial port.

        Args:
            connection: Serial connection to close.
        """
        try:
            if connection and hasattr(connection, "is_open") and connection.is_open:
                device = getattr(connection, "port", "unknown")
                self.logger.info(f"Disconnecting from generic serial device: {device}")
                connection.close()
                self.logger.info(f"Successfully disconnected from {device}")
            else:
                self.logger.warning("Connection already closed or invalid")
        except Exception as e:
            self.logger.error(
                f"Error disconnecting from generic serial device: {str(e)}"
            )
            raise SerialConnectionError(f"Failed to disconnect: {str(e)}") from e

    async def read_data(self, connection: serial.Serial, size: int = 1024) -> bytes:
        """
        Read data from a generic serial port.

        Args:
            connection: Serial connection to read from.
            size: Maximum number of bytes to read.

        Returns:
            Data read from the port.
        """
        try:
            if not connection or not connection.is_open:
                return b""

            original_timeout = connection.timeout
            connection.timeout = 0.1

            try:
                data = connection.read(size)
                if data:
                    self.logger.debug(
                        f"Read {len(data)} bytes from generic serial device"
                    )
                return data
            finally:
                connection.timeout = original_timeout

        except Exception as e:
            self.logger.error(f"Error reading from generic serial device: {str(e)}")
            return b""

    async def write_data(self, connection: serial.Serial, data: bytes) -> int:
        """
        Write data to a generic serial port.

        Args:
            connection: Serial connection to write to.
            data: Data to write.

        Returns:
            Number of bytes written.
        """
        try:
            if not connection or not connection.is_open:
                return 0

            bytes_written = connection.write(data)
            connection.flush()

            self.logger.debug(f"Wrote {bytes_written} bytes to generic serial device")
            return bytes_written

        except Exception as e:
            self.logger.error(f"Error writing to generic serial device: {str(e)}")
            return 0

    def get_supported_properties(self) -> Dict[str, Any]:
        """
        Get generic serial driver properties.

        Returns:
            Dictionary of generic serial driver properties.
        """
        properties = super().get_supported_properties()
        properties.update(
            {
                "device_vid": 0,
                "device_pids": [],
                "supports_dtr_dsr": True,
                "supports_rts_cts": True,
                "supports_xon_xoff": True,
                "supports_custom_baudrates": True,
                "characteristics": {
                    "fallback_driver": True,
                    "universal_compatibility": True,
                    "software_only": False,
                    "plug_and_play": True,
                },
            }
        )
        return properties

    def _supports_flow_control(self) -> bool:
        """Generic driver supports hardware and software flow control."""
        return True
