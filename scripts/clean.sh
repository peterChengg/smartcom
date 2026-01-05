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
