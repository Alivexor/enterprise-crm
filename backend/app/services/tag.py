from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.tag import TagRepository, TaggableEntity
from app.schemas.tag import TagCreate, TagUpdate, TaggableEntityType
from app.services.audit import AuditService, audit_service


class TagNotFoundError(Exception):
    """Raised when a tag is unavailable in the active organization."""


class TagAssignmentTargetNotFoundError(Exception):
    """Raised when a requested tag target is outside the active organization."""


class TagAlreadyExistsError(Exception):
    """Raised when a tag name conflicts within an organization."""


class TagFilterError(Exception):
    """Raised when a tag list filter is incomplete."""


class TagService:
    def __init__(
        self,
        tag_repository: TagRepository,
        audit_service: AuditService,
    ) -> None:
        self.tag_repository = tag_repository
        self.audit_service = audit_service

    def create_tag(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        tag_data: TagCreate,
    ) -> Tag:
        try:
            tag = self.tag_repository.create(
                database_session,
                organization_id=organization_id,
                data=tag_data.model_dump(),
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="tag.created",
                entity_type="tag",
                entity_id=tag.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise TagAlreadyExistsError from exc
        return tag

    def list_tags(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        entity_type: TaggableEntityType | None,
        entity_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Tag], int]:
        if (entity_type is None) != (entity_id is None):
            raise TagFilterError(
                "entity_type and entity_id must be provided together"
            )
        if entity_type is not None and entity_id is not None:
            self._get_assignment_target(
                database_session, organization_id, entity_type, entity_id
            )
        return self.tag_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            entity_type=entity_type,
            entity_id=entity_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_tag(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        tag_id: UUID,
    ) -> Tag:
        tag = self.tag_repository.get_by_id(database_session, organization_id, tag_id)
        if tag is None:
            raise TagNotFoundError
        return tag

    def update_tag(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        tag_id: UUID,
        tag_data: TagUpdate,
    ) -> Tag:
        tag = self.get_tag(
            database_session, organization_id=organization_id, tag_id=tag_id
        )
        try:
            self.tag_repository.update(
                database_session, tag, tag_data.model_dump(exclude_unset=True)
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="tag.updated",
                entity_type="tag",
                entity_id=tag.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise TagAlreadyExistsError from exc
        return tag

    def delete_tag(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        tag_id: UUID,
    ) -> None:
        tag = self.get_tag(
            database_session, organization_id=organization_id, tag_id=tag_id
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="tag.deleted",
            entity_type="tag",
            entity_id=tag.id,
        )
        self.tag_repository.delete(database_session, tag)
        database_session.commit()

    def assign_tag(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        tag_id: UUID,
        entity_type: TaggableEntityType,
        entity_id: UUID,
    ) -> None:
        tag = self.get_tag(
            database_session, organization_id=organization_id, tag_id=tag_id
        )
        target = self._get_assignment_target(
            database_session, organization_id, entity_type, entity_id
        )
        if self.tag_repository.assign(database_session, tag, target):
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="tag.assigned",
                entity_type="tag",
                entity_id=tag.id,
            )
            database_session.commit()

    def unassign_tag(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        tag_id: UUID,
        entity_type: TaggableEntityType,
        entity_id: UUID,
    ) -> None:
        tag = self.get_tag(
            database_session, organization_id=organization_id, tag_id=tag_id
        )
        target = self._get_assignment_target(
            database_session, organization_id, entity_type, entity_id
        )
        if self.tag_repository.unassign(database_session, tag, target):
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="tag.unassigned",
                entity_type="tag",
                entity_id=tag.id,
            )
            database_session.commit()

    def _get_assignment_target(
        self,
        database_session: Session,
        organization_id: UUID,
        entity_type: TaggableEntityType,
        entity_id: UUID,
    ) -> TaggableEntity:
        target = self.tag_repository.get_taggable_entity(
            database_session, organization_id, entity_type, entity_id
        )
        if target is None:
            raise TagAssignmentTargetNotFoundError
        return target


tag_service = TagService(TagRepository(), audit_service)
