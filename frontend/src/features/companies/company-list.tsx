import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import type { Company } from "@/types/company";

export function CompanyList({ companies }: { companies: Company[] }) {
  if (companies.length === 0) {
    return (
      <EmptyState
        description="Create your first company to begin building your CRM."
        title="No companies yet"
      />
    );
  }

  return (
    <div className="crm-table-shell overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="grid grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto] gap-4 border-b border-slate-200 px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase dark:border-slate-800">
        <span><T>Company</T></span>
        <span className="hidden sm:block"><T>Industry</T></span>
        <span><T>Website</T></span>
      </div>
      <ul className="divide-y divide-slate-100 dark:divide-slate-800">
        {companies.map((company) => (
          <li key={company.id}>
            <Link
              className="grid grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-slate-900/60"
              href={`/dashboard/companies/${company.id}`}
            >
              <span className="flex min-w-0 items-center gap-3">
                <RecordMark label={company.name} tone="indigo" />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{company.name}</span>
                  <span className="mt-1 block text-xs text-slate-500 sm:hidden">{company.industry ?? <T>No industry</T>}</span>
                </span>
              </span>
              <span className="hidden truncate text-sm text-slate-600 dark:text-slate-300 sm:block">
                {company.industry ?? "—"}
              </span>
              <span className="max-w-28 truncate text-end text-sm text-indigo-600 dark:text-indigo-300 sm:max-w-52">
                {company.website ?? "—"}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
