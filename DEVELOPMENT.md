# SmartCom Development Guide

This document provides comprehensive guidelines for developing SmartCom, a custom serial port communication tool.

## 🎯 Development Philosophy

SmartCom aims to be:
- **Modular**: Clear separation of concerns with well-defined interfaces
- **Extensible**: Easy to add new protocols, drivers, and features
- **Performant**: Real-time processing with minimal latency
- **Reliable**: Robust error handling and recovery mechanisms
- **User-friendly**: Intuitive interface for technical users

## 🏗️ Architecture Overview

### Core Components

1. **Serial Communication Layer**
   - Driver abstraction (CH340, CP2102, etc.)
   - Connection management and configuration
   - Async data transmission and reception

2. **Protocol Parsing Layer**
   - Configurable protocol definitions
   - Real-time parsing engine
   - Validation and error handling

3. **User Interface Layer**
   - Multi-window display system
   - Real-time data visualization
   - Configuration and settings management

4. **Data Processing Layer**
   - Filtering and transformation
   - Buffer management
   - Performance optimization

## 📁 Project Structure in Detail

### Core Module (`src/core/`)

#### Serial Management
```python
# Serial driver abstraction
class SerialDriver(ABC):
    @abstractmethod
    def detect_devices() -> List[str]: ...
    
    @abstractmethod
    async def connect(config: SerialConfig) -> bool: ...

# High-level manager
class SerialManager:
    def __init__(self, driver: SerialDriver): ...
    async def write_data(self, data: bytes) -> bool: ...
    async def read_data(self, size: int = 1024) -> bytes: ...
```

#### Protocol Parsing
```python
# Protocol definition
@dataclass
class ProtocolDefinition:
    name: str
    fields: List[ProtocolField]
    encryption: Optional[str] = None

# Parsing engine
class ProtocolParser:
    async def parse_data(self, data: bytes) -> Optional[Dict[str, Any]]: ...
    def validate_packet(self, packet: Dict[str, Any]) -> bool: ...
```

### UI Module (`src/ui/`)

#### Window Management
```python
class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings): ...
    
class WindowManager:
    def create_window(self, window_type: str) -> QWidget: ...
    def sync_data(self, data: Any): ...
```

### Configuration Module (`src/config/`)

```python
class AppSettings:
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def save(self) -> None: ...
```

## 🔧 Development Standards

### Code Style Guidelines

#### Naming Conventions
- **Classes**: `PascalCase` (e.g., `SerialManager`, `ProtocolParser`)
- **Functions**: `snake_case` (e.g., `parse_protocol_data`, `connect_serial`)
- **Variables**: `snake_case` (e.g., `serial_buffer`, `protocol_config`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT_MS`, `MAX_BUFFER_SIZE`)
- **Private members**: `_prefix` (e.g., `_internal_buffer`, `_parse_header`)

#### Function Design
```python
# Good function design
async def parse_serial_data(
    self, 
    data: bytes, 
    timeout: float = DEFAULT_TIMEOUT_MS
) -> Optional[Dict[str, Any]]:
    """
    Parse incoming serial data according to configured protocol.
    
    Args:
        data: Raw bytes to parse
        timeout: Maximum parsing time in milliseconds
        
    Returns:
        Parsed data dictionary or None if parsing failed
        
    Raises:
        ProtocolParseError: When protocol format is invalid
    """
    # Implementation...
```

#### Error Handling
```python
# Custom exception hierarchy
class SmartComError(Exception):
    """Base exception for SmartCom application."""
    pass

class SerialConnectionError(SmartComError):
    """Raised when serial connection fails."""
    pass

# Error handling pattern
async def connect_to_device(self, port: str) -> bool:
    try:
        await self.driver.connect(SerialConfig(port=port))
        return True
    except SerialException as e:
        logger.error("Connection failed", port=port, error=str(e))
        raise SerialConnectionError(f"Cannot connect to {port}") from e
```

### Async Programming Guidelines

#### Best Practices
- Use `asyncio` for all I/O operations
- Implement proper cancellation with `asyncio.CancelledError`
- Use `asyncio.gather()` for concurrent operations
- Implement timeouts with `asyncio.wait_for()`

#### Example
```python
class DataProcessor:
    async def process_data_stream(self):
        try:
            while True:
                data = await asyncio.wait_for(
                    self.serial.read_data(), 
                    timeout=1.0
                )
                await self.process_packet(data)
        except asyncio.TimeoutError:
            logger.warning("Data stream timeout")
        except asyncio.CancelledError:
            logger.info("Data processing cancelled")
            raise
```

### Testing Guidelines

#### Test Structure
```python
class TestSerialManager:
    @pytest.fixture
    def mock_driver(self):
        with patch('src.core.drivers.ch340.CH340Driver') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_driver):
        manager = SerialManager(mock_driver)
        result = await manager.connect(SerialConfig(port="/dev/ttyUSB0"))
        assert result is True
        mock_driver.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_write_data_not_connected(self):
        manager = SerialManager()
        result = await manager.write_data(b"test")
        assert result is False
```

#### Performance Testing
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_protocol_parsing_performance():
    parser = ProtocolParser(test_protocol)
    test_data = generate_large_dataset(10000)
    
    start_time = time.time()
    for data in test_data:
        await parser.parse_data(data)
    
    parse_time = time.time() - start_time
    avg_time = parse_time / len(test_data) * 1000
    
    assert avg_time < 10, f"Parse time {avg_time:.2f}ms > 10ms"
```

## 🔍 Debugging and Development

### Logging Strategy

Use structured logging with contextual information:
```python
import logging

logger = logging.getLogger(__name__)

def process_packet(self, packet: bytes):
    logger.info(
        "Processing packet",
        packet_length=len(packet),
        packet_hash=hash(packet),
        timestamp=time.time()
    )
    
    try:
        result = self.parser.parse(packet)
        logger.debug("Packet parsed successfully", fields=list(result.keys()))
    except Exception as e:
        logger.exception(
            "Packet parsing failed",
            packet_data=packet.hex(),
            error=str(e)
        )
        raise
```

### Development Tools

#### Code Quality
```bash
# Format code
./scripts/format_code.sh

# Run quality checks
./scripts/run_lint.sh

# Type checking
mypy src/

# Test with coverage
./scripts/run_tests.sh
```

#### Debugging Serial Issues
```bash
# List available serial ports
python -c "
import serial.tools.list_ports
for port in serial.tools.list_ports.comports():
    print(f'{port.device}: {port.description}')
"

# Test serial connection
python -c "
import asyncio
import serial_asyncio

async def test_connection():
    try:
        reader, writer = await serial_asyncio.open_serial_connection(
            url='/dev/ttyUSB0', baudrate=115200
        )
        print('Connection successful')
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test_connection())
"
```

## 📊 Performance Requirements

### Key Metrics
- **Protocol parsing**: < 10ms latency per packet
- **Memory usage**: < 100MB during normal operation
- **CPU usage**: < 5% during normal operation
- **Data throughput**: Support up to 921600 bps
- **Test coverage**: > 80% for all new code

### Performance Testing
```python
# Benchmark script
def benchmark_protocol_parser():
    parser = ProtocolParser(test_protocol)
    test_packets = generate_test_packets(1000)
    
    # Measure parsing time
    times = []
    for packet in test_packets:
        start = time.perf_counter()
        result = asyncio.run(parser.parse_data(packet))
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print(f"Average parse time: {avg_time:.2f}ms")
    print(f"Maximum parse time: {max_time:.2f}ms")
    
    assert avg_time < 10, f"Average time {avg_time:.2f}ms exceeds 10ms limit"
```

## 🔐 Security Considerations

### Input Validation
- Validate all user inputs
- Sanitize serial data before processing
- Implement buffer size limits
- Handle malformed data gracefully

### Error Information
- Don't expose sensitive information in error messages
- Log detailed errors internally, show generic messages to users
- Implement proper exception handling throughout

## 📚 API Documentation

### Docstring Standards
```python
class ProtocolParser:
    """Parse serial data according to configurable protocol definitions.
    
    This class provides real-time protocol parsing capabilities with support
    for custom field definitions, validation rules, and error handling.
    
    Attributes:
        protocol: The protocol definition used for parsing
        buffer: Internal data buffer for incomplete packets
        timeout: Maximum parsing time in milliseconds
        
    Example:
        >>> protocol = ProtocolDefinition(
        ...     name="TestProtocol",
        ...     fields=[
        ...         ProtocolField("head", FieldType.HEAD, 1, 0, "0xFF"),
        ...         ProtocolField("length", FieldType.LENGTH, 1, 1),
        ...         ProtocolField("data", FieldType.DATA, -1, 2)
        ...     ]
        ... )
        >>> parser = ProtocolParser(protocol)
        >>> result = await parser.parse_data(b"\xFF\x05Hello")
        >>> print(result["data"])
        b"Hello"
    """
```

## 🚀 Deployment and Distribution

### Build Process
```bash
# Build source distribution
python setup.py sdist

# Build wheel distribution
python setup.py bdist_wheel

# Install from local build
pip install dist/smartcom-0.1.0-alpha-py3-none-any.whl
```

### Version Management
- Follow semantic versioning (semver)
- Update version in setup.py and src/__init__.py
- Tag releases in Git
- Maintain CHANGELOG.md

## 🔄 Continuous Integration

The project uses GitHub Actions for CI/CD:
- Automated testing on multiple Python versions
- Code quality checks
- Performance regression testing
- Documentation generation

## 📈 Monitoring and Analytics

### Application Metrics
- Connection success/failure rates
- Protocol parsing performance
- Memory and CPU usage
- Error rates and types

### Logging Strategy
- Structured logging with correlation IDs
- Different log levels for development vs production
- Log rotation and archival policies
- Error alerting and monitoring

---

This development guide serves as the comprehensive reference for SmartCom development. Follow these guidelines to ensure consistent, high-quality contributions to the project.