from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None


class UserCreate(BaseModel):
    organization_id: UUID
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    mfa_enabled: bool
    roles: list[RoleResponse]
    permissions: list[PermissionResponse]
    created_at: datetime
    updated_at: datetime
