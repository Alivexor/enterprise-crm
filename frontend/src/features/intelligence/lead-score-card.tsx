"use client";

import { useEffect, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { V3Empty } from "@/features/v3/v3-ui";
import { ApiError } from "@/services/api-client";
import { v3Service } from "@/services/v3-service";
import type { LeadScore } from "@/types/v3";

function message(error: unknown) {
  return error instanceof ApiError ? error.message : "Unable to calculate lead score.";
}

export function LeadScoreCard({ leadId }: { leadId: string }) {
  const { formatNumber, t } = useI18n();
  const [score, setScore] = useState<LeadScore | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void v3Service.intelligence.leadScore(leadId).then((result) => {
      if (active) { setScore(result); setError(null); }
    }).catch((cause) => {
      if (active) setError(message(cause));
    });
    return () => { active = false; };
  }, [leadId]);

  if (error) return <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">{t(error)}</div>;
  if (!score) return <V3Empty><T>Calculating lead score…</T></V3Empty>;

  const tone = score.grade === "A" ? "from-emerald-500 to-cyan-500" : score.grade === "B" ? "from-indigo-500 to-cyan-500" : score.grade === "C" ? "from-amber-500 to-orange-500" : "from-rose-500 to-orange-500";
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-900/45">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><p className="crm-kicker"><T>Lead intelligence</T></p><h2 className="mt-2 text-lg font-black text-slate-950 dark:text-white"><T>Deterministic lead score</T></h2></div>
        <div className="flex items-baseline gap-2"><span className="text-4xl font-black text-slate-950 dark:text-white">{formatNumber(score.score)}</span><span className="rounded-xl bg-slate-950 px-2.5 py-1 text-sm font-black text-white dark:bg-white dark:text-slate-950">{score.grade}</span></div>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><div className={`h-full rounded-full bg-gradient-to-r ${tone}`} style={{ width: `${score.score}%` }} /></div>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div><p className="text-xs font-black uppercase tracking-[.1em] text-slate-400"><T>Score factors</T></p><ul className="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">{score.factors.map((factor) => <li className="flex gap-2" key={factor}><span className="text-emerald-500">•</span><T>{factor}</T></li>)}</ul></div>
        <div><p className="text-xs font-black uppercase tracking-[.1em] text-slate-400"><T>Next best actions</T></p>{score.next_actions.length ? <ul className="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">{score.next_actions.map((action) => <li className="flex gap-2" key={action}><span className="text-indigo-500">→</span><T>{action}</T></li>)}</ul> : <p className="mt-2 text-sm text-emerald-600 dark:text-emerald-300"><T>No immediate action is required.</T></p>}</div>
      </div>
    </div>
  );
}
