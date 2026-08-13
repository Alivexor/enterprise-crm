from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.notification import (
    NotificationBulkReadRequest,
    NotificationBulkReadResponse,
    NotificationReadFilter,
    NotificationResponse,
)
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.notification import NotificationNotFoundError, notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])
DatabaseSession = Annotated[Session, Depends(get_db)]
NotificationReader = Annotated[
    User, Depends(require_permissions(PermissionName.NOTIFICATIONS_READ))
]
NotificationEditor = Annotated[
    User, Depends(require_permissions(PermissionName.NOTIFICATIONS_UPDATE))
]


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def list_notifications(
    database_session: DatabaseSession,
    current_user: NotificationReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    read_state: Annotated[NotificationReadFilter, Query(alias="read")] = "all",
) -> PaginatedResponse[NotificationResponse]:
    notifications, total = notification_service.list_notifications(
        database_session,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        read_state=read_state,
    )
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(notification) for notification in notifications],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: UUID,
    database_session: DatabaseSession,
    current_user: NotificationEditor,
) -> NotificationResponse:
    try:
        notification = notification_service.mark_notification_read(
            database_session,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        ) from exc
    return NotificationResponse.model_validate(notification)


@router.post("/read-bulk", response_model=NotificationBulkReadResponse)
def mark_notifications_read_bulk(
    payload: NotificationBulkReadRequest,
    database_session: DatabaseSession,
    current_user: NotificationEditor,
) -> NotificationBulkReadResponse:
    updated = notification_service.mark_notifications_read(
        database_session,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        notification_ids=payload.notification_ids,
    )
    return NotificationBulkReadResponse(updated=updated)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(
    database_session: DatabaseSession,
    current_user: NotificationEditor,
) -> Response:
    notification_service.mark_all_notifications_read(
        database_session,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
