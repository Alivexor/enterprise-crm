from typing import Annotated
from uuid import UUID

from pydantic import EmailStr, Field, StringConstraints, field_validator

from app.schemas.common import RequestSchema
from app.schemas.user import UserResponse

UserName = Annotated[str, StringConstraints(min_length=1, max_length=100)]


class ManagedUserCreate(RequestSchema):
    email: EmailStr
    password: str = Field(min_length=12, max_length=1024)
    first_name: UserName
    last_name: UserName
    role_ids: list[UUID] = Field(min_length=1, max_length=25)


class ManagedUserUpdate(RequestSchema):
    email: EmailStr | None = None
    first_name: UserName | None = None
    last_name: UserName | None = None
    is_active: bool | None = None
    role_ids: list[UUID] | None = Field(default=None, min_length=1, max_length=25)

    @field_validator("email", "first_name", "last_name", "is_active", "role_ids")
    @classmethod
    def reject_null_for_explicit_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class ProfileUpdate(RequestSchema):
    email: EmailStr | None = None
    first_name: UserName | None = None
    last_name: UserName | None = None

    @field_validator("email", "first_name", "last_name")
    @classmethod
    def reject_null_for_explicit_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class PasswordChange(RequestSchema):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=12, max_length=1024)


ManagedUserResponse = UserResponse
