from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditActorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str
    last_name: str


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    created_at: datetime
    user: AuditActorResponse
