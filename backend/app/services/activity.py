from uuid import UUID

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.repositories.activity import ActivityRepository
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.audit import AuditService, audit_service
from app.services.assignment_notifications import (
    AssignmentNotificationService,
    assignment_notification_service,
)
from app.services.references import (
    OrganizationReferenceService,
    ReferenceNotFoundError,
    ReferenceRelationshipError,
    reference_service,
)


class ActivityNotFoundError(Exception):
    """Raised when an activity or one of its references is unavailable."""


class ActivityReferenceError(Exception):
    """Raised when the supplied activity references conflict."""


class ActivityService:
    def __init__(
        self,
        activity_repository: ActivityRepository,
        reference_service: OrganizationReferenceService,
        audit_service: AuditService,
        assignment_notification_service: AssignmentNotificationService,
    ) -> None:
        self.activity_repository = activity_repository
        self.reference_service = reference_service
        self.audit_service = audit_service
        self.assignment_notification_service = assignment_notification_service

    def create_activity(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        activity_data: ActivityCreate,
    ) -> Activity:
        data = activity_data.model_dump()
        user_id = data.pop("user_id") or actor_id
        self._validate_references(database_session, organization_id, user_id, data)
        activity = self.activity_repository.create(
            database_session,
            organization_id=organization_id,
            user_id=user_id,
            data=data,
        )
        self.assignment_notification_service.notify_assignee(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            recipient_id=user_id,
            entity_type="activity",
            entity_id=activity.id,
            title=activity.title,
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="activity.created",
            entity_type="activity",
            entity_id=activity.id,
        )
        database_session.commit()
        return activity

    def list_activities(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        activity_type: str | None,
        completed: bool | None,
        user_id: UUID | None,
        company_id: UUID | None,
        contact_id: UUID | None,
        lead_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Activity], int]:
        return self.activity_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            activity_type=activity_type,
            completed=completed,
            user_id=user_id,
            company_id=company_id,
            contact_id=contact_id,
            lead_id=lead_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_activity(
        self, database_session: Session, *, organization_id: UUID, activity_id: UUID
    ) -> Activity:
        activity = self.activity_repository.get_by_id(
            database_session, organization_id, activity_id
        )
        if activity is None:
            raise ActivityNotFoundError
        return activity

    def update_activity(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        activity_id: UUID,
        activity_data: ActivityUpdate,
    ) -> Activity:
        activity = self.get_activity(
            database_session, organization_id=organization_id, activity_id=activity_id
        )
        data = activity_data.model_dump(exclude_unset=True)
        previous_user_id = activity.user_id
        user_id = data.get("user_id", previous_user_id)
        references = {
            "company_id": data.get("company_id", activity.company_id),
            "contact_id": data.get("contact_id", activity.contact_id),
            "lead_id": data.get("lead_id", activity.lead_id),
        }
        self._validate_references(database_session, organization_id, user_id, references)
        self.activity_repository.update(database_session, activity, data)
        if user_id != previous_user_id:
            self.assignment_notification_service.notify_assignee(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                recipient_id=user_id,
                entity_type="activity",
                entity_id=activity.id,
                title=activity.title,
            )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="activity.updated",
            entity_type="activity",
            entity_id=activity.id,
        )
        database_session.commit()
        return activity

    def delete_activity(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        activity_id: UUID,
    ) -> None:
        activity = self.get_activity(
            database_session, organization_id=organization_id, activity_id=activity_id
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="activity.deleted",
            entity_type="activity",
            entity_id=activity.id,
        )
        self.activity_repository.delete(database_session, activity)
        database_session.commit()

    def _validate_references(
        self,
        database_session: Session,
        organization_id: UUID,
        user_id: UUID,
        values: dict[str, object],
    ) -> None:
        try:
            self.reference_service.require_user(database_session, organization_id, user_id)
            company_id = values.get("company_id")
            contact_id = values.get("contact_id")
            self.reference_service.validate_company_contact(
                database_session,
                organization_id=organization_id,
                company_id=company_id if isinstance(company_id, UUID) else None,
                contact_id=contact_id if isinstance(contact_id, UUID) else None,
            )
            lead_id = values.get("lead_id")
            if isinstance(lead_id, UUID):
                self.reference_service.get_lead(database_session, organization_id, lead_id)
        except ReferenceNotFoundError as exc:
            raise ActivityNotFoundError from exc
        except ReferenceRelationshipError as exc:
            raise ActivityReferenceError(str(exc)) from exc


activity_service = ActivityService(
    ActivityRepository(),
    reference_service,
    audit_service,
    assignment_notification_service,
)
