from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.schemas.import_export import CompanyImportRow, ContactImportRow


class ImportExportRepository:
    """Database access for organization-scoped CSV import and export operations."""

    def list_companies_for_export(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        limit: int,
    ) -> list[Company]:
        statement = (
            select(Company)
            .where(Company.organization_id == organization_id)
            .order_by(Company.name.asc(), Company.id.asc())
            .limit(limit)
        )
        return list(database_session.scalars(statement))

    def list_contacts_for_export(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        limit: int,
    ) -> list[tuple[Contact, Company]]:
        statement = (
            select(Contact, Company)
            .join(Contact.company)
            .where(Company.organization_id == organization_id)
            .order_by(
                Company.name.asc(),
                Contact.last_name.asc(),
                Contact.first_name.asc(),
                Contact.id.asc(),
            )
            .limit(limit)
        )
        return list(database_session.execute(statement).tuples())

    def get_companies_by_ids(
        self,
        database_session: Session,
        organization_id: UUID,
        company_ids: Iterable[UUID],
    ) -> dict[UUID, Company]:
        unique_ids = tuple(dict.fromkeys(company_ids))
        if not unique_ids:
            return {}
        statement = select(Company).where(
            Company.organization_id == organization_id,
            Company.id.in_(unique_ids),
        )
        return {
            company.id: company for company in database_session.scalars(statement)
        }

    def get_companies_by_normalized_names(
        self,
        database_session: Session,
        organization_id: UUID,
        names: Iterable[str],
    ) -> dict[str, list[Company]]:
        normalized_names = tuple(dict.fromkeys(name.lower() for name in names))
        if not normalized_names:
            return {}
        statement = select(Company).where(
            Company.organization_id == organization_id,
            func.lower(Company.name).in_(normalized_names),
        )
        companies_by_name: dict[str, list[Company]] = {}
        for company in database_session.scalars(statement):
            companies_by_name.setdefault(company.name.lower(), []).append(company)
        return companies_by_name

    def create_companies(
        self,
        database_session: Session,
        organization_id: UUID,
        rows: Iterable[CompanyImportRow],
    ) -> list[Company]:
        companies = [
            Company(
                organization_id=organization_id,
                name=row.name,
                website=row.website,
                industry=row.industry,
            )
            for row in rows
        ]
        database_session.add_all(companies)
        database_session.flush()
        return companies

    def create_contacts(
        self,
        database_session: Session,
        rows: Iterable[tuple[UUID, ContactImportRow]],
    ) -> list[Contact]:
        contacts = [
            Contact(
                company_id=company_id,
                first_name=row.first_name,
                last_name=row.last_name,
                email=str(row.email) if row.email is not None else None,
                phone=row.phone,
            )
            for company_id, row in rows
        ]
        database_session.add_all(contacts)
        database_session.flush()
        return contacts
