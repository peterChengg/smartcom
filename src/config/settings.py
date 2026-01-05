"""
Application settings and configuration management.
"""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AppSettings:
    """Application settings manager."""
    
    def __init__(self):
        self.settings: Dict[str, Any] = {}
        logger.info("Settings manager initialized")
        
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get setting value."""
        return self.settings.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """Set setting value."""
        self.settings[key] = value
        logger.info("Setting updated", key=key)