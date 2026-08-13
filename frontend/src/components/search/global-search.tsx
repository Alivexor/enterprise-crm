"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/components/i18n/i18n-provider";

export function GlobalSearch() {
  const router = useRouter();
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  function handleSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const normalizedQuery = query.trim(); if (normalizedQuery) router.push(`/dashboard/search?q=${encodeURIComponent(normalizedQuery)}`); }
  return (
    <form className="relative hidden md:block" onSubmit={handleSubmit} role="search">
      <label className="sr-only" htmlFor="global-search">{t("Search the CRM")}</label>
      <svg aria-hidden="true" className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="5.5" stroke="currentColor" strokeWidth="1.7"/><path d="m15 15 4.5 4.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7"/></svg>
      <input className="crm-input h-10 w-40 pe-3 ps-9 text-xs font-medium placeholder:text-slate-400 lg:w-44 xl:w-56" id="global-search" maxLength={255} onChange={(event) => setQuery(event.target.value)} placeholder={t("Search CRM")} type="search" value={query} />
    </form>
  );
}
