from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.task import Task


class TaskRepository:
    def create(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        assigned_user_id: UUID,
        data: dict[str, object],
    ) -> Task:
        task = Task(
            organization_id=organization_id,
            assigned_user_id=assigned_user_id,
            **data,
        )
        database_session.add(task)
        database_session.flush()
        return task

    def get_by_id(
        self, database_session: Session, organization_id: UUID, task_id: UUID
    ) -> Task | None:
        return database_session.scalar(
            select(Task).where(Task.id == task_id, Task.organization_id == organization_id)
        )

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        assigned_user_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Task], int]:
        where_clauses = [Task.organization_id == organization_id]
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(
                or_(
                    func.lower(Task.title).like(pattern),
                    func.lower(Task.description).like(pattern),
                )
            )
        if status is not None:
            where_clauses.append(Task.status == status)
        if assigned_user_id is not None:
            where_clauses.append(Task.assigned_user_id == assigned_user_id)
        ordering = {"due_date": Task.due_date, "created_at": Task.created_at, "priority": Task.priority}[sort_by]
        order_expression = ordering.desc() if sort_direction == "desc" else ordering.asc()
        statement = (
            select(Task)
            .where(*where_clauses)
            .order_by(order_expression, Task.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Task.id)).where(*where_clauses)
        return list(database_session.scalars(statement)), int(database_session.scalar(count_statement) or 0)

    def update(self, database_session: Session, task: Task, data: dict[str, object]) -> Task:
        for field_name, value in data.items():
            setattr(task, field_name, value)
        database_session.flush()
        return task

    def delete(self, database_session: Session, task: Task) -> None:
        database_session.delete(task)
        database_session.flush()
