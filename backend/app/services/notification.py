"""Notification use cases for recipient-owned in-app inboxes."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationCreate
from app.services.audit import AuditService, audit_service
from app.services.references import (
    OrganizationReferenceService,
    ReferenceNotFoundError,
    reference_service,
)


class NotificationNotFoundError(Exception):
    """Raised when a notification is not part of the recipient's inbox."""


class NotificationRecipientNotFoundError(Exception):
    """Raised when an internal notification target is outside the organization."""


class NotificationService:
    def __init__(
        self,
        notification_repository: NotificationRepository,
        reference_service: OrganizationReferenceService,
        audit_service: AuditService,
    ) -> None:
        self.notification_repository = notification_repository
        self.reference_service = reference_service
        self.audit_service = audit_service

    def create_notification(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        notification_data: NotificationCreate,
        commit: bool = True,
    ) -> Notification:
        """Create an in-app notification for use by trusted service workflows.

        This service intentionally has no public create endpoint. Callers can opt out
        of committing so a notification participates in a larger domain transaction.
        """
        try:
            self.reference_service.require_user(
                database_session, organization_id, notification_data.user_id
            )
        except ReferenceNotFoundError as exc:
            raise NotificationRecipientNotFoundError from exc

        try:
            notification = self.notification_repository.create(
                database_session, organization_id, notification_data
            )
            if commit:
                database_session.commit()
            return notification
        except Exception:
            if commit:
                database_session.rollback()
            raise

    def list_notifications(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        page: int,
        page_size: int,
        read_state: str,
    ) -> tuple[list[Notification], int]:
        return self.notification_repository.list_by_user(
            database_session,
            organization_id=organization_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
            read_state=read_state,
        )

    def mark_notification_read(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification:
        notification = self.notification_repository.get_by_id_for_user(
            database_session,
            organization_id=organization_id,
            user_id=user_id,
            notification_id=notification_id,
        )
        if notification is None:
            raise NotificationNotFoundError
        try:
            was_unread = notification.read_at is None
            self.notification_repository.mark_read(database_session, notification)
            if was_unread:
                self.audit_service.record(
                    database_session,
                    actor_id=user_id,
                    action="notification.read",
                    entity_type="notification",
                    entity_id=notification.id,
                )
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return notification

    def mark_notifications_read(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        notification_ids: list[UUID],
    ) -> int:
        try:
            count = self.notification_repository.mark_many_read(
                database_session,
                organization_id=organization_id,
                user_id=user_id,
                notification_ids=notification_ids,
            )
            if count:
                self.audit_service.record(
                    database_session,
                    actor_id=user_id,
                    action="notification.read_bulk",
                    entity_type="notification_inbox",
                    entity_id=user_id,
                )
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return count

    def mark_all_notifications_read(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> int:
        try:
            count = self.notification_repository.mark_all_read(
                database_session,
                organization_id=organization_id,
                user_id=user_id,
            )
            if count:
                self.audit_service.record(
                    database_session,
                    actor_id=user_id,
                    action="notification.read_all",
                    entity_type="notification_inbox",
                    entity_id=user_id,
                )
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return count


notification_service = NotificationService(
    NotificationRepository(), reference_service, audit_service
)
