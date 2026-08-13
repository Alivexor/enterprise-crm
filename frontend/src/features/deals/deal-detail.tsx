"use client";

import { LocalizedDateTime, LocalizedEnum, LocalizedMoney, LocalizedPercent } from "@/components/i18n/localized-value";
import { T, confirmDelete } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { AttachmentPanel } from "@/components/attachments/attachment-panel";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { DealForm } from "@/features/deals/deal-form";
import { CustomFieldsPanel } from "@/features/custom-fields/custom-fields-panel";
import { DealAiInsight } from "@/features/intelligence/deal-ai-insight";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { usePipelineOptions } from "@/hooks/use-pipeline-options";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { dealService } from "@/services/deal-service";
import type { Deal, DealInput } from "@/types/deal";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to load this deal."; }

export function DealDetail({ dealId }: { dealId: string }) {
  const router = useRouter();
  const { user } = useAuth();
  const { companies, isLoading: isLoadingCompanies } = useCompanyOptions();
  const { pipelines, isLoading: isLoadingPipelines } = usePipelineOptions();
  const [deal, setDeal] = useState<Deal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const companyNames = useMemo(() => new Map(companies.map((company) => [company.id, company.name])), [companies]);
  const pipelineNames = useMemo(() => new Map(pipelines.map((pipeline) => [pipeline.id, pipeline.name])), [pipelines]);

  useEffect(() => {
    let isActive = true;
    async function loadDeal() {
      try { const nextDeal = await dealService.get(dealId); if (isActive) { setDeal(nextDeal); setError(null); } }
      catch (caughtError) { if (isActive) setError(getErrorMessage(caughtError)); }
      finally { if (isActive) setIsLoading(false); }
    }
    void loadDeal(); return () => { isActive = false; };
  }, [dealId]);

  async function updateDeal(values: DealInput) {
    setIsSaving(true);
    try { const nextDeal = await dealService.update(dealId, values); setDeal(nextDeal); setError(null); setIsEditing(false); }
    catch (caughtError) { setError(getErrorMessage(caughtError)); }
    finally { setIsSaving(false); }
  }

  async function deleteDeal() {
    if (!confirmDelete(deal?.title)) return;
    setIsDeleting(true);
    try { await dealService.remove(dealId); router.replace("/dashboard/deals"); }
    catch (caughtError) { setError(getErrorMessage(caughtError)); setIsDeleting(false); }
  }

  if (isLoading) return <LoadingState label="Loading deal..." />;
  if (!deal) return <section className="crm-page mx-auto max-w-4xl"><Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/deals"><T>← Back to deals</T></Link><div className="mt-6"><ErrorState description={error ?? "Deal not found."} title="Unable to load deal" /></div></section>;

  const initialValues: DealInput = { assigned_user_id: deal.assigned_user_id, company_id: deal.company_id, contact_id: deal.contact_id, currency: deal.currency, expected_close_date: deal.expected_close_date, pipeline_id: deal.pipeline_id, probability: Number(deal.probability), stage_id: deal.stage_id, status: deal.status, title: deal.title, value: Number(deal.value) };
  return <section className="crm-page mx-auto max-w-4xl"><Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/deals"><T>← Back to deals</T></Link><div className="crm-card mt-6 flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="crm-kicker"><T>Deal</T></p><h1 className="crm-title mt-3">{deal.title}</h1><div className="mt-3"><StatusBadge tone={deal.status === "won" ? "green" : deal.status === "lost" ? "red" : "blue"}><LocalizedEnum value={deal.status} /></StatusBadge></div></div><div className="flex gap-2"><Button onClick={() => setIsEditing((value) => !value)} variant="secondary">{isEditing ? <T>Close edit</T> : <T>Edit</T>}</Button><Button disabled={isDeleting} onClick={() => void deleteDeal()} variant="danger">{isDeleting ? <T>Deleting...</T> : <T>Delete</T>}</Button></div></div>{error ? <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}{isEditing ? (isLoadingCompanies || isLoadingPipelines ? <LoadingState label="Loading deal options..." /> : <DealForm assignedUserId={user?.id ?? deal.assigned_user_id} companies={companies} initialValues={initialValues} isSubmitting={isSaving} key={deal.id} onCancel={() => setIsEditing(false)} onSubmit={updateDeal} pipelines={pipelines} submitLabel="Save changes" />) : <dl className="grid gap-6 border-t border-slate-100 pt-6 sm:grid-cols-2 dark:border-slate-800"><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Value</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedMoney value={deal.value} currency={deal.currency} /></dd></div><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Expected close</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedDateTime value={deal.expected_close_date} /></dd></div><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Company</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">{companyNames.get(deal.company_id) ?? <T>Unknown company</T>}</dd></div><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Pipeline</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">{pipelineNames.get(deal.pipeline_id) ?? <T>Unknown pipeline</T>}</dd></div><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Probability</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedPercent value={deal.probability} /></dd></div></dl>}<DealAiInsight dealId={deal.id} /><CustomFieldsPanel entityId={deal.id} entityType="deal" /><AttachmentPanel entityId={deal.id} entityType="deal" /></div></section>;
}
