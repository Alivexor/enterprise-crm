from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Load, Session, selectinload

from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    @staticmethod
    def _with_authorization_data() -> Load:
        return selectinload(User.roles).selectinload(Role.permissions)

    def get_by_id(
        self,
        database_session: Session,
        user_id: UUID,
        organization_id: UUID,
    ) -> User | None:
        statement = (
            select(User)
            .options(self._with_authorization_data())
            .where(User.id == user_id, User.organization_id == organization_id)
        )
        return database_session.scalar(statement)

    def get_by_email(
        self,
        database_session: Session,
        email: str,
        organization_id: UUID,
    ) -> User | None:
        normalized_email = email.strip().lower()
        statement = (
            select(User)
            .options(self._with_authorization_data())
            .where(
                User.organization_id == organization_id,
                func.lower(User.email) == normalized_email,
            )
        )
        return database_session.scalar(statement)

    def exists_by_email(
        self,
        database_session: Session,
        email: str,
        organization_id: UUID,
    ) -> bool:
        normalized_email = email.strip().lower()
        statement = select(
            select(User.id)
            .where(
                User.organization_id == organization_id,
                func.lower(User.email) == normalized_email,
            )
            .exists()
        )
        return bool(database_session.scalar(statement))

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        is_active: bool | None,
    ) -> tuple[list[User], int]:
        where_clauses = [User.organization_id == organization_id]
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(
                or_(
                    func.lower(User.email).like(pattern),
                    func.lower(User.first_name).like(pattern),
                    func.lower(User.last_name).like(pattern),
                )
            )
        if is_active is not None:
            where_clauses.append(User.is_active == is_active)

        statement = (
            select(User)
            .options(self._with_authorization_data())
            .where(*where_clauses)
            .order_by(User.last_name.asc(), User.first_name.asc(), User.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(User.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def create(self, database_session: Session, user_data: UserCreate) -> User:
        user = User(**user_data.model_dump())
        database_session.add(user)
        database_session.flush()
        return user

    def update(
        self,
        database_session: Session,
        user: User,
        *,
        email: str | None = None,
        password_hash: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_active: bool | None = None,
    ) -> User:
        changes: dict[str, str | bool | None] = {
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": is_active,
        }
        for field_name, value in changes.items():
            if value is not None:
                setattr(user, field_name, value)
        database_session.flush()
        return user
