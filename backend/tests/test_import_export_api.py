import asyncio
import csv
import os
import tempfile
import unittest
from io import StringIO
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
os.environ["IMPORT_EXPORT_MAX_UPLOAD_BYTES"] = "512"
os.environ["IMPORT_EXPORT_MAX_ROWS"] = "3"

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
from app.api.v1.import_export.router import router as import_export_router
from app.core.config import get_settings
from app.db.base import Base
from app.models.company import Company
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.security.password import hash_password
from app.security.tokens import create_access_token
from app.services.development_seed import DevelopmentSeedService


class ImportExportApiTestCase(unittest.TestCase):
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
        with cls.session_factory() as database_session:
            DevelopmentSeedService(
                get_settings(),
                OrganizationRepository(),
                PermissionRepository(),
                RoleRepository(),
                UserRepository(),
            ).seed(database_session)
            cls._create_foreign_company(database_session)
            cls._create_limited_user(database_session)
            cls._create_import_export_only_user(database_session)

        cls.application = FastAPI()
        cls.application.include_router(auth_router, prefix="/api/v1")
        cls.application.include_router(companies_router, prefix="/api/v1")
        cls.application.include_router(contacts_router, prefix="/api/v1")
        cls.application.include_router(import_export_router, prefix="/api/v1")
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
    def _create_foreign_company(cls, database_session: Session) -> None:
        foreign_organization = Organization(id=uuid4(), name="Other Organization")
        database_session.add(foreign_organization)
        database_session.flush()
        foreign_company = Company(
            organization_id=foreign_organization.id,
            name="Foreign Company",
        )
        database_session.add(foreign_company)
        database_session.commit()
        cls.foreign_company_id = foreign_company.id

    @classmethod
    def _create_limited_user(cls, database_session: Session) -> None:
        cls.limited_user_id = UserRepository().create(
            database_session,
            UserCreate(
                organization_id=get_settings().default_organization_id,
                email="import-export-limited@example.com",
                password_hash=hash_password("development-password"),
                first_name="Limited",
                last_name="User",
            ),
        ).id
        database_session.commit()

    @classmethod
    def _create_import_export_only_user(cls, database_session: Session) -> None:
        organization_id = get_settings().default_organization_id
        role = Role(organization_id=organization_id, name="import-export-only")
        database_session.add(role)
        role.permissions = PermissionRepository().get_by_names(
            database_session,
            ("imports.create", "exports.create"),
        )
        user = UserRepository().create(
            database_session,
            UserCreate(
                organization_id=organization_id,
                email="import-export-operations@example.com",
                password_hash=hash_password("development-password"),
                first_name="Import",
                last_name="Export",
            ),
        )
        user.roles.append(role)
        database_session.commit()
        cls.import_export_only_user_id = user.id

    def test_csv_import_export_security_atomicity_and_audit(self) -> None:
        asyncio.run(self._exercise_csv_import_export())

    async def _exercise_csv_import_export(self) -> None:
        transport = httpx.ASGITransport(app=self.application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            headers = await self._authenticate(client)
            limited_access_token = create_access_token(
                self.limited_user_id,
                get_settings().default_organization_id,
                get_settings(),
            )
            limited_headers = {"Authorization": f"Bearer {limited_access_token}"}
            self.assertEqual(
                (await client.get("/api/v1/import-export/companies", headers=limited_headers)).status_code,
                403,
            )
            self.assertEqual(
                (
                    await client.post(
                        "/api/v1/import-export/companies",
                        headers=limited_headers,
                        files={"file": ("companies.csv", b"name,website,industry\nA,,", "text/csv")},
                    )
                ).status_code,
                403,
            )

            import_export_only_token = create_access_token(
                self.import_export_only_user_id,
                get_settings().default_organization_id,
                get_settings(),
            )
            import_export_only_headers = {
                "Authorization": f"Bearer {import_export_only_token}"
            }
            self.assertEqual(
                (
                    await client.get(
                        "/api/v1/import-export/companies",
                        headers=import_export_only_headers,
                    )
                ).status_code,
                403,
            )
            self.assertEqual(
                (
                    await client.post(
                        "/api/v1/import-export/companies",
                        headers=import_export_only_headers,
                        files={
                            "file": (
                                "companies.csv",
                                b"name,website,industry\nScoped,,\n",
                                "text/csv",
                            )
                        },
                    )
                ).status_code,
                403,
            )
            self.assertEqual(
                (
                    await client.get(
                        "/api/v1/import-export/contacts",
                        headers=import_export_only_headers,
                    )
                ).status_code,
                403,
            )
            self.assertEqual(
                (
                    await client.post(
                        "/api/v1/import-export/contacts",
                        headers=import_export_only_headers,
                        files={
                            "file": (
                                "contacts.csv",
                                b"company_id,company_name,first_name,last_name,email,phone\n",
                                "text/csv",
                            )
                        },
                    )
                ).status_code,
                403,
            )

            empty_import_response = await self._upload_csv(
                client,
                headers,
                "companies",
                "name,website,industry\n",
            )
            self.assertEqual(empty_import_response.status_code, 422)

            invalid_header_response = await self._upload_csv(
                client,
                headers,
                "companies",
                "name,website\nAcme,https://acme.example\n",
            )
            self.assertEqual(invalid_header_response.status_code, 422)

            invalid_atomic_response = await self._upload_csv(
                client,
                headers,
                "companies",
                "name,website,industry\n"
                "Good Co,https://good.example,Software\n"
                "Bad Co,javascript:alert(1),Software\n",
            )
            self.assertEqual(invalid_atomic_response.status_code, 422)
            self.assertEqual(
                (
                    await client.get(
                        "/api/v1/companies", headers=headers, params={"search": "Good Co"}
                    )
                ).json()["meta"]["total"],
                0,
            )

            companies_import_response = await self._upload_csv(
                client,
                headers,
                "companies",
                "name,website,industry\n"
                "Formula Co,https://formula.example,=Dangerous\n"
                "Northwind,https://northwind.example,Manufacturing\n",
            )
            self.assertEqual(companies_import_response.status_code, 201)
            self.assertEqual(companies_import_response.json()["created_count"], 2)

            duplicate_company_response = await self._upload_csv(
                client,
                headers,
                "companies",
                "name,website,industry\nNorthwind,https://northwind.example,Manufacturing\n",
            )
            self.assertEqual(duplicate_company_response.status_code, 422)
            duplicate_errors = duplicate_company_response.json()["detail"]["errors"]
            self.assertEqual(duplicate_errors[0]["row_number"], 2)
            self.assertEqual(duplicate_errors[0]["field"], "name")

            companies_export_response = await client.get(
                "/api/v1/import-export/companies", headers=headers
            )
            self.assertEqual(companies_export_response.status_code, 200)
            self.assertEqual(
                companies_export_response.headers["content-type"].split(";")[0],
                "text/csv",
            )
            self.assertIn("attachment; filename=\"companies.csv\"", companies_export_response.headers["content-disposition"])
            exported_companies = list(csv.DictReader(StringIO(companies_export_response.text)))
            formula_row = next(row for row in exported_companies if row["name"] == "Formula Co")
            self.assertEqual(formula_row["industry"], "'=Dangerous")

            northwind_id = UUID(
                next(row for row in exported_companies if row["name"] == "Northwind")["id"]
            ) if "id" in exported_companies[0] else await self._company_id(client, headers, "Northwind")

            contacts_import_response = await self._upload_csv(
                client,
                headers,
                "contacts",
                "company_id,company_name,first_name,last_name,email,phone\n"
                f"{northwind_id},Northwind,Ada,Lovelace,ada@example.com,+123456\n"
                ",Formula Co,Grace,Hopper,grace@example.com,+987654\n",
            )
            self.assertEqual(contacts_import_response.status_code, 201)
            self.assertEqual(contacts_import_response.json()["created_count"], 2)

            foreign_contact_response = await self._upload_csv(
                client,
                headers,
                "contacts",
                "company_id,company_name,first_name,last_name,email,phone\n"
                f"{self.foreign_company_id},,Foreign,Contact,foreign@example.com,+111\n",
            )
            self.assertEqual(foreign_contact_response.status_code, 422)
            self.assertEqual(
                (await client.get("/api/v1/contacts", headers=headers)).json()["meta"]["total"],
                2,
            )

            contacts_export_response = await client.get(
                "/api/v1/import-export/contacts", headers=headers
            )
            self.assertEqual(contacts_export_response.status_code, 200)
            exported_contacts = list(csv.DictReader(StringIO(contacts_export_response.text)))
            self.assertEqual(len(exported_contacts), 2)
            self.assertIn("company_id", exported_contacts[0])
            self.assertIn("company_name", exported_contacts[0])

            too_large_response = await self._upload_csv(
                client,
                headers,
                "companies",
                "name,website,industry\n" + ("A" * 600),
            )
            self.assertEqual(too_large_response.status_code, 413)

            audit_response = await client.get("/api/v1/audit-logs", headers=headers)
            self.assertEqual(audit_response.status_code, 200)
            actions = {entry["action"] for entry in audit_response.json()["items"]}
            self.assertTrue(
                {
                    "companies.imported",
                    "companies.exported",
                    "contacts.imported",
                    "contacts.exported",
                }.issubset(actions)
            )

    async def _authenticate(self, client: httpx.AsyncClient) -> dict[str, str]:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "development-password"},
        )
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    async def _upload_csv(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        resource: str,
        content: str,
    ) -> httpx.Response:
        return await client.post(
            f"/api/v1/import-export/{resource}",
            headers=headers,
            files={"file": (f"{resource}.csv", content.encode("utf-8"), "text/csv")},
        )

    async def _company_id(
        self, client: httpx.AsyncClient, headers: dict[str, str], name: str
    ) -> UUID:
        response = await client.get(
            "/api/v1/companies", headers=headers, params={"search": name}
        )
        self.assertEqual(response.status_code, 200)
        return UUID(response.json()["items"][0]["id"])
