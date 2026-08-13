from datetime import datetime, timedelta, timezone
from enum import StrEnum
from hashlib import sha256
from uuid import UUID, uuid4

import jwt
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.auth import TokenPayload


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenValidationError(Exception):
    """Raised when a JWT is invalid, expired, or has the wrong token type."""


def _create_token(
    *,
    user_id: UUID,
    organization_id: UUID,
    token_type: TokenType,
    lifetime: timedelta,
    settings: Settings,
    jti: UUID | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "organization_id": str(organization_id),
        "type": token_type.value,
        "iat": now,
        "nbf": now,
        "exp": now + lifetime,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": str(jti or uuid4()),
    }
    jwt_client = jwt.PyJWT(options={"enforce_minimum_key_length": True})
    return jwt_client.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: UUID, organization_id: UUID, settings: Settings) -> str:
    return _create_token(
        user_id=user_id,
        organization_id=organization_id,
        token_type=TokenType.ACCESS,
        lifetime=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        settings=settings,
    )


def create_refresh_token(
    user_id: UUID,
    organization_id: UUID,
    settings: Settings,
    *,
    jti: UUID | None = None,
) -> str:
    return _create_token(
        user_id=user_id,
        organization_id=organization_id,
        token_type=TokenType.REFRESH,
        lifetime=timedelta(days=settings.jwt_refresh_token_expire_days),
        settings=settings,
        jti=jti,
    )


def hash_token_jti(jti: UUID) -> str:
    """Return a fixed-length, non-reversible storage identifier for a token JTI."""
    return sha256(jti.bytes).hexdigest()


def decode_token(
    token: str,
    expected_type: TokenType,
    settings: Settings,
) -> TokenPayload:
    jwt_client = jwt.PyJWT(options={"enforce_minimum_key_length": True})
    try:
        payload = jwt_client.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "require": [
                    "sub",
                    "organization_id",
                    "type",
                    "exp",
                    "iat",
                    "nbf",
                    "iss",
                    "aud",
                    "jti",
                ],
                "enforce_minimum_key_length": True,
            },
        )
        token_payload = TokenPayload.model_validate(payload)
    except (jwt.InvalidTokenError, ValidationError, ValueError, TypeError) as exc:
        raise TokenValidationError from exc

    if token_payload.type != expected_type.value:
        raise TokenValidationError
    return token_payload
