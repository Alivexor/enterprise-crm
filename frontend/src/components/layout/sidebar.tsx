"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useI18n } from "@/components/i18n/i18n-provider";
import { NavigationIcon, type NavigationIconName } from "@/components/layout/navigation-icon";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/utils/cn";

type SidebarProps = { isOpen: boolean; onClose: () => void };
type NavigationItem = { exact?: boolean; href: string; icon: NavigationIconName; label: string; permissions?: string[]; requireAllPermissions?: boolean };
type NavigationGroup = { label: string; items: NavigationItem[] };

const navigationGroups: NavigationGroup[] = [
  { label: "Workspace", items: [
    { href: "/dashboard", icon: "dashboard", label: "Dashboard", permissions: ["dashboard.read"] },
    { href: "/dashboard/notifications", icon: "inbox", label: "Inbox", permissions: ["notifications.read"] },
    { href: "/dashboard/search", icon: "search", label: "Search", permissions: ["search.read"] },
  ]},
  { label: "Customers", items: [
    { href: "/dashboard/companies", icon: "building", label: "Companies", permissions: ["companies.read"] },
    { href: "/dashboard/contacts", icon: "people", label: "Contacts", permissions: ["contacts.read"] },
    { href: "/dashboard/leads", icon: "lead", label: "Leads", permissions: ["leads.read"] },
  ]},
  { label: "Sales", items: [
    { href: "/dashboard/pipelines", icon: "pipeline", label: "Pipelines", permissions: ["pipelines.read"] },
    { exact: true, href: "/dashboard/deals", icon: "deal", label: "Deals", permissions: ["deals.read"] },
    { href: "/dashboard/deals/board", icon: "pipeline", label: "Sales board", permissions: ["deals.read", "pipelines.read"], requireAllPermissions: true },
  ]},
  { label: "Intelligence", items: [
    { href: "/dashboard/intelligence", icon: "dashboard", label: "Intelligence center", permissions: ["reports.read", "data_quality.read", "ai.use"] },
    { href: "/dashboard/automation", icon: "activity", label: "Workflow studio", permissions: ["automations.read"] },
    { href: "/dashboard/revenue", icon: "deal", label: "Revenue studio", permissions: ["reports.read", "goals.read", "products.read", "quotes.read"] },
    { href: "/dashboard/sequences", icon: "activity", label: "Sales sequences", permissions: ["sequences.read"] },
    { href: "/dashboard/views", icon: "database", label: "Saved views", permissions: ["saved_views.read"] },
  ]},
  { label: "Work", items: [
    { href: "/dashboard/planner", icon: "planner", label: "Planner", permissions: ["tasks.read", "activities.read"] },
    { href: "/dashboard/tasks", icon: "task", label: "Tasks", permissions: ["tasks.read"] },
    { href: "/dashboard/activities", icon: "activity", label: "Activities", permissions: ["activities.read"] },
    { href: "/dashboard/notes", icon: "note", label: "Notes", permissions: ["notes.read"] },
    { href: "/dashboard/tags", icon: "tag", label: "Tags", permissions: ["tags.read"] },
  ]},
  { label: "Manage", items: [
    { href: "/dashboard/import-export", icon: "database", label: "Import & export", permissions: ["imports.create", "exports.create"] },
    { href: "/dashboard/settings", icon: "settings", label: "Settings", permissions: ["settings.read", "profile.read", "organizations.read", "users.read", "roles.read", "audit_logs.read"] },
  ]},
];

function isActivePath(pathname: string, item: NavigationItem): boolean {
  if (item.exact || item.href === "/dashboard") return pathname === item.href;
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}
function canAccess(item: NavigationItem, permissionNames: Set<string>): boolean {
  if (!item.permissions?.length) return true;
  return item.requireAllPermissions ? item.permissions.every((permission) => permissionNames.has(permission)) : item.permissions.some((permission) => permissionNames.has(permission));
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { isRtl, t } = useI18n();
  const { user } = useAuth();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const permissionNames = new Set(user?.permissions.map((permission) => permission.name) ?? []);

  useEffect(() => {
    if (!isOpen) return;
    previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const originalOverflow = document.body.style.overflow;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); onClose(); return; }
      if (event.key !== "Tab" || !sidebarRef.current) return;
      const focusable = Array.from(sidebarRef.current.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'));
      if (!focusable.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);
    requestAnimationFrame(() => closeButtonRef.current?.focus());
    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener("keydown", onKeyDown);
      requestAnimationFrame(() => previousFocusRef.current?.focus());
    };
  }, [isOpen, onClose]);

  return (
    <>
      {isOpen ? <div aria-hidden="true" className="fixed inset-0 z-30 bg-slate-950/60 backdrop-blur-sm lg:hidden" onClick={onClose} /> : null}
      <aside
        aria-label={t("Primary navigation")}
        ref={sidebarRef}
        className={cn(
          "fixed inset-y-0 z-40 flex w-[17.5rem] flex-col overflow-hidden bg-[#0b1020] px-3.5 py-4 text-white shadow-2xl shadow-slate-950/30 transition-transform duration-300 lg:static lg:translate-x-0 lg:shadow-none",
          isRtl ? "right-0 border-l border-white/[.06]" : "left-0 border-r border-white/[.06]",
          isOpen ? "translate-x-0" : isRtl ? "translate-x-full" : "-translate-x-full",
        )}
      >
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_40%_-10%,rgba(99,102,241,.28),transparent_18rem),radial-gradient(circle_at_100%_80%,rgba(6,182,212,.10),transparent_18rem)]" />
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 opacity-[.055] [background-image:linear-gradient(rgba(255,255,255,.6)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.6)_1px,transparent_1px)] [background-size:32px_32px]" />

        <div className="relative flex items-center justify-between gap-3 px-2 pb-3">
          <Link className="group flex min-w-0 items-center gap-3 rounded-2xl focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/30" href="/dashboard" onClick={onClose}>
            <span className="relative flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-[13px] bg-gradient-to-br from-indigo-400 via-indigo-500 to-violet-700 text-sm font-black text-white shadow-[0_10px_28px_rgba(79,70,229,.38)] ring-1 ring-inset ring-white/20">
              E<span className="absolute inset-x-1 top-0 h-px bg-white/60" />
            </span>
            <span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.02em] text-white">{t("Enterprise CRM")}</span><span className="mt-0.5 block text-[11px] font-medium text-slate-400">{t("Revenue workspace")}</span></span>
          </Link>
          <Button aria-label={t("Close navigation")} className="text-slate-300 hover:bg-white/10 hover:text-white lg:hidden" onClick={onClose} ref={closeButtonRef} size="icon" variant="tertiary">
            <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeLinecap="round" strokeWidth="2" /></svg>
          </Button>
        </div>

        <div className="relative mx-2 mt-2 flex items-center gap-2 rounded-xl border border-white/[.07] bg-white/[.045] px-3 py-2 text-[11px] text-slate-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,.8)]" />
          <span>{t("Workspace online")}</span><span className="ms-auto font-mono text-[9px] text-slate-500">v3.0</span>
        </div>

        <nav aria-label={t("Primary navigation")} className="crm-scroll-mask relative mt-5 flex-1 space-y-5 overflow-y-auto pe-1" id="primary-navigation">
          {navigationGroups.map((group) => {
            const visibleItems = group.items.filter((item) => canAccess(item, permissionNames));
            if (!visibleItems.length) return null;
            return (
              <section key={group.label}>
                <p className="mb-1.5 px-3 text-[9px] font-bold uppercase tracking-[.18em] text-slate-500">{t(group.label)}</p>
                <div className="space-y-1">
                  {visibleItems.map((item) => {
                    const active = isActivePath(pathname, item);
                    return (
                      <Link
                        aria-current={active ? "page" : undefined}
                        className={cn(
                          "group relative flex items-center gap-3 overflow-hidden rounded-xl px-3 py-2.5 text-[13px] font-semibold transition-[color,background-color,border-color,box-shadow,transform] duration-200 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/25",
                          active ? "bg-white/[.10] text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,.07),0_7px_22px_rgba(0,0,0,.12)]" : "text-slate-400 hover:bg-white/[.055] hover:text-slate-100",
                        )}
                        href={item.href}
                        key={item.label}
                        onClick={onClose}
                      >
                        {active ? <span aria-hidden="true" className={`absolute inset-y-2 w-[3px] rounded-full bg-gradient-to-b from-indigo-400 to-cyan-400 ${isRtl ? "right-0" : "left-0"}`} /> : null}
                        <span className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition", active ? "bg-indigo-500/15 text-indigo-300" : "text-slate-500 group-hover:bg-white/[.05] group-hover:text-slate-300")}><NavigationIcon className="h-[17px] w-[17px]" name={item.icon} /></span>
                        <span>{t(item.label)}</span>
                      </Link>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </nav>

        <div className="relative mt-3 rounded-2xl border border-white/[.07] bg-white/[.045] p-3">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-800 text-[11px] font-bold text-white ring-1 ring-inset ring-white/10">{`${user?.first_name?.[0] ?? ""}${user?.last_name?.[0] ?? ""}`.toUpperCase() || "U"}</span>
            <span className="min-w-0"><span className="block truncate text-xs font-semibold text-slate-200">{user?.first_name} {user?.last_name}</span><span className="mt-0.5 block truncate text-[10px] text-slate-500" data-bidi="ltr">{user?.email}</span></span>
          </div>
        </div>
      </aside>
    </>
  );
}
