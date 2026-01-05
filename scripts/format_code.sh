#!/bin/bash
# Format code with black
echo "🎨 Formatting code..."
source venv/bin/activate
black src/ tests/
echo "✅ Code formatted"
