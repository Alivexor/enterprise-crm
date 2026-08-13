"""Transactional in-app notifications for CRM assignment changes."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.notification import NotificationCreate
from app.services.notification import NotificationService, notification_service


class AssignmentNotificationService:
    """Create recipient notifications without committing the caller's transaction."""

    def __init__(self, notification_service: NotificationService) -> None:
        self.notification_service = notification_service

    def notify_assignee(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        recipient_id: UUID,
        entity_type: str,
        entity_id: UUID,
        title: str,
    ) -> None:
        """Notify a different recipient after a valid assignment is persisted."""
        if recipient_id == actor_id:
            return
        self.notification_service.create_notification(
            database_session,
            organization_id=organization_id,
            notification_data=NotificationCreate(
                user_id=recipient_id,
                type=f"{entity_type}_assigned",
                title=f"You were assigned a {entity_type}",
                body=title,
                entity_type=entity_type,
                entity_id=entity_id,
            ),
            commit=False,
        )


assignment_notification_service = AssignmentNotificationService(notification_service)
