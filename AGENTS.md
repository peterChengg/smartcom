# AGENTS.md

This file contains guidelines and commands for agentic coding agents working on the SmartCom project.

## Project Overview

SmartCom is a custom serial port tool that supports multiple serial port drivers (CH340, CP2102) with customizable application-layer protocols. The tool provides advanced features for protocol parsing, data filtering, waveform visualization, and multi-window display capabilities.

## Tech Stack

- **Language**: Python 3.8+
- **GUI Framework**: PyQt6
- **Serial Communication**: pyserial-asyncio
- **Testing**: pytest, pytest-qt
- **Code Quality**: black, flake8, mypy
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, pyqtgraph

## Build/Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run code formatting
black src/ tests/

# Run linting
flake8 src/ tests/

# Run type checking
mypy src/

# Run all tests
python -m pytest

# Run a single test
python -m pytest tests/test_protocol_parser.py -v

# Run tests with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/ui/ -v

# Run performance tests
python -m pytest tests/performance/ -v

# Run the application
python -m src.main
```

## Code Style Guidelines

### General Principles
- Write clear, self-documenting code
- Use meaningful variable and function names
- Keep functions small and focused on a single responsibility
- Add comments only when the code's intent is not obvious
- Follow PEP 8 for Python code style

### Naming Conventions
- **Variables**: `snake_case` (e.g., `serial_buffer`, `protocol_config`)
- **Functions**: `snake_case` (e.g., `parse_protocol_data`, `filter_serial_data`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT_MS`, `MAX_BUFFER_SIZE`)
- **Classes**: `PascalCase` (e.g., `ProtocolParser`, `SerialPortManager`)
- **Private members**: `_prefix` (e.g., `_internal_buffer`, `_parse_header`)
- **File names**: `snake_case` (e.g., `protocol_parser.py`, `serial_manager.py`)

### Import Organization
```python
# Standard library imports
import asyncio
import time
from typing import List, Dict, Optional, Any

# Third-party imports
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from pyserial_asyncio import Serial

# Local imports
from src.core.serial_driver import SerialDriver
from src.utils.protocol_parser import ProtocolParser
```

### Type Hints
- Use type hints for all function signatures and class attributes
- Prefer `Optional[T]` over `None` defaults where appropriate
- Use `Union[T, U]` for multiple possible types
- Define custom types for complex data structures
- Use `Protocol` for abstract interfaces

### Error Handling
```python
# Custom exception hierarchy
class SmartComError(Exception):
    """Base exception for SmartCom"""
    pass

class SerialConnectionError(SmartComError):
    """Raised when serial connection fails"""
    pass

class ProtocolParseError(SmartComError):
    """Raised when protocol parsing fails"""
    pass

# Error handling pattern
async def connect_serial(self, port: str, baudrate: int) -> bool:
    try:
        self.serial = await Serial.create(port, baudrate)
        return True
    except SerialException as e:
        logger.error(f"Failed to connect to {port}: {e}")
        raise SerialConnectionError(f"Cannot connect to {port}") from e
```

### Constants and Configuration
```python
# Use dataclasses for configuration
from dataclasses import dataclass
from typing import Final

@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1
    timeout: float = 1.0

# Constants module
DEFAULT_TIMEOUT_MS: Final = 500
MAX_BUFFER_SIZE: Final = 1024 * 1024  # 1MB
SUPPORTED_BAUDRATES: Final = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
```

### Protocol Implementation Patterns
```python
# Protocol field definition
@dataclass
class ProtocolField:
    name: str
    offset: int
    length: int
    field_type: str  # 'head', 'length', 'data', 'checksum', etc.
    validation: Optional[str] = None

# Protocol parser interface
class ProtocolParser(ABC):
    @abstractmethod
    async def parse(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse incoming data and return protocol fields"""
        pass

    @abstractmethod
    def validate(self, packet: Dict[str, Any]) -> bool:
        """Validate parsed packet"""
        pass
```

### Async/Await Patterns
- Use `asyncio` for all I/O operations (serial communication, file I/O)
- Implement proper cancellation handling
- Use `asyncio.gather()` for concurrent operations
- Implement timeout handling with `asyncio.wait_for()`

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use structured logging
logger.info("Serial connection established", extra={
    'port': port,
    'baudrate': baudrate,
    'timestamp': time.time()
})

# Exception logging with context
logger.exception("Protocol parse failed", extra={
    'data_length': len(data),
    'buffer_size': len(self.buffer)
})
```

## Testing Guidelines

### Unit Tests
- Test all public methods with various input scenarios
- Mock external dependencies (serial ports, file I/O)
- Use `pytest.mark.asyncio` for async functions
- Parameterize tests for multiple test cases

### Integration Tests
- Test protocol parsing with real data streams
- Test GUI interactions with `pytest-qt`
- Test serial communication with mock devices

### Performance Tests
- Protocol parsing must complete in < 10ms
- Memory usage must stay < 100MB
- Test with high data rates (up to 921600 bps)

## Git Workflow

### Branch Naming
```
feature/agent-name/task-id    # e.g., feature/agent-a/task-a1
bugfix/agent-name/issue-id    # e.g., bugfix/agent-b/issue-123
```

### Commit Messages
```
[Agent] task-id: brief description

Detailed explanation of changes...

Closes #task-id
```

## Development Workflow

1. **Setup**: Install dependencies and configure development environment
2. **Implementation**: Follow code style guidelines and write tests first
3. **Quality Checks**: Run black, flake8, mypy, and pytest before committing
4. **Testing**: Ensure all tests pass and coverage > 80%
5. **Documentation**: Update relevant documentation for new features

## Performance Requirements

- **Protocol parsing**: < 10ms latency
- **Memory usage**: < 100MB during normal operation
- **CPU usage**: < 5% during normal operation
- **Data throughput**: Support up to 921600 bps
- **Test coverage**: > 80% for all new code
