from collections.abc import Callable

from app.models.user import User
from app.security.dependencies import CurrentUser, require_current_user_permissions
from app.security.permission_catalog import PermissionName


def require_permissions(
    *required_permissions: str | PermissionName,
) -> Callable[..., User]:
    """Create a FastAPI dependency that requires every named permission."""
    required = frozenset(
        permission.value
        if isinstance(permission, PermissionName)
        else permission
        for permission in required_permissions
    )
    if not required:
        raise ValueError("At least one permission is required")

    def permission_dependency(current_user: CurrentUser) -> User:
        return require_current_user_permissions(current_user, required)

    return permission_dependency
