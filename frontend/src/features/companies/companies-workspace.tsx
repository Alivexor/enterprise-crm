"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { CompanyForm } from "@/features/companies/company-form";
import { CompanyList } from "@/features/companies/company-list";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { companyService } from "@/services/company-service";
import type { CompanyInput } from "@/types/company";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to save this company."; }

export function CompaniesWorkspace({ initialCreate = false }: { initialCreate?: boolean } = {}) {
  const { t } = useI18n();
  const [isCreating, setIsCreating] = useState(initialCreate); const [isSaving, setIsSaving] = useState(false); const [page, setPage] = useState(1); const [search, setSearch] = useState(""); const [appliedSearch, setAppliedSearch] = useState(""); const [industry, setIndustry] = useState(""); const [saveError, setSaveError] = useState<string | null>(null);
  const loadCompanies = useCallback(() => companyService.list({ industry: industry || undefined, page, page_size: 25, search: appliedSearch || undefined, sort_by: "name", sort_direction: "asc" }), [appliedSearch, industry, page]);
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadCompanies);
  function submitSearch(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setPage(1); setAppliedSearch(search.trim()); }
  async function createCompany(values: CompanyInput) { setIsSaving(true); setSaveError(null); try { await companyService.create(values); setIsCreating(false); reload(); } catch (caughtError) { setSaveError(getErrorMessage(caughtError)); } finally { setIsSaving(false); } }
  return <section className="crm-page mx-auto max-w-6xl"><div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="crm-kicker"><T>CRM</T></p><h1 className="crm-title mt-3"><T>Companies</T></h1><p className="crm-subtitle mt-3"><T>Manage the organizations your team works with.</T></p></div><Button aria-controls="new-company-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>{isCreating ? <T>Close form</T> : <T>Add company</T>}</Button></div>
    {isCreating ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-company-form"><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New company</T></h2><p className="mt-1 text-sm text-slate-500"><T>Add the basic company information now.</T></p><div className="mt-6"><CompanyForm isSubmitting={isSaving} onCancel={() => setIsCreating(false)} onSubmit={createCompany} submitLabel="Create company" /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}</div> : null}
    <form className="crm-toolbar mt-8 flex flex-col gap-3 sm:flex-row" onSubmit={submitSearch}><label className="sr-only" htmlFor="company-search"><T>Search companies</T></label><input className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="company-search" onChange={(event) => setSearch(event.target.value)} placeholder={t("Search companies")} value={search} /><label className="sr-only" htmlFor="company-industry-filter"><T>Filter by industry</T></label><input className="crm-input rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="company-industry-filter" onChange={(event) => { setIndustry(event.target.value); setPage(1); }} placeholder={t("Industry")} value={industry} /><Button type="submit" variant="secondary"><T>Search</T></Button></form>
    <div className="mt-6">{isLoading ? <LoadingState label="Loading companies…" /> : null}{!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load companies" /> : null}{!isLoading && !error ? <CompanyList companies={items} /> : null}{!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}</div>
  </section>;
}
