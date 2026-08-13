"use client";

import { useI18n } from "@/components/i18n/i18n-provider";
import { cn } from "@/utils/cn";

export function LanguageToggle({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale, t } = useI18n();

  return (
    <div
      aria-label={t("Language")}
      className={cn(
        "inline-flex items-center rounded-xl border border-slate-200/80 bg-slate-50/80 p-0.5 shadow-sm dark:border-slate-800 dark:bg-slate-900",
        compact ? "h-9" : "h-10",
      )}
      role="group"
    >
      <button
        aria-pressed={locale === "en"}
        className={cn(
          "rounded-[9px] px-2.5 py-1.5 text-xs font-bold transition",
          locale === "en"
            ? "bg-white text-indigo-700 shadow-sm dark:bg-slate-800 dark:text-indigo-200"
            : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white",
        )}
        onClick={() => setLocale("en")}
        type="button"
      >
        EN
      </button>
      <button
        aria-pressed={locale === "fa"}
        className={cn(
          "rounded-[9px] px-2.5 py-1.5 text-xs font-bold transition",
          locale === "fa"
            ? "bg-white text-indigo-700 shadow-sm dark:bg-slate-800 dark:text-indigo-200"
            : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white",
        )}
        onClick={() => setLocale("fa")}
        type="button"
      >
        فا
      </button>
    </div>
  );
}
