import os
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite:///./placeholder.db")
os.environ.setdefault("DEFAULT_ORGANIZATION_ID", "00000000-0000-0000-0000-000000000001")
os.environ.setdefault("JWT_SECRET", "x" * 64)
os.environ.setdefault("ENVIRONMENT", "test")

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.base import Base
from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.developer import WebhookEndpoint
from app.models.lead import Lead
from app.models.organization import Organization
from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.models.task import Task
from app.models.user import User
from app.schemas.v3 import (
    ApiKeyCreate,
    QuoteApprovalRequest,
    WebhookCreate,
    CustomFieldDefinitionCreate,
    ProductCreate,
    QuoteCreate,
    QuoteItemInput,
    SavedViewCreate,
    WorkflowAction,
    WorkflowCondition,
    WorkflowCreate,
)
from app.services.v3_platform import V3PlatformService


class V3PlatformTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.temp.close()
        self.engine = create_engine(f"sqlite+pysqlite:///{Path(self.temp.name).as_posix()}")
        Base.metadata.create_all(self.engine)
        self.settings = Settings(
            environment="test",
            database_url=f"sqlite+pysqlite:///{Path(self.temp.name).as_posix()}",
            default_organization_id=uuid4(),
            jwt_secret="s" * 64,
            ollama_enabled=False,
        )
        self.service = V3PlatformService(self.settings)
        self.db = Session(self.engine)
        self.org = Organization(id=self.settings.default_organization_id, name="V3 Test")
        self.user = User(
            organization_id=self.org.id,
            email="owner@example.com",
            password_hash="not-used",
            first_name="Test",
            last_name="Owner",
            is_active=True,
        )
        self.db.add_all([self.org, self.user])
        self.db.flush()
        self.company = Company(organization_id=self.org.id, name="Acme", industry="SaaS")
        self.db.add(self.company)
        self.db.flush()
        self.contact = Contact(company_id=self.company.id, first_name="Ava", last_name="Stone", email="ava@example.com")
        self.pipeline = Pipeline(organization_id=self.org.id, name="Sales")
        self.db.add_all([self.contact, self.pipeline])
        self.db.flush()
        self.stage = PipelineStage(pipeline_id=self.pipeline.id, name="Qualified", order=1, probability=Decimal("60"))
        self.db.add(self.stage)
        self.db.flush()
        self.deal = Deal(
            organization_id=self.org.id,
            company_id=self.company.id,
            contact_id=self.contact.id,
            pipeline_id=self.pipeline.id,
            stage_id=self.stage.id,
            assigned_user_id=self.user.id,
            title="Expansion",
            value=Decimal("10000"),
            currency="USD",
            probability=Decimal("70"),
            expected_close_date=date.today() + timedelta(days=20),
            status="open",
        )
        self.lead = Lead(
            organization_id=self.org.id,
            company_id=self.company.id,
            contact_id=self.contact.id,
            title="Inbound lead",
            description=None,
            source="website",
            status="new",
            assigned_user_id=self.user.id,
        )
        self.db.add_all([self.deal, self.lead])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        Path(self.temp.name).unlink(missing_ok=True)

    def test_saved_views_custom_fields_workflow_quote_and_api_key(self) -> None:
        view = self.service.create_saved_view(
            self.db,
            self.org.id,
            self.user.id,
            SavedViewCreate(name="High value", resource="deals", filters={"min_value": 5000}, sort_by="value"),
        )
        self.assertEqual(view.name, "High value")
        self.assertEqual(len(self.service.list_saved_views(self.db, self.org.id, self.user.id, "deals")), 1)

        definition = self.service.create_custom_field(
            self.db,
            self.org.id,
            CustomFieldDefinitionCreate(entity_type="company", field_key="account_tier", label="Account tier", data_type="select", options=["A", "B", "C"]),
        )
        values = self.service.set_custom_field_values(self.db, self.org.id, self.user.id, "company", self.company.id, {"account_tier": "A"})
        self.assertEqual(values.values["account_tier"], "A")
        self.assertEqual(definition.field_key, "account_tier")

        workflow = self.service.create_workflow(
            self.db,
            self.org.id,
            WorkflowCreate(
                name="High probability follow-up",
                entity_type="deal",
                event_type="deal.updated",
                conditions=[WorkflowCondition(field="probability", operator="gte", value=70)],
                actions=[WorkflowAction(type="create_task", config={"title": "Prepare close plan", "assigned_user_id": "owner", "due_days": 2, "priority": "high"})],
            ),
        )
        runs = self.service.emit_event(
            self.db,
            organization_id=self.org.id,
            actor_id=self.user.id,
            event_type="deal.updated",
            entity_type="deal",
            entity_id=self.deal.id,
            payload={"probability": "70", "assigned_user_id": str(self.user.id)},
        )
        self.db.commit()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].status, "succeeded")
        self.assertEqual(int(self.db.scalar(select(func.count(Task.id))) or 0), 1)
        self.assertEqual(workflow.run_count, 1)

        product = self.service.create_product(self.db, self.org.id, ProductCreate(name="Platform", sku="PLAT-001", unit_price=Decimal("1200"), currency="USD"))
        quote = self.service.create_quote(
            self.db,
            self.org.id,
            self.user.id,
            QuoteCreate(
                deal_id=self.deal.id,
                company_id=self.company.id,
                contact_id=self.contact.id,
                quote_number="Q-1001",
                currency="USD",
                discount_percent=Decimal("10"),
                tax_percent=Decimal("5"),
                items=[QuoteItemInput(product_id=product.id, description="Platform", quantity=Decimal("2"), unit_price=Decimal("1200"))],
            ),
        )
        self.assertEqual(quote.subtotal, Decimal("2400.00"))
        self.assertEqual(quote.grand_total, Decimal("2268.00"))

        key = self.service.create_api_key(self.db, self.org.id, self.user.id, ApiKeyCreate(name="CI"))
        authenticated = self.service.authenticate_api_key(self.db, key.token)
        self.assertIsNotNone(authenticated)
        self.assertEqual(authenticated.id, self.user.id)

        quality = self.service.data_quality(self.db, self.org.id)
        self.assertGreaterEqual(quality.score, 0)
        forecast = self.service.revenue_forecast(self.db, self.org.id)
        self.assertEqual(forecast.open_pipeline, Decimal("10000"))


    def test_quote_approval_webhook_queue_and_actionable_intelligence(self) -> None:
        product = self.service.create_product(
            self.db, self.org.id,
            ProductCreate(name="Enterprise plan", sku="ENT-001", unit_price=Decimal("5000"), currency="USD"),
        )
        quote = self.service.create_quote(
            self.db, self.org.id, self.user.id,
            QuoteCreate(
                deal_id=self.deal.id, company_id=self.company.id, contact_id=self.contact.id,
                quote_number="Q-APPROVAL", currency="USD", discount_percent=Decimal("25"), tax_percent=Decimal("0"),
                items=[QuoteItemInput(product_id=product.id, description="Enterprise plan", quantity=Decimal("1"), unit_price=Decimal("5000"))],
            ),
        )
        self.assertEqual(quote.status, "pending_approval")
        approved = self.service.approve_quote(
            self.db, self.org.id, self.user.id, quote.id, QuoteApprovalRequest(note="Approved in test"), approved=True,
        )
        self.assertEqual(approved.status, "approved")
        self.assertEqual(approved.approved_by_user_id, self.user.id)
        self.assertIsNotNone(approved.approved_at)

        created_webhook = self.service.create_webhook(
            self.db, self.org.id,
            WebhookCreate(name="Test endpoint", url="https://example.com/crm-hook", events=["deal.updated"], is_active=True),
        )
        self.assertTrue(created_webhook.signing_secret)
        stored_webhook = self.db.scalar(select(WebhookEndpoint).where(WebhookEndpoint.id == created_webhook.id))
        self.assertIsNotNone(stored_webhook)
        self.assertNotEqual(stored_webhook.signing_secret, created_webhook.signing_secret)
        queued = self.service.enqueue_webhook_event(
            self.db, self.org.id, "deal.updated", {"deal_id": str(self.deal.id), "status": "open"}
        )
        self.db.commit()
        self.assertEqual(queued, 1)
        deliveries = self.service.list_webhook_deliveries(self.db, self.org.id, created_webhook.id)
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0].status, "pending")

        self.deal.expected_close_date = date.today() + timedelta(days=3)
        self.lead.updated_at = datetime.now(timezone.utc) - timedelta(days=20)
        overdue = Task(
            organization_id=self.org.id, assigned_user_id=self.user.id, title="Overdue follow-up",
            status="todo", priority="high", due_date=datetime.now(timezone.utc) - timedelta(days=1),
        )
        self.db.add(overdue)
        self.db.commit()

        brief = self.service.morning_brief(self.db, self.org.id, self.user.id)
        self.assertGreaterEqual(brief.overdue_tasks, 1)
        self.assertGreaterEqual(brief.stale_leads, 1)
        self.assertGreaterEqual(brief.closing_soon_deals, 1)
        self.assertTrue(any(item.kind == "task" for item in brief.actions))

        score = self.service.lead_score(self.db, self.org.id, self.lead.id)
        self.assertGreaterEqual(score.score, 0)
        self.assertLessEqual(score.score, 100)
        self.assertIn(score.grade, {"A", "B", "C", "D"})
        self.assertTrue(score.factors)

        won = Deal(
            organization_id=self.org.id, company_id=self.company.id, contact_id=self.contact.id,
            pipeline_id=self.pipeline.id, stage_id=self.stage.id, assigned_user_id=self.user.id,
            title="Won expansion", value=Decimal("3000"), currency="USD", probability=Decimal("100"),
            expected_close_date=date.today(), status="won",
        )
        lost = Deal(
            organization_id=self.org.id, company_id=self.company.id, contact_id=self.contact.id,
            pipeline_id=self.pipeline.id, stage_id=self.stage.id, assigned_user_id=self.user.id,
            title="Lost expansion", value=Decimal("2000"), currency="USD", probability=Decimal("0"),
            expected_close_date=date.today(), status="lost",
        )
        self.db.add_all([won, lost])
        self.db.commit()
        analytics = self.service.win_loss_analytics(self.db, self.org.id)
        self.assertEqual(analytics.won_count, 1)
        self.assertEqual(analytics.lost_count, 1)
        self.assertGreaterEqual(analytics.open_count, 1)
        self.assertEqual(analytics.won_value_by_currency["USD"], Decimal("3000"))
        self.assertEqual(analytics.lost_value_by_currency["USD"], Decimal("2000"))

    def test_relationship_health_and_disabled_ai_status(self) -> None:
        health = self.service.relationship_health(self.db, self.org.id, self.company.id)
        self.assertEqual(health.company_id, self.company.id)
        self.assertGreaterEqual(health.score, 0)
        ai = self.service.ai_status()
        self.assertFalse(ai.available)


if __name__ == "__main__":
    unittest.main()
