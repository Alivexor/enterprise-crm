"""Use cases for securely attaching private files to CRM records."""

import re
import unicodedata
from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.note import Note
from app.models.task import Task
from app.models.activity import Activity
from app.repositories.attachment import AttachmentRepository
from app.services.audit import AuditService, audit_service
from app.services.storage import (
    AttachmentStorage,
    AttachmentStorageError,
)

_DISALLOWED_FILENAME_CHARACTERS = re.compile(r"[\x00-\x1f\x7f/\\]+")
_WHITESPACE = re.compile(r"\s+")
_CONTENT_TYPE = re.compile(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$")


class AttachmentNotFoundError(Exception):
    """Raised when an attachment is not accessible in the current organization."""


class AttachmentTargetNotFoundError(Exception):
    """Raised when a target CRM entity is not accessible in the organization."""


class AttachmentValidationError(Exception):
    """Raised when metadata or an upload is unsafe or incomplete."""


class AttachmentConflictError(Exception):
    """Raised when metadata cannot be persisted after a completed upload."""


class AttachmentStorageService(Protocol):
    async def save(
        self,
        upload: UploadFile,
        *,
        organization_id: UUID,
        max_bytes: int,
    ) -> tuple[str, int]: ...

    async def delete(self, storage_key: str) -> None: ...

    async def open_download(self, storage_key: str) -> AsyncIterator[bytes]: ...


class AttachmentService:
    def __init__(
        self,
        attachment_repository: AttachmentRepository,
        storage: AttachmentStorageService,
        audit_service: AuditService,
        *,
        max_upload_bytes: int,
    ) -> None:
        self.attachment_repository = attachment_repository
        self.storage = storage
        self.audit_service = audit_service
        self.max_upload_bytes = max_upload_bytes

    async def create_attachment(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        entity_type: str,
        entity_id: UUID,
        upload: UploadFile,
    ) -> Attachment:
        self._require_target(database_session, organization_id, entity_type, entity_id)
        filename = self._sanitize_filename(upload.filename)
        content_type = self._normalize_content_type(upload.content_type)
        self._reject_declared_oversize(upload)

        storage_key: str | None = None
        try:
            storage_key, size_bytes = await self.storage.save(
                upload,
                organization_id=organization_id,
                max_bytes=self.max_upload_bytes,
            )
            attachment = self.attachment_repository.create(
                database_session,
                organization_id=organization_id,
                uploaded_by_user_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                original_filename=filename,
                storage_key=storage_key,
                content_type=content_type,
                size_bytes=size_bytes,
            )
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="attachment.created",
                entity_type="attachment",
                entity_id=attachment.id,
            )
            database_session.commit()
            return attachment
        except (AttachmentStorageError, AttachmentValidationError):
            database_session.rollback()
            if storage_key is not None:
                await self._delete_best_effort(storage_key)
            raise
        except IntegrityError as exc:
            database_session.rollback()
            if storage_key is not None:
                await self._delete_best_effort(storage_key)
            raise AttachmentConflictError from exc
        except Exception:
            database_session.rollback()
            if storage_key is not None:
                await self._delete_best_effort(storage_key)
            raise

    def list_attachments(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Attachment], int]:
        self._require_target(database_session, organization_id, entity_type, entity_id)
        return self.attachment_repository.list_by_entity(
            database_session,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            page=page,
            page_size=page_size,
        )

    def get_attachment(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        attachment_id: UUID,
    ) -> Attachment:
        attachment = self.attachment_repository.get_by_id(
            database_session,
            organization_id=organization_id,
            attachment_id=attachment_id,
        )
        if attachment is None:
            raise AttachmentNotFoundError
        self._require_target(
            database_session,
            organization_id,
            attachment.entity_type,
            attachment.entity_id,
        )
        return attachment

    async def download_attachment(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        attachment_id: UUID,
    ) -> tuple[Attachment, AsyncIterator[bytes]]:
        attachment = self.get_attachment(
            database_session,
            organization_id=organization_id,
            attachment_id=attachment_id,
        )
        return attachment, await self.storage.open_download(attachment.storage_key)

    async def delete_attachment(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        attachment_id: UUID,
    ) -> None:
        attachment = self.get_attachment(
            database_session,
            organization_id=organization_id,
            attachment_id=attachment_id,
        )
        try:
            self.audit_service.record(
                database_session,
                actor_id=actor_id,
                action="attachment.deleted",
                entity_type="attachment",
                entity_id=attachment.id,
            )
            self.attachment_repository.delete(database_session, attachment)
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise

        # Keep a committed metadata deletion authoritative. A failed physical
        # cleanup leaves an orphan that can be handled by a future worker, which
        # is safer than leaving a visible row with missing file content.
        await self._delete_best_effort(attachment.storage_key)

    def _require_target(
        self,
        database_session: Session,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
    ) -> None:
        if entity_type == "company":
            from sqlalchemy import select

            statement = select(Company.id).where(
                Company.id == entity_id,
                Company.organization_id == organization_id,
            )
        elif entity_type == "contact":
            from sqlalchemy import select

            statement = (
                select(Contact.id)
                .join(Contact.company)
                .where(
                    Contact.id == entity_id,
                    Company.organization_id == organization_id,
                )
            )
        elif entity_type == "lead":
            from sqlalchemy import select

            statement = select(Lead.id).where(
                Lead.id == entity_id,
                Lead.organization_id == organization_id,
            )
        elif entity_type == "deal":
            from sqlalchemy import select

            statement = select(Deal.id).where(
                Deal.id == entity_id,
                Deal.organization_id == organization_id,
            )
        elif entity_type == "activity":
            from sqlalchemy import select

            statement = select(Activity.id).where(
                Activity.id == entity_id,
                Activity.organization_id == organization_id,
            )
        elif entity_type == "task":
            from sqlalchemy import select

            statement = select(Task.id).where(
                Task.id == entity_id,
                Task.organization_id == organization_id,
            )
        elif entity_type == "note":
            from sqlalchemy import select

            statement = select(Note.id).where(
                Note.id == entity_id,
                Note.organization_id == organization_id,
            )
        else:
            raise AttachmentValidationError("Unsupported attachment entity type")

        if database_session.scalar(statement) is None:
            raise AttachmentTargetNotFoundError

    def _reject_declared_oversize(self, upload: UploadFile) -> None:
        if upload.size is not None and upload.size > self.max_upload_bytes:
            raise AttachmentValidationError(
                f"Attachment exceeds the {self.max_upload_bytes}-byte upload limit"
            )

    @staticmethod
    def _sanitize_filename(value: str | None) -> str:
        if value is None:
            raise AttachmentValidationError("An attachment filename is required")
        filename = unicodedata.normalize("NFKC", value).strip()
        filename = _DISALLOWED_FILENAME_CHARACTERS.sub("_", filename)
        filename = _WHITESPACE.sub(" ", filename).strip(" .")
        if not filename or filename in {".", ".."}:
            raise AttachmentValidationError("Attachment filename is invalid")
        if len(filename) > 255:
            raise AttachmentValidationError("Attachment filename is too long")
        return filename

    @staticmethod
    def _normalize_content_type(value: str | None) -> str:
        if value is None:
            return "application/octet-stream"
        content_type = value.split(";", maxsplit=1)[0].strip().lower()
        if not _CONTENT_TYPE.fullmatch(content_type):
            raise AttachmentValidationError("Attachment content type is invalid")
        return content_type

    async def _delete_best_effort(self, storage_key: str) -> None:
        try:
            await self.storage.delete(storage_key)
        except AttachmentStorageError:
            pass
