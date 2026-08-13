import asyncio
import os
import tempfile
import unittest
from pathlib import Path

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
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.api.v1.auth.router import router as auth_router
from app.api.v1.users.router import profile_router, router as users_router
from app.core.config import get_settings
from app.db.base import Base
from app.models.refresh_session import RefreshSession
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.security.password import hash_password
from app.security.tokens import TokenType, decode_token, hash_token_jti
from app.services.development_seed import DevelopmentSeedService


class RefreshSessionApiTestCase(unittest.TestCase):
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
            managed_user = UserRepository().create(
                database_session,
                UserCreate(
                    organization_id=get_settings().default_organization_id,
                    email="managed-user@example.com",
                    password_hash=hash_password("managed-user-password"),
                    first_name="Managed",
                    last_name="User",
                ),
            )
            database_session.commit()
            cls.managed_user_id = managed_user.id

        cls.application = FastAPI()
        cls.application.include_router(auth_router, prefix="/api/v1")
        cls.application.include_router(users_router, prefix="/api/v1")
        cls.application.include_router(profile_router, prefix="/api/v1")
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

    def test_refresh_rotation_reuse_logout_and_deactivation(self) -> None:
        asyncio.run(self._exercise_refresh_session_lifecycle())

    async def _exercise_refresh_session_lifecycle(self) -> None:
        transport = httpx.ASGITransport(app=self.application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            initial_login = await self._login(client)
            initial_refresh_token = initial_login["refresh_token"]
            initial_session = self._get_session_for_token(initial_refresh_token)
            initial_payload = decode_token(
                initial_refresh_token,
                TokenType.REFRESH,
                get_settings(),
            )
            self.assertEqual(len(initial_session.token_jti_hash), 64)
            self.assertEqual(
                initial_session.token_jti_hash,
                hash_token_jti(initial_payload.jti),
            )
            self.assertNotIn("refresh_token", RefreshSession.__table__.columns)
            self.assertIsNone(initial_session.revoked_at)

            rotated_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": initial_refresh_token},
            )
            self.assertEqual(rotated_response.status_code, 200)
            rotated_refresh_token = rotated_response.json()["refresh_token"]
            self.assertNotEqual(rotated_refresh_token, initial_refresh_token)

            rotated_session = self._get_session_for_token(rotated_refresh_token)
            self.assertEqual(rotated_session.family_id, initial_session.family_id)
            self.assertIsNotNone(
                self._get_session_for_token(initial_refresh_token).revoked_at
            )
            self.assertIsNone(rotated_session.revoked_at)

            reused_token_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": initial_refresh_token},
            )
            self.assertEqual(reused_token_response.status_code, 401)
            self.assertTrue(
                self._family_sessions_are_revoked(initial_session.family_id)
            )

            descendant_refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": rotated_refresh_token},
            )
            self.assertEqual(descendant_refresh_response.status_code, 401)

            logout_login = await self._login(client)
            logout_refresh_token = logout_login["refresh_token"]
            logout_session = self._get_session_for_token(logout_refresh_token)
            logout_response = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": logout_refresh_token},
            )
            self.assertEqual(logout_response.status_code, 204)
            repeated_logout_response = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": logout_refresh_token},
            )
            self.assertEqual(repeated_logout_response.status_code, 204)
            self.assertTrue(
                self._family_sessions_are_revoked(logout_session.family_id)
            )
            logged_out_refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": logout_refresh_token},
            )
            self.assertEqual(logged_out_refresh_response.status_code, 401)

            password_change_login = await self._login(client)
            password_change_refresh_token = password_change_login["refresh_token"]
            password_change_session = self._get_session_for_token(
                password_change_refresh_token
            )
            password_change_response = await client.post(
                "/api/v1/profile/password",
                headers={
                    "Authorization": f"Bearer {password_change_login['access_token']}"
                },
                json={
                    "current_password": "development-password",
                    "new_password": "changed-development-password",
                },
            )
            self.assertEqual(password_change_response.status_code, 204)
            self.assertTrue(
                self._family_sessions_are_revoked(password_change_session.family_id)
            )
            password_changed_refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": password_change_refresh_token},
            )
            self.assertEqual(password_changed_refresh_response.status_code, 401)

            administrator_login = await self._login(
                client,
                password="changed-development-password",
            )
            managed_user_login = await self._login(
                client,
                email="managed-user@example.com",
                password="managed-user-password",
            )
            managed_user_refresh_token = managed_user_login["refresh_token"]
            managed_user_session = self._get_session_for_token(
                managed_user_refresh_token
            )
            deactivate_response = await client.patch(
                f"/api/v1/users/{self.managed_user_id}",
                headers={
                    "Authorization": f"Bearer {administrator_login['access_token']}"
                },
                json={"is_active": False},
            )
            self.assertEqual(deactivate_response.status_code, 200)
            deactivated_refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": managed_user_refresh_token},
            )
            self.assertEqual(deactivated_refresh_response.status_code, 401)
            self.assertTrue(
                self._family_sessions_are_revoked(managed_user_session.family_id)
            )
            reactivate_response = await client.patch(
                f"/api/v1/users/{self.managed_user_id}",
                headers={
                    "Authorization": f"Bearer {administrator_login['access_token']}"
                },
                json={"is_active": True},
            )
            self.assertEqual(reactivate_response.status_code, 200)
            resurrected_refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": managed_user_refresh_token},
            )
            self.assertEqual(resurrected_refresh_response.status_code, 401)

    @staticmethod
    async def _login(
        client: httpx.AsyncClient,
        *,
        email: str = "admin@example.com",
        password: str = "development-password",
    ) -> dict[str, str]:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        if response.status_code != 200:
            raise AssertionError(f"Login returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise AssertionError("Login did not return a JSON object")
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")
        if not isinstance(access_token, str) or not isinstance(refresh_token, str):
            raise AssertionError("Login did not return authentication tokens")
        return {"access_token": access_token, "refresh_token": refresh_token}

    def _get_session_for_token(self, refresh_token: str) -> RefreshSession:
        settings = get_settings()
        payload = decode_token(refresh_token, TokenType.REFRESH, settings)
        with self.session_factory() as database_session:
            refresh_session = database_session.scalar(
                select(RefreshSession).where(
                    RefreshSession.token_jti_hash == hash_token_jti(payload.jti),
                    RefreshSession.organization_id == payload.organization_id,
                    RefreshSession.user_id == payload.sub,
                )
            )
            if refresh_session is None:
                raise AssertionError("Refresh-token session was not persisted")
            database_session.expunge(refresh_session)
            return refresh_session

    def _family_sessions_are_revoked(self, family_id: object) -> bool:
        with self.session_factory() as database_session:
            sessions = list(
                database_session.scalars(
                    select(RefreshSession).where(RefreshSession.family_id == family_id)
                )
            )
            return bool(sessions) and all(
                refresh_session.revoked_at is not None
                for refresh_session in sessions
            )
