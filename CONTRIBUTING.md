# Contributing to SmartCom

Thank you for your interest in contributing to SmartCom! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of serial communication and protocols

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/peterChengg/smartcom.git
   cd smartcom
   ```

2. **Run the development setup script**
   ```bash
   ./setup_dev.sh
   ```

3. **Activate the development environment**
   ```bash
   source activate_dev.sh
   ```

4. **Verify the setup**
   ```bash
   ./scripts/run_tests.sh
   ```

## 📋 Development Workflow

### 1. Create a Branch

Follow the branch naming convention:
```bash
feature/agent-name/task-id    # e.g., feature/agent-a/task-a1
bugfix/agent-name/issue-id    # e.g., bugfix/agent-b/issue-123
```

### 2. Development Process

- Write code following the style guidelines in [DEVELOPMENT.md](DEVELOPMENT.md)
- Write tests for new functionality
- Run quality checks before committing
- Test with different serial hardware if applicable

### 3. Quality Assurance

Before submitting a pull request, ensure:

- [ ] All tests pass: `./scripts/run_tests.sh`
- [ ] Code is formatted: `./scripts/format_code.sh`
- [ ] No linting errors: `./scripts/run_lint.sh`
- [ ] Type checking passes: `mypy src/`
- [ ] Test coverage is > 80%

### 4. Submitting Pull Requests

1. Push your branch to the repository
2. Create a pull request using the provided template
3. Ensure your PR passes all automated checks
4. Wait for code review

## 🏗️ Project Structure

```
smartcom/
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   ├── drivers/       # Serial port drivers
│   │   ├── protocols/     # Protocol parsing
│   │   ├── serial_manager.py
│   │   └── protocol_parser.py
│   ├── ui/                # User interface
│   │   └── windows/       # UI windows
│   ├── config/            # Configuration management
│   ├── utils/             # Utility functions
│   ├── processing/        # Data processing
│   └── storage/           # Data storage
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── ui/                # UI tests
│   └── performance/       # Performance tests
├── scripts/               # Development scripts
├── docs/                  # Documentation
└── requirements.txt       # Dependencies
```

## 🧪 Testing Guidelines

### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **UI Tests**: Test user interface with pytest-qt
- **Performance Tests**: Verify performance requirements

### Running Tests

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/ui/ -v
pytest tests/performance/ -v

# Run a single test file
pytest tests/test_serial_manager.py -v
```

### Writing Tests

- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- Mock external dependencies
- Test both success and failure cases
- Include edge cases and boundary conditions

## 📝 Code Style

### General Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Write self-documenting code
- Add comments only when necessary
- Keep functions small and focused

### Import Organization

```python
# Standard library imports
import asyncio
import time
from typing import List, Dict, Optional

# Third-party imports
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QWidget

# Local imports
from src.core.serial_driver import SerialDriver
```

### Type Hints

- Use type hints for all function signatures
- Prefer `Optional[T]` over `None` defaults
- Use `Union[T, U]` for multiple possible types

## 🐛 Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to reproduce**: Detailed steps to reproduce the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, hardware details
- **Logs**: Relevant error messages or logs

## 💡 Feature Requests

For feature requests:

- Use the feature request template
- Provide clear use cases and requirements
- Consider existing alternatives
- Be open to discussion and feedback

## 🔧 Development Tools

### Available Scripts

- `./scripts/run_tests.sh` - Run all tests with coverage
- `./scripts/run_lint.sh` - Run code quality checks
- `./scripts/format_code.sh` - Format code with black
- `./scripts/clean.sh` - Clean build artifacts

### IDE Configuration

VS Code settings are provided in `.vscode/settings.json`.

## 📚 Documentation

- **API Documentation**: Use docstrings for all public functions
- **User Documentation**: Update README.md for user-facing changes
- **Developer Documentation**: Keep DEVELOPMENT.md updated

## 🤝 Code Review Process

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are comprehensive and passing
- [ ] Documentation is updated
- [ ] Performance requirements are met
- [ ] Security considerations are addressed
- [ ] Error handling is appropriate

### Review Etiquette

- Be constructive and respectful
- Provide clear, actionable feedback
- Focus on the code, not the person
- Ask questions when something is unclear

## 🏷️ Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release notes
4. Tag the release
5. Build and distribute packages

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For general questions and discussions
- **Documentation**: Check DEVELOPMENT.md and AGENTS.md
- **Team**: Contact the development team for urgent issues

## 📄 License

By contributing to SmartCom, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to SmartCom! Your contributions help make this project better for everyone. 🚀