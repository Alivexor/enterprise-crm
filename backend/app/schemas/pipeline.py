"""Request and response contracts for sales pipelines and their stages."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.schemas.common import RequestSchema

PipelineName = Annotated[str, StringConstraints(min_length=1, max_length=255)]
PipelineDescription = Annotated[str, StringConstraints(max_length=20_000)]
PipelineStageName = Annotated[str, StringConstraints(min_length=1, max_length=100)]
PipelineStageOrder = Annotated[int, Field(ge=0)]
Probability = Annotated[
    Decimal,
    Field(ge=0, le=100, max_digits=5, decimal_places=2),
]


class PipelineCreate(RequestSchema):
    name: PipelineName
    description: PipelineDescription | None = None


class PipelineUpdate(RequestSchema):
    name: PipelineName | None = None
    description: PipelineDescription | None = None

    @model_validator(mode="after")
    def require_change(self) -> "PipelineUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name may not be null")
        return self


class PipelineStageCreate(RequestSchema):
    name: PipelineStageName
    order: PipelineStageOrder
    probability: Probability


class PipelineStageUpdate(RequestSchema):
    name: PipelineStageName | None = None
    order: PipelineStageOrder | None = None
    probability: Probability | None = None

    @model_validator(mode="after")
    def require_change(self) -> "PipelineStageUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field_name in ("name", "order", "probability"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} may not be null")
        return self


class PipelineStageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pipeline_id: UUID
    name: str
    order: int
    probability: Decimal
    created_at: datetime


class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PipelineDetailResponse(PipelineResponse):
    stages: list[PipelineStageResponse]
