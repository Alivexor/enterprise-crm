from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate


class NotificationRepository:
    """Persistence operations for recipient-scoped notifications."""

    def create(
        self,
        database_session: Session,
        organization_id: UUID,
        notification_data: NotificationCreate,
    ) -> Notification:
        notification = Notification(
            organization_id=organization_id,
            **notification_data.model_dump(),
        )
        database_session.add(notification)
        database_session.flush()
        return notification

    def list_by_user(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        page: int,
        page_size: int,
        read_state: str,
    ) -> tuple[list[Notification], int]:
        where_clauses = [
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
        ]
        if read_state == "read":
            where_clauses.append(Notification.read_at.is_not(None))
        elif read_state == "unread":
            where_clauses.append(Notification.read_at.is_(None))
        statement = (
            select(Notification)
            .where(*where_clauses)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Notification.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def get_by_id_for_user(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification | None:
        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
        )
        return database_session.scalar(statement)

    def mark_read(self, database_session: Session, notification: Notification) -> Notification:
        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            database_session.flush()
        return notification

    def mark_many_read(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        notification_ids: list[UUID],
    ) -> int:
        if not notification_ids:
            return 0
        result = database_session.execute(
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
        )
        return int(result.rowcount or 0)

    def mark_all_read(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> int:
        result = database_session.execute(
            update(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
        )
        return int(result.rowcount or 0)
