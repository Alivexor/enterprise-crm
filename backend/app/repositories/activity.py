from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.activity import Activity


class ActivityRepository:
    def create(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        user_id: UUID,
        data: dict[str, object],
    ) -> Activity:
        activity = Activity(organization_id=organization_id, user_id=user_id, **data)
        database_session.add(activity)
        database_session.flush()
        return activity

    def get_by_id(
        self, database_session: Session, organization_id: UUID, activity_id: UUID
    ) -> Activity | None:
        return database_session.scalar(
            select(Activity).where(
                Activity.id == activity_id, Activity.organization_id == organization_id
            )
        )

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
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
        where_clauses = [Activity.organization_id == organization_id]
        if activity_type is not None:
            where_clauses.append(Activity.type == activity_type)
        if completed is not None:
            where_clauses.append(Activity.completed == completed)
        if user_id is not None:
            where_clauses.append(Activity.user_id == user_id)
        if company_id is not None:
            where_clauses.append(Activity.company_id == company_id)
        if contact_id is not None:
            where_clauses.append(Activity.contact_id == contact_id)
        if lead_id is not None:
            where_clauses.append(Activity.lead_id == lead_id)
        ordering = {"due_date": Activity.due_date, "created_at": Activity.created_at, "type": Activity.type}[sort_by]
        order_expression = ordering.desc() if sort_direction == "desc" else ordering.asc()
        statement = (
            select(Activity)
            .where(*where_clauses)
            .order_by(order_expression, Activity.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Activity.id)).where(*where_clauses)
        return list(database_session.scalars(statement)), int(database_session.scalar(count_statement) or 0)

    def update(
        self, database_session: Session, activity: Activity, data: dict[str, object]
    ) -> Activity:
        for field_name, value in data.items():
            setattr(activity, field_name, value)
        database_session.flush()
        return activity

    def delete(self, database_session: Session, activity: Activity) -> None:
        database_session.delete(activity)
        database_session.flush()
