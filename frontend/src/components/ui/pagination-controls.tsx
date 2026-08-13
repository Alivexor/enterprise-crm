"use client";

import { useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import type { PageMetadata } from "@/types/pagination";

type PaginationControlsProps = { isLoading?: boolean; meta: PageMetadata; onPageChange: (page: number) => void };
export function PaginationControls({ isLoading = false, meta, onPageChange }: PaginationControlsProps) {
  const { formatNumber, locale, t } = useI18n();
  const totalPages = Math.max(1, Math.ceil(meta.total / meta.page_size));
  const canGoBack = meta.page > 1; const canGoForward = meta.page < totalPages;
  if (meta.total === 0) return null;
  return (
    <nav aria-label={t("Pagination")} className="mt-5 flex flex-col gap-3 rounded-2xl border border-slate-200/70 bg-white/90 px-3 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between dark:border-slate-800 dark:bg-slate-950/90">
      <p className="px-1 text-xs font-medium text-slate-500">{locale === "fa" ? <>صفحه {formatNumber(meta.page)} از {formatNumber(totalPages)} <span className="hidden sm:inline">· مجموع {formatNumber(meta.total)}</span></> : <>Page {formatNumber(meta.page)} of {formatNumber(totalPages)} <span className="hidden sm:inline">· {formatNumber(meta.total)} total</span></>}</p>
      <div className="flex gap-2"><Button disabled={!canGoBack || isLoading} onClick={() => onPageChange(meta.page - 1)} size="sm" variant="secondary"><svg aria-hidden="true" className="h-3.5 w-3.5 rtl:rotate-180" fill="none" viewBox="0 0 20 20"><path d="m12 5-5 5 5 5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7"/></svg>{t("Previous")}</Button><Button disabled={!canGoForward || isLoading} onClick={() => onPageChange(meta.page + 1)} size="sm" variant="secondary">{t("Next")}<svg aria-hidden="true" className="h-3.5 w-3.5 rtl:rotate-180" fill="none" viewBox="0 0 20 20"><path d="m8 5 5 5-5 5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7"/></svg></Button></div>
    </nav>
  );
}
