"use client";

import type { ReactNode } from "react";
import { useI18n } from "@/components/i18n/i18n-provider";
import { cn } from "@/utils/cn";

type StatusBadgeProps = { children: ReactNode; tone?: "blue" | "gray" | "green" | "orange" | "red" | "violet" };
const toneClasses = {
  blue: "border-blue-200/70 bg-blue-50/80 text-blue-700 dark:border-blue-900/70 dark:bg-blue-950/45 dark:text-blue-200",
  gray: "border-slate-200/80 bg-slate-100/80 text-slate-600 dark:border-slate-700/80 dark:bg-slate-800/80 dark:text-slate-200",
  green: "border-emerald-200/70 bg-emerald-50/80 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/45 dark:text-emerald-200",
  orange: "border-amber-200/70 bg-amber-50/80 text-amber-700 dark:border-amber-900/70 dark:bg-amber-950/45 dark:text-amber-200",
  red: "border-rose-200/70 bg-rose-50/80 text-rose-700 dark:border-rose-900/70 dark:bg-rose-950/45 dark:text-rose-200",
  violet: "border-violet-200/70 bg-violet-50/80 text-violet-700 dark:border-violet-900/70 dark:bg-violet-950/45 dark:text-violet-200",
} as const;
const dots = { blue: "bg-blue-500", gray: "bg-slate-400", green: "bg-emerald-500", orange: "bg-amber-500", red: "bg-rose-500", violet: "bg-violet-500" } as const;
export function StatusBadge({ children, tone = "gray" }: StatusBadgeProps) {
  const { enumLabel } = useI18n();
  const localized = typeof children === "string" ? enumLabel(children) : children;
  return <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-bold leading-none shadow-[inset_0_1px_0_rgba(255,255,255,.5)]", toneClasses[tone])}><span aria-hidden="true" className={cn("h-1.5 w-1.5 rounded-full", dots[tone])} />{localized}</span>;
}
