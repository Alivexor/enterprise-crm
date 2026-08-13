"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/i18n-provider";

export type PlannerCalendarEntry = {
  dueDate: string;
  href: string;
  id: string;
  kind: "activity" | "task";
  meta: string;
  title: string;
};

function startOfBusinessWeek(value: Date, locale: "en" | "fa"): Date {
  const date = new Date(value.getFullYear(), value.getMonth(), value.getDate());
  const day = date.getDay();
  const weekStartsOn = locale === "fa" ? 6 : 1;
  const delta = (day - weekStartsOn + 7) % 7;
  date.setDate(date.getDate() - delta);
  return date;
}

function dayKey(value: Date): string {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

function entryDayKey(value: string): string | null {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return dayKey(date);
}

export function PlannerCalendar({ entries }: { entries: PlannerCalendarEntry[] }) {
  const { formatDate, formatNumber, locale, t } = useI18n();
  const [windowOffset, setWindowOffset] = useState(0);
  const start = useMemo(() => {
    const base = startOfBusinessWeek(new Date(), locale);
    base.setDate(base.getDate() + windowOffset * 14);
    return base;
  }, [locale, windowOffset]);

  const days = useMemo(() => Array.from({ length: 14 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    return date;
  }), [start]);

  const grouped = useMemo(() => {
    const map = new Map<string, PlannerCalendarEntry[]>();
    for (const entry of entries) {
      const key = entryDayKey(entry.dueDate);
      if (!key) continue;
      const current = map.get(key) ?? [];
      current.push(entry);
      map.set(key, current);
    }
    return map;
  }, [entries]);

  const todayKey = dayKey(new Date());
  const visibleCount = days.reduce((total, day) => total + (grouped.get(dayKey(day))?.length ?? 0), 0);

  return (
    <section className="crm-card mt-6 overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-slate-200/70 px-5 py-4 dark:border-slate-800 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-bold text-slate-950 dark:text-white">{t("Two-week schedule")}</p>
          <p className="mt-1 text-xs text-slate-500">{t("{count} scheduled items in this window", { count: formatNumber(visibleCount) })}</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800" onClick={() => setWindowOffset((value) => value - 1)} type="button">{t("Previous 2 weeks")}</button>
          <button className="rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-700 transition hover:bg-indigo-100 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-200" onClick={() => setWindowOffset(0)} type="button">{t("Today")}</button>
          <button className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800" onClick={() => setWindowOffset((value) => value + 1)} type="button">{t("Next 2 weeks")}</button>
        </div>
      </div>

      <div className="grid min-w-[840px] grid-cols-7 border-b border-slate-200/70 dark:border-slate-800">
        {days.slice(0, 7).map((day) => (
          <div className="border-e border-slate-100 bg-slate-50/70 px-3 py-2 text-center text-[10px] font-extrabold uppercase tracking-[.12em] text-slate-400 last:border-e-0 dark:border-slate-800 dark:bg-slate-900/50" key={dayKey(day)}>
            {new Intl.DateTimeFormat(locale === "fa" ? "fa-IR" : "en-US", { weekday: "short" }).format(day)}
          </div>
        ))}
      </div>

      <div className="overflow-x-auto">
        <div className="grid min-w-[840px] grid-cols-7">
          {days.map((day) => {
            const key = dayKey(day);
            const dayEntries = grouped.get(key) ?? [];
            const isToday = key === todayKey;
            return (
              <div className={`min-h-44 border-b border-e border-slate-100 p-3 last:border-e-0 dark:border-slate-800 ${isToday ? "bg-indigo-50/45 dark:bg-indigo-950/15" : "bg-white dark:bg-slate-950"}`} key={key}>
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-xs font-bold ${isToday ? "text-indigo-700 dark:text-indigo-200" : "text-slate-600 dark:text-slate-300"}`}>{formatDate(day.toISOString())}</span>
                  {dayEntries.length ? <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-extrabold text-slate-500 dark:bg-slate-800">{formatNumber(dayEntries.length)}</span> : null}
                </div>
                <div className="mt-3 space-y-2">
                  {dayEntries.slice(0, 4).map((entry) => (
                    <Link className={`block rounded-xl border px-2.5 py-2 transition hover:-translate-y-px hover:shadow-sm ${entry.kind === "task" ? "border-violet-100 bg-violet-50/80 hover:border-violet-200 dark:border-violet-950 dark:bg-violet-950/25" : "border-cyan-100 bg-cyan-50/80 hover:border-cyan-200 dark:border-cyan-950 dark:bg-cyan-950/25"}`} href={entry.href} key={`${entry.kind}-${entry.id}`}>
                      <p className="line-clamp-2 text-xs font-bold leading-4 text-slate-800 dark:text-slate-100">{entry.title}</p>
                      <p className="mt-1 truncate text-[10px] text-slate-500">{entry.meta}</p>
                    </Link>
                  ))}
                  {dayEntries.length > 4 ? <p className="px-1 text-[10px] font-bold text-slate-400">+{formatNumber(dayEntries.length - 4)} {t("more")}</p> : null}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
