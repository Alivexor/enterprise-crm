from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.permission import Permission
from app.models.role import Role


class RoleRepository:
    @staticmethod
    def _with_permissions():
        return selectinload(Role.permissions)

    def get_by_id(
        self, database_session: Session, organization_id: UUID, role_id: UUID
    ) -> Role | None:
        statement = (
            select(Role)
            .options(self._with_permissions())
            .where(Role.id == role_id, Role.organization_id == organization_id)
        )
        return database_session.scalar(statement)

    def get_by_name(
        self,
        database_session: Session,
        organization_id: UUID,
        name: str,
    ) -> Role | None:
        statement = (
            select(Role)
            .options(self._with_permissions())
            .where(
                Role.organization_id == organization_id,
                Role.name == name,
            )
        )
        return database_session.scalar(statement)

    def get_by_ids(
        self,
        database_session: Session,
        organization_id: UUID,
        role_ids: list[UUID],
    ) -> list[Role]:
        if not role_ids:
            return []
        statement = (
            select(Role)
            .options(self._with_permissions())
            .where(Role.organization_id == organization_id, Role.id.in_(role_ids))
        )
        roles_by_id = {role.id: role for role in database_session.scalars(statement)}
        return [roles_by_id[role_id] for role_id in role_ids if role_id in roles_by_id]

    def list_by_organization(
        self, database_session: Session, organization_id: UUID
    ) -> list[Role]:
        statement = (
            select(Role)
            .options(self._with_permissions())
            .where(Role.organization_id == organization_id)
            .order_by(Role.name.asc(), Role.id.asc())
        )
        return list(database_session.scalars(statement))

    def create(
        self, database_session: Session, organization_id: UUID, name: str
    ) -> Role:
        role = Role(organization_id=organization_id, name=name)
        database_session.add(role)
        database_session.flush()
        return role

    def update(
        self,
        database_session: Session,
        role: Role,
        *,
        name: str | None = None,
        permissions: list[Permission] | None = None,
    ) -> Role:
        if name is not None:
            role.name = name
        if permissions is not None:
            role.permissions = permissions
        database_session.flush()
        return role

    def delete(self, database_session: Session, role: Role) -> None:
        database_session.delete(role)
        database_session.flush()
