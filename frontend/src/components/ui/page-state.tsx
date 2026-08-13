"use client";

import type { ReactNode } from "react";
import { useI18n } from "@/components/i18n/i18n-provider";

type PageStateProps = { action?: ReactNode; description?: string; title: string };

export function LoadingState({ label = "Loading" }: { label?: string }) {
  const { t } = useI18n();
  return (
    <div aria-live="polite" className="crm-card flex min-h-44 flex-col items-center justify-center px-6 py-10 text-center" role="status">
      <div className="flex items-center gap-2" aria-hidden="true">
        <span className="crm-skeleton h-2.5 w-2.5 rounded-full" />
        <span className="crm-skeleton h-2.5 w-2.5 rounded-full [animation-delay:120ms]" />
        <span className="crm-skeleton h-2.5 w-2.5 rounded-full [animation-delay:240ms]" />
      </div>
      <p className="mt-4 text-sm font-medium text-slate-500 dark:text-slate-400">{t(label)}</p>
      <p className="mt-1 text-xs text-slate-400 dark:text-slate-600">{t("Preparing your workspace")}</p>
    </div>
  );
}

export function EmptyState({ action, description, title }: PageStateProps) {
  const { t } = useI18n();
  return (
    <div className="crm-card flex min-h-52 flex-col items-center justify-center border-dashed px-7 py-12 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-50 to-cyan-50 text-indigo-500 ring-1 ring-indigo-100 dark:from-indigo-950/60 dark:to-cyan-950/30 dark:text-indigo-300 dark:ring-indigo-900/70">
        <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24"><path d="M5 7.5h14M7.5 4.5h9M7 11h10v8H7z" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" /></svg>
      </span>
      <p className="mt-4 text-sm font-bold text-slate-900 dark:text-white">{t(title)}</p>
      {description ? <p className="mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">{t(description)}</p> : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ action, description, title }: PageStateProps) {
  const { t } = useI18n();
  return (
    <div className="rounded-2xl border border-rose-200/80 bg-gradient-to-br from-rose-50 to-white px-6 py-6 shadow-sm dark:border-rose-900/70 dark:from-rose-950/35 dark:to-slate-950">
      <div className="flex items-start gap-4">
        <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600 dark:bg-rose-950 dark:text-rose-300">
          <svg aria-hidden="true" className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24"><path d="M12 8v5M12 16.5h.01M10.2 4.7 3.8 16a2 2 0 0 0 1.7 3h13a2 2 0 0 0 1.7-3L13.8 4.7a2 2 0 0 0-3.6 0Z" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>
        </span>
        <div className="min-w-0 flex-1"><p className="font-bold text-rose-900 dark:text-rose-100">{t(title)}</p>{description ? <p className="mt-1.5 text-sm leading-6 text-rose-700 dark:text-rose-200">{t(description)}</p> : null}{action ? <div className="mt-5">{action}</div> : null}</div>
      </div>
    </div>
  );
}
