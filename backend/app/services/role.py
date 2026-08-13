from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.audit import AuditService, audit_service

SYSTEM_ADMIN_ROLE_NAME = "admin"


class RoleNotFoundError(Exception):
    """Raised when a role is not available within the active organization."""


class RoleConflictError(Exception):
    """Raised when a role name conflicts or a role cannot be deleted."""


class RoleValidationError(Exception):
    """Raised when permissions do not exist in the global permission catalog."""


class RoleService:
    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        audit_service: AuditService,
    ) -> None:
        self.role_repository = role_repository
        self.permission_repository = permission_repository
        self.audit_service = audit_service

    def list_roles(self, database_session: Session, organization_id: UUID) -> list[Role]:
        return self.role_repository.list_by_organization(database_session, organization_id)

    def list_permissions(self, database_session: Session) -> list[Permission]:
        """Return the global permission catalog for authorized role management."""
        return self.permission_repository.list_all(database_session)

    def get_role(
        self, database_session: Session, organization_id: UUID, role_id: UUID
    ) -> Role:
        role = self.role_repository.get_by_id(database_session, organization_id, role_id)
        if role is None:
            raise RoleNotFoundError
        return role

    def create_role(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        role_data: RoleCreate,
    ) -> Role:
        permissions = self._require_permissions(database_session, role_data.permission_ids)
        try:
            role = self.role_repository.create(
                database_session, organization_id, role_data.name
            )
            role.permissions = permissions
            database_session.flush()
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="role.created",
                entity_type="role",
                entity_id=role.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise RoleConflictError from exc
        return self.get_role(database_session, organization_id, role.id)

    def update_role(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        role_id: UUID,
        role_data: RoleUpdate,
    ) -> Role:
        role = self.get_role(database_session, organization_id, role_id)
        if role.name == SYSTEM_ADMIN_ROLE_NAME:
            raise RoleConflictError
        permissions = None
        if role_data.permission_ids is not None:
            permissions = self._require_permissions(
                database_session, role_data.permission_ids
            )
        try:
            self.role_repository.update(
                database_session,
                role,
                name=role_data.name,
                permissions=permissions,
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="role.updated",
                entity_type="role",
                entity_id=role.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise RoleConflictError from exc
        return self.get_role(database_session, organization_id, role.id)

    def delete_role(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        role_id: UUID,
    ) -> None:
        role = self.get_role(database_session, organization_id, role_id)
        if role.name == SYSTEM_ADMIN_ROLE_NAME or role.users:
            raise RoleConflictError
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="role.deleted",
            entity_type="role",
            entity_id=role.id,
        )
        self.role_repository.delete(database_session, role)
        database_session.commit()

    def _require_permissions(
        self, database_session: Session, permission_ids: list[UUID]
    ) -> list:
        if len(set(permission_ids)) != len(permission_ids):
            raise RoleValidationError
        permissions = self.permission_repository.get_by_ids(
            database_session, permission_ids
        )
        if len(permissions) != len(permission_ids):
            raise RoleValidationError
        return permissions


role_service = RoleService(RoleRepository(), PermissionRepository(), audit_service)
