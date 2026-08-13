from uuid import UUID

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import OrganizationUpdate
from app.services.audit import AuditService, audit_service


class OrganizationNotFoundError(Exception):
    """Raised when the configured organization is unavailable."""


class OrganizationService:
    def __init__(
        self,
        organization_repository: OrganizationRepository,
        audit_service: AuditService,
    ) -> None:
        self.organization_repository = organization_repository
        self.audit_service = audit_service

    def get_organization(
        self, database_session: Session, organization_id: UUID
    ) -> Organization:
        organization = self.organization_repository.get_by_id(
            database_session, organization_id
        )
        if organization is None:
            raise OrganizationNotFoundError
        return organization

    def update_organization(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        organization_data: OrganizationUpdate,
    ) -> Organization:
        organization = self.get_organization(database_session, organization_id)
        self.organization_repository.update(
            database_session, organization, name=organization_data.name
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="organization.updated",
            entity_type="organization",
            entity_id=organization.id,
        )
        database_session.commit()
        return organization


organization_service = OrganizationService(OrganizationRepository(), audit_service)
