from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.schemas.common import PageMetadata, PaginatedResponse
from app.security.dependencies import CurrentUser
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.company import (
    CompanyDeletionConflictError,
    CompanyNotFoundError,
    company_service,
)

router = APIRouter(prefix="/companies", tags=["companies"])
DatabaseSession = Annotated[Session, Depends(get_db)]
CompanyCreateAccess = Annotated[
    User, Depends(require_permissions(PermissionName.COMPANIES_CREATE))
]
CompanyReadAccess = Annotated[
    User, Depends(require_permissions(PermissionName.COMPANIES_READ))
]
CompanyUpdateAccess = Annotated[
    User, Depends(require_permissions(PermissionName.COMPANIES_UPDATE))
]
CompanyDeleteAccess = Annotated[
    User, Depends(require_permissions(PermissionName.COMPANIES_DELETE))
]


def _company_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Company not found",
    )


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    company_data: CompanyCreate,
    database_session: DatabaseSession,
    current_user: CurrentUser,
    _: CompanyCreateAccess,
) -> CompanyResponse:
    company = company_service.create_company(
        database_session,
        current_user.organization_id,
        current_user.id,
        company_data,
    )
    return CompanyResponse.model_validate(company)


@router.get("", response_model=PaginatedResponse[CompanyResponse])
def list_companies(
    database_session: DatabaseSession,
    current_user: CurrentUser,
    _: CompanyReadAccess,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    industry: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    sort_by: Literal["name", "created_at", "updated_at"] = "name",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> PaginatedResponse[CompanyResponse]:
    companies, total = company_service.list_companies(
        database_session,
        current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        industry=industry,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return PaginatedResponse(
        items=[CompanyResponse.model_validate(company) for company in companies],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: UUID,
    database_session: DatabaseSession,
    current_user: CurrentUser,
    _: CompanyReadAccess,
) -> CompanyResponse:
    try:
        company = company_service.get_company(
            database_session, current_user.organization_id, company_id
        )
    except CompanyNotFoundError as exc:
        raise _company_not_found() from exc
    return CompanyResponse.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    company_data: CompanyUpdate,
    database_session: DatabaseSession,
    current_user: CurrentUser,
    _: CompanyUpdateAccess,
) -> CompanyResponse:
    try:
        company = company_service.update_company(
            database_session,
            current_user.organization_id,
            current_user.id,
            company_id,
            company_data,
        )
    except CompanyNotFoundError as exc:
        raise _company_not_found() from exc
    return CompanyResponse.model_validate(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: UUID,
    database_session: DatabaseSession,
    current_user: CurrentUser,
    _: CompanyDeleteAccess,
) -> Response:
    try:
        company_service.delete_company(
            database_session,
            current_user.organization_id,
            current_user.id,
            company_id,
        )
    except CompanyNotFoundError as exc:
        raise _company_not_found() from exc
    except CompanyDeletionConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company cannot be deleted while related records exist",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
