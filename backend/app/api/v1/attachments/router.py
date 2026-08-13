from collections.abc import AsyncGenerator
from typing import Annotated, cast, get_args
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from starlette.datastructures import Headers, UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.user import User
from app.repositories.attachment import AttachmentRepository
from app.schemas.attachment import AttachmentEntityType, AttachmentResponse
from app.schemas.common import PageMetadata, PaginatedResponse
from app.security.permission_catalog import PermissionName
from app.security.permissions import require_permissions
from app.services.attachment import (
    AttachmentConflictError,
    AttachmentNotFoundError,
    AttachmentService,
    AttachmentTargetNotFoundError,
    AttachmentValidationError,
)
from app.services.audit import audit_service
from app.services.storage import (
    AttachmentFileMissingError,
    AttachmentStorageError,
    AttachmentStorageUnavailableError,
    AttachmentTooLargeError,
    get_attachment_storage,
)

router = APIRouter(prefix="/attachments", tags=["attachments"])
DatabaseSession = Annotated[Session, Depends(get_db)]
AttachmentReader = Annotated[
    User, Depends(require_permissions(PermissionName.ATTACHMENTS_READ))
]
AttachmentCreator = Annotated[
    User, Depends(require_permissions(PermissionName.ATTACHMENTS_CREATE))
]
AttachmentDeleter = Annotated[
    User, Depends(require_permissions(PermissionName.ATTACHMENTS_DELETE))
]
_MAX_MULTIPART_FIELD_BYTES = 16 * 1024


class BoundedAttachmentMultipartParser(MultiPartParser):
    """Reject file content before Starlette writes it to a temporary file."""

    def __init__(
        self,
        headers: Headers,
        stream: AsyncGenerator[bytes, None],
        *,
        max_file_size: int,
    ) -> None:
        super().__init__(
            headers,
            stream,
            max_files=1,
            max_fields=2,
        )
        self.max_file_size = max_file_size
        self.current_file_size = 0

    def on_part_begin(self) -> None:
        super().on_part_begin()
        self.current_file_size = 0

    def on_part_data(self, data: bytes, start: int, end: int) -> None:
        part_size = end - start
        if self._current_part.file is None:
            if len(self._current_part.data) + part_size > _MAX_MULTIPART_FIELD_BYTES:
                raise MultiPartException("Attachment field exceeds the configured limit")
        else:
            self.current_file_size += part_size
            if self.current_file_size > self.max_file_size:
                raise MultiPartException("Attachment file exceeds the configured upload limit")
        super().on_part_data(data, start, end)


def _attachment_service() -> AttachmentService:
    settings = get_settings()
    return AttachmentService(
        AttachmentRepository(),
        get_attachment_storage(settings),
        audit_service,
        max_upload_bytes=settings.attachment_max_upload_bytes,
    )


def _storage_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Attachment storage is not configured",
    )


def _target_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Attachment target not found",
    )


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment(
    request: Request,
    database_session: DatabaseSession,
    current_user: AttachmentCreator,
) -> AttachmentResponse:
    service = _attachment_service()
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > service.max_upload_bytes + 16_384:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="Attachment exceeds the configured upload limit",
                )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Content-Length header",
            ) from exc

    request_content_type = request.headers.get("content-type", "")
    if not request_content_type.lower().startswith("multipart/form-data"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Attachment uploads require multipart/form-data",
        )

    form = None
    try:
        parser = BoundedAttachmentMultipartParser(
            request.headers,
            request.stream(),
            max_file_size=service.max_upload_bytes,
        )
        form = await parser.parse()
        try:
            entity_type = form.get("entity_type")
            entity_id = form.get("entity_id")
            upload = form.get("file")
            if not isinstance(entity_type, str) or not isinstance(entity_id, str):
                raise AttachmentValidationError(
                    "entity_type and entity_id form fields are required"
                )
            if not isinstance(upload, UploadFile):
                raise AttachmentValidationError("file form field is required")
            try:
                parsed_entity_id = UUID(entity_id)
            except ValueError as exc:
                raise AttachmentValidationError("Attachment target is invalid") from exc
            if entity_type not in get_args(AttachmentEntityType):
                raise AttachmentValidationError("Attachment target is invalid")
            parsed_entity_type = cast(AttachmentEntityType, entity_type)
            attachment = await service.create_attachment(
                database_session,
                organization_id=current_user.organization_id,
                actor_id=current_user.id,
                entity_type=parsed_entity_type,
                entity_id=parsed_entity_id,
                upload=upload,
            )
        finally:
            await form.close()
    except MultiPartException as exc:
        status_code = (
            status.HTTP_413_CONTENT_TOO_LARGE
            if "exceed" in str(exc).lower() or "maximum" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail="Attachment upload exceeds the configured request limits"
            if status_code == status.HTTP_413_CONTENT_TOO_LARGE
            else "Malformed multipart attachment upload",
        ) from exc
    except AttachmentTargetNotFoundError as exc:
        raise _target_not_found() from exc
    except AttachmentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except AttachmentTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)
        ) from exc
    except AttachmentStorageUnavailableError as exc:
        raise _storage_unavailable() from exc
    except AttachmentStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Attachment storage is temporarily unavailable",
        ) from exc
    except AttachmentConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attachment could not be saved",
        ) from exc
    return AttachmentResponse.model_validate(attachment)


@router.get("", response_model=PaginatedResponse[AttachmentResponse])
def list_attachments(
    entity_type: AttachmentEntityType,
    entity_id: UUID,
    database_session: DatabaseSession,
    current_user: AttachmentReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> PaginatedResponse[AttachmentResponse]:
    try:
        attachments, total = _attachment_service().list_attachments(
            database_session,
            organization_id=current_user.organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            page=page,
            page_size=page_size,
        )
    except AttachmentTargetNotFoundError as exc:
        raise _target_not_found() from exc
    return PaginatedResponse(
        items=[AttachmentResponse.model_validate(attachment) for attachment in attachments],
        meta=PageMetadata(page=page, page_size=page_size, total=total),
    )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
def get_attachment(
    attachment_id: UUID,
    database_session: DatabaseSession,
    current_user: AttachmentReader,
) -> AttachmentResponse:
    try:
        attachment = _attachment_service().get_attachment(
            database_session,
            organization_id=current_user.organization_id,
            attachment_id=attachment_id,
        )
    except (AttachmentNotFoundError, AttachmentTargetNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found"
        ) from exc
    return AttachmentResponse.model_validate(attachment)


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    database_session: DatabaseSession,
    current_user: AttachmentReader,
) -> StreamingResponse:
    try:
        attachment, content = await _attachment_service().download_attachment(
            database_session,
            organization_id=current_user.organization_id,
            attachment_id=attachment_id,
        )
        filename = quote(attachment.original_filename, safe="")
        return StreamingResponse(
            content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                "Content-Length": str(attachment.size_bytes),
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, no-store",
            },
        )
    except (AttachmentNotFoundError, AttachmentTargetNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found"
        ) from exc
    except AttachmentFileMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Attachment content is no longer available",
        ) from exc
    except AttachmentStorageUnavailableError as exc:
        raise _storage_unavailable() from exc
    except AttachmentStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Attachment storage is temporarily unavailable",
        ) from exc


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: UUID,
    database_session: DatabaseSession,
    current_user: AttachmentDeleter,
) -> Response:
    try:
        await _attachment_service().delete_attachment(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            attachment_id=attachment_id,
        )
    except (AttachmentNotFoundError, AttachmentTargetNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found"
        ) from exc
    except AttachmentStorageUnavailableError as exc:
        raise _storage_unavailable() from exc
    except AttachmentStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Attachment storage is temporarily unavailable",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
