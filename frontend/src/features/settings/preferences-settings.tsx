"use client";

import { LanguageToggle } from "@/components/i18n/language-toggle";
import { T, useI18n } from "@/components/i18n/i18n-provider";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { useTheme } from "@/components/theme/theme-provider";
import { SettingsNavigation } from "@/features/settings/settings-navigation";

const PREVIEW_DATE = "2026-08-12T12:00:00.000Z";

export function PreferencesSettings() {
  const { direction, formatDateTime, formatMoney, formatNumber, locale, t } = useI18n();
  const { theme } = useTheme();

  return (
    <section className="crm-page mx-auto max-w-5xl space-y-6">
      <div>
        <p className="crm-kicker"><T>Preferences</T></p>
        <h1 className="crm-title mt-3"><T>Language & appearance</T></h1>
        <p className="crm-subtitle mt-3 max-w-2xl">
          <T>Choose how Enterprise CRM looks and reads for you.</T>
        </p>
      </div>

      <SettingsNavigation compact />

      <div className="grid gap-5 lg:grid-cols-2">
        <article className="crm-card crm-card-hover p-6">
          <div className="flex items-start justify-between gap-5">
            <div>
              <h2 className="text-base font-semibold text-slate-950 dark:text-white"><T>Interface language</T></h2>
              <p className="mt-1 text-sm leading-6 text-slate-500"><T>Switch the entire workspace between English and Persian.</T></p>
            </div>
            <LanguageToggle />
          </div>
          <dl className="mt-6 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/70">
              <dt className="text-xs font-semibold text-slate-500"><T>Current language</T></dt>
              <dd className="mt-2 text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{locale === "fa" ? "فارسی" : "English"}</dd>
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/70">
              <dt className="text-xs font-semibold text-slate-500"><T>Reading direction</T></dt>
              <dd className="mt-2 text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{direction === "rtl" ? t("Right to left") : t("Left to right")}</dd>
            </div>
          </dl>
        </article>

        <article className="crm-card crm-card-hover p-6">
          <div className="flex items-start justify-between gap-5">
            <div>
              <h2 className="text-base font-semibold text-slate-950 dark:text-white"><T>Theme</T></h2>
              <p className="mt-1 text-sm leading-6 text-slate-500"><T>Choose a light or dark workspace without changing your data.</T></p>
            </div>
            <ThemeToggle />
          </div>
          <div className="mt-6 rounded-xl bg-slate-50 p-4 dark:bg-slate-900/70">
            <p className="text-xs font-semibold text-slate-500"><T>Current theme</T></p>
            <p className="mt-2 text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{theme === "dark" ? t("Dark") : t("Light")}</p>
          </div>
        </article>
      </div>

      <article className="crm-hero overflow-hidden">
        <div className="border-b border-indigo-100 px-6 py-5 dark:border-indigo-950">
          <p className="text-sm font-semibold text-indigo-700 dark:text-indigo-300"><T>Locale preview</T></p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300"><T>Numbers, dates and money automatically follow the selected language.</T></p>
        </div>
        <dl className="grid gap-px bg-indigo-100 sm:grid-cols-3 dark:bg-indigo-950">
          <div className="bg-white p-6 dark:bg-slate-950">
            <dt className="text-xs font-semibold text-slate-500"><T>Number</T></dt>
            <dd className="mt-2 text-xl font-semibold text-slate-950 dark:text-white">{formatNumber(1250000)}</dd>
          </div>
          <div className="bg-white p-6 dark:bg-slate-950">
            <dt className="text-xs font-semibold text-slate-500"><T>Date & time</T></dt>
            <dd className="mt-2 text-sm font-semibold text-slate-950 dark:text-white">{formatDateTime(PREVIEW_DATE)}</dd>
          </div>
          <div className="bg-white p-6 dark:bg-slate-950">
            <dt className="text-xs font-semibold text-slate-500"><T>Money</T></dt>
            <dd className="mt-2 text-xl font-semibold text-slate-950 dark:text-white">{formatMoney(1250000, "USD")}</dd>
          </div>
        </dl>
      </article>

      <p className="crm-card px-5 py-4 text-sm leading-6 text-slate-600 dark:text-slate-300">
        <T>Your language and theme preferences are saved in this browser and restored automatically.</T>
      </p>
    </section>
  );
}
