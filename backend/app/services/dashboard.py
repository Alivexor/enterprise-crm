from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import (
    AnalyticsResponse,
    DashboardActivity,
    DashboardMetric,
    DashboardResponse,
    DashboardTask,
    OperationalHealthResponse,
    PipelineAnalyticsItem,
    StatusAnalyticsItem,
)


class DashboardService:
    def __init__(self, dashboard_repository: DashboardRepository) -> None:
        self.dashboard_repository = dashboard_repository

    def get_dashboard(
        self, database_session: Session, organization_id: UUID
    ) -> DashboardResponse:
        metrics = self.dashboard_repository.get_metrics(database_session, organization_id)
        tasks = self.dashboard_repository.list_open_tasks(
            database_session, organization_id, limit=8
        )
        activities = self.dashboard_repository.list_upcoming_activities(
            database_session,
            organization_id,
            now=datetime.now(timezone.utc),
            limit=8,
        )
        return DashboardResponse(
            metrics=[
                DashboardMetric(label="Companies", value=metrics["companies"]),
                DashboardMetric(label="Contacts", value=metrics["contacts"]),
                DashboardMetric(label="Open leads", value=metrics["open_leads"]),
                DashboardMetric(
                    label="Open deal value", value=metrics["open_deal_value"]
                ),
            ],
            open_tasks=[
                DashboardTask(
                    id=task.id,
                    title=task.title,
                    priority=task.priority,
                    due_date=task.due_date,
                )
                for task in tasks
            ],
            upcoming_activities=[
                DashboardActivity(
                    id=activity.id,
                    title=activity.title,
                    type=activity.type,
                    due_date=activity.due_date,
                )
                for activity in activities
            ],
        )

    def get_operational_health(
        self, database_session: Session, organization_id: UUID
    ) -> OperationalHealthResponse:
        values = self.dashboard_repository.operational_health(
            database_session, organization_id, now=datetime.now(timezone.utc)
        )
        return OperationalHealthResponse(**values)

    def get_analytics(
        self, database_session: Session, organization_id: UUID
    ) -> AnalyticsResponse:
        pipeline_rows = self.dashboard_repository.pipeline_analytics(
            database_session, organization_id
        )
        deal_status_rows = self.dashboard_repository.deal_status_analytics(
            database_session, organization_id
        )
        lead_status_rows = self.dashboard_repository.lead_status_analytics(
            database_session, organization_id
        )
        return AnalyticsResponse(
            pipeline=[
                PipelineAnalyticsItem(
                    pipeline_id=pipeline_id,
                    pipeline_name=pipeline_name,
                    stage_id=stage_id,
                    stage_name=stage_name,
                    deal_count=deal_count,
                    total_value=total_value,
                )
                for (
                    pipeline_id,
                    pipeline_name,
                    stage_id,
                    stage_name,
                    deal_count,
                    total_value,
                ) in pipeline_rows
            ],
            deals_by_status=[
                StatusAnalyticsItem(
                    status=status, count=count, total_value=total_value
                )
                for status, count, total_value in deal_status_rows
            ],
            leads_by_status=[
                StatusAnalyticsItem(status=status, count=count)
                for status, count in lead_status_rows
            ],
        )


dashboard_service = DashboardService(DashboardRepository())
