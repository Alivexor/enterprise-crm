from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.activity import Activity
from app.models.note import Note
from app.models.task import Task


class SearchRepository:
    def search_companies(
        self, database_session: Session, organization_id: UUID, query: str, limit: int
    ) -> list[Company]:
        pattern = f"%{query.lower()}%"
        statement = (
            select(Company)
            .where(
                Company.organization_id == organization_id,
                or_(
                    func.lower(Company.name).like(pattern),
                    func.lower(Company.industry).like(pattern),
                ),
            )
            .order_by(Company.name.asc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def search_contacts(
        self, database_session: Session, organization_id: UUID, query: str, limit: int
    ) -> list[Contact]:
        pattern = f"%{query.lower()}%"
        statement = (
            select(Contact)
            .join(Contact.company)
            .where(
                Company.organization_id == organization_id,
                or_(
                    func.lower(Contact.first_name).like(pattern),
                    func.lower(Contact.last_name).like(pattern),
                    func.lower(Contact.email).like(pattern),
                ),
            )
            .order_by(Contact.last_name.asc(), Contact.first_name.asc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def search_leads(
        self, database_session: Session, organization_id: UUID, query: str, limit: int
    ) -> list[Lead]:
        pattern = f"%{query.lower()}%"
        statement = (
            select(Lead)
            .where(
                Lead.organization_id == organization_id,
                or_(
                    func.lower(Lead.title).like(pattern),
                    func.lower(Lead.description).like(pattern),
                ),
            )
            .order_by(Lead.updated_at.desc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def search_deals(
        self, database_session: Session, organization_id: UUID, query: str, limit: int
    ) -> list[Deal]:
        pattern = f"%{query.lower()}%"
        statement = (
            select(Deal)
            .where(
                Deal.organization_id == organization_id,
                func.lower(Deal.title).like(pattern),
            )
            .order_by(Deal.updated_at.desc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def search_tasks(
        self, database_session: Session, organization_id: UUID, query: str, limit: int
    ) -> list[Task]:
        pattern = f"%{query.lower()}%"
        statement = (
            select(Task)
            .where(
                Task.organization_id == organization_id,
                or_(
                    func.lower(Task.title).like(pattern),
                    func.lower(Task.description).like(pattern),
                ),
            )
            .order_by(Task.updated_at.desc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def search_activities(
        self, database_session: Session, organization_id: UUID, query: str, limit: int
    ) -> list[Activity]:
        pattern = f"%{query.lower()}%"
        statement = (
            select(Activity)
            .where(
                Activity.organization_id == organization_id,
                or_(
                    func.lower(Activity.title).like(pattern),
                    func.lower(Activity.description).like(pattern),
                ),
            )
            .order_by(Activity.created_at.desc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def search_notes(
        self, database_session: Session, organization_id: UUID, query: str, limit: int
    ) -> list[Note]:
        pattern = f"%{query.lower()}%"
        statement = (
            select(Note)
            .where(
                Note.organization_id == organization_id,
                func.lower(Note.content).like(pattern),
            )
            .order_by(Note.updated_at.desc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))
