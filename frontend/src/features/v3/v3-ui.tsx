"use client";

import type { ReactNode } from "react";

import { T } from "@/components/i18n/i18n-provider";
import { cn } from "@/utils/cn";

export function V3Hero({ eyebrow, title, description, actions, accent = "indigo" }: { eyebrow: string; title: string; description: string; actions?: ReactNode; accent?: "indigo" | "cyan" | "emerald" | "amber" | "violet" }) {
  const accents = {
    indigo: "from-indigo-500/15 via-violet-500/8 to-transparent text-indigo-600 dark:text-indigo-300",
    cyan: "from-cyan-500/15 via-sky-500/8 to-transparent text-cyan-700 dark:text-cyan-300",
    emerald: "from-emerald-500/15 via-teal-500/8 to-transparent text-emerald-700 dark:text-emerald-300",
    amber: "from-amber-500/15 via-orange-500/8 to-transparent text-amber-700 dark:text-amber-300",
    violet: "from-violet-500/15 via-fuchsia-500/8 to-transparent text-violet-700 dark:text-violet-300",
  } as const;
  return (
    <header className="relative overflow-hidden rounded-[28px] border border-slate-200/70 bg-white px-5 py-6 shadow-[0_20px_70px_rgba(15,23,42,.06)] dark:border-slate-800/80 dark:bg-slate-950 sm:px-7 sm:py-7">
      <div aria-hidden="true" className={cn("pointer-events-none absolute inset-0 bg-gradient-to-br", accents[accent].split(" text-")[0])} />
      <div aria-hidden="true" className="pointer-events-none absolute -end-16 -top-20 h-56 w-56 rounded-full border border-white/60 bg-white/30 blur-3xl dark:border-white/5 dark:bg-white/[.02]" />
      <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <p className={cn("text-[10px] font-black uppercase tracking-[.2em]", accents[accent].split(" ").slice(-2).join(" "))}><T>{eyebrow}</T></p>
          <h1 className="mt-3 text-3xl font-black tracking-[-.04em] text-slate-950 dark:text-white sm:text-4xl"><T>{title}</T></h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500 dark:text-slate-400"><T>{description}</T></p>
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
    </header>
  );
}

export function V3Metric({ label, value, hint, tone = "indigo" }: { label: string; value: ReactNode; hint?: string; tone?: "indigo" | "cyan" | "emerald" | "amber" | "rose" | "violet" }) {
  const tones = {
    indigo: "from-indigo-500 to-violet-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300",
    cyan: "from-cyan-500 to-sky-500 bg-cyan-50 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300",
    emerald: "from-emerald-500 to-teal-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
    amber: "from-amber-500 to-orange-500 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
    rose: "from-rose-500 to-pink-500 bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300",
    violet: "from-violet-500 to-fuchsia-500 bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-300",
  } as const;
  const [gradient, ...rest] = tones[tone].split(" ");
  return (
    <article className="crm-card relative overflow-hidden p-5">
      <span aria-hidden="true" className={cn("absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r", gradient, rest[0])} />
      <p className="text-[11px] font-bold uppercase tracking-[.12em] text-slate-400 rtl:tracking-normal"><T>{label}</T></p>
      <div className="mt-3 text-2xl font-black tracking-[-.035em] text-slate-950 dark:text-white">{value}</div>
      {hint ? <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400"><T>{hint}</T></p> : null}
    </article>
  );
}

export function V3Section({ title, description, children, action }: { title: string; description?: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="crm-card p-5 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div><h2 className="text-base font-black tracking-[-.02em] text-slate-950 dark:text-white"><T>{title}</T></h2>{description ? <p className="mt-1.5 text-xs leading-5 text-slate-500"><T>{description}</T></p> : null}</div>
        {action}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function V3Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 px-5 py-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-400">{children}</div>;
}
