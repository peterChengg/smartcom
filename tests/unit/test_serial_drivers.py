"""
Tests for serial port drivers abstraction layer.

This module tests the serial driver functionality including
device detection, connection management, and data transmission.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

# Import from the drivers module
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.drivers.base import (
    SerialDriver, SerialPortInfo, DriverType, SerialDriverError,
    DriverNotAvailableError, SerialConnectionError
)
from src.core.drivers.ch340 import CH340Driver
from src.core.drivers.cp2102 import CP2102Driver
from src.core.drivers.generic import GenericSerialDriver
from src.core.drivers.manager import DriverManager


class TestSerialPortInfo:
    """Test SerialPortInfo dataclass."""
    
    def test_serial_port_info_creation(self):
        """Test creating a SerialPortInfo object."""
        port_info = SerialPortInfo(
            device="/dev/ttyUSB0",
            name="USB Serial Port",
            description="Test Device",
            hwid="USB\\VID_1A86&PID_7523",
            vid=0x1A86,
            pid=0x7523,
            driver_type=DriverType.CH340
        )
        
        assert port_info.device == "/dev/ttyUSB0"
        assert port_info.name == "USB Serial Port"
        assert port_info.description == "Test Device"
        assert port_info.driver_type == DriverType.CH340
        assert port_info.vid == 0x1A86
        assert port_info.pid == 0x7523
    
    def test_serial_port_info_str(self):
        """Test SerialPortInfo string representation."""
        port_info = SerialPortInfo(
            device="/dev/ttyUSB0",
            name="Test Port",
            description="Test Device",
            driver_type=DriverType.GENERIC
        )
        
        str_repr = str(port_info)
        assert "/dev/ttyUSB0 - Test Port (Test Device)" in str_repr
    
    def test_serial_port_info_to_dict(self):
        """Test SerialPortInfo to_dict conversion."""
        port_info = SerialPortInfo(
            device="/dev/ttyUSB0",
            vid=0x1234,
            pid=0x5678,
            driver_type=DriverType.CP2102
        )
        
        port_dict = port_info.to_dict()
        expected_keys = {'device', 'name', 'description', 'hwid', 'vid', 'pid', 'driver_type'}
        
        for key in expected_keys:
            assert key in port_dict
        
        assert port_dict['device'] == "/dev/ttyUSB0"
        assert port_dict['vid'] == 0x1234
        assert port_dict['driver_type'] == "cp2102"


class TestDriverType:
    """Test DriverType enum."""
    
    def test_driver_type_values(self):
        """Test DriverType enum values."""
        assert DriverType.CH340.value == "ch340"
        assert DriverType.CP2102.value == "cp2102"
        assert DriverType.GENERIC.value == "generic"
        assert DriverType.AUTO.value == "auto"


class TestCH340Driver:
    """Test CH340 driver implementation."""
    
    def test_init(self):
        """Test CH340Driver initialization."""
        driver = CH340Driver()
        assert driver.driver_type == DriverType.CH340
        assert hasattr(driver, 'CH340_VID')
        assert hasattr(driver, 'CH340_PID')
    
    @patch('src.core.drivers.ch340.serial.tools.list_ports.comports')
    def test_detect_devices_empty(self, mock_comports):
        """Test device detection with no devices."""
        mock_comports.return_value = []
        
        driver = CH340Driver()
        devices = driver.detect_devices()
        
        assert devices == []
        mock_comports.assert_called_once()
    
    @patch('src.core.drivers.ch340.serial.tools.list_ports.comports')
    def test_detect_devices_with_ch340(self, mock_comports):
        """Test device detection with CH340 devices."""
        # Mock a CH340 device
        mock_port = Mock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.name = "CH340"
        mock_port.description = "USB-SERIAL CH340"
        mock_port.vid = 0x1A86
        mock_port.pid = 0x7523
        mock_port.hwid = "USB\\VID_1A86&PID_7523"
        
        mock_comports.return_value = [mock_port]
        
        driver = CH340Driver()
        devices = driver.detect_devices()
        
        assert len(devices) == 1
        assert devices[0].device == "/dev/ttyUSB0"
        assert devices[0].driver_type == DriverType.CH340
        assert devices[0].vid == 0x1A86
        assert devices[0].pid == 0x7523
        mock_comports.assert_called_once()
    
    def test_get_supported_properties(self):
        """Test CH340 driver properties."""
        driver = CH340Driver()
        properties = driver.get_supported_properties()
        
        assert properties['device_vid'] == 0x1A86
        assert 'device_pids' in properties
        assert 0x7523 in properties['device_pids']
        assert properties['max_baudrate'] == 921600
        assert properties['characteristics']['low_cost'] is True
        assert properties['characteristics']['common_in_arduino'] is True


class TestCP2102Driver:
    """Test CP2102 driver implementation."""
    
    def test_init(self):
        """Test CP2102Driver initialization."""
        driver = CP2102Driver()
        assert driver.driver_type == DriverType.CP2102
        assert hasattr(driver, 'vid_pattern')
        assert hasattr(driver, 'pid_pattern')
    
    @patch('src.core.drivers.cp2102.serial.tools.list_ports.comports')
    def test_detect_devices_with_cp2102(self, mock_comports):
        """Test device detection with CP2102 devices."""
        # Mock a CP2102 device
        mock_port = Mock()
        mock_port.device = "/dev/ttyUSB1"
        mock_port.name = "CP2102"
        mock_port.description = "CP2102 USB UART"
        mock_port.vid = 0x10C4
        mock_port.pid = 0xEA60
        
        mock_comports.return_value = [mock_port]
        
        driver = CP2102Driver()
        devices = driver.detect_devices()
        
        assert len(devices) == 1
        assert devices[0].device == "/dev/ttyUSB1"
        assert devices[0].driver_type == DriverType.CP2102
        assert devices[0].vid == 0x10C4
        assert devices[0].pid == 0xEA60
        mock_comports.assert_called_once()
    
    def test_get_supported_properties(self):
        """Test CP2102 driver properties."""
        driver = CP2102Driver()
        properties = driver.get_supported_properties()
        
        assert properties['device_vid'] == 0x10C4
        assert 'device_pids' in properties
        assert 0xEA60 in properties['device_pids']
        assert properties['max_baudrate'] == 1000000
        assert properties['characteristics']['professional_grade'] is True
        assert properties['characteristics']['configurable'] is True


class TestGenericSerialDriver:
    """Test Generic serial driver implementation."""
    
    def test_init(self):
        """Test GenericSerialDriver initialization."""
        driver = GenericSerialDriver()
        assert driver.driver_type == DriverType.GENERIC
    
    @patch('src.core.drivers.generic.serial.tools.list_ports.comports')
    def test_detect_devices(self, mock_comports):
        """Test device detection with generic driver."""
        # Mock a generic serial port
        mock_port = Mock()
        mock_port.device = "/dev/ttyS0"
        mock_port.name = "Generic Serial"
        mock_port.description = "Serial Port"
        
        mock_comports.return_value = [mock_port]
        
        driver = GenericSerialDriver()
        devices = driver.detect_devices()
        
        assert len(devices) == 1
        assert devices[0].device == "/dev/ttyS0"
        assert devices[0].driver_type == DriverType.GENERIC
        mock_comports.assert_called_once()
    
    def test_get_supported_properties(self):
        """Test Generic driver properties."""
        driver = GenericSerialDriver()
        properties = driver.get_supported_properties()
        
        assert properties['characteristics']['fallback_driver'] is True
        assert properties['characteristics']['universal_compatibility'] is True
        assert properties['supports_custom_baudrates'] is True


class TestDriverManager:
    """Test DriverManager functionality."""
    
    def test_init(self):
        """Test DriverManager initialization."""
        manager = DriverManager()
        assert hasattr(manager, 'drivers')
        assert isinstance(manager.drivers, dict)
    
    @patch('src.core.drivers.manager.CH340Driver')
    @patch('src.core.drivers.manager.CP2102Driver')
    @patch('src.core.drivers.manager.GenericSerialDriver')
    def test_initialization_with_drivers(self, mock_generic, mock_cp2102, mock_ch340):
        """Test DriverManager with all drivers available."""
        # Mock all drivers as available
        mock_ch340.return_value.is_available = True
        mock_cp2102.return_value.is_available = True
        mock_generic.return_value.is_available = True
        
        manager = DriverManager()
        
        # Check that drivers were initialized
        mock_ch340.assert_called_once()
        mock_cp2102.assert_called_once()
        mock_generic.assert_called_once()
        
        # Check that all drivers are in the dict
        assert DriverType.CH340 in manager.drivers
        assert DriverType.CP2102 in manager.drivers
        assert DriverType.GENERIC in manager.drivers
    
    def test_detect_all_devices(self):
        """Test detecting all devices."""
        manager = DriverManager()
        devices = manager.detect_all_devices()
        
        # Should return a list (even if empty)
        assert isinstance(devices, list)
    
    def test_get_available_driver_types(self):
        """Test getting available driver types."""
        manager = DriverManager()
        available_types = manager.get_available_driver_types()
        
        assert isinstance(available_types, list)
        assert DriverType.GENERIC in available_types  # Generic should always be available
    
    def test_get_driver_for_type(self):
        """Test getting driver for specific type."""
        manager = DriverManager()
        
        # Test getting generic driver
        generic_driver = manager.get_driver_for_type(DriverType.GENERIC)
        assert generic_driver is not None
        assert generic_driver.driver_type == DriverType.GENERIC
        
        # Test getting non-existent driver
        unknown_driver = manager.get_driver_for_type(DriverType.AUTO)
        assert unknown_driver is None