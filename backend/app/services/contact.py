from uuid import UUID

from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.repositories.company import CompanyRepository
from app.repositories.contact import ContactRepository
from app.schemas.contact import ContactCreate, ContactUpdate
from app.services.audit import AuditService, audit_service


class ContactNotFoundError(Exception):
    """Raised when a contact is not accessible within an organization."""


class ContactService:
    def __init__(
        self,
        contact_repository: ContactRepository,
        company_repository: CompanyRepository,
        audit_service: AuditService,
    ) -> None:
        self.contact_repository = contact_repository
        self.company_repository = company_repository
        self.audit_service = audit_service

    def create_contact(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        contact_data: ContactCreate,
    ) -> Contact:
        self._require_company(database_session, organization_id, contact_data.company_id)
        contact = self.contact_repository.create(database_session, contact_data)
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="contact.created",
            entity_type="contact",
            entity_id=contact.id,
        )
        database_session.commit()
        return contact

    def list_contacts(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        company_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Contact], int]:
        if company_id is not None:
            self._require_company(database_session, organization_id, company_id)
        return self.contact_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            company_id=company_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_contact(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        contact_id: UUID,
    ) -> Contact:
        contact = self.contact_repository.get_by_id(
            database_session, contact_id, organization_id
        )
        if contact is None:
            raise ContactNotFoundError
        return contact

    def update_contact(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        contact_id: UUID,
        contact_data: ContactUpdate,
    ) -> Contact:
        contact = self.get_contact(
            database_session, organization_id=organization_id, contact_id=contact_id
        )
        if contact_data.company_id is not None:
            self._require_company(database_session, organization_id, contact_data.company_id)
        self.contact_repository.update(database_session, contact, contact_data)
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="contact.updated",
            entity_type="contact",
            entity_id=contact.id,
        )
        database_session.commit()
        return contact

    def delete_contact(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        contact_id: UUID,
    ) -> None:
        contact = self.get_contact(
            database_session, organization_id=organization_id, contact_id=contact_id
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="contact.deleted",
            entity_type="contact",
            entity_id=contact.id,
        )
        self.contact_repository.delete(database_session, contact)
        database_session.commit()

    def _require_company(
        self, database_session: Session, organization_id: UUID, company_id: UUID
    ) -> None:
        company = self.company_repository.get_by_id(
            database_session, company_id, organization_id
        )
        if company is None:
            raise ContactNotFoundError


contact_service = ContactService(ContactRepository(), CompanyRepository(), audit_service)
