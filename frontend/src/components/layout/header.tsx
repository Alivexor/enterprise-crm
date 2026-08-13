"use client";

import { usePathname } from "next/navigation";

import { LanguageToggle } from "@/components/i18n/language-toggle";
import { useI18n } from "@/components/i18n/i18n-provider";
import { UserMenu } from "@/components/layout/user-menu";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { QuickCreateMenu } from "@/components/layout/quick-create-menu";
import { GlobalSearch } from "@/components/search/global-search";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";

type HeaderProps = { onCommandClick: () => void; onMenuClick: () => void };

const pageTitles: Array<{ prefix: string; title: string; eyebrow: string }> = [
  { prefix: "/dashboard/companies", title: "Companies", eyebrow: "Customers" },
  { prefix: "/dashboard/contacts", title: "Contacts", eyebrow: "Customers" },
  { prefix: "/dashboard/leads", title: "Leads", eyebrow: "Customers" },
  { prefix: "/dashboard/pipelines", title: "Pipelines", eyebrow: "Sales" },
  { prefix: "/dashboard/deals/board", title: "Sales board", eyebrow: "Sales" },
  { prefix: "/dashboard/deals", title: "Deals", eyebrow: "Sales" },
  { prefix: "/dashboard/planner", title: "Planner", eyebrow: "Work" },
  { prefix: "/dashboard/tasks", title: "Tasks", eyebrow: "Work" },
  { prefix: "/dashboard/activities", title: "Activities", eyebrow: "Work" },
  { prefix: "/dashboard/notes", title: "Notes", eyebrow: "Work" },
  { prefix: "/dashboard/tags", title: "Tags", eyebrow: "Work" },
  { prefix: "/dashboard/search", title: "Search", eyebrow: "Workspace" },
  { prefix: "/dashboard/notifications", title: "Inbox", eyebrow: "Workspace" },
  { prefix: "/dashboard/import-export", title: "Import & export", eyebrow: "Manage" },
  { prefix: "/dashboard/settings", title: "Settings", eyebrow: "Manage" },
];

function getPageMeta(pathname: string) {
  return pageTitles.find((item) => pathname.startsWith(item.prefix)) ?? { title: "Dashboard", eyebrow: "Workspace" };
}

export function Header({ onCommandClick, onMenuClick }: HeaderProps) {
  const pathname = usePathname();
  const { t } = useI18n();
  const meta = getPageMeta(pathname);

  return (
    <header
      aria-label={t("Workspace header")}
      className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/78 px-4 backdrop-blur-2xl supports-[backdrop-filter]:bg-white/72 dark:border-slate-800/80 dark:bg-slate-950/72 sm:px-6 xl:px-8"
    >
      <div className="flex h-[68px] items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <Button aria-controls="primary-navigation" aria-label={t("Open navigation")} className="lg:hidden" onClick={onMenuClick} size="icon" type="button" variant="tertiary">
            <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" /></svg>
          </Button>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="hidden h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,.10)] sm:block" />
              <p className="hidden truncate text-[10px] font-bold uppercase tracking-[.14em] text-slate-400 sm:block">{t(meta.eyebrow)}</p>
            </div>
            <p className="truncate text-[15px] font-bold tracking-[-.02em] text-slate-950 dark:text-white sm:mt-0.5">{t(meta.title)}</p>
          </div>
        </div>

        <div className="flex items-center gap-1 sm:gap-1.5">
          <Button aria-label={t("Open command palette")} className="group hidden gap-2 border border-slate-200/70 bg-slate-50/80 px-3 shadow-none hover:border-indigo-200 hover:bg-white lg:inline-flex dark:border-slate-800 dark:bg-slate-900/70 dark:hover:border-indigo-900 dark:hover:bg-slate-900" onClick={onCommandClick} size="sm" type="button" variant="tertiary">
            <svg aria-hidden="true" className="h-4 w-4 text-slate-400 transition group-hover:text-indigo-500" fill="none" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="5.5" stroke="currentColor" strokeWidth="1.8" /><path d="m15 15 4.5 4.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" /></svg>
            <span className="hidden xl:inline">{t("Quick command")}</span>
            <kbd className="rounded-md border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 shadow-sm dark:border-slate-700 dark:bg-slate-950">Ctrl/⌘K</kbd>
          </Button>
          <QuickCreateMenu />
          <GlobalSearch />
          <NotificationBell />
          <LanguageToggle compact />
          <ThemeToggle />
          <div className="mx-1 hidden h-7 w-px bg-slate-200/80 dark:bg-slate-800 sm:block" />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
