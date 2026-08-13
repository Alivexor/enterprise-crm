"""Organization-scoped validation for relationships between CRM records."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.lead import Lead
from app.repositories.company import CompanyRepository
from app.repositories.contact import ContactRepository
from app.repositories.lead import LeadRepository
from app.repositories.user import UserRepository


class ReferenceNotFoundError(Exception):
    """A referenced record is not available within the current organization."""


class ReferenceRelationshipError(Exception):
    """Referenced records are valid individually but cannot be related."""


class OrganizationReferenceService:
    def __init__(
        self,
        user_repository: UserRepository,
        company_repository: CompanyRepository,
        contact_repository: ContactRepository,
        lead_repository: LeadRepository,
    ) -> None:
        self.user_repository = user_repository
        self.company_repository = company_repository
        self.contact_repository = contact_repository
        self.lead_repository = lead_repository

    def require_user(
        self, database_session: Session, organization_id: UUID, user_id: UUID
    ) -> None:
        user = self.user_repository.get_by_id(
            database_session, user_id, organization_id
        )
        if user is None or not user.is_active:
            raise ReferenceNotFoundError

    def require_company(
        self, database_session: Session, organization_id: UUID, company_id: UUID
    ) -> None:
        if self.company_repository.get_by_id(database_session, company_id, organization_id) is None:
            raise ReferenceNotFoundError

    def get_contact(
        self, database_session: Session, organization_id: UUID, contact_id: UUID
    ) -> Contact:
        contact = self.contact_repository.get_by_id(
            database_session, contact_id, organization_id
        )
        if contact is None:
            raise ReferenceNotFoundError
        return contact

    def get_lead(
        self, database_session: Session, organization_id: UUID, lead_id: UUID
    ) -> Lead:
        lead = self.lead_repository.get_by_id(database_session, organization_id, lead_id)
        if lead is None:
            raise ReferenceNotFoundError
        return lead

    def validate_company_contact(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        company_id: UUID | None,
        contact_id: UUID | None,
    ) -> None:
        if company_id is not None:
            self.require_company(database_session, organization_id, company_id)
        if contact_id is None:
            return
        contact = self.get_contact(database_session, organization_id, contact_id)
        if company_id is not None and contact.company_id != company_id:
            raise ReferenceRelationshipError(
                "The selected contact does not belong to the selected company"
            )


reference_service = OrganizationReferenceService(
    UserRepository(), CompanyRepository(), ContactRepository(), LeadRepository()
)
