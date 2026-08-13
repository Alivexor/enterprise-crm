"""Dependency-light TOTP helpers for optional two-factor authentication.

The TOTP algorithm follows RFC 6238 (HMAC-SHA1, 30-second time step, 6 digits).
Secrets are encrypted at rest with a Fernet key derived from the application's JWT
secret. Recovery codes are only stored as keyed HMAC digests.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from app.security.secret_storage import decrypt_secret, encrypt_secret


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    padding = "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode((secret + padding).upper(), casefold=True)


def generate_code(secret: str, *, at_time: int | None = None, digits: int = 6, period: int = 30) -> str:
    counter = int((at_time if at_time is not None else time.time()) // period)
    digest = hmac.new(_decode_secret(secret), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(value).zfill(digits)


def verify_code(secret: str, code: str, *, window: int = 1) -> bool:
    normalized = "".join(ch for ch in str(code).strip() if ch.isdigit())
    if len(normalized) != 6:
        return False
    now = int(time.time())
    for step in range(-window, window + 1):
        if hmac.compare_digest(generate_code(secret, at_time=now + step * 30), normalized):
            return True
    return False


def generate_recovery_codes(count: int = 10) -> list[str]:
    return [f"{secrets.token_hex(4)}-{secrets.token_hex(4)}" for _ in range(count)]


def hash_recovery_code(code: str, jwt_secret: str) -> str:
    return hmac.new(jwt_secret.encode("utf-8"), code.strip().lower().encode("utf-8"), hashlib.sha256).hexdigest()


def build_otpauth_uri(secret: str, *, issuer: str, account_name: str) -> str:
    label = quote(f"{issuer}:{account_name}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"
