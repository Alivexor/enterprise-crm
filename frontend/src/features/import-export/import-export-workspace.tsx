"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { ApiError } from "@/services/api-client";
import { importExportService } from "@/services/import-export-service";
import type {
  ImportExportResource,
  ImportResponse,
  ImportRowError,
} from "@/types/import-export";

const resourceDetails: Record<ImportExportResource, {
  columns: string[];
  description: string;
  label: string;
}> = {
  companies: {
    columns: ["name", "website", "industry"],
    description: "Create customer companies from a CSV file.",
    label: "Companies",
  },
  contacts: {
    columns: ["company_id", "company_name", "first_name", "last_name", "email", "phone"],
    description: "Create contacts with either a company ID or a company name in each row.",
    label: "Contacts",
  },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function importRowErrors(error: unknown): ImportRowError[] {
  if (!(error instanceof ApiError) || !isRecord(error.details)) {
    return [];
  }

  const detail = error.details.detail;
  if (!isRecord(detail) || !Array.isArray(detail.errors)) {
    return [];
  }

  return detail.errors.filter((value): value is ImportRowError => (
    isRecord(value)
    && typeof value.row_number === "number"
    && typeof value.message === "string"
    && (typeof value.field === "string" || value.field === null)
  ));
}

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to import this CSV file.";
}

export function ImportExportWorkspace() {
  const { formatNumber, locale, t } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [resource, setResource] = useState<ImportExportResource>("companies");
  const [file, setFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [result, setResult] = useState<ImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rowErrors, setRowErrors] = useState<ImportRowError[]>([]);
  const detail = resourceDetails[resource];

  function selectResource(nextResource: ImportExportResource) {
    setResource(nextResource);
    setFile(null);
    setResult(null);
    setError(null);
    setRowErrors([]);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setResult(null);
    setError(null);
    setRowErrors([]);
  }

  async function importCsv(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file before importing.");
      return;
    }

    setIsImporting(true);
    setResult(null);
    setError(null);
    setRowErrors([]);
    try {
      const nextResult = await importExportService.importCsv(resource, file);
      setResult(nextResult);
      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
      setRowErrors(importRowErrors(caughtError));
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <section className="crm-page mx-auto max-w-5xl">
      <p className="crm-kicker"><T>Workspace</T></p>
      <h1 className="crm-title mt-3"><T>Import & export</T></h1>
      <p className="crm-subtitle mt-3"><T>Move company and contact data into or out of the CRM using CSV files.</T></p>
      <div className="mt-6"><SettingsNavigation compact /></div>

      <div className="mt-8 flex flex-wrap gap-2" role="group" aria-label={t("Import resource")}>
        {(Object.keys(resourceDetails) as ImportExportResource[]).map((value) => <Button aria-pressed={resource === value} key={value} onClick={() => selectResource(value)} size="sm" variant={resource === value ? "primary" : "secondary"}>{t(resourceDetails[value].label)}</Button>)}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="crm-card rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" aria-labelledby="import-heading">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white" id="import-heading">{t("Import {resource}", { resource: t(detail.label) })}</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">{t(detail.description)}</p>
          <p className="mt-5 text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Required CSV headers</T></p>
          <code className="mt-2 block overflow-x-auto rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-700 dark:bg-slate-900 dark:text-slate-200">{detail.columns.join(",")}</code>

          <form className="mt-6 space-y-4" onSubmit={(event) => void importCsv(event)}>
            <label className="block"><span className="text-sm font-medium text-slate-800 dark:text-slate-100"><T>CSV file</T></span><input accept=".csv,text/csv" className="crm-input mt-2 block w-full text-sm text-slate-600 file:me-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-slate-700 hover:file:bg-slate-200 dark:text-slate-300 dark:file:bg-slate-900 dark:file:text-slate-200 dark:hover:file:bg-slate-800" onChange={selectFile} ref={inputRef} required type="file" /></label>
            <Button disabled={!file || isImporting} type="submit">{isImporting ? t("Importing...") : t("Import {resource}", { resource: t(detail.label) })}</Button>
          </form>
          {error ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}
          {result ? <p className="mt-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-100" role="status">{t("Imported {created} of {processed} {resource} rows.", { created: formatNumber(result.created_count), processed: formatNumber(result.rows_processed), resource: t(result.resource === "companies" ? "Companies" : "Contacts") })}</p> : null}
          {rowErrors.length > 0 ? <ul className="mt-4 space-y-2 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-100">{rowErrors.map((rowError) => <li key={`${rowError.row_number}-${rowError.field ?? "row"}-${rowError.message}`}>{locale === "fa" ? `ردیف ${formatNumber(rowError.row_number)}${rowError.field ? ` (${rowError.field})` : ""}: ${rowError.message}` : `Row ${rowError.row_number}${rowError.field ? ` (${rowError.field})` : ""}: ${rowError.message}`}</li>)}</ul> : null}
        </section>

        <section className="crm-card rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" aria-labelledby="export-heading">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white" id="export-heading">{t("Export {resource}", { resource: t(detail.label) })}</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500"><T>Download the current workspace data as a CSV file. The export respects your authorized organization scope.</T></p>
          <a className="mt-6 inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:focus-visible:ring-indigo-950" href={importExportService.exportPath(resource)}>{t("Download {resource} CSV", { resource: t(detail.label) })}</a>
        </section>
      </div>
    </section>
  );
}
