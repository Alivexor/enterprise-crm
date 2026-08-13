from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.common import RequestSchema

TagName = Annotated[str, StringConstraints(min_length=1, max_length=100)]
TagColor = Annotated[
    str,
    StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$"),
]
TaggableEntityType = Literal["company", "contact", "lead", "deal"]


class TagCreate(RequestSchema):
    name: TagName
    color: TagColor


class TagUpdate(RequestSchema):
    name: TagName | None = None
    color: TagColor | None = None

    @field_validator("name", "color")
    @classmethod
    def require_non_null_fields(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Tag fields cannot be null")
        return value


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    color: str
    created_at: datetime
