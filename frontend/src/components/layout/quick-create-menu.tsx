"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { useI18n } from "@/components/i18n/i18n-provider";
import { useAuth } from "@/hooks/use-auth";

const actions = [
  { href: "/dashboard/companies?create=1", label: "Company", permission: "companies.create", tone: "bg-indigo-500" },
  { href: "/dashboard/contacts?create=1", label: "Contact", permission: "contacts.create", tone: "bg-slate-500" },
  { href: "/dashboard/leads?create=1", label: "Lead", permission: "leads.create", tone: "bg-amber-500" },
  { href: "/dashboard/deals?create=1", label: "Deal", permission: "deals.create", tone: "bg-emerald-500" },
  { href: "/dashboard/tasks?create=1", label: "Task", permission: "tasks.create", tone: "bg-violet-500" },
  { href: "/dashboard/activities?create=1", label: "Activity", permission: "activities.create", tone: "bg-cyan-500" },
  { href: "/dashboard/notes?create=1", label: "Note", permission: "notes.create", tone: "bg-fuchsia-500" },
  { href: "/dashboard/pipelines?create=1", label: "Pipeline", permission: "pipelines.create", tone: "bg-blue-500" },
] as const;

export function QuickCreateMenu() {
  const { t } = useI18n();
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const permissions = useMemo(() => new Set(user?.permissions.map((permission) => permission.name) ?? []), [user]);
  const visibleActions = actions.filter((action) => permissions.has(action.permission));

  useEffect(() => {
    function onPointerDown(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  if (visibleActions.length === 0) return null;

  return (
    <div className="relative" ref={rootRef}>
      <button
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={t("Quick create")}
        className="inline-flex h-10 items-center gap-2 rounded-xl bg-gradient-to-b from-indigo-500 to-indigo-600 px-3 text-sm font-bold text-white shadow-[0_8px_20px_rgba(79,70,229,.18)] transition-[transform,box-shadow,filter] duration-200 hover:-translate-y-px hover:shadow-[0_11px_24px_rgba(79,70,229,.26)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:focus-visible:ring-indigo-950"
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 20 20"><path d="M10 4v12M4 10h12" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" /></svg>
        <span className="hidden 2xl:inline">{t("Create")}</span>
      </button>
      {open ? (
        <div className="absolute end-0 top-[calc(100%+.6rem)] z-50 w-[300px] origin-top-right rounded-2xl border border-slate-200/80 bg-white/96 p-2 shadow-[0_24px_70px_rgba(15,23,42,.18)] ring-1 ring-slate-900/5 backdrop-blur-xl dark:border-slate-700/80 dark:bg-slate-900/96 dark:ring-white/5" role="menu">
          <div className="px-3 pb-2 pt-2">
            <p className="text-[10px] font-extrabold uppercase tracking-[.16em] text-slate-400">{t("Quick create")}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">{t("Start a new CRM record without hunting through navigation.")}</p>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            {visibleActions.map((action) => (
              <Link
                className="group flex items-center gap-2.5 rounded-xl border border-transparent px-3 py-3 text-sm font-bold text-slate-700 transition-[background-color,border-color,color,transform] hover:-translate-y-px hover:border-slate-200 hover:bg-slate-50 hover:text-slate-950 dark:text-slate-200 dark:hover:border-slate-700 dark:hover:bg-slate-800/70 dark:hover:text-white"
                href={action.href}
                key={action.href}
                onClick={() => setOpen(false)}
                role="menuitem"
              >
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${action.tone} text-xs font-extrabold text-white shadow-sm`}>{t(action.label).slice(0, 1)}</span>
                <span className="truncate">{t(action.label)}</span>
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
