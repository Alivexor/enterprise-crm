from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.note import NoteNotFoundError, note_service

router = APIRouter(prefix="/notes", tags=["notes"])
DatabaseSession = Annotated[Session, Depends(get_db)]
NoteReader = Annotated[User, Depends(require_permissions(PermissionName.NOTES_READ))]
NoteCreator = Annotated[User, Depends(require_permissions(PermissionName.NOTES_CREATE))]
NoteEditor = Annotated[User, Depends(require_permissions(PermissionName.NOTES_UPDATE))]
NoteDeleter = Annotated[User, Depends(require_permissions(PermissionName.NOTES_DELETE))]


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_data: NoteCreate,
    database_session: DatabaseSession,
    current_user: NoteCreator,
) -> NoteResponse:
    try:
        note = note_service.create_note(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            note_data=note_data,
        )
    except NoteNotFoundError as exc:
        raise _not_found() from exc
    return NoteResponse.model_validate(note)


@router.get("", response_model=PaginatedResponse[NoteResponse])
def list_notes(
    database_session: DatabaseSession,
    current_user: NoteReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    company_id: UUID | None = None,
    contact_id: UUID | None = None,
    lead_id: UUID | None = None,
    user_id: UUID | None = None,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    sort_direction: Literal["asc", "desc"] = "desc",
) -> PaginatedResponse[NoteResponse]:
    try:
        notes, total = note_service.list_notes(
            database_session,
            organization_id=current_user.organization_id,
            page=page,
            page_size=page_size,
            search=search,
            company_id=company_id,
            contact_id=contact_id,
            lead_id=lead_id,
            user_id=user_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except NoteNotFoundError as exc:
        raise _not_found() from exc
    return PaginatedResponse(
        items=[NoteResponse.model_validate(note) for note in notes],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: UUID,
    database_session: DatabaseSession,
    current_user: NoteReader,
) -> NoteResponse:
    try:
        note = note_service.get_note(
            database_session,
            organization_id=current_user.organization_id,
            note_id=note_id,
        )
    except NoteNotFoundError as exc:
        raise _not_found() from exc
    return NoteResponse.model_validate(note)


@router.patch("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: UUID,
    note_data: NoteUpdate,
    database_session: DatabaseSession,
    current_user: NoteEditor,
) -> NoteResponse:
    try:
        note = note_service.update_note(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            note_id=note_id,
            note_data=note_data,
        )
    except NoteNotFoundError as exc:
        raise _not_found() from exc
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: UUID,
    database_session: DatabaseSession,
    current_user: NoteDeleter,
) -> Response:
    try:
        note_service.delete_note(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            note_id=note_id,
        )
    except NoteNotFoundError as exc:
        raise _not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
