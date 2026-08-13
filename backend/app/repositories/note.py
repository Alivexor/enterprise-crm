from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.note import Note


class NoteRepository:
    """Database access for organization-scoped notes."""

    def create(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        data: dict[str, object],
    ) -> Note:
        note = Note(organization_id=organization_id, user_id=user_id, **data)
        database_session.add(note)
        database_session.flush()
        return note

    def get_by_id(
        self,
        database_session: Session,
        organization_id: UUID,
        note_id: UUID,
    ) -> Note | None:
        return database_session.scalar(
            select(Note).where(
                Note.id == note_id,
                Note.organization_id == organization_id,
            )
        )

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        company_id: UUID | None,
        contact_id: UUID | None,
        lead_id: UUID | None,
        user_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Note], int]:
        where_clauses = [Note.organization_id == organization_id]
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(func.lower(Note.content).like(pattern))
        if company_id is not None:
            where_clauses.append(Note.company_id == company_id)
        if contact_id is not None:
            where_clauses.append(Note.contact_id == contact_id)
        if lead_id is not None:
            where_clauses.append(Note.lead_id == lead_id)
        if user_id is not None:
            where_clauses.append(Note.user_id == user_id)

        ordering = {
            "created_at": Note.created_at,
            "updated_at": Note.updated_at,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement = (
            select(Note)
            .where(*where_clauses)
            .order_by(order_expression, Note.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Note.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def update(
        self,
        database_session: Session,
        note: Note,
        data: dict[str, object],
    ) -> Note:
        for field_name, value in data.items():
            setattr(note, field_name, value)
        database_session.flush()
        return note

    def delete(self, database_session: Session, note: Note) -> None:
        database_session.delete(note)
        database_session.flush()
