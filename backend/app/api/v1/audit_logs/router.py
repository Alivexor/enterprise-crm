from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.schemas.common import PageMetadata, PaginatedResponse
from app.security.permissions import require_permissions
from app.services.audit import audit_service

router = APIRouter(prefix="/audit-logs", tags=["audit logs"])
DatabaseSession = Annotated[Session, Depends(get_db)]
AuditLogReader = Annotated[User, Depends(require_permissions("audit_logs.read"))]


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
def list_audit_logs(
    database_session: DatabaseSession,
    current_user: AuditLogReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    action: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    entity_type: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    user_id: UUID | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    sort_direction: Literal["asc", "desc"] = "desc",
) -> PaginatedResponse[AuditLogResponse]:
    if any(
        value is not None and value.tzinfo is None
        for value in (created_after, created_before)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Audit date filters must include a timezone offset",
        )
    if (
        created_after is not None
        and created_before is not None
        and created_after > created_before
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="created_after must be before or equal to created_before",
        )
    entries, total = audit_service.list_entries(
        database_session,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search.strip() if search is not None else None,
        action=action,
        entity_type=entity_type,
        user_id=user_id,
        created_after=created_after,
        created_before=created_before,
        sort_direction=sort_direction,
    )
    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(entry) for entry in entries],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )
