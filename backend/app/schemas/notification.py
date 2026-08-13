from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.common import RequestSchema

NotificationType = Annotated[str, StringConstraints(min_length=1, max_length=100)]
NotificationTitle = Annotated[str, StringConstraints(min_length=1, max_length=255)]
NotificationBody = Annotated[str, StringConstraints(max_length=20_000)]
NotificationEntityType = Annotated[str, StringConstraints(min_length=1, max_length=100)]
NotificationReadFilter = Literal["all", "read", "unread"]


class NotificationCreate(RequestSchema):
    user_id: UUID
    type: NotificationType
    title: NotificationTitle
    body: NotificationBody | None = None
    entity_type: NotificationEntityType | None = None
    entity_id: UUID | None = None


class NotificationBulkReadRequest(RequestSchema):
    notification_ids: list[UUID] = Field(min_length=1, max_length=100)


class NotificationBulkReadResponse(BaseModel):
    updated: int


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    type: str
    title: str
    body: str | None
    entity_type: str | None
    entity_id: UUID | None
    read_at: datetime | None
    created_at: datetime
