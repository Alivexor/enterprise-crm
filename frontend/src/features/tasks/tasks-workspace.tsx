"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { TaskForm } from "@/features/tasks/task-form";
import { TaskList } from "@/features/tasks/task-list";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { taskService } from "@/services/task-service";
import { taskStatuses, type TaskInput, type TaskStatus } from "@/types/task";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to save this task."; }

export function TasksWorkspace({ initialCreate = false }: { initialCreate?: boolean } = {}) {
  const { t } = useI18n();
  const { user } = useAuth();
  const [isCreating, setIsCreating] = useState(initialCreate);
  const [isSaving, setIsSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [status, setStatus] = useState<TaskStatus | "">("");
  const [assignedToMe, setAssignedToMe] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const loadTasks = useCallback(() => taskService.list({ page, page_size: 25, search: appliedSearch || undefined, status: status || undefined, assigned_user_id: assignedToMe ? user?.id : undefined }), [appliedSearch, assignedToMe, page, status, user?.id]);
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadTasks);

  function submitSearch(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setPage(1); setAppliedSearch(search.trim()); }
  async function createTask(values: TaskInput) { setIsSaving(true); setSaveError(null); try { await taskService.create(values); setIsCreating(false); reload(); } catch (caughtError) { setSaveError(getErrorMessage(caughtError)); } finally { setIsSaving(false); } }

  return <section className="crm-page mx-auto max-w-6xl"><div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="crm-kicker"><T>Work</T></p><h1 className="crm-title mt-3"><T>Tasks</T></h1><p className="crm-subtitle mt-3"><T>Keep customer work moving with clear ownership and priorities.</T></p></div><Button aria-controls="new-task-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>{isCreating ? <T>Close form</T> : <T>Add task</T>}</Button></div>
    {isCreating ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-task-form"><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New task</T></h2><p className="mt-1 text-sm text-slate-500"><T>Create an actionable item for the CRM workspace.</T></p><div className="mt-6"><TaskForm isSubmitting={isSaving} onCancel={() => setIsCreating(false)} onSubmit={createTask} submitLabel="Create task" /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}</div> : null}
    <form className="crm-toolbar mt-8 flex flex-col gap-3 sm:flex-row" onSubmit={submitSearch}><label className="sr-only" htmlFor="task-search"><T>Search tasks</T></label><input className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="task-search" onChange={(event) => setSearch(event.target.value)} placeholder={t("Search tasks")} value={search} /><label className="sr-only" htmlFor="task-status-filter"><T>Filter by status</T></label><select className="crm-select rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="task-status-filter" onChange={(event) => { setStatus(event.target.value as TaskStatus | ""); setPage(1); }} value={status}><option value=""><T>All statuses</T></option>{taskStatuses.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}</select><Button aria-pressed={assignedToMe} onClick={() => { setAssignedToMe((value) => !value); setPage(1); }} type="button" variant={assignedToMe ? "primary" : "tertiary"}><T>Assigned to me</T></Button><Button type="submit" variant="secondary"><T>Search</T></Button></form>
    <div className="mt-6">{isLoading ? <LoadingState label="Loading tasks…" /> : null}{!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load tasks" /> : null}{!isLoading && !error ? <TaskList tasks={items} /> : null}{!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}</div>
  </section>;
}
