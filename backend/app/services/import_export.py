import csv
from collections.abc import Iterable, Sized
from io import StringIO
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.repositories.import_export import ImportExportRepository
from app.schemas.import_export import (
    CompanyImportHeaders,
    CompanyImportRow,
    ContactImportHeaders,
    ContactImportRow,
    ImportResponse,
    ImportRowError,
)
from app.services.audit import AuditService, audit_service

ImportRow = TypeVar("ImportRow", bound=BaseModel)


class CsvImportExportError(Exception):
    """Base exception for CSV import and export failures."""


class CsvFormatError(CsvImportExportError):
    """Raised when a CSV document is malformed or has an invalid header."""


class CsvRowLimitExceededError(CsvImportExportError):
    """Raised when a CSV document contains too many non-empty rows."""


class CsvEmptyImportError(CsvImportExportError):
    """Raised when an import contains no data rows."""


class CsvExportLimitExceededError(CsvImportExportError):
    """Raised when an export exceeds the configured record limit."""


class CsvImportValidationError(CsvImportExportError):
    """Raised after all import rows have been validated without mutations."""

    def __init__(self, errors: list[ImportRowError]) -> None:
        super().__init__("CSV validation failed")
        self.errors = errors


class CsvImportPersistenceError(CsvImportExportError):
    """Raised when a validated import cannot be persisted atomically."""


class ImportExportService:
    def __init__(
        self,
        import_export_repository: ImportExportRepository,
        audit_service: AuditService,
    ) -> None:
        self.import_export_repository = import_export_repository
        self.audit_service = audit_service

    def export_companies(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        max_rows: int,
    ) -> str:
        companies = self.import_export_repository.list_companies_for_export(
            database_session, organization_id, limit=max_rows + 1
        )
        self._require_export_within_limit(companies, max_rows)
        csv_content = self._serialize_csv(
            CompanyImportHeaders,
            (
                (company.name, company.website, company.industry)
                for company in companies
            ),
        )
        self._record_export_audit_event(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            action="companies.exported",
        )
        return csv_content

    def export_contacts(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        max_rows: int,
    ) -> str:
        contact_rows = self.import_export_repository.list_contacts_for_export(
            database_session, organization_id, limit=max_rows + 1
        )
        self._require_export_within_limit(contact_rows, max_rows)
        csv_content = self._serialize_csv(
            ContactImportHeaders,
            (
                (
                    contact.company_id,
                    company.name,
                    contact.first_name,
                    contact.last_name,
                    contact.email,
                    contact.phone,
                )
                for contact, company in contact_rows
            ),
        )
        self._record_export_audit_event(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            action="contacts.exported",
        )
        return csv_content

    def import_companies(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        csv_content: bytes,
        max_rows: int,
    ) -> ImportResponse:
        parsed_rows = self._parse_and_validate_rows(
            csv_content,
            expected_headers=CompanyImportHeaders,
            row_type=CompanyImportRow,
            max_rows=max_rows,
        )
        self._validate_company_rows(
            database_session,
            organization_id=organization_id,
            rows=parsed_rows,
        )
        try:
            companies = self.import_export_repository.create_companies(
                database_session,
                organization_id,
                (row for _, row in parsed_rows),
            )
            self._record_import_audit_event(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                action="companies.imported",
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise CsvImportPersistenceError from exc
        return ImportResponse(
            resource="companies",
            rows_processed=len(parsed_rows),
            created_count=len(companies),
        )

    def import_contacts(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        csv_content: bytes,
        max_rows: int,
    ) -> ImportResponse:
        parsed_rows = self._parse_and_validate_rows(
            csv_content,
            expected_headers=ContactImportHeaders,
            row_type=ContactImportRow,
            max_rows=max_rows,
        )
        resolved_rows = self._resolve_contact_companies(
            database_session,
            organization_id=organization_id,
            rows=parsed_rows,
        )
        try:
            contacts = self.import_export_repository.create_contacts(
                database_session, resolved_rows
            )
            self._record_import_audit_event(
                database_session,
                organization_id=organization_id,
                actor_id=actor_id,
                action="contacts.imported",
            )
            database_session.commit()
        except IntegrityError as exc:
            database_session.rollback()
            raise CsvImportPersistenceError from exc
        return ImportResponse(
            resource="contacts",
            rows_processed=len(parsed_rows),
            created_count=len(contacts),
        )

    def _parse_and_validate_rows(
        self,
        csv_content: bytes,
        *,
        expected_headers: tuple[str, ...],
        row_type: type[ImportRow],
        max_rows: int,
    ) -> list[tuple[int, ImportRow]]:
        raw_rows = self._parse_csv(csv_content, expected_headers, max_rows)
        parsed_rows: list[tuple[int, ImportRow]] = []
        errors: list[ImportRowError] = []
        for row_number, raw_row in raw_rows:
            if raw_row.get(None) is not None:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        message="The row contains more values than the CSV header",
                    )
                )
                continue
            row_data = {header: raw_row.get(header) for header in expected_headers}
            try:
                parsed_rows.append((row_number, row_type.model_validate(row_data)))
            except ValidationError as exc:
                errors.extend(self._validation_errors(row_number, exc))
        if errors:
            raise CsvImportValidationError(errors)
        return parsed_rows

    @staticmethod
    def _parse_csv(
        csv_content: bytes,
        expected_headers: tuple[str, ...],
        max_rows: int,
    ) -> list[tuple[int, dict[str | None, str | list[str] | None]]]:
        try:
            decoded_content = csv_content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise CsvFormatError("CSV files must use UTF-8 encoding") from exc

        try:
            reader = csv.DictReader(StringIO(decoded_content, newline=""), strict=True)
            header = tuple(reader.fieldnames or ())
            if not header:
                raise CsvFormatError("CSV file must include a header row")
            if len(header) != len(set(header)):
                raise CsvFormatError("CSV header contains duplicate column names")
            if set(header) != set(expected_headers):
                expected = ", ".join(expected_headers)
                raise CsvFormatError(f"CSV header must contain exactly: {expected}")

            rows: list[tuple[int, dict[str | None, str | list[str] | None]]] = []
            for row_number, row in enumerate(reader, start=2):
                if row.get(None) is None and all(
                    value is None or not str(value).strip()
                    for key, value in row.items()
                    if key is not None
                ):
                    continue
                rows.append((row_number, row))
                if len(rows) > max_rows:
                    raise CsvRowLimitExceededError(
                        f"CSV files may contain at most {max_rows} non-empty data rows"
                    )
        except csv.Error as exc:
            raise CsvFormatError("CSV file is malformed") from exc
        if not rows:
            raise CsvEmptyImportError("CSV file must contain at least one data row")
        return rows

    def _validate_company_rows(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        rows: list[tuple[int, CompanyImportRow]],
    ) -> None:
        errors: list[ImportRowError] = []
        rows_by_name: dict[str, list[int]] = {}
        for row_number, row in rows:
            rows_by_name.setdefault(row.name.lower(), []).append(row_number)
        for row_numbers in rows_by_name.values():
            if len(row_numbers) > 1:
                errors.extend(
                    ImportRowError(
                        row_number=row_number,
                        field="name",
                        message="Duplicate company name in this import file",
                    )
                    for row_number in row_numbers
                )

        existing_companies = self.import_export_repository.get_companies_by_normalized_names(
            database_session,
            organization_id,
            rows_by_name,
        )
        for normalized_name, row_numbers in rows_by_name.items():
            if normalized_name in existing_companies:
                errors.extend(
                    ImportRowError(
                        row_number=row_number,
                        field="name",
                        message="A company with this name already exists",
                    )
                    for row_number in row_numbers
                )
        if errors:
            raise CsvImportValidationError(errors)

    def _resolve_contact_companies(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        rows: list[tuple[int, ContactImportRow]],
    ) -> list[tuple[UUID, ContactImportRow]]:
        companies_by_id = self.import_export_repository.get_companies_by_ids(
            database_session,
            organization_id,
            (row.company_id for _, row in rows if row.company_id is not None),
        )
        companies_by_name = self.import_export_repository.get_companies_by_normalized_names(
            database_session,
            organization_id,
            (row.company_name for _, row in rows if row.company_name is not None),
        )
        errors: list[ImportRowError] = []
        resolved_rows: list[tuple[UUID, ContactImportRow]] = []
        for row_number, row in rows:
            company_by_id = (
                companies_by_id.get(row.company_id)
                if row.company_id is not None
                else None
            )
            company_by_name: Company | None = None
            if row.company_name is not None:
                matching_companies = companies_by_name.get(row.company_name.lower(), [])
                if not matching_companies:
                    errors.append(
                        ImportRowError(
                            row_number=row_number,
                            field="company_name",
                            message="No company with this name exists in the organization",
                        )
                    )
                elif len(matching_companies) > 1:
                    errors.append(
                        ImportRowError(
                            row_number=row_number,
                            field="company_name",
                            message="Company name is ambiguous in the organization",
                        )
                    )
                else:
                    company_by_name = matching_companies[0]

            if row.company_id is not None and company_by_id is None:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field="company_id",
                        message="Company is not available in the organization",
                    )
                )
            if (
                company_by_id is not None
                and company_by_name is not None
                and company_by_id.id != company_by_name.id
            ):
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field="company_name",
                        message="company_id and company_name refer to different companies",
                    )
                )

            company = company_by_id if company_by_id is not None else company_by_name
            if company is not None:
                resolved_rows.append((company.id, row))
        if errors:
            raise CsvImportValidationError(errors)
        return resolved_rows

    @staticmethod
    def _validation_errors(
        row_number: int, validation_error: ValidationError
    ) -> list[ImportRowError]:
        return [
            ImportRowError(
                row_number=row_number,
                field=".".join(str(location) for location in error["loc"]),
                message=error["msg"],
            )
            for error in validation_error.errors()
        ]

    @staticmethod
    def _serialize_csv(
        headers: tuple[str, ...], rows: Iterable[Iterable[object | None]]
    ) -> str:
        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow(headers)
        for row in rows:
            writer.writerow([ImportExportService._sanitize_export_value(value) for value in row])
        return output.getvalue()

    @staticmethod
    def _sanitize_export_value(value: object | None) -> str:
        if value is None:
            return ""
        text = str(value)
        if text.lstrip().startswith(("=", "+", "-", "@")):
            return f"'{text}"
        return text

    @staticmethod
    def _require_export_within_limit(records: Sized, max_rows: int) -> None:
        if len(records) > max_rows:
            raise CsvExportLimitExceededError(
                f"Export exceeds the configured limit of {max_rows} rows"
            )

    def _record_import_audit_event(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        action: str,
    ) -> None:
        self.audit_service.record(
            database_session,
            actor_id=actor_id,
            action=action,
            entity_type="organization",
            entity_id=organization_id,
        )

    def _record_export_audit_event(
        self,
        database_session: Session,
        *,
        organization_id: UUID,
        actor_id: UUID,
        action: str,
    ) -> None:
        self._record_import_audit_event(
            database_session,
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
        )
        database_session.commit()


import_export_service = ImportExportService(ImportExportRepository(), audit_service)
