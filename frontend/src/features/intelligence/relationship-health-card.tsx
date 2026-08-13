"use client";

import { useEffect, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { v3Service } from "@/services/v3-service";
import type { RelationshipHealth } from "@/types/v3";

export function RelationshipHealthCard({ companyId }: { companyId: string }) {
  const { formatDateTime, formatNumber } = useI18n();
  const [health, setHealth] = useState<RelationshipHealth | null>(null);
  useEffect(() => { let active=true; v3Service.intelligence.relationshipHealth(companyId).then((result)=>{if(active)setHealth(result);}).catch(()=>{}); return()=>{active=false;}; }, [companyId]);
  if (!health) return null;
  const tone=health.score>=80?"from-emerald-500 to-teal-500":health.score>=60?"from-amber-500 to-orange-500":"from-rose-500 to-pink-500";
  return <section className="rounded-2xl border border-slate-200/70 bg-slate-50/55 p-5 dark:border-slate-800 dark:bg-slate-900/45"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-xs font-black uppercase tracking-[.12em] text-slate-400 rtl:tracking-normal"><T>Relationship intelligence</T></p><h2 className="mt-2 text-lg font-black text-slate-950 dark:text-white"><T>{health.label}</T></h2><p className="mt-1 text-xs text-slate-500"><T>Health score based on recent activity and open opportunities.</T></p></div><div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white text-xl font-black text-slate-950 shadow-sm ring-1 ring-slate-200 dark:bg-slate-950 dark:text-white dark:ring-slate-800">{formatNumber(health.score)}</div></div><div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200/70 dark:bg-slate-800"><div className={`h-full rounded-full bg-gradient-to-r ${tone}`} style={{width:`${health.score}%`}} /></div><div className="mt-5 grid gap-3 sm:grid-cols-3"><div className="rounded-xl bg-white p-3 dark:bg-slate-950"><p className="text-[10px] font-bold text-slate-400"><T>Activities · 30d</T></p><p className="mt-1 text-sm font-black text-slate-900 dark:text-white">{formatNumber(health.activities_30d)}</p></div><div className="rounded-xl bg-white p-3 dark:bg-slate-950"><p className="text-[10px] font-bold text-slate-400"><T>Open deals</T></p><p className="mt-1 text-sm font-black text-slate-900 dark:text-white">{formatNumber(health.open_deals)}</p></div><div className="rounded-xl bg-white p-3 dark:bg-slate-950"><p className="text-[10px] font-bold text-slate-400"><T>Last activity</T></p><p className="mt-1 text-xs font-bold text-slate-900 dark:text-white">{health.last_activity_at?formatDateTime(health.last_activity_at):"—"}</p></div></div>{health.factors.length?<ul className="mt-4 flex flex-wrap gap-2">{health.factors.map(factor=><li className="rounded-lg bg-white px-2.5 py-1.5 text-[10px] font-semibold text-slate-500 ring-1 ring-slate-200 dark:bg-slate-950 dark:ring-slate-800" key={factor}><T>{factor}</T></li>)}</ul>:null}</section>;
}
