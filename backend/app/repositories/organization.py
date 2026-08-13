from uuid import UUID

from sqlalchemy.orm import Session

from app.models.organization import Organization


class OrganizationRepository:
    def get_by_id(
        self, database_session: Session, organization_id: UUID
    ) -> Organization | None:
        return database_session.get(Organization, organization_id)

    def exists(self, database_session: Session, organization_id: UUID) -> bool:
        return self.get_by_id(database_session, organization_id) is not None

    def create(
        self, database_session: Session, organization_id: UUID, name: str
    ) -> Organization:
        organization = Organization(id=organization_id, name=name)
        database_session.add(organization)
        database_session.flush()
        return organization

    def update(
        self, database_session: Session, organization: Organization, *, name: str
    ) -> Organization:
        organization.name = name
        database_session.flush()
        return organization
