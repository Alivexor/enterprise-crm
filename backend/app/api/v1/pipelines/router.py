from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineDetailResponse,
    PipelineResponse,
    PipelineStageCreate,
    PipelineStageResponse,
    PipelineStageUpdate,
    PipelineUpdate,
)
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.pipeline import (
    PipelineConflictError,
    PipelineDeletionConflictError,
    PipelineNotFoundError,
    PipelineStageConflictError,
    PipelineStageDeletionConflictError,
    PipelineStageNotFoundError,
    pipeline_service,
)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])
DatabaseSession = Annotated[Session, Depends(get_db)]
PipelineReader = Annotated[
    User, Depends(require_permissions(PermissionName.PIPELINES_READ))
]
PipelineCreator = Annotated[
    User, Depends(require_permissions(PermissionName.PIPELINES_CREATE))
]
PipelineEditor = Annotated[
    User, Depends(require_permissions(PermissionName.PIPELINES_UPDATE))
]
PipelineDeleter = Annotated[
    User, Depends(require_permissions(PermissionName.PIPELINES_DELETE))
]


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


@router.post("", response_model=PipelineDetailResponse, status_code=status.HTTP_201_CREATED)
def create_pipeline(
    pipeline_data: PipelineCreate,
    database_session: DatabaseSession,
    current_user: PipelineCreator,
) -> PipelineDetailResponse:
    try:
        pipeline = pipeline_service.create_pipeline(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            pipeline_data=pipeline_data,
        )
    except PipelineConflictError as exc:
        raise _conflict("A pipeline with this name already exists") from exc
    return PipelineDetailResponse.model_validate(pipeline)


@router.get("", response_model=PaginatedResponse[PipelineResponse])
def list_pipelines(
    database_session: DatabaseSession,
    current_user: PipelineReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    sort_by: Literal["name", "created_at", "updated_at"] = "name",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> PaginatedResponse[PipelineResponse]:
    pipelines, total = pipeline_service.list_pipelines(
        database_session,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return PaginatedResponse(
        items=[PipelineResponse.model_validate(pipeline) for pipeline in pipelines],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.post(
    "/{pipeline_id}/stages",
    response_model=PipelineStageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stage(
    pipeline_id: UUID,
    stage_data: PipelineStageCreate,
    database_session: DatabaseSession,
    current_user: PipelineCreator,
) -> PipelineStageResponse:
    try:
        stage = pipeline_service.create_stage(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            pipeline_id=pipeline_id,
            stage_data=stage_data,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    except PipelineStageConflictError as exc:
        raise _conflict("A pipeline stage already uses this order") from exc
    return PipelineStageResponse.model_validate(stage)


@router.get("/{pipeline_id}/stages", response_model=PaginatedResponse[PipelineStageResponse])
def list_stages(
    pipeline_id: UUID,
    database_session: DatabaseSession,
    current_user: PipelineReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    sort_by: Literal["order", "name", "probability", "created_at"] = "order",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> PaginatedResponse[PipelineStageResponse]:
    try:
        stages, total = pipeline_service.list_stages(
            database_session,
            organization_id=current_user.organization_id,
            pipeline_id=pipeline_id,
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    return PaginatedResponse(
        items=[PipelineStageResponse.model_validate(stage) for stage in stages],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{pipeline_id}/stages/{stage_id}", response_model=PipelineStageResponse)
def get_stage(
    pipeline_id: UUID,
    stage_id: UUID,
    database_session: DatabaseSession,
    current_user: PipelineReader,
) -> PipelineStageResponse:
    try:
        stage = pipeline_service.get_stage(
            database_session,
            organization_id=current_user.organization_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    except PipelineStageNotFoundError as exc:
        raise _not_found("Pipeline stage not found") from exc
    return PipelineStageResponse.model_validate(stage)


@router.patch("/{pipeline_id}/stages/{stage_id}", response_model=PipelineStageResponse)
def update_stage(
    pipeline_id: UUID,
    stage_id: UUID,
    stage_data: PipelineStageUpdate,
    database_session: DatabaseSession,
    current_user: PipelineEditor,
) -> PipelineStageResponse:
    try:
        stage = pipeline_service.update_stage(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            stage_data=stage_data,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    except PipelineStageNotFoundError as exc:
        raise _not_found("Pipeline stage not found") from exc
    except PipelineStageConflictError as exc:
        raise _conflict("A pipeline stage already uses this order") from exc
    return PipelineStageResponse.model_validate(stage)


@router.delete("/{pipeline_id}/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stage(
    pipeline_id: UUID,
    stage_id: UUID,
    database_session: DatabaseSession,
    current_user: PipelineDeleter,
) -> Response:
    try:
        pipeline_service.delete_stage(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    except PipelineStageNotFoundError as exc:
        raise _not_found("Pipeline stage not found") from exc
    except PipelineStageDeletionConflictError as exc:
        raise _conflict("Pipeline stage cannot be deleted while related deals exist") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{pipeline_id}", response_model=PipelineDetailResponse)
def get_pipeline(
    pipeline_id: UUID,
    database_session: DatabaseSession,
    current_user: PipelineReader,
) -> PipelineDetailResponse:
    try:
        pipeline = pipeline_service.get_pipeline(
            database_session,
            organization_id=current_user.organization_id,
            pipeline_id=pipeline_id,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    return PipelineDetailResponse.model_validate(pipeline)


@router.patch("/{pipeline_id}", response_model=PipelineDetailResponse)
def update_pipeline(
    pipeline_id: UUID,
    pipeline_data: PipelineUpdate,
    database_session: DatabaseSession,
    current_user: PipelineEditor,
) -> PipelineDetailResponse:
    try:
        pipeline = pipeline_service.update_pipeline(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            pipeline_id=pipeline_id,
            pipeline_data=pipeline_data,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    except PipelineConflictError as exc:
        raise _conflict("A pipeline with this name already exists") from exc
    return PipelineDetailResponse.model_validate(pipeline)


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(
    pipeline_id: UUID,
    database_session: DatabaseSession,
    current_user: PipelineDeleter,
) -> Response:
    try:
        pipeline_service.delete_pipeline(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            pipeline_id=pipeline_id,
        )
    except PipelineNotFoundError as exc:
        raise _not_found("Pipeline not found") from exc
    except PipelineDeletionConflictError as exc:
        raise _conflict("Pipeline cannot be deleted while related records exist") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
