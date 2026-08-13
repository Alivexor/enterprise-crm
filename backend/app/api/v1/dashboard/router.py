from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.dashboard import AnalyticsResponse, DashboardResponse, OperationalHealthResponse
from app.security.permissions import require_permissions
from app.services.dashboard import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
DatabaseSession = Annotated[Session, Depends(get_db)]
DashboardReader = Annotated[User, Depends(require_permissions("dashboard.read"))]
AnalyticsReader = Annotated[User, Depends(require_permissions("analytics.read"))]


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    database_session: DatabaseSession, current_user: DashboardReader
) -> DashboardResponse:
    return dashboard_service.get_dashboard(database_session, current_user.organization_id)


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    database_session: DatabaseSession, current_user: AnalyticsReader
) -> AnalyticsResponse:
    return dashboard_service.get_analytics(database_session, current_user.organization_id)


@router.get("/health", response_model=OperationalHealthResponse)
def get_operational_health(
    database_session: DatabaseSession, current_user: AnalyticsReader
) -> OperationalHealthResponse:
    return dashboard_service.get_operational_health(
        database_session, current_user.organization_id
    )
