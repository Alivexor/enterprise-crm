from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.security.permission_catalog import PermissionDefinition


class PermissionRepository:
    """Database access for the global permission catalog."""

    def get_by_names(
        self, database_session: Session, names: Iterable[str]
    ) -> list[Permission]:
        requested_names = tuple(dict.fromkeys(names))
        if not requested_names:
            return []

        statement = select(Permission).where(Permission.name.in_(requested_names))
        return list(database_session.scalars(statement))

    def get_by_ids(
        self, database_session: Session, permission_ids: list[UUID]
    ) -> list[Permission]:
        if not permission_ids:
            return []
        statement = select(Permission).where(Permission.id.in_(permission_ids))
        permissions_by_id = {
            permission.id: permission for permission in database_session.scalars(statement)
        }
        return [
            permissions_by_id[permission_id]
            for permission_id in permission_ids
            if permission_id in permissions_by_id
        ]

    def list_all(self, database_session: Session) -> list[Permission]:
        statement = select(Permission).order_by(Permission.name.asc())
        return list(database_session.scalars(statement))

    def ensure_catalog(
        self,
        database_session: Session,
        definitions: Iterable[PermissionDefinition],
    ) -> tuple[list[Permission], int]:
        """Create missing catalog rows and return all requested permissions."""
        catalog = tuple(definitions)
        existing_permissions = {
            permission.name: permission
            for permission in self.get_by_names(
                database_session,
                (definition.name.value for definition in catalog),
            )
        }
        created_count = 0

        for definition in catalog:
            permission = existing_permissions.get(definition.name.value)
            if permission is None:
                permission = Permission(
                    name=definition.name.value,
                    description=definition.description,
                )
                database_session.add(permission)
                existing_permissions[permission.name] = permission
                created_count += 1
            elif permission.description != definition.description:
                permission.description = definition.description

        database_session.flush()
        return (
            [existing_permissions[definition.name.value] for definition in catalog],
            created_count,
        )
