from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.schemas.common import RequestSchema

PersonName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class RegisterRequest(RequestSchema):
    email: EmailStr
    password: str = Field(min_length=12, max_length=1024)
    first_name: PersonName
    last_name: PersonName


class LoginRequest(RequestSchema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)
    mfa_code: str | None = Field(default=None, min_length=6, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class RefreshTokenRequest(RequestSchema):
    refresh_token: str = Field(min_length=1, max_length=8192)


class TokenPayload(BaseModel):
    sub: UUID
    organization_id: UUID
    type: Literal["access", "refresh"]
    jti: UUID
    exp: datetime


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


class MfaConfirmRequest(RequestSchema):
    code: str = Field(min_length=6, max_length=64)


class MfaConfirmResponse(BaseModel):
    enabled: bool = True
    recovery_codes: list[str]


class MfaDisableRequest(RequestSchema):
    password: str = Field(min_length=1, max_length=1024)
    code: str = Field(min_length=6, max_length=64)
