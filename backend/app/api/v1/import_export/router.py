from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from starlette.datastructures import Headers, UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.user import User
from app.schemas.import_export import (
    ImportResource,
    ImportResponse,
    ImportRowError,
)
from app.security.dependencies import require_import_export_permissions
from app.services.import_export import (
    CsvEmptyImportError,
    CsvExportLimitExceededError,
    CsvFormatError,
    CsvImportPersistenceError,
    CsvImportValidationError,
    CsvRowLimitExceededError,
    import_export_service,
)

router = APIRouter(prefix="/import-export", tags=["import/export"])
DatabaseSession = Annotated[Session, Depends(get_db)]
ImportCreator = Annotated[User, Depends(require_import_export_permissions("import"))]
ExportCreator = Annotated[User, Depends(require_import_export_permissions("export"))]
_MULTIPART_OVERHEAD_BYTES = 16 * 1024
_MAX_MULTIPART_FIELD_BYTES = 16 * 1024


class BoundedCsvMultipartParser(MultiPartParser):
    """Reject oversized CSV file parts before Starlette spools them to disk."""

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
            max_fields=0,
            max_part_size=_MAX_MULTIPART_FIELD_BYTES,
        )
        self.max_file_size = max_file_size
        self.current_file_size = 0

    def on_part_begin(self) -> None:
        super().on_part_begin()
        self.current_file_size = 0

    def on_part_data(self, data: bytes, start: int, end: int) -> None:
        if self._current_part.file is not None:
            self.current_file_size += end - start
            if self.current_file_size > self.max_file_size:
                raise MultiPartException("CSV file exceeds the configured upload limit")
        super().on_part_data(data, start, end)


def _csv_response(content: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([content.encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _validation_error_response(errors: list[ImportRowError]) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "message": "CSV validation failed",
            "errors": [error.model_dump(mode="json") for error in errors],
        },
    )


async def _read_csv_upload(request: Request) -> bytes:
    settings = get_settings()
    max_request_bytes = (
        settings.import_export_max_upload_bytes + _MULTIPART_OVERHEAD_BYTES
    )
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) < 0:
                raise ValueError
            if int(content_length) > max_request_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="CSV upload exceeds the configured size limit",
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
            detail="CSV imports require multipart/form-data",
        )

    form = None
    try:
        parser = BoundedCsvMultipartParser(
            request.headers,
            _bounded_request_stream(request.stream(), max_request_bytes),
            max_file_size=settings.import_export_max_upload_bytes,
        )
        form = await parser.parse()
        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="file form field is required",
            )
        if upload.content_type not in {"text/csv", "application/csv", "text/plain"}:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="CSV imports require a text/csv upload",
            )
        if upload.size is not None and upload.size > settings.import_export_max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="CSV upload exceeds the configured size limit",
            )
        content = await upload.read(settings.import_export_max_upload_bytes + 1)
    except MultiPartException as exc:
        status_code = (
            status.HTTP_413_CONTENT_TOO_LARGE
            if "exceed" in str(exc).lower() or "maximum" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail="CSV upload exceeds the configured request limits"
            if status_code == status.HTTP_413_CONTENT_TOO_LARGE
            else "Malformed multipart CSV upload",
        ) from exc
    finally:
        if form is not None:
            await form.close()
    if len(content) > settings.import_export_max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="CSV upload exceeds the configured size limit",
        )
    return content


async def _bounded_request_stream(
    stream: AsyncGenerator[bytes, None], max_bytes: int
) -> AsyncGenerator[bytes, None]:
    received_bytes = 0
    async for chunk in stream:
        received_bytes += len(chunk)
        if received_bytes > max_bytes:
            raise MultiPartException("CSV upload exceeds the configured request limit")
        yield chunk


@router.get("/{resource}")
def export_csv(
    resource: ImportResource,
    database_session: DatabaseSession,
    current_user: ExportCreator,
) -> StreamingResponse:
    settings = get_settings()
    try:
        if resource == "companies":
            content = import_export_service.export_companies(
                database_session,
                organization_id=current_user.organization_id,
                actor_id=current_user.id,
                max_rows=settings.import_export_max_rows,
            )
        else:
            content = import_export_service.export_contacts(
                database_session,
                organization_id=current_user.organization_id,
                actor_id=current_user.id,
                max_rows=settings.import_export_max_rows,
            )
    except CsvExportLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)
        ) from exc
    return _csv_response(content, f"{resource}.csv")


@router.post("/{resource}", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
async def import_csv(
    resource: ImportResource,
    request: Request,
    database_session: DatabaseSession,
    current_user: ImportCreator,
) -> ImportResponse:
    csv_content = await _read_csv_upload(request)
    settings = get_settings()
    try:
        if resource == "companies":
            return import_export_service.import_companies(
                database_session,
                organization_id=current_user.organization_id,
                actor_id=current_user.id,
                csv_content=csv_content,
                max_rows=settings.import_export_max_rows,
            )
        return import_export_service.import_contacts(
            database_session,
            organization_id=current_user.organization_id,
            actor_id=current_user.id,
            csv_content=csv_content,
            max_rows=settings.import_export_max_rows,
        )
    except CsvImportValidationError as exc:
        raise _validation_error_response(exc.errors) from exc
    except (CsvFormatError, CsvEmptyImportError, CsvRowLimitExceededError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except CsvImportPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CSV import could not be saved",
        ) from exc
