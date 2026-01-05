# SmartCom Documentation

Welcome to the SmartCom documentation center.

## 📚 Documentation Structure

### User Documentation
- [**Installation Guide**](user/installation.md) - How to install and set up SmartCom
- [**User Manual**](user/manual.md) - Complete user guide and features
- [**Protocol Configuration**](user/protocols.md) - How to configure custom protocols
- [**Troubleshooting**](user/troubleshooting.md) - Common issues and solutions

### Developer Documentation
- [**Development Guide**](../DEVELOPMENT.md) - Comprehensive development guidelines
- [**API Reference**](api/README.md) - Complete API documentation
- [**Architecture Overview**](developer/architecture.md) - System architecture and design
- [**Contributing Guide**](../CONTRIBUTING.md) - How to contribute to the project

### Technical Documentation
- [**Serial Port Drivers**](developer/drivers.md) - Driver implementation details
- [**Protocol Parser**](developer/protocol-parser.md) - Protocol parsing engine
- [**Performance Optimization**](developer/performance.md) - Performance tuning guide
- [**Testing Strategy**](developer/testing.md) - Testing approach and guidelines

## 🚀 Quick Start

### For Users

1. **Install SmartCom**
   ```bash
   pip install smartcom
   ```

2. **Run the application**
   ```bash
   smartcom
   ```

3. **Connect to your serial device**
   - Select the appropriate driver (CH340, CP2102, etc.)
   - Configure baud rate and other settings
   - Click "Connect"

### For Developers

1. **Clone the repository**
   ```bash
   git clone https://github.com/smartcom/smartcom.git
   cd smartcom
   ```

2. **Set up development environment**
   ```bash
   ./setup_dev.sh
   source activate_dev.sh
   ```

3. **Run tests**
   ```bash
   ./scripts/run_tests.sh
   ```

4. **Start development**
   ```bash
   python src/main.py
   ```

## 📖 Key Concepts

### Serial Communication
SmartCom provides a unified interface for different serial port drivers:
- **CH340 Driver**: For CH340-based USB-to-serial adapters
- **CP2102 Driver**: For Silicon Labs CP2102 devices
- **Generic Driver**: For standard serial ports

### Protocol Parsing
The flexible protocol parser supports:
- **Custom field definitions**: Define your own protocol structure
- **Real-time parsing**: Parse data as it arrives
- **Validation rules**: Ensure data integrity
- **Multiple protocols**: Support different protocols simultaneously

### Data Processing
Advanced data processing capabilities:
- **Regex filtering**: Filter data using regular expressions
- **Data transformation**: Convert and format data
- **Buffer management**: Efficient data buffering and storage
- **Performance optimization**: High-speed data processing

## 🔧 Configuration

SmartCom is highly configurable:

### Serial Port Configuration
```python
config = SerialConfig(
    port="/dev/ttyUSB0",
    baudrate=115200,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1.0
)
```

### Protocol Configuration
```python
protocol = ProtocolDefinition(
    name="CustomProtocol",
    fields=[
        ProtocolField("head", FieldType.HEAD, 1, 0, "0xFF"),
        ProtocolField("length", FieldType.LENGTH, 1, 1),
        ProtocolField("data", FieldType.DATA, -1, 2),
        ProtocolField("checksum", FieldType.CHECKSUM, 1, -1)
    ]
)
```

## 📊 Performance

SmartCom is designed for high-performance applications:

- **Low latency**: Protocol parsing < 10ms
- **High throughput**: Support for up to 921600 bps
- **Memory efficient**: < 100MB memory usage
- **CPU optimized**: < 5% CPU usage during normal operation

## 🛠️ Development Status

Current version: **0.1.0-alpha**

### Completed Features
- ✅ Project structure and development environment
- ✅ Serial port abstraction layer
- ✅ Basic protocol parsing framework
- ✅ Configuration management system
- ✅ Testing infrastructure

### In Progress
- 🔄 GUI implementation
- 🔄 Advanced protocol features
- 🔄 Data filtering and processing
- 🔄 Performance optimization

### Planned Features
- 📋 Waveform visualization
- 📋 Multi-window display system
- 📋 Advanced configuration options
- 📋 Plugin system

## 🤝 Getting Help

- **Documentation**: Check the relevant sections in this documentation center
- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/smartcom/smartcom/issues)
- **Discussions**: Join the [GitHub Discussions](https://github.com/smartcom/smartcom/discussions)
- **Community**: Connect with other users and developers

## 📄 License

SmartCom is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

---

For the most up-to-date information, visit the [SmartCom GitHub Repository](https://github.com/smartcom/smartcom).