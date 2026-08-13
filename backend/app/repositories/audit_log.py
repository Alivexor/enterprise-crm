from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogRepository:
    """Persist and query organization-scoped audit entries."""

    def create(
        self,
        database_session: Session,
        *,
        user_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        database_session.add(entry)
        database_session.flush()
        return entry

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
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
        where_clauses = [User.organization_id == organization_id]
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(
                or_(
                    func.lower(AuditLog.action).like(pattern),
                    func.lower(AuditLog.entity_type).like(pattern),
                    func.lower(User.email).like(pattern),
                )
            )
        if action is not None:
            where_clauses.append(AuditLog.action == action)
        if entity_type is not None:
            where_clauses.append(AuditLog.entity_type == entity_type)
        if user_id is not None:
            where_clauses.append(AuditLog.user_id == user_id)
        if created_after is not None:
            where_clauses.append(AuditLog.created_at >= created_after)
        if created_before is not None:
            where_clauses.append(AuditLog.created_at <= created_before)
        ordering = (
            AuditLog.created_at.asc()
            if sort_direction == "asc"
            else AuditLog.created_at.desc()
        )
        statement = (
            select(AuditLog)
            .join(AuditLog.user)
            .options(joinedload(AuditLog.user))
            .where(*where_clauses)
            .order_by(ordering, AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = (
            select(func.count(AuditLog.id)).join(AuditLog.user).where(*where_clauses)
        )
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )
