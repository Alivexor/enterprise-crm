import unittest
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.activity import Activity
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead import Lead
from app.models.organization import Organization
from app.models.user import User
from app.repositories.activity import ActivityRepository


class ActivityRepositoryFilterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_company_contact_and_lead_filters_are_organization_scoped(self) -> None:
        organization_id = uuid4()
        with Session(self.engine) as session:
            session.add(Organization(id=organization_id, name="Org"))
            session.flush()
            user = User(
                organization_id=organization_id,
                email="owner@example.com",
                password_hash="test",
                first_name="Owner",
                last_name="User",
            )
            first_company = Company(organization_id=organization_id, name="First")
            second_company = Company(organization_id=organization_id, name="Second")
            session.add_all([user, first_company, second_company])
            session.flush()
            contact = Contact(company_id=first_company.id, first_name="A", last_name="Contact")
            session.add(contact)
            session.flush()
            lead = Lead(
                organization_id=organization_id,
                company_id=first_company.id,
                contact_id=contact.id,
                title="Lead",
                description=None,
                source="website",
                status="new",
                assigned_user_id=user.id,
            )
            session.add(lead)
            session.flush()
            session.add_all([
                Activity(
                    organization_id=organization_id,
                    user_id=user.id,
                    company_id=first_company.id,
                    contact_id=contact.id,
                    lead_id=lead.id,
                    type="meeting",
                    title="Matched",
                    completed=False,
                ),
                Activity(
                    organization_id=organization_id,
                    user_id=user.id,
                    company_id=second_company.id,
                    type="call",
                    title="Other",
                    completed=False,
                ),
            ])
            session.commit()

            repository = ActivityRepository()
            items, total = repository.list_by_organization(
                session,
                organization_id,
                page=1,
                page_size=25,
                activity_type=None,
                completed=False,
                user_id=None,
                company_id=first_company.id,
                contact_id=contact.id,
                lead_id=lead.id,
                sort_by="created_at",
                sort_direction="asc",
            )
            self.assertEqual(total, 1)
            self.assertEqual([item.title for item in items], ["Matched"])


if __name__ == "__main__":
    unittest.main()
