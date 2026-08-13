from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.refresh_session import RefreshSessionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import PermissionResponse, UserCreate, UserResponse
from app.security.password import hash_password, verify_password
from app.security.totp import decrypt_secret, hash_recovery_code, verify_code
from app.security.tokens import (
    TokenType,
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token_jti,
)


class AuthenticationError(Exception):
    """Raised when credentials or an access token cannot authenticate a user."""


class UserAlreadyExistsError(Exception):
    """Raised when registration would duplicate an organization email."""


class AuthenticationConfigurationError(Exception):
    """Raised when required tenant or default-role data is missing."""


class SelfRegistrationDisabledError(Exception):
    """Raised when public self-registration is disabled by configuration."""


class AuthenticationSessionError(Exception):
    """Raised when a refresh-session mutation cannot be safely persisted."""


class AuthenticationMfaRequiredError(AuthenticationError):
    """Raised when valid primary credentials require a second factor."""


class AuthenticationMfaInvalidError(AuthenticationError):
    """Raised when the supplied second factor is invalid."""


class AuthenticationService:
    def __init__(
        self,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        role_repository: RoleRepository,
        refresh_session_repository: RefreshSessionRepository,
        settings: Settings,
    ) -> None:
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.role_repository = role_repository
        self.refresh_session_repository = refresh_session_repository
        self.settings = settings

    def create_user(
        self, database_session: Session, registration: RegisterRequest
    ) -> User:
        if not self.settings.allow_self_registration:
            raise SelfRegistrationDisabledError

        default_role_name = (
            self.settings.default_role_name.strip()
            if self.settings.default_role_name is not None
            else ""
        )
        if not default_role_name:
            raise AuthenticationConfigurationError

        organization_id = self.settings.default_organization_id
        if not self.organization_repository.exists(database_session, organization_id):
            raise AuthenticationConfigurationError

        normalized_email = str(registration.email).strip().lower()
        if self.user_repository.exists_by_email(
            database_session, normalized_email, organization_id
        ):
            raise UserAlreadyExistsError

        user_data = UserCreate(
            organization_id=organization_id,
            email=normalized_email,
            password_hash=hash_password(registration.password),
            first_name=registration.first_name,
            last_name=registration.last_name,
        )

        try:
            user = self.user_repository.create(database_session, user_data)
            role = self.role_repository.get_by_name(
                database_session,
                organization_id,
                default_role_name,
            )
            if role is None:
                raise AuthenticationConfigurationError
            user.roles.append(role)
            database_session.commit()
        except AuthenticationConfigurationError:
            database_session.rollback()
            raise
        except IntegrityError as exc:
            database_session.rollback()
            raise UserAlreadyExistsError from exc

        created_user = self.user_repository.get_by_id(
            database_session, user.id, organization_id
        )
        if created_user is None:
            raise AuthenticationConfigurationError
        return created_user

    def verify_user_credentials(
        self, database_session: Session, login: LoginRequest
    ) -> User:
        user = self.user_repository.get_by_email(
            database_session,
            str(login.email),
            self.settings.default_organization_id,
        )
        if user is None:
            raise AuthenticationError

        is_valid, replacement_hash = verify_password(login.password, user.password_hash)
        if not is_valid or not user.is_active:
            raise AuthenticationError

        if replacement_hash is not None:
            self.user_repository.update(
                database_session, user, password_hash=replacement_hash
            )
            database_session.commit()
        return user

    def verify_mfa(self, database_session: Session, user: User, code: str | None) -> None:
        if not user.mfa_enabled:
            return
        if not code:
            raise AuthenticationMfaRequiredError
        encrypted = user.mfa_secret_encrypted
        if not encrypted:
            raise AuthenticationMfaInvalidError
        secret = decrypt_secret(encrypted, self.settings.jwt_secret.get_secret_value())
        if verify_code(secret, code):
            return
        digest = hash_recovery_code(code, self.settings.jwt_secret.get_secret_value())
        recovery_hashes = list(user.mfa_recovery_codes or [])
        if digest in recovery_hashes:
            recovery_hashes.remove(digest)
            user.mfa_recovery_codes = recovery_hashes
            database_session.flush()
            return
        raise AuthenticationMfaInvalidError

    def generate_authentication_tokens(
        self, database_session: Session, user: User
    ) -> TokenResponse:
        """Create a new independently revocable refresh-token family on login."""
        try:
            tokens = self._create_authentication_tokens(
                database_session,
                user,
                family_id=uuid4(),
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise AuthenticationSessionError from exc
        return tokens

    def _create_authentication_tokens(
        self,
        database_session: Session,
        user: User,
        *,
        family_id: UUID,
    ) -> TokenResponse:
        refresh_token_jti = uuid4()
        access_token = create_access_token(user.id, user.organization_id, self.settings)
        refresh_token = create_refresh_token(
            user.id,
            user.organization_id,
            self.settings,
            jti=refresh_token_jti,
        )
        refresh_token_payload = decode_token(
            refresh_token,
            TokenType.REFRESH,
            self.settings,
        )
        self.refresh_session_repository.create(
            database_session,
            family_id=family_id,
            organization_id=user.organization_id,
            user_id=user.id,
            token_jti_hash=hash_token_jti(refresh_token_jti),
            expires_at=refresh_token_payload.exp,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.jwt_access_token_expire_minutes * 60,
        )

    def refresh_authentication_tokens(
        self, database_session: Session, refresh_token: str
    ) -> TokenResponse:
        """Issue a fresh access/refresh token pair from a valid refresh token."""
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH, self.settings)
        except TokenValidationError as exc:
            raise AuthenticationError from exc

        if payload.organization_id != self.settings.default_organization_id:
            raise AuthenticationError

        refresh_session = self.refresh_session_repository.get_by_token_jti_hash(
            database_session,
            token_jti_hash=hash_token_jti(payload.jti),
            organization_id=payload.organization_id,
            user_id=payload.sub,
            lock_for_update=True,
        )
        if refresh_session is None:
            raise AuthenticationError

        now = datetime.now(timezone.utc)
        if refresh_session.revoked_at is not None:
            self._revoke_refresh_session_family(
                database_session,
                family_id=refresh_session.family_id,
                organization_id=payload.organization_id,
                user_id=payload.sub,
                revoked_at=now,
            )
            raise AuthenticationError

        if self._is_expired(refresh_session.expires_at, now):
            self.refresh_session_repository.revoke(
                database_session,
                refresh_session,
                revoked_at=now,
            )
            self._commit_refresh_session_mutation(database_session)
            raise AuthenticationError

        user = self.user_repository.get_by_id(
            database_session, payload.sub, payload.organization_id
        )
        if user is None or not user.is_active:
            self._revoke_refresh_session_family(
                database_session,
                family_id=refresh_session.family_id,
                organization_id=payload.organization_id,
                user_id=payload.sub,
                revoked_at=now,
            )
            raise AuthenticationError

        try:
            self.refresh_session_repository.revoke(
                database_session,
                refresh_session,
                revoked_at=now,
            )
            tokens = self._create_authentication_tokens(
                database_session,
                user,
                family_id=refresh_session.family_id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise AuthenticationSessionError from exc
        return tokens

    def logout(self, database_session: Session, refresh_token: str) -> None:
        """Revoke a refresh-token family without revealing token/session validity."""
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH, self.settings)
        except TokenValidationError:
            return

        if payload.organization_id != self.settings.default_organization_id:
            return

        refresh_session = self.refresh_session_repository.get_by_token_jti_hash(
            database_session,
            token_jti_hash=hash_token_jti(payload.jti),
            organization_id=payload.organization_id,
            user_id=payload.sub,
            lock_for_update=True,
        )
        if refresh_session is None:
            return

        self._revoke_refresh_session_family(
            database_session,
            family_id=refresh_session.family_id,
            organization_id=payload.organization_id,
            user_id=payload.sub,
            revoked_at=datetime.now(timezone.utc),
        )

    def revoke_user_refresh_sessions(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> None:
        """Stage revocation for a user-management transaction without committing it."""
        self.refresh_session_repository.revoke_all_for_user(
            database_session,
            organization_id=organization_id,
            user_id=user_id,
            revoked_at=datetime.now(timezone.utc),
        )

    def _revoke_refresh_session_family(
        self,
        database_session: Session,
        *,
        family_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None:
        try:
            self.refresh_session_repository.revoke_family(
                database_session,
                family_id=family_id,
                organization_id=organization_id,
                user_id=user_id,
                revoked_at=revoked_at,
            )
            self._commit_refresh_session_mutation(database_session)
        except IntegrityError as exc:
            database_session.rollback()
            raise AuthenticationSessionError from exc

    @staticmethod
    def _is_expired(expires_at: datetime, now: datetime) -> bool:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= now

    @staticmethod
    def _commit_refresh_session_mutation(database_session: Session) -> None:
        try:
            database_session.commit()
        except Exception as exc:
            database_session.rollback()
            raise AuthenticationSessionError from exc

    def authenticate(
        self, database_session: Session, login: LoginRequest
    ) -> TokenResponse:
        user = self.verify_user_credentials(database_session, login)
        self.verify_mfa(database_session, user, login.mfa_code)
        return self.generate_authentication_tokens(database_session, user)

    def get_current_authenticated_user(
        self, database_session: Session, access_token: str
    ) -> User:
        try:
            payload = decode_token(access_token, TokenType.ACCESS, self.settings)
        except TokenValidationError as exc:
            raise AuthenticationError from exc

        if payload.organization_id != self.settings.default_organization_id:
            raise AuthenticationError

        user = self.user_repository.get_by_id(
            database_session, payload.sub, payload.organization_id
        )
        if user is None or not user.is_active:
            raise AuthenticationError
        return user

    @staticmethod
    def get_user_response(user: User) -> UserResponse:
        """Serialize authorization data without leaking password or token data."""
        permission_by_name = {
            permission.name: permission
            for role in user.roles
            if role.organization_id == user.organization_id
            for permission in role.permissions
        }
        return UserResponse(
            id=user.id,
            organization_id=user.organization_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            mfa_enabled=user.mfa_enabled,
            roles=sorted(
                (
                    role
                    for role in user.roles
                    if role.organization_id == user.organization_id
                ),
                key=lambda role: role.name,
            ),
            permissions=[
                PermissionResponse.model_validate(permission)
                for permission in sorted(
                    permission_by_name.values(), key=lambda permission: permission.name
                )
            ],
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


auth_service = AuthenticationService(
    UserRepository(),
    OrganizationRepository(),
    RoleRepository(),
    RefreshSessionRepository(),
    get_settings(),
)
