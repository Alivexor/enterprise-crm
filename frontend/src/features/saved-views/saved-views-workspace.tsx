"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { V3Empty, V3Hero, V3Metric, V3Section } from "@/features/v3/v3-ui";
import { ApiError } from "@/services/api-client";
import { v3Service } from "@/services/v3-service";
import type { SavedView } from "@/types/v3";

const resources = ["companies", "contacts", "leads", "deals", "tasks", "activities"] as const;
const sampleFilters: Record<string, Record<string, unknown>> = {
  companies: { industry: "Technology" },
  contacts: {},
  leads: { status: "qualified" },
  deals: { status: "open" },
  tasks: { status: "open", priority: "high" },
  activities: { type: "meeting" },
};
function message(error: unknown) { return error instanceof ApiError ? error.message : "Unable to update saved views."; }
function viewHref(item: SavedView): string {
  const params = new URLSearchParams();
  Object.entries(item.filters).forEach(([key, value]) => { if (["string", "number", "boolean"].includes(typeof value)) params.set(key, String(value)); });
  if (item.sort_by) params.set("sort_by", item.sort_by);
  if (item.sort_direction) params.set("sort_direction", item.sort_direction);
  const query = params.toString();
  return `/dashboard/${item.resource}${query ? `?${query}` : ""}`;
}

export function SavedViewsWorkspace() {
  const { formatDateTime, formatNumber, t } = useI18n();
  const { notify } = useToast();
  const [items, setItems] = useState<SavedView[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [resource, setResource] = useState<(typeof resources)[number]>("deals");
  const [filtersText, setFiltersText] = useState(JSON.stringify(sampleFilters.deals, null, 2));
  const [sortBy, setSortBy] = useState("updated_at");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [shared, setShared] = useState(false);

  const load = useCallback(async () => { setLoading(true); try { setItems(await v3Service.savedViews.list()); } catch (cause) { notify({ tone: "error", title: t("Unable to load saved views"), description: t(message(cause)) }); } finally { setLoading(false); } }, [notify, t]);
  useEffect(() => { void Promise.resolve().then(load); }, [load]);

  const sharedCount = useMemo(() => items.filter((item) => item.is_shared).length, [items]);
  const resourceCount = new Set(items.map((item) => item.resource)).size;

  async function create(event: FormEvent) {
    event.preventDefault();
    let filters: Record<string, unknown>;
    try { filters = filtersText.trim() ? JSON.parse(filtersText) : {}; if (!filters || Array.isArray(filters) || typeof filters !== "object") throw new Error(); }
    catch { notify({ tone: "warning", title: t("Filters must be valid JSON") }); return; }
    setSaving(true);
    try {
      await v3Service.savedViews.create({ name: name.trim(), resource, filters, sort_by: sortBy.trim() || null, sort_direction: sortDirection, is_shared: shared });
      notify({ tone: "success", title: t("Saved view created") }); setName(""); await load();
    } catch (cause) { notify({ tone: "error", title: t("Unable to create saved view"), description: t(message(cause)) }); }
    finally { setSaving(false); }
  }
  async function remove(item: SavedView) { if (!window.confirm(t("Delete this saved view?"))) return; try { await v3Service.savedViews.remove(item.id); await load(); } catch (cause) { notify({ tone: "error", title: t("Unable to delete saved view"), description: t(message(cause)) }); } }

  return <section className="crm-page mx-auto max-w-[1450px] space-y-6">
    <V3Hero accent="indigo" eyebrow="V3 Productivity" title="Saved views" description="Save repeatable CRM filters and sort rules, share useful operating views with the workspace, and reopen them in one click." />
    <div className="grid gap-4 sm:grid-cols-3"><V3Metric label="Saved views" value={formatNumber(items.length)} /><V3Metric label="Shared views" value={formatNumber(sharedCount)} tone="cyan" /><V3Metric label="Covered resources" value={formatNumber(resourceCount)} tone="emerald" /></div>
    <div className="grid gap-6 xl:grid-cols-[1.15fr_.85fr]">
      <V3Section title="View library" description="Open a saved view to apply its supported filters directly to the matching CRM workspace.">
        {loading ? <V3Empty><T>Loading saved views…</T></V3Empty> : !items.length ? <V3Empty><T>No saved views yet.</T></V3Empty> : <div className="grid gap-3 md:grid-cols-2">{items.map((item) => <article className="rounded-2xl border border-slate-200/75 bg-slate-50/55 p-4 dark:border-slate-800 dark:bg-slate-900/45" key={item.id}><div className="flex items-start justify-between gap-3"><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-black text-slate-950 dark:text-white">{item.name}</h3>{item.is_shared ? <span className="rounded-lg bg-cyan-50 px-2 py-1 text-[10px] font-black text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300"><T>Shared</T></span> : null}</div><p className="mt-1 text-xs text-slate-500"><T>{item.resource}</T> · {item.sort_by || t("Default sort")} · {item.sort_direction}</p></div><span className="rounded-lg bg-white px-2 py-1 text-[10px] font-bold text-slate-500 ring-1 ring-slate-200 dark:bg-slate-950 dark:ring-slate-800">{formatNumber(Object.keys(item.filters).length)} <T>filters</T></span></div><pre className="mt-3 max-h-24 overflow-auto rounded-xl bg-slate-950 px-3 py-2 text-[10px] leading-5 text-slate-300" dir="ltr">{JSON.stringify(item.filters, null, 2)}</pre><div className="mt-3 flex items-center justify-between gap-3"><span className="text-[10px] text-slate-400">{formatDateTime(item.updated_at)}</span><div className="flex gap-2"><Link className="inline-flex min-h-9 items-center rounded-xl bg-indigo-600 px-3 text-xs font-bold text-white hover:bg-indigo-500" href={viewHref(item)}><T>Open view</T></Link><Button onClick={() => void remove(item)} size="sm" variant="tertiary">{t("Delete")}</Button></div></div></article>)}</div>}
      </V3Section>
      <V3Section title="Create saved view" description="Define a reusable filter object. Only simple URL-compatible filters are applied when opening the view.">
        <form className="space-y-4" onSubmit={create}><label className="block text-sm font-bold text-slate-700 dark:text-slate-200"><T>Name</T><input className="crm-input mt-2 w-full" maxLength={120} onChange={(e) => setName(e.target.value)} required value={name} /></label><label className="block text-sm font-bold text-slate-700 dark:text-slate-200"><T>Resource</T><select className="crm-select mt-2 w-full" onChange={(e) => { const next = e.target.value as (typeof resources)[number]; setResource(next); setFiltersText(JSON.stringify(sampleFilters[next], null, 2)); }} value={resource}>{resources.map((item) => <option key={item} value={item}>{t(item)}</option>)}</select></label><label className="block text-sm font-bold text-slate-700 dark:text-slate-200"><T>Filters JSON</T><textarea className="crm-input mt-2 min-h-32 w-full font-mono text-xs" dir="ltr" onChange={(e) => setFiltersText(e.target.value)} value={filtersText} /></label><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-bold text-slate-700 dark:text-slate-200"><T>Sort field</T><input className="crm-input mt-2 w-full" onChange={(e) => setSortBy(e.target.value)} value={sortBy} /></label><label className="text-sm font-bold text-slate-700 dark:text-slate-200"><T>Direction</T><select className="crm-select mt-2 w-full" onChange={(e) => setSortDirection(e.target.value as "asc" | "desc")} value={sortDirection}><option value="desc">{t("Descending")}</option><option value="asc">{t("Ascending")}</option></select></label></div><label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300"><input checked={shared} onChange={(e) => setShared(e.target.checked)} type="checkbox" /><T>Share with workspace</T></label><Button className="w-full" disabled={saving || !name.trim()} type="submit">{saving ? t("Saving…") : t("Save view")}</Button></form>
      </V3Section>
    </div>
  </section>;
}
