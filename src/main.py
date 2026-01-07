#!/usr/bin/env python3
"""
SmartCom - 自定义串口工具主入口
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# PyQt6 imports will be added when GUI is implemented
# from PyQt6.QtWidgets import QApplication
# from PyQt6.QtCore import QSettings

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import AppSettings
from src.ui.main_window import MainWindow


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging for the application."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> int:
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting SmartCom application")

    try:
        # Create settings
        settings = AppSettings()

        # Create main window (GUI will be implemented later)
        main_window = MainWindow(settings)

        logger.info("Application initialized successfully")

        # For now, just return success
        # GUI event loop will be implemented when PyQt6 is added
        return 0

    except Exception as e:
        logger.error("Failed to start application: %s", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
