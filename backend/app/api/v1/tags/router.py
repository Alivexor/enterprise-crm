from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.tag import TagCreate, TagResponse, TagUpdate, TaggableEntityType
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.tag import (
    TagAlreadyExistsError,
    TagAssignmentTargetNotFoundError,
    TagFilterError,
    TagNotFoundError,
    tag_service,
)

router = APIRouter(prefix="/tags", tags=["tags"])
DatabaseSession = Annotated[Session, Depends(get_db)]
TagReader = Annotated[User, Depends(require_permissions(PermissionName.TAGS_READ))]
TagCreator = Annotated[User, Depends(require_permissions(PermissionName.TAGS_CREATE))]
TagEditor = Annotated[User, Depends(require_permissions(PermissionName.TAGS_UPDATE))]
TagDeleter = Annotated[User, Depends(require_permissions(PermissionName.TAGS_DELETE))]


def _tag_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")


def _target_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Tag assignment target not found",
    )


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    database_session: DatabaseSession,
    current_user: TagCreator,
) -> TagResponse:
    try:
        tag = tag_service.create_tag(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            tag_data=tag_data,
        )
    except TagAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        ) from exc
    return TagResponse.model_validate(tag)


@router.get("", response_model=PaginatedResponse[TagResponse])
def list_tags(
    database_session: DatabaseSession,
    current_user: TagReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    entity_type: TaggableEntityType | None = None,
    entity_id: UUID | None = None,
    sort_by: Literal["name", "created_at"] = "name",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> PaginatedResponse[TagResponse]:
    try:
        tags, total = tag_service.list_tags(
            database_session,
            organization_id=current_user.organization_id,
            page=page,
            page_size=page_size,
            search=search,
            entity_type=entity_type,
            entity_id=entity_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except TagFilterError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except TagAssignmentTargetNotFoundError as exc:
        raise _target_not_found() from exc
    return PaginatedResponse(
        items=[TagResponse.model_validate(tag) for tag in tags],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.put(
    "/{tag_id}/assignments/{entity_type}/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def assign_tag(
    tag_id: UUID,
    entity_type: TaggableEntityType,
    entity_id: UUID,
    database_session: DatabaseSession,
    current_user: TagEditor,
) -> Response:
    try:
        tag_service.assign_tag(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    except TagNotFoundError as exc:
        raise _tag_not_found() from exc
    except TagAssignmentTargetNotFoundError as exc:
        raise _target_not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{tag_id}/assignments/{entity_type}/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_tag(
    tag_id: UUID,
    entity_type: TaggableEntityType,
    entity_id: UUID,
    database_session: DatabaseSession,
    current_user: TagEditor,
) -> Response:
    try:
        tag_service.unassign_tag(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    except TagNotFoundError as exc:
        raise _tag_not_found() from exc
    except TagAssignmentTargetNotFoundError as exc:
        raise _target_not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: UUID,
    database_session: DatabaseSession,
    current_user: TagReader,
) -> TagResponse:
    try:
        tag = tag_service.get_tag(
            database_session,
            organization_id=current_user.organization_id,
            tag_id=tag_id,
        )
    except TagNotFoundError as exc:
        raise _tag_not_found() from exc
    return TagResponse.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: UUID,
    tag_data: TagUpdate,
    database_session: DatabaseSession,
    current_user: TagEditor,
) -> TagResponse:
    try:
        tag = tag_service.update_tag(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            tag_id=tag_id,
            tag_data=tag_data,
        )
    except TagNotFoundError as exc:
        raise _tag_not_found() from exc
    except TagAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        ) from exc
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: UUID,
    database_session: DatabaseSession,
    current_user: TagDeleter,
) -> Response:
    try:
        tag_service.delete_tag(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            tag_id=tag_id,
        )
    except TagNotFoundError as exc:
        raise _tag_not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
