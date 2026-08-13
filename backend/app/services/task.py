from uuid import UUID

from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.audit import AuditService, audit_service
from app.services.assignment_notifications import (
    AssignmentNotificationService,
    assignment_notification_service,
)
from app.services.references import (
    OrganizationReferenceService,
    ReferenceNotFoundError,
    reference_service,
)


class TaskNotFoundError(Exception):
    """Raised when a task is unavailable in the active organization."""


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        reference_service: OrganizationReferenceService,
        audit_service: AuditService,
        assignment_notification_service: AssignmentNotificationService,
    ) -> None:
        self.task_repository = task_repository
        self.reference_service = reference_service
        self.audit_service = audit_service
        self.assignment_notification_service = assignment_notification_service

    def create_task(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        task_data: TaskCreate,
    ) -> Task:
        data = task_data.model_dump()
        assigned_user_id = data.pop("assigned_user_id") or actor_id
        self._require_user(database_session, organization_id, assigned_user_id)
        task = self.task_repository.create(
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
            entity_type="task",
            entity_id=task.id,
            title=task.title,
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="task.created",
            entity_type="task",
            entity_id=task.id,
        )
        from app.services.v3_platform import v3_platform_service
        v3_platform_service.emit_event(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            event_type="task.created",
            entity_type="task",
            entity_id=task.id,
            payload={
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "assigned_user_id": str(task.assigned_user_id),
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
        )
        database_session.commit()
        return task

    def list_tasks(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        assigned_user_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Task], int]:
        return self.task_repository.list_by_organization(
            database_session,
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            assigned_user_id=assigned_user_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    def get_task(
        self, database_session: Session, *, organization_id: UUID, task_id: UUID
    ) -> Task:
        task = self.task_repository.get_by_id(database_session, organization_id, task_id)
        if task is None:
            raise TaskNotFoundError
        return task

    def update_task(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        task_id: UUID,
        task_data: TaskUpdate,
    ) -> Task:
        task = self.get_task(
            database_session, organization_id=organization_id, task_id=task_id
        )
        data = task_data.model_dump(exclude_unset=True)
        previous_assigned_user_id = task.assigned_user_id
        assigned_user_id = data.get("assigned_user_id", previous_assigned_user_id)
        self._require_user(database_session, organization_id, assigned_user_id)
        self.task_repository.update(database_session, task, data)
        if assigned_user_id != previous_assigned_user_id:
            self.assignment_notification_service.notify_assignee(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                recipient_id=assigned_user_id,
                entity_type="task",
                entity_id=task.id,
                title=task.title,
            )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="task.updated",
            entity_type="task",
            entity_id=task.id,
        )
        from app.services.v3_platform import v3_platform_service
        v3_platform_service.emit_event(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            event_type="task.updated",
            entity_type="task",
            entity_id=task.id,
            payload={
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "assigned_user_id": str(task.assigned_user_id),
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
        )
        database_session.commit()
        return task

    def delete_task(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        task_id: UUID,
    ) -> None:
        task = self.get_task(
            database_session, organization_id=organization_id, task_id=task_id
        )
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action="task.deleted",
            entity_type="task",
            entity_id=task.id,
        )
        self.task_repository.delete(database_session, task)
        database_session.commit()

    def _require_user(
        self, database_session: Session, organization_id: UUID, user_id: UUID
    ) -> None:
        try:
            self.reference_service.require_user(database_session, organization_id, user_id)
        except ReferenceNotFoundError as exc:
            raise TaskNotFoundError from exc


task_service = TaskService(
    TaskRepository(),
    reference_service,
    audit_service,
    assignment_notification_service,
)
