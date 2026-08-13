"use client";

import { useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { v3Service } from "@/services/v3-service";
import type { AiDealInsight } from "@/types/v3";

export function DealAiInsight({ dealId }: { dealId: string }) {
  const { t }=useI18n(); const {notify}=useToast(); const {user}=useAuth(); const permissions=useMemo(()=>new Set(user?.permissions.map(p=>p.name)??[]),[user]);
  const [insight,setInsight]=useState<AiDealInsight|null>(null); const [loading,setLoading]=useState(false);
  if(!permissions.has("ai.use"))return null;
  async function analyze(){setLoading(true);try{setInsight(await v3Service.ai.dealInsight(dealId));}catch(cause){notify({tone:"error",title:t("AI analysis unavailable"),description:t(cause instanceof ApiError?cause.message:"Unable to run local AI analysis.")});}finally{setLoading(false);}}
  const risk=insight?.risk_level; const tone=risk==="high"?"border-rose-200 bg-rose-50/60 dark:border-rose-900 dark:bg-rose-950/25":risk==="medium"?"border-amber-200 bg-amber-50/60 dark:border-amber-900 dark:bg-amber-950/25":"border-emerald-200 bg-emerald-50/60 dark:border-emerald-900 dark:bg-emerald-950/25";
  return <section className={`rounded-2xl border p-5 ${insight?tone:"border-violet-200/70 bg-violet-50/55 dark:border-violet-900/70 dark:bg-violet-950/25"}`}><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[.12em] text-violet-600 rtl:tracking-normal dark:text-violet-300"><T>Local AI deal coach</T></p><h2 className="mt-2 text-base font-black text-slate-950 dark:text-white"><T>{insight?"Deal insight":"Analyze this opportunity"}</T></h2></div><Button disabled={loading} onClick={()=>void analyze()} size="sm" variant="secondary">{loading?t("Analyzing…"):insight?t("Refresh insight"):t("Analyze locally")}</Button></div>{insight?<div className="mt-4"><div className="flex items-center gap-2"><span className="rounded-lg bg-white/80 px-2 py-1 text-[10px] font-black uppercase text-slate-700 ring-1 ring-black/5 dark:bg-slate-950/60 dark:text-slate-200">{t(`${insight.risk_level} risk`)}</span><span className="text-[10px] text-slate-400" data-bidi="ltr">{insight.model}</span></div><p className="mt-3 text-sm leading-7 text-slate-700 dark:text-slate-200">{insight.summary}</p>{insight.risk_reasons.length?<div className="mt-4"><p className="text-xs font-black text-slate-900 dark:text-white"><T>Risk signals</T></p><ul className="mt-2 space-y-1.5 text-xs text-slate-600 dark:text-slate-300">{insight.risk_reasons.map(item=><li key={item}>• {item}</li>)}</ul></div>:null}{insight.next_actions.length?<div className="mt-4"><p className="text-xs font-black text-slate-900 dark:text-white"><T>Recommended next actions</T></p><ol className="mt-2 space-y-1.5 text-xs text-slate-600 dark:text-slate-300">{insight.next_actions.map((item,index)=><li key={item}>{index+1}. {item}</li>)}</ol></div>:null}</div>:<p className="mt-3 text-xs leading-5 text-slate-500"><T>Uses the configured local Ollama model and CRM deal context. No paid AI API key is required.</T></p>}</section>;
}
