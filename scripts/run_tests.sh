#!/bin/bash
# Run all tests with coverage
echo "🧪 Running all tests..."
source venv/bin/activate
python -m pytest --cov=src --cov-report=html --cov-report=term-missing -v
echo "📊 Coverage report generated in htmlcov/"
