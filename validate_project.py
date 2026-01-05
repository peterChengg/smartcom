#!/usr/bin/env python3
"""
Validate project structure and configuration.
"""

import os
import sys
from pathlib import Path


def check_file_structure():
    """Check that all required files exist."""
    required_files = [
        "src/__init__.py",
        "src/main.py",
        "src/core/__init__.py",
        "src/core/serial_manager.py", 
        "src/core/protocol_parser.py",
        "src/ui/__init__.py",
        "src/ui/main_window.py",
        "src/utils/__init__.py",
        "src/processing/__init__.py",
        "src/config/__init__.py",
        "src/config/settings.py",
        "src/storage/__init__.py",
        "tests/__init__.py",
        "tests/test_project_structure.py",
        "requirements.txt",
        "setup.py",
        "pytest.ini",
        ".flake8",
        "mypy.ini",
        "pyproject.toml",
    ]
    
    print("🔍 Checking file structure...")
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    print("✅ All required files exist")
    return True


def check_python_imports():
    """Check that Python modules can be imported."""
    print("\n🔍 Checking Python imports...")
    
    # Add src to path
    sys.path.insert(0, str(Path(".") / "src"))
    
    try:
        import src.core.serial_manager
        print("  ✅ src.core.serial_manager")
    except ImportError as e:
        print(f"  ❌ src.core.serial_manager: {e}")
        return False
        
    try:
        import src.core.protocol_parser
        print("  ✅ src.core.protocol_parser")
    except ImportError as e:
        print(f"  ❌ src.core.protocol_parser: {e}")
        return False
        
    try:
        import src.ui.main_window
        print("  ✅ src.ui.main_window")
    except ImportError as e:
        print(f"  ❌ src.ui.main_window: {e}")
        return False
        
    try:
        import src.config.settings
        print("  ✅ src.config.settings")
    except ImportError as e:
        print(f"  ❌ src.config.settings: {e}")
        return False
    
    print("✅ All imports successful")
    return True


def check_basic_functionality():
    """Check basic functionality."""
    print("\n🔍 Checking basic functionality...")
    
    sys.path.insert(0, str(Path(".") / "src"))
    
    try:
        import src
        assert hasattr(src, '__version__')
        assert src.__version__ == "0.1.0-alpha"
        print("  ✅ Version information correct")
    except Exception as e:
        print(f"  ❌ Version check failed: {e}")
        return False
        
    try:
        from src.main import main
        assert callable(main)
        print("  ✅ Main function exists")
    except Exception as e:
        print(f"  ❌ Main function check failed: {e}")
        return False
        
    try:
        from src.core.serial_manager import SerialManager, SerialConfig
        manager = SerialManager()
        config = SerialConfig(port="/dev/ttyUSB0")
        assert manager.is_connected == False
        assert config.port == "/dev/ttyUSB0"
        print("  ✅ SerialManager functionality")
    except Exception as e:
        print(f"  ❌ SerialManager check failed: {e}")
        return False
        
    try:
        from src.core.protocol_parser import FieldType, ProtocolField, ProtocolParser
        field = ProtocolField(name="test", field_type=FieldType.DATA, length=1, offset=0)
        assert field.name == "test"
        assert field.field_type == FieldType.DATA
        print("  ✅ ProtocolParser functionality")
    except Exception as e:
        print(f"  ❌ ProtocolParser check failed: {e}")
        return False
    
    print("✅ All functionality checks passed")
    return True


def main():
    """Main validation function."""
    print("🚀 SmartCom Project Structure Validation\n")
    
    all_passed = True
    
    # Check file structure
    if not check_file_structure():
        all_passed = False
        
    # Check imports
    if not check_python_imports():
        all_passed = False
        
    # Check functionality
    if not check_basic_functionality():
        all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All validation checks passed! ✅")
        print("Project structure is ready for development.")
        return 0
    else:
        print("❌ Some validation checks failed!")
        print("Please fix the issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())