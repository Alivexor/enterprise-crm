from typing import Annotated
from uuid import UUID

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.v3 import (
    AiCopilotRequest,
    AiCopilotResponse,
    AiModelPullRequest,
    AiDealInsightResponse,
    AiStatusResponse,
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionResponse,
    CustomFieldDefinitionUpdate,
    CustomFieldValuesResponse,
    CustomFieldValuesUpdate,
    DataQualityResponse,
    LeadScoreResponse,
    MorningBriefResponse,
    WebhookDeliveryResponse,
    QuoteApprovalRequest,
    SequenceEnrollmentResponse,
    SequenceEnrollRequest,
    SalesSequenceResponse,
    SalesSequenceCreate,
    DashboardWidgetUpdate,
    DashboardWidgetResponse,
    DashboardWidgetCreate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    QuoteCreate,
    QuoteResponse,
    RelationshipHealthResponse,
    ReportBuilderResponse,
    RevenueForecastResponse,
    SalesGoalCreate,
    SalesGoalResponse,
    SavedViewCreate,
    SavedViewResponse,
    SavedViewUpdate,
    WebhookCreate,
    WebhookCreatedResponse,
    WebhookResponse,
    WinLossAnalyticsResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowUpdate,
)
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.v3_platform import (
    V3ConflictError,
    V3ExternalServiceError,
    V3NotFoundError,
    V3ValidationError,
    v3_platform_service,
)

router = APIRouter(prefix="/v3", tags=["v3"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _errors(exc: Exception) -> HTTPException:
    if isinstance(exc, V3NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, V3ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, V3ValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    if isinstance(exc, V3ExternalServiceError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected V3 platform error")


# Saved views
@router.get("/saved-views", response_model=list[SavedViewResponse])
def list_saved_views(
    database_session: DatabaseSession,
    current_user: Annotated[User, Depends(require_permissions(PermissionName.SAVED_VIEWS_READ))],
    resource: str | None = Query(default=None, max_length=64),
) -> list[SavedViewResponse]:
    return [SavedViewResponse.model_validate(item) for item in v3_platform_service.list_saved_views(database_session, current_user.organization_id, current_user.id, resource)]


@router.post("/saved-views", response_model=SavedViewResponse, status_code=status.HTTP_201_CREATED)
def create_saved_view(data: SavedViewCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SAVED_VIEWS_UPDATE))]) -> SavedViewResponse:
    try:
        return SavedViewResponse.model_validate(v3_platform_service.create_saved_view(database_session, current_user.organization_id, current_user.id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.patch("/saved-views/{view_id}", response_model=SavedViewResponse)
def update_saved_view(view_id: UUID, data: SavedViewUpdate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SAVED_VIEWS_UPDATE))]) -> SavedViewResponse:
    try:
        return SavedViewResponse.model_validate(v3_platform_service.update_saved_view(database_session, current_user.organization_id, current_user.id, view_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.delete("/saved-views/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_view(view_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SAVED_VIEWS_UPDATE))]) -> Response:
    try:
        v3_platform_service.delete_saved_view(database_session, current_user.organization_id, current_user.id, view_id)
    except Exception as exc:
        raise _errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Custom fields
@router.get("/custom-fields", response_model=list[CustomFieldDefinitionResponse])
def list_custom_fields(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.CUSTOM_FIELDS_READ))], entity_type: str | None = None) -> list[CustomFieldDefinitionResponse]:
    return [CustomFieldDefinitionResponse.model_validate(item) for item in v3_platform_service.list_custom_fields(database_session, current_user.organization_id, entity_type)]


@router.post("/custom-fields", response_model=CustomFieldDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_custom_field(data: CustomFieldDefinitionCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.CUSTOM_FIELDS_UPDATE))]) -> CustomFieldDefinitionResponse:
    try:
        return CustomFieldDefinitionResponse.model_validate(v3_platform_service.create_custom_field(database_session, current_user.organization_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.patch("/custom-fields/{definition_id}", response_model=CustomFieldDefinitionResponse)
def update_custom_field(definition_id: UUID, data: CustomFieldDefinitionUpdate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.CUSTOM_FIELDS_UPDATE))]) -> CustomFieldDefinitionResponse:
    try:
        return CustomFieldDefinitionResponse.model_validate(v3_platform_service.update_custom_field(database_session, current_user.organization_id, definition_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.delete("/custom-fields/{definition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_field(definition_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.CUSTOM_FIELDS_UPDATE))]) -> Response:
    try:
        v3_platform_service.delete_custom_field(database_session, current_user.organization_id, definition_id)
    except Exception as exc:
        raise _errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/custom-fields/{entity_type}/{entity_id}/values", response_model=CustomFieldValuesResponse)
def get_custom_field_values(entity_type: str, entity_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.CUSTOM_FIELDS_READ))]) -> CustomFieldValuesResponse:
    try:
        return v3_platform_service.get_custom_field_values(database_session, current_user.organization_id, entity_type, entity_id)
    except Exception as exc:
        raise _errors(exc) from exc


@router.put("/custom-fields/{entity_type}/{entity_id}/values", response_model=CustomFieldValuesResponse)
def set_custom_field_values(entity_type: str, entity_id: UUID, data: CustomFieldValuesUpdate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.CUSTOM_FIELDS_UPDATE))]) -> CustomFieldValuesResponse:
    try:
        return v3_platform_service.set_custom_field_values(database_session, current_user.organization_id, current_user.id, entity_type, entity_id, data.values)
    except Exception as exc:
        raise _errors(exc) from exc


# Workflow automation
@router.get("/automation/workflows", response_model=list[WorkflowResponse])
def list_workflows(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.AUTOMATIONS_READ))]) -> list[WorkflowResponse]:
    return [WorkflowResponse.model_validate(item) for item in v3_platform_service.list_workflows(database_session, current_user.organization_id)]


@router.post("/automation/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(data: WorkflowCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.AUTOMATIONS_UPDATE))]) -> WorkflowResponse:
    try:
        return WorkflowResponse.model_validate(v3_platform_service.create_workflow(database_session, current_user.organization_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.patch("/automation/workflows/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: UUID, data: WorkflowUpdate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.AUTOMATIONS_UPDATE))]) -> WorkflowResponse:
    try:
        return WorkflowResponse.model_validate(v3_platform_service.update_workflow(database_session, current_user.organization_id, workflow_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.delete("/automation/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.AUTOMATIONS_UPDATE))]) -> Response:
    try:
        v3_platform_service.delete_workflow(database_session, current_user.organization_id, workflow_id)
    except Exception as exc:
        raise _errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/automation/workflows/{workflow_id}/run", response_model=WorkflowRunResponse)
def run_workflow(workflow_id: UUID, data: WorkflowRunRequest, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.AUTOMATIONS_UPDATE))]) -> WorkflowRunResponse:
    try:
        return WorkflowRunResponse.model_validate(v3_platform_service.run_workflow(database_session, current_user.organization_id, current_user.id, workflow_id, data.entity_id, data.payload))
    except Exception as exc:
        raise _errors(exc) from exc


# Intelligence and reports
@router.get("/intelligence/data-quality", response_model=DataQualityResponse)
def data_quality(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DATA_QUALITY_READ))]) -> DataQualityResponse:
    return v3_platform_service.data_quality(database_session, current_user.organization_id)


@router.get("/intelligence/morning-brief", response_model=MorningBriefResponse)
def morning_brief(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.REPORTS_READ))]) -> MorningBriefResponse:
    return v3_platform_service.morning_brief(database_session, current_user.organization_id, current_user.id)


@router.get("/intelligence/lead-score/{lead_id}", response_model=LeadScoreResponse)
def lead_score(lead_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.REPORTS_READ))]) -> LeadScoreResponse:
    try:
        return v3_platform_service.lead_score(database_session, current_user.organization_id, lead_id)
    except Exception as exc:
        raise _errors(exc) from exc


@router.get("/reports/win-loss", response_model=WinLossAnalyticsResponse)
def win_loss(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.REPORTS_READ))]) -> WinLossAnalyticsResponse:
    return v3_platform_service.win_loss_analytics(database_session, current_user.organization_id)


@router.get("/reports/forecast", response_model=RevenueForecastResponse)
def forecast(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.REPORTS_READ))]) -> RevenueForecastResponse:
    return v3_platform_service.revenue_forecast(database_session, current_user.organization_id)


@router.get("/reports/builder", response_model=ReportBuilderResponse)
def build_report(
    database_session: DatabaseSession,
    current_user: Annotated[User, Depends(require_permissions(PermissionName.REPORTS_READ))],
    resource: str = Query(pattern=r"^(deals|leads|tasks|activities)$"),
    metric: str = Query(pattern=r"^(count|sum_value|weighted_value)$"),
    group_by: str = Query(min_length=2, max_length=40),
) -> ReportBuilderResponse:
    try:
        return v3_platform_service.report_builder(database_session, current_user.organization_id, resource, metric, group_by)
    except Exception as exc:
        raise _errors(exc) from exc


@router.get("/intelligence/relationship-health/{company_id}", response_model=RelationshipHealthResponse)
def relationship_health(company_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DATA_QUALITY_READ))]) -> RelationshipHealthResponse:
    try:
        return v3_platform_service.relationship_health(database_session, current_user.organization_id, company_id)
    except Exception as exc:
        raise _errors(exc) from exc


# Goals
@router.get("/goals", response_model=list[SalesGoalResponse])
def list_goals(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.GOALS_READ))]) -> list[SalesGoalResponse]:
    return v3_platform_service.list_goals(database_session, current_user.organization_id)


@router.post("/goals", response_model=SalesGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(data: SalesGoalCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.GOALS_UPDATE))]) -> SalesGoalResponse:
    try:
        return v3_platform_service.create_goal(database_session, current_user.organization_id, data)
    except Exception as exc:
        raise _errors(exc) from exc


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.GOALS_UPDATE))]) -> Response:
    try:
        v3_platform_service.delete_goal(database_session, current_user.organization_id, goal_id)
    except Exception as exc:
        raise _errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Product catalog and quote lite
@router.get("/products", response_model=list[ProductResponse])
def list_products(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.PRODUCTS_READ))], include_inactive: bool = False) -> list[ProductResponse]:
    return [ProductResponse.model_validate(item) for item in v3_platform_service.list_products(database_session, current_user.organization_id, include_inactive)]


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.PRODUCTS_UPDATE))]) -> ProductResponse:
    try:
        return ProductResponse.model_validate(v3_platform_service.create_product(database_session, current_user.organization_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: UUID, data: ProductUpdate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.PRODUCTS_UPDATE))]) -> ProductResponse:
    try:
        return ProductResponse.model_validate(v3_platform_service.update_product(database_session, current_user.organization_id, product_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.get("/quotes", response_model=list[QuoteResponse])
def list_quotes(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.QUOTES_READ))]) -> list[QuoteResponse]:
    return v3_platform_service.list_quotes(database_session, current_user.organization_id)


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.QUOTES_READ))]) -> QuoteResponse:
    try:
        return v3_platform_service.get_quote(database_session, current_user.organization_id, quote_id)
    except Exception as exc:
        raise _errors(exc) from exc


@router.post("/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(data: QuoteCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.QUOTES_UPDATE))]) -> QuoteResponse:
    try:
        return v3_platform_service.create_quote(database_session, current_user.organization_id, current_user.id, data)
    except Exception as exc:
        raise _errors(exc) from exc


@router.post("/quotes/{quote_id}/approve", response_model=QuoteResponse)
def approve_quote(quote_id: UUID, data: QuoteApprovalRequest, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.QUOTES_APPROVE))]) -> QuoteResponse:
    try:
        return v3_platform_service.approve_quote(database_session, current_user.organization_id, current_user.id, quote_id, data, approved=True)
    except Exception as exc:
        raise _errors(exc) from exc


@router.post("/quotes/{quote_id}/reject", response_model=QuoteResponse)
def reject_quote(quote_id: UUID, data: QuoteApprovalRequest, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.QUOTES_APPROVE))]) -> QuoteResponse:
    try:
        return v3_platform_service.approve_quote(database_session, current_user.organization_id, current_user.id, quote_id, data, approved=False)
    except Exception as exc:
        raise _errors(exc) from exc


# Local AI via Ollama
@router.get("/ai/status", response_model=AiStatusResponse)
def ai_status(current_user: Annotated[User, Depends(require_permissions(PermissionName.AI_USE))]) -> AiStatusResponse:
    _ = current_user
    return v3_platform_service.ai_status()


@router.post("/ai/copilot", response_model=AiCopilotResponse)
def ai_copilot(data: AiCopilotRequest, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.AI_USE))]) -> AiCopilotResponse:
    try:
        return v3_platform_service.ai_copilot(database_session, current_user.organization_id, current_user.id, data.prompt, data.locale)
    except Exception as exc:
        raise _errors(exc) from exc


@router.post("/ai/copilot/stream")
def ai_copilot_stream(
    data: AiCopilotRequest,
    database_session: DatabaseSession,
    current_user: Annotated[User, Depends(require_permissions(PermissionName.AI_USE))],
) -> StreamingResponse:
    try:
        events = v3_platform_service.build_ai_copilot_stream(
            database_session,
            current_user.organization_id,
            current_user.id,
            data.prompt,
            data.locale,
            data.model,
        )
    except Exception as exc:
        raise _errors(exc) from exc

    def encode_events():
        for event in events:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        encode_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/ai/models/pull")
def ai_model_pull(
    data: AiModelPullRequest,
    current_user: Annotated[User, Depends(require_permissions(PermissionName.AI_USE))],
) -> StreamingResponse:
    _ = current_user
    def encode_events():
        for event in v3_platform_service.pull_ai_model(data.model):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(encode_events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/ai/deals/{deal_id}/insight", response_model=AiDealInsightResponse)
def ai_deal_insight(deal_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.AI_USE))]) -> AiDealInsightResponse:
    try:
        return v3_platform_service.ai_deal_insight(database_session, current_user.organization_id, deal_id)
    except Exception as exc:
        raise _errors(exc) from exc


# Developer platform
@router.get("/developer/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DEVELOPER_READ))]) -> list[ApiKeyResponse]:
    return [ApiKeyResponse.model_validate(item) for item in v3_platform_service.list_api_keys(database_session, current_user.organization_id, current_user.id)]


@router.post("/developer/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(data: ApiKeyCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DEVELOPER_UPDATE))]) -> ApiKeyCreatedResponse:
    try:
        return v3_platform_service.create_api_key(database_session, current_user.organization_id, current_user.id, data)
    except Exception as exc:
        raise _errors(exc) from exc


@router.delete("/developer/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(key_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DEVELOPER_UPDATE))]) -> Response:
    try:
        v3_platform_service.revoke_api_key(database_session, current_user.organization_id, current_user.id, key_id)
    except Exception as exc:
        raise _errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/developer/webhooks", response_model=list[WebhookResponse])
def list_webhooks(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DEVELOPER_READ))]) -> list[WebhookResponse]:
    return [WebhookResponse.model_validate(item) for item in v3_platform_service.list_webhooks(database_session, current_user.organization_id)]


@router.post("/developer/webhooks", response_model=WebhookCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(data: WebhookCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DEVELOPER_UPDATE))]) -> WebhookCreatedResponse:
    try:
        return v3_platform_service.create_webhook(database_session, current_user.organization_id, data)
    except Exception as exc:
        raise _errors(exc) from exc


# Personal dashboards
@router.get("/dashboard-widgets", response_model=list[DashboardWidgetResponse])
def list_dashboard_widgets(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DASHBOARDS_READ))]) -> list[DashboardWidgetResponse]:
    return [DashboardWidgetResponse.model_validate(item) for item in v3_platform_service.list_dashboard_widgets(database_session, current_user.organization_id, current_user.id)]


@router.post("/dashboard-widgets", response_model=DashboardWidgetResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard_widget(data: DashboardWidgetCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DASHBOARDS_UPDATE))]) -> DashboardWidgetResponse:
    try:
        return DashboardWidgetResponse.model_validate(v3_platform_service.create_dashboard_widget(database_session, current_user.organization_id, current_user.id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.patch("/dashboard-widgets/{widget_id}", response_model=DashboardWidgetResponse)
def update_dashboard_widget(widget_id: UUID, data: DashboardWidgetUpdate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DASHBOARDS_UPDATE))]) -> DashboardWidgetResponse:
    try:
        return DashboardWidgetResponse.model_validate(v3_platform_service.update_dashboard_widget(database_session, current_user.organization_id, current_user.id, widget_id, data))
    except Exception as exc:
        raise _errors(exc) from exc


@router.delete("/dashboard-widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard_widget(widget_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DASHBOARDS_UPDATE))]) -> Response:
    try:
        v3_platform_service.delete_dashboard_widget(database_session, current_user.organization_id, current_user.id, widget_id)
    except Exception as exc:
        raise _errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Sales sequences
@router.get("/sequences", response_model=list[SalesSequenceResponse])
def list_sequences(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SEQUENCES_READ))]) -> list[SalesSequenceResponse]:
    return v3_platform_service.list_sequences(database_session, current_user.organization_id)


@router.post("/sequences", response_model=SalesSequenceResponse, status_code=status.HTTP_201_CREATED)
def create_sequence(data: SalesSequenceCreate, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SEQUENCES_UPDATE))]) -> SalesSequenceResponse:
    try:
        return v3_platform_service.create_sequence(database_session, current_user.organization_id, data)
    except Exception as exc:
        raise _errors(exc) from exc


@router.delete("/sequences/{sequence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sequence(sequence_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SEQUENCES_UPDATE))]) -> Response:
    try:
        v3_platform_service.delete_sequence(database_session, current_user.organization_id, sequence_id)
    except Exception as exc:
        raise _errors(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sequences/enrollments", response_model=list[SequenceEnrollmentResponse])
def list_sequence_enrollments(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SEQUENCES_READ))]) -> list[SequenceEnrollmentResponse]:
    return [SequenceEnrollmentResponse.model_validate(item) for item in v3_platform_service.list_sequence_enrollments(database_session, current_user.organization_id)]


@router.post("/sequences/{sequence_id}/enroll", response_model=SequenceEnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_sequence(sequence_id: UUID, data: SequenceEnrollRequest, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.SEQUENCES_UPDATE))]) -> SequenceEnrollmentResponse:
    try:
        return SequenceEnrollmentResponse.model_validate(v3_platform_service.enroll_sequence(database_session, current_user.organization_id, current_user.id, sequence_id, data.entity_id, data.owner_user_id))
    except Exception as exc:
        raise _errors(exc) from exc


# Webhook delivery log
@router.get("/developer/webhook-deliveries", response_model=list[WebhookDeliveryResponse])
def list_webhook_deliveries(database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DEVELOPER_READ))], endpoint_id: UUID | None = None) -> list[WebhookDeliveryResponse]:
    return [WebhookDeliveryResponse.model_validate(item) for item in v3_platform_service.list_webhook_deliveries(database_session, current_user.organization_id, endpoint_id)]


@router.post("/developer/webhook-deliveries/{delivery_id}/retry", response_model=WebhookDeliveryResponse)
def retry_webhook_delivery(delivery_id: UUID, database_session: DatabaseSession, current_user: Annotated[User, Depends(require_permissions(PermissionName.DEVELOPER_UPDATE))]) -> WebhookDeliveryResponse:
    try:
        return WebhookDeliveryResponse.model_validate(v3_platform_service.retry_webhook_delivery(database_session, current_user.organization_id, delivery_id))
    except Exception as exc:
        raise _errors(exc) from exc
