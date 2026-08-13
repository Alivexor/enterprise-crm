from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.search import SearchEntityType, SearchResponse
from app.security.dependencies import get_current_user_permissions
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.search import search_service

router = APIRouter(prefix="/search", tags=["search"])
DatabaseSession = Annotated[Session, Depends(get_db)]
SearchReader = Annotated[User, Depends(require_permissions("search.read"))]

_SEARCH_RESOURCE_PERMISSIONS: dict[SearchEntityType, PermissionName] = {
    "company": PermissionName.COMPANIES_READ,
    "contact": PermissionName.CONTACTS_READ,
    "lead": PermissionName.LEADS_READ,
    "deal": PermissionName.DEALS_READ,
    "task": PermissionName.TASKS_READ,
    "activity": PermissionName.ACTIVITIES_READ,
    "note": PermissionName.NOTES_READ,
}


@router.get("", response_model=SearchResponse)
def search(
    database_session: DatabaseSession,
    current_user: SearchReader,
    query: Annotated[str, Query(alias="q", min_length=1, max_length=255)],
    limit_per_type: Annotated[int, Query(ge=1, le=20)] = 5,
) -> SearchResponse:
    normalized_query = query.strip()
    if not normalized_query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Search query must not be blank",
        )
    granted_permissions = get_current_user_permissions(current_user)
    allowed_entity_types = frozenset(
        entity_type
        for entity_type, required_permission in _SEARCH_RESOURCE_PERMISSIONS.items()
        if required_permission.value in granted_permissions
    )
    return search_service.search(
        database_session,
        organization_id=current_user.organization_id,
        query=normalized_query,
        limit_per_type=limit_per_type,
        allowed_entity_types=allowed_entity_types,
    )
