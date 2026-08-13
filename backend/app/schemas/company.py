from datetime import datetime
from typing import Annotated
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.common import RequestSchema

CompanyName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
Website = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)]
Industry = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class CompanyFields(RequestSchema):
    website: Website | None = None
    industry: Industry | None = None

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed_url = urlparse(value)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("Website must be an absolute HTTP(S) URL")
        return value


class CompanyCreate(CompanyFields):
    name: CompanyName


class CompanyUpdate(CompanyFields):
    name: CompanyName | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    website: str | None
    industry: str | None
    created_at: datetime
    updated_at: datetime
