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
