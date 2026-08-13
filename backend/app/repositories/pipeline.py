"""Persistence operations for pipelines and their stages."""

from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineStageCreate,
    PipelineStageUpdate,
    PipelineUpdate,
)


class PipelineRepository:
    """Database access for organization-scoped pipelines and their stages."""

    def create(
        self,
        database_session: Session,
        organization_id: UUID,
        pipeline_data: PipelineCreate,
    ) -> Pipeline:
        pipeline = Pipeline(organization_id=organization_id, **pipeline_data.model_dump())
        database_session.add(pipeline)
        database_session.flush()
        return pipeline

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Pipeline], int]:
        where_clauses = [Pipeline.organization_id == organization_id]
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(
                or_(
                    func.lower(Pipeline.name).like(pattern),
                    func.lower(Pipeline.description).like(pattern),
                )
            )

        ordering = {
            "name": Pipeline.name,
            "created_at": Pipeline.created_at,
            "updated_at": Pipeline.updated_at,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement: Select[tuple[Pipeline]] = (
            select(Pipeline)
            .where(*where_clauses)
            .order_by(order_expression, Pipeline.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Pipeline.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def get_by_id(
        self,
        database_session: Session,
        pipeline_id: UUID,
        organization_id: UUID,
        *,
        include_stages: bool = False,
    ) -> Pipeline | None:
        statement = select(Pipeline).where(
            Pipeline.id == pipeline_id,
            Pipeline.organization_id == organization_id,
        )
        if include_stages:
            statement = statement.options(selectinload(Pipeline.stages))
        return database_session.scalar(statement)

    def update(
        self,
        database_session: Session,
        pipeline: Pipeline,
        pipeline_data: PipelineUpdate,
    ) -> Pipeline:
        for field_name, value in pipeline_data.model_dump(exclude_unset=True).items():
            setattr(pipeline, field_name, value)
        database_session.flush()
        return pipeline

    def delete(self, database_session: Session, pipeline: Pipeline) -> None:
        database_session.delete(pipeline)
        database_session.flush()

    def create_stage(
        self,
        database_session: Session,
        pipeline_id: UUID,
        stage_data: PipelineStageCreate,
    ) -> PipelineStage:
        stage = PipelineStage(pipeline_id=pipeline_id, **stage_data.model_dump())
        database_session.add(stage)
        database_session.flush()
        return stage

    def list_stages(
        self,
        database_session: Session,
        pipeline_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[PipelineStage], int]:
        where_clauses = [PipelineStage.pipeline_id == pipeline_id]
        if search:
            where_clauses.append(
                func.lower(PipelineStage.name).like(f"%{search.lower()}%")
            )

        ordering = {
            "order": PipelineStage.order,
            "name": PipelineStage.name,
            "probability": PipelineStage.probability,
            "created_at": PipelineStage.created_at,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement: Select[tuple[PipelineStage]] = (
            select(PipelineStage)
            .where(*where_clauses)
            .order_by(order_expression, PipelineStage.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(PipelineStage.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def get_stage_by_id(
        self,
        database_session: Session,
        stage_id: UUID,
        organization_id: UUID,
    ) -> PipelineStage | None:
        statement = (
            select(PipelineStage)
            .join(PipelineStage.pipeline)
            .where(
                PipelineStage.id == stage_id,
                Pipeline.organization_id == organization_id,
            )
        )
        return database_session.scalar(statement)

    def update_stage(
        self,
        database_session: Session,
        stage: PipelineStage,
        stage_data: PipelineStageUpdate,
    ) -> PipelineStage:
        for field_name, value in stage_data.model_dump(exclude_unset=True).items():
            setattr(stage, field_name, value)
        database_session.flush()
        return stage

    def delete_stage(self, database_session: Session, stage: PipelineStage) -> None:
        database_session.delete(stage)
        database_session.flush()
