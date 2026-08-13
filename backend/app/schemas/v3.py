from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import RequestSchema


SavedViewResource = Literal["companies", "contacts", "leads", "deals", "tasks", "activities"]
CustomEntityType = Literal["company", "contact", "lead", "deal"]
CustomFieldType = Literal[
    "text", "number", "currency", "date", "boolean", "select", "multi_select", "url", "email"
]
WorkflowEntityType = Literal["lead", "deal", "task", "company"]
WorkflowEventType = Literal[
    "manual", "lead.created", "lead.updated", "deal.created", "deal.updated", "task.created", "task.updated"
]
GoalMetric = Literal["won_revenue", "won_deals", "created_leads", "converted_leads", "activities_completed"]
QuoteStatus = Literal["draft", "sent", "approved", "rejected", "expired"]


class SavedViewCreate(RequestSchema):
    name: str = Field(min_length=1, max_length=120)
    resource: SavedViewResource
    filters: dict[str, Any] = Field(default_factory=dict)
    sort_by: str | None = Field(default=None, max_length=64)
    sort_direction: Literal["asc", "desc"] = "desc"
    is_shared: bool = False


class SavedViewUpdate(RequestSchema):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    filters: dict[str, Any] | None = None
    sort_by: str | None = Field(default=None, max_length=64)
    sort_direction: Literal["asc", "desc"] | None = None
    is_shared: bool | None = None


class SavedViewResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    resource: str
    filters: dict[str, Any]
    sort_by: str | None
    sort_direction: str
    is_shared: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomFieldDefinitionCreate(RequestSchema):
    entity_type: CustomEntityType
    field_key: str = Field(pattern=r"^[a-z][a-z0-9_]{1,62}[a-z0-9]$", max_length=64)
    label: str = Field(min_length=1, max_length=120)
    data_type: CustomFieldType
    required: bool = False
    options: list[str] | None = None
    position: int = Field(default=0, ge=0, le=1000)

    @model_validator(mode="after")
    def validate_options(self):
        if self.data_type in {"select", "multi_select"}:
            if not self.options or len(self.options) > 100:
                raise ValueError("Select fields require between 1 and 100 options")
        elif self.options:
            raise ValueError("Options are only allowed for select fields")
        return self


class CustomFieldDefinitionUpdate(RequestSchema):
    label: str | None = Field(default=None, min_length=1, max_length=120)
    required: bool | None = None
    options: list[str] | None = None
    position: int | None = Field(default=None, ge=0, le=1000)
    is_active: bool | None = None


class CustomFieldDefinitionResponse(BaseModel):
    id: UUID
    entity_type: str
    field_key: str
    label: str
    data_type: str
    required: bool
    options: list[str] | None
    position: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomFieldValuesUpdate(RequestSchema):
    values: dict[str, Any]


class CustomFieldValuesResponse(BaseModel):
    entity_type: str
    entity_id: UUID
    values: dict[str, Any]


class WorkflowCondition(RequestSchema):
    field: str = Field(min_length=1, max_length=80)
    operator: Literal["eq", "neq", "contains", "gt", "gte", "lt", "lte", "in", "is_empty", "not_empty"]
    value: Any = None


class WorkflowAction(RequestSchema):
    type: Literal["create_task", "notify_user", "set_field"]
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowCreate(RequestSchema):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    entity_type: WorkflowEntityType
    event_type: WorkflowEventType
    conditions: list[WorkflowCondition] = Field(default_factory=list, max_length=20)
    actions: list[WorkflowAction] = Field(min_length=1, max_length=20)
    is_active: bool = True


class WorkflowUpdate(RequestSchema):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    conditions: list[WorkflowCondition] | None = Field(default=None, max_length=20)
    actions: list[WorkflowAction] | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    entity_type: str
    event_type: str
    conditions: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    is_active: bool
    run_count: int
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowRunRequest(RequestSchema):
    entity_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    status: str
    event_type: str
    entity_id: UUID | None
    output_payload: dict[str, Any]
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SalesGoalCreate(RequestSchema):
    user_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    metric: GoalMetric
    target_value: Decimal = Field(gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_period(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.metric == "won_revenue" and self.currency is None:
            raise ValueError("currency is required for revenue goals")
        return self


class SalesGoalResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    name: str
    metric: str
    target_value: Decimal
    currency: str | None
    start_date: date
    end_date: date
    current_value: Decimal = Decimal("0")
    progress_percent: Decimal = Decimal("0")
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductCreate(RequestSchema):
    name: str = Field(min_length=1, max_length=180)
    sku: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=3000)
    unit_price: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    is_active: bool = True


class ProductUpdate(RequestSchema):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=3000)
    unit_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    sku: str
    description: str | None
    unit_price: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuoteItemInput(RequestSchema):
    product_id: UUID | None = None
    description: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class QuoteCreate(RequestSchema):
    deal_id: UUID | None = None
    company_id: UUID
    contact_id: UUID | None = None
    quote_number: str = Field(min_length=1, max_length=60)
    status: QuoteStatus = "draft"
    currency: str = Field(min_length=3, max_length=3)
    discount_percent: Decimal = Field(default=0, ge=0, le=100)
    tax_percent: Decimal = Field(default=0, ge=0, le=100)
    valid_until: date | None = None
    notes: str | None = Field(default=None, max_length=5000)
    items: list[QuoteItemInput] = Field(min_length=1, max_length=100)


class QuoteItemResponse(BaseModel):
    id: UUID
    product_id: UUID | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class QuoteResponse(BaseModel):
    id: UUID
    deal_id: UUID | None
    company_id: UUID
    contact_id: UUID | None
    owner_user_id: UUID
    quote_number: str
    status: str
    currency: str
    discount_percent: Decimal
    tax_percent: Decimal
    valid_until: date | None
    notes: str | None
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    approval_note: str | None
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    items: list[QuoteItemResponse]
    created_at: datetime
    updated_at: datetime


class DataQualityIssue(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    title: str
    count: int
    resource: str
    sample_ids: list[UUID] = Field(default_factory=list)


class DataQualityResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    total_issues: int
    issues: list[DataQualityIssue]


class ForecastBucket(BaseModel):
    label: str
    deal_count: int
    total_value: Decimal
    weighted_value: Decimal


class CurrencyForecast(BaseModel):
    currency: str
    open_pipeline: Decimal
    weighted_pipeline: Decimal
    won_revenue: Decimal
    commit: Decimal
    best_case: Decimal


class RevenueForecastResponse(BaseModel):
    currency: str | None
    open_pipeline: Decimal
    weighted_pipeline: Decimal
    won_revenue: Decimal
    commit: Decimal
    best_case: Decimal
    pipeline: Decimal
    buckets: list[ForecastBucket]
    currency_breakdown: list[CurrencyForecast] = Field(default_factory=list)


class ReportRow(BaseModel):
    label: str
    value: Decimal
    count: int


class ReportBuilderResponse(BaseModel):
    resource: str
    metric: str
    group_by: str
    rows: list[ReportRow]
    total: Decimal


class RelationshipHealthResponse(BaseModel):
    company_id: UUID
    score: int = Field(ge=0, le=100)
    label: str
    last_activity_at: datetime | None
    activities_30d: int
    open_deals: int
    open_deal_value: Decimal
    overdue_tasks: int
    factors: list[str]


class AiModelResponse(BaseModel):
    name: str
    size_bytes: int | None = None
    installed: bool
    recommended: bool = False


class AiStatusResponse(BaseModel):
    available: bool
    ollama_reachable: bool
    configured_model_available: bool
    base_url: str
    model: str
    detail: str
    installed_models: list[AiModelResponse] = Field(default_factory=list)
    recommended_models: list[AiModelResponse] = Field(default_factory=list)
    setup_steps: list[str] = Field(default_factory=list)


class AiCopilotRequest(RequestSchema):
    prompt: str = Field(min_length=2, max_length=4000)
    locale: Literal["en", "fa"] = "en"
    model: str | None = Field(default=None, max_length=200)


class AiModelPullRequest(RequestSchema):
    model: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$")


class AiCopilotResponse(BaseModel):
    answer: str
    model: str
    context_summary: dict[str, Any]


class AiDealInsightResponse(BaseModel):
    deal_id: UUID
    summary: str
    risk_level: Literal["low", "medium", "high"]
    risk_reasons: list[str]
    next_actions: list[str]
    model: str


class ApiKeyCreate(RequestSchema):
    name: str = Field(min_length=1, max_length=120)
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(ApiKeyResponse):
    token: str


class WebhookCreate(RequestSchema):
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=8, max_length=2048)
    events: list[str] = Field(min_length=1, max_length=50)
    is_active: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        return value


class WebhookResponse(BaseModel):
    id: UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookCreatedResponse(WebhookResponse):
    signing_secret: str

# ---------------------- V3 zero-cost productivity ----------------------

class DashboardWidgetCreate(RequestSchema):
    title: str = Field(min_length=1, max_length=120)
    widget_type: Literal["report", "forecast", "data_quality", "goal"]
    config: dict[str, Any] = Field(default_factory=dict)
    position: int = Field(default=0, ge=0, le=200)


class DashboardWidgetUpdate(RequestSchema):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    config: dict[str, Any] | None = None
    position: int | None = Field(default=None, ge=0, le=200)


class DashboardWidgetResponse(BaseModel):
    id: UUID
    title: str
    widget_type: str
    config: dict[str, Any]
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SequenceStepInput(RequestSchema):
    delay_days: int = Field(default=0, ge=0, le=3650)
    action_type: Literal["create_task", "notify_owner"]
    config: dict[str, Any] = Field(default_factory=dict)


class SalesSequenceCreate(RequestSchema):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    entity_type: Literal["lead", "contact"] = "lead"
    is_active: bool = True
    steps: list[SequenceStepInput] = Field(min_length=1, max_length=50)


class SequenceStepResponse(BaseModel):
    id: UUID
    position: int
    delay_days: int
    action_type: str
    config: dict[str, Any]

    model_config = {"from_attributes": True}


class SalesSequenceResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    entity_type: str
    is_active: bool
    steps: list[SequenceStepResponse] = Field(default_factory=list)
    enrollment_count: int = 0
    created_at: datetime
    updated_at: datetime


class SequenceEnrollRequest(RequestSchema):
    entity_id: UUID
    owner_user_id: UUID | None = None


class SequenceEnrollmentResponse(BaseModel):
    id: UUID
    sequence_id: UUID
    entity_type: str
    entity_id: UUID
    owner_user_id: UUID
    status: str
    next_step_position: int
    next_run_at: datetime | None
    started_at: datetime
    finished_at: datetime | None
    last_error: str | None

    model_config = {"from_attributes": True}


class QuoteApprovalRequest(RequestSchema):
    note: str | None = Field(default=None, max_length=2000)


class WebhookDeliveryResponse(BaseModel):
    id: UUID
    endpoint_id: UUID
    event_type: str
    status: str
    attempts: int
    response_status: int | None
    last_error: str | None
    delivered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

# ------------------------ V3 actionable intelligence ------------------------

class AttentionItem(BaseModel):
    kind: Literal["task", "deal", "lead", "activity"]
    entity_id: UUID
    title: str
    reason: str
    priority: Literal["low", "medium", "high"]
    route: str


class MorningBriefResponse(BaseModel):
    generated_at: datetime
    overdue_tasks: int
    due_today: int
    stale_leads: int
    closing_soon_deals: int
    actions: list[AttentionItem]


class LeadScoreResponse(BaseModel):
    lead_id: UUID
    score: int = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D"]
    factors: list[str]
    next_actions: list[str]


class WinLossAnalyticsResponse(BaseModel):
    won_count: int
    lost_count: int
    open_count: int
    win_rate: Decimal
    won_value_by_currency: dict[str, Decimal]
    lost_value_by_currency: dict[str, Decimal]
    average_won_value_by_currency: dict[str, Decimal]
