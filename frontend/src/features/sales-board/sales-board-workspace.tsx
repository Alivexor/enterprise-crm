"use client";

import { LocalizedDate, LocalizedEnum, LocalizedMoney } from "@/components/i18n/localized-value";
import { T, useI18n } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuth } from "@/hooks/use-auth";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { ApiError } from "@/services/api-client";
import { dealService } from "@/services/deal-service";
import { pipelineService } from "@/services/pipeline-service";
import type { Deal } from "@/types/deal";
import type { Pipeline, PipelineDetail, PipelineStage } from "@/types/pipeline";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load the sales board.";
}

const stageAccents = [
  { bar: "from-indigo-400 to-indigo-500" },
  { bar: "from-violet-400 to-violet-500" },
  { bar: "from-cyan-400 to-cyan-500" },
  { bar: "from-emerald-400 to-emerald-500" },
  { bar: "from-amber-400 to-orange-500" },
] as const;


async function loadAllPipelineDeals(pipelineId: string): Promise<Deal[]> {
  const firstPage = await dealService.list({ page: 1, page_size: 100, pipeline_id: pipelineId, sort_by: "expected_close_date", sort_direction: "asc" });
  const totalPages = Math.ceil(firstPage.meta.total / firstPage.meta.page_size);
  if (totalPages <= 1) return firstPage.items;

  const items = [...firstPage.items];
  for (let page = 2; page <= totalPages; page += 1) {
    const result = await dealService.list({ page, page_size: 100, pipeline_id: pipelineId, sort_by: "expected_close_date", sort_direction: "asc" });
    items.push(...result.items);
  }
  return items;
}

function stageTotals(deals: Deal[]): Array<[string, number]> {
  const totals = new Map<string, number>();
  for (const deal of deals) {
    const value = Number(deal.value);
    if (!Number.isFinite(value)) continue;
    totals.set(deal.currency, (totals.get(deal.currency) ?? 0) + value);
  }
  return [...totals.entries()].slice(0, 2);
}

export function SalesBoardWorkspace() {
  const { formatMoney, formatNumber, locale, t } = useI18n();
  const { user } = useAuth();
  const { companies } = useCompanyOptions();
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [pipeline, setPipeline] = useState<PipelineDetail | null>(null);
  const [selectedPipelineId, setSelectedPipelineId] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [movingDealId, setMovingDealId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadNonce, setReloadNonce] = useState(0);

  const canUpdateDeals = user?.permissions.some((permission) => permission.name === "deals.update") ?? false;
  const companyNames = useMemo(() => new Map(companies.map((company) => [company.id, company.name])), [companies]);

  const loadPipelines = useCallback(async () => {
    const result = await pipelineService.list({ page: 1, page_size: 100, sort_by: "name", sort_direction: "asc" });
    return result.items;
  }, []);

  useEffect(() => {
    let active = true;
    async function bootstrap() {
      setIsLoading(true);
      try {
        const nextPipelines = await loadPipelines();
        if (!active) return;
        setPipelines(nextPipelines);
        const nextPipelineId = selectedPipelineId || nextPipelines[0]?.id || "";
        setSelectedPipelineId(nextPipelineId);
        if (!nextPipelineId) {
          setPipeline(null);
          setDeals([]);
          setError(null);
          return;
        }
        const [pipelineResult, dealsResult] = await Promise.all([
          pipelineService.get(nextPipelineId),
          loadAllPipelineDeals(nextPipelineId),
        ]);
        if (!active) return;
        setPipeline(pipelineResult);
        setDeals(dealsResult);
        setError(null);
      } catch (caughtError) {
        if (active) setError(getErrorMessage(caughtError));
      } finally {
        if (active) setIsLoading(false);
      }
    }
    void bootstrap();
    return () => { active = false; };
  }, [loadPipelines, reloadNonce, selectedPipelineId]);

  async function refreshBoard() {
    setIsRefreshing(true);
    setReloadNonce((value) => value + 1);
    window.setTimeout(() => setIsRefreshing(false), 250);
  }

  async function moveDeal(dealId: string, stage: PipelineStage) {
    const current = deals.find((deal) => deal.id === dealId);
    if (!current || current.stage_id === stage.id || !canUpdateDeals) return;

    const previousDeals = deals;
    setMovingDealId(dealId);
    setError(null);
    setDeals((items) => items.map((deal) => deal.id === dealId ? { ...deal, probability: stage.probability, stage_id: stage.id } : deal));
    try {
      const updated = await dealService.update(dealId, { probability: Number(stage.probability), stage_id: stage.id });
      setDeals((items) => items.map((deal) => deal.id === dealId ? updated : deal));
    } catch (caughtError) {
      setDeals(previousDeals);
      setError(getErrorMessage(caughtError));
    } finally {
      setMovingDealId(null);
    }
  }

  if (isLoading) return <LoadingState label="Loading sales board..." />;
  if (error && pipelines.length === 0) return <ErrorState action={<Button onClick={() => setReloadNonce((value) => value + 1)}><T>Try again</T></Button>} description={error} title="Unable to load sales board" />;

  const stages = [...(pipeline?.stages ?? [])].sort((a, b) => a.order - b.order);
  const openDeals = deals.filter((deal) => deal.status === "open");
  const weightedValue = openDeals.reduce((sum, deal) => sum + (Number(deal.value) * Number(deal.probability)) / 100, 0);
  const currencies = new Set(openDeals.map((deal) => deal.currency));
  const weightedLabel = currencies.size === 1 && openDeals[0] ? formatMoney(weightedValue, openDeals[0].currency) : openDeals.length > 0 ? t("Mixed currencies") : "—";

  return (
    <section className="crm-page mx-auto max-w-[1800px]">
      <div className="crm-hero p-6 sm:p-8">
        <div aria-hidden="true" className="absolute -right-16 -top-20 h-56 w-56 rounded-full bg-indigo-400/10 blur-3xl" />
        <div className="relative flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="crm-kicker"><T>Sales workspace</T></p>
            <h1 className="mt-5 text-3xl font-bold tracking-[-0.045em] text-slate-950 dark:text-white sm:text-[2.55rem]"><T>Pipeline board</T></h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400"><T>Move opportunities through the funnel, spot bottlenecks and keep the sales team focused on the next best action.</T></p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <label className="sr-only" htmlFor="sales-board-pipeline"><T>Pipeline</T></label>
            <select className="crm-select min-w-60 rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm font-semibold text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="sales-board-pipeline" onChange={(event) => setSelectedPipelineId(event.target.value)} value={selectedPipelineId}>
              {pipelines.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <Button disabled={isRefreshing} onClick={() => void refreshBoard()} variant="secondary">{isRefreshing ? t("Refreshing...") : t("Refresh")}</Button>
            <Link className="inline-flex min-h-10 items-center justify-center rounded-xl bg-gradient-to-b from-indigo-500 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-[0_8px_22px_rgba(79,70,229,.24)] transition hover:-translate-y-px hover:shadow-[0_12px_28px_rgba(79,70,229,.30)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:focus-visible:ring-indigo-950" href="/dashboard/deals"><T>Deals list</T></Link>
          </div>
        </div>
      </div>

      {pipelines.length === 0 ? (
        <div className="mt-6"><ErrorState description="Create a pipeline and its stages before using the board." title="No sales pipeline yet" /></div>
      ) : null}

      {pipeline ? (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <article className="crm-metric p-5"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400"><T>Open deals</T></p><p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{formatNumber(openDeals.length)}</p></article>
            <article className="crm-metric p-5"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400"><T>Stages</T></p><p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{formatNumber(stages.length)}</p></article>
            <article className="crm-metric p-5"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400"><T>Weighted pipeline</T></p><p className="mt-3 truncate text-3xl font-semibold text-slate-950 dark:text-white">{weightedLabel}</p></article>
            <article className="crm-metric p-5"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400"><T>Closed</T></p><p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{formatNumber(deals.filter((deal) => deal.status !== "open").length)}</p></article>
          </div>

          {error ? <p className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}
          {!canUpdateDeals ? <p className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/35 dark:text-amber-200"><T>You have read-only access to deals. Stage movement is disabled.</T></p> : null}

          {stages.length === 0 ? <div className="mt-6"><ErrorState description="Add at least one stage to this pipeline before moving deals on the board." title="Pipeline has no stages" /></div> : null}

          <div className="crm-scroll-mask mt-6 overflow-x-auto pb-5">
            <div className="grid min-w-max auto-cols-[minmax(310px,350px)] grid-flow-col gap-4">
              {stages.map((stage, stageIndex) => {
                const stageDeals = deals.filter((deal) => deal.stage_id === stage.id);
                const totals = stageTotals(stageDeals);
                const accent = stageAccents[stageIndex % stageAccents.length];
                return (
                  <section
                    aria-label={locale === "fa" ? `مرحله ${stage.name}` : `${stage.name} stage`}
                    className="relative flex max-h-[70vh] min-h-[430px] flex-col overflow-hidden rounded-[20px] border border-slate-200/80 bg-slate-50/75 shadow-sm transition hover:border-indigo-200/70 dark:border-slate-800 dark:bg-slate-900/45 dark:hover:border-indigo-900/80"
                    key={stage.id}
                    onDragOver={(event) => { if (canUpdateDeals) event.preventDefault(); }}
                    onDrop={(event) => { event.preventDefault(); const dealId = event.dataTransfer.getData("text/deal-id"); if (dealId) void moveDeal(dealId, stage); }}
                  >
                    <div aria-hidden="true" className={`h-[3px] w-full bg-gradient-to-r ${accent.bar}`} />
                    <header className="relative border-b border-slate-200/70 bg-white/92 p-4 dark:border-slate-800 dark:bg-slate-950/82">
                      <div className="flex items-start justify-between gap-3"><div><h2 className="font-semibold text-slate-950 dark:text-white">{stage.name}</h2><p className="mt-1 text-xs text-slate-500">{formatNumber(stage.probability)}{locale === "fa" ? "٪" : "%"} {t("Probability")}</p></div><span className="rounded-lg bg-white px-2.5 py-1 text-xs font-bold tabular-nums text-slate-700 shadow-sm ring-1 ring-slate-200 dark:bg-slate-950 dark:text-slate-200 dark:ring-slate-800">{formatNumber(stageDeals.length)}</span></div>
                      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200/70 dark:bg-slate-800"><div className={`h-full rounded-full bg-gradient-to-r ${accent.bar}`} style={{ width: `${Math.max(Number(stage.probability), 4)}%` }} /></div>
                      {totals.length > 0 ? <p className="mt-3 truncate text-xs font-semibold text-slate-600 dark:text-slate-300">{totals.map(([currency, value]) => formatMoney(value, currency)).join(" · ")}</p> : null}
                    </header>
                    <div className="crm-scroll-mask flex-1 space-y-3 overflow-y-auto p-3">
                      {stageDeals.length === 0 ? <div className="flex min-h-28 items-center justify-center rounded-2xl border border-dashed border-slate-300/80 bg-white/55 px-4 text-center text-xs font-medium text-slate-400 transition dark:border-slate-700 dark:bg-slate-950/30"><T>Drop a deal here</T></div> : null}
                      {stageDeals.map((deal) => (
                        <article className="group rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,.03),0_8px_20px_rgba(15,23,42,.045)] transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-1 hover:border-indigo-200 hover:shadow-[0_14px_32px_rgba(15,23,42,.09)] dark:border-slate-800 dark:bg-slate-950 dark:hover:border-indigo-900" draggable={canUpdateDeals} key={deal.id} onDragStart={(event) => { event.dataTransfer.effectAllowed = "move"; event.dataTransfer.setData("text/deal-id", deal.id); }}>
                          <div className="flex items-start justify-between gap-3"><div className="min-w-0"><Link className="block truncate text-sm font-bold text-slate-950 transition group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-300" href={`/dashboard/deals/${deal.id}`}>{deal.title}</Link><p className="mt-1 truncate text-xs text-slate-500">{companyNames.get(deal.company_id) ?? t("Company")}</p></div><StatusBadge tone={deal.status === "won" ? "green" : deal.status === "lost" ? "red" : "blue"}><LocalizedEnum value={deal.status} /></StatusBadge></div>
                          <div className="mt-4 flex items-end justify-between gap-3"><div><p className="text-sm font-bold text-slate-900 dark:text-slate-100"><LocalizedMoney value={deal.value} currency={deal.currency} /></p><p className="mt-1 text-xs text-slate-500"><T>Close</T> <LocalizedDate value={deal.expected_close_date} /></p></div><span className="text-xs font-bold text-slate-400">{formatNumber(deal.probability)}{locale === "fa" ? "٪" : "%"}</span></div>
                          <div className="mt-4 border-t border-slate-100 pt-3 dark:border-slate-800"><label className="sr-only" htmlFor={`move-${deal.id}`}>{locale === "fa" ? `انتقال ${deal.title}` : `Move ${deal.title}`}</label><select className="crm-select w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2 text-xs font-semibold text-slate-700 outline-none focus:border-indigo-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200" disabled={!canUpdateDeals || movingDealId === deal.id} id={`move-${deal.id}`} onChange={(event) => { const nextStage = stages.find((item) => item.id === event.target.value); if (nextStage) void moveDeal(deal.id, nextStage); }} value={deal.stage_id}>{stages.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div>
                        </article>
                      ))}
                    </div>
                  </section>
                );
              })}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
