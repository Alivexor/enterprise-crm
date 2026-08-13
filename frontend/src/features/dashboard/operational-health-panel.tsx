import Link from "next/link";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import type { OperationalHealth } from "@/types/dashboard";

function Signal({ description, href, label, tone, value }: { description: string; href: string; label: string; tone: "amber" | "cyan" | "indigo" | "rose"; value: string }) {
  const tones = {
    amber: "border-amber-200/70 bg-amber-50/45 text-amber-700 dark:border-amber-950 dark:bg-amber-950/15 dark:text-amber-300",
    cyan: "border-cyan-200/70 bg-cyan-50/45 text-cyan-700 dark:border-cyan-950 dark:bg-cyan-950/15 dark:text-cyan-300",
    indigo: "border-indigo-200/70 bg-indigo-50/45 text-indigo-700 dark:border-indigo-950 dark:bg-indigo-950/15 dark:text-indigo-300",
    rose: "border-rose-200/70 bg-rose-50/45 text-rose-700 dark:border-rose-950 dark:bg-rose-950/15 dark:text-rose-300",
  } as const;
  return (
    <Link className={`group rounded-2xl border p-4 transition-[transform,box-shadow,border-color] hover:-translate-y-px hover:shadow-md ${tones[tone]}`} href={href}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-extrabold uppercase tracking-[.13em] opacity-75"><T>{label}</T></p>
          <p className="mt-2 text-2xl font-extrabold tracking-[-.04em]">{value}</p>
        </div>
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/60 opacity-70 shadow-sm transition group-hover:opacity-100 dark:bg-slate-900/60">
          <svg aria-hidden="true" className="h-4 w-4 rtl:rotate-180" fill="none" viewBox="0 0 20 20"><path d="M6 10h8m-3-3 3 3-3 3" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" /></svg>
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 opacity-75"><T>{description}</T></p>
    </Link>
  );
}

export function OperationalHealthPanel({ health }: { health: OperationalHealth }) {
  const { formatMoney, formatNumber, t } = useI18n();
  const pipelineCurrency = "USD";
  const conversionRate = `${formatNumber(Number(health.lead_conversion_rate).toFixed(1))}%`;

  return (
    <section className="crm-card mt-5 overflow-hidden p-5 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="crm-kicker"><T>Operational health</T></p>
          <h2 className="mt-3 text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white"><T>Signals that need attention</T></h2>
          <p className="mt-2 max-w-2xl text-xs leading-5 text-slate-500"><T>Actionable workload and pipeline signals calculated from live CRM data.</T></p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="crm-chip">{t("Weighted pipeline")}: <strong className="ms-1 text-slate-800 dark:text-slate-100">{formatMoney(health.weighted_pipeline_value, pipelineCurrency)}</strong></span>
          <span className="crm-chip">{t("Lead conversion rate")}: <strong className="ms-1 text-slate-800 dark:text-slate-100">{conversionRate}</strong></span>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Signal description="Tasks past their due date and still open." href="/dashboard/tasks" label="Overdue tasks" tone="rose" value={formatNumber(health.overdue_tasks)} />
        <Signal description="Open tasks scheduled for today." href="/dashboard/planner" label="Due today" tone="indigo" value={formatNumber(health.tasks_due_today)} />
        <Signal description="Open leads without a recent update for 14 days." href="/dashboard/leads" label="Stale leads" tone="amber" value={formatNumber(health.stale_leads)} />
        <Signal description="Open deals without a recent update for 30 days." href="/dashboard/deals" label="Stale deals" tone="cyan" value={formatNumber(health.stale_deals)} />
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200/70 bg-slate-50/55 p-4 dark:border-slate-800 dark:bg-slate-900/45"><p className="text-xs font-semibold text-slate-500"><T>Open pipeline</T></p><p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatMoney(health.open_pipeline_value, pipelineCurrency)}</p></div>
        <div className="rounded-2xl border border-slate-200/70 bg-slate-50/55 p-4 dark:border-slate-800 dark:bg-slate-900/45"><p className="text-xs font-semibold text-slate-500"><T>Won deal value</T></p><p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatMoney(health.won_deal_value, pipelineCurrency)}</p></div>
        <div className="rounded-2xl border border-slate-200/70 bg-slate-50/55 p-4 dark:border-slate-800 dark:bg-slate-900/45"><p className="text-xs font-semibold text-slate-500"><T>Activities next 7 days</T></p><p className="mt-2 text-lg font-bold text-slate-950 dark:text-white">{formatNumber(health.activities_next_7_days)}</p></div>
      </div>
    </section>
  );
}
