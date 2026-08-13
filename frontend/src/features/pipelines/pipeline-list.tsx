import { LocalizedDateTime } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import type { Pipeline } from "@/types/pipeline";

export function PipelineList({ pipelines }: { pipelines: Pipeline[] }) {
  if (pipelines.length === 0) return <EmptyState description="Create a sales pipeline to define how your team progresses opportunities." title="No pipelines yet" />;
  return <div className="crm-table-shell overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950"><div className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 border-b border-slate-200 px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase dark:border-slate-800 sm:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_auto]"><span><T>Pipeline</T></span><span className="hidden sm:block"><T>Description</T></span><span><T>Updated</T></span></div><ul className="divide-y divide-slate-100 dark:divide-slate-800">{pipelines.map((pipeline) => <li key={pipeline.id}><Link className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-slate-900/60 sm:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_auto]" href={`/dashboard/pipelines/${pipeline.id}`}><span className="flex min-w-0 items-center gap-3"><RecordMark label={pipeline.name} tone="indigo" /><span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{pipeline.name}</span><span className="mt-1 block truncate text-xs text-slate-500 sm:hidden">{pipeline.description ?? <T>No description</T>}</span></span></span><span className="hidden truncate text-sm text-slate-600 dark:text-slate-300 sm:block">{pipeline.description ?? "—"}</span><span className="text-end text-sm text-slate-500"><LocalizedDateTime value={pipeline.updated_at} /></span></Link></li>)}</ul></div>;
}
