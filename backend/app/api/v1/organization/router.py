from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.security.permissions import require_permissions
from app.services.organization import (
    OrganizationNotFoundError,
    organization_service,
)

router = APIRouter(prefix="/organization", tags=["organization"])
DatabaseSession = Annotated[Session, Depends(get_db)]
OrganizationReader = Annotated[User, Depends(require_permissions("organizations.read"))]
OrganizationEditor = Annotated[User, Depends(require_permissions("organizations.update"))]


@router.get("", response_model=OrganizationResponse)
def get_organization(
    database_session: DatabaseSession, current_user: OrganizationReader
) -> OrganizationResponse:
    try:
        organization = organization_service.get_organization(
            database_session, current_user.organization_id
        )
    except OrganizationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Organization not found") from exc
    return OrganizationResponse.model_validate(organization)


@router.patch("", response_model=OrganizationResponse)
def update_organization(
    organization_data: OrganizationUpdate,
    database_session: DatabaseSession,
    current_user: OrganizationEditor,
) -> OrganizationResponse:
    try:
        organization = organization_service.update_organization(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            organization_data=organization_data,
        )
    except OrganizationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Organization not found") from exc
    return OrganizationResponse.model_validate(organization)
