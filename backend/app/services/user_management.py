from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.schemas.user_management import (
    ManagedUserCreate,
    ManagedUserUpdate,
    PasswordChange,
    ProfileUpdate,
)
from app.security.password import hash_password, verify_password
from app.services.audit import AuditService, audit_service
from app.services.auth import AuthenticationError, AuthenticationService, auth_service


class ManagedUserNotFoundError(Exception):
    """Raised when a user is unavailable within the active organization."""


class ManagedUserConflictError(Exception):
    """Raised when a user violates a managed-user business rule."""


class ManagedUserValidationError(Exception):
    """Raised when supplied roles are not valid within the organization."""


class UserManagementService:
    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        audit_service: AuditService,
        authentication_service: AuthenticationService,
    ) -> None:
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.audit_service = audit_service
        self.authentication_service = authentication_service

    def list_users(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        is_active: bool | None,
    ) -> tuple[list[User], int]:
        return self.user_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            is_active=is_active,
        )

    def get_user(
        self, database_session: Session, *, organization_id: UUID, user_id: UUID
    ) -> User:
        user = self.user_repository.get_by_id(database_session, user_id, organization_id)
        if user is None:
            raise ManagedUserNotFoundError
        return user

    def create_user(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        user_data: ManagedUserCreate,
    ) -> User:
        normalized_email = str(user_data.email).lower()
        if self.user_repository.exists_by_email(
            database_session, normalized_email, organization_id
        ):
            raise ManagedUserConflictError
        roles = self._require_roles(database_session, organization_id, user_data.role_ids)
        try:
            user = self.user_repository.create(
                database_session,
                UserCreate(
                    organization_id=organization_id,
                    email=normalized_email,
                    password_hash=hash_password(user_data.password),
                    first_name=user_data.first_name,
                    last_name=user_data.last_name,
                ),
            )
            user.roles = roles
            database_session.flush()
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="user.created",
                entity_type="user",
                entity_id=user.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise ManagedUserConflictError from exc
        return self.get_user(
            database_session, organization_id=organization_id, user_id=user.id
        )

    def update_user(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        user_id: UUID,
        user_data: ManagedUserUpdate,
    ) -> User:
        if user_id == actor_id and (
            user_data.is_active is not None or user_data.role_ids is not None
        ):
            raise ManagedUserConflictError
        user = self.get_user(
            database_session, organization_id=organization_id, user_id=user_id
        )
        data = user_data.model_dump(exclude_unset=True)
        roles = None
        if "role_ids" in data:
            role_ids = data.pop("role_ids")
            if not isinstance(role_ids, list):
                raise ManagedUserValidationError
            roles = self._require_roles(database_session, organization_id, role_ids)
        email = data.get("email")
        if isinstance(email, str):
            normalized_email = email.lower()
            existing_user = self.user_repository.get_by_email(
                database_session, normalized_email, organization_id
            )
            if existing_user is not None and existing_user.id != user.id:
                raise ManagedUserConflictError
            data["email"] = normalized_email
        try:
            self.user_repository.update(database_session, user, **data)
            if roles is not None:
                user.roles = roles
                database_session.flush()
            if data.get("is_active") is False:
                self.authentication_service.revoke_user_refresh_sessions(
                    database_session,
                    organization_id=organization_id,
                    user_id=user.id,
                )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="user.updated",
                entity_type="user",
                entity_id=user.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise ManagedUserConflictError from exc
        return self.get_user(
            database_session, organization_id=organization_id, user_id=user.id
        )

    def update_profile(
        self,
        database_session: Session,
        *,
        current_user: User,
        profile_data: ProfileUpdate,
    ) -> User:
        data = profile_data.model_dump(exclude_unset=True)
        email = data.get("email")
        if isinstance(email, str):
            normalized_email = email.lower()
            existing_user = self.user_repository.get_by_email(
                database_session, normalized_email, current_user.organization_id
            )
            if existing_user is not None and existing_user.id != current_user.id:
                raise ManagedUserConflictError
            data["email"] = normalized_email
        try:
            self.user_repository.update(database_session, current_user, **data)
            self.audit_service.record(
                database_session,
                actor_id=current_user.id,
                action="profile.updated",
                entity_type="user",
                entity_id=current_user.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise ManagedUserConflictError from exc
        return self.get_user(
            database_session,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
        )

    def change_password(
        self,
        database_session: Session,
        *,
        current_user: User,
        password_data: PasswordChange,
    ) -> None:
        valid, _ = verify_password(
            password_data.current_password, current_user.password_hash
        )
        if not valid:
            raise AuthenticationError
        self.user_repository.update(
            database_session,
            current_user,
            password_hash=hash_password(password_data.new_password),
        )
        self.authentication_service.revoke_user_refresh_sessions(
            database_session,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
        )
        self.audit_service.record(
            database_session,
            actor_id=current_user.id,
            action="profile.password_changed",
            entity_type="user",
            entity_id=current_user.id,
        )
        database_session.commit()

    def response(self, user: User) -> UserResponse:
        return self.authentication_service.get_user_response(user)

    def _require_roles(
        self, database_session: Session, organization_id: UUID, role_ids: list[UUID]
    ) -> list:
        if len(set(role_ids)) != len(role_ids):
            raise ManagedUserValidationError
        roles = self.role_repository.get_by_ids(
            database_session, organization_id, role_ids
        )
        if len(roles) != len(role_ids):
            raise ManagedUserValidationError
        return roles


user_management_service = UserManagementService(
    UserRepository(), RoleRepository(), audit_service, auth_service
)
