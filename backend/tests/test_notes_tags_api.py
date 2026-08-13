import asyncio
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["DEFAULT_ORGANIZATION_ID"] = "00000000-0000-0000-0000-000000000001"
os.environ["DEFAULT_ADMIN_EMAIL"] = "admin@example.com"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "development-password"
os.environ["DEFAULT_ADMIN_FIRST_NAME"] = "Development"
os.environ["DEFAULT_ADMIN_LAST_NAME"] = "Admin"
os.environ["DEFAULT_ROLE_NAME"] = ""
os.environ["JWT_SECRET"] = "0123456789abcdef0123456789abcdef0123456789abcdef"

import httpx
from fastapi import FastAPI
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.api.v1.audit_logs.router import router as audit_logs_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.companies.router import router as companies_router
from app.api.v1.contacts.router import router as contacts_router
from app.api.v1.leads.router import router as leads_router
from app.api.v1.notes.router import router as notes_router
from app.api.v1.tags.router import router as tags_router
from app.core.config import get_settings
from app.db.base import Base
from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.organization import Organization
from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.security.password import hash_password
from app.security.tokens import create_access_token
from app.services.development_seed import DevelopmentSeedService


class NotesTagsApiTestCase(unittest.TestCase):
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
            cls._create_deal_record(database_session)

        cls.application = FastAPI()
        cls.application.include_router(auth_router, prefix="/api/v1")
        cls.application.include_router(companies_router, prefix="/api/v1")
        cls.application.include_router(contacts_router, prefix="/api/v1")
        cls.application.include_router(leads_router, prefix="/api/v1")
        cls.application.include_router(notes_router, prefix="/api/v1")
        cls.application.include_router(tags_router, prefix="/api/v1")
        cls.application.include_router(audit_logs_router, prefix="/api/v1")
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
        database_session.add_all([foreign_user, foreign_company])
        database_session.flush()
        foreign_contact = Contact(
            company_id=foreign_company.id,
            first_name="Private",
            last_name="Contact",
        )
        database_session.add(foreign_contact)
        database_session.flush()
        foreign_lead = Lead(
            organization_id=foreign_organization.id,
            company_id=foreign_company.id,
            contact_id=foreign_contact.id,
            title="Private Lead",
            source="other",
            status="new",
            assigned_user_id=foreign_user.id,
        )
        database_session.add(foreign_lead)
        database_session.commit()
        cls.foreign_company_id = foreign_company.id
        cls.foreign_contact_id = foreign_contact.id
        cls.foreign_lead_id = foreign_lead.id

    @classmethod
    def _create_deal_record(cls, database_session: Session) -> None:
        settings = get_settings()
        admin_user = UserRepository().get_by_email(
            database_session,
            str(settings.default_admin_email),
            settings.default_organization_id,
        )
        if admin_user is None:
            raise RuntimeError("Seeded admin user was not created")

        company = Company(
            organization_id=settings.default_organization_id,
            name="Taggable Deal Company",
        )
        pipeline = Pipeline(
            organization_id=settings.default_organization_id,
            name="Taggable Deal Pipeline",
        )
        database_session.add_all([company, pipeline])
        database_session.flush()
        stage = PipelineStage(
            pipeline_id=pipeline.id,
            name="Qualified",
            order=1,
            probability=Decimal("50.00"),
        )
        database_session.add(stage)
        database_session.flush()
        deal = Deal(
            organization_id=settings.default_organization_id,
            company_id=company.id,
            pipeline_id=pipeline.id,
            stage_id=stage.id,
            assigned_user_id=admin_user.id,
            title="Taggable Deal",
            value=Decimal("1000.00"),
            currency="USD",
            probability=Decimal("50.00"),
            expected_close_date=date(2026, 12, 31),
            status="open",
        )
        limited_user = User(
            organization_id=settings.default_organization_id,
            email="notes-tags-limited@example.com",
            password_hash=hash_password("development-password"),
            first_name="Limited",
            last_name="User",
        )
        database_session.add_all([deal, limited_user])
        database_session.commit()
        cls.deal_id = deal.id
        cls.limited_user_id = limited_user.id

    def test_notes_tags_crud_assignments_audit_and_organization_isolation(self) -> None:
        asyncio.run(self._exercise_notes_and_tags_api())

    async def _exercise_notes_and_tags_api(self) -> None:
        transport = httpx.ASGITransport(app=self.application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            limited_access_token = create_access_token(
                self.limited_user_id,
                get_settings().default_organization_id,
                get_settings(),
            )
            limited_headers = {"Authorization": f"Bearer {limited_access_token}"}
            self.assertEqual(
                (await client.get("/api/v1/notes", headers=limited_headers)).status_code,
                403,
            )
            self.assertEqual(
                (await client.get("/api/v1/tags", headers=limited_headers)).status_code,
                403,
            )

            headers = await self._authenticate(client)
            company = await self._create_company(client, headers)
            contact = await self._create_contact(client, headers, UUID(company["id"]))
            lead = await self._create_lead(
                client,
                headers,
                UUID(company["id"]),
                UUID(contact["id"]),
            )

            note_response = await client.post(
                "/api/v1/notes",
                headers=headers,
                json={
                    "content": "Capture the next commercial step.",
                    "company_id": company["id"],
                    "contact_id": contact["id"],
                    "lead_id": lead["id"],
                },
            )
            self.assertEqual(note_response.status_code, 201)
            note = note_response.json()
            self.assertEqual(note["company_id"], company["id"])
            self.assertEqual(note["contact_id"], contact["id"])
            self.assertEqual(note["lead_id"], lead["id"])

            note_detail_response = await client.get(
                f"/api/v1/notes/{note['id']}", headers=headers
            )
            self.assertEqual(note_detail_response.status_code, 200)
            self.assertEqual(note_detail_response.json()["content"], note["content"])

            invalid_note_response = await client.post(
                "/api/v1/notes",
                headers=headers,
                json={"content": ""},
            )
            self.assertEqual(invalid_note_response.status_code, 422)

            list_notes_response = await client.get(
                "/api/v1/notes",
                headers=headers,
                params={
                    "company_id": company["id"],
                    "contact_id": contact["id"],
                    "lead_id": lead["id"],
                    "search": "commercial",
                },
            )
            self.assertEqual(list_notes_response.status_code, 200)
            listed_notes = list_notes_response.json()
            self.assertEqual(listed_notes["meta"]["total"], 1)
            self.assertEqual(listed_notes["items"][0]["id"], note["id"])

            foreign_company_note_response = await client.post(
                "/api/v1/notes",
                headers=headers,
                json={
                    "content": "This must not be created.",
                    "company_id": str(self.foreign_company_id),
                },
            )
            self.assertEqual(foreign_company_note_response.status_code, 404)

            foreign_contact_update_response = await client.patch(
                f"/api/v1/notes/{note['id']}",
                headers=headers,
                json={"contact_id": str(self.foreign_contact_id)},
            )
            self.assertEqual(foreign_contact_update_response.status_code, 404)

            foreign_lead_update_response = await client.patch(
                f"/api/v1/notes/{note['id']}",
                headers=headers,
                json={"lead_id": str(self.foreign_lead_id)},
            )
            self.assertEqual(foreign_lead_update_response.status_code, 404)

            update_note_response = await client.patch(
                f"/api/v1/notes/{note['id']}",
                headers=headers,
                json={"content": "Follow up with the buying committee.", "lead_id": None},
            )
            self.assertEqual(update_note_response.status_code, 200)
            self.assertIsNone(update_note_response.json()["lead_id"])

            tag_response = await client.post(
                "/api/v1/tags",
                headers=headers,
                json={"name": "Priority", "color": "#2563EB"},
            )
            self.assertEqual(tag_response.status_code, 201)
            tag = tag_response.json()

            tag_detail_response = await client.get(
                f"/api/v1/tags/{tag['id']}", headers=headers
            )
            self.assertEqual(tag_detail_response.status_code, 200)
            self.assertEqual(tag_detail_response.json()["name"], "Priority")

            invalid_tag_response = await client.post(
                "/api/v1/tags",
                headers=headers,
                json={"name": "Invalid", "color": "blue"},
            )
            self.assertEqual(invalid_tag_response.status_code, 422)

            duplicate_tag_response = await client.post(
                "/api/v1/tags",
                headers=headers,
                json={"name": "Priority", "color": "#2563EB"},
            )
            self.assertEqual(duplicate_tag_response.status_code, 409)

            for entity_type, entity_id in (
                ("company", company["id"]),
                ("contact", contact["id"]),
                ("lead", lead["id"]),
                ("deal", str(self.deal_id)),
            ):
                assignment_response = await client.put(
                    f"/api/v1/tags/{tag['id']}/assignments/{entity_type}/{entity_id}",
                    headers=headers,
                )
                self.assertEqual(assignment_response.status_code, 204)

                filtered_tags_response = await client.get(
                    "/api/v1/tags",
                    headers=headers,
                    params={"entity_type": entity_type, "entity_id": entity_id},
                )
                self.assertEqual(filtered_tags_response.status_code, 200)
                self.assertEqual(filtered_tags_response.json()["meta"]["total"], 1)
                self.assertEqual(filtered_tags_response.json()["items"][0]["id"], tag["id"])

            idempotent_assignment_response = await client.put(
                f"/api/v1/tags/{tag['id']}/assignments/company/{company['id']}",
                headers=headers,
            )
            self.assertEqual(idempotent_assignment_response.status_code, 204)

            foreign_assignment_response = await client.put(
                f"/api/v1/tags/{tag['id']}/assignments/company/{self.foreign_company_id}",
                headers=headers,
            )
            self.assertEqual(foreign_assignment_response.status_code, 404)

            incomplete_filter_response = await client.get(
                "/api/v1/tags",
                headers=headers,
                params={"entity_type": "company"},
            )
            self.assertEqual(incomplete_filter_response.status_code, 422)

            update_tag_response = await client.patch(
                f"/api/v1/tags/{tag['id']}",
                headers=headers,
                json={"name": "Strategic", "color": "#0F766E"},
            )
            self.assertEqual(update_tag_response.status_code, 200)
            self.assertEqual(update_tag_response.json()["name"], "Strategic")

            unassignment_response = await client.delete(
                f"/api/v1/tags/{tag['id']}/assignments/contact/{contact['id']}",
                headers=headers,
            )
            self.assertEqual(unassignment_response.status_code, 204)

            unassigned_filter_response = await client.get(
                "/api/v1/tags",
                headers=headers,
                params={"entity_type": "contact", "entity_id": contact["id"]},
            )
            self.assertEqual(unassigned_filter_response.status_code, 200)
            self.assertEqual(unassigned_filter_response.json()["meta"]["total"], 0)

            audit_response = await client.get("/api/v1/audit-logs", headers=headers)
            self.assertEqual(audit_response.status_code, 200)
            actions = {entry["action"] for entry in audit_response.json()["items"]}
            self.assertTrue(
                {"note.created", "note.updated", "tag.created", "tag.assigned"}.issubset(
                    actions
                )
            )

            delete_note_response = await client.delete(
                f"/api/v1/notes/{note['id']}", headers=headers
            )
            self.assertEqual(delete_note_response.status_code, 204)
            self.assertEqual(
                (await client.get(f"/api/v1/notes/{note['id']}", headers=headers)).status_code,
                404,
            )

            delete_tag_response = await client.delete(
                f"/api/v1/tags/{tag['id']}", headers=headers
            )
            self.assertEqual(delete_tag_response.status_code, 204)
            self.assertEqual(
                (await client.get(f"/api/v1/tags/{tag['id']}", headers=headers)).status_code,
                404,
            )

    async def _authenticate(self, client: httpx.AsyncClient) -> dict[str, str]:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "development-password",
            },
        )
        self.assertEqual(login_response.status_code, 200)
        return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    async def _create_company(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> dict[str, str]:
        response = await client.post(
            "/api/v1/companies",
            headers=headers,
            json={"name": "Notes and Tags Company"},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def _create_contact(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        company_id: UUID,
    ) -> dict[str, str]:
        response = await client.post(
            "/api/v1/contacts",
            headers=headers,
            json={
                "company_id": str(company_id),
                "first_name": "Taylor",
                "last_name": "Buyer",
                "email": "taylor@example.com",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def _create_lead(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        company_id: UUID,
        contact_id: UUID,
    ) -> dict[str, str]:
        response = await client.post(
            "/api/v1/leads",
            headers=headers,
            json={
                "title": "Notes and Tags Lead",
                "source": "referral",
                "company_id": str(company_id),
                "contact_id": str(contact_id),
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()
