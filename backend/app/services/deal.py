"""Use cases for organization-scoped CRM deals."""

from typing import cast
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.repositories.company import CompanyRepository
from app.repositories.contact import ContactRepository
from app.repositories.deal import DealRepository
from app.repositories.pipeline import PipelineRepository
from app.repositories.user import UserRepository
from app.schemas.deal import DealCreate, DealUpdate
from app.services.audit import AuditService, audit_service
from app.services.assignment_notifications import (
    AssignmentNotificationService,
    assignment_notification_service,
)


class DealNotFoundError(Exception):
    """Raised when a deal is outside the caller's organization scope."""


class DealReferenceNotFoundError(Exception):
    """Raised when a related record is unavailable in the caller's organization."""


class DealRelationshipMismatchError(Exception):
    """Raised when otherwise accessible related records cannot be combined."""


class DealConflictError(Exception):
    """Raised when a database constraint prevents a deal mutation."""


class DealDeletionConflictError(Exception):
    """Raised when a deal cannot be removed while dependent records exist."""


class DealService:
    def __init__(
        self,
        deal_repository: DealRepository,
        company_repository: CompanyRepository,
        contact_repository: ContactRepository,
        pipeline_repository: PipelineRepository,
        user_repository: UserRepository,
        audit_service: AuditService,
        assignment_notification_service: AssignmentNotificationService,
    ) -> None:
        self.deal_repository = deal_repository
        self.company_repository = company_repository
        self.contact_repository = contact_repository
        self.pipeline_repository = pipeline_repository
        self.user_repository = user_repository
        self.audit_service = audit_service
        self.assignment_notification_service = assignment_notification_service

    def create_deal(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        deal_data: DealCreate,
        commit: bool = True,
    ) -> Deal:
        self._validate_references(
            database_session,
            organization_id=organization_id,
            company_id=deal_data.company_id,
            contact_id=deal_data.contact_id,
            pipeline_id=deal_data.pipeline_id,
            stage_id=deal_data.stage_id,
            assigned_user_id=deal_data.assigned_user_id,
        )
        try:
            deal = self.deal_repository.create(
                database_session, organization_id, deal_data
            )
            self.assignment_notification_service.notify_assignee(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                recipient_id=deal.assigned_user_id,
                entity_type="deal",
                entity_id=deal.id,
                title=deal.title,
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="deal.created",
                entity_type="deal",
                entity_id=deal.id,
            )
            from app.services.v3_platform import v3_platform_service
            v3_platform_service.emit_event(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                event_type="deal.created",
                entity_type="deal",
                entity_id=deal.id,
                payload={
                    "id": str(deal.id),
                    "title": deal.title,
                    "status": deal.status,
                    "value": str(deal.value),
                    "currency": deal.currency,
                    "probability": str(deal.probability),
                    "assigned_user_id": str(deal.assigned_user_id),
                    "company_id": str(deal.company_id),
                    "pipeline_id": str(deal.pipeline_id),
                    "stage_id": str(deal.stage_id),
                },
            )
            if commit:
                database_session.commit()
            else:
                database_session.flush()
        except IntegrityError as exc:
            database_session.rollback()
            raise DealConflictError from exc
        except Exception:
            database_session.rollback()
            raise
        if not commit:
            return deal
        return self.get_deal(
            database_session,
            organization_id=organization_id,
            deal_id=deal.id,
        )

    def list_deals(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        company_id: UUID | None,
        contact_id: UUID | None,
        pipeline_id: UUID | None,
        stage_id: UUID | None,
        assigned_user_id: UUID | None,
        status: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Deal], int]:
        self._validate_list_filters(
            database_session,
            organization_id=organization_id,
            company_id=company_id,
            contact_id=contact_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            assigned_user_id=assigned_user_id,
        )
        normalized_search = search.strip() if search is not None else None
        return self.deal_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=normalized_search or None,
            company_id=company_id,
            contact_id=contact_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            assigned_user_id=assigned_user_id,
            status=status,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_deal(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        deal_id: UUID,
    ) -> Deal:
        deal = self.deal_repository.get_by_id(
            database_session, deal_id, organization_id
        )
        if deal is None:
            raise DealNotFoundError
        return deal

    def update_deal(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        deal_id: UUID,
        deal_data: DealUpdate,
    ) -> Deal:
        deal = self.get_deal(
            database_session, organization_id=organization_id, deal_id=deal_id
        )
        changes = deal_data.model_dump(exclude_unset=True)
        previous_assigned_user_id = deal.assigned_user_id
        final_assigned_user_id = self._updated_uuid(
            changes, "assigned_user_id", previous_assigned_user_id
        )
        self._validate_references(
            database_session,
            organization_id=organization_id,
            company_id=self._updated_uuid(changes, "company_id", deal.company_id),
            contact_id=self._updated_optional_uuid(changes, "contact_id", deal.contact_id),
            pipeline_id=self._updated_uuid(changes, "pipeline_id", deal.pipeline_id),
            stage_id=self._updated_uuid(changes, "stage_id", deal.stage_id),
            assigned_user_id=final_assigned_user_id,
        )
        try:
            self.deal_repository.update(database_session, deal, deal_data)
            if final_assigned_user_id != previous_assigned_user_id:
                self.assignment_notification_service.notify_assignee(
                    database_session,
                    organization_id=organization_id,
                    actor_id=actor_id,
                    recipient_id=final_assigned_user_id,
                    entity_type="deal",
                    entity_id=deal.id,
                    title=deal.title,
                )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="deal.updated",
                entity_type="deal",
                entity_id=deal.id,
            )
            from app.services.v3_platform import v3_platform_service
            v3_platform_service.emit_event(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                event_type="deal.updated",
                entity_type="deal",
                entity_id=deal.id,
                payload={
                    "id": str(deal.id),
                    "title": deal.title,
                    "status": deal.status,
                    "value": str(deal.value),
                    "currency": deal.currency,
                    "probability": str(deal.probability),
                    "assigned_user_id": str(deal.assigned_user_id),
                    "company_id": str(deal.company_id),
                    "pipeline_id": str(deal.pipeline_id),
                    "stage_id": str(deal.stage_id),
                },
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise DealConflictError from exc
        return self.get_deal(
            database_session, organization_id=organization_id, deal_id=deal_id
        )

    def delete_deal(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        deal_id: UUID,
    ) -> None:
        deal = self.get_deal(
            database_session, organization_id=organization_id, deal_id=deal_id
        )
        try:
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="deal.deleted",
                entity_type="deal",
                entity_id=deal.id,
            )
            self.deal_repository.delete(database_session, deal)
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise DealDeletionConflictError from exc

    def _validate_list_filters(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        company_id: UUID | None,
        contact_id: UUID | None,
        pipeline_id: UUID | None,
        stage_id: UUID | None,
        assigned_user_id: UUID | None,
    ) -> None:
        company = None
        if company_id is not None:
            company = self._require_company(
                database_session, organization_id, company_id
            )
        if contact_id is not None:
            contact = self._require_contact(database_session, organization_id, contact_id)
            if company is not None and contact.company_id != company.id:
                raise DealRelationshipMismatchError
        pipeline = None
        if pipeline_id is not None:
            pipeline = self._require_pipeline(
                database_session, organization_id, pipeline_id
            )
        if stage_id is not None:
            stage = self._require_stage(database_session, organization_id, stage_id)
            if pipeline is not None and stage.pipeline_id != pipeline.id:
                raise DealRelationshipMismatchError
        if assigned_user_id is not None:
            self._require_active_user(database_session, organization_id, assigned_user_id)

    def _validate_references(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        company_id: UUID,
        contact_id: UUID | None,
        pipeline_id: UUID,
        stage_id: UUID,
        assigned_user_id: UUID,
    ) -> None:
        company = self._require_company(database_session, organization_id, company_id)
        if contact_id is not None:
            contact = self._require_contact(database_session, organization_id, contact_id)
            if contact.company_id != company.id:
                raise DealRelationshipMismatchError
        pipeline = self._require_pipeline(database_session, organization_id, pipeline_id)
        stage = self._require_stage(database_session, organization_id, stage_id)
        if stage.pipeline_id != pipeline.id:
            raise DealRelationshipMismatchError
        self._require_active_user(database_session, organization_id, assigned_user_id)

    def _require_company(
        self, database_session: Session, organization_id: UUID, company_id: UUID
    ) -> Company:
        company = self.company_repository.get_by_id(
            database_session, company_id, organization_id
        )
        if company is None:
            raise DealReferenceNotFoundError
        return company

    def _require_contact(
        self, database_session: Session, organization_id: UUID, contact_id: UUID
    ) -> Contact:
        contact = self.contact_repository.get_by_id(
            database_session, contact_id, organization_id
        )
        if contact is None:
            raise DealReferenceNotFoundError
        return contact

    def _require_pipeline(
        self, database_session: Session, organization_id: UUID, pipeline_id: UUID
    ) -> Pipeline:
        pipeline = self.pipeline_repository.get_by_id(
            database_session, pipeline_id, organization_id
        )
        if pipeline is None:
            raise DealReferenceNotFoundError
        return pipeline

    def _require_stage(
        self, database_session: Session, organization_id: UUID, stage_id: UUID
    ) -> PipelineStage:
        stage = self.pipeline_repository.get_stage_by_id(
            database_session, stage_id, organization_id
        )
        if stage is None:
            raise DealReferenceNotFoundError
        return stage

    def _require_active_user(
        self, database_session: Session, organization_id: UUID, user_id: UUID
    ) -> None:
        user = self.user_repository.get_by_id(database_session, user_id, organization_id)
        if user is None or not user.is_active:
            raise DealReferenceNotFoundError

    @staticmethod
    def _updated_uuid(
        changes: dict[str, object], field_name: str, existing_value: UUID
    ) -> UUID:
        return cast(UUID, changes.get(field_name, existing_value))

    @staticmethod
    def _updated_optional_uuid(
        changes: dict[str, object], field_name: str, existing_value: UUID | None
    ) -> UUID | None:
        return cast(UUID | None, changes.get(field_name, existing_value))


deal_service = DealService(
    DealRepository(),
    CompanyRepository(),
    ContactRepository(),
    PipelineRepository(),
    UserRepository(),
    audit_service,
    assignment_notification_service,
)
