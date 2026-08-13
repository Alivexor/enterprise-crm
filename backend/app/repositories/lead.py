from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.lead import Lead


class LeadRepository:
    def create(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        assigned_user_id: UUID,
        data: dict[str, object],
    ) -> Lead:
        lead = Lead(
            organization_id=organization_id,
            assigned_user_id=assigned_user_id,
            **data,
        )
        database_session.add(lead)
        database_session.flush()
        return lead

    def get_by_id(
        self, database_session: Session, organization_id: UUID, lead_id: UUID
    ) -> Lead | None:
        statement = select(Lead).where(
            Lead.id == lead_id, Lead.organization_id == organization_id
        )
        return database_session.scalar(statement)

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        assigned_user_id: UUID | None,
        company_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Lead], int]:
        where_clauses = [Lead.organization_id == organization_id]
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(
                or_(
                    func.lower(Lead.title).like(pattern),
                    func.lower(Lead.description).like(pattern),
                )
            )
        if status is not None:
            where_clauses.append(Lead.status == status)
        if assigned_user_id is not None:
            where_clauses.append(Lead.assigned_user_id == assigned_user_id)
        if company_id is not None:
            where_clauses.append(Lead.company_id == company_id)

        ordering = {
            "created_at": Lead.created_at,
            "title": Lead.title,
            "status": Lead.status,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement = (
            select(Lead)
            .where(*where_clauses)
            .order_by(order_expression, Lead.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Lead.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def update(
        self, database_session: Session, lead: Lead, data: dict[str, object]
    ) -> Lead:
        for field_name, value in data.items():
            setattr(lead, field_name, value)
        database_session.flush()
        return lead

    def delete(self, database_session: Session, lead: Lead) -> None:
        database_session.delete(lead)
        database_session.flush()
