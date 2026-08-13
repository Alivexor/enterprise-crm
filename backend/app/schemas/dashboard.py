from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DashboardMetric(BaseModel):
    label: str
    value: int | Decimal


class DashboardTask(BaseModel):
    id: UUID
    title: str
    priority: str
    due_date: datetime | None


class DashboardActivity(BaseModel):
    id: UUID
    title: str
    type: str
    due_date: datetime | None


class DashboardResponse(BaseModel):
    metrics: list[DashboardMetric]
    open_tasks: list[DashboardTask]
    upcoming_activities: list[DashboardActivity]


class PipelineAnalyticsItem(BaseModel):
    pipeline_id: UUID
    pipeline_name: str
    stage_id: UUID
    stage_name: str
    deal_count: int
    total_value: Decimal


class StatusAnalyticsItem(BaseModel):
    status: str
    count: int
    total_value: Decimal | None = None


class AnalyticsResponse(BaseModel):
    pipeline: list[PipelineAnalyticsItem]
    deals_by_status: list[StatusAnalyticsItem]
    leads_by_status: list[StatusAnalyticsItem]


class OperationalHealthResponse(BaseModel):
    overdue_tasks: int
    tasks_due_today: int
    activities_next_7_days: int
    stale_leads: int
    stale_deals: int
    open_pipeline_value: Decimal
    weighted_pipeline_value: Decimal
    won_deal_value: Decimal
    lead_conversion_rate: Decimal
