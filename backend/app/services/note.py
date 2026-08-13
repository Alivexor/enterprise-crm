from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.note import Note
from app.repositories.note import NoteRepository
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.audit import AuditService, audit_service
from app.services.references import (
    OrganizationReferenceService,
    ReferenceNotFoundError,
    reference_service,
)


class NoteNotFoundError(Exception):
    """Raised when a note or its referenced record is outside the organization."""


class NoteService:
    def __init__(
        self,
        note_repository: NoteRepository,
        reference_service: OrganizationReferenceService,
        audit_service: AuditService,
    ) -> None:
        self.note_repository = note_repository
        self.reference_service = reference_service
        self.audit_service = audit_service

    def create_note(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        note_data: NoteCreate,
    ) -> Note:
        data = note_data.model_dump()
        self._validate_references(database_session, organization_id, data)
        try:
            note = self.note_repository.create(
                database_session,
                organization_id=organization_id,
                user_id=actor_id,
                data=data,
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="note.created",
                entity_type="note",
                entity_id=note.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise NoteNotFoundError from exc
        return note

    def list_notes(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        company_id: UUID | None,
        contact_id: UUID | None,
        lead_id: UUID | None,
        user_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Note], int]:
        self._validate_references(
            database_session,
            organization_id,
            {
                "company_id": company_id,
                "contact_id": contact_id,
                "lead_id": lead_id,
            },
        )
        if user_id is not None:
            self._require_user(database_session, organization_id, user_id)
        return self.note_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            company_id=company_id,
            contact_id=contact_id,
            lead_id=lead_id,
            user_id=user_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_note(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        note_id: UUID,
    ) -> Note:
        note = self.note_repository.get_by_id(
            database_session, organization_id, note_id
        )
        if note is None:
            raise NoteNotFoundError
        return note

    def update_note(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        note_id: UUID,
        note_data: NoteUpdate,
    ) -> Note:
        note = self.get_note(
            database_session, organization_id=organization_id, note_id=note_id
        )
        data = note_data.model_dump(exclude_unset=True)
        self._validate_references(
            database_session,
            organization_id,
            {
                "company_id": data.get("company_id", note.company_id),
                "contact_id": data.get("contact_id", note.contact_id),
                "lead_id": data.get("lead_id", note.lead_id),
            },
        )
        try:
            self.note_repository.update(database_session, note, data)
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="note.updated",
                entity_type="note",
                entity_id=note.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise NoteNotFoundError from exc
        return note

    def delete_note(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        note_id: UUID,
    ) -> None:
        note = self.get_note(
            database_session, organization_id=organization_id, note_id=note_id
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="note.deleted",
            entity_type="note",
            entity_id=note.id,
        )
        self.note_repository.delete(database_session, note)
        database_session.commit()

    def _validate_references(
        self,
        database_session: Session,
        organization_id: UUID,
        values: dict[str, UUID | None],
    ) -> None:
        try:
            company_id = values.get("company_id")
            if company_id is not None:
                self.reference_service.require_company(
                    database_session, organization_id, company_id
                )
            contact_id = values.get("contact_id")
            if contact_id is not None:
                self.reference_service.get_contact(
                    database_session, organization_id, contact_id
                )
            lead_id = values.get("lead_id")
            if lead_id is not None:
                self.reference_service.get_lead(
                    database_session, organization_id, lead_id
                )
        except ReferenceNotFoundError as exc:
            raise NoteNotFoundError from exc

    def _require_user(
        self, database_session: Session, organization_id: UUID, user_id: UUID
    ) -> None:
        try:
            self.reference_service.require_user(database_session, organization_id, user_id)
        except ReferenceNotFoundError as exc:
            raise NoteNotFoundError from exc


note_service = NoteService(NoteRepository(), reference_service, audit_service)
