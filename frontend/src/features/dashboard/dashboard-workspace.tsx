"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { dashboardService } from "@/services/dashboard-service";
import { OperationalHealthPanel } from "@/features/dashboard/operational-health-panel";
import { PersonalDashboardWidgets } from "@/features/dashboard-customization/personal-dashboard-widgets";
import type { AnalyticsData, DashboardData, OperationalHealth, StatusAnalyticsItem } from "@/types/dashboard";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to load dashboard data."; }

const metricVisuals = [
  { gradient: "from-indigo-500 to-violet-500", glow: "bg-indigo-500/10", icon: <path d="M4 19V9m5 10V5m5 14v-7m5 7V3" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" /> },
  { gradient: "from-cyan-500 to-sky-500", glow: "bg-cyan-500/10", icon: <><circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.7"/><path d="M3.5 20v-1.5A5.5 5.5 0 0 1 9 13h.5a5.5 5.5 0 0 1 5.5 5.5V20M17 7v6M14 10h6" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7"/></> },
  { gradient: "from-emerald-500 to-teal-500", glow: "bg-emerald-500/10", icon: <><path d="M4.5 7.5h15v11a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-11Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.7"/><path d="M8 7.5V5.8A2.3 2.3 0 0 1 10.3 3.5h3.4A2.3 2.3 0 0 1 16 5.8v1.7M4.5 12h15" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7"/></> },
  { gradient: "from-amber-500 to-orange-500", glow: "bg-amber-500/10", icon: <><rect height="16" rx="2" stroke="currentColor" strokeWidth="1.7" width="17" x="3.5" y="5"/><path d="M7.5 3v4M16.5 3v4M3.5 9.5h17M8 14h3l1 2 4-5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7"/></> },
] as const;

function ArrowIcon() { return <svg aria-hidden="true" className="h-3.5 w-3.5 rtl:rotate-180" fill="none" viewBox="0 0 20 20"><path d="M6 10h8m-3-3 3 3-3 3" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" /></svg>; }
function MetricIcon({ children, className }: { children: ReactNode; className: string }) { return <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${className}`}><svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24">{children}</svg></span>; }

function StatusBars({ items, kind }: { items: StatusAnalyticsItem[]; kind: "deal" | "lead" }) {
  const { formatNumber, t } = useI18n();
  if (!items.length) return <p className="mt-6 text-sm text-slate-500">{t(kind === "deal" ? "No deal analytics yet." : "No lead analytics yet.")}</p>;
  const maximum = Math.max(...items.map((item) => item.count), 1);
  return (
    <ul className="mt-6 space-y-5">
      {items.map((item) => {
        const width = Math.max((item.count / maximum) * 100, 5);
        const tone = item.status === "won" || item.status === "converted" ? "green" : item.status === "lost" ? "red" : kind === "deal" ? "blue" : "orange";
        const gradient = tone === "green" ? "from-emerald-400 to-emerald-500" : tone === "red" ? "from-rose-400 to-rose-500" : tone === "orange" ? "from-amber-400 to-orange-500" : "from-indigo-400 to-violet-500";
        return (
          <li key={item.status}>
            <div className="flex items-center justify-between gap-3"><StatusBadge tone={tone}><LocalizedEnum value={item.status} /></StatusBadge><span className="text-xs font-bold tabular-nums text-slate-500 dark:text-slate-400">{formatNumber(item.count)}{kind === "deal" && item.total_value !== null ? ` · ${formatNumber(item.total_value)}` : ""}</span></div>
            <div className="mt-2.5 h-2 overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200/50 dark:bg-slate-800 dark:ring-slate-700/50"><div className={`h-full rounded-full bg-gradient-to-r ${gradient} shadow-[0_0_10px_rgba(99,102,241,.18)] transition-[width] duration-700 ease-out`} style={{ width: `${width}%` }} /></div>
          </li>
        );
      })}
    </ul>
  );
}

function AnalyticsPanel({ analytics }: { analytics: AnalyticsData | null }) {
  const { formatNumber } = useI18n();
  if (!analytics) return null;
  return (
    <section className="mt-6 space-y-5">
      <div className="grid gap-5 xl:grid-cols-2">
        <article className="crm-card p-5 sm:p-6"><div className="flex items-start justify-between"><div><div className="crm-kicker"><T>Revenue</T></div><h2 className="mt-3 text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white"><T>Deals by status</T></h2></div><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-500 dark:bg-indigo-950/50 dark:text-indigo-300"><svg aria-hidden="true" className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24"><path d="M4 18 9 13l3 3 7-9" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8"/></svg></span></div><StatusBars items={analytics.deals_by_status} kind="deal" /></article>
        <article className="crm-card p-5 sm:p-6"><div className="flex items-start justify-between"><div><div className="crm-kicker"><T>Acquisition</T></div><h2 className="mt-3 text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white"><T>Leads by status</T></h2></div><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-50 text-cyan-600 dark:bg-cyan-950/40 dark:text-cyan-300"><svg aria-hidden="true" className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.7"/><path d="M3.5 20v-1.2A5.8 5.8 0 0 1 9.3 13h.4a5.8 5.8 0 0 1 5.8 5.8V20M17 6v7M13.5 9.5h7" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7"/></svg></span></div><StatusBars items={analytics.leads_by_status} kind="lead" /></article>
      </div>
      {analytics.pipeline.length ? (
        <article className="crm-card p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><div className="crm-kicker"><T>Pipeline health</T></div><h2 className="mt-3 text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white"><T>Stage distribution</T></h2></div><Link className="inline-flex items-center gap-1.5 text-sm font-bold text-indigo-600 transition hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/pipelines"><T>Manage pipelines</T><ArrowIcon /></Link></div>
          <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {analytics.pipeline.slice(0, 9).map((item, index) => (
              <div className="group rounded-2xl border border-slate-200/70 bg-slate-50/70 px-4 py-4 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-white hover:shadow-md dark:border-slate-800 dark:bg-slate-900/55 dark:hover:border-indigo-900 dark:hover:bg-slate-900" key={`${item.pipeline_id}-${item.stage_id}`}>
                <div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="truncate text-sm font-bold text-slate-900 dark:text-white">{item.stage_name}</p><p className="mt-1 truncate text-[11px] text-slate-500">{item.pipeline_name}</p></div><span className={`flex h-8 min-w-8 items-center justify-center rounded-xl px-2 text-xs font-extrabold tabular-nums ${index % 3 === 0 ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-300" : index % 3 === 1 ? "bg-cyan-50 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300" : "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-300"}`}>{formatNumber(item.deal_count)}</span></div>
                <div className="mt-4 flex items-center justify-between border-t border-slate-200/60 pt-3 dark:border-slate-800"><span className="text-[11px] font-medium text-slate-400"><T>Value</T></span><span className="text-xs font-bold tabular-nums text-slate-700 dark:text-slate-200">{formatNumber(item.total_value)}</span></div>
              </div>
            ))}
          </div>
        </article>
      ) : null}
    </section>
  );
}

export function DashboardWorkspace() {
  const { formatNumber, t } = useI18n();
  const { user } = useAuth();
  const canViewSalesBoard = user?.permissions.some((permission) => permission.name === "deals.read") && user?.permissions.some((permission) => permission.name === "pipelines.read");
  const canViewPlanner = user?.permissions.some((permission) => ["tasks.read", "activities.read"].includes(permission.name));
  const [dashboard, setDashboard] = useState<DashboardData | null>(null); const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [health, setHealth] = useState<OperationalHealth | null>(null);
  const [error, setError] = useState<string | null>(null); const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true); const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    let isActive = true;
    async function loadDashboard() {
      setIsLoading(true);
      try {
        const [dashboardResult, analyticsResult, healthResult] = await Promise.allSettled([
          dashboardService.getDashboard(),
          dashboardService.getAnalytics(),
          dashboardService.getOperationalHealth(),
        ]);
        if (!isActive) return;
        if (dashboardResult.status === "fulfilled") { setDashboard(dashboardResult.value); setError(null); } else setError(getErrorMessage(dashboardResult.reason));
        if (analyticsResult.status === "fulfilled") { setAnalytics(analyticsResult.value); setAnalyticsError(null); } else { setAnalytics(null); setAnalyticsError(getErrorMessage(analyticsResult.reason)); }
        if (healthResult.status === "fulfilled") setHealth(healthResult.value); else setHealth(null);
      } finally { if (isActive) setIsLoading(false); }
    }
    void loadDashboard(); return () => { isActive = false; };
  }, [reloadNonce]);

  if (isLoading) return <LoadingState label="Loading dashboard..." />;
  if (!dashboard) return <ErrorState action={<Button onClick={() => setReloadNonce((value) => value + 1)}><T>Try again</T></Button>} description={error ?? "Dashboard data is unavailable."} title="Unable to load dashboard" />;

  return (
    <section className="crm-page mx-auto max-w-[1480px]">
      <div className="crm-hero px-6 py-7 sm:px-8 sm:py-8 lg:px-9">
        <div className="relative z-[1] grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
          <div><div className="crm-kicker"><T>Live workspace</T></div><h1 className="mt-5 max-w-3xl text-3xl font-bold tracking-[-.045em] text-slate-950 dark:text-white sm:text-[2.55rem] sm:leading-[1.08]"><T>Revenue command center</T></h1><p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400"><T>Customer relationships, sales execution and team follow-ups in one operational view.</T></p><div className="mt-5 flex flex-wrap items-center gap-2"><span className="crm-chip"><span className="me-1.5 h-1.5 w-1.5 rounded-full bg-emerald-500" />{t("Live data")}</span><span className="crm-chip">{user?.first_name ? `${t("Welcome")}, ${user.first_name}` : t("Team workspace")}</span></div></div>
          <div className="flex flex-wrap gap-2 lg:justify-end">{canViewSalesBoard ? <Link className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-gradient-to-b from-indigo-500 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-[0_8px_22px_rgba(79,70,229,.24)] transition hover:-translate-y-px hover:shadow-[0_12px_28px_rgba(79,70,229,.30)]" href="/dashboard/deals/board"><T>Open sales board</T><ArrowIcon /></Link> : null}{canViewPlanner ? <Link className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-slate-200/80 bg-white/70 px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition hover:-translate-y-px hover:bg-white dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-200" href="/dashboard/planner"><T>Open planner</T><ArrowIcon /></Link> : null}<Button onClick={() => setReloadNonce((value) => value + 1)} variant="tertiary"><T>Refresh</T></Button></div>
        </div>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {dashboard.metrics.map((metric, index) => { const visual = metricVisuals[index % metricVisuals.length]; return (
          <div className="crm-metric group p-5" key={metric.label}><div className="flex items-start justify-between gap-4"><div><dt className="text-[10px] font-bold uppercase tracking-[.13em] text-slate-400">{t(metric.label)}</dt><dd className="mt-3 text-[2rem] font-bold tracking-[-.045em] text-slate-950 dark:text-white">{formatNumber(metric.value)}</dd></div><MetricIcon className={`${visual.glow} bg-gradient-to-br ${visual.gradient} bg-clip-padding text-white shadow-sm`} >{visual.icon}</MetricIcon></div><div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-800/80"><span className="text-[11px] text-slate-400"><T>Current organization</T></span><span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /><T>Live</T></span></div></div>
        ); })}
      </dl>

      {health ? <OperationalHealthPanel health={health} /> : null}
      <PersonalDashboardWidgets />

      <section className="mt-5 grid gap-5 xl:grid-cols-2">
        <article className="crm-card overflow-hidden p-5 sm:p-6"><div className="flex items-center justify-between gap-4"><div><div className="crm-kicker"><T>Execution</T></div><h2 className="mt-3 text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white"><T>Open tasks</T></h2></div><Link className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/tasks"><T>View all</T><ArrowIcon /></Link></div>{dashboard.open_tasks.length === 0 ? <p className="mt-6 text-sm text-slate-500"><T>No open tasks.</T></p> : <ul className="mt-5 space-y-1.5">{dashboard.open_tasks.map((task) => <li key={task.id}><Link className="group flex items-center justify-between gap-3 rounded-xl border border-transparent px-3 py-3 transition hover:border-slate-200/70 hover:bg-slate-50/80 dark:hover:border-slate-800 dark:hover:bg-slate-900/60" href={`/dashboard/tasks/${task.id}`}><span className="flex min-w-0 items-center gap-3"><span className={`h-8 w-1 shrink-0 rounded-full ${task.priority === "urgent" ? "bg-rose-400" : task.priority === "high" ? "bg-amber-400" : "bg-indigo-300 dark:bg-indigo-600"}`} /><span className="min-w-0"><span className="block truncate text-sm font-bold text-slate-900 transition group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-300">{task.title}</span><span className="mt-1 block text-[11px] text-slate-500"><T>Due</T> <LocalizedDateTime value={task.due_date} /></span></span></span><StatusBadge tone={task.priority === "urgent" ? "red" : task.priority === "high" ? "orange" : "gray"}><LocalizedEnum value={task.priority} /></StatusBadge></Link></li>)}</ul>}</article>
        <article className="crm-card overflow-hidden p-5 sm:p-6"><div className="flex items-center justify-between gap-4"><div><div className="crm-kicker"><T>Engagement</T></div><h2 className="mt-3 text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white"><T>Upcoming activities</T></h2></div><Link className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/activities"><T>View all</T><ArrowIcon /></Link></div>{dashboard.upcoming_activities.length === 0 ? <p className="mt-6 text-sm text-slate-500"><T>No upcoming activities.</T></p> : <ul className="mt-5 space-y-1.5">{dashboard.upcoming_activities.map((activity, index) => <li key={activity.id}><Link className="group flex items-center gap-3 rounded-xl border border-transparent px-3 py-3 transition hover:border-slate-200/70 hover:bg-slate-50/80 dark:hover:border-slate-800 dark:hover:bg-slate-900/60" href={`/dashboard/activities/${activity.id}`}><span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${index % 3 === 0 ? "bg-cyan-50 text-cyan-600 dark:bg-cyan-950/40 dark:text-cyan-300" : index % 3 === 1 ? "bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-300" : "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-300"}`}><svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24"><path d="M5 12h3l2-5 4 10 2-5h3" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8"/></svg></span><span className="min-w-0"><span className="block truncate text-sm font-bold text-slate-900 transition group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-300">{activity.title}</span><span className="mt-1 block text-[11px] text-slate-500"><LocalizedEnum value={activity.type} /> · <LocalizedDateTime value={activity.due_date} /></span></span></Link></li>)}</ul>}</article>
      </section>

      {analyticsError ? <div className="mt-6"><ErrorState description={analyticsError} title="Analytics are currently unavailable" /></div> : <AnalyticsPanel analytics={analytics} />}
    </section>
  );
}
