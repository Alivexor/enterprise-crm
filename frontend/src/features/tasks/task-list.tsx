import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import { StatusBadge } from "@/components/ui/status-badge";
import type { Task } from "@/types/task";

function tone(status: Task["status"]): "blue" | "gray" | "green" | "orange" | "red" {
  if (status === "completed") return "green";
  if (status === "cancelled") return "gray";
  if (status === "in_progress") return "blue";
  return "orange";
}

export function TaskList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) return <EmptyState description="Add a task to keep your team's customer work organized." title="No tasks yet" />;
  return <div className="crm-table-shell overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950"><div className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 border-b border-slate-200 px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase dark:border-slate-800 sm:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_auto]"><span><T>Task</T></span><span className="hidden sm:block"><T>Due date</T></span><span><T>Status</T></span></div><ul className="divide-y divide-slate-100 dark:divide-slate-800">{tasks.map((task) => <li key={task.id}><Link className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-slate-900/60 sm:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_auto]" href={`/dashboard/tasks/${task.id}`}><span className="flex min-w-0 items-center gap-3"><RecordMark label={task.title} tone="violet" /><span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{task.title}</span><span className="mt-1 block text-xs text-slate-500 sm:hidden"><LocalizedEnum value={task.priority} /> <T>priority</T></span></span></span><span className="hidden text-sm text-slate-600 dark:text-slate-300 sm:block"><LocalizedDateTime value={task.due_date} /></span><StatusBadge tone={tone(task.status)}><LocalizedEnum value={task.status} /></StatusBadge></Link></li>)}</ul></div>;
}
