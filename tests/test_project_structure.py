"""
Test basic project structure and imports.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_project_imports():
    """Test that basic modules can be imported."""
    try:
        import src.config.settings
        import src.core.protocol_parser
        import src.core.serial_manager
        import src.ui.main_window

        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")


def test_version_exists():
    """Test that version is defined."""
    import src

    assert hasattr(src, "__version__")
    assert src.__version__ == "0.1.0-alpha"


def test_main_function_exists():
    """Test that main function exists."""
    from src.main import main

    assert callable(main)


class TestSerialManager:
    """Test basic SerialManager functionality."""

    def test_init(self):
        """Test SerialManager initialization."""
        from src.core.serial_manager import SerialManager

        manager = SerialManager()
        assert manager.config is None
        assert manager.is_connected is False

    def test_serial_config(self):
        """Test SerialConfig dataclass."""
        from src.core.serial_manager import SerialConfig

        config = SerialConfig(port="/dev/ttyUSB0", baudrate=115200)
        assert config.port == "/dev/ttyUSB0"
        assert config.baudrate == 115200


class TestProtocolParser:
    """Test basic ProtocolParser functionality."""

    def test_field_types(self):
        """Test FieldType enum."""
        from src.core.protocol_parser import FieldType

        assert FieldType.HEAD.value == "head"
        assert FieldType.DATA.value == "data"

    def test_protocol_field(self):
        """Test ProtocolField dataclass."""
        from src.core.protocol_parser import FieldType, ProtocolField

        field = ProtocolField(
            name="head", field_type=FieldType.HEAD, length=1, offset=0
        )
        assert field.name == "head"
        assert field.field_type == FieldType.HEAD
