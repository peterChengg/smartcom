"""
Serial configuration management UI module.

This module provides user interface components for serial port configuration,
including port selection, parameter setting, and connection management.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class Parity(Enum):
    """Serial parity options."""

    NONE = "N"
    EVEN = "E"
    ODD = "O"
    MARK = "M"
    SPACE = "S"


class StopBits(Enum):
    """Serial stop bits options."""

    ONE = 1
    ONE_FIVE = 1.5
    TWO = 2


@dataclass
class PortConfig:
    """Serial port configuration."""

    port: str
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout: float = 1.0
    xonxoff: bool = False
    rtscts: bool = False
    dsrdtr: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "parity": self.parity,
            "stopbits": self.stopbits,
            "timeout": self.timeout,
            "xonxoff": self.xonxoff,
            "rtscts": self.rtscts,
            "dsrdtr": self.dsrdtr,
        }


class PortConfigDialog(QWidget):
    """Serial port configuration dialog."""

    # Signals
    config_changed = pyqtSignal(dict)
    connection_requested = pyqtSignal(dict)
    config_saved = pyqtSignal()

    # Standard baud rates
    BAUDRATES = [
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

    # Standard parity values
    PARITY_MAP = {
        "N": Parity.NONE,
        "E": Parity.EVEN,
        "O": Parity.ODD,
        "M": Parity.MARK,
        "S": Parity.SPACE,
    }

    # Standard stop bits values
    STOPBITS_MAP = {
        1: StopBits.ONE,
        1.5: StopBits.ONE_FIVE,
        2: StopBits.TWO,
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current_config = PortConfig(port="")
        self.setWindowTitle("Serial Port Configuration")
        self.resize(500, 600)

        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup UI layout."""
        layout = QVBoxLayout()

        # Port selection
        port_group = self.create_port_selection_group()
        layout.addWidget(port_group)

        # Connection parameters
        params_group = self.create_connection_params_group()
        layout.addWidget(params_group)

        # Control buttons
        buttons_group = self.create_control_buttons()
        layout.addWidget(buttons_group)

        layout.addStretch()

        self.load_saved_configs()

    def create_port_selection_group(self) -> QGroupBox:
        """Create port selection group."""
        group = QGroupBox("Port Selection")
        layout = QFormLayout()

        self.port_combo = QComboBox()
        self.refresh_ports_button = QPushButton("Refresh")
        self.refresh_ports_button.clicked.connect(self.refresh_ports)

        layout.addRow(QLabel("Port:"), self.port_combo, self.refresh_ports_button)
        group.setLayout(layout)

        return group

    def create_connection_params_group(self) -> QGroupBox:
        """Create connection parameters group."""
        group = QGroupBox("Connection Parameters")
        layout = QFormLayout()

        # Baud rate
        layout.addRow("Baud Rate:", self.create_baudrate_combo())

        # Data bits
        layout.addRow("Data Bits:", self.create_bytesize_combo())

        # Parity
        layout.addRow("Parity:", self.create_parity_combo())

        # Stop bits
        layout.addRow("Stop Bits:", self.create_stopbits_combo())

        # Flow control
        flow_control_layout = QHBoxLayout()

        self.xonxoff_cb = QCheckBox("XON/XOFF")
        self.rtscts_cb = QCheckBox("RTS/CTS")
        self.dsrdtr_cb = QCheckBox("DTR/DSR")

        flow_control_layout.addWidget(self.xonxoff_cb)
        flow_control_layout.addWidget(self.rtscts_cb)
        flow_control_layout.addWidget(self.dsrdtr_cb)
        flow_control_layout.addStretch()

        layout.addRow("Flow Control:", self.create_widget(flow_control_layout))

        # Timeout
        layout.addRow("Timeout (s):", self.create_timeout_spinbox())

        group.setLayout(layout)

        return group

    def create_baudrate_combo(self) -> QComboBox:
        """Create baudrate selection combo box."""
        combo = QComboBox()
        combo.setEditable(False)

        for rate in self.BAUDRATES:
            combo.addItem(f"{rate}")

        if self.current_config.baudrate:
            index = combo.findText(str(self.current_config.baudrate))
            if index >= 0:
                combo.setCurrentIndex(index)

        return combo

    def create_bytesize_combo(self) -> QComboBox:
        """Create data bits selection combo box."""
        combo = QComboBox()
        combo.setEditable(False)

        for bits in [5, 6, 7, 8]:
            combo.addItem(f"{bits} bits")

        if self.current_config.bytesize:
            index = combo.findText(str(self.current_config.bytesize))
            if index >= 0:
                combo.setCurrentIndex(index)

        return combo

    def create_parity_combo(self) -> QComboBox:
        """Create parity selection combo box."""
        combo = QComboBox()
        combo.setEditable(False)

        combo.addItem("None (N)")
        combo.addItem("Even (E)")
        combo.addItem("Odd (O)")
        combo.addItem("Mark (M)")
        combo.addItem("Space (S)")

        if self.current_config.parity:
            index = combo.findText(self.current_config.parity)
            if index >= 0:
                combo.setCurrentIndex(index)

        return combo

    def create_stopbits_combo(self) -> QComboBox:
        """Create stop bits selection combo box."""
        combo = QComboBox()
        combo.setEditable(False)

        combo.addItem("1")
        combo.addItem("1.5")
        combo.addItem("2")

        if self.current_config.stopbits:
            index = combo.findText(str(self.current_config.stopbits))
            if index >= 0:
                combo.setCurrentIndex(index)

        return combo

    def create_timeout_spinbox(self) -> QSpinBox:
        """Create timeout spinbox."""
        spinbox = QSpinBox()
        spinbox.setRange(100, 10000, 100)  # 100ms to 10s
        spinbox.setValue(1000)
        spinbox.setSuffix(" ms")

        if self.current_config.timeout:
            spinbox.setValue(int(self.current_config.timeout * 1000))

        return spinbox

    def create_control_buttons(self) -> QHBoxLayout:
        """Create control buttons."""
        layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.on_disconnect)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.on_apply)

        self.save_btn = QPushButton("Save Config")
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        layout.addWidget(self.connect_btn)
        layout.addWidget(self.disconnect_btn)
        layout.addWidget(self.apply_btn)
        layout.addWidget(self.save_btn)
        layout.addStretch()

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def refresh_ports(self) -> None:
        """Refresh available serial ports."""
        # TODO: Implement port refresh
        logger.info("Refresh ports called")
        self.port_combo.clear()
        self.port_combo.addItems(["/dev/ttyUSB0", "/dev/ttyUSB1"])

    def on_connect(self) -> None:
        """Handle connect button click."""
        config = self.get_current_config()
        self.connection_requested.emit(config)
        self.logger.info(f"Connect requested: {config}")

    def on_disconnect(self) -> None:
        """Handle disconnect button click."""
        self.logger.info("Disconnect requested")
        self.connection_requested.emit({"action": "disconnect"})

    def on_apply(self) -> None:
        """Handle apply button click."""
        config = self.get_current_config()
        self.config_changed.emit(config)
        self.logger.info(f"Config changed: {config}")

    def on_save(self) -> None:
        """Handle save button click."""
        config = self.get_current_config()
        self.config_saved.emit(config)
        self.logger.info(f"Config saved: {config}")

    def get_current_config(self) -> PortConfig:
        """Get current configuration from UI."""
        return PortConfig(
            port=self.port_combo.currentText() or "",
            baudrate=int(self.current_baudrate_combo.currentText() or 9600),
            parity=self.current_parity_combo.currentText() or "N",
            stopbits=int(self.current_stopbits_combo.currentText() or 1),
            timeout=float(self.current_timeout_spinbox.value()) / 1000.0,
            xonxoff=self.xonxoff_cb.isChecked(),
            rtscts=self.rtscts_cb.isChecked(),
            dsrdtr=self.dsrdtr_cb.isChecked(),
        )

    def load_saved_configs(self) -> None:
        """Load saved configurations."""
        # TODO: Implement config loading
        logger.info("Load saved configs called")

    def set_config(self, config: PortConfig) -> None:
        """Set configuration."""
        self.current_config = config
        logger.info(f"Config set: {config}")

        # Update UI elements
        if config.port:
            index = self.port_combo.findText(config.port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

        if config.baudrate:
            index = self.current_baudrate_combo.findText(str(config.baudrate))
            if index >= 0:
                self.current_baudrate_combo.setCurrentIndex(index)

        # TODO: Update other UI elements
