"""
Automatic serial driver detection and management.

This module provides automatic detection of available serial port drivers
and creates appropriate driver instances for detected devices.
"""

from typing import List, Dict, Optional, Type, Any
import logging

from .base import SerialDriver, SerialPortInfo, DriverType, DriverNotAvailableError
from .generic import GenericSerialDriver

logger = logging.getLogger(__name__)


class DriverManager:
    """
    Automatic driver detection and management system.

    This class automatically detects available serial port devices
    and creates appropriate driver instances for them.
    """

    def __init__(self):
        self.drivers: Dict[DriverType, SerialDriver] = {}
        self.logger = logging.getLogger(__name__)
        self._initialize_drivers()

    def _initialize_drivers(self) -> None:
        """Initialize all available drivers."""
        self.logger.info("Initializing serial drivers...")

        # Initialize generic driver (always available)
        try:
            generic_driver = GenericSerialDriver()
            self.drivers[DriverType.GENERIC] = generic_driver
            self.logger.info("Initialized Generic driver")
        except Exception as e:
            self.logger.error(f"Failed to initialize Generic driver: {e}")

        # Try to initialize specific drivers
        try:
            from .ch340 import CH340Driver

            ch340_driver = CH340Driver()
            if ch340_driver.is_available:
                self.drivers[DriverType.CH340] = ch340_driver
                self.logger.info("Initialized CH340 driver")
            else:
                self.logger.warning("CH340 driver is not available")
        except ImportError:
            self.logger.warning("CH340 driver module not found")
        except Exception as e:
            self.logger.error(f"Failed to initialize CH340 driver: {e}")

        try:
            from .cp2102 import CP2102Driver

            cp2102_driver = CP2102Driver()
            if cp2102_driver.is_available:
                self.drivers[DriverType.CP2102] = cp2102_driver
                self.logger.info("Initialized CP2102 driver")
            else:
                self.logger.warning("CP2102 driver is not available")
        except ImportError:
            self.logger.warning("CP2102 driver module not found")
        except Exception as e:
            self.logger.error(f"Failed to initialize CP2102 driver: {e}")

    def detect_all_devices(self) -> List[SerialPortInfo]:
        """
        Detect all available serial devices using available drivers.

        Returns:
            List of all detected serial devices.
        """
        self.logger.info("Scanning for all serial devices...")
        all_devices = []

        for driver_type, driver in self.drivers.items():
            try:
                devices = driver.detect_devices()
                all_devices.extend(devices)
                self.logger.debug(f"{driver_type.value} found {len(devices)} devices")
            except Exception as e:
                self.logger.error(
                    f"Error scanning with {driver_type.value} driver: {e}"
                )

        # Remove duplicates (some devices might be detected by multiple drivers)
        unique_devices = self._remove_duplicate_devices(all_devices)

        self.logger.info(f"Total unique devices found: {len(unique_devices)}")
        return unique_devices

    def get_device_driver(self, port_info: SerialPortInfo) -> Optional[SerialDriver]:
        """
        Get the appropriate driver for a specific device.

        Args:
            port_info: Information about a serial device.

        Returns:
            Driver instance that can handle this device, or None.
        """
        # If device already has a driver type specified, use that
        if port_info.driver_type:
            return self.drivers.get(port_info.driver_type)

        # Try to match device based on VID/PID
        if port_info.vid and port_info.pid:
            for driver_type, driver in self.drivers.items():
                if self._device_matches_driver(port_info, driver):
                    self.logger.info(
                        f"Matched {port_info.device} to {driver_type.value} driver"
                    )
                    return driver

        # Fallback to generic handling
        return self.drivers.get(DriverType.GENERIC)

    def _device_matches_driver(
        self, port_info: SerialPortInfo, driver: SerialDriver
    ) -> bool:
        """
        Check if a device matches a specific driver.

        Args:
            port_info: Device information.
            driver: Driver instance.

        Returns:
            True if device matches this driver.
        """
        try:
            # Get driver properties
            properties = driver.get_supported_properties()

            # Check VID
            if properties.get("device_vid"):
                if port_info.vid and port_info.vid == properties["device_vid"]:
                    # Check PID
                    device_pids = properties.get("device_pids", [])
                    if port_info.pid and port_info.pid in device_pids:
                        return True

        except Exception as e:
            self.logger.error(f"Error checking driver compatibility: {e}")

        return False

    def _remove_duplicate_devices(
        self, devices: List[SerialPortInfo]
    ) -> List[SerialPortInfo]:
        """
        Remove duplicate devices from the list.

        Args:
            devices: List of detected devices.

        Returns:
            List with duplicates removed.
        """
        seen_devices = set()
        unique_devices = []

        for device in devices:
            device_key = (device.device, device.vid, device.pid)
            if device_key not in seen_devices:
                seen_devices.add(device_key)
                unique_devices.append(device)
            else:
                self.logger.debug(f"Removing duplicate device: {device.device}")

        return unique_devices

    def get_driver_for_type(self, driver_type: DriverType) -> Optional[SerialDriver]:
        """
        Get a driver instance for a specific driver type.

        Args:
            driver_type: The type of driver desired.

        Returns:
            Driver instance or None if not available.
        """
        return self.drivers.get(driver_type)

    def get_available_driver_types(self) -> List[DriverType]:
        """
        Get list of available driver types.

        Returns:
            List of available DriverType enum values.
        """
        return list(self.drivers.keys())

    def get_driver_info(self) -> Dict[str, Any]:
        """
        Get information about all initialized drivers.

        Returns:
            Dictionary with driver information.
        """
        driver_info: Dict[str, Any] = {}
        for driver_type, driver in self.drivers.items():
            try:
                properties = driver.get_supported_properties()
                driver_info[driver_type.value] = {
                    "name": driver_type.value.upper(),
                    "available": driver.is_available,
                    "properties": properties,
                }
            except Exception as e:
                driver_info[driver_type.value] = {
                    "name": driver_type.value.upper(),
                    "available": False,
                    "error": str(e),
                }

        return driver_info
