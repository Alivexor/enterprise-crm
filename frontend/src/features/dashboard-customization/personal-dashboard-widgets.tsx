"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { v3Service } from "@/services/v3-service";
import type { DashboardWidget, DataQuality, RevenueForecast, SalesGoal } from "@/types/v3";

type WidgetData = { widget: DashboardWidget; value: string; hint: string };

export function PersonalDashboardWidgets() {
  const { formatMoney, formatNumber, t } = useI18n();
  const [items, setItems] = useState<WidgetData[]>([]);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const widgets = await v3Service.dashboards.list();
        const qualityPromise = widgets.some((w)=>w.widget_type==="data_quality") ? v3Service.intelligence.dataQuality().catch(()=>null) : Promise.resolve<DataQuality|null>(null);
        const forecastPromise = widgets.some((w)=>w.widget_type==="forecast") ? v3Service.intelligence.forecast().catch(()=>null) : Promise.resolve<RevenueForecast|null>(null);
        const goalsPromise = widgets.some((w)=>w.widget_type==="goal") ? v3Service.goals.list().catch(()=>[]) : Promise.resolve<SalesGoal[]>([]);
        const [quality, forecast, goals] = await Promise.all([qualityPromise, forecastPromise, goalsPromise]);
        const resolved = await Promise.all(widgets.slice(0,6).map(async (widget): Promise<WidgetData> => {
          if (widget.widget_type === "data_quality") return { widget, value: quality ? `${formatNumber(quality.score)}%` : "—", hint: quality ? `${formatNumber(quality.total_issues)} ${t("issues")}` : t("Unavailable") };
          if (widget.widget_type === "forecast") {
            const preferred = forecast?.currency_breakdown?.[0];
            const value = preferred ? formatMoney(preferred.weighted_pipeline, preferred.currency) : forecast?.currency ? formatMoney(forecast.weighted_pipeline, forecast.currency) : "—";
            return { widget, value, hint: t("Weighted pipeline") };
          }
          if (widget.widget_type === "goal") {
            const goalId = typeof widget.config.goal_id === "string" ? widget.config.goal_id : undefined;
            const goal = goals.find((g)=>g.id===goalId) ?? goals[0];
            return { widget, value: goal ? `${formatNumber(Number(goal.progress_percent))}%` : "—", hint: goal?.name ?? t("No goal selected") };
          }
          const resource = typeof widget.config.resource === "string" ? widget.config.resource : "deals";
          const metric = typeof widget.config.metric === "string" ? widget.config.metric : "count";
          const groupBy = typeof widget.config.group_by === "string" ? widget.config.group_by : "status";
          try { const report = await v3Service.intelligence.report(resource, metric, groupBy); return { widget, value: metric === "count" ? formatNumber(Number(report.total)) : formatNumber(Number(report.total)), hint: `${t(resource)} · ${t(groupBy)}` }; }
          catch { return { widget, value: "—", hint: t("Report unavailable") }; }
        }));
        if (active) setItems(resolved);
      } catch { if (active) setItems([]); }
    }
    void load(); return () => { active=false; };
  }, [formatMoney, formatNumber, t]);

  if (!items.length) return null;
  return <section className="mt-5"><div className="mb-3 flex items-center justify-between"><div><div className="crm-kicker"><T>My dashboard</T></div><h2 className="mt-2 text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white"><T>Personal widgets</T></h2></div><Link className="text-xs font-bold text-indigo-600 dark:text-indigo-300" href="/dashboard/settings/dashboard"><T>Customize</T></Link></div><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{items.map(({widget,value,hint})=><article className="crm-card relative overflow-hidden p-5" key={widget.id}><div aria-hidden="true" className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-500"/><p className="text-[10px] font-bold uppercase tracking-[.12em] text-slate-400"><T>{widget.widget_type}</T></p><p className="mt-3 text-sm font-black text-slate-900 dark:text-white">{widget.title}</p><p className="mt-4 text-2xl font-black tracking-[-.04em] text-slate-950 dark:text-white">{value}</p><p className="mt-2 text-xs text-slate-500">{hint}</p></article>)}</div></section>;
}
