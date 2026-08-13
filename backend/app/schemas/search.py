from typing import Literal
from uuid import UUID

from pydantic import BaseModel

SearchEntityType = Literal[
    "company",
    "contact",
    "lead",
    "deal",
    "task",
    "activity",
    "note",
]


class SearchResult(BaseModel):
    entity_type: SearchEntityType
    id: UUID
    title: str
    subtitle: str | None = None


class SearchResponse(BaseModel):
    items: list[SearchResult]
