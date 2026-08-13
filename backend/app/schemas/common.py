"""Shared API request and response contracts."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class RequestSchema(BaseModel):
    """Base for externally supplied payloads that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PageMetadata(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


ResponseItem = TypeVar("ResponseItem")


class PaginatedResponse(BaseModel, Generic[ResponseItem]):
    items: list[ResponseItem]
    meta: PageMetadata
