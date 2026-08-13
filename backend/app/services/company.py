from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.services.audit import AuditService, audit_service


class CompanyNotFoundError(Exception):
    """Raised when an organization-scoped company does not exist."""


class CompanyDeletionConflictError(Exception):
    """Raised when related records prevent company deletion."""


class CompanyService:
    def __init__(
        self, company_repository: CompanyRepository, audit_service: AuditService
    ) -> None:
        self.company_repository = company_repository
        self.audit_service = audit_service

    def create_company(
        self,
        database_session: Session,
        organization_id: UUID,
        actor_id: UUID,
        company_data: CompanyCreate,
    ) -> Company:
        company = self.company_repository.create(
            database_session, organization_id, company_data
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="company.created",
            entity_type="company",
            entity_id=company.id,
        )
        database_session.commit()
        return company

    def list_companies(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        industry: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Company], int]:
        return self.company_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            industry=industry,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_company(
        self,
        database_session: Session,
        organization_id: UUID,
        company_id: UUID,
    ) -> Company:
        company = self.company_repository.get_by_id(
            database_session, company_id, organization_id
        )
        if company is None:
            raise CompanyNotFoundError
        return company

    def update_company(
        self,
        database_session: Session,
        organization_id: UUID,
        actor_id: UUID,
        company_id: UUID,
        company_data: CompanyUpdate,
    ) -> Company:
        company = self.get_company(database_session, organization_id, company_id)
        self.company_repository.update(database_session, company, company_data)
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="company.updated",
            entity_type="company",
            entity_id=company.id,
        )
        database_session.commit()
        return company

    def delete_company(
        self,
        database_session: Session,
        organization_id: UUID,
        actor_id: UUID,
        company_id: UUID,
    ) -> None:
        company = self.get_company(database_session, organization_id, company_id)
        if self.company_repository.has_contacts(database_session, company.id):
            raise CompanyDeletionConflictError
        try:
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="company.deleted",
                entity_type="company",
                entity_id=company.id,
            )
            self.company_repository.delete(database_session, company)
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise CompanyDeletionConflictError from exc


company_service = CompanyService(CompanyRepository(), audit_service)
