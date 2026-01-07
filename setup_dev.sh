#!/bin/bash

# SmartCom Development Environment Setup Script
# This script sets up a complete development environment for SmartCom

set -e  # Exit on any error

echo "🚀 Setting up SmartCom Development Environment..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the project root."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
echo "🔍 Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python found: $PYTHON_VERSION"
else
    echo "❌ Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is available
echo "🔍 Checking pip installation..."
if command_exists pip3; then
    echo "✅ pip found"
else
    echo "❌ Error: pip3 is not installed. Please install pip3."
    exit 1
fi

# Create virtual environment
echo "🏗️  Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing it..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🛠️  Installing development dependencies..."
pip install pytest pytest-qt pytest-cov pytest-asyncio black flake8 mypy coverage

# Install pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
if command_exists pre-commit; then
    pre-commit install
else
    echo "⚠️  pre-commit not found. Installing it..."
    pip install pre-commit
    pre-commit install
fi

# Create development configuration files
echo "📝 Setting up development configuration..."

# Create pre-commit configuration if not exists
if [ ! -f ".pre-commit-config.yaml" ]; then
    cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF
    echo "✅ .pre-commit-config.yaml created"
fi

# Create development script directory
mkdir -p scripts

# Create useful development scripts
cat > scripts/run_tests.sh << 'EOF'
#!/bin/bash
# Run all tests with coverage
echo "🧪 Running all tests..."
source venv/bin/activate
python -m pytest --cov=src --cov-report=html --cov-report=term-missing -v
echo "📊 Coverage report generated in htmlcov/"
EOF

cat > scripts/run_lint.sh << 'EOF'
#!/bin/bash
# Run code quality checks
echo "🔍 Running code quality checks..."
source venv/bin/activate

echo "Running black..."
black --check src/ tests/
echo "Running flake8..."
flake8 src/ tests/
echo "Running mypy..."
mypy src/
echo "✅ All checks completed"
EOF

cat > scripts/format_code.sh << 'EOF'
#!/bin/bash
# Format code with black
echo "🎨 Formatting code..."
source venv/bin/activate
black src/ tests/
echo "✅ Code formatted"
EOF

cat > scripts/clean.sh << 'EOF'
#!/bin/bash
# Clean build artifacts
echo "🧹 Cleaning build artifacts..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
rm -rf htmlcov/
rm -rf .coverage
rm -rf .pytest_cache/
rm -rf .mypy_cache/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "✅ Clean completed"
EOF

# Make scripts executable
chmod +x scripts/*.sh

# Create development environment file
if [ ! -f ".env.example" ]; then
    cat > .env.example << 'EOF'
# SmartCom Development Environment Configuration
# Copy this file to .env and modify as needed

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Test configuration
TEST_SERIAL_PORT=/dev/ttyUSB0
TEST_BAUDRATE=115200

# Development flags
DEBUG_MODE=true
ENABLE_MOCK_DRIVERS=true
EOF
    echo "✅ .env.example created"
fi

# Verify installation
echo "🔍 Verifying installation..."
source venv/bin/activate

# Test Python imports
python -c "
import sys
sys.path.insert(0, 'src')
try:
    import src.core.serial_manager
    import src.core.protocol_parser
    import src.ui.main_window
    print('✅ All modules imported successfully')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

# Test tools
echo "🧪 Testing development tools..."
python -m pytest --version >/dev/null 2>&1 && echo "✅ pytest working" || echo "❌ pytest failed"
black --version >/dev/null 2>&1 && echo "✅ black working" || echo "❌ black failed"
flake8 --version >/dev/null 2>&1 && echo "✅ flake8 working" || echo "❌ flake8 failed"
mypy --version >/dev/null 2>&1 && echo "✅ mypy working" || echo "❌ mypy failed"

# Create activation script
cat > activate_dev.sh << 'EOF'
#!/bin/bash
# Activate SmartCom development environment
echo "🔌 Activating SmartCom development environment..."
source venv/bin/activate
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
echo "✅ Development environment activated"
echo "📝 To start development:"
echo "   - Run tests: ./scripts/run_tests.sh"
echo "   - Format code: ./scripts/format_code.sh"
echo "   - Run linting: ./scripts/run_lint.sh"
echo "   - Clean project: ./scripts/clean.sh"
EOF

chmod +x activate_dev.sh

echo ""
echo "🎉 SmartCom development environment setup complete!"
echo "=================================================="
echo ""
echo "📋 Next steps:"
echo "   1. Activate environment: source activate_dev.sh"
echo "   2. Copy .env.example to .env and configure as needed"
echo "   3. Start developing!"
echo ""
echo "🛠️  Available commands:"
echo "   - Run tests: ./scripts/run_tests.sh"
echo "   - Format code: ./scripts/format_code.sh"
echo "   - Run linting: ./scripts/run_lint.sh"
echo "   - Clean project: ./scripts/clean.sh"
echo ""
echo "📚 For development guidelines, see DEVELOPMENT.md"
echo "🤝 For contribution guidelines, see CONTRIBUTING.md"
echo ""
echo "Happy coding! 🚀"
