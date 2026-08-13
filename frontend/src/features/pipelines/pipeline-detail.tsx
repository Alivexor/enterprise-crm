"use client";

import { LocalizedNumber, LocalizedPercent } from "@/components/i18n/localized-value";
import { T, confirmDelete } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PipelineForm } from "@/features/pipelines/pipeline-form";
import { StageForm } from "@/features/pipelines/stage-form";
import { ApiError } from "@/services/api-client";
import { pipelineService } from "@/services/pipeline-service";
import type { PipelineDetail as PipelineDetailType, PipelineInput, PipelineStage, PipelineStageInput } from "@/types/pipeline";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load this pipeline.";
}

export function PipelineDetail({ pipelineId }: { pipelineId: string }) {
  const router = useRouter();
  const [pipeline, setPipeline] = useState<PipelineDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreatingStage, setIsCreatingStage] = useState(false);
  const [editingStage, setEditingStage] = useState<PipelineStage | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadPipeline = async () => {
    try {
      const nextPipeline = await pipelineService.get(pipelineId);
      setPipeline(nextPipeline);
      setError(null);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isActive = true;

    async function initialLoad() {
      try {
        const nextPipeline = await pipelineService.get(pipelineId);
        if (isActive) {
          setPipeline(nextPipeline);
          setError(null);
        }
      } catch (caughtError) {
        if (isActive) {
          setError(getErrorMessage(caughtError));
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void initialLoad();
    return () => {
      isActive = false;
    };
  }, [pipelineId]);

  async function updatePipeline(values: PipelineInput) {
    setIsSaving(true);
    try { setPipeline(await pipelineService.update(pipelineId, values)); setIsEditing(false); setError(null); }
    catch (caughtError) { setError(getErrorMessage(caughtError)); }
    finally { setIsSaving(false); }
  }

  async function saveStage(values: PipelineStageInput) {
    setIsSaving(true);
    try {
      if (editingStage) await pipelineService.updateStage(pipelineId, editingStage.id, values);
      else await pipelineService.createStage(pipelineId, values);
      setEditingStage(null); setIsCreatingStage(false); await loadPipeline();
    } catch (caughtError) { setError(getErrorMessage(caughtError)); }
    finally { setIsSaving(false); }
  }

  async function deleteStage(stage: PipelineStage) {
    if (!confirmDelete(stage.name)) return;
    setIsSaving(true);
    try { await pipelineService.removeStage(pipelineId, stage.id); await loadPipeline(); }
    catch (caughtError) { setError(getErrorMessage(caughtError)); }
    finally { setIsSaving(false); }
  }

  async function deletePipeline() {
    if (!confirmDelete(pipeline?.name)) return;
    setIsDeleting(true);
    try { await pipelineService.remove(pipelineId); router.replace("/dashboard/pipelines"); }
    catch (caughtError) { setError(getErrorMessage(caughtError)); setIsDeleting(false); }
  }

  if (isLoading) return <LoadingState label="Loading pipeline..." />;
  if (!pipeline) return <section className="crm-page mx-auto max-w-4xl"><Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/pipelines"><T>← Back to pipelines</T></Link><div className="mt-6"><ErrorState description={error ?? "Pipeline not found."} title="Unable to load pipeline" /></div></section>;

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/pipelines"><T>← Back to pipelines</T></Link>
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div><p className="crm-kicker"><T>Pipeline</T></p><h1 className="crm-title mt-3">{pipeline.name}</h1></div>
          <div className="flex gap-2"><Button onClick={() => setIsEditing((value) => !value)} variant="secondary">{isEditing ? <T>Close edit</T> : <T>Edit</T>}</Button><Button disabled={isDeleting} onClick={() => void deletePipeline()} variant="danger">{isDeleting ? <T>Deleting...</T> : <T>Delete</T>}</Button></div>
        </div>
        {error ? <p className="mt-5 rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}
        {isEditing ? <div className="mt-6"><PipelineForm initialValues={{ description: pipeline.description, name: pipeline.name }} isSubmitting={isSaving} onCancel={() => setIsEditing(false)} onSubmit={updatePipeline} submitLabel="Save changes" /></div> : <p className="mt-5 text-sm leading-6 text-slate-600 dark:text-slate-300">{pipeline.description ?? <T>No description.</T>}</p>}
        <div className="mt-8 border-t border-slate-100 pt-6 dark:border-slate-800"><div className="flex items-center justify-between gap-4"><div><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>Stages</T></h2><p className="mt-1 text-sm text-slate-500"><T>Order and probability define how opportunities progress.</T></p></div><Button onClick={() => { setEditingStage(null); setIsCreatingStage((value) => !value); }} size="sm">{isCreatingStage ? <T>Close form</T> : <T>Add stage</T>}</Button></div>
          {isCreatingStage ? <div className="mt-5"><StageForm isSubmitting={isSaving} onCancel={() => setIsCreatingStage(false)} onSubmit={saveStage} submitLabel="Add stage" /></div> : null}
          <ol className="mt-5 space-y-3">{pipeline.stages.map((stage) => <li className="rounded-lg border border-slate-200 p-4 dark:border-slate-800" key={stage.id}>{editingStage?.id === stage.id ? <StageForm initialValues={{ name: stage.name, order: stage.order, probability: Number(stage.probability) }} isSubmitting={isSaving} onCancel={() => setEditingStage(null)} onSubmit={saveStage} submitLabel="Save stage" /> : <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold text-slate-900 dark:text-white"><LocalizedNumber value={stage.order + 1} />. {stage.name}</p><p className="mt-1 text-sm text-slate-500"><LocalizedPercent value={stage.probability} /> <T>probability</T></p></div><div className="flex gap-2"><Button onClick={() => setEditingStage(stage)} size="sm" variant="secondary"><T>Edit</T></Button><Button disabled={isSaving} onClick={() => void deleteStage(stage)} size="sm" variant="danger"><T>Delete</T></Button></div></div>}</li>)}</ol>
        </div>
      </div>
    </section>
  );
}
