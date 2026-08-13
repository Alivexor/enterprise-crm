"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { useI18n } from "@/components/i18n/i18n-provider";
import { LocalizedEnum } from "@/components/i18n/localized-value";
import { NavigationIcon, type NavigationIconName } from "@/components/layout/navigation-icon";
import { useAuth } from "@/hooks/use-auth";
import { searchService } from "@/services/search-service";
import type { SearchResult } from "@/types/search";
import { searchResultPath } from "@/utils/search-result-path";

type CommandPaletteProps = { onClose: () => void };

type StaticCommand = {
  href: string;
  icon: NavigationIconName;
  label: string;
  permissions?: string[];
  requireAll?: boolean;
};

type PaletteItem =
  | { command: StaticCommand; key: string; kind: "command" }
  | { key: string; kind: "result"; result: SearchResult };

const commands: StaticCommand[] = [
  { href: "/dashboard", icon: "dashboard", label: "Dashboard", permissions: ["dashboard.read"] },
  { href: "/dashboard/planner", icon: "planner", label: "Planner", permissions: ["tasks.read", "activities.read"] },
  { href: "/dashboard/companies", icon: "building", label: "Companies", permissions: ["companies.read"] },
  { href: "/dashboard/contacts", icon: "people", label: "Contacts", permissions: ["contacts.read"] },
  { href: "/dashboard/leads", icon: "lead", label: "Leads", permissions: ["leads.read"] },
  { href: "/dashboard/deals/board", icon: "pipeline", label: "Sales board", permissions: ["deals.read", "pipelines.read"], requireAll: true },
  { href: "/dashboard/deals", icon: "deal", label: "Deals", permissions: ["deals.read"] },
  { href: "/dashboard/tasks", icon: "task", label: "Tasks", permissions: ["tasks.read"] },
  { href: "/dashboard/activities", icon: "activity", label: "Activities", permissions: ["activities.read"] },
  { href: "/dashboard/notes", icon: "note", label: "Notes", permissions: ["notes.read"] },
  { href: "/dashboard/notifications", icon: "inbox", label: "Inbox", permissions: ["notifications.read"] },
  { href: "/dashboard/settings", icon: "settings", label: "Settings", permissions: ["settings.read", "profile.read", "users.read", "roles.read", "organizations.read"] },
  { href: "/dashboard/companies?create=1", icon: "building", label: "Create company", permissions: ["companies.create"] },
  { href: "/dashboard/contacts?create=1", icon: "people", label: "Create contact", permissions: ["contacts.create"] },
  { href: "/dashboard/leads?create=1", icon: "lead", label: "Create lead", permissions: ["leads.create"] },
  { href: "/dashboard/deals?create=1", icon: "deal", label: "Create deal", permissions: ["deals.create"] },
  { href: "/dashboard/tasks?create=1", icon: "task", label: "Create task", permissions: ["tasks.create"] },
  { href: "/dashboard/activities?create=1", icon: "activity", label: "Create activity", permissions: ["activities.create"] },
];

function hasAccess(command: StaticCommand, permissionNames: Set<string>): boolean {
  if (!command.permissions || command.permissions.length === 0) return true;
  return command.requireAll
    ? command.permissions.every((permission) => permissionNames.has(permission))
    : command.permissions.some((permission) => permissionNames.has(permission));
}

export function CommandPalette({ onClose }: CommandPaletteProps) {
  const router = useRouter();
  const { t } = useI18n();
  const { user } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const permissionNames = useMemo(
    () => new Set(user?.permissions.map((permission) => permission.name) ?? []),
    [user],
  );

  const normalizedQuery = query.trim();
  const canSearchCrm = normalizedQuery.length >= 2 && permissionNames.has("search.read");

  const visibleCommands = useMemo(() => {
    const normalized = normalizedQuery.toLocaleLowerCase();
    return commands.filter((command) => {
      if (!hasAccess(command, permissionNames)) return false;
      if (!normalized) return true;
      return t(command.label).toLocaleLowerCase().includes(normalized) || command.label.toLocaleLowerCase().includes(normalized);
    });
  }, [normalizedQuery, permissionNames, t]);

  useEffect(() => {
    previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const focusFrame = requestAnimationFrame(() => inputRef.current?.focus());

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      )).filter((element) => !element.hasAttribute("aria-hidden"));
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      cancelAnimationFrame(focusFrame);
      document.removeEventListener("keydown", onKeyDown);
      requestAnimationFrame(() => previousFocusRef.current?.focus());
    };
  }, [onClose]);

  useEffect(() => {
    if (!canSearchCrm) return;
    let active = true;
    const timer = window.setTimeout(() => {
      searchService.search(normalizedQuery)
        .then((response) => {
          if (active) setResults(response.items.slice(0, 12));
        })
        .catch(() => {
          if (active) setResults([]);
        })
        .finally(() => {
          if (active) setIsSearching(false);
        });
    }, 180);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [canSearchCrm, normalizedQuery]);

  const visibleResults = canSearchCrm ? results : [];
  const items: PaletteItem[] = [
    ...visibleCommands.map((command) => ({ command, key: `command-${command.href}`, kind: "command" as const })),
    ...visibleResults.map((result) => ({ key: `result-${result.entity_type}-${result.id}`, kind: "result" as const, result })),
  ];
  const selectedIndex = Math.min(activeIndex, Math.max(items.length - 1, 0));

  function navigate(item: PaletteItem) {
    const href = item.kind === "command" ? item.command.href : searchResultPath(item.result);
    onClose();
    router.push(href);
  }

  return (
    <div aria-label={t("Command palette")} aria-modal="true" className="crm-overlay-enter fixed inset-0 z-[70] flex items-start justify-center bg-slate-950/65 px-4 pt-[9vh] backdrop-blur-md" onMouseDown={(event) => { if (event.currentTarget === event.target) onClose(); }} role="dialog">
      <div className="crm-dialog-enter w-full max-w-2xl overflow-hidden rounded-[22px] border border-white/20 bg-white/96 shadow-[0_28px_90px_rgba(2,6,23,.34)] ring-1 ring-black/[.03] backdrop-blur-2xl dark:border-slate-700/80 dark:bg-slate-950/96 dark:ring-white/[.03]" ref={dialogRef}>
        <div className="flex items-center gap-3 border-b border-slate-200/80 px-5 dark:border-slate-800">
          <svg aria-hidden="true" className="h-5 w-5 shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="5.5" stroke="currentColor" strokeWidth="1.8" /><path d="m15 15 4.5 4.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" /></svg>
          <input
            aria-label={t("Search commands and CRM")}
            className="h-16 min-w-0 flex-1 border-0 bg-transparent text-[15px] font-medium text-slate-950 outline-none placeholder:text-slate-400 dark:text-white"
            onChange={(event) => {
              const nextQuery = event.target.value;
              setQuery(nextQuery);
              setResults([]);
              setActiveIndex(0);
              setIsSearching(nextQuery.trim().length >= 2 && permissionNames.has("search.read"));
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") { event.preventDefault(); onClose(); }
              else if (event.key === "ArrowDown") { event.preventDefault(); setActiveIndex((index) => Math.min(index + 1, Math.max(items.length - 1, 0))); }
              else if (event.key === "ArrowUp") { event.preventDefault(); setActiveIndex((index) => Math.max(index - 1, 0)); }
              else if (event.key === "Enter" && items[selectedIndex]) { event.preventDefault(); navigate(items[selectedIndex]); }
            }}
            placeholder={t("Search pages, customers, deals and work...")}
            ref={inputRef}
            value={query}
          />
          <kbd className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-semibold text-slate-500 dark:border-slate-700 dark:bg-slate-900">ESC</kbd>
        </div>

        <div className="crm-scroll-mask max-h-[62vh] overflow-y-auto p-2.5">
          {visibleCommands.length > 0 ? <div><p className="px-3 pb-2 pt-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">{t("Navigate")}</p>{items.map((item, index) => item.kind !== "command" ? null : <button className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-start text-sm transition ${selectedIndex === index ? "bg-gradient-to-r from-indigo-50 to-violet-50 text-indigo-700 ring-1 ring-inset ring-indigo-100 dark:from-indigo-950/55 dark:to-violet-950/30 dark:text-indigo-200 dark:ring-indigo-900/60" : "text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-900"}`} key={item.key} onClick={() => navigate(item)} onMouseEnter={() => setActiveIndex(index)} type="button"><NavigationIcon className="h-[18px] w-[18px] shrink-0 text-slate-400" name={item.command.icon} /><span className="font-medium">{t(item.command.label)}</span></button>)}</div> : null}

          {visibleResults.length > 0 ? <div className={visibleCommands.length > 0 ? "mt-2 border-t border-slate-100 pt-2 dark:border-slate-800" : ""}><p className="px-3 pb-2 pt-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">{t("CRM results")}</p>{items.map((item, index) => item.kind !== "result" ? null : <button className={`flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-start transition ${selectedIndex === index ? "bg-indigo-50 dark:bg-indigo-950/55" : "hover:bg-slate-50 dark:hover:bg-slate-900"}`} key={item.key} onClick={() => navigate(item)} onMouseEnter={() => setActiveIndex(index)} type="button"><span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{item.result.title}</span>{item.result.subtitle ? <span className="mt-0.5 block truncate text-xs text-slate-500">{item.result.subtitle}</span> : null}</span><span className="shrink-0 text-[10px] font-bold uppercase tracking-wide text-indigo-500"><LocalizedEnum value={item.result.entity_type} /></span></button>)}</div> : null}

          {canSearchCrm && isSearching ? <p className="px-3 py-6 text-center text-sm text-slate-500">{t("Searching CRM...")}</p> : null}
          {(!canSearchCrm || !isSearching) && items.length === 0 ? <p className="px-3 py-8 text-center text-sm text-slate-500">{t("No matching command or CRM record.")}</p> : null}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 bg-slate-50/80 px-5 py-3 text-[11px] text-slate-500 dark:border-slate-800 dark:bg-slate-900/50"><span>{t("Use arrow keys to navigate and Enter to open.")}</span><span>{t("Shortcut")}: <kbd className="font-semibold">Ctrl/⌘ K</kbd></span></div>
      </div>
    </div>
  );
}
