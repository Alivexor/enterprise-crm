from uuid import UUID

from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.repositories.company import CompanyRepository
from app.repositories.contact import ContactRepository
from app.repositories.lead import LeadRepository
from app.repositories.user import UserRepository
from app.schemas.deal import DealCreate
from app.schemas.lead import LeadConversionRequest, LeadCreate, LeadUpdate
from app.services.audit import AuditService, audit_service
from app.services.assignment_notifications import (
    AssignmentNotificationService,
    assignment_notification_service,
)
from app.services.deal import (
    DealConflictError,
    DealReferenceNotFoundError,
    DealRelationshipMismatchError,
    DealService,
    deal_service,
)


class LeadNotFoundError(Exception):
    """Raised when a lead or supplied related record is outside the organization."""


class LeadReferenceError(Exception):
    """Raised when valid records are combined in an invalid relationship."""


class LeadConversionValidationError(Exception):
    """Raised when a lead cannot be converted with the supplied deal context."""


class LeadConversionConflictError(Exception):
    """Raised when a lead has already been converted or deal creation conflicts."""


class LeadService:
    def __init__(
        self,
        lead_repository: LeadRepository,
        company_repository: CompanyRepository,
        contact_repository: ContactRepository,
        user_repository: UserRepository,
        audit_service: AuditService,
        assignment_notification_service: AssignmentNotificationService,
        deal_service: DealService,
    ) -> None:
        self.lead_repository = lead_repository
        self.company_repository = company_repository
        self.contact_repository = contact_repository
        self.user_repository = user_repository
        self.audit_service = audit_service
        self.assignment_notification_service = assignment_notification_service
        self.deal_service = deal_service

    def create_lead(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        lead_data: LeadCreate,
    ) -> Lead:
        data = lead_data.model_dump()
        assigned_user_id = data.pop("assigned_user_id") or actor_id
        self._validate_references(
            database_session,
            organization_id=organization_id,
            company_id=data.get("company_id"),
            contact_id=data.get("contact_id"),
            assigned_user_id=assigned_user_id,
        )
        lead = self.lead_repository.create(
            database_session,
            organization_id=organization_id,
            assigned_user_id=assigned_user_id,
            data=data,
        )
        self.assignment_notification_service.notify_assignee(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            recipient_id=assigned_user_id,
            entity_type="lead",
            entity_id=lead.id,
            title=lead.title,
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="lead.created",
            entity_type="lead",
            entity_id=lead.id,
        )
        from app.services.v3_platform import v3_platform_service
        v3_platform_service.emit_event(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            event_type="lead.created",
            entity_type="lead",
            entity_id=lead.id,
            payload={
                "id": str(lead.id),
                "title": lead.title,
                "status": lead.status,
                "source": lead.source,
                "assigned_user_id": str(lead.assigned_user_id),
                "company_id": str(lead.company_id) if lead.company_id else None,
                "contact_id": str(lead.contact_id) if lead.contact_id else None,
            },
        )
        database_session.commit()
        return lead

    def list_leads(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        assigned_user_id: UUID | None,
        company_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Lead], int]:
        return self.lead_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            assigned_user_id=assigned_user_id,
            company_id=company_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_lead(
        self, database_session: Session, *, organization_id: UUID, lead_id: UUID
    ) -> Lead:
        lead = self.lead_repository.get_by_id(database_session, organization_id, lead_id)
        if lead is None:
            raise LeadNotFoundError
        return lead

    def update_lead(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        lead_id: UUID,
        lead_data: LeadUpdate,
    ) -> Lead:
        lead = self.get_lead(
            database_session, organization_id=organization_id, lead_id=lead_id
        )
        data = lead_data.model_dump(exclude_unset=True)
        final_company_id = data.get("company_id", lead.company_id)
        final_contact_id = data.get("contact_id", lead.contact_id)
        previous_assigned_user_id = lead.assigned_user_id
        final_assigned_user_id = data.get(
            "assigned_user_id", previous_assigned_user_id
        )
        self._validate_references(
            database_session,
            organization_id=organization_id,
            company_id=final_company_id,
            contact_id=final_contact_id,
            assigned_user_id=final_assigned_user_id,
        )
        self.lead_repository.update(database_session, lead, data)
        if final_assigned_user_id != previous_assigned_user_id:
            self.assignment_notification_service.notify_assignee(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                recipient_id=final_assigned_user_id,
                entity_type="lead",
                entity_id=lead.id,
                title=lead.title,
            )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="lead.updated",
            entity_type="lead",
            entity_id=lead.id,
        )
        from app.services.v3_platform import v3_platform_service
        v3_platform_service.emit_event(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            event_type="lead.updated",
            entity_type="lead",
            entity_id=lead.id,
            payload={
                "id": str(lead.id),
                "title": lead.title,
                "status": lead.status,
                "source": lead.source,
                "assigned_user_id": str(lead.assigned_user_id),
                "company_id": str(lead.company_id) if lead.company_id else None,
                "contact_id": str(lead.contact_id) if lead.contact_id else None,
            },
        )
        database_session.commit()
        return lead

    def convert_lead(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        lead_id: UUID,
        conversion_data: LeadConversionRequest,
    ) -> tuple[Lead, Deal]:
        lead = self.get_lead(
            database_session, organization_id=organization_id, lead_id=lead_id
        )
        if lead.status == "converted":
            raise LeadConversionConflictError("Lead has already been converted")
        if lead.status == "lost":
            raise LeadConversionValidationError(
                "A lost lead must be reopened before it can be converted"
            )
        if lead.company_id is None:
            raise LeadConversionValidationError(
                "Link the lead to a company before converting it to a deal"
            )

        deal_data = DealCreate(
            company_id=lead.company_id,
            contact_id=lead.contact_id,
            pipeline_id=conversion_data.pipeline_id,
            stage_id=conversion_data.stage_id,
            assigned_user_id=lead.assigned_user_id,
            title=conversion_data.title or lead.title,
            value=conversion_data.value,
            currency=conversion_data.currency,
            probability=conversion_data.probability,
            expected_close_date=conversion_data.expected_close_date,
            status="open",
        )
        try:
            deal = self.deal_service.create_deal(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                deal_data=deal_data,
                commit=False,
            )
            self.lead_repository.update(database_session, lead, {"status": "converted"})
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="lead.converted",
                entity_type="lead",
                entity_id=lead.id,
            )
            database_session.commit()
        except DealReferenceNotFoundError as exc:
            database_session.rollback()
            raise LeadConversionValidationError(
                "Selected pipeline, stage, or related record was not found"
            ) from exc
        except DealRelationshipMismatchError as exc:
            database_session.rollback()
            raise LeadConversionValidationError(
                "The selected stage does not belong to the selected pipeline"
            ) from exc
        except DealConflictError as exc:
            database_session.rollback()
            raise LeadConversionConflictError(
                "A deal could not be created from this lead"
            ) from exc
        except Exception:
            database_session.rollback()
            raise
        return lead, deal

    def delete_lead(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        lead_id: UUID,
    ) -> None:
        lead = self.get_lead(
            database_session, organization_id=organization_id, lead_id=lead_id
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="lead.deleted",
            entity_type="lead",
            entity_id=lead.id,
        )
        self.lead_repository.delete(database_session, lead)
        database_session.commit()

    def _validate_references(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        company_id: UUID | None,
        contact_id: UUID | None,
        assigned_user_id: UUID,
    ) -> None:
        assigned_user = self.user_repository.get_by_id(
            database_session, assigned_user_id, organization_id
        )
        if assigned_user is None or not assigned_user.is_active:
            raise LeadNotFoundError

        if company_id is not None and self.company_repository.get_by_id(
            database_session, company_id, organization_id
        ) is None:
            raise LeadNotFoundError

        contact: Contact | None = None
        if contact_id is not None:
            contact = self.contact_repository.get_by_id(
                database_session, contact_id, organization_id
            )
            if contact is None:
                raise LeadNotFoundError
        if company_id is not None and contact is not None and contact.company_id != company_id:
            raise LeadReferenceError(
                "The selected contact does not belong to the selected company"
            )


lead_service = LeadService(
    LeadRepository(),
    CompanyRepository(),
    ContactRepository(),
    UserRepository(),
    audit_service,
    assignment_notification_service,
    deal_service,
)
