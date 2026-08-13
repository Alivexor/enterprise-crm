"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { ActivityForm } from "@/features/activities/activity-form";
import { ActivityList } from "@/features/activities/activity-list";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { activityService } from "@/services/activity-service";
import { activityTypes, type ActivityInput, type ActivityType } from "@/types/activity";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to save this activity."; }

export function ActivitiesWorkspace({ initialCreate = false }: { initialCreate?: boolean } = {}) {
  const [isCreating, setIsCreating] = useState(initialCreate); const [isSaving, setIsSaving] = useState(false); const [page, setPage] = useState(1); const [type, setType] = useState<ActivityType | "">(""); const [completed, setCompleted] = useState<"" | "completed" | "open">(""); const [saveError, setSaveError] = useState<string | null>(null);
  const loadActivities = useCallback(() => activityService.list({ completed: completed === "" ? undefined : completed === "completed", page, page_size: 25, type: type || undefined }), [completed, page, type]);
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadActivities);
  async function createActivity(values: ActivityInput) { setIsSaving(true); setSaveError(null); try { await activityService.create(values); setIsCreating(false); reload(); } catch (caughtError) { setSaveError(getErrorMessage(caughtError)); } finally { setIsSaving(false); } }
  return <section className="crm-page mx-auto max-w-6xl"><div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="crm-kicker"><T>Work</T></p><h1 className="crm-title mt-3"><T>Activities</T></h1><p className="crm-subtitle mt-3"><T>Record calls, emails, meetings, and customer follow-ups.</T></p></div><Button aria-controls="new-activity-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>{isCreating ? <T>Close form</T> : <T>Add activity</T>}</Button></div>
    {isCreating ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-activity-form"><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New activity</T></h2><p className="mt-1 text-sm text-slate-500"><T>Log an interaction or create a future follow-up.</T></p><div className="mt-6"><ActivityForm isSubmitting={isSaving} onCancel={() => setIsCreating(false)} onSubmit={createActivity} submitLabel="Create activity" /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}</div> : null}
    <div className="crm-toolbar mt-8 flex flex-col gap-3 sm:flex-row"><label className="sr-only" htmlFor="activity-type-filter"><T>Filter by type</T></label><select className="crm-select rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="activity-type-filter" onChange={(event) => { setType(event.target.value as ActivityType | ""); setPage(1); }} value={type}><option value=""><T>All types</T></option>{activityTypes.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}</select><label className="sr-only" htmlFor="activity-completed-filter"><T>Filter by completion</T></label><select className="crm-select rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="activity-completed-filter" onChange={(event) => { setCompleted(event.target.value as typeof completed); setPage(1); }} value={completed}><option value=""><T>All states</T></option><option value="open"><T>Open</T></option><option value="completed"><T>Completed</T></option></select></div>
    <div className="mt-6">{isLoading ? <LoadingState label="Loading activities…" /> : null}{!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load activities" /> : null}{!isLoading && !error ? <ActivityList activities={items} /> : null}{!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}</div>
  </section>;
}
