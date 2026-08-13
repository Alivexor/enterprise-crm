import unittest
from uuid import uuid4

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.base import Base
from app.models.activity import Activity
from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.pipeline import Pipeline
from app.models.role import Role
from app.models.task import Task
from app.models.user import User
from app.models.custom_field import CustomFieldDefinition
from app.models.dashboard import DashboardWidget
from app.models.revenue import Product, Quote, SalesGoal
from app.models.saved_view import SavedView
from app.models.sequence import SalesSequence, SalesSequenceEnrollment
from app.models.workflow import Workflow
from app.services.demo_seed import DemoDataService


class DemoSeedTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.organization_id = uuid4()
        self.settings = Settings(
            environment="development",
            database_url="sqlite://",
            default_organization_id=self.organization_id,
            default_admin_email="admin@example.com",
            default_admin_password="AdminPassword12345",
            default_admin_first_name="Admin",
            default_admin_last_name="User",
            jwt_secret="d" * 64,
        )
        self.engine = create_engine("sqlite://")

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.add(Organization(id=self.organization_id, name="Demo Org"))
            session.flush()
            session.add(
                User(
                    organization_id=self.organization_id,
                    email="admin@example.com",
                    password_hash="test-only-hash",
                    first_name="Admin",
                    last_name="User",
                )
            )
            session.commit()

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_demo_seed_is_dense_idempotent_and_reversible(self) -> None:
        service = DemoDataService(self.settings)
        with Session(self.engine) as session:
            first = service.seed(session)
            second = service.seed(session)
            self.assertEqual(first, second)
            self.assertEqual(first.users, 5)
            self.assertEqual(first.roles, 3)
            self.assertEqual(first.companies, 24)
            self.assertEqual(first.contacts, 36)
            self.assertEqual(first.leads, 32)
            self.assertEqual(first.pipelines, 2)
            self.assertEqual(first.pipeline_stages, 10)
            self.assertEqual(first.deals, 34)
            self.assertEqual(first.tasks, 40)
            self.assertEqual(first.activities, 42)
            self.assertEqual(first.notes, 30)
            self.assertEqual(first.tags, 10)
            self.assertEqual(first.notifications, 18)
            self.assertEqual(first.saved_views, 3)
            self.assertEqual(first.custom_fields, 4)
            self.assertEqual(first.workflows, 3)
            self.assertEqual(first.goals, 3)
            self.assertEqual(first.products, 4)
            self.assertEqual(first.quotes, 3)
            self.assertEqual(first.dashboard_widgets, 4)
            self.assertEqual(first.sequences, 2)
            self.assertEqual(first.sequence_enrollments, 4)

            self.assertEqual(session.scalar(select(func.count()).select_from(Company)), 24)
            self.assertEqual(session.scalar(select(func.count()).select_from(Contact)), 36)
            self.assertEqual(session.scalar(select(func.count()).select_from(Lead)), 32)
            self.assertEqual(session.scalar(select(func.count()).select_from(Pipeline)), 2)
            self.assertEqual(session.scalar(select(func.count()).select_from(Deal)), 34)
            self.assertEqual(session.scalar(select(func.count()).select_from(Task)), 40)
            self.assertEqual(session.scalar(select(func.count()).select_from(Activity)), 42)
            self.assertEqual(session.scalar(select(func.count()).select_from(Notification)), 18)
            self.assertEqual(session.scalar(select(func.count()).select_from(SavedView)), 3)
            self.assertEqual(session.scalar(select(func.count()).select_from(CustomFieldDefinition)), 4)
            self.assertEqual(session.scalar(select(func.count()).select_from(Workflow)), 3)
            self.assertEqual(session.scalar(select(func.count()).select_from(SalesGoal)), 3)
            self.assertEqual(session.scalar(select(func.count()).select_from(Product)), 4)
            self.assertEqual(session.scalar(select(func.count()).select_from(Quote)), 3)
            self.assertEqual(session.scalar(select(func.count()).select_from(DashboardWidget)), 4)
            self.assertEqual(session.scalar(select(func.count()).select_from(SalesSequence)), 2)
            self.assertEqual(session.scalar(select(func.count()).select_from(SalesSequenceEnrollment)), 4)

            cleared = service.clear(session)
            self.assertEqual(cleared.companies, 24)
            self.assertEqual(cleared.users, 5)
            self.assertEqual(cleared.roles, 3)
            self.assertEqual(cleared.saved_views, 3)
            self.assertEqual(cleared.sequences, 2)
            self.assertEqual(session.scalar(select(func.count()).select_from(Company)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(Deal)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(Task)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(Notification)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(SavedView)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(CustomFieldDefinition)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(Workflow)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(Quote)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(SalesSequence)), 0)
            # The real local admin is never removed by demo cleanup.
            self.assertEqual(session.scalar(select(func.count()).select_from(User)), 1)
            self.assertEqual(session.scalar(select(func.count()).select_from(Role)), 0)


if __name__ == "__main__":
    unittest.main()
