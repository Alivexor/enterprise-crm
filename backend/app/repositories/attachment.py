from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment


class AttachmentRepository:
    """Persistence operations for organization-scoped attachment metadata."""

    def create(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        uploaded_by_user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        original_filename: str,
        storage_key: str,
        content_type: str,
        size_bytes: int,
    ) -> Attachment:
        attachment = Attachment(
            organization_id=organization_id,
            uploaded_by_user_id=uploaded_by_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            original_filename=original_filename,
            storage_key=storage_key,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        database_session.add(attachment)
        database_session.flush()
        return attachment

    def list_by_entity(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Attachment], int]:
        where_clauses = [
            Attachment.organization_id == organization_id,
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id,
        ]
        statement = (
            select(Attachment)
            .where(*where_clauses)
            .order_by(Attachment.created_at.desc(), Attachment.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Attachment.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def get_by_id(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        attachment_id: UUID,
    ) -> Attachment | None:
        return database_session.scalar(
            select(Attachment).where(
                Attachment.id == attachment_id,
                Attachment.organization_id == organization_id,
            )
        )

    def delete(self, database_session: Session, attachment: Attachment) -> None:
        database_session.delete(attachment)
        database_session.flush()
