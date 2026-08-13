from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate


class ContactRepository:
    """Database access for contacts scoped through their parent company."""

    def create(self, database_session: Session, contact_data: ContactCreate) -> Contact:
        contact = Contact(**contact_data.model_dump())
        database_session.add(contact)
        database_session.flush()
        return contact

    def get_by_id(
        self,
        database_session: Session,
        contact_id: UUID,
        organization_id: UUID,
    ) -> Contact | None:
        statement = (
            select(Contact)
            .join(Contact.company)
            .where(Contact.id == contact_id, Company.organization_id == organization_id)
        )
        return database_session.scalar(statement)

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        company_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Contact], int]:
        where_clauses = [Company.organization_id == organization_id]
        if company_id is not None:
            where_clauses.append(Contact.company_id == company_id)
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(
                or_(
                    func.lower(Contact.first_name).like(pattern),
                    func.lower(Contact.last_name).like(pattern),
                    func.lower(Contact.email).like(pattern),
                )
            )

        ordering = {
            "first_name": Contact.first_name,
            "last_name": Contact.last_name,
            "email": Contact.email,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement: Select[tuple[Contact]] = (
            select(Contact)
            .join(Contact.company)
            .where(*where_clauses)
            .order_by(order_expression, Contact.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = (
            select(func.count(Contact.id)).join(Contact.company).where(*where_clauses)
        )
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def update(
        self,
        database_session: Session,
        contact: Contact,
        contact_data: ContactUpdate,
    ) -> Contact:
        for field_name, value in contact_data.model_dump(exclude_unset=True).items():
            setattr(contact, field_name, value)
        database_session.flush()
        return contact

    def delete(self, database_session: Session, contact: Contact) -> None:
        database_session.delete(contact)
        database_session.flush()
