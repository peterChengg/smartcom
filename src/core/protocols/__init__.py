"""
Protocol definition and DSL parsing modules.

This package provides:
- DSL parser for user-friendly protocol configuration
- Encryption/decryption interfaces
- Protocol validation mechanisms
"""

from .dsl_parser import (
    ProtocolDSLParseError,
    ProtocolDSLParser,
)

from .encryption import (
    AESEncryption,
    Base64Encoding,
    EncryptionError,
    EncryptionFactory,
    EncryptionInterface,
    NoEncryption,
    XOREncryption,
)

__all__ = [
    # DSL Parser
    "ProtocolDSLParser",
    "ProtocolDSLParseError",
    # Encryption
    "EncryptionInterface",
    "NoEncryption",
    "XOREncryption",
    "AESEncryption",
    "Base64Encoding",
    "EncryptionFactory",
    "EncryptionError",
]
