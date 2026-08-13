from typing import Annotated
from uuid import UUID

from pydantic import ConfigDict, EmailStr, StringConstraints, field_validator

from app.schemas.common import RequestSchema

ContactName = Annotated[str, StringConstraints(min_length=1, max_length=100)]
PhoneNumber = Annotated[str, StringConstraints(min_length=1, max_length=50)]


class ContactFields(RequestSchema):
    first_name: ContactName
    last_name: ContactName
    email: EmailStr | None = None
    phone: PhoneNumber | None = None


class ContactCreate(ContactFields):
    company_id: UUID


class ContactUpdate(RequestSchema):
    company_id: UUID | None = None
    first_name: ContactName | None = None
    last_name: ContactName | None = None
    email: EmailStr | None = None
    phone: PhoneNumber | None = None

    @field_validator("company_id", "first_name", "last_name")
    @classmethod
    def require_non_null_names(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Contact names cannot be null")
        return value


class ContactResponse(ContactFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
