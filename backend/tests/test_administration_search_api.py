import asyncio
import atexit
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

os.environ["ENVIRONMENT"] = "development"
_bootstrap_database_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
_bootstrap_database_file.close()
os.environ["DATABASE_URL"] = (
    f"sqlite+pysqlite:///{Path(_bootstrap_database_file.name).as_posix()}"
)
os.environ["DEFAULT_ORGANIZATION_ID"] = "00000000-0000-0000-0000-000000000001"
os.environ["DEFAULT_ADMIN_EMAIL"] = "admin@example.com"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "development-password"
os.environ["DEFAULT_ADMIN_FIRST_NAME"] = "Development"
os.environ["DEFAULT_ADMIN_LAST_NAME"] = "Admin"
os.environ["DEFAULT_ROLE_NAME"] = ""
os.environ["JWT_SECRET"] = "0123456789abcdef0123456789abcdef0123456789abcdef"


@atexit.register
def _remove_bootstrap_database() -> None:
    try:
        Path(_bootstrap_database_file.name).unlink(missing_ok=True)
    except OSError:
        pass

import httpx
from fastapi import FastAPI
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.api.v1.audit_logs.router import router as audit_logs_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.organization.router import router as organization_router
from app.api.v1.roles.router import router as roles_router
from app.api.v1.search.router import router as search_router
from app.api.v1.users.router import profile_router, router as users_router
from app.core.config import get_settings
from app.db.base import Base
from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.note import Note
from app.models.organization import Organization
from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.models.role import Role
from app.models.task import Task
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.security.password import hash_password
from app.services.development_seed import DevelopmentSeedService


class AdministrationSearchApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_settings.cache_clear()
        cls.database_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        cls.database_file.close()
        cls.engine = create_engine(
            f"sqlite+pysqlite:///{Path(cls.database_file.name).as_posix()}"
        )

        @event.listens_for(cls.engine, "connect")
        def enable_foreign_keys(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

        cls.session_factory = sessionmaker(bind=cls.engine, autoflush=False)
        Base.metadata.create_all(cls.engine)
        cls.settings = get_settings()

        with cls.session_factory() as database_session:
            DevelopmentSeedService(
                cls.settings,
                OrganizationRepository(),
                PermissionRepository(),
                RoleRepository(),
                UserRepository(),
            ).seed(database_session)
            cls._create_fixture_records(database_session)

        cls.application = FastAPI()
        cls.application.include_router(auth_router, prefix="/api/v1")
        cls.application.include_router(organization_router, prefix="/api/v1")
        cls.application.include_router(users_router, prefix="/api/v1")
        cls.application.include_router(profile_router, prefix="/api/v1")
        cls.application.include_router(roles_router, prefix="/api/v1")
        cls.application.include_router(audit_logs_router, prefix="/api/v1")
        cls.application.include_router(search_router, prefix="/api/v1")
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
    def _create_fixture_records(cls, database_session: Session) -> None:
        permission_repository = PermissionRepository()
        user_repository = UserRepository()
        admin_user = user_repository.get_by_email(
            database_session,
            str(cls.settings.default_admin_email),
            cls.settings.default_organization_id,
        )
        if admin_user is None:
            raise RuntimeError("Seeded administrator was not created")

        searcher_role = Role(
            organization_id=cls.settings.default_organization_id,
            name="company-searcher",
        )
        searcher_role.permissions = permission_repository.get_by_names(
            database_session,
            ("search.read", "companies.read"),
        )
        limited_user = User(
            organization_id=cls.settings.default_organization_id,
            email="limited-administration@example.com",
            password_hash=hash_password("development-password"),
            first_name="Limited",
            last_name="Administration",
        )
        company_searcher = User(
            organization_id=cls.settings.default_organization_id,
            email="company-searcher@example.com",
            password_hash=hash_password("development-password"),
            first_name="Company",
            last_name="Searcher",
            roles=[searcher_role],
        )
        local_company = Company(
            organization_id=cls.settings.default_organization_id,
            name="scope-token Company",
            industry="scope-token Industry",
        )
        local_pipeline = Pipeline(
            organization_id=cls.settings.default_organization_id,
            name="scope-token Pipeline",
        )
        foreign_organization = Organization(id=uuid4(), name="Other Organization")
        database_session.add_all(
            [
                searcher_role,
                limited_user,
                company_searcher,
                local_company,
                local_pipeline,
                foreign_organization,
            ]
        )
        database_session.flush()

        local_contact = Contact(
            company_id=local_company.id,
            first_name="scope-token",
            last_name="Contact",
            email="scope-token-contact@example.com",
        )
        local_stage = PipelineStage(
            pipeline_id=local_pipeline.id,
            name="Qualified",
            order=1,
            probability=Decimal("50.00"),
        )
        foreign_user = User(
            organization_id=foreign_organization.id,
            email="foreign-administration@example.com",
            password_hash=hash_password("development-password"),
            first_name="Foreign",
            last_name="User",
        )
        foreign_role = Role(organization_id=foreign_organization.id, name="foreign-role")
        foreign_company = Company(
            organization_id=foreign_organization.id,
            name="scope-token Foreign Company",
        )
        foreign_pipeline = Pipeline(
            organization_id=foreign_organization.id,
            name="Foreign Pipeline",
        )
        database_session.add_all(
            [
                local_contact,
                local_stage,
                foreign_user,
                foreign_role,
                foreign_company,
                foreign_pipeline,
            ]
        )
        database_session.flush()

        local_lead = Lead(
            organization_id=cls.settings.default_organization_id,
            company_id=local_company.id,
            contact_id=local_contact.id,
            title="scope-token Lead",
            source="test",
            status="new",
            assigned_user_id=admin_user.id,
        )
        local_deal = Deal(
            organization_id=cls.settings.default_organization_id,
            company_id=local_company.id,
            contact_id=local_contact.id,
            pipeline_id=local_pipeline.id,
            stage_id=local_stage.id,
            assigned_user_id=admin_user.id,
            title="scope-token Deal",
            value=Decimal("1000.00"),
            currency="USD",
            probability=Decimal("50.00"),
            expected_close_date=date(2026, 12, 31),
            status="open",
        )
        local_task = Task(
            organization_id=cls.settings.default_organization_id,
            assigned_user_id=admin_user.id,
            title="scope-token Task",
            priority="medium",
            status="open",
        )
        local_activity = Activity(
            organization_id=cls.settings.default_organization_id,
            user_id=admin_user.id,
            company_id=local_company.id,
            title="scope-token Activity",
            type="call",
        )
        local_note = Note(
            organization_id=cls.settings.default_organization_id,
            user_id=admin_user.id,
            company_id=local_company.id,
            content="scope-token Note",
        )
        foreign_stage = PipelineStage(
            pipeline_id=foreign_pipeline.id,
            name="Qualified",
            order=1,
            probability=Decimal("50.00"),
        )
        foreign_contact = Contact(
            company_id=foreign_company.id,
            first_name="scope-token",
            last_name="Foreign Contact",
        )
        database_session.add_all(
            [
                local_lead,
                local_deal,
                local_task,
                local_activity,
                local_note,
                foreign_stage,
                foreign_contact,
            ]
        )
        database_session.flush()

        now = datetime.now(timezone.utc)
        local_audit_old = AuditLog(
            user_id=admin_user.id,
            action="scope-token.audit",
            entity_type="audit-test",
            entity_id=uuid4(),
            created_at=now - timedelta(minutes=2),
        )
        local_audit_new = AuditLog(
            user_id=admin_user.id,
            action="scope-token.audit",
            entity_type="audit-test",
            entity_id=uuid4(),
            created_at=now - timedelta(minutes=1),
        )
        foreign_audit = AuditLog(
            user_id=foreign_user.id,
            action="scope-token.audit",
            entity_type="audit-test",
            entity_id=uuid4(),
            created_at=now,
        )
        database_session.add_all([local_audit_old, local_audit_new, foreign_audit])
        database_session.commit()

        cls.admin_user_id = admin_user.id
        cls.admin_role_id = next(role.id for role in admin_user.roles if role.name == "admin")
        cls.limited_user_id = limited_user.id
        cls.company_searcher_id = company_searcher.id
        cls.foreign_user_id = foreign_user.id
        cls.foreign_role_id = foreign_role.id
        cls.foreign_company_id = foreign_company.id
        cls.local_search_ids = {
            local_company.id,
            local_contact.id,
            local_lead.id,
            local_deal.id,
            local_task.id,
            local_activity.id,
            local_note.id,
        }
        cls.local_audit_ids = [local_audit_old.id, local_audit_new.id]
        cls.local_audit_range = (
            (now - timedelta(minutes=3)).isoformat(),
            now.isoformat(),
        )

    def test_administration_profile_audit_and_search_contracts(self) -> None:
        asyncio.run(self._exercise_api_contracts())

    async def _exercise_api_contracts(self) -> None:
        transport = httpx.ASGITransport(app=self.application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            admin_headers = await self._authenticate(
                client, "admin@example.com", "development-password"
            )
            limited_headers = await self._authenticate(
                client, "limited-administration@example.com", "development-password"
            )
            company_searcher_headers = await self._authenticate(
                client, "company-searcher@example.com", "development-password"
            )

            await self._assert_permission_boundaries(client, limited_headers)
            role_id = await self._exercise_organization_roles_and_users(
                client, admin_headers, company_searcher_headers
            )
            await self._exercise_audit_filters(client, admin_headers)
            await self._exercise_search_contracts(
                client, admin_headers, company_searcher_headers
            )
            await self._exercise_profile_contracts(client, admin_headers, role_id)

    async def _assert_permission_boundaries(
        self, client: httpx.AsyncClient, limited_headers: dict[str, str]
    ) -> None:
        protected_requests = (
            client.get("/api/v1/organization", headers=limited_headers),
            client.get("/api/v1/users", headers=limited_headers),
            client.get("/api/v1/roles", headers=limited_headers),
            client.get("/api/v1/audit-logs", headers=limited_headers),
            client.get(
                "/api/v1/search", headers=limited_headers, params={"q": "scope-token"}
            ),
        )
        for response in await asyncio.gather(*protected_requests):
            self.assertEqual(response.status_code, 403)

    async def _exercise_organization_roles_and_users(
        self,
        client: httpx.AsyncClient,
        admin_headers: dict[str, str],
        company_searcher_headers: dict[str, str],
    ) -> UUID:
        organization_response = await client.get(
            "/api/v1/organization", headers=admin_headers
        )
        self.assertEqual(organization_response.status_code, 200)
        self.assertEqual(
            organization_response.json()["id"], str(self.settings.default_organization_id)
        )

        invalid_organization_response = await client.patch(
            "/api/v1/organization", headers=admin_headers, json={"name": "   "}
        )
        self.assertEqual(invalid_organization_response.status_code, 422)
        update_organization_response = await client.patch(
            "/api/v1/organization",
            headers=admin_headers,
            json={"name": "Enterprise CRM Verification"},
        )
        self.assertEqual(update_organization_response.status_code, 200)
        self.assertEqual(update_organization_response.json()["name"], "Enterprise CRM Verification")

        roles_response = await client.get("/api/v1/roles", headers=admin_headers)
        self.assertEqual(roles_response.status_code, 200)
        role_names = {role["name"] for role in roles_response.json()}
        self.assertIn("admin", role_names)
        self.assertNotIn("foreign-role", role_names)

        permissions_response = await client.get(
            "/api/v1/roles/permissions", headers=admin_headers
        )
        self.assertEqual(permissions_response.status_code, 200)
        permission_id_by_name = {
            permission["name"]: permission["id"] for permission in permissions_response.json()
        }
        self.assertIn("companies.read", permission_id_by_name)
        self.assertIn("contacts.read", permission_id_by_name)

        create_role_response = await client.post(
            "/api/v1/roles",
            headers=admin_headers,
            json={
                "name": "account-manager",
                "permission_ids": [
                    permission_id_by_name["companies.read"],
                    permission_id_by_name["contacts.read"],
                ],
            },
        )
        self.assertEqual(create_role_response.status_code, 201)
        role = create_role_response.json()
        role_id = UUID(role["id"])
        self.assertEqual(role["name"], "account-manager")
        self.assertEqual(
            {permission["name"] for permission in role["permissions"]},
            {"companies.read", "contacts.read"},
        )

        duplicate_role_response = await client.post(
            "/api/v1/roles",
            headers=admin_headers,
            json={"name": "account-manager", "permission_ids": []},
        )
        self.assertEqual(duplicate_role_response.status_code, 409)
        invalid_role_permissions_response = await client.post(
            "/api/v1/roles",
            headers=admin_headers,
            json={"name": "invalid-role", "permission_ids": [str(uuid4())]},
        )
        self.assertEqual(invalid_role_permissions_response.status_code, 422)
        foreign_role_response = await client.get(
            f"/api/v1/roles/{self.foreign_role_id}", headers=admin_headers
        )
        self.assertEqual(foreign_role_response.status_code, 404)
        foreign_role_delete_response = await client.delete(
            f"/api/v1/roles/{self.foreign_role_id}", headers=admin_headers
        )
        self.assertEqual(foreign_role_delete_response.status_code, 404)
        protected_admin_role_response = await client.patch(
            f"/api/v1/roles/{self.admin_role_id}",
            headers=admin_headers,
            json={"name": "not-admin"},
        )
        self.assertEqual(protected_admin_role_response.status_code, 409)

        update_role_response = await client.patch(
            f"/api/v1/roles/{role_id}",
            headers=admin_headers,
            json={
                "name": "senior-account-manager",
                "permission_ids": [permission_id_by_name["companies.read"]],
            },
        )
        self.assertEqual(update_role_response.status_code, 200)
        self.assertEqual(update_role_response.json()["name"], "senior-account-manager")
        self.assertEqual(
            [permission["name"] for permission in update_role_response.json()["permissions"]],
            ["companies.read"],
        )

        temporary_role_response = await client.post(
            "/api/v1/roles",
            headers=admin_headers,
            json={"name": "temporary-role", "permission_ids": []},
        )
        self.assertEqual(temporary_role_response.status_code, 201)
        delete_temporary_role_response = await client.delete(
            f"/api/v1/roles/{temporary_role_response.json()['id']}", headers=admin_headers
        )
        self.assertEqual(delete_temporary_role_response.status_code, 204)

        create_user_response = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "email": "managed.user@example.com",
                "password": "managed-user-password",
                "first_name": "Managed",
                "last_name": "User",
                "role_ids": [str(role_id)],
            },
        )
        self.assertEqual(create_user_response.status_code, 201)
        managed_user = create_user_response.json()
        managed_user_id = UUID(managed_user["id"])
        self.assertEqual(managed_user["email"], "managed.user@example.com")
        self.assertEqual(managed_user["roles"], [{"id": str(role_id), "name": "senior-account-manager"}])
        self.assertNotIn("password_hash", managed_user)

        duplicate_user_response = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "email": "MANAGED.USER@example.com",
                "password": "managed-user-password",
                "first_name": "Duplicate",
                "last_name": "User",
                "role_ids": [str(role_id)],
            },
        )
        self.assertEqual(duplicate_user_response.status_code, 409)
        foreign_role_user_response = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "email": "foreign.role@example.com",
                "password": "managed-user-password",
                "first_name": "Foreign",
                "last_name": "Role",
                "role_ids": [str(self.foreign_role_id)],
            },
        )
        self.assertEqual(foreign_role_user_response.status_code, 422)

        managed_headers = await self._authenticate(
            client, "managed.user@example.com", "managed-user-password"
        )
        self.assertEqual(
            (await client.get("/api/v1/users", headers=managed_headers)).status_code, 403
        )

        list_users_response = await client.get(
            "/api/v1/users",
            headers=admin_headers,
            params={"search": "managed.user", "is_active": "true", "page_size": 1},
        )
        self.assertEqual(list_users_response.status_code, 200)
        self.assertEqual(list_users_response.json()["meta"], {"page": 1, "page_size": 1, "total": 1})
        self.assertEqual(list_users_response.json()["items"][0]["id"], str(managed_user_id))
        self.assertEqual(
            (await client.get(f"/api/v1/users/{self.foreign_user_id}", headers=admin_headers)).status_code,
            404,
        )
        self.assertEqual(
            (
                await client.patch(
                    f"/api/v1/users/{self.foreign_user_id}",
                    headers=admin_headers,
                    json={"first_name": "Nope"},
                )
            ).status_code,
            404,
        )
        self.assertEqual(
            (
                await client.patch(
                    f"/api/v1/users/{self.admin_user_id}",
                    headers=admin_headers,
                    json={"is_active": False},
                )
            ).status_code,
            409,
        )

        update_user_response = await client.patch(
            f"/api/v1/users/{managed_user_id}",
            headers=admin_headers,
            json={
                "email": "MANAGED.RENAMED@example.com",
                "first_name": "Renamed",
                "is_active": False,
            },
        )
        self.assertEqual(update_user_response.status_code, 200)
        self.assertEqual(update_user_response.json()["email"], "managed.renamed@example.com")
        self.assertFalse(update_user_response.json()["is_active"])
        inactive_users_response = await client.get(
            "/api/v1/users", headers=admin_headers, params={"is_active": "false"}
        )
        self.assertEqual(inactive_users_response.status_code, 200)
        self.assertIn(
            str(managed_user_id),
            {user["id"] for user in inactive_users_response.json()["items"]},
        )
        assigned_role_delete_response = await client.delete(
            f"/api/v1/roles/{role_id}", headers=admin_headers
        )
        self.assertEqual(assigned_role_delete_response.status_code, 409)

        self.assertEqual(
            (await client.get("/api/v1/search", headers=company_searcher_headers, params={"q": "scope-token"})).status_code,
            200,
        )
        return role_id

    async def _exercise_audit_filters(
        self, client: httpx.AsyncClient, admin_headers: dict[str, str]
    ) -> None:
        query_params = {
            "search": "scope-token",
            "action": "scope-token.audit",
            "entity_type": "audit-test",
            "created_after": self.local_audit_range[0],
            "created_before": self.local_audit_range[1],
            "sort_direction": "asc",
        }
        audit_response = await client.get(
            "/api/v1/audit-logs", headers=admin_headers, params=query_params
        )
        self.assertEqual(audit_response.status_code, 200)
        audit_payload = audit_response.json()
        self.assertEqual(audit_payload["meta"]["total"], 2)
        self.assertEqual(
            [entry["id"] for entry in audit_payload["items"]],
            [str(audit_id) for audit_id in self.local_audit_ids],
        )
        self.assertTrue(
            all(entry["user"]["id"] == str(self.admin_user_id) for entry in audit_payload["items"])
        )

        foreign_user_filter_response = await client.get(
            "/api/v1/audit-logs",
            headers=admin_headers,
            params={"user_id": str(self.foreign_user_id)},
        )
        self.assertEqual(foreign_user_filter_response.status_code, 200)
        self.assertEqual(foreign_user_filter_response.json()["items"], [])

        timezone_required_response = await client.get(
            "/api/v1/audit-logs",
            headers=admin_headers,
            params={"created_after": "2026-08-12T10:00:00"},
        )
        self.assertEqual(timezone_required_response.status_code, 422)
        inverted_date_range_response = await client.get(
            "/api/v1/audit-logs",
            headers=admin_headers,
            params={
                "created_after": "2026-08-13T10:00:00+00:00",
                "created_before": "2026-08-12T10:00:00+00:00",
            },
        )
        self.assertEqual(inverted_date_range_response.status_code, 422)

    async def _exercise_search_contracts(
        self,
        client: httpx.AsyncClient,
        admin_headers: dict[str, str],
        company_searcher_headers: dict[str, str],
    ) -> None:
        search_response = await client.get(
            "/api/v1/search",
            headers=admin_headers,
            params={"q": "scope-token", "limit_per_type": 1},
        )
        self.assertEqual(search_response.status_code, 200)
        search_items = search_response.json()["items"]
        self.assertEqual(
            {item["entity_type"] for item in search_items},
            {"company", "contact", "lead", "deal", "task", "activity", "note"},
        )
        self.assertEqual({UUID(item["id"]) for item in search_items}, self.local_search_ids)

        restricted_search_response = await client.get(
            "/api/v1/search",
            headers=company_searcher_headers,
            params={"q": "scope-token", "limit_per_type": 5},
        )
        self.assertEqual(restricted_search_response.status_code, 200)
        self.assertEqual(
            {item["entity_type"] for item in restricted_search_response.json()["items"]},
            {"company"},
        )

        whitespace_search_response = await client.get(
            "/api/v1/search", headers=admin_headers, params={"q": "   "}
        )
        self.assertEqual(whitespace_search_response.status_code, 422)

    async def _exercise_profile_contracts(
        self,
        client: httpx.AsyncClient,
        admin_headers: dict[str, str],
        role_id: UUID,
    ) -> None:
        profile_response = await client.get("/api/v1/profile", headers=admin_headers)
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["id"], str(self.admin_user_id))

        duplicate_email_response = await client.patch(
            "/api/v1/profile",
            headers=admin_headers,
            json={"email": "managed.renamed@example.com"},
        )
        self.assertEqual(duplicate_email_response.status_code, 409)
        update_profile_response = await client.patch(
            "/api/v1/profile",
            headers=admin_headers,
            json={"first_name": "Verified"},
        )
        self.assertEqual(update_profile_response.status_code, 200)
        self.assertEqual(update_profile_response.json()["first_name"], "Verified")

        incorrect_password_response = await client.post(
            "/api/v1/profile/password",
            headers=admin_headers,
            json={
                "current_password": "incorrect-password",
                "new_password": "updated-admin-password",
            },
        )
        self.assertEqual(incorrect_password_response.status_code, 400)
        change_password_response = await client.post(
            "/api/v1/profile/password",
            headers=admin_headers,
            json={
                "current_password": "development-password",
                "new_password": "updated-admin-password",
            },
        )
        self.assertEqual(change_password_response.status_code, 204)
        old_password_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "development-password"},
        )
        self.assertEqual(old_password_response.status_code, 401)
        new_password_headers = await self._authenticate(
            client, "admin@example.com", "updated-admin-password"
        )
        self.assertEqual(
            (await client.get("/api/v1/roles", headers=new_password_headers)).status_code,
            200,
        )

        with self.session_factory() as database_session:
            audit_actions = {
                action
                for action in database_session.scalars(
                    AuditLog.__table__.select()
                    .with_only_columns(AuditLog.action)
                    .where(AuditLog.user_id == self.admin_user_id)
                )
            }
        self.assertTrue(
            {
                "organization.updated",
                "role.created",
                "role.updated",
                "role.deleted",
                "user.created",
                "user.updated",
                "profile.updated",
                "profile.password_changed",
            }.issubset(audit_actions)
        )
        self.assertIsInstance(role_id, UUID)

    async def _authenticate(
        self, client: httpx.AsyncClient, email: str, password: str
    ) -> dict[str, str]:
        login_response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)
        return {"Authorization": f"Bearer {login_response.json()['access_token']}"}
