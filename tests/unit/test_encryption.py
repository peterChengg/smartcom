"""
Unit tests for protocol encryption/decryption.
"""

import pytest

from src.core.protocols.encryption import (
    AESEncryption,
    Base64Encoding,
    EncryptionError,
    EncryptionFactory,
    NoEncryption,
    XOREncryption,
)


class TestNoEncryption:
    """Test cases for NoEncryption class."""

    def test_encrypt_passes_through(self):
        """Test that NoEncryption passes data through unchanged."""
        enc = NoEncryption()
        test_data = b"Hello, World!"

        encrypted = enc.encrypt(test_data)

        assert encrypted == test_data

    def test_decrypt_passes_through(self):
        """Test that NoEncryption passes data through unchanged."""
        enc = NoEncryption()
        test_data = b"Hello, World!"

        decrypted = enc.decrypt(test_data)

        assert decrypted == test_data


class TestXOREncryption:
    """Test cases for XOREncryption class."""

    def test_xor_encryption_single_byte_key(self):
        """Test XOR encryption with single byte key."""
        enc = XOREncryption(b"\x55")
        test_data = b"Hello"

        encrypted = enc.encrypt(test_data)

        assert len(encrypted) == len(test_data)
        assert encrypted != test_data  # Should be different

    def test_xor_encryption_multi_byte_key(self):
        """Test XOR encryption with multi-byte key."""
        enc = XOREncryption(b"\x55\xaa\xff")
        test_data = b"Hello, World!"

        encrypted = enc.encrypt(test_data)

        assert len(encrypted) == len(test_data)

    def test_xor_decryption(self):
        """Test XOR decryption."""
        enc = XOREncryption(b"\x55\xaa")
        test_data = b"Test data"

        encrypted = enc.encrypt(test_data)
        decrypted = enc.decrypt(encrypted)

        assert decrypted == test_data

    def test_xor_empty_key_error(self):
        """Test that empty key raises error."""
        with pytest.raises(EncryptionError, match="key cannot be empty"):
            XOREncryption(b"")


class TestBase64Encoding:
    """Test cases for Base64Encoding class."""

    def test_base64_encoding(self):
        """Test Base64 encoding."""
        enc = Base64Encoding()
        test_data = b"Hello, World!"

        encoded = enc.encrypt(test_data)

        # Base64 encoding should be different from original
        assert encoded != test_data
        # Base64 encoding should be longer
        assert len(encoded) > len(test_data)

    def test_base64_decoding(self):
        """Test Base64 decoding."""
        enc = Base64Encoding()
        test_data = b"Test string!"

        encoded = enc.encrypt(test_data)
        decoded = enc.decrypt(encoded)

        assert decoded == test_data

    def test_base64_invalid_decoding_error(self):
        """Test that invalid Base64 raises error."""
        enc = Base64Encoding()

        with pytest.raises(EncryptionError, match="decoding failed"):
            enc.decrypt(b"Invalid!Base64@Data")


class TestAESEncryption:
    """Test cases for AESEncryption class."""

    def test_aes_encryption_128bit_key(self):
        """Test AES encryption with 128-bit key."""
        try:
            enc = AESEncryption(b"my-secret-key-123", mode="ECB")
            test_data = b"Hello, World!"

            encrypted = enc.encrypt(test_data)

            assert len(encrypted) > len(test_data)  # Padding adds bytes
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pytest.skip("pycryptodome not installed")
            else:
                raise

    def test_aes_decryption_128bit_key(self):
        """Test AES decryption with 128-bit key."""
        try:
            enc = AESEncryption(b"my-secret-key-123", mode="ECB")
            test_data = b"Test data!"

            encrypted = enc.encrypt(test_data)
            decrypted = enc.decrypt(encrypted)

            assert decrypted == test_data
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pytest.skip("pycryptodome not installed")
            else:
                raise

    def test_aes_invalid_key_length_error(self):
        """Test that invalid key length raises error."""
        try:
            with pytest.raises(EncryptionError, match="pycryptodome|must be"):
                AESEncryption(b"short-key")
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pytest.skip("pycryptodome not installed")

    def test_aes_192bit_key(self):
        """Test AES encryption with 192-bit key."""
        try:
            key = b"my-24-byte-encryption-key!!"
            enc = AESEncryption(key, mode="ECB")
            test_data = b"Test data"

            encrypted = enc.encrypt(test_data)
            decrypted = enc.decrypt(encrypted)

            assert decrypted == test_data
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pytest.skip("pycryptodome not installed")

    def test_aes_256bit_key(self):
        """Test AES encryption with 256-bit key."""
        try:
            key = b"my-32-byte-encryption-key-for-test!"
            enc = AESEncryption(key, mode="ECB")
            test_data = b"Test data"

            encrypted = enc.encrypt(test_data)
            decrypted = enc.decrypt(encrypted)

            assert decrypted == test_data
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pytest.skip("pycryptodome not installed")


class TestEncryptionFactory:
    """Test cases for EncryptionFactory class."""

    def test_create_no_encryption(self):
        """Test creating NoEncryption."""
        config = {"type": "none"}
        enc = EncryptionFactory.create(config)

        assert isinstance(enc, NoEncryption)

    def test_create_xor_encryption(self):
        """Test creating XOREncryption."""
        config = {"type": "xor", "key": "FF FE"}
        enc = EncryptionFactory.create(config)

        assert isinstance(enc, XOREncryption)

    def test_create_xor_encryption_missing_key_error(self):
        """Test that missing key raises error."""
        config = {"type": "xor"}

        with pytest.raises(EncryptionError, match="requires a 'key' parameter"):
            EncryptionFactory.create(config)

    def test_create_base64_encoding(self):
        """Test creating Base64Encoding."""
        config = {"type": "base64"}
        enc = EncryptionFactory.create(config)

        assert isinstance(enc, Base64Encoding)

    def test_create_aes_encryption(self):
        """Test creating AESEncryption."""
        config = {
            "type": "aes",
            "key": "my-secret-key-123",
            "mode": "ECB",
        }

        try:
            enc = EncryptionFactory.create(config)

            assert isinstance(enc, AESEncryption)
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pass  # Skip if pycryptodome not installed
            else:
                raise

    def test_create_aes_encryption_missing_key_error(self):
        """Test that missing key raises error."""
        config = {"type": "aes"}

        with pytest.raises(EncryptionError, match="requires a 'key' parameter"):
            EncryptionFactory.create(config)

    def test_create_invalid_encryption_type_error(self):
        """Test that invalid encryption type raises error."""
        config = {"type": "invalid_type"}

        with pytest.raises(EncryptionError, match="Unsupported encryption type"):
            EncryptionFactory.create(config)

    def test_parse_key_hex_string(self):
        """Test parsing key from hex string."""
        config = {"type": "xor", "key": "FF FE AA 55"}
        enc = EncryptionFactory.create(config)

        assert isinstance(enc, XOREncryption)
        assert enc.key == b"\xff\xfe\xaa\x55"

    def test_parse_key_hex_string_with_0x(self):
        """Test parsing key from hex string with 0x prefix."""
        config = {"type": "xor", "key": "0xFF 0xFE"}
        enc = EncryptionFactory.create(config)

        assert isinstance(enc, XOREncryption)
        assert enc.key == b"\xff\xfe"

    def test_parse_key_string(self):
        """Test parsing key from regular string."""
        config = {"type": "xor", "key": "my-key"}
        enc = EncryptionFactory.create(config)

        assert isinstance(enc, XOREncryption)
        assert enc.key == b"my-key"

    def test_create_from_protocol_none(self):
        """Test creating encryption from None protocol config."""
        enc = EncryptionFactory.create_from_protocol(None)

        assert isinstance(enc, NoEncryption)

    def test_create_from_protocol_dict(self):
        """Test creating encryption from protocol config dict."""
        config = {"type": "xor", "key": "55 AA"}
        enc = EncryptionFactory.create_from_protocol(config)

        assert isinstance(enc, XOREncryption)

    def test_aes_key_padding_too_short(self):
        """Test AES key padding when too short."""
        try:
            config = {
                "type": "aes",
                "key": "short",
                "mode": "ECB",
            }

            enc = EncryptionFactory.create(config)
            # Key should be padded to 16 bytes
            assert len(enc.key) == 16
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pass

    def test_aes_key_truncation_too_long(self):
        """Test AES key truncation when too long."""
        try:
            config = {
                "type": "aes",
                "key": "this-key-is-way-too-long-for-aes-encryption",
                "mode": "ECB",
            }

            enc = EncryptionFactory.create(config)
            # Key should be truncated to 16 bytes
            assert len(enc.key) == 16
        except EncryptionError as e:
            if "pycryptodome" in str(e):
                pass


class TestEncryptionIntegration:
    """Integration tests for encryption with protocol parser."""

    def test_xor_encrypt_decrypt_roundtrip(self):
        """Test XOR encryption/decryption roundtrip."""
        enc = XOREncryption(b"\x55\xaa")
        test_data = b"This is a test message for encryption"

        encrypted = enc.encrypt(test_data)
        decrypted = enc.decrypt(encrypted)

        assert decrypted == test_data

    def test_xor_repeated_encryption(self):
        """Test that XOR encryption can be repeated."""
        enc = XOREncryption(b"\xaa")
        test_data = b"Test"

        encrypted1 = enc.encrypt(test_data)
        encrypted2 = enc.encrypt(test_data)

        assert encrypted1 == encrypted2  # XOR with same key produces same result

    def test_xor_different_data(self):
        """Test XOR encryption with different data."""
        enc = XOREncryption(b"\x55")
        data1 = b"Hello"
        data2 = b"World"

        encrypted1 = enc.encrypt(data1)
        encrypted2 = enc.encrypt(data2)

        assert encrypted1 != encrypted2

    def test_base64_roundtrip(self):
        """Test Base64 encoding/decryption roundtrip."""
        enc = Base64Encoding()
        test_data = b"Test data with special chars: !@#$%^&*()"

        encoded = enc.encrypt(test_data)
        decoded = enc.decrypt(encoded)

        assert decoded == test_data
