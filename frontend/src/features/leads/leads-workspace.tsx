"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { LeadForm } from "@/features/leads/lead-form";
import { LeadList } from "@/features/leads/lead-list";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { leadService } from "@/services/lead-service";
import { leadStatuses, type LeadInput, type LeadStatus } from "@/types/lead";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to save this lead.";
}

export function LeadsWorkspace({ initialCreate = false }: { initialCreate?: boolean } = {}) {
  const { t } = useI18n();
  const [isCreating, setIsCreating] = useState(initialCreate);
  const [isSaving, setIsSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [status, setStatus] = useState<LeadStatus | "">("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const { companies } = useCompanyOptions();
  const loadLeads = useCallback(
    () => leadService.list({ page, page_size: 25, search: appliedSearch || undefined, status: status || undefined }),
    [appliedSearch, page, status],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadLeads);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setAppliedSearch(search.trim());
  }

  async function createLead(values: LeadInput) {
    setIsSaving(true);
    setSaveError(null);
    try {
      await leadService.create(values);
      setIsCreating(false);
      reload();
    } catch (caughtError) {
      setSaveError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="crm-page mx-auto max-w-6xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="crm-kicker"><T>Sales</T></p><h1 className="crm-title mt-3"><T>Leads</T></h1><p className="crm-subtitle mt-3"><T>Capture, qualify, and track potential customers.</T></p></div>
        <Button aria-controls="new-lead-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>{isCreating ? <T>Close form</T> : <T>Add lead</T>}</Button>
      </div>
      {isCreating ? (
        <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-lead-form">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New lead</T></h2><p className="mt-1 text-sm text-slate-500"><T>Create a potential customer for your sales team to qualify.</T></p>
          <div className="mt-6"><LeadForm companies={companies} isSubmitting={isSaving} onCancel={() => setIsCreating(false)} onSubmit={createLead} submitLabel="Create lead" /></div>
          {saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}
        </div>
      ) : null}
      <form className="crm-toolbar mt-8 flex flex-col gap-3 sm:flex-row" onSubmit={submitSearch}>
        <label className="sr-only" htmlFor="lead-search"><T>Search leads</T></label>
        <input className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="lead-search" onChange={(event) => setSearch(event.target.value)} placeholder={t("Search leads")} value={search} />
        <label className="sr-only" htmlFor="lead-status-filter"><T>Filter by status</T></label>
        <select className="crm-select rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="lead-status-filter" onChange={(event) => { setStatus(event.target.value as LeadStatus | ""); setPage(1); }} value={status}>
          <option value=""><T>All statuses</T></option>{leadStatuses.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}
        </select>
        <Button type="submit" variant="secondary"><T>Search</T></Button>
      </form>
      <div className="mt-6">
        {isLoading ? <LoadingState label="Loading leads…" /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load leads" /> : null}
        {!isLoading && !error ? <LeadList leads={items} /> : null}
        {!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}
      </div>
    </section>
  );
}
