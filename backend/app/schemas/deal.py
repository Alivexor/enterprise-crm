"""Request and response contracts for CRM deals."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.schemas.common import RequestSchema

DealTitle = Annotated[str, StringConstraints(min_length=1, max_length=255)]
DealAmount = Annotated[
    Decimal,
    Field(gt=0, max_digits=18, decimal_places=2),
]
DealProbability = Annotated[
    Decimal,
    Field(ge=0, le=100, max_digits=5, decimal_places=2),
]
CurrencyCode = Annotated[
    str,
    StringConstraints(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
]
DealStatus = Literal["open", "won", "lost"]


class DealCreate(RequestSchema):
    company_id: UUID
    contact_id: UUID | None = None
    pipeline_id: UUID
    stage_id: UUID
    assigned_user_id: UUID
    title: DealTitle
    value: DealAmount
    currency: CurrencyCode = "USD"
    probability: DealProbability
    expected_close_date: date
    status: DealStatus = "open"

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class DealUpdate(RequestSchema):
    company_id: UUID | None = None
    contact_id: UUID | None = None
    pipeline_id: UUID | None = None
    stage_id: UUID | None = None
    assigned_user_id: UUID | None = None
    title: DealTitle | None = None
    value: DealAmount | None = None
    currency: CurrencyCode | None = None
    probability: DealProbability | None = None
    expected_close_date: date | None = None
    status: DealStatus | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @model_validator(mode="after")
    def validate_update(self) -> "DealUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field_name in (
            "company_id",
            "pipeline_id",
            "stage_id",
            "assigned_user_id",
            "title",
            "value",
            "currency",
            "probability",
            "expected_close_date",
            "status",
        ):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} may not be null")
        return self


class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    company_id: UUID
    contact_id: UUID | None
    pipeline_id: UUID
    stage_id: UUID
    assigned_user_id: UUID
    title: str
    value: Decimal
    currency: str
    probability: Decimal
    expected_close_date: date
    status: DealStatus
    created_at: datetime
    updated_at: datetime
