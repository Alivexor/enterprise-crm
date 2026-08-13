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
os.environ["JWT_SECRET"] = "0123456789abcdef0123456789abcdef0123456789abcdef"
os.environ["DEFAULT_ROLE_NAME"] = ""

test_database_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
test_database_file.close()
os.environ["DATABASE_URL"] = (
    f"sqlite+pysqlite:///{Path(test_database_file.name).as_posix()}"
)

import httpx

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.company import Company
from app.models.organization import Organization
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.security.password import hash_password
from app.security.permission_catalog import PermissionName
from app.security.tokens import create_access_token
from app.security.totp import generate_code
from app.services.development_seed import DevelopmentSeedService


class CompanyApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(engine)
        seed_service = DevelopmentSeedService(
            get_settings(),
            OrganizationRepository(),
            PermissionRepository(),
            RoleRepository(),
            UserRepository(),
        )
        with SessionLocal() as database_session:
            seed_service.seed(database_session)

            foreign_organization = Organization(id=uuid4(), name="Other Organization")
            database_session.add(foreign_organization)
            database_session.flush()
            foreign_company = Company(
                organization_id=foreign_organization.id,
                name="Private Company",
            )
            database_session.add(foreign_company)

            limited_user = UserRepository().create(
                database_session,
                UserCreate(
                    organization_id=get_settings().default_organization_id,
                    email="limited@example.com",
                    password_hash=hash_password("development-password"),
                    first_name="Limited",
                    last_name="User",
                ),
            )
            search_only_role = RoleRepository().create(
                database_session,
                get_settings().default_organization_id,
                "search-only",
            )
            search_only_role.permissions = PermissionRepository().get_by_names(
                database_session,
                (PermissionName.SEARCH_READ.value,),
            )
            search_only_user = UserRepository().create(
                database_session,
                UserCreate(
                    organization_id=get_settings().default_organization_id,
                    email="search-only@example.com",
                    password_hash=hash_password("development-password"),
                    first_name="Search",
                    last_name="Only",
                ),
            )
            search_only_user.roles.append(search_only_role)
            database_session.commit()
            cls.foreign_company_id = foreign_company.id
            cls.limited_user_id = limited_user.id
            cls.search_only_user_id = search_only_user.id

    @classmethod
    def tearDownClass(cls) -> None:
        engine.dispose()
        Path(test_database_file.name).unlink(missing_ok=True)

    def test_company_crud_and_organization_isolation(self) -> None:
        asyncio.run(self._exercise_company_api())

    def test_authentication_refresh_and_company_permissions(self) -> None:
        asyncio.run(self._exercise_authentication_and_permissions())

    def test_core_crm_administration_and_workflow(self) -> None:
        asyncio.run(self._exercise_core_crm_workflow())

    async def _exercise_authentication_and_permissions(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "development-password",
                },
            )
            self.assertEqual(login_response.status_code, 200)
            token_response = login_response.json()
            access_token = token_response["access_token"]
            refresh_token = token_response["refresh_token"]

            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            self.assertEqual(me_response.status_code, 200)
            permission_names = {
                permission["name"] for permission in me_response.json()["permissions"]
            }
            self.assertIn(PermissionName.COMPANIES_READ.value, permission_names)
            self.assertIn(PermissionName.AUDIT_LOGS_READ.value, permission_names)

            refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            self.assertEqual(refresh_response.status_code, 200)
            refreshed_tokens = refresh_response.json()
            self.assertNotEqual(refreshed_tokens["access_token"], access_token)
            self.assertNotEqual(refreshed_tokens["refresh_token"], refresh_token)

            refreshed_me_response = await client.get(
                "/api/v1/auth/me",
                headers={
                    "Authorization": f"Bearer {refreshed_tokens['access_token']}"
                },
            )
            self.assertEqual(refreshed_me_response.status_code, 200)

            wrong_token_type_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": access_token},
            )
            self.assertEqual(wrong_token_type_response.status_code, 401)

            registration_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "new.user@example.com",
                    "password": "new-development-password",
                    "first_name": "New",
                    "last_name": "User",
                },
            )
            self.assertEqual(registration_response.status_code, 403)

            limited_user_access_token = create_access_token(
                self.limited_user_id,
                get_settings().default_organization_id,
                get_settings(),
            )
            unauthorized_companies_response = await client.get(
                "/api/v1/companies",
                headers={"Authorization": f"Bearer {limited_user_access_token}"},
            )
            self.assertEqual(unauthorized_companies_response.status_code, 403)

            search_only_access_token = create_access_token(
                self.search_only_user_id,
                get_settings().default_organization_id,
                get_settings(),
            )
            search_only_response = await client.get(
                "/api/v1/search?q=private",
                headers={"Authorization": f"Bearer {search_only_access_token}"},
            )
            self.assertEqual(search_only_response.status_code, 200)
            self.assertEqual(search_only_response.json()["items"], [])


    def test_mfa_lifecycle_and_one_time_recovery_code(self) -> None:
        asyncio.run(self._exercise_mfa_lifecycle())

    async def _exercise_mfa_lifecycle(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "development-password"},
            )
            self.assertEqual(login_response.status_code, 200)
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            setup_response = await client.post("/api/v1/auth/mfa/setup", headers=headers)
            self.assertEqual(setup_response.status_code, 200)
            secret = setup_response.json()["secret"]
            code = generate_code(secret)

            confirm_response = await client.post(
                "/api/v1/auth/mfa/confirm", headers=headers, json={"code": code}
            )
            self.assertEqual(confirm_response.status_code, 200)
            recovery_codes = confirm_response.json()["recovery_codes"]
            self.assertEqual(len(recovery_codes), 10)

            missing_code = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "development-password"},
            )
            self.assertEqual(missing_code.status_code, 401)
            self.assertEqual(missing_code.headers.get("x-crm-mfa"), "required")

            wrong_code = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "development-password", "mfa_code": "000000"},
            )
            self.assertEqual(wrong_code.status_code, 401)

            totp_login = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "development-password", "mfa_code": generate_code(secret)},
            )
            self.assertEqual(totp_login.status_code, 200)

            recovery_code = recovery_codes[0]
            recovery_login = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "development-password", "mfa_code": recovery_code},
            )
            self.assertEqual(recovery_login.status_code, 200)

            reused_recovery = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "development-password", "mfa_code": recovery_code},
            )
            self.assertEqual(reused_recovery.status_code, 401)

            disable_headers = {"Authorization": f"Bearer {totp_login.json()['access_token']}"}
            disable_response = await client.post(
                "/api/v1/auth/mfa/disable",
                headers=disable_headers,
                json={"password": "development-password", "code": generate_code(secret)},
            )
            self.assertEqual(disable_response.status_code, 204)

            final_login = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "development-password"},
            )
            self.assertEqual(final_login.status_code, 200)

    async def _exercise_company_api(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "development-password",
                },
            )
            self.assertEqual(login_response.status_code, 200)
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            create_response = await client.post(
                "/api/v1/companies",
                headers=headers,
                json={
                    "name": "Acme Corporation",
                    "website": "https://acme.example",
                    "industry": "Manufacturing",
                },
            )
            self.assertEqual(create_response.status_code, 201)
            company = create_response.json()
            self.assertEqual(company["name"], "Acme Corporation")
            self.assertEqual(
                company["organization_id"],
                "00000000-0000-0000-0000-000000000001",
            )

            list_response = await client.get("/api/v1/companies", headers=headers)
            self.assertEqual(list_response.status_code, 200)
            self.assertEqual(
                [item["id"] for item in list_response.json()["items"]],
                [company["id"]],
            )

            detail_response = await client.get(
                f"/api/v1/companies/{company['id']}", headers=headers
            )
            self.assertEqual(detail_response.status_code, 200)
            self.assertEqual(detail_response.json()["website"], "https://acme.example")

            update_response = await client.patch(
                f"/api/v1/companies/{company['id']}",
                headers=headers,
                json={"industry": "Software", "website": None},
            )
            self.assertEqual(update_response.status_code, 200)
            self.assertEqual(update_response.json()["industry"], "Software")
            self.assertIsNone(update_response.json()["website"])

            invalid_website_response = await client.patch(
                f"/api/v1/companies/{company['id']}",
                headers=headers,
                json={"website": "javascript:alert(1)"},
            )
            self.assertEqual(invalid_website_response.status_code, 422)

            foreign_response = await client.get(
                f"/api/v1/companies/{self.foreign_company_id}", headers=headers
            )
            self.assertEqual(foreign_response.status_code, 404)

            delete_response = await client.delete(
                f"/api/v1/companies/{company['id']}", headers=headers
            )
            self.assertEqual(delete_response.status_code, 204)

            missing_response = await client.get(
                f"/api/v1/companies/{company['id']}", headers=headers
            )
            self.assertEqual(missing_response.status_code, 404)

    async def _exercise_core_crm_workflow(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "development-password",
                },
            )
            self.assertEqual(login_response.status_code, 200)
            headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

            organization_response = await client.get(
                "/api/v1/organization", headers=headers
            )
            self.assertEqual(organization_response.status_code, 200)
            self.assertEqual(
                organization_response.json()["id"],
                "00000000-0000-0000-0000-000000000001",
            )

            roles_response = await client.get("/api/v1/roles", headers=headers)
            self.assertEqual(roles_response.status_code, 200)
            admin_role = next(
                role for role in roles_response.json() if role["name"] == "admin"
            )

            managed_user_response = await client.post(
                "/api/v1/users",
                headers=headers,
                json={
                    "email": "workflow.user@example.com",
                    "password": "workflow-password",
                    "first_name": "Workflow",
                    "last_name": "User",
                    "role_ids": [admin_role["id"]],
                },
            )
            self.assertEqual(managed_user_response.status_code, 201)
            managed_user = managed_user_response.json()

            company_response = await client.post(
                "/api/v1/companies",
                headers=headers,
                json={"name": "Workflow Company", "industry": "Software"},
            )
            self.assertEqual(company_response.status_code, 201)
            company = company_response.json()

            contact_response = await client.post(
                "/api/v1/contacts",
                headers=headers,
                json={
                    "company_id": company["id"],
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.com",
                },
            )
            self.assertEqual(contact_response.status_code, 201)
            contact = contact_response.json()

            lead_response = await client.post(
                "/api/v1/leads",
                headers=headers,
                json={
                    "title": "Platform expansion",
                    "source": "referral",
                    "company_id": company["id"],
                    "contact_id": contact["id"],
                    "assigned_user_id": managed_user["id"],
                },
            )
            self.assertEqual(lead_response.status_code, 201)
            lead = lead_response.json()

            task_response = await client.post(
                "/api/v1/tasks",
                headers=headers,
                json={
                    "title": "Prepare account plan",
                    "priority": "high",
                    "assigned_user_id": managed_user["id"],
                },
            )
            self.assertEqual(task_response.status_code, 201)

            activity_response = await client.post(
                "/api/v1/activities",
                headers=headers,
                json={
                    "type": "call",
                    "title": "Discovery call",
                    "company_id": company["id"],
                    "contact_id": contact["id"],
                    "lead_id": lead["id"],
                    "user_id": managed_user["id"],
                },
            )
            self.assertEqual(activity_response.status_code, 201)

            company_activity_response = await client.get(
                f"/api/v1/activities?company_id={company['id']}&page=1&page_size=10",
                headers=headers,
            )
            self.assertEqual(company_activity_response.status_code, 200)
            self.assertEqual(company_activity_response.json()["meta"]["total"], 1)

            assignee_access_token = create_access_token(
                UUID(managed_user["id"]),
                get_settings().default_organization_id,
                get_settings(),
            )
            assignee_headers = {
                "Authorization": f"Bearer {assignee_access_token}",
            }
            notifications_response = await client.get(
                "/api/v1/notifications?read=unread", headers=assignee_headers
            )
            self.assertEqual(notifications_response.status_code, 200)
            notifications = notifications_response.json()["items"]
            notification_types = {notification["type"] for notification in notifications}
            self.assertTrue(
                {"lead_assigned", "task_assigned", "activity_assigned"}.issubset(
                    notification_types
                )
            )
            read_notification_response = await client.post(
                f"/api/v1/notifications/{notifications[0]['id']}/read",
                headers=assignee_headers,
            )
            self.assertEqual(read_notification_response.status_code, 200)
            mark_all_notifications_read_response = await client.post(
                "/api/v1/notifications/read-all", headers=assignee_headers
            )
            self.assertEqual(mark_all_notifications_read_response.status_code, 204)

            contacts_response = await client.get(
                "/api/v1/contacts?search=ada&page=1&page_size=10", headers=headers
            )
            self.assertEqual(contacts_response.status_code, 200)
            self.assertEqual(contacts_response.json()["meta"]["total"], 1)

            leads_response = await client.get(
                "/api/v1/leads?status=new&page=1&page_size=10", headers=headers
            )
            self.assertEqual(leads_response.status_code, 200)
            self.assertEqual(leads_response.json()["meta"]["total"], 1)

            dashboard_response = await client.get("/api/v1/dashboard", headers=headers)
            self.assertEqual(dashboard_response.status_code, 200)
            dashboard_metrics = {
                metric["label"]: metric["value"]
                for metric in dashboard_response.json()["metrics"]
            }
            self.assertGreaterEqual(dashboard_metrics["Companies"], 1)
            self.assertGreaterEqual(dashboard_metrics["Contacts"], 1)

            operational_health_response = await client.get(
                "/api/v1/dashboard/health", headers=headers
            )
            self.assertEqual(operational_health_response.status_code, 200)
            operational_health = operational_health_response.json()
            self.assertIn("overdue_tasks", operational_health)
            self.assertIn("weighted_pipeline_value", operational_health)
            self.assertIn("lead_conversion_rate", operational_health)
            self.assertGreaterEqual(float(operational_health["open_pipeline_value"]), 0)

            search_response = await client.get(
                "/api/v1/search?q=workflow", headers=headers
            )
            self.assertEqual(search_response.status_code, 200)
            self.assertIn(
                "company",
                {item["entity_type"] for item in search_response.json()["items"]},
            )

            task_search_response = await client.get(
                "/api/v1/search?q=account", headers=headers
            )
            self.assertEqual(task_search_response.status_code, 200)
            self.assertIn(
                "task",
                {
                    item["entity_type"]
                    for item in task_search_response.json()["items"]
                },
            )

            audit_response = await client.get(
                "/api/v1/audit-logs?page=1&page_size=100", headers=headers
            )
            self.assertEqual(audit_response.status_code, 200)
            audit_actions = {item["action"] for item in audit_response.json()["items"]}
            self.assertTrue(
                {
                    "contact.created",
                    "lead.created",
                    "task.created",
                    "activity.created",
                }.issubset(audit_actions)
            )
            filtered_audit_response = await client.get(
                "/api/v1/audit-logs?entity_type=task&sort_direction=asc",
                headers=headers,
            )
            self.assertEqual(filtered_audit_response.status_code, 200)
            self.assertTrue(
                all(
                    item["entity_type"] == "task"
                    for item in filtered_audit_response.json()["items"]
                )
            )
