"use client";

import { useState, type FormEvent } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { LocalizedPercent } from "@/components/i18n/localized-value";
import { Button } from "@/components/ui/button";
import { usePipelineOptions } from "@/hooks/use-pipeline-options";
import { pipelineService } from "@/services/pipeline-service";
import type { Lead, LeadConversionInput, LeadConversionResult } from "@/types/lead";
import type { PipelineStage } from "@/types/pipeline";

function defaultCloseDate(): string {
  const date = new Date();
  date.setDate(date.getDate() + 30);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function LeadConversionPanel({
  lead,
  isSubmitting,
  onCancel,
  onSubmit,
}: {
  lead: Lead;
  isSubmitting: boolean;
  onCancel: () => void;
  onSubmit: (input: LeadConversionInput) => Promise<LeadConversionResult>;
}) {
  const { t } = useI18n();
  const { error: pipelineError, isLoading: isLoadingPipelines, pipelines } = usePipelineOptions();
  const [title, setTitle] = useState(lead.title);
  const [pipelineId, setPipelineId] = useState("");
  const [stageId, setStageId] = useState("");
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [isLoadingStages, setIsLoadingStages] = useState(false);
  const [stageError, setStageError] = useState<string | null>(null);
  const [value, setValue] = useState("1000");
  const [currency, setCurrency] = useState("USD");
  const [probability, setProbability] = useState("50");
  const [expectedCloseDate, setExpectedCloseDate] = useState(defaultCloseDate);

  async function selectPipeline(nextPipelineId: string) {
    setPipelineId(nextPipelineId);
    setStageId("");
    setStages([]);
    setStageError(null);
    if (!nextPipelineId) return;
    setIsLoadingStages(true);
    try {
      const pipeline = await pipelineService.get(nextPipelineId);
      setStages(pipeline.stages);
      const firstStage = pipeline.stages[0];
      if (firstStage) {
        setStageId(firstStage.id);
        setProbability(String(firstStage.probability));
      }
    } catch {
      setStageError(t("Unable to load stages for this pipeline."));
    } finally {
      setIsLoadingStages(false);
    }
  }

  function selectStage(nextStageId: string) {
    setStageId(nextStageId);
    const stage = stages.find((item) => item.id === nextStageId);
    if (stage) setProbability(String(stage.probability));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await onSubmit({
        currency: currency.trim().toUpperCase(),
        expected_close_date: expectedCloseDate,
        pipeline_id: pipelineId,
        probability: Number(probability),
        stage_id: stageId,
        title: title.trim(),
        value: Number(value),
      });
    } catch {
      // The parent owns translated error feedback and keeps this form open for correction.
    }
  }

  const canSubmit = Boolean(
    lead.company_id
      && pipelineId
      && stageId
      && Number(value) > 0
      && expectedCloseDate
      && currency.trim().length === 3,
  );

  return (
    <form className="crm-card mt-5 overflow-hidden border-indigo-200/80 dark:border-indigo-950" onSubmit={(event) => void submit(event)}>
      <div className="border-b border-indigo-100/80 bg-gradient-to-r from-indigo-50/80 to-cyan-50/40 px-5 py-4 dark:border-indigo-950 dark:from-indigo-950/35 dark:to-cyan-950/15">
        <p className="crm-kicker"><T>Lead conversion</T></p>
        <h2 className="mt-2 text-base font-bold text-slate-950 dark:text-white"><T>Create a sales opportunity from this lead</T></h2>
        <p className="mt-1 text-xs leading-5 text-slate-500"><T>Company, contact and owner stay linked automatically. Choose where the new deal enters the pipeline.</T></p>
      </div>

      <div className="space-y-5 p-5">
        {!lead.company_id ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-950 dark:bg-amber-950/30 dark:text-amber-200">
            <T>Link this lead to a company before converting it.</T>
          </div>
        ) : null}
        {pipelineError ? <p className="text-sm text-rose-700 dark:text-rose-200"><T>{pipelineError}</T></p> : null}
        {stageError ? <p className="text-sm text-rose-700 dark:text-rose-200"><T>{stageError}</T></p> : null}

        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-800 dark:text-slate-100" htmlFor="lead-conversion-title"><T>Deal title</T></label>
          <input className="crm-input w-full" id="lead-conversion-title" maxLength={255} minLength={1} onChange={(event) => setTitle(event.target.value)} required value={title} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-800 dark:text-slate-100" htmlFor="lead-conversion-pipeline"><T>Pipeline</T></label>
            <select className="crm-select w-full" disabled={isLoadingPipelines || !lead.company_id} id="lead-conversion-pipeline" onChange={(event) => void selectPipeline(event.target.value)} required value={pipelineId}>
              <option value="">{isLoadingPipelines ? t("Loading pipelines...") : t("Select a pipeline")}</option>
              {pipelines.map((pipeline) => <option key={pipeline.id} value={pipeline.id}>{pipeline.name}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-800 dark:text-slate-100" htmlFor="lead-conversion-stage"><T>Stage</T></label>
            <select className="crm-select w-full" disabled={!pipelineId || isLoadingStages || !stages.length} id="lead-conversion-stage" onChange={(event) => selectStage(event.target.value)} required value={stageId}>
              <option value="">{isLoadingStages ? t("Loading stages...") : t("Select a stage")}</option>
              {stages.map((stage) => <option key={stage.id} value={stage.id}>{stage.name} ({String(stage.probability)}%)</option>)}
            </select>
            {stageId ? <p className="text-xs text-slate-500"><T>Stage probability</T>: <LocalizedPercent value={probability} /></p> : null}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-4">
          <div className="space-y-2 sm:col-span-2">
            <label className="text-sm font-semibold text-slate-800 dark:text-slate-100" htmlFor="lead-conversion-value"><T>Value</T></label>
            <input className="crm-input w-full" id="lead-conversion-value" min="0.01" onChange={(event) => setValue(event.target.value)} required step="0.01" type="number" value={value} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-800 dark:text-slate-100" htmlFor="lead-conversion-currency"><T>Currency</T></label>
            <input className="crm-input w-full uppercase" dir="ltr" id="lead-conversion-currency" maxLength={3} minLength={3} onChange={(event) => setCurrency(event.target.value)} required value={currency} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-800 dark:text-slate-100" htmlFor="lead-conversion-probability"><T>Probability</T></label>
            <input className="crm-input w-full" id="lead-conversion-probability" max="100" min="0" onChange={(event) => setProbability(event.target.value)} required step="0.01" type="number" value={probability} />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-800 dark:text-slate-100" htmlFor="lead-conversion-close-date"><T>Expected close date</T></label>
          <input className="crm-input w-full" id="lead-conversion-close-date" onChange={(event) => setExpectedCloseDate(event.target.value)} required type="date" value={expectedCloseDate} />
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-slate-100 pt-4 sm:flex-row sm:justify-end dark:border-slate-800">
          <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button>
          <Button disabled={isSubmitting || !canSubmit} type="submit">{isSubmitting ? <T>Converting...</T> : <T>Convert to deal</T>}</Button>
        </div>
      </div>
    </form>
  );
}
