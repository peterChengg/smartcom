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

from .advanced_fields import (
    AdvancedProtocolDefinition,
    AdvancedProtocolParser,
    ConditionalField,
    DynamicField,
    MultiFrameField,
    TransformationField,
    create_conditional_field,
    create_dynamic_field,
    create_multi_frame_field,
    create_transformation_field,
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
    # Advanced Fields
    "AdvancedProtocolDefinition",
    "AdvancedProtocolParser",
    "ConditionalField",
    "DynamicField",
    "MultiFrameField",
    "TransformationField",
    "create_conditional_field",
    "create_dynamic_field",
    "create_multi_frame_field",
    "create_transformation_field",
]
