"""
ProcureAI — Encryption utility for sensitive configuration values.

Uses Fernet symmetric encryption for SMTP passwords and other secrets stored in the database.
The encryption key is derived from a machine-local secret or environment variable.
"""

import os
import base64
import hashlib
import structlog
from typing import Optional

logger = structlog.get_logger()

# The encryption key can be provided via environment variable.
# If not set, a deterministic key is derived from the machine's hostname + a salt.
# In production, ALWAYS set PROCUREAI_ENCRYPTION_KEY to a strong random value.
_ENCRYPTION_KEY_ENV = "PROCUREAI_ENCRYPTION_KEY"
_FERNET_INSTANCE = None


def _get_fernet():
    """Returns a Fernet instance for encrypting/decrypting secrets."""
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE is not None:
        return _FERNET_INSTANCE

    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.warning(
            "cryptography package not installed. SMTP passwords will be stored in plaintext. "
            "Run: pip install cryptography"
        )
        return None

    key_material = os.getenv(_ENCRYPTION_KEY_ENV)
    if key_material:
        # Use provided key directly (must be 32 url-safe base64 bytes for Fernet)
        if len(key_material) < 32:
            # Derive a proper Fernet key from the provided material
            key_bytes = hashlib.sha256(key_material.encode()).digest()
            key = base64.urlsafe_b64encode(key_bytes)
        else:
            key = key_material.encode() if isinstance(key_material, str) else key_material
    else:
        # Fallback: derive from hostname + static salt (not ideal for production)
        import platform
        raw = f"procureai-{platform.node()}-smtp-key-v1"
        key_bytes = hashlib.sha256(raw.encode()).digest()
        key = base64.urlsafe_b64encode(key_bytes)
        logger.warning(
            "No PROCUREAI_ENCRYPTION_KEY set. Using machine-derived key. "
            "Set PROCUREAI_ENCRYPTION_KEY in .env for production use."
        )

    _FERNET_INSTANCE = Fernet(key)
    return _FERNET_INSTANCE


def encrypt_value(plaintext: Optional[str]) -> Optional[str]:
    """Encrypts a plaintext string. Returns base64-encoded ciphertext, or None if input is None/empty."""
    if not plaintext:
        return plaintext

    fernet = _get_fernet()
    if fernet is None:
        # Fallback: return plaintext if cryptography is not available
        return plaintext

    try:
        encrypted = fernet.encrypt(plaintext.encode("utf-8"))
        return f"enc:{encrypted.decode('utf-8')}"
    except Exception as e:
        logger.error("Failed to encrypt value", error=str(e))
        return plaintext


def decrypt_value(stored: Optional[str]) -> Optional[str]:
    """Decrypts a stored value. Handles both encrypted (enc: prefix) and legacy plaintext values."""
    if not stored:
        return stored

    # If not encrypted (legacy plaintext), return as-is
    if not stored.startswith("enc:"):
        return stored

    fernet = _get_fernet()
    if fernet is None:
        logger.warning("Cannot decrypt value — cryptography package not installed. Returning raw value.")
        return stored

    try:
        cipher_text = stored[4:]  # Strip "enc:" prefix
        decrypted = fernet.decrypt(cipher_text.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception as e:
        logger.error("Failed to decrypt value. It may have been encrypted with a different key.", error=str(e))
        return None
