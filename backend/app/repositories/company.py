from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyRepository:
    def create(
        self,
        database_session: Session,
        organization_id: UUID,
        company_data: CompanyCreate,
    ) -> Company:
        company = Company(
            organization_id=organization_id,
            **company_data.model_dump(),
        )
        database_session.add(company)
        database_session.flush()
        return company

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        industry: str | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Company], int]:
        where_clauses = [Company.organization_id == organization_id]
        if search:
            pattern = f"%{search.lower()}%"
            where_clauses.append(
                or_(
                    func.lower(Company.name).like(pattern),
                    func.lower(Company.website).like(pattern),
                    func.lower(Company.industry).like(pattern),
                )
            )
        if industry:
            where_clauses.append(func.lower(Company.industry) == industry.lower())
        ordering = {
            "name": Company.name,
            "created_at": Company.created_at,
            "updated_at": Company.updated_at,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement = (
            select(Company)
            .where(*where_clauses)
            .order_by(order_expression, Company.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count(Company.id)).where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def get_by_id(
        self,
        database_session: Session,
        company_id: UUID,
        organization_id: UUID,
    ) -> Company | None:
        statement = select(Company).where(
            Company.id == company_id,
            Company.organization_id == organization_id,
        )
        return database_session.scalar(statement)

    def update(
        self,
        database_session: Session,
        company: Company,
        company_data: CompanyUpdate,
    ) -> Company:
        for field_name, value in company_data.model_dump(exclude_unset=True).items():
            setattr(company, field_name, value)
        database_session.flush()
        return company

    def delete(self, database_session: Session, company: Company) -> None:
        database_session.delete(company)
        database_session.flush()

    def has_contacts(self, database_session: Session, company_id: UUID) -> bool:
        statement = select(select(Contact.id).where(Contact.company_id == company_id).exists())
        return bool(database_session.scalar(statement))
