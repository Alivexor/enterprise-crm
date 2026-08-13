"use client";

import Link from "next/link";
import { useI18n } from "@/components/i18n/i18n-provider";
import { usePathname } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/utils/cn";

type SettingsLink = {
  description: string;
  href: string;
  label: string;
  permissions: string[];
};

const settingsLinks: SettingsLink[] = [
  { description: "Language, direction, number/date format and theme", href: "/dashboard/settings/preferences", label: "Language & appearance", permissions: ["profile.read"] },
  { description: "Your personal details and password", href: "/dashboard/settings/profile", label: "Profile", permissions: ["profile.read"] },
  { description: "MFA, recovery codes and account protection", href: "/dashboard/settings/security", label: "Security", permissions: ["profile.read"] },
  { description: "Workspace name and organization details", href: "/dashboard/settings/organization", label: "Organization", permissions: ["organizations.read"] },
  { description: "Invite and manage workspace members", href: "/dashboard/settings/users", label: "Users", permissions: ["users.read"] },
  { description: "Roles and permission assignments", href: "/dashboard/settings/roles", label: "Roles & permissions", permissions: ["roles.read", "permissions.read"] },
  { description: "Security-relevant workspace activity", href: "/dashboard/settings/audit-logs", label: "Audit log", permissions: ["audit_logs.read"] },
  { description: "Extend CRM records with workspace-defined data fields", href: "/dashboard/settings/custom-fields", label: "Custom fields", permissions: ["custom_fields.read"] },
  { description: "Personalize the main dashboard with live CRM widgets", href: "/dashboard/settings/dashboard", label: "Dashboard studio", permissions: ["dashboards.read"] },
  { description: "API keys, webhooks and local integration controls", href: "/dashboard/settings/developer", label: "Developer platform", permissions: ["developer.read"] },
  { description: "Move supported CRM data with CSV files", href: "/dashboard/import-export", label: "Import & export", permissions: ["imports.create", "exports.create"] },
];

export function SettingsNavigation({ compact = false }: { compact?: boolean }) {
  const { t } = useI18n();
  const pathname = usePathname();
  const { user } = useAuth();
  const permissionNames = new Set(user?.permissions.map((permission) => permission.name) ?? []);
  const visibleLinks = settingsLinks.filter((link) => link.permissions.some((permission) => permissionNames.has(permission)));

  return (
    <nav aria-label={t("Settings navigation")} className={compact ? "flex flex-wrap gap-2" : "grid gap-3 sm:grid-cols-2"}>
      {visibleLinks.map((link) => {
        const isActive = pathname === link.href;
        return (
          <Link
            aria-current={isActive ? "page" : undefined}
            className={cn(
              compact
                ? "rounded-xl px-3 py-2 text-sm font-semibold"
                : "group rounded-2xl border p-4 transition-[color,background-color,border-color,box-shadow,transform] duration-200 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500",
              isActive
                ? "border-indigo-200 bg-gradient-to-br from-indigo-50 to-violet-50 text-indigo-800 shadow-sm dark:border-indigo-900 dark:from-indigo-950/55 dark:to-violet-950/25 dark:text-indigo-100"
                : "border-slate-200/80 bg-white/80 text-slate-800 shadow-sm hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-white hover:shadow-md dark:border-slate-800 dark:bg-slate-950/80 dark:text-slate-100 dark:hover:border-indigo-900 dark:hover:bg-slate-900",
            )}
            href={link.href}
            key={link.href}
          >
            <span className="block text-sm font-semibold">{t(link.label)}</span>
            {!compact ? <span className="mt-1 block text-sm font-normal leading-5 text-slate-500">{t(link.description)}</span> : null}
          </Link>
        );
      })}
    </nav>
  );
}
