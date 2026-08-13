"""Small encrypted-at-rest secret storage helper.

Uses a Fernet key derived from the application's high-entropy JWT secret. This keeps
recoverable integration secrets encrypted in the database while avoiding a second
local key file for the self-hosted edition.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _fernet(master_secret: str) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(master_secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(secret: str, master_secret: str) -> str:
    return _fernet(master_secret).encrypt(secret.encode("utf-8")).decode("ascii")


def decrypt_secret(encrypted: str, master_secret: str) -> str:
    try:
        return _fernet(master_secret).decrypt(encrypted.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt stored secret") from exc
