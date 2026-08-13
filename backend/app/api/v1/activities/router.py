from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityResponse, ActivityType, ActivityUpdate
from app.schemas.common import PageMetadata, PaginatedResponse
from app.security.permissions import require_permissions
from app.services.activity import (
    ActivityNotFoundError,
    ActivityReferenceError,
    activity_service,
)

router = APIRouter(prefix="/activities", tags=["activities"])
DatabaseSession = Annotated[Session, Depends(get_db)]
ActivityReader = Annotated[User, Depends(require_permissions("activities.read"))]
ActivityCreator = Annotated[User, Depends(require_permissions("activities.create"))]
ActivityEditor = Annotated[User, Depends(require_permissions("activities.update"))]
ActivityDeleter = Annotated[User, Depends(require_permissions("activities.delete"))]


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_data: ActivityCreate,
    database_session: DatabaseSession,
    current_user: ActivityCreator,
) -> ActivityResponse:
    try:
        activity = activity_service.create_activity(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            activity_data=activity_data,
        )
    except ActivityNotFoundError as exc:
        raise _not_found() from exc
    except ActivityReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return ActivityResponse.model_validate(activity)


@router.get("", response_model=PaginatedResponse[ActivityResponse])
def list_activities(
    database_session: DatabaseSession,
    current_user: ActivityReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    activity_type: Annotated[ActivityType | None, Query(alias="type")] = None,
    completed: bool | None = None,
    user_id: UUID | None = None,
    company_id: UUID | None = None,
    contact_id: UUID | None = None,
    lead_id: UUID | None = None,
    sort_by: Literal["due_date", "created_at", "type"] = "due_date",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> PaginatedResponse[ActivityResponse]:
    activities, total = activity_service.list_activities(
        database_session,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        activity_type=activity_type,
        completed=completed,
        user_id=user_id,
        company_id=company_id,
        contact_id=contact_id,
        lead_id=lead_id,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return PaginatedResponse(
        items=[ActivityResponse.model_validate(activity) for activity in activities],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: UUID,
    database_session: DatabaseSession,
    current_user: ActivityReader,
) -> ActivityResponse:
    try:
        activity = activity_service.get_activity(
            database_session,
            organization_id=current_user.organization_id,
            activity_id=activity_id,
        )
    except ActivityNotFoundError as exc:
        raise _not_found() from exc
    return ActivityResponse.model_validate(activity)


@router.patch("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: UUID,
    activity_data: ActivityUpdate,
    database_session: DatabaseSession,
    current_user: ActivityEditor,
) -> ActivityResponse:
    try:
        activity = activity_service.update_activity(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            activity_id=activity_id,
            activity_data=activity_data,
        )
    except ActivityNotFoundError as exc:
        raise _not_found() from exc
    except ActivityReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return ActivityResponse.model_validate(activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: UUID,
    database_session: DatabaseSession,
    current_user: ActivityDeleter,
) -> Response:
    try:
        activity_service.delete_activity(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            activity_id=activity_id,
        )
    except ActivityNotFoundError as exc:
        raise _not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
