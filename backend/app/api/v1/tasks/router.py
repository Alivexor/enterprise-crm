from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.common import PageMetadata, PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskStatus, TaskUpdate
from app.security.permissions import require_permissions
from app.services.task import TaskNotFoundError, task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])
DatabaseSession = Annotated[Session, Depends(get_db)]
TaskReader = Annotated[User, Depends(require_permissions("tasks.read"))]
TaskCreator = Annotated[User, Depends(require_permissions("tasks.create"))]
TaskEditor = Annotated[User, Depends(require_permissions("tasks.update"))]
TaskDeleter = Annotated[User, Depends(require_permissions("tasks.delete"))]


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    database_session: DatabaseSession,
    current_user: TaskCreator,
) -> TaskResponse:
    try:
        task = task_service.create_task(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            task_data=task_data,
        )
    except TaskNotFoundError as exc:
        raise _not_found() from exc
    return TaskResponse.model_validate(task)


@router.get("", response_model=PaginatedResponse[TaskResponse])
def list_tasks(
    database_session: DatabaseSession,
    current_user: TaskReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    assigned_user_id: UUID | None = None,
    sort_by: Literal["due_date", "created_at", "priority"] = "due_date",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> PaginatedResponse[TaskResponse]:
    tasks, total = task_service.list_tasks(
        database_session,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        assigned_user_id=assigned_user_id,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return PaginatedResponse(
        items=[TaskResponse.model_validate(task) for task in tasks],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    database_session: DatabaseSession,
    current_user: TaskReader,
) -> TaskResponse:
    try:
        task = task_service.get_task(
            database_session, organization_id=current_user.organization_id, task_id=task_id
        )
    except TaskNotFoundError as exc:
        raise _not_found() from exc
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    database_session: DatabaseSession,
    current_user: TaskEditor,
) -> TaskResponse:
    try:
        task = task_service.update_task(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            task_id=task_id,
            task_data=task_data,
        )
    except TaskNotFoundError as exc:
        raise _not_found() from exc
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    database_session: DatabaseSession,
    current_user: TaskDeleter,
) -> Response:
    try:
        task_service.delete_task(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            task_id=task_id,
        )
    except TaskNotFoundError as exc:
        raise _not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
