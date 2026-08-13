from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.deal import DealResponse
from app.schemas.lead import (
    LeadConversionRequest,
    LeadConversionResponse,
    LeadCreate,
    LeadResponse,
    LeadStatus,
    LeadUpdate,
)
from app.security.permissions import require_permissions
from app.services.lead import (
    LeadConversionConflictError,
    LeadConversionValidationError,
    LeadNotFoundError,
    LeadReferenceError,
    lead_service,
)

router = APIRouter(prefix="/leads", tags=["leads"])
DatabaseSession = Annotated[Session, Depends(get_db)]
LeadReader = Annotated[User, Depends(require_permissions("leads.read"))]
LeadCreator = Annotated[User, Depends(require_permissions("leads.create"))]
LeadEditor = Annotated[User, Depends(require_permissions("leads.update"))]
LeadDeleter = Annotated[User, Depends(require_permissions("leads.delete"))]
LeadConverter = Annotated[
    User, Depends(require_permissions("leads.update", "deals.create"))
]


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    lead_data: LeadCreate,
    database_session: DatabaseSession,
    current_user: LeadCreator,
) -> LeadResponse:
    try:
        lead = lead_service.create_lead(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            lead_data=lead_data,
        )
    except LeadNotFoundError as exc:
        raise _not_found() from exc
    except LeadReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return LeadResponse.model_validate(lead)


@router.get("", response_model=PaginatedResponse[LeadResponse])
def list_leads(
    database_session: DatabaseSession,
    current_user: LeadReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    status_filter: Annotated[LeadStatus | None, Query(alias="status")] = None,
    assigned_user_id: UUID | None = None,
    company_id: UUID | None = None,
    sort_by: Literal["created_at", "title", "status"] = "created_at",
    sort_direction: Literal["asc", "desc"] = "desc",
) -> PaginatedResponse[LeadResponse]:
    leads, total = lead_service.list_leads(
        database_session,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        assigned_user_id=assigned_user_id,
        company_id=company_id,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return PaginatedResponse(
        items=[LeadResponse.model_validate(lead) for lead in leads],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.post("/{lead_id}/convert", response_model=LeadConversionResponse)
def convert_lead(
    lead_id: UUID,
    conversion_data: LeadConversionRequest,
    database_session: DatabaseSession,
    current_user: LeadConverter,
) -> LeadConversionResponse:
    try:
        lead, deal = lead_service.convert_lead(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            lead_id=lead_id,
            conversion_data=conversion_data,
        )
    except LeadNotFoundError as exc:
        raise _not_found() from exc
    except LeadConversionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except LeadConversionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return LeadConversionResponse(
        lead=LeadResponse.model_validate(lead),
        deal=DealResponse.model_validate(deal),
    )


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: UUID,
    database_session: DatabaseSession,
    current_user: LeadReader,
) -> LeadResponse:
    try:
        lead = lead_service.get_lead(
            database_session, organization_id=current_user.organization_id, lead_id=lead_id
        )
    except LeadNotFoundError as exc:
        raise _not_found() from exc
    return LeadResponse.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    database_session: DatabaseSession,
    current_user: LeadEditor,
) -> LeadResponse:
    try:
        lead = lead_service.update_lead(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            lead_id=lead_id,
            lead_data=lead_data,
        )
    except LeadNotFoundError as exc:
        raise _not_found() from exc
    except LeadReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: UUID,
    database_session: DatabaseSession,
    current_user: LeadDeleter,
) -> Response:
    try:
        lead_service.delete_lead(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            lead_id=lead_id,
        )
    except LeadNotFoundError as exc:
        raise _not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
