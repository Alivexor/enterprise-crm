from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.role import RoleCreate, RoleDetailResponse, RoleUpdate
from app.schemas.user import PermissionResponse
from app.security.permissions import require_permissions
from app.services.role import (
    RoleConflictError,
    RoleNotFoundError,
    RoleValidationError,
    role_service,
)

router = APIRouter(prefix="/roles", tags=["roles"])
DatabaseSession = Annotated[Session, Depends(get_db)]
RoleReader = Annotated[User, Depends(require_permissions("roles.read"))]
RoleCreator = Annotated[User, Depends(require_permissions("roles.create"))]
RoleEditor = Annotated[User, Depends(require_permissions("roles.update"))]
RoleDeleter = Annotated[User, Depends(require_permissions("roles.delete"))]
PermissionReader = Annotated[User, Depends(require_permissions("permissions.read"))]


def _role_response(role: object) -> RoleDetailResponse:
    return RoleDetailResponse.model_validate(role)


@router.get("", response_model=list[RoleDetailResponse])
def list_roles(
    database_session: DatabaseSession, current_user: RoleReader
) -> list[RoleDetailResponse]:
    roles = role_service.list_roles(database_session, current_user.organization_id)
    return [_role_response(role) for role in roles]


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(
    database_session: DatabaseSession, _: PermissionReader
) -> list[PermissionResponse]:
    permissions = role_service.list_permissions(database_session)
    return [PermissionResponse.model_validate(permission) for permission in permissions]


@router.post("", response_model=RoleDetailResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreate,
    database_session: DatabaseSession,
    current_user: RoleCreator,
) -> RoleDetailResponse:
    try:
        role = role_service.create_role(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            role_data=role_data,
        )
    except RoleValidationError as exc:
        raise HTTPException(status_code=422, detail="One or more permissions do not exist") from exc
    except RoleConflictError as exc:
        raise HTTPException(status_code=409, detail="A role with this name already exists") from exc
    return _role_response(role)


@router.get("/{role_id}", response_model=RoleDetailResponse)
def get_role(
    role_id: UUID,
    database_session: DatabaseSession,
    current_user: RoleReader,
) -> RoleDetailResponse:
    try:
        role = role_service.get_role(database_session, current_user.organization_id, role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Role not found") from exc
    return _role_response(role)


@router.patch("/{role_id}", response_model=RoleDetailResponse)
def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    database_session: DatabaseSession,
    current_user: RoleEditor,
) -> RoleDetailResponse:
    try:
        role = role_service.update_role(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            role_id=role_id,
            role_data=role_data,
        )
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Role not found") from exc
    except RoleValidationError as exc:
        raise HTTPException(status_code=422, detail="One or more permissions do not exist") from exc
    except RoleConflictError as exc:
        raise HTTPException(status_code=409, detail="The system admin role cannot be modified") from exc
    return _role_response(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: UUID,
    database_session: DatabaseSession,
    current_user: RoleDeleter,
) -> Response:
    try:
        role_service.delete_role(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            role_id=role_id,
        )
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Role not found") from exc
    except RoleConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="The system admin role and assigned roles cannot be deleted",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
