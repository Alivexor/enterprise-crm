"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import { ApiError } from "@/services/api-client";
import { searchService } from "@/services/search-service";
import type { SearchResult } from "@/types/search";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to search the CRM.";
}

function resultPath(result: SearchResult): string {
  const routeByType = {
    activity: "activities",
    company: "companies",
    contact: "contacts",
    deal: "deals",
    lead: "leads",
    note: "notes",
    task: "tasks",
  } as const;
  return `/dashboard/${routeByType[result.entity_type]}/${result.id}`;
}

function resultTone(type: SearchResult["entity_type"]): "amber" | "cyan" | "emerald" | "indigo" | "slate" | "violet" {
  const tones = { activity: "cyan", company: "indigo", contact: "slate", deal: "emerald", lead: "amber", note: "violet", task: "violet" } as const;
  return tones[type];
}

export function SearchWorkspace() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q")?.trim() ?? "";
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    let isActive = true;
    if (!query) {
      return () => { isActive = false; };
    }

    async function search() {
      setIsLoading(true);
      try {
        const response = await searchService.search(query);
        if (isActive) {
          setResults(response.items);
          setError(null);
        }
      } catch (caughtError) {
        if (isActive) setError(getErrorMessage(caughtError));
      } finally {
        if (isActive) setIsLoading(false);
      }
    }
    void search();
    return () => { isActive = false; };
  }, [query, reloadNonce]);

  return (
    <section className="crm-page mx-auto max-w-5xl">
      <p className="crm-kicker"><T>Search</T></p>
      <h1 className="crm-title mt-3"><T>CRM search</T></h1>
      {!query ? <div className="mt-8"><EmptyState description="Use the search field in the workspace header to find companies, contacts, leads, and deals." title="Search your CRM" /></div> : null}
      {query ? <p className="mt-3 text-sm text-slate-500"><T>Results for</T> <span className="font-medium text-slate-800 dark:text-slate-100">&quot;{query}&quot;</span></p> : null}
      <div className="mt-8">
        {isLoading ? <LoadingState label="Searching CRM..." /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={() => setReloadNonce((value) => value + 1)}><T>Try again</T></Button>} description={error} title="Unable to search" /> : null}
        {!isLoading && !error && query && results.length === 0 ? <EmptyState description="Try a different name, company, or email address." title="No results found" /> : null}
        {!isLoading && !error && results.length > 0 ? <ul className="crm-table-shell divide-y divide-slate-100 dark:divide-slate-800">{results.map((result) => <li key={`${result.entity_type}-${result.id}`}><Link className="flex items-start gap-3 px-5 py-4 transition hover:bg-indigo-50/35 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-indigo-950/15" href={resultPath(result)}><RecordMark label={result.title} tone={resultTone(result.entity_type)} /><span className="min-w-0 flex-1"><span className="text-[10px] font-bold tracking-[.12em] text-indigo-600 uppercase dark:text-indigo-300"><LocalizedEnum value={result.entity_type} /></span><span className="mt-1 block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{result.title}</span>{result.subtitle ? <span className="mt-1 block truncate text-sm text-slate-500">{result.subtitle}</span> : null}</span><svg aria-hidden="true" className="mt-3 h-4 w-4 shrink-0 text-slate-300 rtl:rotate-180 dark:text-slate-700" fill="none" viewBox="0 0 20 20"><path d="m7 5 5 5-5 5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" /></svg></Link></li>)}</ul> : null}
      </div>
    </section>
  );
}
