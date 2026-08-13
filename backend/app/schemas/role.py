from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.common import RequestSchema
from app.schemas.user import PermissionResponse

RoleName = Annotated[str, StringConstraints(min_length=1, max_length=100)]


class RoleCreate(RequestSchema):
    name: RoleName
    permission_ids: list[UUID] = Field(default_factory=list, max_length=100)


class RoleUpdate(RequestSchema):
    name: RoleName | None = None
    permission_ids: list[UUID] | None = Field(default=None, max_length=100)

    @field_validator("name", "permission_ids")
    @classmethod
    def reject_null_for_explicit_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class RoleDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    permissions: list[PermissionResponse]
