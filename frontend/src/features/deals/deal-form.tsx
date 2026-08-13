"use client";

import { LocalizedEnum, LocalizedPercent } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { pipelineService } from "@/services/pipeline-service";
import type { Company } from "@/types/company";
import { dealStatuses, type DealInput } from "@/types/deal";
import type { Pipeline, PipelineStage } from "@/types/pipeline";

type DealFormProps = {
  assignedUserId: string;
  companies: Company[];
  initialValues?: DealInput;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (input: DealInput) => Promise<void>;
  pipelines: Pipeline[];
  submitLabel: string;
};

const emptyDeal: DealInput = {
  assigned_user_id: "",
  company_id: "",
  contact_id: null,
  currency: "USD",
  expected_close_date: "",
  pipeline_id: "",
  probability: 0,
  stage_id: "",
  status: "open",
  title: "",
  value: 0,
};

export function DealForm({
  assignedUserId,
  companies,
  initialValues = emptyDeal,
  isSubmitting,
  onCancel,
  onSubmit,
  pipelines,
  submitLabel,
}: DealFormProps) {
  const [title, setTitle] = useState(initialValues.title);
  const [companyId, setCompanyId] = useState(initialValues.company_id);
  const [pipelineId, setPipelineId] = useState(initialValues.pipeline_id);
  const [stageId, setStageId] = useState(initialValues.stage_id);
  const [value, setValue] = useState(String(initialValues.value));
  const [currency, setCurrency] = useState(initialValues.currency);
  const [probability, setProbability] = useState(String(initialValues.probability));
  const [expectedCloseDate, setExpectedCloseDate] = useState(initialValues.expected_close_date);
  const [status, setStatus] = useState(initialValues.status);
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [isLoadingStages, setIsLoadingStages] = useState(false);
  const [stageError, setStageError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    if (!pipelineId) {
      return () => { isActive = false; };
    }

    async function loadStages() {
      setIsLoadingStages(true);
      try {
        const pipeline = await pipelineService.get(pipelineId);
        if (isActive) {
          setStages(pipeline.stages);
          setStageError(null);
          if (!pipeline.stages.some((stage) => stage.id === stageId)) {
            setStageId(pipeline.stages[0]?.id ?? "");
          }
        }
      } catch {
        if (isActive) {
          setStages([]);
          setStageError("Unable to load stages for this pipeline.");
        }
      } finally {
        if (isActive) setIsLoadingStages(false);
      }
    }
    void loadStages();
    return () => { isActive = false; };
  }, [pipelineId, stageId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      assigned_user_id: initialValues.assigned_user_id || assignedUserId,
      company_id: companyId,
      contact_id: null,
      currency: currency.trim().toUpperCase(),
      expected_close_date: expectedCloseDate,
      pipeline_id: pipelineId,
      probability: Number(probability),
      stage_id: stageId,
      status,
      title: title.trim(),
      value: Number(value),
    });
  }

  const canSubmit = Boolean(companyId && pipelineId && stageId && assignedUserId);

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-title"><T>Deal title</T></label>
        <input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-title" maxLength={255} minLength={1} onChange={(event) => setTitle(event.target.value)} required value={title} />
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-company"><T>Company</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" disabled={!companies.length} id="deal-company" onChange={(event) => setCompanyId(event.target.value)} required value={companyId}><option value=""><T>Select a company</T></option>{companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}</select></div>
        <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-pipeline"><T>Pipeline</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" disabled={!pipelines.length} id="deal-pipeline" onChange={(event) => { setPipelineId(event.target.value); setStageId(""); }} required value={pipelineId}><option value=""><T>Select a pipeline</T></option>{pipelines.map((pipeline) => <option key={pipeline.id} value={pipeline.id}>{pipeline.name}</option>)}</select></div>
      </div>
      <div className="grid gap-5 sm:grid-cols-2"><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-stage"><T>Stage</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" disabled={!pipelineId || isLoadingStages || !stages.length} id="deal-stage" onChange={(event) => setStageId(event.target.value)} required value={stageId}><option value="">{isLoadingStages ? <T>Loading stages...</T> : <T>Select a stage</T>}</option>{stages.map((stage) => <option key={stage.id} value={stage.id}>{stage.name} (<LocalizedPercent value={stage.probability} />)</option>)}</select>{stageError ? <p className="text-sm text-rose-700 dark:text-rose-200"><T>{stageError}</T></p> : null}</div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-status"><T>Status</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-status" onChange={(event) => setStatus(event.target.value as DealInput["status"])} value={status}>{dealStatuses.map((item) => <option key={item} value={item}><LocalizedEnum value={item} /></option>)}</select></div></div>
      <div className="grid gap-5 sm:grid-cols-4"><div className="space-y-2 sm:col-span-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-value"><T>Value</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-value" min="0.01" onChange={(event) => setValue(event.target.value)} required step="0.01" type="number" value={value} /></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-currency"><T>Currency</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm uppercase text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-currency" maxLength={3} minLength={3} onChange={(event) => setCurrency(event.target.value)} required value={currency} /></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-probability"><T>Probability</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-probability" max="100" min="0" onChange={(event) => setProbability(event.target.value)} required step="0.01" type="number" value={probability} /></div></div>
      <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="deal-close-date"><T>Expected close date</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="deal-close-date" onChange={(event) => setExpectedCloseDate(event.target.value)} required type="date" value={expectedCloseDate} /></div>
      <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">{onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}<Button disabled={isSubmitting || !canSubmit} type="submit">{isSubmitting ? <T>Saving...</T> : <T>{submitLabel}</T>}</Button></div>
    </form>
  );
}
