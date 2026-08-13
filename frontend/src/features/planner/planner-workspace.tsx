"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/page-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast-provider";
import { PlannerCalendar, type PlannerCalendarEntry } from "@/features/planner/planner-calendar";
import { useAuth } from "@/hooks/use-auth";
import { activityService } from "@/services/activity-service";
import { ApiError } from "@/services/api-client";
import { taskService } from "@/services/task-service";
import { downloadPlannerCalendar } from "@/utils/calendar-export";
import type { Activity } from "@/types/activity";
import type { Task } from "@/types/task";

const DAY_MS = 24 * 60 * 60 * 1000;

type PlannerItem =
  | { dueDate: string | null; id: string; kind: "task"; task: Task }
  | { activity: Activity; dueDate: string | null; id: string; kind: "activity" };

type Bucket = "overdue" | "today" | "week" | "later" | "unscheduled";

type PlannerData = { activities: Activity[]; error: string | null; tasks: Task[] };

function startOfDay(value: Date): Date {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

function bucketFor(value: string | null, today: Date): Bucket {
  if (!value) return "unscheduled";
  const due = new Date(value);
  if (Number.isNaN(due.getTime())) return "unscheduled";
  const dueDay = startOfDay(due).getTime();
  const todayTime = startOfDay(today).getTime();
  if (dueDay < todayTime) return "overdue";
  if (dueDay === todayTime) return "today";
  if (dueDay <= todayTime + 7 * DAY_MS) return "week";
  return "later";
}

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load your work planner.";
}

function plannerHref(item: PlannerItem): string {
  return item.kind === "task" ? `/dashboard/tasks/${item.id}` : `/dashboard/activities/${item.id}`;
}

export function PlannerWorkspace() {
  const { user } = useAuth();
  const { enumLabel, formatNumber, t } = useI18n();
  const { notify } = useToast();
  const permissions = useMemo(() => new Set(user?.permissions.map((permission) => permission.name) ?? []), [user]);
  const canReadTasks = permissions.has("tasks.read");
  const canReadActivities = permissions.has("activities.read");
  const canUpdateTasks = permissions.has("tasks.update");
  const canUpdateActivities = permissions.has("activities.update");

  const [tasks, setTasks] = useState<Task[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [reloadNonce, setReloadNonce] = useState(0);
  const [viewMode, setViewMode] = useState<"agenda" | "calendar">("agenda");

  const fetchPlannerData = useCallback(async (): Promise<PlannerData> => {
    const taskRequest = canReadTasks
      ? taskService.list({ page: 1, page_size: 100, sort_by: "due_date", sort_direction: "asc" })
      : Promise.resolve(null);
    const activityRequest = canReadActivities
      ? activityService.list({ completed: false, page: 1, page_size: 100, sort_by: "due_date", sort_direction: "asc" })
      : Promise.resolve(null);

    const [taskResult, activityResult] = await Promise.allSettled([taskRequest, activityRequest]);
    let nextError: string | null = null;
    let nextTasks: Task[] = [];
    let nextActivities: Activity[] = [];

    if (taskResult.status === "fulfilled" && taskResult.value) {
      nextTasks = taskResult.value.items.filter((task) => !["completed", "cancelled"].includes(task.status));
    } else if (taskResult.status === "rejected") {
      nextError = errorMessage(taskResult.reason);
    }

    if (activityResult.status === "fulfilled" && activityResult.value) {
      nextActivities = activityResult.value.items;
    } else if (activityResult.status === "rejected") {
      nextError ??= errorMessage(activityResult.reason);
    }

    return { activities: nextActivities, error: nextError, tasks: nextTasks };
  }, [canReadActivities, canReadTasks]);

  useEffect(() => {
    let active = true;

    fetchPlannerData()
      .then((data) => {
        if (!active) return;
        setTasks(data.tasks);
        setActivities(data.activities);
        setError(data.error);
        setIsLoading(false);
      })
      .catch((caught) => {
        if (!active) return;
        setError(errorMessage(caught));
        setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [fetchPlannerData, reloadNonce]);

  const items = useMemo<PlannerItem[]>(() => {
    const combined: PlannerItem[] = [
      ...tasks.map((task) => ({ dueDate: task.due_date, id: task.id, kind: "task" as const, task })),
      ...activities.map((activity) => ({ activity, dueDate: activity.due_date, id: activity.id, kind: "activity" as const })),
    ];
    return combined.sort((left, right) => {
      if (!left.dueDate && !right.dueDate) return 0;
      if (!left.dueDate) return 1;
      if (!right.dueDate) return -1;
      return new Date(left.dueDate).getTime() - new Date(right.dueDate).getTime();
    });
  }, [activities, tasks]);

  const calendarEntries = useMemo<PlannerCalendarEntry[]>(() => items.flatMap((item) => {
    if (!item.dueDate) return [];
    return [{
      dueDate: item.dueDate,
      href: plannerHref(item),
      id: item.id,
      kind: item.kind,
      meta: item.kind === "task" ? enumLabel(item.task.priority) : enumLabel(item.activity.type),
      title: item.kind === "task" ? item.task.title : item.activity.title,
    }];
  }), [enumLabel, items]);

  const today = startOfDay(new Date());
  const grouped: Record<Bucket, PlannerItem[]> = { overdue: [], today: [], week: [], later: [], unscheduled: [] };
  for (const item of items) grouped[bucketFor(item.dueDate, today)].push(item);

  function requestReload() {
    setIsLoading(true);
    setReloadNonce((value) => value + 1);
  }

  async function markDone(item: PlannerItem) {
    setUpdatingId(item.id);
    try {
      if (item.kind === "task") {
        await taskService.update(item.id, { status: "completed" });
      } else {
        await activityService.update(item.id, { completed: true });
      }
      notify({ title: t("Work item completed"), tone: "success" });
      requestReload();
    } catch (caught) {
      const message = errorMessage(caught);
      setError(message);
      notify({ description: message, title: t("Unable to update work item"), tone: "error" });
    } finally {
      setUpdatingId(null);
    }
  }

  const buckets: Array<{ key: Bucket; title: string; description: string }> = [
    { key: "overdue", title: "Overdue", description: "Work that needs attention now." },
    { key: "today", title: "Today", description: "Your focus for today." },
    { key: "week", title: "Next 7 days", description: "Upcoming commitments and follow-ups." },
    { key: "later", title: "Later", description: "Future work already on the radar." },
    { key: "unscheduled", title: "Unscheduled", description: "Work that still needs a due date." },
  ];

  if (isLoading) return <LoadingState label="Loading work planner..." />;
  if (!canReadTasks && !canReadActivities) {
    return <ErrorState description="You do not have permission to view tasks or activities." title="Planner is unavailable" />;
  }

  return (
    <section className="crm-page mx-auto max-w-7xl">
      <div className="crm-hero px-6 py-7 sm:px-8">
        <div aria-hidden="true" className="absolute -end-20 -top-28 h-64 w-64 rounded-full bg-violet-500/10 blur-3xl" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="crm-kicker"><T>Execution planner</T></p>
            <h1 className="mt-5 text-3xl font-bold tracking-[-0.045em] text-slate-950 dark:text-white sm:text-[2.55rem]"><T>{"One place for today's follow-ups"}</T></h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400"><T>{"Prioritize overdue work, today's commitments and the next seven days without jumping between modules."}</T></p>
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="inline-flex rounded-xl border border-slate-200 bg-white/70 p-1 shadow-sm dark:border-slate-700 dark:bg-slate-900/70" role="group" aria-label={t("Planner view")}>
              <button aria-pressed={viewMode === "agenda"} className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${viewMode === "agenda" ? "bg-slate-950 text-white shadow-sm dark:bg-white dark:text-slate-950" : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"}`} onClick={() => setViewMode("agenda")} type="button">{t("Agenda")}</button>
              <button aria-pressed={viewMode === "calendar"} className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${viewMode === "calendar" ? "bg-slate-950 text-white shadow-sm dark:bg-white dark:text-slate-950" : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"}`} onClick={() => setViewMode("calendar")} type="button">{t("Calendar")}</button>
            </div>
            {canReadTasks ? <Link className="inline-flex min-h-10 items-center rounded-xl border border-slate-200 bg-white/70 px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition hover:-translate-y-px hover:bg-white dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-200" href="/dashboard/tasks"><T>Open tasks</T></Link> : null}
            {canReadActivities ? <Link className="inline-flex min-h-10 items-center rounded-xl bg-gradient-to-b from-violet-500 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-[0_8px_22px_rgba(109,40,217,.20)] transition hover:-translate-y-px hover:shadow-[0_11px_28px_rgba(109,40,217,.28)]" href="/dashboard/activities"><T>Open activities</T></Link> : null}
            <Button disabled={!calendarEntries.length} onClick={() => downloadPlannerCalendar(calendarEntries)} variant="secondary"><T>Export calendar</T></Button>
            <Button onClick={requestReload} variant="secondary"><T>Refresh data</T></Button>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="crm-metric border-rose-200/70 p-5 dark:border-rose-950"><p className="text-xs font-bold uppercase tracking-[0.14em] text-rose-600 dark:text-rose-300"><T>Overdue</T></p><p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{formatNumber(grouped.overdue.length)}</p></article>
        <article className="crm-metric border-indigo-200/70 p-5 dark:border-indigo-950"><p className="text-xs font-bold uppercase tracking-[0.14em] text-indigo-600 dark:text-indigo-300"><T>Today</T></p><p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{formatNumber(grouped.today.length)}</p></article>
        <article className="crm-metric border-emerald-200/70 p-5 dark:border-emerald-950"><p className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-600 dark:text-emerald-300"><T>Next 7 days</T></p><p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{formatNumber(grouped.week.length)}</p></article>
        <article className="crm-metric p-5"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500"><T>Total open work</T></p><p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{formatNumber(items.length)}</p></article>
      </div>

      {error ? <div className="mt-6"><ErrorState action={<Button onClick={requestReload}><T>Try again</T></Button>} description={error} title="Some planner data could not be loaded" /></div> : null}

      {viewMode === "calendar" ? <PlannerCalendar entries={calendarEntries} /> : null}

      {viewMode === "agenda" ? <div className="mt-8 grid gap-6 xl:grid-cols-2">
        {buckets.map((bucket) => {
          const bucketItems = grouped[bucket.key];
          if (bucketItems.length === 0 && bucket.key === "later") return null;
          return (
            <article className="crm-card overflow-hidden" key={bucket.key}>
              <div className="border-b border-slate-200/60 bg-slate-50/55 px-5 py-4 dark:border-slate-800 dark:bg-slate-900/35"><div className="flex items-center justify-between gap-3"><div><h2 className="text-base font-bold text-slate-950 dark:text-white">{t(bucket.title)}</h2><p className="mt-1 text-xs text-slate-500">{t(bucket.description)}</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold tabular-nums text-slate-600 dark:bg-slate-900 dark:text-slate-300">{formatNumber(bucketItems.length)}</span></div></div>
              {bucketItems.length === 0 ? <div className="p-5"><EmptyState description="Nothing needs attention in this section." title="All clear" /></div> : (
                <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                  {bucketItems.slice(0, 20).map((item) => {
                    const canComplete = item.kind === "task" ? canUpdateTasks : canUpdateActivities;
                    return (
                      <li className="group flex items-center gap-3 px-5 py-4 transition hover:bg-indigo-50/35 dark:hover:bg-indigo-950/10" key={`${item.kind}-${item.id}`}>
                        <Link className="min-w-0 flex-1 rounded-lg focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:focus-visible:ring-indigo-950" href={plannerHref(item)}>
                          <div className="flex flex-wrap items-center gap-2"><StatusBadge tone={item.kind === "task" ? "blue" : "violet"}>{item.kind === "task" ? <T>Task</T> : <T>Activity</T>}</StatusBadge>{item.kind === "task" ? <StatusBadge tone={item.task.priority === "urgent" ? "red" : item.task.priority === "high" ? "orange" : "gray"}><LocalizedEnum value={item.task.priority} /></StatusBadge> : <StatusBadge tone="gray"><LocalizedEnum value={item.activity.type} /></StatusBadge>}</div>
                          <p className="mt-2 truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{item.kind === "task" ? item.task.title : item.activity.title}</p>
                          <p className="mt-1 text-xs text-slate-500">{item.dueDate ? <LocalizedDateTime value={item.dueDate} /> : t("No due date")}</p>
                        </Link>
                        {canComplete ? <Button disabled={updatingId === item.id} onClick={() => void markDone(item)} size="sm" variant="secondary">{updatingId === item.id ? t("Saving...") : t("Mark done")}</Button> : null}
                      </li>
                    );
                  })}
                </ul>
              )}
            </article>
          );
        })}
      </div> : null}
    </section>
  );
}
