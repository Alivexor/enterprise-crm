from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_session import RefreshSession


class RefreshSessionRepository:
    """Database operations for persisted refresh-token sessions."""

    def create(
        self,
        database_session: Session,
        *,
        family_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        token_jti_hash: str,
        expires_at: datetime,
    ) -> RefreshSession:
        refresh_session = RefreshSession(
            family_id=family_id,
            organization_id=organization_id,
            user_id=user_id,
            token_jti_hash=token_jti_hash,
            expires_at=expires_at,
        )
        database_session.add(refresh_session)
        database_session.flush()
        return refresh_session

    def get_by_token_jti_hash(
        self,
        database_session: Session,
        *,
        token_jti_hash: str,
        organization_id: UUID,
        user_id: UUID,
        lock_for_update: bool = False,
    ) -> RefreshSession | None:
        statement = select(RefreshSession).where(
            RefreshSession.token_jti_hash == token_jti_hash,
            RefreshSession.organization_id == organization_id,
            RefreshSession.user_id == user_id,
        )
        if lock_for_update:
            statement = statement.with_for_update()
        return database_session.scalar(statement)

    @staticmethod
    def revoke(
        database_session: Session,
        refresh_session: RefreshSession,
        *,
        revoked_at: datetime,
    ) -> None:
        if refresh_session.revoked_at is None:
            refresh_session.revoked_at = revoked_at
            database_session.flush()

    @staticmethod
    def revoke_family(
        database_session: Session,
        *,
        family_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None:
        database_session.execute(
            update(RefreshSession)
            .where(
                RefreshSession.family_id == family_id,
                RefreshSession.organization_id == organization_id,
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
            .execution_options(synchronize_session=False)
        )
        database_session.flush()

    @staticmethod
    def revoke_all_for_user(
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None:
        """Revoke every active refresh session owned by one organization user."""
        database_session.execute(
            update(RefreshSession)
            .where(
                RefreshSession.organization_id == organization_id,
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
            .execution_options(synchronize_session=False)
        )
        database_session.flush()
