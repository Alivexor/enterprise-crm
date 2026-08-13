import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import { StatusBadge } from "@/components/ui/status-badge";
import type { Lead } from "@/types/lead";

function statusTone(status: Lead["status"]): "blue" | "gray" | "green" | "orange" | "red" {
  if (status === "converted") return "green";
  if (status === "lost" || status === "unqualified") return "red";
  if (status === "qualified") return "blue";
  return "orange";
}

export function LeadList({ leads }: { leads: Lead[] }) {
  if (leads.length === 0) {
    return <EmptyState description="Capture a potential customer to begin qualifying your sales pipeline." title="No leads yet" />;
  }

  return (
    <div className="crm-table-shell overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 border-b border-slate-200 px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase dark:border-slate-800 sm:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_auto]">
        <span><T>Lead</T></span><span className="hidden sm:block"><T>Source</T></span><span><T>Status</T></span>
      </div>
      <ul className="divide-y divide-slate-100 dark:divide-slate-800">
        {leads.map((lead) => (
          <li key={lead.id}>
            <Link className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-slate-900/60 sm:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_auto]" href={`/dashboard/leads/${lead.id}`}>
              <span className="flex min-w-0 items-center gap-3"><RecordMark label={lead.title} tone="amber" /><span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{lead.title}</span><span className="mt-1 block text-xs text-slate-500 sm:hidden"><LocalizedDateTime value={lead.created_at} /></span></span></span>
              <span className="hidden text-sm text-slate-600 dark:text-slate-300 sm:block"><LocalizedEnum value={lead.source} /></span>
              <StatusBadge tone={statusTone(lead.status)}><LocalizedEnum value={lead.status} /></StatusBadge>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
