from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from sentinel.config import settings

_ENC_PREFIX = "enc:"


def _load_key() -> bytes:
    raw = settings.encryption_key
    if not raw:
        raise ValueError("SENTINEL_ENCRYPTION_KEY is required for key encryption")
    try:
        key = base64.urlsafe_b64decode(raw.encode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("SENTINEL_ENCRYPTION_KEY must be base64-url encoded") from exc
    if len(key) != 32:
        raise ValueError("SENTINEL_ENCRYPTION_KEY must decode to 32 bytes (AES-256)")
    return key


def encrypt_text(value: str) -> str:
    if value is None:
        raise ValueError("Cannot encrypt empty value")
<<<<<<< HEAD
    # Local/dev workflows still need partner-key management even before
    # operators provision AES material. Fall back to plaintext only outside prod.
    if not settings.encryption_key and settings.app_env.lower() != "prod":
        return value
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    key = _load_key()
    nonce = os.urandom(12)
    aes = AESGCM(key)
    ciphertext = aes.encrypt(nonce, value.encode("utf-8"), None)
    token = base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")
    return f"{_ENC_PREFIX}{token}"


def decrypt_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not value.startswith(_ENC_PREFIX):
        return value
    key = _load_key()
    token = value[len(_ENC_PREFIX) :]
    data = base64.urlsafe_b64decode(token.encode("utf-8"))
    nonce, ciphertext = data[:12], data[12:]
    aes = AESGCM(key)
    plaintext = aes.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
