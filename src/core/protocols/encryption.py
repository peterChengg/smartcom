"""
Protocol encryption and decryption interfaces.

This module provides encryption/decryption support for custom protocols.
Supports multiple encryption algorithms including AES, XOR, and Base64.
"""

import base64
import hashlib
import logging
from typing import Any, Dict, Optional

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Encryption/decryption error."""

    pass


class EncryptionInterface:
    """Base interface for encryption/decryption."""

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data.

        Args:
            data: Data to encrypt.

        Returns:
            Encrypted data.

        Raises:
            EncryptionError: If encryption fails.
        """
        raise NotImplementedError

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data.

        Args:
            data: Data to decrypt.

        Returns:
            Decrypted data.

        Raises:
            EncryptionError: If decryption fails.
        """
        raise NotImplementedError


class NoEncryption(EncryptionInterface):
    """No encryption (pass-through)."""

    def encrypt(self, data: bytes) -> bytes:
        """No encryption, return data as-is."""
        return data

    def decrypt(self, data: bytes) -> bytes:
        """No decryption, return data as-is."""
        return data


class XOREncryption(EncryptionInterface):
    """XOR encryption with a key."""

    def __init__(self, key: bytes):
        """
        Initialize XOR encryption.

        Args:
            key: XOR key (any length).
        """
        if not key:
            raise EncryptionError("XOR key cannot be empty")

        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data using XOR.

        Args:
            data: Data to encrypt.

        Returns:
            Encrypted data.
        """
        encrypted = bytearray(len(data))
        for i, byte in enumerate(data):
            encrypted[i] = byte ^ self.key[i % len(self.key)]

        return bytes(encrypted)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data using XOR.

        Args:
            data: Data to decrypt.

        Returns:
            Decrypted data.
        """
        decrypted = bytearray(len(data))
        for i, byte in enumerate(data):
            decrypted[i] = byte ^ self.key[i % len(self.key)]

        return bytes(decrypted)


class AESEncryption(EncryptionInterface):
    """AES encryption with configurable mode."""

    def __init__(self, key: bytes, mode: str = "ECB"):
        """
        Initialize AES encryption.

        Args:
            key: AES key (16, 24, or 32 bytes for AES-128/192/256).
            mode: AES mode ('ECB', 'CBC', etc.).
        """
        if not HAS_CRYPTO:
            raise EncryptionError(
                "AES encryption requires pycryptodome. Install with: pip install pycryptodome"
            )

        if len(key) not in [16, 24, 32]:
            raise EncryptionError(
                f"AES key must be 16, 24, or 32 bytes, got {len(key)}"
            )

        self.key = key
        self.mode = mode.upper()

    def _get_cipher(self) -> Any:  # type: ignore[no-any-return]
        """Get AES cipher instance."""
        return AES.new(self.key, mode=self.mode)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data using AES.

        Args:
            data: Data to encrypt.

        Returns:
            Encrypted data (padded to block size).
        """
        try:
            cipher = self._get_cipher()
            padded_data = pad(data, AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            return encrypted
        except Exception as e:
            raise EncryptionError(f"AES encryption failed: {e}")

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data using AES.

        Args:
            data: Data to decrypt.

        Returns:
            Decrypted data (padding removed).
        """
        try:
            cipher = self._get_cipher()
            decrypted = cipher.decrypt(data)
            unpadded = unpad(decrypted, AES.block_size)
            return unpadded
        except Exception as e:
            raise EncryptionError(f"AES decryption failed: {e}")


class Base64Encoding(EncryptionInterface):
    """Base64 encoding (not encryption, but common for protocol encoding)."""

    def encrypt(self, data: bytes) -> bytes:
        """
        Encode data using Base64.

        Args:
            data: Data to encode.

        Returns:
            Base64 encoded data.
        """
        return base64.b64encode(data)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decode Base64 data.

        Args:
            data: Data to decode.

        Returns:
            Decoded data.
        """
        try:
            return base64.b64decode(data)
        except Exception as e:
            raise EncryptionError(f"Base64 decoding failed: {e}")


class EncryptionFactory:
    """
    Factory for creating encryption instances.

    Supports creating encryption instances from configuration dictionaries.
    """

    @staticmethod
    def create(encryption_config: Dict[str, Any]) -> EncryptionInterface:
        """
        Create encryption instance from configuration.

        Args:
            encryption_config: Encryption configuration dictionary.
                Example:
                {
                    "type": "xor",
                    "key": "0x55"
                }
                or
                {
                    "type": "aes",
                    "key": "my-secret-key-123456",
                    "mode": "ECB"
                }

        Returns:
            EncryptionInterface instance.

        Raises:
            EncryptionError: If encryption type is invalid or configuration is missing.
        """
        encryption_type = encryption_config.get("type", "none")

        if encryption_type == "none":
            return NoEncryption()

        elif encryption_type == "xor":
            key = encryption_config.get("key", "")
            if not key:
                raise EncryptionError("XOR encryption requires a 'key' parameter")

            # Parse key (hex string or bytes)
            key_bytes = EncryptionFactory._parse_key(key)
            return XOREncryption(key_bytes)

        elif encryption_type == "aes":
            key = encryption_config.get("key", "")
            if not key:
                raise EncryptionError("AES encryption requires a 'key' parameter")

            mode = encryption_config.get("mode", "ECB")

            # Parse key (hex string or bytes)
            key_bytes = EncryptionFactory._parse_key(key)

            # Ensure key is correct length for AES
            if len(key_bytes) not in [16, 24, 32]:
                # Pad or truncate key to 16 bytes (AES-128)
                if len(key_bytes) < 16:
                    key_bytes = key_bytes.ljust(16, b"\x00")
                else:
                    key_bytes = key_bytes[:16]

            return AESEncryption(key_bytes, mode)

        elif encryption_type == "base64":
            return Base64Encoding()

        else:
            raise EncryptionError(
                f"Unsupported encryption type: {encryption_type}. "
                f"Supported types: none, xor, aes, base64"
            )

    @staticmethod
    def _parse_key(key: Any) -> bytes:
        """
        Parse key from various formats.

        Supports:
        - Hex string: "FF FE" or "0xFF 0xFE"
        - String: "my-key"
        - Bytes: already bytes

        Args:
            key: Key in any supported format.

        Returns:
            Key as bytes.
        """
        if isinstance(key, bytes):
            return key

        if isinstance(key, str):
            # Check if it's a hex string
            if key.startswith("0x") or all(c in "0123456789ABCDEFabcdef " for c in key):
                try:
                    # Parse hex string (space or no separator)
                    hex_values = key.replace("0x", "").split()
                    return bytes([int(h, 16) for h in hex_values])
                except ValueError:
                    pass

            # Regular string, encode to bytes
            return key.encode("utf-8")

        raise EncryptionError(f"Cannot parse key: {key}")

    @staticmethod
    def create_from_protocol(
        encryption_config: Optional[Dict[str, Any]],
    ) -> EncryptionInterface:
        """
        Create encryption instance from protocol configuration.

        Args:
            encryption_config: Protocol encryption configuration (can be None).

        Returns:
            EncryptionInterface instance (NoEncryption if config is None).
        """
        if not encryption_config:
            return NoEncryption()

        return EncryptionFactory.create(encryption_config)


def test_encryption():
    """Test encryption functionality."""
    test_data = b"Hello, World!"

    # Test No Encryption
    no_enc = NoEncryption()
    encrypted = no_enc.encrypt(test_data)
    decrypted = no_enc.decrypt(encrypted)
    assert encrypted == test_data
    assert decrypted == test_data
    print("✅ NoEncryption test passed")

    # Test XOR Encryption
    xor_enc = XOREncryption(b"\x55\xaa")
    encrypted = xor_enc.encrypt(test_data)
    decrypted = xor_enc.decrypt(encrypted)
    assert decrypted == test_data
    print("✅ XOREncryption test passed")

    # Test Base64 Encoding
    base64_enc = Base64Encoding()
    encrypted = base64_enc.encrypt(test_data)
    decrypted = base64_enc.decrypt(encrypted)
    assert decrypted == test_data
    print("✅ Base64Encoding test passed")

    # Test AES Encryption
    try:
        aes_enc = AESEncryption(b"my-secret-key-123", mode="ECB")
        encrypted = aes_enc.encrypt(test_data)
        decrypted = aes_enc.decrypt(encrypted)
        assert decrypted == test_data
        print("✅ AESEncryption test passed")
    except ImportError:
        print("⚠️ pycryptodome not available, skipping AES test")

    # Test Factory
    xor_config = {"type": "xor", "key": "FF FE"}
    enc = EncryptionFactory.create(xor_config)
    assert isinstance(enc, XOREncryption)
    print("✅ Factory test passed")

    print("\n🎉 All encryption tests passed!")


if __name__ == "__main__":
    test_encryption()
