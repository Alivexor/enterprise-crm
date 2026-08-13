from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.common import RequestSchema

TaskTitle = Annotated[str, StringConstraints(min_length=1, max_length=255)]
TaskDescription = Annotated[str, StringConstraints(max_length=20_000)]
TaskPriority = Literal["low", "medium", "high", "urgent"]
TaskStatus = Literal["open", "in_progress", "completed", "cancelled"]


class TaskCreate(RequestSchema):
    title: TaskTitle
    description: TaskDescription | None = None
    priority: TaskPriority = "medium"
    status: TaskStatus = "open"
    due_date: datetime | None = None
    assigned_user_id: UUID | None = None


class TaskUpdate(RequestSchema):
    title: TaskTitle | None = None
    description: TaskDescription | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None
    assigned_user_id: UUID | None = None

    @field_validator("title", "priority", "status", "assigned_user_id")
    @classmethod
    def require_non_null_required_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    assigned_user_id: UUID
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
