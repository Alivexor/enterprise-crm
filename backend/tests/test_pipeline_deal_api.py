import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from uuid import UUID, uuid4

os.environ["ENVIRONMENT"] = "development"
os.environ["DEFAULT_ORGANIZATION_ID"] = "00000000-0000-0000-0000-000000000001"
os.environ["DEFAULT_ADMIN_EMAIL"] = "admin@example.com"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "development-password"
os.environ["DEFAULT_ADMIN_FIRST_NAME"] = "Development"
os.environ["DEFAULT_ADMIN_LAST_NAME"] = "Admin"
os.environ["DEFAULT_ROLE_NAME"] = ""
os.environ["JWT_SECRET"] = "0123456789abcdef0123456789abcdef0123456789abcdef"

import httpx
from fastapi import FastAPI
from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.api.v1.auth.router import router as auth_router
from app.api.v1.companies.router import router as companies_router
from app.api.v1.contacts.router import router as contacts_router
from app.api.v1.deals.router import router as deals_router
from app.api.v1.leads.router import router as leads_router
from app.api.v1.pipelines.router import router as pipelines_router
from app.core.config import get_settings
from app.db.base import Base
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.contact import Contact
from app.models.organization import Organization
from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.security.password import hash_password
from app.services.development_seed import DevelopmentSeedService


class PipelineDealApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        cls.database_file.close()
        database_url = f"sqlite+pysqlite:///{Path(cls.database_file.name).as_posix()}"
        cls.engine = create_engine(database_url)

        @event.listens_for(cls.engine, "connect")
        def enable_foreign_keys(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

        cls.session_factory = sessionmaker(bind=cls.engine, autoflush=False)
        Base.metadata.create_all(cls.engine)

        with cls.session_factory() as database_session:
            seed_service = DevelopmentSeedService(
                get_settings(),
                OrganizationRepository(),
                PermissionRepository(),
                RoleRepository(),
                UserRepository(),
            )
            seed_service.seed(database_session)
            cls._create_foreign_records(database_session)

        cls.application = FastAPI()
        cls.application.include_router(auth_router, prefix="/api/v1")
        cls.application.include_router(companies_router, prefix="/api/v1")
        cls.application.include_router(contacts_router, prefix="/api/v1")
        cls.application.include_router(pipelines_router, prefix="/api/v1")
        cls.application.include_router(deals_router, prefix="/api/v1")
        cls.application.include_router(leads_router, prefix="/api/v1")
        cls.application.dependency_overrides[get_db] = cls._get_test_db

    @classmethod
    def tearDownClass(cls) -> None:
        cls.application.dependency_overrides.clear()
        cls.engine.dispose()
        Path(cls.database_file.name).unlink(missing_ok=True)

    @classmethod
    def _get_test_db(cls):
        database_session = cls.session_factory()
        try:
            yield database_session
        finally:
            database_session.close()

    @classmethod
    def _create_foreign_records(cls, database_session: Session) -> None:
        foreign_organization = Organization(id=uuid4(), name="Other Organization")
        database_session.add(foreign_organization)
        database_session.flush()
        foreign_user = User(
            organization_id=foreign_organization.id,
            email="foreign@example.com",
            password_hash=hash_password("development-password"),
            first_name="Foreign",
            last_name="User",
        )
        foreign_company = Company(
            organization_id=foreign_organization.id,
            name="Private Company",
        )
        foreign_pipeline = Pipeline(
            organization_id=foreign_organization.id,
            name="Private Pipeline",
        )
        database_session.add_all([foreign_user, foreign_company, foreign_pipeline])
        database_session.flush()
        foreign_stage = PipelineStage(
            pipeline_id=foreign_pipeline.id,
            name="Private stage",
            order=0,
            probability=0,
        )
        database_session.add(foreign_stage)
        database_session.commit()
        cls.foreign_company_id = foreign_company.id
        cls.foreign_pipeline_id = foreign_pipeline.id
        cls.foreign_stage_id = foreign_stage.id

    def test_pipeline_stage_and_deal_lifecycle(self) -> None:
        asyncio.run(self._exercise_lifecycle())

    async def _exercise_lifecycle(self) -> None:
        transport = httpx.ASGITransport(app=self.application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            headers, admin_id = await self._authenticate(client)
            company = await self._create_company(client, headers, "Acme Corporation")
            contact = await self._create_contact(
                client,
                headers,
                company["id"],
                "Ada",
                "Lovelace",
            )
            pipeline = await self._create_pipeline(client, headers, "Enterprise sales")
            discovery_stage = await self._create_stage(
                client,
                headers,
                pipeline["id"],
                name="Discovery",
                order=0,
                probability="20.00",
            )
            proposal_stage = await self._create_stage(
                client,
                headers,
                pipeline["id"],
                name="Proposal",
                order=1,
                probability="60.00",
            )

            pipeline_detail = await client.get(
                f"/api/v1/pipelines/{pipeline['id']}", headers=headers
            )
            self.assertEqual(pipeline_detail.status_code, 200)
            self.assertEqual(
                [stage["id"] for stage in pipeline_detail.json()["stages"]],
                [discovery_stage["id"], proposal_stage["id"]],
            )

            pipeline_page = await client.get(
                "/api/v1/pipelines",
                headers=headers,
                params={"search": "enterprise", "page": 1, "page_size": 1},
            )
            self.assertEqual(pipeline_page.status_code, 200)
            self.assertEqual(pipeline_page.json()["meta"], {"page": 1, "page_size": 1, "total": 1})
            self.assertEqual(pipeline_page.json()["items"][0]["id"], pipeline["id"])

            stage_page = await client.get(
                f"/api/v1/pipelines/{pipeline['id']}/stages",
                headers=headers,
                params={"page": 1, "page_size": 1, "sort_by": "order"},
            )
            self.assertEqual(stage_page.status_code, 200)
            self.assertEqual(stage_page.json()["meta"]["total"], 2)
            self.assertEqual(stage_page.json()["items"][0]["id"], discovery_stage["id"])

            duplicate_order = await client.post(
                f"/api/v1/pipelines/{pipeline['id']}/stages",
                headers=headers,
                json={"name": "Duplicate", "order": 1, "probability": "70.00"},
            )
            self.assertEqual(duplicate_order.status_code, 409)

            alternate_pipeline = await self._create_pipeline(
                client, headers, "Renewals"
            )
            alternate_stage = await self._create_stage(
                client,
                headers,
                alternate_pipeline["id"],
                name="Renewal",
                order=0,
                probability="50.00",
            )

            mismatch_stage = await client.post(
                "/api/v1/deals",
                headers=headers,
                json=self._deal_payload(
                    company_id=company["id"],
                    contact_id=contact["id"],
                    pipeline_id=pipeline["id"],
                    stage_id=alternate_stage["id"],
                    assigned_user_id=admin_id,
                ),
            )
            self.assertEqual(mismatch_stage.status_code, 422)

            foreign_reference = await client.post(
                "/api/v1/deals",
                headers=headers,
                json=self._deal_payload(
                    company_id=str(self.foreign_company_id),
                    contact_id=None,
                    pipeline_id=pipeline["id"],
                    stage_id=discovery_stage["id"],
                    assigned_user_id=admin_id,
                ),
            )
            self.assertEqual(foreign_reference.status_code, 404)

            other_company = await self._create_company(client, headers, "Other Company")
            other_contact = await self._create_contact(
                client,
                headers,
                other_company["id"],
                "Grace",
                "Hopper",
            )
            mismatch_contact = await client.post(
                "/api/v1/deals",
                headers=headers,
                json=self._deal_payload(
                    company_id=company["id"],
                    contact_id=other_contact["id"],
                    pipeline_id=pipeline["id"],
                    stage_id=discovery_stage["id"],
                    assigned_user_id=admin_id,
                ),
            )
            self.assertEqual(mismatch_contact.status_code, 422)

            create_deal = await client.post(
                "/api/v1/deals",
                headers=headers,
                json=self._deal_payload(
                    company_id=company["id"],
                    contact_id=contact["id"],
                    pipeline_id=pipeline["id"],
                    stage_id=discovery_stage["id"],
                    assigned_user_id=admin_id,
                ),
            )
            self.assertEqual(create_deal.status_code, 201)
            deal = create_deal.json()
            self.assertEqual(deal["currency"], "USD")
            self.assertEqual(deal["stage_id"], discovery_stage["id"])

            deal_page = await client.get(
                "/api/v1/deals",
                headers=headers,
                params={
                    "pipeline_id": pipeline["id"],
                    "status": "open",
                    "page": 1,
                    "page_size": 1,
                    "sort_by": "created_at",
                    "sort_direction": "desc",
                },
            )
            self.assertEqual(deal_page.status_code, 200)
            self.assertEqual(deal_page.json()["meta"], {"page": 1, "page_size": 1, "total": 1})
            self.assertEqual(deal_page.json()["items"][0]["id"], deal["id"])

            conversion_lead_response = await client.post(
                "/api/v1/leads",
                headers=headers,
                json={
                    "title": "Expansion lead",
                    "source": "website",
                    "company_id": company["id"],
                    "contact_id": contact["id"],
                    "assigned_user_id": admin_id,
                },
            )
            self.assertEqual(conversion_lead_response.status_code, 201, conversion_lead_response.text)
            conversion_lead = conversion_lead_response.json()
            conversion_response = await client.post(
                f"/api/v1/leads/{conversion_lead['id']}/convert",
                headers=headers,
                json={
                    "pipeline_id": pipeline["id"],
                    "stage_id": discovery_stage["id"],
                    "value": "25000.00",
                    "currency": "usd",
                    "probability": "20.00",
                    "expected_close_date": "2027-01-15",
                },
            )
            self.assertEqual(conversion_response.status_code, 200, conversion_response.text)
            conversion_payload = conversion_response.json()
            self.assertEqual(conversion_payload["lead"]["status"], "converted")
            self.assertEqual(conversion_payload["deal"]["company_id"], company["id"])
            self.assertEqual(conversion_payload["deal"]["contact_id"], contact["id"])
            self.assertEqual(conversion_payload["deal"]["currency"], "USD")
            self.assertEqual(conversion_payload["deal"]["assigned_user_id"], admin_id)

            duplicate_conversion = await client.post(
                f"/api/v1/leads/{conversion_lead['id']}/convert",
                headers=headers,
                json={
                    "pipeline_id": pipeline["id"],
                    "stage_id": discovery_stage["id"],
                    "value": "25000.00",
                    "currency": "USD",
                    "probability": "20.00",
                    "expected_close_date": "2027-01-15",
                },
            )
            self.assertEqual(duplicate_conversion.status_code, 409)

            rollback_lead_response = await client.post(
                "/api/v1/leads",
                headers=headers,
                json={
                    "title": "Atomic conversion check",
                    "source": "referral",
                    "company_id": company["id"],
                    "assigned_user_id": admin_id,
                },
            )
            self.assertEqual(rollback_lead_response.status_code, 201)
            rollback_lead = rollback_lead_response.json()
            rejected_conversion = await client.post(
                f"/api/v1/leads/{rollback_lead['id']}/convert",
                headers=headers,
                json={
                    "pipeline_id": pipeline["id"],
                    "stage_id": alternate_stage["id"],
                    "value": "1000.00",
                    "currency": "USD",
                    "probability": "50.00",
                    "expected_close_date": "2027-01-15",
                },
            )
            self.assertEqual(rejected_conversion.status_code, 422)
            rollback_lead_state = await client.get(
                f"/api/v1/leads/{rollback_lead['id']}", headers=headers
            )
            self.assertEqual(rollback_lead_state.status_code, 200)
            self.assertEqual(rollback_lead_state.json()["status"], "new")

            invalid_pipeline_change = await client.patch(
                f"/api/v1/deals/{deal['id']}",
                headers=headers,
                json={"pipeline_id": alternate_pipeline["id"]},
            )
            self.assertEqual(invalid_pipeline_change.status_code, 422)

            update_deal = await client.patch(
                f"/api/v1/deals/{deal['id']}",
                headers=headers,
                json={
                    "stage_id": proposal_stage["id"],
                    "probability": "60.00",
                    "status": "won",
                },
            )
            self.assertEqual(update_deal.status_code, 200)
            self.assertEqual(update_deal.json()["stage_id"], proposal_stage["id"])
            self.assertEqual(update_deal.json()["status"], "won")

            foreign_pipeline = await client.get(
                f"/api/v1/pipelines/{self.foreign_pipeline_id}", headers=headers
            )
            self.assertEqual(foreign_pipeline.status_code, 404)

            blocked_stage_delete = await client.delete(
                f"/api/v1/pipelines/{pipeline['id']}/stages/{proposal_stage['id']}",
                headers=headers,
            )
            self.assertEqual(blocked_stage_delete.status_code, 409)
            blocked_pipeline_delete = await client.delete(
                f"/api/v1/pipelines/{pipeline['id']}", headers=headers
            )
            self.assertEqual(blocked_pipeline_delete.status_code, 409)

            delete_deal = await client.delete(
                f"/api/v1/deals/{deal['id']}", headers=headers
            )
            self.assertEqual(delete_deal.status_code, 204)
            self.assertEqual(
                (await client.get(f"/api/v1/deals/{deal['id']}", headers=headers)).status_code,
                404,
            )

            deleted_stage = await client.delete(
                f"/api/v1/pipelines/{pipeline['id']}/stages/{proposal_stage['id']}",
                headers=headers,
            )
            self.assertEqual(deleted_stage.status_code, 204)

        self._assert_audit_history(UUID(pipeline["id"]), UUID(deal["id"]))

    async def _authenticate(
        self, client: httpx.AsyncClient
    ) -> tuple[dict[str, str], str]:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "development-password"},
        )
        self.assertEqual(response.status_code, 200)
        access_token = response.json()["access_token"]
        me_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(me_response.status_code, 200)
        return {"Authorization": f"Bearer {access_token}"}, me_response.json()["id"]

    async def _create_company(
        self, client: httpx.AsyncClient, headers: dict[str, str], name: str
    ) -> dict[str, object]:
        response = await client.post("/api/v1/companies", headers=headers, json={"name": name})
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def _create_contact(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        company_id: str,
        first_name: str,
        last_name: str,
    ) -> dict[str, object]:
        response = await client.post(
            "/api/v1/contacts",
            headers=headers,
            json={
                "company_id": company_id,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def _create_pipeline(
        self, client: httpx.AsyncClient, headers: dict[str, str], name: str
    ) -> dict[str, object]:
        response = await client.post(
            "/api/v1/pipelines",
            headers=headers,
            json={"name": name, "description": "Sales process"},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def _create_stage(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        pipeline_id: str,
        *,
        name: str,
        order: int,
        probability: str,
    ) -> dict[str, object]:
        response = await client.post(
            f"/api/v1/pipelines/{pipeline_id}/stages",
            headers=headers,
            json={"name": name, "order": order, "probability": probability},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    @staticmethod
    def _deal_payload(
        *,
        company_id: str,
        contact_id: str | None,
        pipeline_id: str,
        stage_id: str,
        assigned_user_id: str,
    ) -> dict[str, object]:
        return {
            "company_id": company_id,
            "contact_id": contact_id,
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
            "assigned_user_id": assigned_user_id,
            "title": "Acme renewal",
            "value": "12000.50",
            "currency": "usd",
            "probability": "20.00",
            "expected_close_date": "2026-12-31",
            "status": "open",
        }

    def _assert_audit_history(self, pipeline_id: UUID, deal_id: UUID) -> None:
        with self.session_factory() as database_session:
            actions = set(
                database_session.scalars(
                    select(AuditLog.action).where(
                        AuditLog.entity_id.in_([pipeline_id, deal_id])
                    )
                )
            )
        self.assertTrue({"pipeline.created", "deal.created", "deal.updated", "deal.deleted"}.issubset(actions))
