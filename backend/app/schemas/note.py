from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.common import RequestSchema

NoteContent = Annotated[str, StringConstraints(min_length=1, max_length=20_000)]


class NoteCreate(RequestSchema):
    content: NoteContent
    company_id: UUID | None = None
    contact_id: UUID | None = None
    lead_id: UUID | None = None


class NoteUpdate(RequestSchema):
    content: NoteContent | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    lead_id: UUID | None = None

    @field_validator("content")
    @classmethod
    def require_non_null_content(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Note content cannot be null")
        return value


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    company_id: UUID | None
    contact_id: UUID | None
    lead_id: UUID | None
    content: str
    created_at: datetime
    updated_at: datetime
