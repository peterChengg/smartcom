"""
Protocol definition DSL parser.

This module provides a user-friendly DSL for defining custom serial communication protocols.
Supports YAML, JSON, and Python dictionary formats.
"""

import base64
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

import yaml

from ..protocol_parser import (
    FieldType,
    ParseError,
    ProtocolDefinition,
    ProtocolField,
)

logger = logging.getLogger(__name__)


class ProtocolDSLParseError(ParseError):
    """Protocol DSL parsing error."""

    pass


class ProtocolDSLParser:
    """
    Parser for protocol definition DSL.

    Supports multiple formats:
    - YAML: User-friendly configuration files
    - JSON: Machine-readable format
    - Python dict: Programmatic usage

    Example YAML format:
    ```yaml
    name: "SimpleProtocol"
    head_pattern: "FF FE"
    min_length: 0
    max_length: 1024
    checksum_type: "xor"
    timeout: 0.5
    fields:
      - name: "head"
        type: "head"
        length: 2
        offset: 0
        description: "Packet header"
      - name: "length"
        type: "length"
        length: 2
        offset: 2
      - name: "cmd"
        type: "cmd"
        length: 1
        offset: 4
      - name: "data"
        type: "data"
        length: 4
        offset: 5
      - name: "checksum"
        type: "checksum"
        length: 1
        offset: 9
    encryption:
      type: "none"
    validation:
      - rule: "cmd in [0x10, 0x15, 0x18]"
        field: "cmd"
    ```

    Example JSON format:
    ```json
    {
      "name": "SimpleProtocol",
      "head_pattern": "FF FE",
      "fields": [
        {
          "name": "head",
          "type": "head",
          "length": 2,
          "offset": 0
        }
      ]
    }
    ```
    """

    def __init__(self):
        self.protocols: Dict[str, ProtocolDefinition] = {}

    def load_from_yaml(self, yaml_content: str) -> ProtocolDefinition:
        """
        Load protocol definition from YAML string.

        Args:
            yaml_content: YAML configuration string.

        Returns:
            ProtocolDefinition object.

        Raises:
            ProtocolDSLParseError: If YAML parsing fails.
        """
        try:
            config = yaml.safe_load(yaml_content)
            if not isinstance(config, dict):
                raise ProtocolDSLParseError("YAML must be a dictionary")

            return self.parse_config(config)
        except yaml.YAMLError as e:
            raise ProtocolDSLParseError(f"Failed to parse YAML: {e}")

    def load_from_json(self, json_content: str) -> ProtocolDefinition:
        """
        Load protocol definition from JSON string.

        Args:
            json_content: JSON configuration string.

        Returns:
            ProtocolDefinition object.

        Raises:
            ProtocolDSLParseError: If JSON parsing fails.
        """
        try:
            config = json.loads(json_content)
            if not isinstance(config, dict):
                raise ProtocolDSLParseError("JSON must be a dictionary")

            return self.parse_config(config)
        except json.JSONDecodeError as e:
            raise ProtocolDSLParseError(f"Failed to parse JSON: {e}")

    def parse_config(self, config: Dict[str, Any]) -> ProtocolDefinition:
        """
        Parse protocol configuration from dictionary.

        Args:
            config: Protocol configuration dictionary.

        Returns:
            ProtocolDefinition object.

        Raises:
            ProtocolDSLParseError: If configuration is invalid.
        """
        # Validate required fields
        if "name" not in config:
            raise ProtocolDSLParseError("Protocol must have a 'name' field")

        if "fields" not in config:
            raise ProtocolDSLParseError("Protocol must have a 'fields' list")

        # Parse basic properties
        name = config["name"]
        fields_config = config["fields"]

        if not isinstance(fields_config, list):
            raise ProtocolDSLParseError("'fields' must be a list")

        # Parse fields
        fields = []
        for field_config in fields_config:
            try:
                field = self._parse_field_config(field_config)
                fields.append(field)
            except Exception as e:
                raise ProtocolDSLParseError(
                    f"Failed to parse field '{field_config.get('name', 'unknown')}': {e}"
                )

        # Parse optional properties
        head_pattern = None
        if "head_pattern" in config:
            head_pattern = self._parse_head_pattern(config["head_pattern"])

        min_length = int(config.get("min_length", 0))
        max_length = int(config.get("max_length", 1024))
        checksum_type = config.get("checksum_type", "none")
        parse_timeout = float(config.get("timeout", 0.5))

        # Parse encryption (optional)
        encryption = None
        if "encryption" in config:
            encryption_config = config["encryption"]
            encryption = self._parse_encryption(encryption_config)

        # Parse validation (optional)
        custom_validation = None
        if "validation" in config:
            validation_config = config["validation"]
            custom_validation = self._parse_validation(validation_config)

        # Validate protocol
        self._validate_protocol(fields, min_length, max_length)

        # Create protocol definition
        protocol = ProtocolDefinition(
            name=name,
            fields=fields,
            head_pattern=head_pattern,
            min_length=min_length,
            max_length=max_length,
            checksum_type=checksum_type,
            encryption=encryption,
            custom_validation=custom_validation,
            parse_timeout=parse_timeout,
        )

        return protocol

    def _parse_field_config(self, field_config: Dict[str, Any]) -> ProtocolField:
        """
        Parse field configuration.

        Args:
            field_config: Field configuration dictionary.

        Returns:
            ProtocolField object.

        Raises:
            ProtocolDSLParseError: If field configuration is invalid.
        """
        # Validate required fields
        if "name" not in field_config:
            raise ProtocolDSLParseError("Field must have a 'name'")

        if "type" not in field_config:
            raise ProtocolDSLParseError("Field must have a 'type'")

        if "length" not in field_config:
            raise ProtocolDSLParseError("Field must have a 'length'")

        if "offset" not in field_config:
            raise ProtocolDSLParseError("Field must have an 'offset'")

        # Parse field type
        field_type_str = field_config["type"]
        try:
            field_type = FieldType(field_type_str)
        except ValueError:
            raise ProtocolDSLParseError(
                f"Invalid field type '{field_type_str}'. "
                f"Must be one of: {', '.join([t.value for t in FieldType])}"
            )

        # Parse field properties
        name = field_config["name"]
        length = int(field_config["length"])
        offset = int(field_config["offset"])
        description = field_config.get("description", "")
        validation = field_config.get("validation")
        required = field_config.get("required", True)
        default_value = field_config.get("default_value")

        # Validate field
        if length < 0:
            raise ProtocolDSLParseError(f"Field '{name}': length must be >= 0")

        if offset < 0:
            raise ProtocolDSLParseError(f"Field '{name}': offset must be >= 0")

        # Create field
        return ProtocolField(
            name=name,
            field_type=field_type,
            length=length,
            offset=offset,
            description=description,
            validation=validation,
            required=required,
            default_value=default_value,
        )

    def _parse_head_pattern(self, pattern: str) -> bytes:
        """
        Parse head pattern string to bytes.

        Supports formats:
        - "FF FE" -> bytes([0xFF, 0xFE])
        - "AA55" -> bytes([0xAA, 0x55])
        - "FF" -> bytes([0xFF])

        Args:
            pattern: Head pattern string.

        Returns:
            Head pattern as bytes.
        """
        try:
            # Remove spaces and split
            hex_values = pattern.strip().split()
            # Convert hex strings to bytes
            bytes_list = [int(hex_str, 16) for hex_str in hex_values]
            return bytes(bytes_list)
        except ValueError as e:
            raise ProtocolDSLParseError(f"Invalid head pattern '{pattern}': {e}")

    def _parse_encryption(self, encryption_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse encryption configuration.

        Args:
            encryption_config: Encryption configuration dictionary.

        Returns:
            Encryption configuration dictionary.
        """
        encryption_type = encryption_config.get("type", "none")

        encryption = {"type": encryption_type}

        # Parse encryption-specific parameters
        if encryption_type == "aes":
            encryption["key"] = encryption_config.get("key", "")
            encryption["mode"] = encryption_config.get("mode", "ECB")
        elif encryption_type == "xor":
            encryption["key"] = encryption_config.get("key", "")
        elif encryption_type == "base64":
            pass  # No additional parameters

        return encryption

    def _parse_validation(self, validation_config: Any) -> List[Dict[str, Any]]:
        """
        Parse validation configuration.

        Args:
            validation_config: Validation configuration (can be list or dict).

        Returns:
            List of validation rules.
        """
        validations = []

        if isinstance(validation_config, list):
            for rule_config in validation_config:
                if isinstance(rule_config, dict) and "rule" in rule_config:
                    validations.append(rule_config)
        elif isinstance(validation_config, dict) and "rule" in validation_config:
            validations.append(validation_config)

        return validations

    def _validate_protocol(
        self, fields: List[ProtocolField], min_length: int, max_length: int
    ):
        """
        Validate protocol definition.

        Args:
            fields: List of protocol fields.
            min_length: Minimum packet length.
            max_length: Maximum packet length.

        Raises:
            ProtocolDSLParseError: If protocol is invalid.
        """
        # Check for duplicate field names
        field_names = [field.name for field in fields]
        duplicates = [name for name in field_names if field_names.count(name) > 1]

        if duplicates:
            raise ProtocolDSLParseError(
                f"Duplicate field names: {', '.join(duplicates)}"
            )

        # Validate field offsets don't overlap
        for i, field1 in enumerate(fields):
            for field2 in fields[i + 1 :]:
                if (
                    field1.field_type != FieldType.DATA
                    and field2.field_type != FieldType.DATA
                ):
                    # Both are fixed-length fields
                    end1 = field1.offset + field1.length
                    end2 = field2.offset + field2.length
                    if not (end1 <= field2.offset or end2 <= field1.offset):
                        raise ProtocolDSLParseError(
                            f"Fields '{field1.name}' and '{field2.name}' have overlapping offsets"
                        )

        # Validate length constraints
        if min_length < 0:
            raise ProtocolDSLParseError("min_length must be >= 0")

        if max_length <= 0:
            raise ProtocolDSLParseError("max_length must be > 0")

        if min_length > max_length:
            raise ProtocolDSLParseError("min_length cannot be greater than max_length")

    def save_to_yaml(self, protocol: ProtocolDefinition) -> str:
        """
        Save protocol definition to YAML string.

        Args:
            protocol: ProtocolDefinition object.

        Returns:
            YAML configuration string.
        """
        config = self._protocol_to_dict(protocol)
        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    def save_to_json(self, protocol: ProtocolDefinition) -> str:
        """
        Save protocol definition to JSON string.

        Args:
            protocol: ProtocolDefinition object.

        Returns:
            JSON configuration string.
        """
        config = self._protocol_to_dict(protocol)
        return json.dumps(config, indent=2)

    def _protocol_to_dict(self, protocol: ProtocolDefinition) -> Dict[str, Any]:
        """
        Convert protocol definition to dictionary.

        Args:
            protocol: ProtocolDefinition object.

        Returns:
            Protocol configuration dictionary.
        """
        config = {
            "name": protocol.name,
            "min_length": protocol.min_length,
            "max_length": protocol.max_length,
            "checksum_type": protocol.checksum_type,
            "timeout": protocol.parse_timeout,
            "fields": [],
        }

        # Add head pattern if present
        if protocol.head_pattern:
            hex_str = " ".join([f"{b:02X}" for b in protocol.head_pattern])
            config["head_pattern"] = hex_str

        # Add fields
        for field in protocol.fields:
            field_dict = {
                "name": field.name,
                "type": field.field_type.value,
                "length": field.length,
                "offset": field.offset,
            }

            if field.description:
                field_dict["description"] = field.description
            if field.validation:
                field_dict["validation"] = field.validation
            if not field.required:
                field_dict["required"] = False
            if field.default_value is not None:
                field_dict["default_value"] = str(field.default_value)

            config["fields"].append(field_dict)

        # Add encryption if present
        if protocol.encryption:
            config["encryption"] = protocol.encryption

        # Add validation if present
        if protocol.custom_validation:
            config["validation"] = protocol.custom_validation

        return config

    def load_protocol_from_file(self, file_path: str) -> ProtocolDefinition:
        """
        Load protocol definition from file.

        Supports .yaml, .yml, and .json files.

        Args:
            file_path: Path to protocol definition file.

        Returns:
            ProtocolDefinition object.

        Raises:
            ProtocolDSLParseError: If file parsing fails.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Determine file type and parse accordingly
            if file_path.endswith((".yaml", ".yml")):
                return self.load_from_yaml(content)
            elif file_path.endswith(".json"):
                return self.load_from_json(content)
            else:
                # Try YAML first, then JSON
                try:
                    return self.load_from_yaml(content)
                except ProtocolDSLParseError:
                    return self.load_from_json(content)
        except FileNotFoundError:
            raise ProtocolDSLParseError(f"Protocol file not found: {file_path}")
        except Exception as e:
            raise ProtocolDSLParseError(f"Failed to load protocol file: {e}")

    def save_protocol_to_file(
        self, protocol: ProtocolDefinition, file_path: str, format: str = "yaml"
    ):
        """
        Save protocol definition to file.

        Args:
            protocol: ProtocolDefinition object.
            file_path: Path to save file.
            format: Output format ('yaml' or 'json').

        Raises:
            ProtocolDSLParseError: If file saving fails.
        """
        try:
            if format == "yaml":
                content = self.save_to_yaml(protocol)
            elif format == "json":
                content = self.save_to_json(protocol)
            else:
                raise ProtocolDSLParseError(f"Unsupported format: {format}")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Protocol saved to {file_path}")
        except Exception as e:
            raise ProtocolDSLParseError(f"Failed to save protocol file: {e}")
