from collections.abc import Callable, Iterable
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.security.permission_catalog import PermissionName
from app.services.auth import AuthenticationError, auth_service
from app.services.v3_platform import v3_platform_service

bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    database_session: DatabaseSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    if token.startswith("crm_live_"):
        api_user = v3_platform_service.authenticate_api_key(database_session, token)
        if api_user is not None:
            return api_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return auth_service.get_current_authenticated_user(database_session, token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[User, Depends(get_current_user)]

ImportExportResource = Literal["companies", "contacts"]
ImportExportOperation = Literal["import", "export"]


def get_current_user_permissions(current_user: User) -> frozenset[str]:
    """Return permissions granted through roles in the user's organization."""
    return frozenset(
        permission.name
        for role in current_user.roles
        if role.organization_id == current_user.organization_id
        for permission in role.permissions
    )


def require_current_user_permissions(
    current_user: User, required_permissions: Iterable[str]
) -> User:
    """Ensure an authenticated user has every supplied organization permission."""
    required = frozenset(required_permissions)
    if not required.issubset(get_current_user_permissions(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


def require_import_export_permissions(
    operation: ImportExportOperation,
) -> Callable[..., User]:
    """Authorize CSV operations with both operation and resource permissions."""
    operation_permission = (
        PermissionName.IMPORTS_CREATE
        if operation == "import"
        else PermissionName.EXPORTS_CREATE
    )
    resource_permissions = {
        "companies": {
            "import": PermissionName.COMPANIES_CREATE,
            "export": PermissionName.COMPANIES_READ,
        },
        "contacts": {
            "import": PermissionName.CONTACTS_CREATE,
            "export": PermissionName.CONTACTS_READ,
        },
    }

    def permission_dependency(
        resource: ImportExportResource, current_user: CurrentUser
    ) -> User:
        return require_current_user_permissions(
            current_user,
            (operation_permission.value, resource_permissions[resource][operation].value),
        )

    return permission_dependency
