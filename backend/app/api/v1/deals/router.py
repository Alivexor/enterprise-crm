from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.deal import DealCreate, DealResponse, DealStatus, DealUpdate
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.deal import (
    DealConflictError,
    DealDeletionConflictError,
    DealNotFoundError,
    DealReferenceNotFoundError,
    DealRelationshipMismatchError,
    deal_service,
)

router = APIRouter(prefix="/deals", tags=["deals"])
DatabaseSession = Annotated[Session, Depends(get_db)]
DealReader = Annotated[User, Depends(require_permissions(PermissionName.DEALS_READ))]
DealCreator = Annotated[User, Depends(require_permissions(PermissionName.DEALS_CREATE))]
DealEditor = Annotated[User, Depends(require_permissions(PermissionName.DEALS_UPDATE))]
DealDeleter = Annotated[User, Depends(require_permissions(PermissionName.DEALS_DELETE))]


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _relationship_mismatch() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Referenced records are not compatible",
    )


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
def create_deal(
    deal_data: DealCreate,
    database_session: DatabaseSession,
    current_user: DealCreator,
) -> DealResponse:
    try:
        deal = deal_service.create_deal(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            deal_data=deal_data,
        )
    except DealReferenceNotFoundError as exc:
        raise _not_found("Referenced record not found") from exc
    except DealRelationshipMismatchError as exc:
        raise _relationship_mismatch() from exc
    except DealConflictError as exc:
        raise _conflict("Deal could not be created") from exc
    return DealResponse.model_validate(deal)


@router.get("", response_model=PaginatedResponse[DealResponse])
def list_deals(
    database_session: DatabaseSession,
    current_user: DealReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    company_id: UUID | None = None,
    contact_id: UUID | None = None,
    pipeline_id: UUID | None = None,
    stage_id: UUID | None = None,
    assigned_user_id: UUID | None = None,
    deal_status: Annotated[DealStatus | None, Query(alias="status")] = None,
    sort_by: Literal[
        "title",
        "value",
        "probability",
        "expected_close_date",
        "created_at",
        "updated_at",
    ] = "created_at",
    sort_direction: Literal["asc", "desc"] = "desc",
) -> PaginatedResponse[DealResponse]:
    try:
        deals, total = deal_service.list_deals(
            database_session,
            organization_id=current_user.organization_id,
            page=page,
            page_size=page_size,
            search=search,
            company_id=company_id,
            contact_id=contact_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            assigned_user_id=assigned_user_id,
            status=deal_status,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except DealReferenceNotFoundError as exc:
        raise _not_found("Referenced record not found") from exc
    except DealRelationshipMismatchError as exc:
        raise _relationship_mismatch() from exc
    return PaginatedResponse(
        items=[DealResponse.model_validate(deal) for deal in deals],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{deal_id}", response_model=DealResponse)
def get_deal(
    deal_id: UUID,
    database_session: DatabaseSession,
    current_user: DealReader,
) -> DealResponse:
    try:
        deal = deal_service.get_deal(
            database_session,
            organization_id=current_user.organization_id,
            deal_id=deal_id,
        )
    except DealNotFoundError as exc:
        raise _not_found("Deal not found") from exc
    return DealResponse.model_validate(deal)


@router.patch("/{deal_id}", response_model=DealResponse)
def update_deal(
    deal_id: UUID,
    deal_data: DealUpdate,
    database_session: DatabaseSession,
    current_user: DealEditor,
) -> DealResponse:
    try:
        deal = deal_service.update_deal(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            deal_id=deal_id,
            deal_data=deal_data,
        )
    except DealNotFoundError as exc:
        raise _not_found("Deal not found") from exc
    except DealReferenceNotFoundError as exc:
        raise _not_found("Referenced record not found") from exc
    except DealRelationshipMismatchError as exc:
        raise _relationship_mismatch() from exc
    except DealConflictError as exc:
        raise _conflict("Deal could not be updated") from exc
    return DealResponse.model_validate(deal)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(
    deal_id: UUID,
    database_session: DatabaseSession,
    current_user: DealDeleter,
) -> Response:
    try:
        deal_service.delete_deal(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            deal_id=deal_id,
        )
    except DealNotFoundError as exc:
        raise _not_found("Deal not found") from exc
    except DealDeletionConflictError as exc:
        raise _conflict("Deal cannot be deleted while related records exist") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
