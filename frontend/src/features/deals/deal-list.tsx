import { LocalizedDateTime, LocalizedEnum, LocalizedMoney } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import { StatusBadge } from "@/components/ui/status-badge";
import type { Deal } from "@/types/deal";

type DealListProps = { deals: Deal[]; pipelineNames: ReadonlyMap<string, string> };

export function DealList({ deals, pipelineNames }: DealListProps) {
  if (deals.length === 0) return <EmptyState description="Add an opportunity once a lead is ready for your sales pipeline." title="No deals yet" />;
  return <div className="crm-table-shell overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950"><div className="grid grid-cols-[minmax(0,1.2fr)_auto] gap-4 border-b border-slate-200 px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase dark:border-slate-800 sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_auto]"><span><T>Deal</T></span><span className="hidden sm:block"><T>Pipeline</T></span><span className="hidden sm:block"><T>Close date</T></span><span><T>Value</T></span></div><ul className="divide-y divide-slate-100 dark:divide-slate-800">{deals.map((deal) => <li key={deal.id}><Link className="grid grid-cols-[minmax(0,1.2fr)_auto] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-slate-900/60 sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_auto]" href={`/dashboard/deals/${deal.id}`}><span className="flex min-w-0 items-center gap-3"><RecordMark label={deal.title} tone="emerald" /><span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{deal.title}</span><span className="mt-1 block sm:hidden"><StatusBadge tone={deal.status === "won" ? "green" : deal.status === "lost" ? "red" : "blue"}><LocalizedEnum value={deal.status} /></StatusBadge></span></span></span><span className="hidden truncate text-sm text-slate-600 dark:text-slate-300 sm:block">{pipelineNames.get(deal.pipeline_id) ?? <T>Unknown pipeline</T>}</span><span className="hidden text-sm text-slate-600 dark:text-slate-300 sm:block"><LocalizedDateTime value={deal.expected_close_date} /></span><span className="text-end text-sm font-semibold text-slate-800 dark:text-slate-100"><LocalizedMoney value={deal.value} currency={deal.currency} /></span></Link></li>)}</ul></div>;
}
