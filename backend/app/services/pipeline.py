"""Use cases for sales pipelines and pipeline stages."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.repositories.pipeline import PipelineRepository
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineStageCreate,
    PipelineStageUpdate,
    PipelineUpdate,
)
from app.services.audit import AuditService, audit_service


class PipelineNotFoundError(Exception):
    """Raised when a pipeline is outside the caller's organization scope."""


class PipelineStageNotFoundError(Exception):
    """Raised when a pipeline stage is outside the requested pipeline scope."""


class PipelineConflictError(Exception):
    """Raised when a pipeline violates a uniqueness constraint."""


class PipelineStageConflictError(Exception):
    """Raised when a stage violates a uniqueness constraint within its pipeline."""


class PipelineDeletionConflictError(Exception):
    """Raised when a pipeline cannot be removed while dependent records exist."""


class PipelineStageDeletionConflictError(Exception):
    """Raised when a stage cannot be removed while dependent deals exist."""


class PipelineService:
    def __init__(
        self,
        pipeline_repository: PipelineRepository,
        audit_service: AuditService,
    ) -> None:
        self.pipeline_repository = pipeline_repository
        self.audit_service = audit_service

    def create_pipeline(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        pipeline_data: PipelineCreate,
    ) -> Pipeline:
        try:
            pipeline = self.pipeline_repository.create(
                database_session, organization_id, pipeline_data
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="pipeline.created",
                entity_type="pipeline",
                entity_id=pipeline.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise PipelineConflictError from exc
        return self.get_pipeline(
            database_session,
            organization_id=organization_id,
            pipeline_id=pipeline.id,
        )

    def list_pipelines(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Pipeline], int]:
        normalized_search = search.strip() if search is not None else None
        return self.pipeline_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=normalized_search or None,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_pipeline(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        pipeline_id: UUID,
    ) -> Pipeline:
        pipeline = self.pipeline_repository.get_by_id(
            database_session,
            pipeline_id,
            organization_id,
            include_stages=True,
        )
        if pipeline is None:
            raise PipelineNotFoundError
        pipeline.stages.sort(key=lambda stage: (stage.order, str(stage.id)))
        return pipeline

    def update_pipeline(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        pipeline_id: UUID,
        pipeline_data: PipelineUpdate,
    ) -> Pipeline:
        pipeline = self._require_pipeline(database_session, organization_id, pipeline_id)
        try:
            self.pipeline_repository.update(database_session, pipeline, pipeline_data)
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="pipeline.updated",
                entity_type="pipeline",
                entity_id=pipeline.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise PipelineConflictError from exc
        return self.get_pipeline(
            database_session,
            organization_id=organization_id,
            pipeline_id=pipeline_id,
        )

    def delete_pipeline(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        pipeline_id: UUID,
    ) -> None:
        pipeline = self._require_pipeline(database_session, organization_id, pipeline_id)
        try:
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="pipeline.deleted",
                entity_type="pipeline",
                entity_id=pipeline.id,
            )
            self.pipeline_repository.delete(database_session, pipeline)
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise PipelineDeletionConflictError from exc

    def create_stage(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        pipeline_id: UUID,
        stage_data: PipelineStageCreate,
    ) -> PipelineStage:
        self._require_pipeline(database_session, organization_id, pipeline_id)
        try:
            stage = self.pipeline_repository.create_stage(
                database_session, pipeline_id, stage_data
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="pipeline_stage.created",
                entity_type="pipeline_stage",
                entity_id=stage.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise PipelineStageConflictError from exc
        return self.get_stage(
            database_session,
            organization_id=organization_id,
            pipeline_id=pipeline_id,
            stage_id=stage.id,
        )

    def list_stages(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        pipeline_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[PipelineStage], int]:
        self._require_pipeline(database_session, organization_id, pipeline_id)
        normalized_search = search.strip() if search is not None else None
        return self.pipeline_repository.list_stages(
            database_session,
            pipeline_id,
            page=page,
            page_size=page_size,
            search=normalized_search or None,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_stage(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        pipeline_id: UUID,
        stage_id: UUID,
    ) -> PipelineStage:
        self._require_pipeline(database_session, organization_id, pipeline_id)
        stage = self.pipeline_repository.get_stage_by_id(
            database_session, stage_id, organization_id
        )
        if stage is None or stage.pipeline_id != pipeline_id:
            raise PipelineStageNotFoundError
        return stage

    def update_stage(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        pipeline_id: UUID,
        stage_id: UUID,
        stage_data: PipelineStageUpdate,
    ) -> PipelineStage:
        stage = self.get_stage(
            database_session,
            organization_id=organization_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )
        try:
            self.pipeline_repository.update_stage(database_session, stage, stage_data)
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="pipeline_stage.updated",
                entity_type="pipeline_stage",
                entity_id=stage.id,
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise PipelineStageConflictError from exc
        return self.get_stage(
            database_session,
            organization_id=organization_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )

    def delete_stage(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        pipeline_id: UUID,
        stage_id: UUID,
    ) -> None:
        stage = self.get_stage(
            database_session,
            organization_id=organization_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )
        try:
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="pipeline_stage.deleted",
                entity_type="pipeline_stage",
                entity_id=stage.id,
            )
            self.pipeline_repository.delete_stage(database_session, stage)
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise PipelineStageDeletionConflictError from exc

    def _require_pipeline(
        self,
        database_session: Session,
        organization_id: UUID,
        pipeline_id: UUID,
    ) -> Pipeline:
        pipeline = self.pipeline_repository.get_by_id(
            database_session, pipeline_id, organization_id
        )
        if pipeline is None:
            raise PipelineNotFoundError
        return pipeline


pipeline_service = PipelineService(PipelineRepository(), audit_service)
