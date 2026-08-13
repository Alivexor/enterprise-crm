from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.models.task import Task


class DashboardRepository:
    def get_metrics(self, database_session: Session, organization_id: UUID) -> dict[str, int | Decimal]:
        contact_count_statement = (
            select(func.count(Contact.id))
            .join(Contact.company)
            .where(Company.organization_id == organization_id)
        )
        return {
            "companies": int(
                database_session.scalar(
                    select(func.count(Company.id)).where(
                        Company.organization_id == organization_id
                    )
                )
                or 0
            ),
            "contacts": int(database_session.scalar(contact_count_statement) or 0),
            "open_leads": int(
                database_session.scalar(
                    select(func.count(Lead.id)).where(
                        Lead.organization_id == organization_id,
                        Lead.status.not_in(("converted", "lost")),
                    )
                )
                or 0
            ),
            "open_deal_value": database_session.scalar(
                select(func.coalesce(func.sum(Deal.value), 0)).where(
                    Deal.organization_id == organization_id,
                    Deal.status.not_in(("won", "lost")),
                )
            )
            or Decimal("0"),
        }

    def list_open_tasks(
        self, database_session: Session, organization_id: UUID, *, limit: int
    ) -> list[Task]:
        statement = (
            select(Task)
            .where(
                Task.organization_id == organization_id,
                Task.status.not_in(("completed", "cancelled")),
            )
            .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def list_upcoming_activities(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        now: datetime,
        limit: int,
    ) -> list[Activity]:
        statement = (
            select(Activity)
            .where(
                Activity.organization_id == organization_id,
                Activity.completed.is_(False),
                Activity.due_date.is_not(None),
                Activity.due_date >= now,
            )
            .order_by(Activity.due_date.asc(), Activity.created_at.desc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def operational_health(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        now: datetime,
    ) -> dict[str, int | Decimal]:
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        week_end = now + timedelta(days=7)
        stale_lead_before = now - timedelta(days=14)
        stale_deal_before = now - timedelta(days=30)
        open_deal_clause = Deal.status.not_in(("won", "lost"))
        open_lead_clause = Lead.status.not_in(("converted", "lost"))

        overdue_tasks = int(database_session.scalar(
            select(func.count(Task.id)).where(
                Task.organization_id == organization_id,
                Task.status.not_in(("completed", "cancelled")),
                Task.due_date.is_not(None),
                Task.due_date < now,
            )
        ) or 0)
        tasks_due_today = int(database_session.scalar(
            select(func.count(Task.id)).where(
                Task.organization_id == organization_id,
                Task.status.not_in(("completed", "cancelled")),
                Task.due_date >= day_start,
                Task.due_date < day_end,
            )
        ) or 0)
        activities_next_7_days = int(database_session.scalar(
            select(func.count(Activity.id)).where(
                Activity.organization_id == organization_id,
                Activity.completed.is_(False),
                Activity.due_date >= now,
                Activity.due_date < week_end,
            )
        ) or 0)
        stale_leads = int(database_session.scalar(
            select(func.count(Lead.id)).where(
                Lead.organization_id == organization_id,
                open_lead_clause,
                Lead.updated_at < stale_lead_before,
            )
        ) or 0)
        stale_deals = int(database_session.scalar(
            select(func.count(Deal.id)).where(
                Deal.organization_id == organization_id,
                open_deal_clause,
                Deal.updated_at < stale_deal_before,
            )
        ) or 0)
        open_pipeline_value = database_session.scalar(
            select(func.coalesce(func.sum(Deal.value), 0)).where(
                Deal.organization_id == organization_id, open_deal_clause
            )
        ) or Decimal("0")
        weighted_pipeline_value = database_session.scalar(
            select(func.coalesce(func.sum(Deal.value * Deal.probability / 100), 0)).where(
                Deal.organization_id == organization_id, open_deal_clause
            )
        ) or Decimal("0")
        won_deal_value = database_session.scalar(
            select(func.coalesce(func.sum(Deal.value), 0)).where(
                Deal.organization_id == organization_id, Deal.status == "won"
            )
        ) or Decimal("0")
        total_leads = int(database_session.scalar(
            select(func.count(Lead.id)).where(Lead.organization_id == organization_id)
        ) or 0)
        converted_leads = int(database_session.scalar(
            select(func.count(Lead.id)).where(
                Lead.organization_id == organization_id, Lead.status == "converted"
            )
        ) or 0)
        lead_conversion_rate = (
            (Decimal(converted_leads) * Decimal("100") / Decimal(total_leads))
            if total_leads
            else Decimal("0")
        )
        return {
            "overdue_tasks": overdue_tasks,
            "tasks_due_today": tasks_due_today,
            "activities_next_7_days": activities_next_7_days,
            "stale_leads": stale_leads,
            "stale_deals": stale_deals,
            "open_pipeline_value": open_pipeline_value,
            "weighted_pipeline_value": weighted_pipeline_value,
            "won_deal_value": won_deal_value,
            "lead_conversion_rate": lead_conversion_rate,
        }

    def pipeline_analytics(
        self, database_session: Session, organization_id: UUID
    ) -> list[tuple[UUID, str, UUID, str, int, Decimal]]:
        statement = (
            select(
                Pipeline.id,
                Pipeline.name,
                PipelineStage.id,
                PipelineStage.name,
                func.count(Deal.id),
                func.coalesce(func.sum(Deal.value), 0),
            )
            .join(Pipeline.stages)
            .outerjoin(
                Deal,
                and_(
                    Deal.stage_id == PipelineStage.id,
                    Deal.organization_id == organization_id,
                ),
            )
            .where(Pipeline.organization_id == organization_id)
            .group_by(Pipeline.id, Pipeline.name, PipelineStage.id, PipelineStage.name)
            .order_by(Pipeline.name.asc(), PipelineStage.order.asc())
        )
        return list(database_session.execute(statement).all())

    def deal_status_analytics(
        self, database_session: Session, organization_id: UUID
    ) -> list[tuple[str, int, Decimal]]:
        statement = (
            select(Deal.status, func.count(Deal.id), func.coalesce(func.sum(Deal.value), 0))
            .where(Deal.organization_id == organization_id)
            .group_by(Deal.status)
            .order_by(Deal.status.asc())
        )
        return list(database_session.execute(statement).all())

    def lead_status_analytics(
        self, database_session: Session, organization_id: UUID
    ) -> list[tuple[str, int]]:
        statement = (
            select(Lead.status, func.count(Lead.id))
            .where(Lead.organization_id == organization_id)
            .group_by(Lead.status)
            .order_by(Lead.status.asc())
        )
        return list(database_session.execute(statement).all())
