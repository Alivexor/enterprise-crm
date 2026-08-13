import asyncio
import os
import tempfile
import unittest
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import patch
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
from fastapi import FastAPI, UploadFile
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.api.v1.attachments.router import router as attachments_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.notifications.router import router as notifications_router
from app.core.config import get_settings
from app.db.base import Base
from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.user import User
from app.repositories.attachment import AttachmentRepository
from app.repositories.notification import NotificationRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.notification import NotificationCreate
from app.security.password import hash_password
from app.services.attachment import AttachmentService
from app.services.audit import audit_service
from app.services.development_seed import DevelopmentSeedService
from app.services.notification import NotificationService
from app.services.references import reference_service
from app.services.storage import (
    AttachmentStorageError,
    LocalAttachmentStorage,
)


class FailingCleanupStorage:
    """Storage double which proves DB deletion is authoritative on cleanup failure."""

    async def save(
        self,
        upload: UploadFile,
        *,
        organization_id: UUID,
        max_bytes: int,
    ) -> tuple[str, int]:
        raise AssertionError("save is not used by this deletion test")

    async def delete(self, storage_key: str) -> None:
        raise AttachmentStorageError("simulated cleanup failure")

    async def open_download(self, storage_key: str) -> AsyncIterator[bytes]:
        raise AssertionError("open_download is not used by this deletion test")


class NotificationAttachmentApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_settings.cache_clear()
        cls.database_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        cls.database_file.close()
        cls.storage_directory = tempfile.TemporaryDirectory()
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
        cls.local_storage_settings = cls.settings.model_copy(
            update={
                "attachment_storage_backend": "local",
                "attachment_local_storage_path": Path(cls.storage_directory.name),
                "attachment_max_upload_bytes": 64,
            }
        )
        cls.disabled_storage_settings = cls.settings.model_copy(
            update={
                "attachment_storage_backend": "disabled",
                "attachment_local_storage_path": None,
            }
        )
        cls.tiny_upload_settings = cls.local_storage_settings.model_copy(
            update={"attachment_max_upload_bytes": 4}
        )

        with cls.session_factory() as database_session:
            DevelopmentSeedService(
                cls.settings,
                OrganizationRepository(),
                PermissionRepository(),
                RoleRepository(),
                UserRepository(),
            ).seed(database_session)
            cls._create_records(database_session)

        cls.application = FastAPI()
        cls.application.include_router(auth_router, prefix="/api/v1")
        cls.application.include_router(notifications_router, prefix="/api/v1")
        cls.application.include_router(attachments_router, prefix="/api/v1")
        cls.application.dependency_overrides[get_db] = cls._get_test_db

    @classmethod
    def tearDownClass(cls) -> None:
        cls.application.dependency_overrides.clear()
        cls.engine.dispose()
        cls.storage_directory.cleanup()
        Path(cls.database_file.name).unlink(missing_ok=True)

    @classmethod
    def _get_test_db(cls):
        database_session = cls.session_factory()
        try:
            yield database_session
        finally:
            database_session.close()

    @classmethod
    def _create_records(cls, database_session: Session) -> None:
        admin_user = UserRepository().get_by_email(
            database_session,
            str(cls.settings.default_admin_email),
            cls.settings.default_organization_id,
        )
        if admin_user is None:
            raise RuntimeError("Seeded admin user was not created")

        company = Company(
            organization_id=cls.settings.default_organization_id,
            name="Attachment Test Company",
        )
        other_user = User(
            organization_id=cls.settings.default_organization_id,
            email="notification-recipient@example.com",
            password_hash=hash_password("development-password"),
            first_name="Notification",
            last_name="Recipient",
        )
        foreign_organization = Organization(id=uuid4(), name="Other Organization")
        database_session.add_all([company, other_user, foreign_organization])
        database_session.flush()
        foreign_company = Company(
            organization_id=foreign_organization.id,
            name="Foreign Attachment Target",
        )
        database_session.add(foreign_company)
        database_session.commit()

        cls.admin_user_id = admin_user.id
        cls.other_user_id = other_user.id
        cls.company_id = company.id
        cls.foreign_company_id = foreign_company.id

    def test_notification_inbox_and_private_attachments(self) -> None:
        asyncio.run(self._exercise_notification_and_attachment_api())

    async def _exercise_notification_and_attachment_api(self) -> None:
        with self.session_factory() as database_session:
            notification_service = NotificationService(
                NotificationRepository(), reference_service, audit_service
            )
            first_notification = notification_service.create_notification(
                database_session,
                organization_id=self.settings.default_organization_id,
                notification_data=NotificationCreate(
                    user_id=self.admin_user_id,
                    type="task_assigned",
                    title="Follow up with Acme",
                    entity_type="company",
                    entity_id=self.company_id,
                ),
            )
            second_notification = notification_service.create_notification(
                database_session,
                organization_id=self.settings.default_organization_id,
                notification_data=NotificationCreate(
                    user_id=self.admin_user_id,
                    type="activity_due",
                    title="Prepare meeting",
                ),
            )
            third_notification = notification_service.create_notification(
                database_session,
                organization_id=self.settings.default_organization_id,
                notification_data=NotificationCreate(
                    user_id=self.admin_user_id,
                    type="deal_assigned",
                    title="Review renewal proposal",
                    entity_type="company",
                    entity_id=self.company_id,
                ),
            )
            foreign_recipient_notification = notification_service.create_notification(
                database_session,
                organization_id=self.settings.default_organization_id,
                notification_data=NotificationCreate(
                    user_id=self.other_user_id,
                    type="private",
                    title="Not the admin's notification",
                ),
            )
            first_notification_id = first_notification.id
            second_notification_id = second_notification.id
            third_notification_id = third_notification.id
            foreign_recipient_notification_id = foreign_recipient_notification.id

        transport = httpx.ASGITransport(app=self.application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            headers = await self._authenticate(client)

            unread_response = await client.get(
                "/api/v1/notifications", headers=headers, params={"read": "unread"}
            )
            self.assertEqual(unread_response.status_code, 200)
            unread_payload = unread_response.json()
            self.assertEqual(unread_payload["meta"]["total"], 3)
            self.assertEqual(
                {item["id"] for item in unread_payload["items"]},
                {str(first_notification_id), str(second_notification_id), str(third_notification_id)},
            )

            inaccessible_notification_response = await client.post(
                f"/api/v1/notifications/{foreign_recipient_notification_id}/read",
                headers=headers,
            )
            self.assertEqual(inaccessible_notification_response.status_code, 404)

            mark_read_response = await client.post(
                f"/api/v1/notifications/{first_notification_id}/read", headers=headers
            )
            self.assertEqual(mark_read_response.status_code, 200)
            self.assertIsNotNone(mark_read_response.json()["read_at"])

            bulk_read_response = await client.post(
                "/api/v1/notifications/read-bulk",
                headers=headers,
                json={"notification_ids": [str(second_notification_id)]},
            )
            self.assertEqual(bulk_read_response.status_code, 200)
            self.assertEqual(bulk_read_response.json()["updated"], 1)

            bulk_foreign_response = await client.post(
                "/api/v1/notifications/read-bulk",
                headers=headers,
                json={"notification_ids": [str(foreign_recipient_notification_id)]},
            )
            self.assertEqual(bulk_foreign_response.status_code, 200)
            self.assertEqual(bulk_foreign_response.json()["updated"], 0)

            mark_all_read_response = await client.post(
                "/api/v1/notifications/read-all", headers=headers
            )
            self.assertEqual(mark_all_read_response.status_code, 204)
            fully_read_response = await client.get(
                "/api/v1/notifications", headers=headers, params={"read": "read"}
            )
            self.assertEqual(fully_read_response.status_code, 200)
            self.assertEqual(fully_read_response.json()["meta"]["total"], 3)

            with patch(
                "app.api.v1.attachments.router.get_settings",
                return_value=self.local_storage_settings,
            ):
                upload_response = await client.post(
                    "/api/v1/attachments",
                    headers=headers,
                    data={
                        "entity_type": "company",
                        "entity_id": str(self.company_id),
                    },
                    files={
                        "file": (
                            "confidential-plan.txt",
                            b"private enterprise plan",
                            "text/plain",
                        )
                    },
                )
            self.assertEqual(upload_response.status_code, 201, upload_response.text)
            attachment = upload_response.json()
            self.assertNotIn("storage_key", attachment)
            self.assertEqual(attachment["original_filename"], "confidential-plan.txt")
            attachment_id = UUID(attachment["id"])
            with self.session_factory() as database_session:
                stored_attachment = database_session.get(Attachment, attachment_id)
                self.assertIsNotNone(stored_attachment)
                if stored_attachment is None:
                    raise AssertionError("attachment metadata was not persisted")
                storage_key = stored_attachment.storage_key
            storage = LocalAttachmentStorage(Path(self.storage_directory.name))
            stored_file_path = storage._path_for(storage_key)
            self.assertTrue(stored_file_path.is_file())

            with patch(
                "app.api.v1.attachments.router.get_settings",
                return_value=self.local_storage_settings,
            ):
                list_response = await client.get(
                    "/api/v1/attachments",
                    headers=headers,
                    params={
                        "entity_type": "company",
                        "entity_id": str(self.company_id),
                    },
                )
                download_response = await client.get(
                    f"/api/v1/attachments/{attachment_id}/download", headers=headers
                )
            self.assertEqual(list_response.status_code, 200)
            self.assertEqual(list_response.json()["meta"]["total"], 1)
            self.assertEqual(download_response.status_code, 200)
            self.assertEqual(download_response.content, b"private enterprise plan")
            self.assertEqual(download_response.headers["x-content-type-options"], "nosniff")
            self.assertEqual(download_response.headers["cache-control"], "private, no-store")

            with patch(
                "app.api.v1.attachments.router.get_settings",
                return_value=self.disabled_storage_settings,
            ):
                disabled_download_response = await client.get(
                    f"/api/v1/attachments/{attachment_id}/download", headers=headers
                )
            self.assertEqual(disabled_download_response.status_code, 503)

            with patch(
                "app.api.v1.attachments.router.get_settings",
                return_value=self.tiny_upload_settings,
            ):
                oversized_upload_response = await client.post(
                    "/api/v1/attachments",
                    headers=headers,
                    data={
                        "entity_type": "company",
                        "entity_id": str(self.company_id),
                    },
                    files={"file": ("too-large.txt", b"12345", "text/plain")},
                )
            self.assertEqual(oversized_upload_response.status_code, 413)

            with patch(
                "app.api.v1.attachments.router.get_settings",
                return_value=self.local_storage_settings,
            ):
                foreign_target_response = await client.post(
                    "/api/v1/attachments",
                    headers=headers,
                    data={
                        "entity_type": "company",
                        "entity_id": str(self.foreign_company_id),
                    },
                    files={"file": ("private.txt", b"secret", "text/plain")},
                )
                delete_response = await client.delete(
                    f"/api/v1/attachments/{attachment_id}", headers=headers
                )
            self.assertEqual(foreign_target_response.status_code, 404)
            self.assertEqual(delete_response.status_code, 204)
            self.assertFalse(stored_file_path.exists())

            with patch(
                "app.api.v1.attachments.router.get_settings",
                return_value=self.local_storage_settings,
            ):
                deleted_metadata_response = await client.get(
                    f"/api/v1/attachments/{attachment_id}", headers=headers
                )
            self.assertEqual(deleted_metadata_response.status_code, 404)

        await self._verify_cleanup_failure_keeps_metadata_state_consistent()
        with self.session_factory() as database_session:
            audit_actions = set(
                database_session.scalars(
                    select(AuditLog.action).where(AuditLog.user_id == self.admin_user_id)
                )
            )
            self.assertTrue(
                {
                    "notification.read",
                    "notification.read_bulk",
                    "notification.read_all",
                    "attachment.created",
                    "attachment.deleted",
                }.issubset(audit_actions)
            )

    async def _verify_cleanup_failure_keeps_metadata_state_consistent(self) -> None:
        repository = AttachmentRepository()
        with self.session_factory() as database_session:
            attachment = repository.create(
                database_session,
                organization_id=self.settings.default_organization_id,
                uploaded_by_user_id=self.admin_user_id,
                entity_type="company",
                entity_id=self.company_id,
                original_filename="orphan.txt",
                storage_key=f"{self.settings.default_organization_id}/orphan-object",
                content_type="text/plain",
                size_bytes=1,
            )
            database_session.commit()
            attachment_id = attachment.id

            service = AttachmentService(
                repository,
                FailingCleanupStorage(),
                audit_service,
                max_upload_bytes=64,
            )
            await service.delete_attachment(
                database_session,
                organization_id=self.settings.default_organization_id,
                actor_id=self.admin_user_id,
                attachment_id=attachment_id,
            )
            self.assertIsNone(
                repository.get_by_id(
                    database_session,
                    organization_id=self.settings.default_organization_id,
                    attachment_id=attachment_id,
                )
            )

    async def _authenticate(self, client: httpx.AsyncClient) -> dict[str, str]:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "development-password"},
        )
        self.assertEqual(login_response.status_code, 200)
        return {"Authorization": f"Bearer {login_response.json()['access_token']}"}
