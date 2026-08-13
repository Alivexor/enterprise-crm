"use client";

import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { useAuth } from "@/hooks/use-auth";

export function SettingsWorkspace() {
  const { user } = useAuth();

  return (
    <section className="crm-page mx-auto max-w-5xl">
      <p className="crm-kicker"><T>Workspace</T></p>
      <h1 className="crm-title mt-3"><T>Settings</T></h1>
      <p className="crm-subtitle mt-3"><T>Manage your profile, workspace access, and administrative controls.</T></p>
      <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6">
        <p className="text-sm font-medium text-slate-800 dark:text-slate-100"><T>Signed in as</T></p>
        <p className="mt-1 text-sm text-slate-500">{user?.first_name} {user?.last_name} · {user?.email}</p>
        <Link className="mt-4 inline-flex text-sm font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/settings/profile"><T>Open profile settings</T></Link>
      </div>
      <div className="mt-8"><SettingsNavigation /></div>
    </section>
  );
}
