"""
Main application window.

This module provides the main GUI window for SmartCom application
with multi-window display capabilities.
"""

from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.config.settings import AppSettings

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window."""

    def __init__(self, settings: "AppSettings"):
        self.settings = settings
        logger.info("Main window initialized")

    def show(self):
        """Show the main window."""
        # TODO: Implement actual window display
        logger.info("Main window shown")
