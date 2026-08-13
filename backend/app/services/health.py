"""Infrastructure readiness checks."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class HealthService:
    def database_ready(self, database_session: Session) -> bool:
        try:
            database_session.execute(select(1)).scalar_one()
        except SQLAlchemyError:
            return False
        return True


health_service = HealthService()
