from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository


class AuditService:
    """Record audit events within the caller's active database transaction."""

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self.audit_log_repository = audit_log_repository

    def record(
        self,
        database_session: Session,
        *,
        actor_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
    ) -> AuditLog:
        return self.audit_log_repository.create(
            database_session,
            user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )

    def list_entries(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        action: str | None,
        entity_type: str | None,
        user_id: UUID | None,
        created_after: datetime | None,
        created_before: datetime | None,
        sort_direction: str,
    ) -> tuple[list[AuditLog], int]:
        """List organization-scoped events through the service layer."""
        return self.audit_log_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            created_after=created_after,
            created_before=created_before,
            sort_direction=sort_direction,
        )


audit_service = AuditService(AuditLogRepository())
