from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.common import RequestSchema

OrganizationName = Annotated[str, StringConstraints(min_length=1, max_length=255)]


class OrganizationUpdate(RequestSchema):
    name: OrganizationName


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
