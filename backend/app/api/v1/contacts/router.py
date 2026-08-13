from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from app.security.permissions import require_permissions
from app.services.contact import ContactNotFoundError, contact_service

router = APIRouter(prefix="/contacts", tags=["contacts"])
DatabaseSession = Annotated[Session, Depends(get_db)]
ContactReader = Annotated[User, Depends(require_permissions("contacts.read"))]
ContactCreator = Annotated[User, Depends(require_permissions("contacts.create"))]
ContactEditor = Annotated[User, Depends(require_permissions("contacts.update"))]
ContactDeleter = Annotated[User, Depends(require_permissions("contacts.delete"))]


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_data: ContactCreate,
    database_session: DatabaseSession,
    current_user: ContactCreator,
) -> ContactResponse:
    try:
        contact = contact_service.create_contact(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            contact_data=contact_data,
        )
    except ContactNotFoundError as exc:
        raise _not_found() from exc
    return ContactResponse.model_validate(contact)


@router.get("", response_model=PaginatedResponse[ContactResponse])
def list_contacts(
    database_session: DatabaseSession,
    current_user: ContactReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    company_id: UUID | None = None,
    sort_by: Literal["first_name", "last_name", "email"] = "last_name",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> PaginatedResponse[ContactResponse]:
    try:
        contacts, total = contact_service.list_contacts(
            database_session,
            organization_id=current_user.organization_id,
            page=page,
            page_size=page_size,
            search=search,
            company_id=company_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except ContactNotFoundError as exc:
        raise _not_found() from exc
    return PaginatedResponse(
        items=[ContactResponse.model_validate(contact) for contact in contacts],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: UUID,
    database_session: DatabaseSession,
    current_user: ContactReader,
) -> ContactResponse:
    try:
        contact = contact_service.get_contact(
            database_session,
            organization_id=current_user.organization_id,
            contact_id=contact_id,
        )
    except ContactNotFoundError as exc:
        raise _not_found() from exc
    return ContactResponse.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: UUID,
    contact_data: ContactUpdate,
    database_session: DatabaseSession,
    current_user: ContactEditor,
) -> ContactResponse:
    try:
        contact = contact_service.update_contact(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            contact_id=contact_id,
            contact_data=contact_data,
        )
    except ContactNotFoundError as exc:
        raise _not_found() from exc
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: UUID,
    database_session: DatabaseSession,
    current_user: ContactDeleter,
) -> Response:
    try:
        contact_service.delete_contact(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            contact_id=contact_id,
        )
    except ContactNotFoundError as exc:
        raise _not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
