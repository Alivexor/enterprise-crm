from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

AttachmentEntityType = Literal[
    "company",
    "contact",
    "lead",
    "deal",
    "activity",
    "task",
    "note",
]
AttachmentFilename = Annotated[str, StringConstraints(min_length=1, max_length=255)]
AttachmentContentType = Annotated[str, StringConstraints(min_length=1, max_length=255)]


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    uploaded_by_user_id: UUID
    entity_type: AttachmentEntityType
    entity_id: UUID
    original_filename: AttachmentFilename
    content_type: AttachmentContentType
    size_bytes: int
    created_at: datetime
