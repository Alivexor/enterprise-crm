from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.tag import Tag
from app.schemas.tag import TaggableEntityType

TaggableEntity = Company | Contact | Lead | Deal


class TagRepository:
    """Database access for tags and their organization-scoped assignments."""

    def create(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        data: dict[str, object],
    ) -> Tag:
        tag = Tag(organization_id=organization_id, **data)
        database_session.add(tag)
        database_session.flush()
        return tag

    def get_by_id(
        self,
        database_session: Session,
        organization_id: UUID,
        tag_id: UUID,
    ) -> Tag | None:
        return database_session.scalar(
            select(Tag).where(
                Tag.id == tag_id,
                Tag.organization_id == organization_id,
            )
        )

    def list_by_organization(
        self,
        database_session: Session,
        organization_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        entity_type: TaggableEntityType | None,
        entity_id: UUID | None,
        sort_by: str,
        sort_direction: str,
    ) -> tuple[list[Tag], int]:
        where_clauses = [Tag.organization_id == organization_id]
        if search:
            where_clauses.append(func.lower(Tag.name).like(f"%{search.lower()}%"))

        statement = select(Tag)
        count_statement = select(func.count(Tag.id))
        if entity_type == "company":
            statement = statement.join(Tag.companies).where(Company.id == entity_id)
            count_statement = count_statement.join(Tag.companies).where(
                Company.id == entity_id
            )
        elif entity_type == "contact":
            statement = statement.join(Tag.contacts).where(Contact.id == entity_id)
            count_statement = count_statement.join(Tag.contacts).where(
                Contact.id == entity_id
            )
        elif entity_type == "lead":
            statement = statement.join(Tag.leads).where(Lead.id == entity_id)
            count_statement = count_statement.join(Tag.leads).where(Lead.id == entity_id)
        elif entity_type == "deal":
            statement = statement.join(Tag.deals).where(Deal.id == entity_id)
            count_statement = count_statement.join(Tag.deals).where(Deal.id == entity_id)

        ordering = {
            "name": Tag.name,
            "created_at": Tag.created_at,
        }[sort_by]
        order_expression = (
            ordering.desc() if sort_direction == "desc" else ordering.asc()
        )
        statement = (
            statement.where(*where_clauses)
            .order_by(order_expression, Tag.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = count_statement.where(*where_clauses)
        return (
            list(database_session.scalars(statement)),
            int(database_session.scalar(count_statement) or 0),
        )

    def get_taggable_entity(
        self,
        database_session: Session,
        organization_id: UUID,
        entity_type: TaggableEntityType,
        entity_id: UUID,
    ) -> TaggableEntity | None:
        if entity_type == "company":
            return database_session.scalar(
                select(Company).where(
                    Company.id == entity_id,
                    Company.organization_id == organization_id,
                )
            )
        if entity_type == "contact":
            return database_session.scalar(
                select(Contact)
                .join(Contact.company)
                .where(
                    Contact.id == entity_id,
                    Company.organization_id == organization_id,
                )
            )
        if entity_type == "lead":
            return database_session.scalar(
                select(Lead).where(
                    Lead.id == entity_id,
                    Lead.organization_id == organization_id,
                )
            )
        return database_session.scalar(
            select(Deal).where(
                Deal.id == entity_id,
                Deal.organization_id == organization_id,
            )
        )

    def assign(self, database_session: Session, tag: Tag, target: TaggableEntity) -> bool:
        if tag in target.tags:
            return False
        target.tags.append(tag)
        database_session.flush()
        return True

    def unassign(
        self,
        database_session: Session,
        tag: Tag,
        target: TaggableEntity,
    ) -> bool:
        if tag not in target.tags:
            return False
        target.tags.remove(tag)
        database_session.flush()
        return True

    def update(
        self,
        database_session: Session,
        tag: Tag,
        data: dict[str, object],
    ) -> Tag:
        for field_name, value in data.items():
            setattr(tag, field_name, value)
        database_session.flush()
        return tag

    def delete(self, database_session: Session, tag: Tag) -> None:
        database_session.delete(tag)
        database_session.flush()
