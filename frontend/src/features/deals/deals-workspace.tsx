"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T, useI18n } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useCallback, useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { DealForm } from "@/features/deals/deal-form";
import { DealList } from "@/features/deals/deal-list";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { usePipelineOptions } from "@/hooks/use-pipeline-options";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { dealService } from "@/services/deal-service";
import { dealStatuses, type DealInput, type DealStatus } from "@/types/deal";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to save this deal."; }

export function DealsWorkspace({ initialCreate = false }: { initialCreate?: boolean } = {}) {
  const { t } = useI18n();
  const { user } = useAuth();
  const canViewSalesBoard = user?.permissions.some((permission) => permission.name === "pipelines.read") ?? false;
  const { companies, error: companiesError } = useCompanyOptions();
  const { pipelines, error: pipelinesError } = usePipelineOptions();
  const [isCreating, setIsCreating] = useState(initialCreate); const [isSaving, setIsSaving] = useState(false); const [page, setPage] = useState(1); const [search, setSearch] = useState(""); const [appliedSearch, setAppliedSearch] = useState(""); const [status, setStatus] = useState<DealStatus | "">(""); const [saveError, setSaveError] = useState<string | null>(null);
  const loadDeals = useCallback(() => dealService.list({ page, page_size: 25, search: appliedSearch || undefined, status: status || undefined }), [appliedSearch, page, status]);
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadDeals);
  const pipelineNames = useMemo(() => new Map(pipelines.map((pipeline) => [pipeline.id, pipeline.name])), [pipelines]);
  function submitSearch(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setPage(1); setAppliedSearch(search.trim()); }
  async function createDeal(values: DealInput) { setIsSaving(true); setSaveError(null); try { await dealService.create(values); setIsCreating(false); reload(); } catch (caughtError) { setSaveError(getErrorMessage(caughtError)); } finally { setIsSaving(false); } }
  const setupError = companiesError ?? pipelinesError;
  return <section className="crm-page mx-auto max-w-6xl"><div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="crm-kicker"><T>Sales</T></p><h1 className="crm-title mt-3"><T>Deals</T></h1><p className="crm-subtitle mt-3"><T>Track active opportunities and expected revenue.</T></p></div><div className="flex flex-wrap gap-2">{canViewSalesBoard ? <Link className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-slate-200 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900 dark:focus-visible:ring-slate-800" href="/dashboard/deals/board"><T>Open sales board</T></Link> : null}<Button aria-controls="new-deal-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>{isCreating ? <T>Close form</T> : <T>Add deal</T>}</Button></div></div>
    {setupError ? <div className="mt-6"><ErrorState description={setupError} title="Unable to load deal options" /></div> : null}
    {isCreating ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-deal-form"><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New deal</T></h2><p className="mt-1 text-sm text-slate-500"><T>Create a sales opportunity in an existing pipeline stage.</T></p><div className="mt-6"><DealForm assignedUserId={user?.id ?? ""} companies={companies} isSubmitting={isSaving} onCancel={() => setIsCreating(false)} onSubmit={createDeal} pipelines={pipelines} submitLabel="Create deal" /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}</div> : null}
    <form className="crm-toolbar mt-8 flex flex-col gap-3 sm:flex-row" onSubmit={submitSearch}><label className="sr-only" htmlFor="deal-search"><T>Search deals</T></label><input className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-search" onChange={(event) => setSearch(event.target.value)} placeholder={t("Search deals")} value={search} /><label className="sr-only" htmlFor="deal-status-filter"><T>Filter by status</T></label><select className="crm-select rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-status-filter" onChange={(event) => { setStatus(event.target.value as DealStatus | ""); setPage(1); }} value={status}><option value=""><T>All statuses</T></option>{dealStatuses.map((item) => <option key={item} value={item}><LocalizedEnum value={item} /></option>)}</select><Button type="submit" variant="secondary"><T>Search</T></Button></form>
    <div className="mt-6">{isLoading ? <LoadingState label="Loading deals..." /> : null}{!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load deals" /> : null}{!isLoading && !error ? <DealList deals={items} pipelineNames={pipelineNames} /> : null}{!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}</div>
  </section>;
}
