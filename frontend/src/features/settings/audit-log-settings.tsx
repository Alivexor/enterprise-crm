"use client";

import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { T, useI18n } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useCallback, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { auditLogService } from "@/services/audit-log-service";
import type { AuditLog } from "@/types/audit-log";

const entityTypes = [
  "activity",
  "company",
  "contact",
  "deal",
  "lead",
  "note",
  "organization",
  "role",
  "task",
  "user",
] as const;

function entityHref(entry: AuditLog): string | null {
  const entityRoutes: Record<string, string> = {
    activity: "activities",
    company: "companies",
    contact: "contacts",
    deal: "deals",
    lead: "leads",
    note: "notes",
    task: "tasks",
  };
  const route = entityRoutes[entry.entity_type];
  return route ? `/dashboard/${route}/${entry.entity_id}` : null;
}

export function AuditLogSettings() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [filters, setFilters] = useState({
    action: "",
    entityType: "",
    search: "",
    sortDirection: "desc" as "asc" | "desc",
  });

  const loadEntries = useCallback(
    () => auditLogService.list({
      action: filters.action || undefined,
      entity_type: filters.entityType || undefined,
      page,
      page_size: 25,
      search: filters.search || undefined,
      sort_direction: filters.sortDirection,
    }),
    [filters, page],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadEntries);

  function submitFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setFilters({
      action: action.trim(),
      entityType,
      search: search.trim(),
      sortDirection,
    });
  }

  return (
    <section className="crm-page mx-auto max-w-6xl">
      <p className="crm-kicker"><T>Settings</T></p>
      <h1 className="crm-title mt-3"><T>Audit log</T></h1>
      <p className="crm-subtitle mt-3"><T>Review changes made in this CRM workspace.</T></p>
      <div className="mt-6"><SettingsNavigation compact /></div>

      <form className="crm-toolbar mt-8 grid gap-3 lg:grid-cols-[1fr_12rem_12rem_10rem_auto]" onSubmit={submitFilters}>
        <div><label className="sr-only" htmlFor="audit-search"><T>Search audit log</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="audit-search" maxLength={255} onChange={(event) => setSearch(event.target.value)} placeholder={t("Search actions or records")} value={search} /></div>
        <div><label className="sr-only" htmlFor="audit-action"><T>Action</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="audit-action" maxLength={100} onChange={(event) => setAction(event.target.value)} placeholder={t("Action")} value={action} /></div>
        <div><label className="sr-only" htmlFor="audit-entity-type"><T>Entity type</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="audit-entity-type" onChange={(event) => setEntityType(event.target.value)} value={entityType}><option value=""><T>All records</T></option>{entityTypes.map((type) => <option key={type} value={type}><LocalizedEnum value={type} /></option>)}</select></div>
        <div><label className="sr-only" htmlFor="audit-sort"><T>Sort order</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="audit-sort" onChange={(event) => setSortDirection(event.target.value as "asc" | "desc")} value={sortDirection}><option value="desc"><T>Newest first</T></option><option value="asc"><T>Oldest first</T></option></select></div>
        <Button type="submit" variant="secondary"><T>Apply</T></Button>
      </form>

      <div className="mt-6">
        {isLoading ? <LoadingState label="Loading audit log..." /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load audit log" /> : null}
        {!isLoading && !error && items.length === 0 ? <EmptyState description="Try a different filter or check back after people make workspace changes." title="No audit entries found" /> : null}
        {!isLoading && !error && items.length > 0 ? (
          <div className="crm-table-shell overflow-x-auto">
            <table className="w-full min-w-180 text-start text-sm">
              <thead className="border-b border-slate-100 text-xs tracking-wide text-slate-500 uppercase dark:border-slate-800"><tr><th className="px-5 py-3 font-semibold"><T>Action</T></th><th className="px-5 py-3 font-semibold"><T>Actor</T></th><th className="px-5 py-3 font-semibold"><T>Record</T></th><th className="px-5 py-3 font-semibold"><T>When</T></th></tr></thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {items.map((entry) => {
                  const href = entityHref(entry);
                  return <tr key={entry.id}><td className="px-5 py-4 font-medium text-slate-900 dark:text-white"><LocalizedEnum value={entry.action} /></td><td className="px-5 py-4"><p className="text-slate-800 dark:text-slate-100">{entry.user.first_name} {entry.user.last_name}</p><p className="mt-1 text-slate-500">{entry.user.email}</p></td><td className="px-5 py-4">{href ? <Link className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href={href}><LocalizedEnum value={entry.entity_type} /></Link> : <span className="text-slate-600 dark:text-slate-300"><LocalizedEnum value={entry.entity_type} /></span>}<p className="mt-1 max-w-48 truncate text-xs text-slate-500" title={entry.entity_id}>{entry.entity_id}</p></td><td className="px-5 py-4 text-slate-500"><LocalizedDateTime value={entry.created_at} /></td></tr>;
                })}
              </tbody>
            </table>
          </div>
        ) : null}
        {!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}
      </div>
    </section>
  );
}
