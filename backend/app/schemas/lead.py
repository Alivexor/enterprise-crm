from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.schemas.common import RequestSchema
from app.schemas.deal import CurrencyCode, DealAmount, DealProbability, DealResponse, DealTitle

LeadTitle = Annotated[str, StringConstraints(min_length=1, max_length=255)]
LeadDescription = Annotated[str, StringConstraints(max_length=20_000)]
LeadSource = Literal[
    "advertising",
    "event",
    "outbound",
    "referral",
    "website",
    "other",
]
LeadStatus = Literal["new", "qualified", "unqualified", "converted", "lost"]


class LeadCreate(RequestSchema):
    title: LeadTitle
    description: LeadDescription | None = None
    source: LeadSource = "other"
    status: LeadStatus = "new"
    company_id: UUID | None = None
    contact_id: UUID | None = None
    assigned_user_id: UUID | None = None


class LeadUpdate(RequestSchema):
    title: LeadTitle | None = None
    description: LeadDescription | None = None
    source: LeadSource | None = None
    status: LeadStatus | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    assigned_user_id: UUID | None = None

    @field_validator("title", "source", "status", "assigned_user_id")
    @classmethod
    def require_non_null_required_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    company_id: UUID | None
    contact_id: UUID | None
    title: str
    description: str | None
    source: LeadSource
    status: LeadStatus
    assigned_user_id: UUID
    created_at: datetime
    updated_at: datetime

class LeadConversionRequest(RequestSchema):
    pipeline_id: UUID
    stage_id: UUID
    value: DealAmount
    currency: CurrencyCode = "USD"
    probability: DealProbability
    expected_close_date: date
    title: DealTitle | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class LeadConversionResponse(BaseModel):
    lead: LeadResponse
    deal: DealResponse
