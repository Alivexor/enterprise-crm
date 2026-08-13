"""Private attachment storage abstractions for the supported local backend."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings

FILE_CHUNK_SIZE = 64 * 1024


class AttachmentStorageError(Exception):
    """A storage backend could not safely complete an operation."""


class AttachmentStorageUnavailableError(AttachmentStorageError):
    """The configured deployment does not provide attachment storage."""


class AttachmentTooLargeError(AttachmentStorageError):
    """An upload exceeds the configured byte limit."""


class AttachmentFileMissingError(AttachmentStorageError):
    """Metadata exists but its backing object is unavailable."""


class AttachmentStorage(ABC):
    @abstractmethod
    async def save(
        self,
        upload: UploadFile,
        *,
        organization_id: UUID,
        max_bytes: int,
    ) -> tuple[str, int]:
        ...

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        ...

    @abstractmethod
    async def open_download(self, storage_key: str) -> AsyncIterator[bytes]:
        ...


class DisabledAttachmentStorage(AttachmentStorage):
    def _unavailable(self) -> AttachmentStorageUnavailableError:
        return AttachmentStorageUnavailableError(
            "Attachment storage is not configured for this environment"
        )

    async def save(
        self,
        upload: UploadFile,
        *,
        organization_id: UUID,
        max_bytes: int,
    ) -> tuple[str, int]:
        raise self._unavailable()

    async def delete(self, storage_key: str) -> None:
        raise self._unavailable()

    async def open_download(self, storage_key: str) -> AsyncIterator[bytes]:
        raise self._unavailable()


class LocalAttachmentStorage(AttachmentStorage):
    """Private local storage for development and test environments only."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _path_for(self, storage_key: str) -> Path:
        relative_path = Path(storage_key)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise AttachmentStorageError("Invalid attachment storage key")
        resolved_path = (self.root / relative_path).resolve()
        if self.root != resolved_path and self.root not in resolved_path.parents:
            raise AttachmentStorageError("Invalid attachment storage key")
        return resolved_path

    async def save(
        self,
        upload: UploadFile,
        *,
        organization_id: UUID,
        max_bytes: int,
    ) -> tuple[str, int]:
        storage_key = f"{organization_id}/{uuid4().hex}"
        destination = self._path_for(storage_key)
        temporary_destination = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
        total_size = 0
        target = None

        try:
            await run_in_threadpool(destination.parent.mkdir, parents=True, exist_ok=True)
            target = await run_in_threadpool(temporary_destination.open, "xb")
            while chunk := await upload.read(FILE_CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > max_bytes:
                    raise AttachmentTooLargeError(
                        f"Attachment exceeds the {max_bytes}-byte upload limit"
                    )
                await run_in_threadpool(target.write, chunk)
            await run_in_threadpool(target.close)
            target = None
            await run_in_threadpool(temporary_destination.replace, destination)
        except AttachmentStorageError:
            await self._remove_if_present(temporary_destination)
            raise
        except OSError as exc:
            await self._remove_if_present(temporary_destination)
            raise AttachmentStorageError("Attachment could not be stored") from exc
        finally:
            if target is not None:
                try:
                    await run_in_threadpool(target.close)
                except OSError:
                    pass
            await upload.close()
        return storage_key, total_size

    async def delete(self, storage_key: str) -> None:
        path = self._path_for(storage_key)
        try:
            await run_in_threadpool(path.unlink, missing_ok=True)
        except OSError as exc:
            raise AttachmentStorageError("Attachment could not be removed") from exc

    async def open_download(self, storage_key: str) -> AsyncIterator[bytes]:
        path = self._path_for(storage_key)
        try:
            file_handle = await run_in_threadpool(path.open, "rb")
        except FileNotFoundError as exc:
            raise AttachmentFileMissingError("Attachment content is unavailable") from exc
        except OSError as exc:
            raise AttachmentStorageError("Attachment content could not be read") from exc
        async def stream() -> AsyncIterator[bytes]:
            try:
                while chunk := await run_in_threadpool(file_handle.read, FILE_CHUNK_SIZE):
                    yield chunk
            finally:
                await run_in_threadpool(file_handle.close)

        return stream()

    async def _remove_if_present(self, path: Path) -> None:
        try:
            await run_in_threadpool(path.unlink, missing_ok=True)
        except OSError:
            pass


def get_attachment_storage(settings: Settings) -> AttachmentStorage:
    if settings.attachment_storage_backend == "local":
        if settings.attachment_local_storage_path is None:
            raise AttachmentStorageUnavailableError(
                "Local attachment storage is not configured"
            )
        return LocalAttachmentStorage(settings.attachment_local_storage_path)
    return DisabledAttachmentStorage()
