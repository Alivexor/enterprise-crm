"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AttachmentPanel } from "@/components/attachments/attachment-panel";
import { T, confirmDelete, useI18n } from "@/components/i18n/i18n-provider";
import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { useToast } from "@/components/ui/toast-provider";
import { LeadConversionPanel } from "@/features/leads/lead-conversion-panel";
import { LeadForm } from "@/features/leads/lead-form";
import { CustomFieldsPanel } from "@/features/custom-fields/custom-fields-panel";
import { LeadScoreCard } from "@/features/intelligence/lead-score-card";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { leadService } from "@/services/lead-service";
import type { Lead, LeadConversionInput, LeadConversionResult, LeadInput } from "@/types/lead";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load this lead.";
}

function leadTone(status: Lead["status"]): "blue" | "gray" | "green" | "orange" | "red" {
  if (status === "converted") return "green";
  if (status === "lost" || status === "unqualified") return "red";
  if (status === "qualified") return "blue";
  return "orange";
}

export function LeadDetail({ leadId }: { leadId: string }) {
  const router = useRouter();
  const { user } = useAuth();
  const { t } = useI18n();
  const { notify } = useToast();
  const [lead, setLead] = useState<Lead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSubmittingConversion, setIsSubmittingConversion] = useState(false);
  const [convertedDealId, setConvertedDealId] = useState<string | null>(null);
  const { companies, isLoading: isLoadingCompanies } = useCompanyOptions();
  const companyNames = useMemo(
    () => new Map(companies.map((company) => [company.id, company.name])),
    [companies],
  );
  const permissions = useMemo(
    () => new Set(user?.permissions.map((permission) => permission.name) ?? []),
    [user],
  );
  const canConvert = permissions.has("leads.update")
    && permissions.has("deals.create")
    && permissions.has("pipelines.read");

  useEffect(() => {
    let isActive = true;
    async function loadLead() {
      try {
        const nextLead = await leadService.get(leadId);
        if (isActive) {
          setLead(nextLead);
          setError(null);
        }
      } catch (caughtError) {
        if (isActive) setError(getErrorMessage(caughtError));
      } finally {
        if (isActive) setIsLoading(false);
      }
    }
    void loadLead();
    return () => { isActive = false; };
  }, [leadId]);

  async function updateLead(values: LeadInput) {
    setIsSaving(true);
    try {
      const nextLead = await leadService.update(leadId, values);
      setLead(nextLead);
      setError(null);
      setIsEditing(false);
      notify({ title: t("Lead updated"), tone: "success" });
    } catch (caughtError) {
      const message = getErrorMessage(caughtError);
      setError(message);
      notify({ description: message, title: t("Unable to update lead"), tone: "error" });
    } finally {
      setIsSaving(false);
    }
  }

  async function convertLead(input: LeadConversionInput): Promise<LeadConversionResult> {
    setIsSubmittingConversion(true);
    try {
      const result = await leadService.convert(leadId, input);
      setLead(result.lead);
      setConvertedDealId(result.deal.id);
      setError(null);
      setIsConverting(false);
      notify({
        description: t("The opportunity was added to the sales pipeline."),
        title: t("Lead converted successfully"),
        tone: "success",
      });
      return result;
    } catch (caughtError) {
      const message = getErrorMessage(caughtError);
      setError(message);
      notify({ description: message, title: t("Lead conversion failed"), tone: "error" });
      throw caughtError;
    } finally {
      setIsSubmittingConversion(false);
    }
  }

  async function deleteLead() {
    if (!confirmDelete(lead?.title)) return;
    setIsDeleting(true);
    try {
      await leadService.remove(leadId);
      router.replace("/dashboard/leads");
    } catch (caughtError) {
      const message = getErrorMessage(caughtError);
      setError(message);
      setIsDeleting(false);
      notify({ description: message, title: t("Unable to delete lead"), tone: "error" });
    }
  }

  if (isLoading) return <LoadingState label="Loading lead…" />;
  if (!lead) {
    return (
      <section className="crm-page mx-auto max-w-4xl">
        <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/leads"><T>← Back to leads</T></Link>
        <div className="mt-6"><ErrorState description={error ?? "Lead not found."} title="Unable to load lead" /></div>
      </section>
    );
  }

  const initialValues: LeadInput = {
    company_id: lead.company_id,
    contact_id: lead.contact_id,
    description: lead.description,
    source: lead.source,
    status: lead.status,
    title: lead.title,
  };
  const conversionAvailable = canConvert && !["converted", "lost"].includes(lead.status);

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/leads"><T>← Back to leads</T></Link>
      <div className="crm-card mt-6 flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="crm-kicker"><T>Lead</T></p>
            <h1 className="crm-title mt-3">{lead.title}</h1>
            <div className="mt-3"><StatusBadge tone={leadTone(lead.status)}><LocalizedEnum value={lead.status} /></StatusBadge></div>
          </div>
          <div className="flex flex-wrap gap-2">
            {conversionAvailable ? <Button onClick={() => { setIsEditing(false); setIsConverting((value) => !value); }}>{isConverting ? <T>Close conversion</T> : <T>Convert to deal</T>}</Button> : null}
            <Button onClick={() => { setIsConverting(false); setIsEditing((value) => !value); }} variant="secondary">{isEditing ? <T>Close edit</T> : <T>Edit</T>}</Button>
            <Button disabled={isDeleting} onClick={() => void deleteLead()} variant="danger">{isDeleting ? <T>Deleting…</T> : <T>Delete</T>}</Button>
          </div>
        </div>

        {error ? <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}
        {convertedDealId ? (
          <div className="flex flex-col gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3.5 dark:border-emerald-950 dark:bg-emerald-950/25 sm:flex-row sm:items-center sm:justify-between">
            <div><p className="text-sm font-bold text-emerald-800 dark:text-emerald-200"><T>Lead converted successfully</T></p><p className="mt-1 text-xs text-emerald-700/80 dark:text-emerald-300/80"><T>The new deal is ready in your sales pipeline.</T></p></div>
            <Link className="text-sm font-bold text-emerald-800 hover:text-emerald-600 dark:text-emerald-200" href={`/dashboard/deals/${convertedDealId}`}><T>Open deal</T> →</Link>
          </div>
        ) : null}

        {isConverting ? (
          <LeadConversionPanel
            isSubmitting={isSubmittingConversion}
            lead={lead}
            onCancel={() => setIsConverting(false)}
            onSubmit={convertLead}
          />
        ) : null}

        {isEditing ? (
          isLoadingCompanies
            ? <LoadingState label="Loading company options…" />
            : <LeadForm companies={companies} initialValues={initialValues} isSubmitting={isSaving} key={lead.id} onCancel={() => setIsEditing(false)} onSubmit={updateLead} submitLabel="Save changes" />
        ) : !isConverting ? (
          <dl className="grid gap-6 border-t border-slate-100 pt-6 sm:grid-cols-2 dark:border-slate-800">
            <div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Source</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedEnum value={lead.source} /></dd></div>
            <div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Company</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">{lead.company_id ? companyNames.get(lead.company_id) ?? <T>Unknown company</T> : "—"}</dd></div>
            <div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Created</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedDateTime value={lead.created_at} /></dd></div>
            <div className="sm:col-span-2"><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Description</T></dt><dd className="mt-2 whitespace-pre-wrap text-sm text-slate-800 dark:text-slate-100">{lead.description ?? "—"}</dd></div>
          </dl>
        ) : null}
        <LeadScoreCard leadId={lead.id} />
        <CustomFieldsPanel entityId={lead.id} entityType="lead" />
        <AttachmentPanel entityId={lead.id} entityType="lead" />
      </div>
    </section>
  );
}
