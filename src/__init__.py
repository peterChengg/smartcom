"""
SmartCom - 自定义串口通信工具

A powerful serial port communication tool with customizable protocol parsing,
data filtering, waveform visualization, and multi-window display capabilities.
"""

__version__ = "0.1.0-alpha"
__author__ = "SmartCom Team"
__email__ = "team@smartcom.dev"

from src.core.serial_manager import SerialManager
from src.core.protocol_parser import ProtocolParser
from src.ui.main_window import MainWindow

__all__ = [
    "SerialManager",
    "ProtocolParser", 
    "MainWindow",
]