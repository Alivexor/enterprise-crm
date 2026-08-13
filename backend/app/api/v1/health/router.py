from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.health import health_service

router = APIRouter(prefix="/health", tags=["health"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("", status_code=status.HTTP_200_OK)
def liveness() -> dict[str, str]:
    """Return process liveness without touching the database."""
    return {"status": "ok"}


@router.get("/ready", status_code=status.HTTP_200_OK)
def readiness(database_session: DatabaseSession) -> dict[str, str]:
    """Return readiness only when the configured database is reachable."""
    if not health_service.database_ready(database_session):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return {"status": "ready"}
