"""Persistence operations for organization-scoped CRM deals."""

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.deal import Deal
from app.schemas.deal import DealCreate, DealUpdate


class DealRepository:
    """Database access for deals; relationship validation belongs in the service."""

    def create(
        self,
        database_session: Session,
        organization_id: UUID,
        deal_data: DealCreate,
    ) -> Deal:
        deal = Deal(organization_id=organization_id, **deal_data.model_dump())
        database_session.add(deal)
        database_session.flush()
        return deal

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
        pipeline_id: UUID | None,
        stage_id: UUID | None,
        assigned_user_id: UUID | None,
        status: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Deal], int]:
        where_clauses = [Deal.organization_id == organization_id]
        if search:
            where_clauses.append(func.lower(Deal.title).like(f"%{search.lower()}%"))
        if company_id is not None:
            where_clauses.append(Deal.company_id == company_id)
        if contact_id is not None:
            where_clauses.append(Deal.contact_id == contact_id)
        if pipeline_id is not None:
            where_clauses.append(Deal.pipeline_id == pipeline_id)
        if stage_id is not None:
            where_clauses.append(Deal.stage_id == stage_id)
        if assigned_user_id is not None:
            where_clauses.append(Deal.assigned_user_id == assigned_user_id)
        if status is not None:
            where_clauses.append(Deal.status == status)

        ordering = {
            "title": Deal.title,
            "value": Deal.value,
            "probability": Deal.probability,
            "expected_close_date": Deal.expected_close_date,
            "created_at": Deal.created_at,
            "updated_at": Deal.updated_at,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement: Select[tuple[Deal]] = (
            select(Deal)
            .where(*where_clauses)
            .order_by(order_expression, Deal.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Deal.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def get_by_id(
        self,
        database_session: Session,
        deal_id: UUID,
        organization_id: UUID,
    ) -> Deal | None:
        statement = select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == organization_id,
        )
        return database_session.scalar(statement)

    def update(
        self,
        database_session: Session,
        deal: Deal,
        deal_data: DealUpdate,
    ) -> Deal:
        for field_name, value in deal_data.model_dump(exclude_unset=True).items():
            setattr(deal, field_name, value)
        database_session.flush()
        return deal

    def delete(self, database_session: Session, deal: Deal) -> None:
        database_session.delete(deal)
        database_session.flush()
