from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.user import UserResponse
from app.schemas.user_management import (
    ManagedUserCreate,
    ManagedUserUpdate,
    PasswordChange,
    ProfileUpdate,
)
from app.security.dependencies import CurrentUser
from app.security.permissions import require_permissions
from app.services.auth import AuthenticationError
from app.services.user_management import (
    ManagedUserConflictError,
    ManagedUserNotFoundError,
    ManagedUserValidationError,
    user_management_service,
)

router = APIRouter(prefix="/users", tags=["users"])
profile_router = APIRouter(prefix="/profile", tags=["profile"])
DatabaseSession = Annotated[Session, Depends(get_db)]
UserReader = Annotated[User, Depends(require_permissions("users.read"))]
UserCreator = Annotated[User, Depends(require_permissions("users.create"))]
UserEditor = Annotated[User, Depends(require_permissions("users.update"))]


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="User not found")


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    database_session: DatabaseSession,
    current_user: UserReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    is_active: bool | None = None,
) -> PaginatedResponse[UserResponse]:
    users, total = user_management_service.list_users(
        database_session,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
    )
    return PaginatedResponse(
        items=[user_management_service.response(user) for user in users],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: ManagedUserCreate,
    database_session: DatabaseSession,
    current_user: UserCreator,
) -> UserResponse:
    try:
        user = user_management_service.create_user(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            user_data=user_data,
        )
    except ManagedUserConflictError as exc:
        raise HTTPException(status_code=409, detail="A user with this email already exists") from exc
    except ManagedUserValidationError as exc:
        raise HTTPException(status_code=422, detail="One or more roles do not exist") from exc
    return user_management_service.response(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    database_session: DatabaseSession,
    current_user: UserReader,
) -> UserResponse:
    try:
        user = user_management_service.get_user(
            database_session, organization_id=current_user.organization_id, user_id=user_id
        )
    except ManagedUserNotFoundError as exc:
        raise _not_found() from exc
    return user_management_service.response(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_data: ManagedUserUpdate,
    database_session: DatabaseSession,
    current_user: UserEditor,
) -> UserResponse:
    try:
        user = user_management_service.update_user(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            user_id=user_id,
            user_data=user_data,
        )
    except ManagedUserNotFoundError as exc:
        raise _not_found() from exc
    except ManagedUserValidationError as exc:
        raise HTTPException(status_code=422, detail="One or more roles do not exist") from exc
    except ManagedUserConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="You cannot deactivate yourself or change your own roles here",
        ) from exc
    return user_management_service.response(user)


@profile_router.get("", response_model=UserResponse)
def get_profile(current_user: CurrentUser) -> UserResponse:
    return user_management_service.response(current_user)


@profile_router.patch("", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> UserResponse:
    try:
        user = user_management_service.update_profile(
            database_session, current_user=current_user, profile_data=profile_data
        )
    except ManagedUserConflictError as exc:
        raise HTTPException(status_code=409, detail="A user with this email already exists") from exc
    return user_management_service.response(user)


@profile_router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    password_data: PasswordChange,
    database_session: DatabaseSession,
    current_user: CurrentUser,
) -> None:
    try:
        user_management_service.change_password(
            database_session, current_user=current_user, password_data=password_data
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=400, detail="Current password is incorrect") from exc
