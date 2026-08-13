from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.security.password import hash_password
from app.security.permission_catalog import (
    DEFAULT_ADMIN_PERMISSION_NAMES,
    PERMISSION_CATALOG,
)

DEFAULT_ADMIN_ROLE_NAME = "admin"


class DevelopmentSeedConfigurationError(Exception):
    """Raised when development seed configuration is incomplete or unsafe."""


@dataclass(frozen=True)
class DevelopmentSeedResult:
    organization_created: bool
    role_created: bool
    permissions_created: int
    user_created: bool
    role_assigned: bool
    permissions_assigned: int
    user: User


class DevelopmentSeedService:
    def __init__(
        self,
        settings: Settings,
        organization_repository: OrganizationRepository,
        permission_repository: PermissionRepository,
        role_repository: RoleRepository,
        user_repository: UserRepository,
    ) -> None:
        self.settings = settings
        self.organization_repository = organization_repository
        self.permission_repository = permission_repository
        self.role_repository = role_repository
        self.user_repository = user_repository

    def seed(self, database_session: Session) -> DevelopmentSeedResult:
        self._validate_configuration()

        organization = self.organization_repository.get_by_id(
            database_session, self.settings.default_organization_id
        )
        organization_created = organization is None
        if organization is None:
            organization = self.organization_repository.create(
                database_session,
                self.settings.default_organization_id,
                self.settings.default_organization_name.strip(),
            )

        role = self.role_repository.get_by_name(
            database_session,
            organization.id,
            DEFAULT_ADMIN_ROLE_NAME,
        )
        role_created = role is None
        if role is None:
            role = self.role_repository.create(
                database_session, organization.id, DEFAULT_ADMIN_ROLE_NAME
            )

        permissions, permissions_created = self.permission_repository.ensure_catalog(
            database_session, PERMISSION_CATALOG
        )
        assigned_permission_names = {
            permission.name for permission in role.permissions
        }
        missing_permissions = [
            permission
            for permission in permissions
            if (
                permission.name in DEFAULT_ADMIN_PERMISSION_NAMES
                and permission.name not in assigned_permission_names
            )
        ]
        role.permissions.extend(missing_permissions)

        admin_email = str(self.settings.default_admin_email).lower()
        user = self.user_repository.get_by_email(
            database_session, admin_email, organization.id
        )
        user_created = user is None
        if user is None:
            user = self.user_repository.create(
                database_session,
                UserCreate(
                    organization_id=organization.id,
                    email=admin_email,
                    password_hash=hash_password(
                        self.settings.default_admin_password.get_secret_value()
                    ),
                    first_name=self.settings.default_admin_first_name.strip(),
                    last_name=self.settings.default_admin_last_name.strip(),
                ),
            )

        role_assigned = role not in user.roles
        if role_assigned:
            user.roles.append(role)

        database_session.commit()
        return DevelopmentSeedResult(
            organization_created=organization_created,
            role_created=role_created,
            permissions_created=permissions_created,
            user_created=user_created,
            role_assigned=role_assigned,
            permissions_assigned=len(missing_permissions),
            user=user,
        )

    def _validate_configuration(self) -> None:
        if self.settings.environment != "development":
            raise DevelopmentSeedConfigurationError(
                "Development seeding is only permitted when ENVIRONMENT=development"
            )

        required_values = {
            "DEFAULT_ADMIN_EMAIL": self.settings.default_admin_email,
            "DEFAULT_ADMIN_PASSWORD": self.settings.default_admin_password,
            "DEFAULT_ADMIN_FIRST_NAME": self.settings.default_admin_first_name,
            "DEFAULT_ADMIN_LAST_NAME": self.settings.default_admin_last_name,
        }
        missing = [name for name, value in required_values.items() if value is None]
        if missing:
            raise DevelopmentSeedConfigurationError(
                f"Missing required development seed variables: {', '.join(missing)}"
            )

        if len(self.settings.default_admin_password.get_secret_value()) < 12:
            raise DevelopmentSeedConfigurationError(
                "DEFAULT_ADMIN_PASSWORD must be at least 12 characters long"
            )
        if not self.settings.default_organization_name.strip():
            raise DevelopmentSeedConfigurationError(
                "DEFAULT_ORGANIZATION_NAME must not be blank"
            )
        if not self.settings.default_admin_first_name.strip() or not self.settings.default_admin_last_name.strip():
            raise DevelopmentSeedConfigurationError(
                "Default admin first and last names must not be blank"
            )
