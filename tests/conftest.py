"""
Pytest configuration for SmartCom.

This file sets up pytest for running tests in CI environments
without a display server.
"""

import os

# Set Qt platform to offscreen for CI environments
# This prevents the "libEGL.so.1: cannot open shared object file" error
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
