"""
Unit tests for protocol DSL parser.
"""

import pytest

from src.core.protocols.dsl_parser import ProtocolDSLParseError, ProtocolDSLParser
from src.core.protocol_parser import (
    FieldType,
    ProtocolDefinition,
    ProtocolField,
)


@pytest.fixture
def yaml_protocol_config():
    """YAML protocol configuration."""
    return """
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
"""


@pytest.fixture
def json_protocol_config():
    """JSON protocol configuration."""
    return """{
  "name": "JSONProtocol",
  "head_pattern": "AA 55",
  "fields": [
    {
      "name": "head",
      "type": "head",
      "length": 2,
      "offset": 0
    },
    {
      "name": "length",
      "type": "length",
      "length": 2,
      "offset": 2
    }
  ]
}"""


@pytest.fixture
def parser():
    """Create DSL parser instance."""
    return ProtocolDSLParser()


class TestProtocolDSLParser:
    """Test cases for ProtocolDSLParser."""

    def test_parser_initialization(self, parser):
        """Test parser initialization."""
        assert parser.protocols == {}

    def test_load_from_yaml(self, parser, yaml_protocol_config):
        """Test loading protocol from YAML."""
        protocol = parser.load_from_yaml(yaml_protocol_config)

        assert protocol is not None
        assert protocol.name == "SimpleProtocol"
        assert len(protocol.fields) == 5
        assert protocol.checksum_type == "xor"
        assert protocol.head_pattern == bytes([0xFF, 0xFE])

    def test_load_from_json(self, parser, json_protocol_config):
        """Test loading protocol from JSON."""
        protocol = parser.load_from_json(json_protocol_config)

        assert protocol is not None
        assert protocol.name == "JSONProtocol"
        assert len(protocol.fields) == 2
        assert protocol.head_pattern == bytes([0xAA, 0x55])

    def test_parse_config_dict(self, parser):
        """Test parsing configuration from dictionary."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 2,
                    "offset": 0,
                }
            ],
        }

        protocol = parser.parse_config(config)

        assert protocol is not None
        assert protocol.name == "TestProtocol"
        assert len(protocol.fields) == 1
        assert protocol.fields[0].name == "head"
        assert protocol.fields[0].field_type == FieldType.HEAD

    def test_missing_name_error(self, parser):
        """Test error when protocol name is missing."""
        config = {"fields": []}

        with pytest.raises(ProtocolDSLParseError, match="must have a 'name' field"):
            parser.parse_config(config)

    def test_missing_fields_error(self, parser):
        """Test error when fields list is missing."""
        config = {"name": "TestProtocol"}

        with pytest.raises(ProtocolDSLParseError, match="must have a 'fields' list"):
            parser.parse_config(config)

    def test_invalid_field_type_error(self, parser):
        """Test error when field type is invalid."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "invalid_type",
                    "length": 2,
                    "offset": 0,
                }
            ],
        }

        with pytest.raises(ProtocolDSLParseError, match="Invalid field type"):
            parser.parse_config(config)

    def test_missing_field_properties_error(self, parser):
        """Test error when field properties are missing."""
        config = {
            "name": "TestProtocol",
            "fields": [{"name": "head"}],
        }

        with pytest.raises(ProtocolDSLParseError, match="must have"):
            parser.parse_config(config)

    def test_negative_length_error(self, parser):
        """Test error when field length is negative."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": -1,
                    "offset": 0,
                }
            ],
        }

        with pytest.raises(ProtocolDSLParseError, match="must be >= 0"):
            parser.parse_config(config)

    def test_negative_offset_error(self, parser):
        """Test error when field offset is negative."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 2,
                    "offset": -1,
                }
            ],
        }

        with pytest.raises(ProtocolDSLParseError, match="must be >= 0"):
            parser.parse_config(config)

    def test_duplicate_field_names_error(self, parser):
        """Test error when field names are duplicated."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 2,
                    "offset": 0,
                },
                {
                    "name": "head",
                    "type": "length",
                    "length": 2,
                    "offset": 2,
                },
            ],
        }

        with pytest.raises(ProtocolDSLParseError, match="Duplicate field names"):
            parser.parse_config(config)

    def test_overlapping_fields_error(self, parser):
        """Test error when fields have overlapping offsets."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 4,
                    "offset": 0,
                },
                {
                    "name": "length",
                    "type": "length",
                    "length": 2,
                    "offset": 2,
                },
            ],
        }

        with pytest.raises(ProtocolDSLParseError, match="overlapping"):
            parser.parse_config(config)

    def test_save_to_yaml(self, parser):
        """Test saving protocol to YAML."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 2,
                    "offset": 0,
                }
            ],
        }

        protocol = parser.parse_config(config)
        yaml_output = parser.save_to_yaml(protocol)

        assert "name: TestProtocol" in yaml_output
        assert "fields:" in yaml_output

    def test_save_to_json(self, parser):
        """Test saving protocol to JSON."""
        config = {
            "name": "TestProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 2,
                    "offset": 0,
                }
            ],
        }

        protocol = parser.parse_config(config)
        json_output = parser.save_to_json(protocol)

        assert '"name": "TestProtocol"' in json_output
        assert '"fields"' in json_output

    def test_optional_field_parsing(self, parser):
        """Test parsing optional fields."""
        config = {
            "name": "OptionalFieldProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 2,
                    "offset": 0,
                },
                {
                    "name": "optional_data",
                    "type": "data",
                    "length": 4,
                    "offset": 2,
                    "required": False,
                    "default_value": "0x00 0x00 0x00 0x00",
                },
            ],
        }

        protocol = parser.parse_config(config)

        assert protocol is not None
        assert len(protocol.fields) == 2
        assert protocol.fields[1].required is False

    def test_field_validation_parsing(self, parser):
        """Test parsing field validation rules."""
        config = {
            "name": "ValidatedProtocol",
            "fields": [
                {
                    "name": "cmd",
                    "type": "cmd",
                    "length": 1,
                    "offset": 0,
                    "validation": "cmd in [0x10, 0x15, 0x18]",
                }
            ],
            "validation": [
                {
                    "rule": "cmd in [0x10, 0x15, 0x18]",
                    "field": "cmd",
                }
            ],
        }

        protocol = parser.parse_config(config)

        assert protocol is not None
        assert protocol.fields[0].validation == "cmd in [0x10, 0x15, 0x18]"
        assert protocol.custom_validation is not None
        assert len(protocol.custom_validation) == 1

    def test_encryption_parsing(self, parser):
        """Test parsing encryption configuration."""
        config = {
            "name": "EncryptedProtocol",
            "fields": [
                {
                    "name": "head",
                    "type": "head",
                    "length": 2,
                    "offset": 0,
                }
            ],
            "encryption": {"type": "xor", "key": "FF"},
        }

        protocol = parser.parse_config(config)

        assert protocol is not None
        assert protocol.encryption is not None
        assert protocol.encryption["type"] == "xor"
        assert protocol.encryption["key"] == "FF"

    def test_min_max_length_validation(self, parser):
        """Test min/max length validation."""
        config = {
            "name": "TestProtocol",
            "min_length": -1,
            "max_length": 1024,
            "fields": [{"name": "head", "type": "head", "length": 2, "offset": 0}],
        }

        with pytest.raises(ProtocolDSLParseError, match="must be >= 0"):
            parser.parse_config(config)

        config["min_length"] = 0
        config["max_length"] = 0

        with pytest.raises(ProtocolDSLParseError, match="must be > 0"):
            parser.parse_config(config)

        config["min_length"] = 100
        config["max_length"] = 50

        with pytest.raises(ProtocolDSLParseError, match="cannot be greater"):
            parser.parse_config(config)

    def test_parse_head_pattern(self, parser):
        """Test head pattern parsing."""
        config = {
            "name": "TestProtocol",
            "head_pattern": "FF FE",
            "fields": [{"name": "head", "type": "head", "length": 2, "offset": 0}],
        }

        protocol = parser.parse_config(config)

        assert protocol.head_pattern == bytes([0xFF, 0xFE])

        # Test single byte pattern
        config["head_pattern"] = "FF"
        protocol = parser.parse_config(config)

        assert protocol.head_pattern == bytes([0xFF])
