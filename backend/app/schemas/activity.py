from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.common import RequestSchema

ActivityType = Literal["call", "email", "meeting", "follow_up"]
ActivityTitle = Annotated[str, StringConstraints(min_length=1, max_length=255)]
ActivityDescription = Annotated[str, StringConstraints(max_length=20_000)]


class ActivityCreate(RequestSchema):
    type: ActivityType
    title: ActivityTitle
    description: ActivityDescription | None = None
    due_date: datetime | None = None
    completed: bool = False
    user_id: UUID | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    lead_id: UUID | None = None


class ActivityUpdate(RequestSchema):
    type: ActivityType | None = None
    title: ActivityTitle | None = None
    description: ActivityDescription | None = None
    due_date: datetime | None = None
    completed: bool | None = None
    user_id: UUID | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    lead_id: UUID | None = None

    @field_validator("type", "title", "user_id", "completed")
    @classmethod
    def require_non_null_required_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    company_id: UUID | None
    contact_id: UUID | None
    lead_id: UUID | None
    type: ActivityType
    title: str
    description: str | None
    due_date: datetime | None
    completed: bool
    created_at: datetime
