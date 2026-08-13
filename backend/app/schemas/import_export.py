from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.schemas.common import RequestSchema
from app.schemas.company import CompanyCreate, CompanyName
from app.schemas.contact import ContactName, PhoneNumber

ImportResource = Literal["companies", "contacts"]
CompanyImportHeaders = ("name", "website", "industry")
ContactImportHeaders = (
    "company_id",
    "company_name",
    "first_name",
    "last_name",
    "email",
    "phone",
)


def _blank_to_none(value: object) -> object:
    if isinstance(value, str) and not value.strip():
        return None
    return value


class CompanyImportRow(CompanyCreate):
    @field_validator("website", "industry", mode="before")
    @classmethod
    def normalize_blank_optional_values(cls, value: object) -> object:
        return _blank_to_none(value)


class ContactImportRow(RequestSchema):
    company_id: UUID | None = None
    company_name: CompanyName | None = None
    first_name: ContactName
    last_name: ContactName
    email: EmailStr | None = None
    phone: PhoneNumber | None = None

    @field_validator("company_id", "company_name", "email", "phone", mode="before")
    @classmethod
    def normalize_blank_optional_values(cls, value: object) -> object:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def require_company_reference(self) -> "ContactImportRow":
        if self.company_id is None and self.company_name is None:
            raise ValueError("Either company_id or company_name is required")
        return self


class ImportRowError(BaseModel):
    row_number: int = Field(ge=2)
    field: str | None = None
    message: str


class ImportResponse(BaseModel):
    resource: ImportResource
    rows_processed: int = Field(ge=0)
    created_count: int = Field(ge=0)
