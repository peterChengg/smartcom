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
