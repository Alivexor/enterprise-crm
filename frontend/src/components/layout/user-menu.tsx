"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useI18n } from "@/components/i18n/i18n-provider";
import { useAuth } from "@/hooks/use-auth";

export function UserMenu() {
  const router = useRouter();
  const { isRtl, t } = useI18n();
  const { signOut, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const menuId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const initials = `${user?.first_name[0] ?? ""}${user?.last_name[0] ?? ""}` || "U";

  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (event: PointerEvent) => { if (!containerRef.current?.contains(event.target as Node)) setIsOpen(false); };
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") { setIsOpen(false); triggerRef.current?.focus(); } };
    document.addEventListener("pointerdown", onPointerDown); document.addEventListener("keydown", onKeyDown);
    return () => { document.removeEventListener("pointerdown", onPointerDown); document.removeEventListener("keydown", onKeyDown); };
  }, [isOpen]);

  async function handleSignOut() { setIsSigningOut(true); try { await signOut(); } finally { router.replace("/login"); } }

  return (
    <div className="relative" ref={containerRef}>
      <button aria-label={t("Open user menu")} aria-controls={menuId} aria-expanded={isOpen} aria-haspopup="menu" className="group flex items-center gap-2 rounded-xl border border-transparent p-1 transition-[background-color,border-color,box-shadow,transform] duration-200 hover:border-slate-200/70 hover:bg-white hover:shadow-sm focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:hover:border-slate-800 dark:hover:bg-slate-900 dark:focus-visible:ring-indigo-950" onClick={() => setIsOpen((open) => !open)} ref={triggerRef} type="button">
        <span className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 text-xs font-extrabold text-indigo-700 ring-1 ring-inset ring-indigo-200/60 dark:from-indigo-950 dark:to-violet-950 dark:text-indigo-200 dark:ring-indigo-900">
          {initials.toUpperCase()}<span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500 dark:border-slate-950" />
        </span>
        <span className="hidden text-start xl:block"><span className="block max-w-32 truncate text-xs font-bold text-slate-800 dark:text-slate-100">{user?.first_name} {user?.last_name}</span><span className="mt-0.5 block max-w-32 truncate text-[10px] text-slate-400" data-bidi="ltr">{user?.email}</span></span>
        <svg aria-hidden="true" className="hidden h-3.5 w-3.5 text-slate-400 transition group-hover:text-slate-600 xl:block dark:group-hover:text-slate-300" fill="none" viewBox="0 0 20 20"><path d="m6 8 4 4 4-4" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" /></svg>
      </button>
      {isOpen ? (
        <div className={`crm-popover-enter absolute mt-2 w-64 overflow-hidden rounded-2xl border border-slate-200/80 bg-white/96 p-1.5 shadow-[0_22px_55px_rgba(15,23,42,.18)] backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/96 ${isRtl ? "left-0" : "right-0"}`} id={menuId} role="menu">
          <div className="rounded-xl bg-slate-50 px-3 py-3 dark:bg-slate-900/70"><p className="text-sm font-bold text-slate-900 dark:text-white">{user?.first_name} {user?.last_name}</p><p className="mt-1 truncate text-[11px] text-slate-500" data-bidi="ltr">{user?.email}</p></div>
          <div className="mt-1">
            <Link className="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-indigo-50 hover:text-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:text-slate-200 dark:hover:bg-indigo-950/40 dark:hover:text-indigo-200" href="/dashboard/settings/profile" onClick={() => setIsOpen(false)} role="menuitem"><svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.7"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7"/></svg>{t("Profile settings")}</Link>
            <button className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-start text-sm font-medium text-rose-600 transition hover:bg-rose-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 disabled:cursor-not-allowed disabled:opacity-60 dark:text-rose-300 dark:hover:bg-rose-950/35" disabled={isSigningOut} onClick={() => void handleSignOut()} role="menuitem" type="button"><svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24"><path d="M10 5H6.5A2.5 2.5 0 0 0 4 7.5v9A2.5 2.5 0 0 0 6.5 19H10M14 8l4 4-4 4M9 12h9" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7"/></svg>{isSigningOut ? t("Signing out…") : t("Sign out")}</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
